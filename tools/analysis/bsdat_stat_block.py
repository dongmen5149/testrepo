"""BSDAT body = stat block 가설 정밀 검증.

3 BSDAT 파일이 같은 entries (루칸 등) 를 가지므로 같은 entry index 의 body 를 비교하여:
- byte 위치별 값 차이 (전직/등급별?)
- LE16/LE32 stat 후보 식별
"""
from __future__ import annotations
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[2]
E_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'E'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_bsdat_stat_analysis.json'


def is_bsdat_entry(d, i):
    if i + 6 > len(d): return False
    if d[i+1] != 0: return False
    nl = d[i+2]
    if not (3 <= nl <= 30): return False
    if i + 3 + nl > len(d): return False
    first = d[i+3:i+3+min(6, nl)]
    return any(0xa1 <= first[k] <= 0xfe and k+1 < len(first) and 0xa1 <= first[k+1] <= 0xfe
               for k in range(len(first)-1))


def extract_entries(data):
    out = []
    i = 0
    while i < len(data) - 6:
        if not is_bsdat_entry(data, i):
            i += 1
            continue
        nl = data[i+2]
        name = data[i+3:i+3+nl].decode('euc-kr', errors='replace')
        body_start = i + 3 + nl
        nxt = body_start
        while nxt < len(data) - 6:
            if is_bsdat_entry(data, nxt):
                break
            nxt += 1
        else:
            nxt = len(data)
        out.append({'name': name, 'body': data[body_start:nxt]})
        i = nxt
    return out


def fix(s):
    try: return s.encode('latin-1').decode('cp949')
    except: return s


def main():
    files = {}
    for fn in ['_BSDAT_0', '_BSDAT_1', '_BSDAT_2']:
        files[fn] = extract_entries((E_DIR / fn).read_bytes())

    # align by name across 3 files
    names_0 = [e['name'] for e in files['_BSDAT_0']]
    aligned = []
    for idx, nm in enumerate(names_0):
        rec = {'idx': idx, 'name': nm, 'name_fixed': nm}  # already decoded
        for fn in ['_BSDAT_0', '_BSDAT_1', '_BSDAT_2']:
            ent = next((e for e in files[fn] if e['name'] == nm), None)
            if ent:
                rec[f'{fn}_body_len'] = len(ent['body'])
                rec[f'{fn}_body_hex'] = ent['body'].hex()
        aligned.append(rec)

    # cross-file diff analysis for first 5 entries
    diffs = []
    for rec in aligned[:6]:
        bodies = [bytes.fromhex(rec[f'_BSDAT_{k}_body_hex']) for k in range(3)
                  if f'_BSDAT_{k}_body_hex' in rec]
        if len(bodies) < 2:
            continue
        common_len = min(len(b) for b in bodies)
        # byte-pos diffs
        pos_diffs = []
        for p in range(common_len):
            vals = [b[p] for b in bodies]
            if len(set(vals)) > 1:
                pos_diffs.append({'pos': p, 'vals': vals})
        diffs.append({
            'name': rec['name'],
            'lengths': [len(b) for b in bodies],
            'differing_positions': pos_diffs[:20],
            'differing_count': len(pos_diffs),
        })

    # likely LE16 stat candidates: pairs (p, p+1) where p+1 == 0 in majority
    le16_evidence = {'BSDAT_0_first_entry_bytes': aligned[0].get('_BSDAT_0_body_hex', '')}

    out = {
        'meta': {
            'round': 'R76 track B (refined)',
            'hypothesis': 'BSDAT body = boss stat block (not script bytecode)',
            'evidence': '3 BSDAT 파일이 같은 boss 이름을 공유 → tier/difficulty 별 variant 가능성',
        },
        'aligned_entries': aligned,
        'cross_file_diffs': diffs,
        'le16_hints': le16_evidence,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    # Console
    print('=== Cross-BSDAT (_0/_1/_2) entry name alignment ===')
    for rec in aligned[:10]:
        lens = [rec.get(f'_BSDAT_{k}_body_len', '-') for k in range(3)]
        print(f"  idx{rec['idx']:>2} {rec['name']!r:<20} lengths={lens}")

    print('\n=== Byte-position diffs across 3 files (first 6 entries) ===')
    for d in diffs:
        print(f"\n  {d['name']!r} (lengths={d['lengths']}, diffs={d['differing_count']})")
        for pd in d['differing_positions'][:15]:
            print(f"    pos[{pd['pos']:>3}] = {pd['vals']}")

    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
