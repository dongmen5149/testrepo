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
    """단일 hero cif 베이크. 첫 4 그룹 × 8 frame = 32 PNG + dir_mapping.json."""
    import json
    from PIL import ImageChops
    data = cif_path.read_bytes()
    frames = find_frames(data)
    if len(frames) < 32:
        print(f'! {cif_path.name}: only {len(frames)} frames, skipping')
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    images = [[None] * 8 for _ in range(4)]
    for dir_idx in range(4):
        for k in range(8):
            i = dir_idx * 8 + k
            if i >= len(frames):
                break
            off = frames[i]
            rec = data[off:off+41]
            img = composite(rec)
            img.save(out_dir / f'dir{dir_idx}_{k}.png')
            images[dir_idx][k] = img
            written += 1
    # dir_mapping.json: 픽셀 symmetry 로 LEFT/RIGHT mirror 쌍 자동 검출 → FACING_*->cif dir 매핑.
    mirror = _detect_mirror_pair(images)
    facing_to_dir = _facing_mapping(mirror)
    (out_dir / 'dir_mapping.json').write_text(json.dumps({
        'facing_to_dir': facing_to_dir,  # [DOWN, UP, LEFT, RIGHT]
        'mirror_pair': list(mirror),
        'note': 'DOWN/UP 순서는 임의 (디바이스 검증 필요). LEFT/RIGHT 는 픽셀 symmetry 로 식별.',
    }, indent=2))
    print(f'{cif_path.name}: {written} PNG -> {out_dir.name}/  mirror={mirror} facing_to_dir={facing_to_dir}')
    return written


def _detect_mirror_pair(images: list[list]) -> tuple[int, int]:
    """4 dir 의 frame 0 끼리 비교, dir{i} flipped vs dir{j} score 가 최소인 (i, j) 반환."""
    from PIL import ImageChops
    best = (1e9, 0, 1)
    for i in range(4):
        if images[i][0] is None: continue
        a = images[i][0].transpose(Image.FLIP_LEFT_RIGHT)
        for j in range(4):
            if j == i or images[j][0] is None: continue
            b = images[j][0]
            da = ImageChops.difference(a, b)
            px = list(da.getdata())
            s = sum(p[0]+p[1]+p[2]+p[3] for p in px) / max(1, len(px))
            if s < best[0]:
                best = (s, i, j)
    return (best[1], best[2])


def _facing_mapping(mirror: tuple[int, int]) -> list[int]:
    """LEFT=mirror[0], RIGHT=mirror[1] 로 두고 나머지 두 개를 DOWN, UP 에 임의 할당.
    return [DOWN, UP, LEFT, RIGHT] dir indices. (DOWN/UP 순서는 추측)"""
    others = sorted(set(range(4)) - set(mirror))
    return [others[0], others[1], mirror[0], mirror[1]]


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
