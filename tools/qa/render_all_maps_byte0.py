"""Phase 4 (R109) — render all 134 maps using the byte[0]=theme rule.

Confirmed in Phase 2/4 prep: meta_bytes[0] is the universal theme-sheet ID.
For each map, render layer_0 alone (theme tiles) as a PNG and emit a thumbnail
grid so we can scan for any malformed map at a glance.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from PIL import Image

MAP_RE = re.compile(r"map(\d+)_mp\.json")


def parse_hex_bytes(s: str) -> list[int]:
    s = s.strip().replace(" ", "")
    return [int(s[i:i + 2], 16) for i in range(0, len(s), 2)]


def load_sheet_first_png(sheet_root: Path):
    pngs = sorted(p for p in sheet_root.iterdir() if p.suffix.lower() == ".png")
    if not pngs:
        return None
    return Image.open(pngs[0]).convert("RGBA")


def best_shift(values, cap):
    for s in range(8):
        if all((v >> s) < cap for v in values):
            return s
    return None


def render_one(map_path: Path, sheetsdir: Path) -> tuple[Image.Image | None, dict]:
    d = json.loads(map_path.read_text(encoding="utf-8"))
    mb = parse_hex_bytes(d.get("meta_header_hex", ""))
    if not mb:
        return None, {"err": "no meta"}
    theme_id = mb[0]
    sheet_root = sheetsdir / f"theme_{theme_id}_bm"
    if not sheet_root.exists():
        return None, {"err": f"theme_{theme_id}_bm missing"}
    sheet_img = load_sheet_first_png(sheet_root)
    if not sheet_img:
        return None, {"err": "no sheet png"}
    tile_px = sheet_img.width
    rows = sheet_img.height // tile_px
    l0 = d.get("layer_0") or []
    W, H = d["width"], d["height"]
    shift = best_shift(l0, rows)
    if shift is None:
        return None, {"err": f"no shift fits (rows={rows}, max={max(l0)})"}
    out = Image.new("RGBA", (W * tile_px, H * tile_px), (0, 0, 0, 0))
    for y in range(H):
        for x in range(W):
            v = l0[y * W + x]
            row = v >> shift
            tile = sheet_img.crop((0, row * tile_px, tile_px, (row + 1) * tile_px))
            out.paste(tile, (x * tile_px, y * tile_px))
    return out, {"theme": f"theme_{theme_id}_bm", "shift": shift, "rows": rows, "size": (W, H), "name": d.get("name")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapsdir", required=True)
    ap.add_argument("--sheetsdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--thumbnail-grid", default=None,
                    help="if given, emit a thumb grid PNG path")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    summary: dict = {}
    rendered_images: list[tuple[int, str, Image.Image]] = []
    files = sorted(Path(args.mapsdir).iterdir(),
                   key=lambda p: int(MAP_RE.match(p.name).group(1)) if MAP_RE.match(p.name) else 1_000_000)
    n_ok = 0
    n_err = 0
    for f in files:
        m = MAP_RE.match(f.name)
        if not m:
            continue
        mid = int(m.group(1))
        img, info = render_one(f, Path(args.sheetsdir))
        info["map"] = f"map{mid}"
        if img is None:
            n_err += 1
            summary[f"map{mid}"] = info
            continue
        n_ok += 1
        outp = out / f"map{mid:03d}_{info['name']}.png"
        img.save(outp)
        summary[f"map{mid}"] = {**info, "out": outp.name}
        rendered_images.append((mid, info["name"], img))

    Path(args.summary).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"rendered {n_ok}/{n_ok+n_err} maps   errors:{n_err}")

    # Optional thumbnail grid
    if args.thumbnail_grid:
        thumb_w = 128
        thumb_h = 96
        cols = 12
        rendered_images.sort(key=lambda x: x[0])
        rows_n = (len(rendered_images) + cols - 1) // cols
        grid = Image.new("RGBA", (cols * thumb_w, rows_n * thumb_h), (0, 0, 0, 255))
        for i, (mid, name, im) in enumerate(rendered_images):
            r, c = divmod(i, cols)
            t = im.copy()
            t.thumbnail((thumb_w, thumb_h))
            tx = c * thumb_w + (thumb_w - t.width) // 2
            ty = r * thumb_h + (thumb_h - t.height) // 2
            grid.paste(t, (tx, ty))
        grid.save(args.thumbnail_grid)
        print(f"thumb grid → {args.thumbnail_grid}")


if __name__ == "__main__":
    main()
