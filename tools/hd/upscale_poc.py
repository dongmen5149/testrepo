"""HD 리마스터 PoC.

3가지 업스케일 알고리즘 비교:
    1. Nearest-neighbor 4× (pure pixel-art look, baseline)
    2. Lanczos 4× (Pillow built-in, smooth)
    3. Scale2x × 2 (pixel-art preserving, deterministic)

추후 Real-ESRGAN-anime 추가 가능.
"""
from __future__ import annotations
import pathlib, sys
from PIL import Image

CONVERTED = pathlib.Path(__file__).parent.parent.parent / 'work' / 'converted'
OUT = pathlib.Path(__file__).parent.parent.parent / 'work' / 'hd_poc'
OUT.mkdir(exist_ok=True)


def scale2x(img: Image.Image) -> Image.Image:
    """Eric Johnston's Scale2x algorithm — pixel-art preserving 2× upscale."""
    w, h = img.size
    src = img.convert('RGBA').load()
    dst = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    dpix = dst.load()
    for y in range(h):
        for x in range(w):
            P = src[x, y]
            A = src[x, y - 1] if y > 0 else P
            B = src[x + 1, y] if x < w - 1 else P
            C = src[x, y + 1] if y < h - 1 else P
            D = src[x - 1, y] if x > 0 else P
            E0, E1, E2, E3 = P, P, P, P
            if A != C and D != B:
                if D == A: E0 = A
                if A == B: E1 = B
                if D == C: E2 = D
                if C == B: E3 = C
            dpix[x*2, y*2] = E0
            dpix[x*2 + 1, y*2] = E1
            dpix[x*2, y*2 + 1] = E2
            dpix[x*2 + 1, y*2 + 1] = E3
    return dst


def scale4x(img: Image.Image) -> Image.Image:
    return scale2x(scale2x(img))


def upscale_methods(img: Image.Image) -> dict[str, Image.Image]:
    w, h = img.size
    return {
        'nearest_4x': img.resize((w * 4, h * 4), Image.NEAREST),
        'lanczos_4x': img.resize((w * 4, h * 4), Image.LANCZOS),
        'scale4x': scale4x(img),
    }


# 비교 캔버스 만들기 (원본 + 3가지 변환 결과 가로 배치)
def comparison_canvas(name: str, img: Image.Image, results: dict) -> Image.Image:
    pad = 8
    label_h = 14
    nearest = results['nearest_4x']
    items = [('original', img.resize((nearest.width, nearest.height), Image.NEAREST))] + list(results.items())
    item_w = nearest.width + pad
    item_h = nearest.height + pad + label_h
    canvas_w = item_w * len(items) + pad
    canvas_h = item_h + pad
    canvas = Image.new('RGBA', (canvas_w, canvas_h), (40, 40, 50, 255))
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(canvas)
    for i, (label, im) in enumerate(items):
        x = pad + i * item_w
        y = pad + label_h
        canvas.paste(im, (x, y), im if im.mode == 'RGBA' else None)
        draw.text((x, pad), f'{label}', fill=(220, 220, 220))
    return canvas


targets = [
    'boss/boss9000_bm/frame_00_22x32_tb.png',
    'boss/boss9000_bm/frame_01_42x58_tb.png',
    'enemy/e1011_bm/frame_00_18x18_tb.png',
    'comm/number_bm/frame_00_200x20_tb.png',
    'menu/menu_bm/frame_00_240x320_tb.png' if (CONVERTED / 'menu/menu_bm/frame_00_240x320_tb.png').exists() else None,
]

for t in targets:
    if not t:
        continue
    src = CONVERTED / t
    if not src.exists():
        print(f'MISSING: {t}')
        continue
    img = Image.open(src).convert('RGBA')
    print(f'{t}: {img.size}')
    results = upscale_methods(img)
    out_dir = OUT / pathlib.Path(t).parent.name
    out_dir.mkdir(parents=True, exist_ok=True)
    base = pathlib.Path(t).stem
    for label, im in results.items():
        im.save(out_dir / f'{base}_{label}.png')
    canvas = comparison_canvas(base, img, results)
    canvas.save(out_dir / f'{base}_compare.png')
    print(f'  → {out_dir / (base + "_compare.png")}')

print(f'\nResults: {OUT}')
