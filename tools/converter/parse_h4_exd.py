"""Hero4 _EXD 캐릭터 데이터 parser (단순 count=1 케이스 확정 분).

2026-05-18 발견 layout:

    Header (8 byte):
        byte 0 : count       (number of "frames" / entries)
        byte 1 : 0x00
        byte 2 : 0x01
        byte 3 : 0x00
        byte 4 : 0x01
        byte 5 : subtype     (1, 2, or 3 — entry layout discriminator)
        byte 6 : 0x00
        byte 7 : 0x00

    Payload (count=1 entry types):

        subtype=1: variable (2/3/7 byte). 14 files. 미정 (sentinel / footer).
        subtype=2: 12 byte = 4B head + 1×8B box
            head: 00 ?? ff 01
            box : LE int16 dx, dy, w, h  (signed)
        subtype=3: 21 byte = 4B head + box1(8) + sep_byte(0x02) + box2(8)
            head: 00 ?? ff 01
            box1: dx,dy,w,h — collision/feet box (~14×9 around feet)
            box2: dx,dy,w,h — sprite/body bounding box (~12×25 vertical)

    Payload (count>1):
        First entry follows subtype=3 layout (21B). Subsequent entries variable,
        with 0x03 box separators. Phase B 까지 보류.

CIF 와 페어 (117 캐릭터). subtype 별 분포:
    subtype=1: 5 files (count=1)
    subtype=2: 14 files (count=1)
    subtype=3: 26 files (count=1) + 71 files (count>1)
"""
from __future__ import annotations
import argparse, glob, json, os, pathlib, struct, sys
from collections import defaultdict


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXD_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'H4' / 'EXD'
OUT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'exd_parsed.json'


def parse_header(d: bytes) -> dict | None:
    if len(d) < 8:
        return None
    return {
        'count': d[0],
        'subtype': d[5],
        'header_check': d[1] == 0 and d[2] == 1 and d[3] == 0 and d[4] == 1
                        and d[6] == 0 and d[7] == 0,
        'header_hex': d[:8].hex(),
    }


def parse_box(data: bytes, off: int) -> dict | None:
    if off + 8 > len(data):
        return None
    dx, dy, w, h = struct.unpack_from('<hhhh', data, off)
    return {'dx': dx, 'dy': dy, 'w': w, 'h': h}


def parse_subtype2_entry(payload: bytes) -> dict | None:
    """4B head + 1×8B box. Total 12B."""
    if len(payload) != 12:
        return None
    return {
        'kind': 'subtype2',
        'head_byte0': payload[0],
        'sprite_id': payload[1],
        'marker_byte2': payload[2],
        'flag_byte3': payload[3],
        'box': parse_box(payload, 4),
    }


def parse_subtype3_entry(payload: bytes) -> dict | None:
    """4B head + box1 + 1B sep(0x02) + box2. Total 21B."""
    if len(payload) != 21:
        return None
    if payload[12] != 0x02:
        return None
    return {
        'kind': 'subtype3',
        'head_byte0': payload[0],
        'sprite_id': payload[1],
        'marker_byte2': payload[2],
        'flag_byte3': payload[3],
        'box1': parse_box(payload, 4),  # collision/feet
        'sep_byte': payload[12],
        'box2': parse_box(payload, 13),  # body/sprite
    }


def parse_subtype1_entry(payload: bytes) -> dict:
    """Variable length (2/3/7). Pass through raw."""
    return {'kind': 'subtype1_raw', 'size': len(payload), 'hex': payload.hex()}


def parse_multi(payload: bytes, count: int) -> dict:
    """count > 1 multi-entry: parse first 21B as subtype3, rest pass-through."""
    out = {'kind': 'multi', 'count': count, 'first_entry': None, 'rest_hex': ''}
    if len(payload) >= 21 and payload[0] == 0x00 and payload[2] == 0xff and payload[12] == 0x02:
        out['first_entry'] = parse_subtype3_entry(payload[:21])
    out['rest_hex'] = payload[21:].hex() if len(payload) > 21 else ''
    return out


def parse_file(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    result = {'file': path.name, 'size': len(data)}
    hdr = parse_header(data)
    if hdr is None:
        result['error'] = 'too_short'
        return result
    result['header'] = hdr
    payload = data[8:]
    result['payload_size'] = len(payload)

    if hdr['count'] == 1:
        if hdr['subtype'] == 1:
            result['entry'] = parse_subtype1_entry(payload)
        elif hdr['subtype'] == 2:
            result['entry'] = parse_subtype2_entry(payload)
        elif hdr['subtype'] == 3:
            result['entry'] = parse_subtype3_entry(payload)
        else:
            result['entry'] = {'kind': f'subtype{hdr["subtype"]}_unknown', 'hex': payload.hex()}
    else:
        result['entries'] = parse_multi(payload, hdr['count'])
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=str(OUT_JSON))
    args = ap.parse_args()

    files = sorted(EXD_DIR.glob('*_EXD'))
    parsed = []
    summary = defaultdict(int)
    for f in files:
        r = parse_file(f)
        parsed.append(r)
        if 'header' in r:
            key = f'count={r["header"]["count"]} subtype={r["header"]["subtype"]}'
            summary[key] += 1

    out = {
        'files': len(parsed),
        'summary': dict(summary),
        'parsed': parsed,
    }
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    # Summary stdout
    print(f'Parsed {len(parsed)} _EXD files. Wrote {args.out}')
    print(f'\nDistribution:')
    for k, v in sorted(summary.items()):
        print(f'  {k}: {v}')

    # Quality check: how many have header_check=True
    good = sum(1 for p in parsed if p.get('header', {}).get('header_check'))
    print(f'\nHeader check pass: {good}/{len(parsed)}')

    # Show full parse of a few examples
    print(f'\n=== Sample parses ===')
    for sub in [1, 2, 3]:
        for p in parsed:
            if p.get('header', {}).get('count') == 1 and p.get('header', {}).get('subtype') == sub:
                print(f'\n{p["file"]} (count=1, subtype={sub}, {p["size"]}B):')
                print(json.dumps(p, indent=2, ensure_ascii=False))
                break

    return 0


if __name__ == '__main__':
    sys.exit(main())
