"""Phase 1 Step 2 (R109) — dump map _mp metadata cross-reference.

Reads android/app/src/main/assets/maps/mapNN_mp.json and emits an
inventory: per map, meta_header_hex bytes, meta4, palette range,
layer_0/layer_1 value range, sizes, and palette content.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

MAP_RE = re.compile(r"map(\d+)_mp\.json")


def parse_hex_bytes(s: str) -> list[int]:
    # accept "06070141" or "06 07 01 41"
    s = s.strip().replace(" ", "")
    return [int(s[i:i + 2], 16) for i in range(0, len(s), 2)]


def stats(values):
    if not values:
        return None
    mn, mx = min(values), max(values)
    uniq = sorted(set(values))
    return {"min": mn, "max": mx, "uniq_count": len(uniq)}


def inspect_map(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    meta_hex = d.get("meta_header_hex", "")
    meta_bytes = parse_hex_bytes(meta_hex) if meta_hex else []
    palette = d.get("palette", []) or []
    l0 = d.get("layer_0", []) or []
    l1 = d.get("layer_1", []) or []
    extras = d.get("extras_records", []) or []
    return {
        "name": d.get("name", ""),
        "width": d.get("width", 0),
        "height": d.get("height", 0),
        "version": d.get("version"),
        "meta_hex": meta_hex,
        "meta_bytes": meta_bytes,
        "meta4": d.get("meta4"),
        "palette_count": d.get("palette_count", len(palette)),
        "palette": palette,
        "palette_stats": stats(palette),
        "layer_0_stats": stats(l0),
        "layer_1_stats": stats(l1),
        "extras_count": len(extras),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    root = Path(args.inp)
    out: dict[str, dict] = {}
    for f in sorted(root.iterdir(), key=lambda p: int(MAP_RE.match(p.name).group(1)) if MAP_RE.match(p.name) else 1_000_000):
        m = MAP_RE.match(f.name)
        if not m:
            continue
        key = f"map{int(m.group(1))}"
        try:
            out[key] = inspect_map(f)
        except Exception as e:  # noqa: BLE001
            out[key] = {"error": str(e)}

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out}: {len(out)} maps")

    # summary aggregates
    pal_max, pal_min, l0_max, l1_max = [], [], [], []
    meta_byte_uniques: list[set[int]] = []
    meta4s: list[int] = []
    for k, v in out.items():
        if "error" in v:
            continue
        ps = v["palette_stats"];
        if ps:
            pal_max.append(ps["max"]); pal_min.append(ps["min"])
        l0 = v["layer_0_stats"];
        if l0:
            l0_max.append(l0["max"])
        l1 = v["layer_1_stats"];
        if l1:
            l1_max.append(l1["max"])
        mb = v["meta_bytes"] or []
        while len(meta_byte_uniques) < len(mb):
            meta_byte_uniques.append(set())
        for i, b in enumerate(mb):
            meta_byte_uniques[i].add(b)
        if isinstance(v.get("meta4"), int):
            meta4s.append(v["meta4"])
    if pal_max:
        print(f"  palette: min∈[{min(pal_min)}..{max(pal_min)}] max∈[{min(pal_max)}..{max(pal_max)}]")
    if l0_max:
        print(f"  layer_0 max range across maps: [{min(l0_max)}..{max(l0_max)}]")
    if l1_max:
        print(f"  layer_1 max range across maps: [{min(l1_max)}..{max(l1_max)}]")
    print("  meta byte unique counts: " + ", ".join(
        f"[{i}]={len(s)} ({min(s)}..{max(s)})" for i, s in enumerate(meta_byte_uniques)))
    if meta4s:
        print(f"  meta4 unique: {sorted(set(meta4s))}")


if __name__ == "__main__":
    main()
