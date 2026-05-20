"""Hero4 Round 106 — `_ITM_OPTION` 1928B binary structure 정밀.

R84 에서는 텍스트 run 만 추출. R106 은 entry stride/payload 를 확정.

발견된 layout:
- 6B header: `04 00 00 00 00 00`  (LE32=4? L1-L4 4 levels?)
- variable entries:
    [size LE16][nlen 1B][name N B][payload 3B]
  size = nlen(1) + name(N) + payload(3) - 1?  (실측 검증)

산출: work/h4/converted/h4_itm_option_struct.json
"""
from __future__ import annotations
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / 'work' / 'h4' / 'decrypted' / 'ITM' / 'DAT' / '_ITM_OPTION'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_itm_option_struct.json'


def decode_euckr(b: bytes) -> str:
    try:
        return b.decode('euc-kr', errors='replace')
    except Exception:
        return b.hex()


def parse_entries(data: bytes, start: int):
    entries = []
    i = start
    while i + 3 <= len(data):
        size = int.from_bytes(data[i:i+2], 'little')
        if size == 0 or i + 2 + size > len(data):
            break
        nlen = data[i+2]
        if nlen == 0 or 2 + 1 + nlen > 2 + size:
            break
        name_bytes = data[i+3:i+3+nlen]
        payload_off = i + 3 + nlen
        payload_len = (i + 2 + size) - payload_off
        payload = data[payload_off:payload_off+payload_len]
        entries.append({
            'offset': i,
            'size': size,
            'nlen': nlen,
            'name': decode_euckr(name_bytes),
            'name_hex': name_bytes.hex(),
            'payload_len': payload_len,
            'payload_hex': payload.hex(),
            'payload': list(payload),
        })
        i = i + 2 + size
    return entries, i


def main():
    data = SRC.read_bytes()
    header = data[:6]
    header_le32 = int.from_bytes(data[:4], 'little')
    entries, end = parse_entries(data, 6)

    # validate
    consumed = end
    remaining = len(data) - consumed

    # Payload size histogram
    pay_sizes = {}
    for e in entries:
        pay_sizes[e['payload_len']] = pay_sizes.get(e['payload_len'], 0) + 1

    # Group by level suffix (L1..L9) for structure
    from collections import Counter
    payload_byte0 = Counter()
    payload_byte1 = Counter()
    payload_byte2 = Counter()
    for e in entries:
        if e['payload_len'] >= 3:
            payload_byte0[e['payload'][0]] += 1
            payload_byte1[e['payload'][1]] += 1
            payload_byte2[e['payload'][2]] += 1

    # Group entries by base name → list of (level, payload bytes)
    import re
    lvl_pat = re.compile(r' L([1-9])([A-Z]?)$')
    base_map = {}
    for e in entries:
        m = lvl_pat.search(e['name'])
        if m:
            lvl = int(m.group(1))
            tag = m.group(2)
            base = e['name'][:m.start()]
            base_map.setdefault(base, []).append({
                'level': lvl, 'tag': tag, 'payload': e['payload'], 'offset': e['offset'],
            })

    # See if payload monotonic with level for each base
    monotonic_report = []
    for base, items in sorted(base_map.items()):
        items.sort(key=lambda x: (x['level'], x['tag']))
        b0_seq = [x['payload'][0] for x in items if len(x['payload']) >= 1]
        b1_seq = [x['payload'][1] for x in items if len(x['payload']) >= 2]
        b2_seq = [x['payload'][2] for x in items if len(x['payload']) >= 3]
        monotonic_report.append({
            'base': base,
            'count': len(items),
            'levels': [(x['level'], x['tag']) for x in items],
            'p0_seq': b0_seq,
            'p1_seq': b1_seq,
            'p2_seq': b2_seq,
        })

    out = {
        'meta': {
            'round': 'R106',
            'date': '2026-05-20',
            'source': str(SRC.relative_to(ROOT)),
            'file_size': len(data),
        },
        'header': {
            'hex': header.hex(),
            'le32_first4': header_le32,
        },
        'entry_count': len(entries),
        'consumed_bytes': consumed,
        'trailing_bytes': remaining,
        'trailing_hex': data[consumed:].hex() if remaining else '',
        'payload_len_histogram': pay_sizes,
        'payload_byte_freq': {
            'byte0_top': payload_byte0.most_common(10),
            'byte1_top': payload_byte1.most_common(10),
            'byte2_top': payload_byte2.most_common(10),
        },
        'by_base': monotonic_report,
        'entries': entries,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'=== _ITM_OPTION {len(data)}B ===')
    print(f'header: {header.hex()}  (LE32={header_le32})')
    print(f'entries parsed: {len(entries)}  consumed={consumed}  trailing={remaining}B')
    print(f'payload_len histogram: {pay_sizes}')
    print(f'byte0 top: {payload_byte0.most_common(5)}')
    print(f'byte1 top: {payload_byte1.most_common(5)}')
    print(f'byte2 top: {payload_byte2.most_common(5)}')
    print(f'\nfirst 5 entries:')
    for e in entries[:5]:
        print(f"  [{e['offset']:04x}] size={e['size']:2d} nlen={e['nlen']:2d} name='{e['name']}' payload={e['payload_hex']}")
    print(f'\nlast 3 entries:')
    for e in entries[-3:]:
        print(f"  [{e['offset']:04x}] size={e['size']:2d} nlen={e['nlen']:2d} name='{e['name']}' payload={e['payload_hex']}")
    print(f'\nwrote {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
