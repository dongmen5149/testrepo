"""
Hero3 _cif 프레임 실제 BM 합성 렌더 (가설 검증).

가설: cell.ref 는 h1XXXX_bm 글로벌 cumulative frame 인덱스 (3 frames/file).
  ref → file_idx = ref // 3, local_frame = ref % 3
  실제 BM = sprites/hero/h1{file_idx:04d}_bm/frame_{local_frame:02d}_*.png

산출: work/h3/cif_render_real/<group>_<offset>.png (128×128)
"""
from __future__ import annotations
import sys, pathlib, glob
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from analyze_cif import find_frames, parse_cells_4byte


SPRITE_DIR = pathlib.Path('android/app/src/main/assets/sprites/hero')


def load_bm_frame(ref: int) -> Image.Image | None:
    file_idx, local = ref // 3, ref % 3
    bm_dir = SPRITE_DIR / f'h1{file_idx:04d}_bm'
    if not bm_dir.is_dir():
        return None
    matches = sorted(bm_dir.glob(f'frame_{local:02d}_*.png'))
    if not matches:
        return None
    return Image.open(matches[0]).convert('RGBA')


def composite(rec: bytes, out: pathlib.Path, n_cells: int = 9,
              canvas: int = 128, mirror_x: bool = False) -> None:
    img = Image.new('RGBA', (canvas, canvas), (40, 40, 50, 255))
    cx, cy = canvas // 2, canvas // 2 + 24
    cells = parse_cells_4byte(rec, 3, n_cells)
    placed = []
    for c in cells:
        bm = load_bm_frame(c['ref'])
        x = c['x']
        if mirror_x:
            x = -x
        if bm is None:
            placed.append(f'cell{c["idx"]}: ref=0x{c["ref"]:02x} MISSING')
            continue
        if mirror_x:
            bm = bm.transpose(Image.FLIP_LEFT_RIGHT)
        px, py = cx + x - bm.width // 2, cy + c['y'] - bm.height // 2
        img.alpha_composite(bm, (max(0, px), max(0, py)))
        placed.append(f'cell{c["idx"]}: ref=0x{c["ref"]:02x} -> h1{c["ref"]//3:04d}_bm/frame_{c["ref"]%3:02d} @({x:+d},{c["y"]:+d})')
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f'wrote {out}')
    for line in placed:
        print(f'  {line}')


def main(argv: list[str]) -> int:
    cif = pathlib.Path(argv[1] if len(argv) > 1 else 'work/extracted/hero/h0_cif')
    data = cif.read_bytes()
    frames = find_frames(data)
    out_dir = pathlib.Path('work/h3/cif_render_real')
    targets = [
        ('0a020b', False),
        ('0a2208', True),   # mirror hypothesis
        ('0a0208', False),
        ('0a2306', False),
    ]
    for lead, mirror in targets:
        for off in frames:
            if data[off:off+3].hex() == lead:
                rec = data[off:off+41]
                tag = lead + ('_mir' if mirror else '')
                composite(rec, out_dir / f'{cif.stem}_{tag}_at{off}.png',
                          mirror_x=mirror)
                print()
                break
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
