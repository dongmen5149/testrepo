"""
Hero3 _pa 팔레트 → JSON.

포맷:
    uint8  count
    uint32 colors[count]   # 추정 RGBA8888 또는 BGRA8888

검증: len(file) == count * 4 + 1.
"""
from __future__ import annotations
import struct, sys, json, pathlib


def parse_palette(data: bytes) -> list[dict]:
    count = data[0]
    expected = count * 4 + 1
    if expected != len(data):
        raise ValueError(f'size mismatch: count={count} expected={expected} actual={len(data)}')
    colors = []
    for i in range(count):
        b0, b1, b2, b3 = data[1 + i*4 : 1 + i*4 + 4]
        colors.append({
            'rgba_be': f'#{b0:02x}{b1:02x}{b2:02x}{b3:02x}',
            'argb_le': f'#{b3:02x}{b2:02x}{b1:02x}{b0:02x}',
            'bytes': [b0, b1, b2, b3],
        })
    return colors


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    colors = parse_palette(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps({'count': len(colors), 'colors': colors}, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({len(colors)} colors)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
