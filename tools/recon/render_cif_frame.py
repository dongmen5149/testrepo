"""
Hero3 _cif 프레임 시각 렌더 (placeholder 박스).

ref → BM 매핑이 미해결이므로, cell의 (x_off, y_off, ref) 를 ref 별 색상의 16x16 박스로 캔버스에 그려
4-byte cell layout 가설 (group `0a 02 0b`) 이 휴머노이드 모양인지 시각 검증.

산출: work/h3/h0_cif_R0.png  (96×96 PNG)
"""
from __future__ import annotations
import sys, pathlib
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from analyze_cif import find_frames, parse_cells_4byte


PALETTE = [
    (255, 80, 80), (80, 200, 80), (80, 120, 255), (240, 200, 60),
    (200, 100, 220), (100, 220, 220), (220, 140, 100), (160, 160, 160),
    (255, 255, 120),
]


def render(rec: bytes, out: pathlib.Path, n_cells: int = 9, tile: int = 16,
           canvas: int = 96, label: str = '') -> None:
    cells = parse_cells_4byte(rec, 3, n_cells)
    img = Image.new('RGBA', (canvas, canvas), (32, 32, 40, 255))
    d = ImageDraw.Draw(img, 'RGBA')
    cx, cy = canvas // 2, canvas // 2 + 16
    for c in cells:
        x = cx + c['x']
        y = cy + c['y']
        col = PALETTE[c['idx'] % len(PALETTE)]
        d.rectangle([x - 2, y - 2, x + tile - 2, y + tile - 2],
                    outline=col, width=1, fill=(*col, 80))
        d.text((x, y), str(c['idx']), fill=(255, 255, 255, 255))
    if label:
        d.text((2, 2), label, fill=(255, 255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f'wrote {out}')


def main(argv: list[str]) -> int:
    cif = pathlib.Path(argv[1] if len(argv) > 1 else 'work/extracted/hero/h0_cif')
    data = cif.read_bytes()
    frames = find_frames(data)
    target_leads = ['0a020b', '0a2208', '0a0208', '0a2306']
    out_dir = pathlib.Path('work/h3/cif_render')
    for lead in target_leads:
        for off in frames:
            if data[off:off+3].hex() == lead:
                rec = data[off:off+41]
                render(rec, out_dir / f'{cif.stem}_{lead}_at{off}.png',
                       label=f'{lead} @{off}')
                break
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
