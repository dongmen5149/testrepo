"""
Hero3 _cif → JSON 메타데이터 (부분 파싱).

2026-05-04 헤더 재해석:
    uint8  slot_count          // 0..8 (hero/boss=8, enemy=0~7)
    uint8  type_or_category    // 0=hero/boss, 1=enemy 추정
    uint8  sprite_indices[slot_count]
    bytes  animation_data[]    // 미해독 (timing/event)

`19 19` 패턴이 76% 파일에 존재 → frame size 마커.
animation_data 의 정확한 record 구조는 Ghidra 분석 필요 (보류).

사용:
    python convert_cif.py <input.cif> <output.json>
"""
from __future__ import annotations
import struct, sys, json, pathlib


def parse_cif(data: bytes) -> dict:
    if len(data) < 2:
        return {'slot_count': 0, 'category': 0, 'indices': [], 'raw_size': len(data)}
    slot_count = data[0]
    category = data[1]
    end = 2 + slot_count
    indices_bytes = data[2:end] if end <= len(data) else data[2:]
    indices = list(indices_bytes)
    rest = data[end:] if end <= len(data) else b''
    return {
        'slot_count': slot_count,
        'category': category,
        'indices': indices,
        'animation_data_size': len(rest),
        'animation_data_hex_preview': rest[:32].hex() if rest else '',
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    out = parse_cif(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} (slots={out["slot_count"]}, indices={out["indices"]})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
