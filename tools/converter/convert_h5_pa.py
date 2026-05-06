"""
Hero5 팔레트 (`uint8 count + count × 4 bytes`) → JSON.

Hero5 인코딩 = **2 × RGB565 LE per entry** (Hero3 의 RGBA 와 다름).
근거: 4-byte entry 에서 byte[0]/byte[2] (low byte) 과 byte[1]/byte[3] (high byte) 의
엔트로피·zero·ff 분포가 짝지어져 있음 → 2개의 LE uint16 패턴.

검증 샘플:
- `b5 63 7a 85` → 0x63b5=(98,119,173) 푸른보라 / 0x857a=(132,175,214) 연파랑
- `00 90 00 a8` → 0x9000=(148,0,0) / 0xa800=(172,0,0) 빨강

사용:
    python convert_h5_pa.py <input.bin> <output.json>
"""
from __future__ import annotations
import json, sys, pathlib


def rgb565_le_to_rgb(b0: int, b1: int) -> tuple[int, int, int]:
    v = b0 | (b1 << 8)
    r = (v >> 11) & 0x1f
    g = (v >> 5) & 0x3f
    b = v & 0x1f
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31)


def parse_h5_palette(data: bytes) -> dict:
    if len(data) < 5:
        raise ValueError('too short')
    count = data[0]
    if count == 0 or len(data) != count * 4 + 1:
        raise ValueError(f'size mismatch: count={count}, expected {count*4+1}, got {len(data)}')
    colors: list[dict] = []
    for i in range(count):
        off = 1 + i * 4
        c1 = rgb565_le_to_rgb(data[off], data[off + 1])
        c2 = rgb565_le_to_rgb(data[off + 2], data[off + 3])
        colors.append({
            'primary':   '#{:02x}{:02x}{:02x}'.format(*c1),
            'secondary': '#{:02x}{:02x}{:02x}'.format(*c2),
        })
    return {'count': count, 'total_colors': count * 2, 'colors': colors}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    out = parse_h5_palette(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({out["count"]} pairs / {out["total_colors"]} colors)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
