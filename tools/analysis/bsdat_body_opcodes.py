"""Round 76 Track B — Hero4 BSDAT/ESDAT body opcode dispatch.

R72 의 BSDAT 88 entries + ESDAT 471 entries 의 body 영역에서
SCN bytecode 와의 opcode 공통성 분석.

SCN 기준 known opcode (e0184/e0185 plaintext + e0185 disasm):
  0x01  : record start (string/entity ref), 0x2e terminator
  0x00 07 00 00 00 : REFERENCE_ENTITY 5-byte fixed prefix (op_0x01 record 내부)
  0x07  : magic
  0x0c  : small immediate value (1B)
  0xf7  : 3-arg bind
  0xff  : record separator
  0x2e  : record terminator ('.')

분석 절차:
  1. 각 BSDAT/ESDAT 평문에서 entry 의 body 영역 byte 추출 (parser 와 동일 로직)
  2. body 의 byte frequency 분포 + 0xff/0x01/0x2e count
  3. SCN op_0x01 reference 패턴 (`01 00 07 00 00 00 ?? ?? 2e`) 매칭
  4. opcode (1B) + length (1B) 추론 시도

산출: work/h4/converted/h4_bsdat_body_opcodes.json
"""
from __future__ import annotations
import json
import pathlib
import sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[2]
E_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'E'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_bsdat_body_opcodes.json'


def is_bsdat_entry(d: bytes, i: int) -> bool:
    if i + 6 > len(d):
        return False
    if d[i+1] != 0:
        return False
    nl = d[i+2]
    if not (3 <= nl <= 30):
        return False
    if i + 3 + nl > len(d):
        return False
    first = d[i+3:i+3+min(6, nl)]
    return any(0xa1 <= first[k] <= 0xfe and k+1 < len(first) and 0xa1 <= first[k+1] <= 0xfe
               for k in range(len(first) - 1))


def is_esdat_entry(d: bytes, i: int) -> bool:
    if i + 7 > len(d):
        return False
    if d[i+1] != 0:
        return False
    nl = d[i+3]
    if not (3 <= nl <= 30):
        return False
    if i + 4 + nl > len(d):
        return False
    first = d[i+4:i+4+min(6, nl)]
    return any(0xa1 <= first[k] <= 0xfe and k+1 < len(first) and 0xa1 <= first[k+1] <= 0xfe
               for k in range(len(first) - 1))


def extract_bodies(data: bytes, detector, name_off: int):
    """Return list of (name_bytes, body_bytes)."""
    out = []
    i = 0
    while i < len(data) - 6:
        if not detector(data, i):
            i += 1
            continue
        nl_off = name_off - 1
        nl = data[i + nl_off]
        name = data[i+name_off:i+name_off+nl]
        body_start = i + name_off + nl
        next_i = body_start
        while next_i < len(data) - 6:
            if detector(data, next_i):
                break
            next_i += 1
        else:
            next_i = len(data)
        out.append((name, data[body_start:next_i]))
        i = next_i
    return out


SCN_REF_PREFIX = bytes.fromhex('00070000 00'.replace(' ', ''))  # 5 byte after 0x01


def detect_scn_refs(body: bytes) -> int:
    """Count occurrences of SCN op_0x01 reference pattern: 01 00 07 00 00 00 ?? ?? 2e"""
    cnt = 0
    i = 0
    while i < len(body) - 8:
        if body[i] == 0x01 and body[i+1:i+6] == SCN_REF_PREFIX:
            # find 0x2e within next 10 bytes
            for j in range(i+6, min(i+15, len(body))):
                if body[j] == 0x2e:
                    cnt += 1
                    i = j + 1
                    break
            else:
                i += 1
        else:
            i += 1
    return cnt


def analyze_bodies(bodies):
    total_len = 0
    byte_freq = Counter()
    sep_counts = []
    term_counts = []
    ref_counts = []
    op_pairs = Counter()  # (opcode, next_byte) for first-byte dispatch hypothesis
    starts = Counter()  # first byte of each body
    for _name, body in bodies:
        total_len += len(body)
        byte_freq.update(body)
        sep_counts.append(body.count(0xff))
        term_counts.append(body.count(0x2e))
        ref_counts.append(detect_scn_refs(body))
        if body:
            starts[body[0]] += 1
        # find records delimited by 0xff and tally first byte (opcode hypothesis)
        records = body.split(b'\xff')
        for r in records:
            if len(r) >= 2:
                op_pairs[(r[0], r[1] if len(r) > 1 else None)] += 1
    return {
        'entry_count': len(bodies),
        'total_body_bytes': total_len,
        'avg_body_bytes': round(total_len / max(1, len(bodies)), 1),
        'byte_freq_top10': [
            {'byte': hex(b), 'count': c, 'pct': round(100*c/max(1,total_len), 2)}
            for b, c in byte_freq.most_common(10)
        ],
        'ff_separator_per_entry_avg': round(sum(sep_counts)/max(1,len(sep_counts)), 1),
        '2e_terminator_per_entry_avg': round(sum(term_counts)/max(1,len(term_counts)), 1),
        'scn_ref_pattern_total': sum(ref_counts),
        'scn_ref_pattern_per_entry_avg': round(sum(ref_counts)/max(1,len(ref_counts)), 2),
        'body_first_byte_top5': [
            {'byte': hex(b), 'count': c} for b, c in starts.most_common(5)
        ],
        'top_record_opcodes': [
            {'op': hex(op), 'next': hex(nx) if nx is not None else None, 'count': c}
            for (op, nx), c in op_pairs.most_common(15)
        ],
    }


def main():
    all_bodies_bsdat = []
    all_bodies_esdat = []
    per_file = {}
    for fn in ['_BSDAT_0', '_BSDAT_1', '_BSDAT_2']:
        p = E_DIR / fn
        if not p.exists():
            print(f'MISSING: {p}')
            continue
        data = p.read_bytes()
        bodies = extract_bodies(data, is_bsdat_entry, name_off=3)
        all_bodies_bsdat.extend(bodies)
        per_file[fn] = {'size': len(data), 'entries': len(bodies), 'analysis': analyze_bodies(bodies)}
    for fn in ['_ESDAT_0', '_ESDAT_1', '_ESDAT_2']:
        p = E_DIR / fn
        if not p.exists():
            print(f'MISSING: {p}')
            continue
        data = p.read_bytes()
        bodies = extract_bodies(data, is_esdat_entry, name_off=4)
        all_bodies_esdat.extend(bodies)
        per_file[fn] = {'size': len(data), 'entries': len(bodies), 'analysis': analyze_bodies(bodies)}

    out = {
        'meta': {
            'round': 'R76 track B',
            'date': '2026-05-19',
            'source': str(E_DIR.relative_to(ROOT)),
            'method': 'body byte frequency + SCN opcode (0x01/0x07/0x2e/0xff) cross-check',
        },
        'aggregate_bsdat': analyze_bodies(all_bodies_bsdat),
        'aggregate_esdat': analyze_bodies(all_bodies_esdat),
        'per_file': per_file,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    # Console summary
    print(f"\n=== BSDAT aggregate ({out['aggregate_bsdat']['entry_count']} entries) ===")
    a = out['aggregate_bsdat']
    print(f"  total body: {a['total_body_bytes']}B  avg: {a['avg_body_bytes']}B")
    print(f"  ff sep avg/entry: {a['ff_separator_per_entry_avg']}  2e term avg: {a['2e_terminator_per_entry_avg']}")
    print(f"  SCN op_0x01 ref pattern: total={a['scn_ref_pattern_total']}, per-entry avg={a['scn_ref_pattern_per_entry_avg']}")
    print(f"  top byte freq: {a['byte_freq_top10'][:6]}")
    print(f"  top record opcodes (after 0xff split): {a['top_record_opcodes'][:8]}")

    print(f"\n=== ESDAT aggregate ({out['aggregate_esdat']['entry_count']} entries) ===")
    a = out['aggregate_esdat']
    print(f"  total body: {a['total_body_bytes']}B  avg: {a['avg_body_bytes']}B")
    print(f"  ff sep avg/entry: {a['ff_separator_per_entry_avg']}  2e term avg: {a['2e_terminator_per_entry_avg']}")
    print(f"  SCN op_0x01 ref pattern: total={a['scn_ref_pattern_total']}, per-entry avg={a['scn_ref_pattern_per_entry_avg']}")
    print(f"  top byte freq: {a['byte_freq_top10'][:6]}")
    print(f"  top record opcodes: {a['top_record_opcodes'][:8]}")

    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
