"""R110a Phase 3 — composite render of layer_0 (theme) + layer_1 (obj) for anchor maps.

Hypothesis: layer_1[i] = (frame_idx << 6).
For each nonzero tile, draw obj_<byte[0]>_bm/frame_{frame_idx}_*.png at the tile.
Anchor variant: bottom-center if sprite height > tile_px, else top-left.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from PIL import Image

THEME_RE = re.compile(r"theme_(\d+)_bm")


def parse_hex_bytes(s: str) -> list[int]:
    s = s.strip().replace(" ", "")
    return [int(s[i:i + 2], 16) for i in range(0, len(s), 2)]


def best_shift(values, cap):
    for s in range(8):
        if all((v >> s) < cap for v in values):
            return s
    return None


def load_theme_tiles(sheet_root: Path):
    pngs = sorted(p for p in sheet_root.iterdir() if p.suffix.lower() == ".png")
    if not pngs:
        return None
    img = Image.open(pngs[0]).convert("RGBA")
    tpx = img.width
    rows = img.height // tpx
    return img, tpx, rows


def load_obj_frames(sheet_root: Path) -> dict[int, Image.Image]:
    """Return {frame_idx: PIL.Image} for each frame_NN_*.png in the dir."""
    out = {}
    pat = re.compile(r"frame_(\d+)_(\d+)x(\d+)_")
    for p in sorted(sheet_root.iterdir()):
        m = pat.match(p.name)
        if m and p.suffix.lower() == ".png":
            out[int(m.group(1))] = Image.open(p).convert("RGBA")
    return out


def render(map_path: Path, sheetsdir: Path, out: Path, anchor: str = "bottom_center"):
    d = json.loads(map_path.read_text(encoding="utf-8"))
    mb = parse_hex_bytes(d.get("meta_header_hex", ""))
    theme_id = mb[0]
    l0 = d["layer_0"]; l1 = d["layer_1"]
    W, H = d["width"], d["height"]
    name = d.get("name", "")

    # Layer 0
    theme = load_theme_tiles(sheetsdir / f"theme_{theme_id}_bm")
    if theme is None: return
    theme_img, tpx, rows = theme
    shift0 = best_shift(l0, rows)
    img = Image.new("RGBA", (W * tpx, H * tpx), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            v = l0[y * W + x]
            row = v >> shift0
            tile = theme_img.crop((0, row * tpx, tpx, (row + 1) * tpx))
            img.paste(tile, (x * tpx, y * tpx))

    # Layer 1: obj sprites at frame_idx = layer_1[i] >> 6
    obj_root = sheetsdir / f"obj_{theme_id}_bm"
    obj_frames = load_obj_frames(obj_root) if obj_root.exists() else {}
    for y in range(H):
        for x in range(W):
            v = l1[y * W + x]
            if v == 0:
                continue
            fidx = v >> 6
            sprite = obj_frames.get(fidx)
            if sprite is None:
                continue
            sw, sh = sprite.size
            if anchor == "bottom_center":
                px = x * tpx + (tpx - sw) // 2
                py = y * tpx + (tpx - sh)
            elif anchor == "top_left":
                px = x * tpx
                py = y * tpx
            else:  # center
                px = x * tpx + (tpx - sw) // 2
                py = y * tpx + (tpx - sh) // 2
            img.alpha_composite(sprite, dest=(px, py))

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"  → {out.name}  theme_{theme_id} + obj_{theme_id} ({len(obj_frames)} frames, anchor={anchor})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapsdir", required=True)
    ap.add_argument("--sheetsdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--anchors", nargs="+", default=["0", "44", "118", "126"])
    args = ap.parse_args()
    for mid in args.anchors:
        f = Path(args.mapsdir) / f"map{mid}_mp.json"
        if not f.exists():
            continue
        name = json.loads(f.read_text(encoding="utf-8")).get("name", "")
        for anc in ("bottom_center", "top_left"):
            outp = Path(args.out) / f"map{mid}_{name}_obj_{anc}.png"
            render(f, Path(args.sheetsdir), outp, anchor=anc)


if __name__ == "__main__":
    main()
