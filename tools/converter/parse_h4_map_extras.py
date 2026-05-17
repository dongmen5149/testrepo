"""Hero4 _MAP_M_ extras 영역 partial parser.

2026-05-18 발견:
    extras = 4~8 개의 section 으로 분해 가능
    각 section = `1B count + N × 8B records`
    8B record = type(1) + sub-data(3) + x(2 LE) + y(2 LE)

distribution:
    4 sections: 28 files
    5 sections: 48 files
    6 sections: 15 files
    7 sections: 4 files
    8 sections: 2 files

97 / 97 파일에서 첫 section 의 `1B count + N×8B` fits. 13 / 97 은 완전 소비,
나머지 84 / 97 은 1~40B 의 trailing data (variable-length tail section 추정).

Section 별 의미 추정 (확정 미정, Ghidra 후 명명):
    sec 0: 가장 큰 count (50~200) — terrain/NPC layout 또는 spawn 위치
    sec 1+: 작은 count (10~50) — exit/event/trigger 등 sub-category
"""
from __future__ import annotations
import argparse, glob, json, os, pathlib, struct, sys
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MAP_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'M'
OUT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'map_extras_parsed.json'

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from convert_h4_map import parse_h4_map  # noqa: E402


def get_extras_offset(d: bytes):
    p = parse_h4_map(d)
    if not p:
        return None, None
    v = p['version']
    pos = 1 + 2 * v
    nlen1 = d[pos]
    pos += 1 + nlen1
    nlen2 = d[pos]
    pos += 1 + nlen2 + 1  # +1 trailing NUL
    w = p['width']; h = p['height']; pc = p['palette_count']
    pos += 4 + pc + 2 * w * h
    return pos, p


def parse_record(rec: bytes) -> dict:
    """8-byte record: type(1) + sub_data(3) + x(LE16) + y(LE16)."""
    return {
        'type': rec[0],
        'sub': [rec[1], rec[2], rec[3]],
        'x': struct.unpack_from('<H', rec, 4)[0],
        'y': struct.unpack_from('<H', rec, 6)[0],
    }


def parse_extras(extras: bytes) -> dict:
    """Greedy 1B count + N×8B sections until exhausted or fails."""
    pos = 0
    sections = []
    while pos < len(extras):
        if pos + 1 > len(extras):
            break
        n = extras[pos]
        block_end = pos + 1 + 8 * n
        if block_end > len(extras):
            break
        records = [parse_record(extras[pos+1+8*i:pos+1+8*(i+1)]) for i in range(n)]
        sections.append({
            'count': n,
            'records': records,
        })
        pos = block_end
    tail = extras[pos:]
    return {
        'sections': sections,
        'tail_size': len(tail),
        'tail_hex': tail.hex(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=str(OUT_JSON))
    args = ap.parse_args()

    files = sorted(MAP_DIR.glob('_MAP_M_*'))
    parsed = []
    sec_counts = Counter()
    fully = 0

    for fp in files:
        d = fp.read_bytes()
        off, p = get_extras_offset(d)
        if off is None:
            continue
        extras = d[off:]
        if not extras:
            continue
        result = parse_extras(extras)
        result['file'] = fp.name
        result['zone'] = p['name']
        result['place'] = p['place']
        result['size'] = p['width'] * p['height']
        result['extras_size'] = len(extras)
        sec_counts[len(result['sections'])] += 1
        if result['tail_size'] == 0:
            fully += 1
        parsed.append(result)

    out = {
        'files': len(parsed),
        'fully_consumed': fully,
        'section_count_distribution': dict(sec_counts),
        'parsed': parsed,
    }
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    print(f'Parsed {len(parsed)} _MAP_M_ files. Wrote {args.out}')
    print(f'Fully consumed (no tail): {fully} / {len(parsed)}')
    print(f'\nSection count distribution:')
    for k, v in sorted(sec_counts.items()):
        print(f'  {k} sections: {v} files')

    # Sample _MAP_M_000
    sample = next((r for r in parsed if r['file'] == '_MAP_M_000'), None)
    if sample:
        print(f'\n=== _MAP_M_000 ({sample["zone"]}/{sample["place"]}) ===')
        print(f'extras={sample["extras_size"]}B, {len(sample["sections"])} sections, tail={sample["tail_size"]}B')
        for i, sec in enumerate(sample['sections']):
            print(f'  sec[{i}]: {sec["count"]} records')
            for j, rec in enumerate(sec['records'][:3]):
                print(f'    rec[{j}]: type={rec["type"]} sub={rec["sub"]} pos=({rec["x"]},{rec["y"]})')

    return 0


if __name__ == '__main__':
    sys.exit(main())
