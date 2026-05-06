"""
Hero5 sprite frame payload 내부 구조 분석 + 시각 디코딩 시도.

Outer: u32 count + (u32 frame_len + frame_payload)*  — 검증 완료.
Frame payload (가설):
    u8  type     (0x14 / 0x18)
    u8  variant  (0x01..0x0f, 0xd8 등)
    u16 width  LE
    u16 height LE
    ... pixels (인코딩은 type/variant 에 따라 다름)

각 sprite-like 파일의 모든 frame 에 대해:
  - bytes_per_pixel = (frame_len - 6) / (w*h)  계산해서 인코딩 후보 추정
  - bpp 카테고리별 빈도 집계 → 인코딩 분기점 찾기
  - 샘플 4 frame 을 RGB565-direct 와 4bit-indexed-with-embedded-palette 두 가지로 시도해 PNG 출력

산출: work/h5/analysis/frames/{magic}/{file}/frame_NN_{strategy}.png
       work/h5/analysis/frame_bpp_distribution.txt
"""
from __future__ import annotations
import sys, struct, pathlib, collections
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'frames'


def is_sprite_like(d: bytes) -> bool:
    if len(d) < 14: return False
    if d[8] not in (0x14, 0x18): return False
    cnt = struct.unpack_from('<I', d, 0)[0]
    return 0 < cnt <= 64


def walk_frames(d: bytes):
    cnt = struct.unpack_from('<I', d, 0)[0]
    pos = 4
    for i in range(cnt):
        if pos + 4 > len(d): return
        ln = struct.unpack_from('<I', d, pos)[0]
        if pos + 4 + ln > len(d): return
        payload = d[pos+4:pos+4+ln]
        if len(payload) >= 6:
            t, var = payload[0], payload[1]
            w = struct.unpack_from('<H', payload, 2)[0]
            h = struct.unpack_from('<H', payload, 4)[0]
            yield i, t, var, w, h, payload[6:]
        pos += 4 + ln


def rgb565(b0, b1):
    v = b0 | (b1 << 8)
    if v == 0xf81f: return (255, 0, 255, 0)
    return ((v >> 11 & 0x1f) * 255 // 31,
            (v >> 5 & 0x3f) * 255 // 63,
            (v & 0x1f) * 255 // 31, 255)


def render_rgb565_direct(pixels: bytes, w: int, h: int) -> Image.Image | None:
    need = w * h * 2
    if len(pixels) < need: return None
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    for i in range(w * h):
        px[i % w, i // w] = rgb565(pixels[i*2], pixels[i*2+1])
    return img


def render_4bit_with_pal(pixels: bytes, w: int, h: int, pal_count: int = 16) -> Image.Image | None:
    """앞 pal_count*2 bytes = RGB565 LE palette, 이어서 4-bit packed pixels (high nibble first)."""
    pal_bytes = pal_count * 2
    if len(pixels) < pal_bytes: return None
    palette = [rgb565(pixels[i*2], pixels[i*2+1]) for i in range(pal_count)]
    pixel_data = pixels[pal_bytes:]
    need = (w * h + 1) // 2
    if len(pixel_data) < need: return None
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    for i in range(w * h):
        b = pixel_data[i // 2]
        idx = (b >> 4) if (i & 1) == 0 else (b & 0xf)
        px[i % w, i // w] = palette[idx] if idx < pal_count else (255, 0, 255, 255)
    return img


def main() -> int:
    target_magics = ['07000000', '0d000000', '04000000', '11000000', '0c000000', '06000000']
    OUT.mkdir(parents=True, exist_ok=True)

    bpp_dist: collections.Counter = collections.Counter()  # rounded to 0.1
    type_var: collections.Counter = collections.Counter()

    rendered = 0
    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        if not is_sprite_like(d): continue
        magic = d[:4].hex()
        if magic not in target_magics: continue

        for idx, t, var, w, h, pixels in walk_frames(d):
            if w == 0 or h == 0: continue
            bpp = len(pixels) * 8 / (w * h)
            bpp_dist[round(bpp * 2) / 2] += 1
            type_var[(f'{t:02x}', f'{var:02x}', round(bpp))] += 1

        # render samples — first 4 frames of first 2 files per magic
        magic_files_seen = sum(1 for _ in (OUT / magic).glob('*')) if (OUT / magic).exists() else 0
        if magic_files_seen >= 2: continue

        out_dir = OUT / magic / p.stem
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, t, var, w, h, pixels in walk_frames(d):
            if idx >= 4: break
            if w == 0 or h == 0: continue
            tag = f'frame{idx:02d}_t{t:02x}_v{var:02x}_{w}x{h}'
            # try RGB565 direct
            im_rgb = render_rgb565_direct(pixels, w, h)
            if im_rgb:
                im_rgb.resize((w*4, h*4), Image.NEAREST).save(out_dir / f'{tag}_rgb565.png')
                rendered += 1
            # try 4-bit indexed + 16-color embedded palette
            im_4 = render_4bit_with_pal(pixels, w, h, 16)
            if im_4:
                im_4.resize((w*4, h*4), Image.NEAREST).save(out_dir / f'{tag}_4bit16pal.png')
                rendered += 1

    # write bpp distribution
    rep = OUT.parent / 'frame_bpp_distribution.txt'
    with open(rep, 'w', encoding='utf-8') as f:
        total = sum(bpp_dist.values())
        f.write(f'total frames analyzed: {total}\n\nbpp distribution (rounded to 0.5):\n')
        for k, v in sorted(bpp_dist.items()):
            bar = '#' * int(80 * v / total)
            f.write(f'  {k:5.1f}  {v:6d}  {bar}\n')
        f.write(f'\ntop 30 (type, variant, round(bpp)) combinations:\n')
        for k, v in type_var.most_common(30):
            f.write(f'  type={k[0]} var={k[1]} bpp~={k[2]}  {v}\n')

    print(f'rendered {rendered} sample images')
    print(f'report: {rep}')
    print(open(rep, encoding='utf-8').read()[:2000])
    return 0


if __name__ == '__main__':
    sys.exit(main())
