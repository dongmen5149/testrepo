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


def bake_one(cif_path: pathlib.Path, out_dir: pathlib.Path) -> int:
    """단일 hero cif 베이크. 첫 4 그룹 × 8 frame = 32 PNG."""
    data = cif_path.read_bytes()
    frames = find_frames(data)
    if len(frames) < 32:
        print(f'! {cif_path.name}: only {len(frames)} frames, skipping')
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for dir_idx in range(4):
        for k in range(8):
            i = dir_idx * 8 + k
            if i >= len(frames):
                break
            off = frames[i]
            rec = data[off:off+41]
            img = composite(rec)
            img.save(out_dir / f'dir{dir_idx}_{k}.png')
            written += 1
    print(f'{cif_path.name}: {written} PNG -> {out_dir.name}/')
    return written


def main() -> int:
    hero_dir = ROOT / 'work/extracted/hero'
    cifs = sorted(p for p in hero_dir.glob('h*_cif') if p.name != 'commeffect_cif')
    total = 0
    for cif in cifs:
        stem = cif.stem  # e.g. h0_cif -> h0_cif (no ext though, since file has no dot)
        # cif_path.stem 은 'h0_cif' (확장자 없음). 그대로 사용.
        out = SPRITE_DIR / f'{stem.replace("_cif", "_walk")}'
        total += bake_one(cif, out)
    print(f'\ntotal {total} PNG written across {len(cifs)} hero cif files')
    return 0


if __name__ == '__main__':
    sys.exit(main())
