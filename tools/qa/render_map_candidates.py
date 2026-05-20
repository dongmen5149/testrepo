"""Phase 4 prep (R109) — render multiple candidate tile-sheet renderings per map.

For each anchor map and each meta_bytes[i] candidate, render the map's layer_0
using theme_{bytes[i]}_bm as the tile sheet. Index = (layer_0[k] >> shift)
where shift is selected so all indices fit in the sheet's row count.

This produces PNGs we can visually compare to the original game to pick the
correct byte position.
"""
from __future__ import annotations
import argparse, json, math, re
from pathlib import Path
from PIL import Image

THEME_RE = re.compile(r"theme_(\d+)_bm")


def parse_hex_bytes(s: str) -> list[int]:
    s = s.strip().replace(" ", "")
    return [int(s[i:i + 2], 16) for i in range(0, len(s), 2)]


def load_theme_tiles(sheet_root: Path):
    """Open the first PNG inside `sheet_root` and split it into 16x16 (or w x w) tiles."""
    pngs = sorted(p for p in sheet_root.iterdir() if p.suffix.lower() == ".png")
    if not pngs:
        return None, 0
    img = Image.open(pngs[0]).convert("RGBA")
    tile_px = img.width
    rows = img.height // tile_px
    return img, rows


def best_shift_for(values, cap):
    if not values or not cap:
        return None
    for s in range(8):
        if all((v >> s) < cap for v in values):
            return s
    return None


def render(sheet_img, tile_px: int, layer_0: list[int], shift: int, W: int, H: int) -> Image.Image:
    out = Image.new("RGBA", (W * tile_px, H * tile_px), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            v = layer_0[y * W + x]
            row = v >> shift
            src_box = (0, row * tile_px, tile_px, (row + 1) * tile_px)
            tile = sheet_img.crop(src_box)
            out.paste(tile, (x * tile_px, y * tile_px))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapsdir", required=True)
    ap.add_argument("--sheetsdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--anchors", nargs="+", default=["0", "44", "101", "118", "126"],
                    help="map indices to render (default: NEOSOLTIA, SECRET_ROOM x2, GUARDIAN_CAVE_1, BOSS_TOWN)")
    args = ap.parse_args()

    mapsdir = Path(args.mapsdir)
    sheetsdir = Path(args.sheetsdir)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    for mid in args.anchors:
        f = mapsdir / f"map{mid}_mp.json"
        if not f.exists():
            print(f"skip {f} (missing)")
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        mb = parse_hex_bytes(d.get("meta_header_hex", ""))
        l0 = d.get("layer_0") or []
        W, H = d["width"], d["height"]
        name = d.get("name", "")
        print(f"\nmap{mid} {name} ({W}x{H}) meta_bytes={mb}")
        for i, b in enumerate(mb):
            sheet_root = sheetsdir / f"theme_{b}_bm"
            if not sheet_root.exists():
                continue
            sheet_img, rows = load_theme_tiles(sheet_root)
            if not sheet_img or not rows:
                continue
            shift = best_shift_for(l0, rows)
            if shift is None:
                print(f"  byte[{i}]={b} → theme_{b}_bm ({rows} rows): no shift fits, skip")
                continue
            tile_px = sheet_img.width
            img = render(sheet_img, tile_px, l0, shift, W, H)
            outpath = out / f"map{mid}_{name}_byte{i}_theme{b}_shift{shift}.png"
            img.save(outpath)
            print(f"  byte[{i}]={b} → theme_{b}_bm ({rows} rows, shift={shift}) → {outpath.name}")


if __name__ == "__main__":
    main()
