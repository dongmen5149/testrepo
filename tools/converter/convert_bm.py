"""
Hero3 _bm → PNG 변환기 (단일 프레임 / frame 0 추출).

검증된 포맷:
    - 15-byte master header
    - 32-byte master palette (RGB565, palette[0] = 0xf81f magenta = 투명색)
    - frame 0 픽셀: 4-bit big-nibble-first packed, width*height pixels

다중 프레임: 첫 프레임만 정확히 추출됨. 이후 프레임은 per-frame 메타데이터로
        오프셋이 변동하여 Ghidra 분석 후 별도 처리 필요.

사용:
    python convert_bm.py <input.bm> <output.png>
"""
from __future__ import annotations
import struct, sys, pathlib
from PIL import Image


PALETTE_OFFSET = 15
FRAME0_PIXEL_OFFSET = 47


def parse_header(data: bytes) -> dict:
    if len(data) < FRAME0_PIXEL_OFFSET:
        raise ValueError(f'too small: {len(data)} bytes')
    return {
        'count': struct.unpack_from('<H', data, 0)[0],
        'flag1': struct.unpack_from('<H', data, 2)[0],
        'type': data[6],
        'width': struct.unpack_from('<H', data, 7)[0],
        'height': struct.unpack_from('<H', data, 9)[0],
        'cell_w': struct.unpack_from('<H', data, 11)[0],
        'cell_h': struct.unpack_from('<H', data, 13)[0],
    }


def rgb565_to_rgba(v: int) -> tuple[int, int, int, int]:
    """0xf81f magenta는 투명 (alpha=0), 나머지는 불투명."""
    if v == 0xf81f:
        return (255, 0, 255, 0)
    r = (v >> 11) & 0x1f
    g = (v >> 5) & 0x3f
    b = v & 0x1f
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31, 255)


def read_palette(data: bytes) -> list[tuple[int, int, int, int]]:
    return [rgb565_to_rgba(struct.unpack_from('<H', data, PALETTE_OFFSET + i*2)[0])
            for i in range(16)]


def render_frame0(data: bytes) -> Image.Image:
    h = parse_header(data)
    palette = read_palette(data)
    w, hh = h['width'], h['height']
    img = Image.new('RGBA', (w, hh), (0, 0, 0, 0))
    pix = img.load()
    pixel_count = w * hh
    body = data[FRAME0_PIXEL_OFFSET:]
    for i in range(pixel_count):
        byte_idx = i // 2
        if byte_idx >= len(body):
            break
        byte = body[byte_idx]
        idx = (byte >> 4) if (i % 2 == 0) else (byte & 0x0f)
        if idx < len(palette):
            x = i % w
            y = i // w
            pix[x, y] = palette[idx]
    return img


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    img = render_frame0(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    h = parse_header(src.read_bytes())
    print(f'  {src.name} -> {dst.name} ({h["width"]}x{h["height"]}, frame0 of {h["count"]})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
