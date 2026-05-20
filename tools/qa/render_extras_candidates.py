"""R110e Phase 2 — try various hypotheses for extras_records → sprite mapping.

For NEOSOLTIA (map0), render with:
  H1: every extras → obj_<themeId>_bm/frame_4 (the 80x63 big bush)
  H2: every extras → sprObj0 (60x39 tree)
  H3: extras grouped by id ranges → various sprObj sheets (a heuristic guess)

Each candidate is composited on top of layers 0+1 (themed bg + obj). Visual diff
tells us which mapping is meaningful.
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


def load_theme_tiles(root: Path):
    pngs = sorted(p for p in root.iterdir() if p.suffix.lower() == ".png")
    if not pngs:
        return None
    img = Image.open(pngs[0]).convert("RGBA")
    tpx = img.width
    rows = img.height // tpx
    return img, tpx, rows


def load_frames(root: Path) -> dict[int, Image.Image]:
    out = {}
    pat = re.compile(r"frame_(\d+)_(\d+)x(\d+)_")
    if not root.exists():
        return out
    for p in sorted(root.iterdir()):
        m = pat.match(p.name)
        if m and p.suffix.lower() == ".png":
            out[int(m.group(1))] = Image.open(p).convert("RGBA")
    return out


def build_base_layer(d: dict, sheetsdir: Path) -> Image.Image | None:
    """Render layer_0 + layer_1 obj using R109+R110a rules."""
    mb = parse_hex_bytes(d.get("meta_header_hex", ""))
    theme_id = mb[0]
    l0 = d["layer_0"]; l1 = d["layer_1"]
    W, H = d["width"], d["height"]
    theme = load_theme_tiles(sheetsdir / f"theme_{theme_id}_bm")
    if theme is None: return None
    theme_img, tpx, rows = theme
    shift0 = best_shift(l0, rows)
    img = Image.new("RGBA", (W * tpx, H * tpx), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            v = l0[y * W + x]
            row = v >> shift0
            tile = theme_img.crop((0, row * tpx, tpx, (row + 1) * tpx))
            img.paste(tile, (x * tpx, y * tpx))
    # layer 1
    obj_frames = load_frames(sheetsdir / f"obj_{theme_id}_bm")
    for y in range(H):
        for x in range(W):
            v = l1[y * W + x]
            if v == 0: continue
            sprite = obj_frames.get(v >> 6)
            if sprite is None: continue
            sw, sh = sprite.size
            px = x * tpx + (tpx - sw) // 2
            py = y * tpx + (tpx - sh)
            img.alpha_composite(sprite, dest=(px, py))
    return img


def overlay_extras(img: Image.Image, extras: list[dict], sprite_picker, tpx: int = 16):
    for e in extras:
        sprite = sprite_picker(e)
        if sprite is None:
            continue
        # Use px (pixel) if present, else tile * tpx
        cx, cy = e.get("px", [e["tile"][0] * tpx + tpx//2, e["tile"][1] * tpx + tpx])
        sw, sh = sprite.size
        sx = cx - sw // 2
        sy = cy - sh
        img.alpha_composite(sprite, dest=(max(0, sx), max(0, sy)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapsdir", required=True)
    ap.add_argument("--sheetsdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--anchors", nargs="+", default=["0", "44", "126"])
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    sheetsdir = Path(args.sheetsdir)

    # Load all sprObj sheets once
    sprObj = {}
    for i in range(7):
        d = sheetsdir / f"sprObj{i}_bm"
        if d.exists():
            f = load_frames(d)
            if f:
                sprObj[i] = f.get(0)

    for mid in args.anchors:
        f = Path(args.mapsdir) / f"map{mid}_mp.json"
        if not f.exists(): continue
        d = json.loads(f.read_text(encoding="utf-8"))
        name = d.get("name", "")
        extras = d.get("extras_records", [])
        mb = parse_hex_bytes(d.get("meta_header_hex", ""))
        theme_id = mb[0]
        obj_frames = load_frames(sheetsdir / f"obj_{theme_id}_bm")

        # H1: all extras → obj_<themeId>/frame_4
        base = build_base_layer(d, sheetsdir)
        if base is None: continue
        h1 = base.copy()
        f4 = obj_frames.get(4)
        if f4:
            overlay_extras(h1, extras, lambda e: f4)
            h1.save(out / f"map{mid}_{name}_H1_frame4_all.png")

        # H2: all extras → sprObj0 (tree)
        h2 = base.copy()
        if 0 in sprObj:
            overlay_extras(h2, extras, lambda e: sprObj[0])
            h2.save(out / f"map{mid}_{name}_H2_sprObj0_all.png")

        # H3: id-range heuristic — id 62/63 = sprObj0 (tree), id<10 = sprObj6 (small),
        #     id 35-50 = sprObj1, id 100+ = sprObj2 (big building), else sprObj5
        def pick(e):
            i = e["id"]
            if i in (62, 63):     return sprObj.get(0)  # grass/bush → tree
            if i < 10:            return sprObj.get(6)  # special/chest → small
            if 30 <= i <= 59:     return sprObj.get(1)  # furniture/NPC → small tree
            if 100 <= i <= 130:   return sprObj.get(2)  # yellow → big building
            if 140 <= i <= 170:   return sprObj.get(3)  # purple → lamp
            return sprObj.get(5)
        h3 = base.copy()
        overlay_extras(h3, extras, pick)
        h3.save(out / f"map{mid}_{name}_H3_id_range_heuristic.png")
        print(f"map{mid} {name}: H1/H2/H3 rendered")


if __name__ == "__main__":
    main()
