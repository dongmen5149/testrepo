"""
Hero5 팔레트 후보(.bin, len==count*4+1) 시각 검증.

각 후보에 대해 4가지 해석을 한 시트에 나란히 렌더링:
  Row A: RGBA8888  (b0=R b1=G b2=B b3=A)
  Row B: BGRA8888  (b0=B b1=G b2=R b3=A)
  Row C: ARGB8888  (b0=A b1=R b2=G b3=B)
  Row D: RGB565×2  (4바이트를 2개의 LE uint16 RGB565 색으로 — Hero3 _bm 팔레트 같은 형식)

결과:
  work/h5/analysis/pa_swatches/<name>.png  — 1개 후보당 한 이미지
  work/h5/analysis/pa_swatches/_index.html  — 모든 후보 미리보기 그리드
"""
from __future__ import annotations
import pathlib, struct, sys, html
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'pa_swatches'

CELL = 24    # px per color
ROW_H = CELL
PAD = 4
LABEL_W = 90


def is_pa_candidate(data: bytes) -> int:
    if len(data) < 5:
        return 0
    c = data[0]
    if c == 0 or c > 64:
        return 0
    if len(data) != c * 4 + 1:
        return 0
    return c


def rgb565_le(b0: int, b1: int) -> tuple[int, int, int, int]:
    v = b0 | (b1 << 8)
    if v == 0xf81f:
        return (255, 0, 255, 0)
    r = (v >> 11) & 0x1f
    g = (v >> 5) & 0x3f
    b = v & 0x1f
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31, 255)


def render_swatch(name: str, data: bytes, count: int) -> Image.Image:
    rows = ['RGBA', 'BGRA', 'ARGB', 'RGB565x2']
    width = LABEL_W + count * CELL + PAD * 2
    # row D has 2x columns
    width_d = LABEL_W + (count * 2) * (CELL // 2) + PAD * 2
    width = max(width, width_d)
    height = PAD * 2 + len(rows) * (ROW_H + PAD) + 14
    img = Image.new('RGBA', (width, height), (32, 32, 32, 255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', 11)
    except Exception:
        font = ImageFont.load_default()

    d.text((PAD, PAD), name, fill=(220, 220, 220, 255), font=font)
    y0 = PAD + 14

    for ri, label in enumerate(rows):
        y = y0 + ri * (ROW_H + PAD)
        d.text((PAD, y + 6), label, fill=(180, 180, 180, 255), font=font)
        for i in range(count):
            off = 1 + i * 4
            b0, b1, b2, b3 = data[off:off + 4]
            x = LABEL_W + i * CELL
            if label == 'RGBA':
                col = (b0, b1, b2, 255)
            elif label == 'BGRA':
                col = (b2, b1, b0, 255)
            elif label == 'ARGB':
                col = (b1, b2, b3, 255)
            else:  # RGB565x2 — 2 colors per entry
                c1 = rgb565_le(b0, b1)
                c2 = rgb565_le(b2, b3)
                xh = LABEL_W + i * CELL
                d.rectangle([xh, y, xh + CELL // 2 - 1, y + ROW_H - 1], fill=c1)
                d.rectangle([xh + CELL // 2, y, xh + CELL - 1, y + ROW_H - 1], fill=c2)
                continue
            d.rectangle([x, y, x + CELL - 1, y + ROW_H - 1], fill=col)

    return img


def main() -> int:
    candidates = []
    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        c = is_pa_candidate(d)
        if c:
            candidates.append((p, d, c))

    print(f'pa-shaped candidates: {len(candidates)}')
    OUT.mkdir(parents=True, exist_ok=True)

    # sample strategy: take ~64 covering size diversity
    by_size: dict[int, list] = {}
    for p, d, c in candidates:
        by_size.setdefault(c, []).append((p, d, c))
    sample = []
    for cnt, group in sorted(by_size.items()):
        sample.extend(group[:6])  # up to 6 per distinct count
    print(f'rendering {len(sample)} samples covering {len(by_size)} distinct counts: {sorted(by_size)}')

    rendered = []
    for p, d, c in sample:
        img = render_swatch(p.name, d, c)
        out = OUT / (p.stem + '.png')
        img.save(out)
        rendered.append(out.name)

    # index html
    idx = OUT / '_index.html'
    parts = ['<html><head><meta charset="utf-8"><title>Hero5 _pa swatches</title>',
             '<style>body{background:#222;color:#ccc;font:12px sans-serif}',
             'img{display:block;margin:6px 0;background:#000}</style></head><body>',
             f'<h2>Hero5 _pa candidate swatches — {len(rendered)} samples / {len(candidates)} total</h2>',
             '<p>Rows per swatch: RGBA / BGRA / ARGB / RGB565×2.</p>']
    for n in rendered:
        parts.append(f'<div><div>{html.escape(n)}</div><img src="{html.escape(n)}"></div>')
    parts.append('</body></html>')
    idx.write_text('\n'.join(parts), encoding='utf-8')
    print(f'index: {idx}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
