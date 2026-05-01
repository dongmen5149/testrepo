"""
Hero3 _mp → JSON tilemap.

확정된 포맷:
    uint8 version              // 0x02 또는 0x03
    bytes meta[hdr_size-1]     // version 0x02: 4바이트, 0x03: 5바이트 추가 (의미 미확정)
    uint8 name_length
    char  name[name_length]    // ASCII (예: "NEOSOLTIA", "SMALL_FACTORY_4")
    uint8 nul                  // 0x00
    uint8 width
    uint8 height
    uint8 palette_count
    uint8 meta4
    uint8 palette[palette_count]   // 사용된 tile ID 목록
    bytes grid_data[]              // 다중 layer (2 layers × W*H 바이트 + extras)
                                   //   layer 0: terrain (varied IDs)
                                   //   layer 1: objects/collision (few IDs)
                                   //   extras:  events/exits/NPCs (포맷 미확정)

사용:
    python convert_mp.py <input.mp> <output.json>
"""
from __future__ import annotations
import struct, sys, json, pathlib


def parse_mp(data: bytes) -> dict:
    if len(data) < 10:
        raise ValueError(f'too small: {len(data)} bytes')
    version = data[0]
    if version == 0x02:
        hdr_size = 5
    elif version == 0x03:
        hdr_size = 6
    else:
        raise ValueError(f'unknown version {version:#x}')

    name_len = data[hdr_size]
    name_start = hdr_size + 1
    name_end = name_start + name_len
    if name_end >= len(data):
        raise ValueError('name overflow')
    name = data[name_start:name_end].decode('ascii', errors='replace')
    if data[name_end] != 0:
        raise ValueError(f'missing NUL after name @ {name_end}')

    pos = name_end + 1
    width = data[pos]; pos += 1
    height = data[pos]; pos += 1
    pal_count = data[pos]; pos += 1
    meta4 = data[pos]; pos += 1
    palette = list(data[pos:pos + pal_count])
    pos += pal_count

    grid_start = pos
    cell_count = width * height
    layer0 = list(data[grid_start:grid_start + cell_count])
    layer1 = list(data[grid_start + cell_count:grid_start + 2 * cell_count])
    extras_start = grid_start + 2 * cell_count
    extras = list(data[extras_start:]) if extras_start < len(data) else []

    return {
        'version': version,
        'meta_header_hex': data[1:hdr_size].hex(),
        'name': name,
        'width': width,
        'height': height,
        'palette_count': pal_count,
        'meta4': meta4,
        'palette': palette,
        'layer_0': layer0,
        'layer_1': layer1,
        'extras_size': len(extras),
        'extras_hex_preview': bytes(extras[:64]).hex(),
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    info = parse_mp(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(info, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({info["name"]} {info["width"]}x{info["height"]})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
