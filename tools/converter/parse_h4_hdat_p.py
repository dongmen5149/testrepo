"""Hero4 HDAT Group B (`_H_P000`~`P005`) parser.

2026-05-18 발견 layout:

    File = [3B header] [N × 50B entries]

    Header (3 bytes):
        byte 0 : group_type  (0=P000, 1=P005, 2=P004, 3=P001~P003)
        byte 1 : 0x00
        byte 2 : 0x00

    Entry (50 bytes):
        offset 0..15 (16B): 8 × uint16 LE — prominent progression values
            val[0]: small (5, 10, 15, 20, 50)         — level / rank / count
            val[1]: medium (300, 500, 1000)           — HP / cost / stat1
            val[2]: 0 always                          — reserved/padding
            val[3]: 400~2000                           — stat2
            val[4]: 0 always                          — reserved/padding
            val[5]: 100~20000                          — large value (gold/EXP)
            val[6]: 800~1500                           — atk / def
            val[7]: 1000~2000                          — hp_max / cap
        byte 16 (1B): marker (0xff in 11/13 entries, 0x00 in special)
        bytes 17..21 (5B): param block (b4 f4 c8 32 f4 형식, 정확한 의미 미정)
        bytes 22..49 (28B): tail u16 sub-records (대부분 0, 일부 nested pairs)

검증: P000(1ent), P001-3(2ent), P004(3ent), P005(2ent) 모두 `3 + 50N` byte size 정확히 일치.

게임 wiring 단계에서 정확한 field 명명 (HP vs 스킬 cost vs 가격) 은 Phase B
Ghidra 분석 필요. 현재는 raw values 만 보존.
"""
from __future__ import annotations
import argparse, glob, json, os, pathlib, struct, sys


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
HDAT_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'HDAT'
OUT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'hdat_p_parsed.json'


def parse_entry(data: bytes) -> dict:
    """50B entry."""
    if len(data) != 50:
        return {'error': f'wrong_size={len(data)}'}
    main = list(struct.unpack_from('<8H', data, 0))
    marker = data[16]
    params = list(data[17:22])  # 5B
    tail_u16 = list(struct.unpack_from('<14H', data, 22))  # 28B as 14 × u16
    return {
        'main_values': main,
        'marker': marker,
        'param_bytes': params,
        'tail_u16': tail_u16,
    }


def parse_file(path: pathlib.Path) -> dict:
    d = path.read_bytes()
    result = {'file': path.name, 'size': len(d)}
    if len(d) < 3 or (len(d) - 3) % 50 != 0:
        result['error'] = 'size_not_aligned'
        return result
    n = (len(d) - 3) // 50
    result['group_type'] = d[0]
    result['header_bytes12'] = list(d[1:3])
    result['entries_count'] = n
    result['entries'] = []
    for i in range(n):
        off = 3 + i * 50
        ent = parse_entry(d[off:off+50])
        result['entries'].append(ent)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=str(OUT_JSON))
    args = ap.parse_args()

    files = sorted(HDAT_DIR.glob('_H_P00?'))  # P000..P009
    parsed = []
    for fp in files:
        r = parse_file(fp)
        parsed.append(r)

    out = {
        'files': len(parsed),
        'parsed': parsed,
    }
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print(f'Parsed {len(parsed)} HDAT Group B files. Wrote {args.out}')

    print('\n=== Summary ===')
    for p in parsed:
        if 'error' in p:
            print(f'  {p["file"]}: ERROR ({p["error"]})')
            continue
        print(f'  {p["file"]}: group={p["group_type"]} entries={p["entries_count"]}')
        for i, e in enumerate(p['entries']):
            print(f'    [{i}] main={e["main_values"]}  mk=0x{e["marker"]:02x}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
