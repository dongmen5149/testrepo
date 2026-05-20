"""Phase 1 Step 1 (R109) — dump tile sheet inventory.

Reads android/app/src/main/assets/sprites_hd/map/*_bm/*.png frame files
and emits a JSON inventory: per sheet, frame count + each frame's (w,h)
and inferred row count if width-divides-height (theme strip pattern).
"""
from __future__ import annotations
import argparse, json, os, re
from pathlib import Path

# frame filename pattern: frame_NN_WxH_<suffix>.png
FRAME_RE = re.compile(r"frame_(\d+)_(\d+)x(\d+)_([a-zA-Z0-9]+)\.png")


def inspect_sheet(sheet_dir: Path) -> dict:
    frames = []
    for f in sorted(sheet_dir.iterdir()):
        if f.suffix.lower() != ".png":
            continue
        m = FRAME_RE.match(f.name)
        if not m:
            frames.append({"name": f.name, "parse": "FAIL"})
            continue
        idx, w, h, suf = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
        entry = {"i": idx, "w": w, "h": h, "suf": suf, "name": f.name}
        if w > 0 and h % w == 0:
            entry["strip_rows"] = h // w
        frames.append(entry)
    return {"frame_count": len(frames), "frames": frames}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = Path(args.inp)
    result: dict[str, dict] = {}
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        result[d.name] = inspect_sheet(d)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"wrote {args.out}: {len(result)} sheets")

    # Summary
    theme = [k for k in result if k.startswith("theme_")]
    obj = [k for k in result if k.startswith("obj_")]
    other = [k for k in result if k not in theme and k not in obj]
    print(f"  theme_*: {len(theme)}, obj_*: {len(obj)}, other: {len(other)} {other[:10]}")
    # theme strip row distribution
    rows = []
    for k in theme:
        fr = result[k]["frames"]
        if fr and "strip_rows" in fr[0]:
            rows.append(fr[0]["strip_rows"])
    if rows:
        print(f"  theme first-frame strip_rows: min={min(rows)} max={max(rows)} n={len(rows)}")


if __name__ == "__main__":
    main()
