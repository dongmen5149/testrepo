"""Hero4 HDAT/_H_PS* 파서 (캐릭터 클래스 progression).

2026-05-14 [tools/recon/analyze_hdat_ps.py](../recon/analyze_hdat_ps.py) 의 통계 분석으로
PS000-007 의 entry layout 추론 완료. PS008 은 별도 schema (보존만).

Schema A (PS000-007, 70 bytes):
    Header (10 bytes):
        0..5: 06 00 01 02 03 04           ← 고정 signature
        6   : <class> (1..4)              ← 워리어/마법/도적/궁수
        7..9: 01 01 06                    ← 고정

    6 records × 10 bytes:
        0   : <marker> (보통 0x01)
        1   : <type_code> (보통 0x85, PS003 R4-R5 만 0xa5)
        2   : <param_a>                   ← 캐릭터별 고정 (weapon/skill ID 추정)
        3..4: <flags>
        5,6 : <stat_pair> (보통 동일)     ← 레벨별 능력치
        7   : <extra>
        8   : <curve>                     ← progression curve (ff/dc/c8 등 plateau)
        9   : <terminator> (보통 0x1c)

Schema B (PS008, 69 bytes): 별도 entity, 보존만.

사용:
    python convert_h4_hdat_ps.py        ← work/h4/extracted/HDAT/_H_PS* → work/h4/converted/HDAT/ps.json
"""
from __future__ import annotations
import json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402


CLASS_NAMES = {
    1: 'warrior',
    2: 'mage',
    3: 'rogue',
    4: 'archer',
}


def parse_schema_a(data: bytes, name: str) -> dict:
    """PS000-007 schema (70 bytes)."""
    if len(data) != 70:
        raise ValueError(f'{name}: schema A expects 70 bytes, got {len(data)}')
    header = {
        'signature': data[0:6].hex(),
        'class_id': data[6],
        'class_name': CLASS_NAMES.get(data[6], f'class_{data[6]}'),
        'trailer': data[7:10].hex(),
    }
    records = []
    for i in range(6):
        r = data[10 + i*10 : 10 + (i+1)*10]
        records.append({
            'index': i,
            'marker': r[0],
            'type_code': r[1],
            'param_a': r[2],
            'flags': [r[3], r[4]],
            'stat_pair': [r[5], r[6]],
            'extra': r[7],
            'curve': r[8],
            'terminator': r[9],
            'raw_hex': r.hex(),
        })
    return {
        'schema': 'A',
        'header': header,
        'records': records,
    }


def parse_schema_b(data: bytes, name: str) -> dict:
    """PS008 schema (69 bytes) — 별도 entity, 보존만."""
    return {
        'schema': 'B',
        'note': 'distinct entity (boss/pet/vehicle?) — entry layout TBD in Phase B',
        'header_hex': data[:10].hex(),
        'class_id_byte': data[6],
        'size': len(data),
        'raw_hex': data.hex(),
    }


def main():
    g = select('h4')
    src = g.extracted_root / 'HDAT'
    dst = g.converted_root / 'HDAT'
    dst.mkdir(parents=True, exist_ok=True)

    files = sorted(src.glob('_H_PS*'))
    if not files:
        print(f'No _H_PS* under {src}', file=sys.stderr)
        return 1

    result = {}
    for f in files:
        data = f.read_bytes()
        if len(data) == 70:
            result[f.name] = parse_schema_a(data, f.name)
        elif len(data) == 69:
            result[f.name] = parse_schema_b(data, f.name)
        else:
            result[f.name] = {'schema': 'unknown', 'size': len(data), 'raw_hex': data.hex()}

    out = dst / 'ps.json'
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Wrote {len(result)} PS records → {out}')

    # Summary
    schema_a = [n for n, r in result.items() if r['schema'] == 'A']
    schema_b = [n for n, r in result.items() if r['schema'] == 'B']
    print(f'  Schema A: {len(schema_a)} ({", ".join(schema_a)})')
    print(f'  Schema B: {len(schema_b)} ({", ".join(schema_b)})')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
