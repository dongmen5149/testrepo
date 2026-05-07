"""
Hero3 _cif walk-cycle 8 frame PNG 베이킹.

h0_cif 의 첫 4 그룹 × 8 frame 을 실제 BM 합성으로 PNG 출력.
산출: android/app/src/main/assets/sprites/hero/h0_walk/dir{0..3}_{0..7}.png

가설:
- group1 (offset 12, lead 0a020b, 8 frames) — direction 0
- group2 (offset 341, lead 0a0501, 8 frames) — direction 1
- group3 (offset 670, lead 0a0208, 8 frames) — direction 2
- group4 (offset 1039, lead 0a2208, 8 frames) — direction 3 (mirror of 0)

ref ≤ 0x44 인 cell 만 렌더 (메타 cell 필터).
"""
from __future__ import annotations
import sys, pathlib
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'recon'))
from analyze_cif import find_frames, parse_cells_4byte

SPRITE_DIR = ROOT / 'android/app/src/main/assets/sprites/hero'
REF_MAX = 0x44


def load_bm(ref: int) -> Image.Image | None:
    if ref > REF_MAX:
        return None
    bm_dir = SPRITE_DIR / f'h1{ref//3:04d}_bm'
    if not bm_dir.is_dir():
        return None
    matches = sorted(bm_dir.glob(f'frame_{ref%3:02d}_*.png'))
    return Image.open(matches[0]).convert('RGBA') if matches else None


def composite(rec: bytes, canvas: int = 64) -> Image.Image:
    img = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
    cx, cy = canvas // 2, canvas // 2 + 12
    for c in parse_cells_4byte(rec, 3, 9):
        bm = load_bm(c['ref'])
        if bm is None:
            continue
        px = cx + c['x'] - bm.width // 2
        py = cy + c['y'] - bm.height // 2
        img.alpha_composite(bm, (max(0, px), max(0, py)))
    return img


def main() -> int:
    cif_path = ROOT / 'work/extracted/hero/h0_cif'
    data = cif_path.read_bytes()
    frames = find_frames(data)
    out_dir = SPRITE_DIR / 'h0_walk'
    out_dir.mkdir(parents=True, exist_ok=True)

    direction_starts = [12, 341, 670, 1039]
    for dir_idx, start in enumerate(direction_starts):
        try:
            i0 = frames.index(start)
        except ValueError:
            print(f'! direction {dir_idx} start {start} not in frame list, skipping')
            continue
        for k in range(8):
            if i0 + k >= len(frames):
                break
            off = frames[i0 + k]
            rec = data[off:off+41]
            img = composite(rec)
            out = out_dir / f'dir{dir_idx}_{k}.png'
            img.save(out)
            print(f'dir{dir_idx} frame{k} @{off}: {out.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
