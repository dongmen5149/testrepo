"""
Hero4 single-frame BM 디코더 (TILE/, OBJ/{000,001,002}/ 공용).

포맷 (TILE 과 OBJ 모두 동일, Ghidra FUN_00010fe4 @ 0x10fe4 분석 결과):
    [type=0x0b 또는 0x0c][w_LE16][h_LE16][cw_LE16][ch_LE16][marker=0x1ff8]
    [palette: 16 × RGB565][pixels]

  - 0x0b: 4-bit big-nibble-first dense (Hero3 _bm 기존 알고리즘)
  - 0x0c: 8-bit dense palette indexed (1 byte = 1 pixel, index 0 = 투명 skip)

multi-frame _bm 와 차이는 file header (6 bytes) 가 없다는 점.

컨테이너 변형 (예: _TILE_030):
    [01 00 00 00][payload_size LE32][위 inner BM ...]
    → 앞 8 bytes 를 stripping 하고 동일 디코더로 처리.
"""
from __future__ import annotations
import struct, sys, pathlib
from PIL import Image


def rgb565_to_rgba(v: int) -> tuple[int, int, int, int]:
    if v == 0xf81f:
        return (255, 0, 255, 0)
    r = (v >> 11) & 0x1f
    g = (v >> 5) & 0x3f
    b = v & 0x1f
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31, 255)


def decode_h4_tile(data: bytes) -> Image.Image | None:
    # 컨테이너 prefix `01 00 00 00 <size LE32>` 감지 → inner 로 재진입
    if len(data) >= 8 and data[:4] == b'\x01\x00\x00\x00':
        payload_size = struct.unpack_from('<I', data, 4)[0]
        if 8 + payload_size <= len(data) and len(data) - 8 >= 11 + 32:
            inner = data[8:8 + payload_size]
            if inner and inner[0] in (0x0b, 0x0c):
                data = inner
    if len(data) < 11 + 32:
        return None
    type_b = data[0]
    if type_b not in (0x0b, 0x0c):
        return None
    if struct.unpack_from('<H', data, 9)[0] != 0xf81f:
        return None
    w, h = struct.unpack_from('<HH', data, 1)
    palette = [rgb565_to_rgba(struct.unpack_from('<H', data, 11 + i*2)[0]) for i in range(16)]
    pix = data[11 + 32:]
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    pmap = img.load()
    n = w * h

    if type_b == 0x0c:
        # 8-bit dense palette indexed (1 byte = 1 pixel, index 0 = 투명 skip)
        # FUN_00010fe4 line 4847-4851: read 1 byte/pixel, if !=0 lookup palette[byte]
        for i in range(n):
            if i >= len(pix):
                break
            idx = pix[i]
            if idx == 0:
                continue
            if idx < len(palette):
                pmap[i % w, i // w] = palette[idx]
    else:
        # 0x0b dense 4-bit big-nibble-first
        for i in range(n):
            bi = i // 2
            if bi >= len(pix):
                break
            b = pix[bi]
            idx = (b >> 4) if (i % 2 == 0) else (b & 0x0f)
            pmap[i % w, i // w] = palette[idx]
    return img


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    img = decode_h4_tile(src.read_bytes())
    if img is None:
        print(f'  SKIP {src.name}: not a single-frame 0x0c TILE')
        return 1
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst)
    print(f'  {src.name} -> {dst.name} ({img.size})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
