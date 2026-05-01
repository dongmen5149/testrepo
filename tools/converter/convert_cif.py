"""
Hero3 _cif → JSON 메타데이터 (부분 파싱).

확정된 부분:
    uint16 slot_count                       // 0..1
    uint8  sprite_indices[slot_count]       // 2..2+count
    bytes  animation_data[]                 // 나머지 (포맷 미확정)

slot_count + indices 만으로도 캐릭터 시스템의 키프레임 매핑을 알 수 있음.
animation_data 의 timing/event 디코딩은 추가 분석 필요 (보류).

사용:
    python convert_cif.py <input.cif> <output.json>
"""
from __future__ import annotations
import struct, sys, json, pathlib


def parse_cif(data: bytes) -> dict:
    if len(data) < 2:
        return {'slot_count': 0, 'indices': [], 'raw_size': len(data)}
    slot_count = struct.unpack_from('<H', data, 0)[0]
    indices_bytes = data[2:2 + slot_count] if slot_count + 2 <= len(data) else data[2:]
    indices = list(indices_bytes)
    rest = data[2 + slot_count:] if 2 + slot_count <= len(data) else b''
    return {
        'slot_count': slot_count,
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
