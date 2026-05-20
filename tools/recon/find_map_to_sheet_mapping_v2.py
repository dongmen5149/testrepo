"""Phase 2 v2 (R109) — deeper mapping discovery using raw layer values.

For each map's full layer_0/layer_1 lists, try every (byte_position, shift)
combination against the corresponding sheet capacity (theme rows / obj frames),
and report which byte position is the universal best.
"""
from __future__ import annotations
import argparse, json, re
from collections import Counter
from pathlib import Path


THEME_RE = re.compile(r"theme_(\d+)_bm")
OBJ_RE = re.compile(r"obj_(\d+)_bm")
MAP_RE = re.compile(r"map(\d+)_mp\.json")


def parse_hex_bytes(s: str) -> list[int]:
    s = s.strip().replace(" ", "")
    return [int(s[i:i + 2], 16) for i in range(0, len(s), 2)]


def sheet_rows(sheets: dict, name: str) -> int | None:
    s = sheets.get(name)
    if not s or not s["frames"]:
        return None
    return s["frames"][0].get("strip_rows") or 1


def sheet_frame_count(sheets: dict, name: str) -> int | None:
    s = sheets.get(name)
    return None if not s else s["frame_count"]


def best_shift_fit(values, cap):
    """Smallest shift in 0..7 s.t. all (v>>shift) < cap. Returns (shift, pct@best)."""
    if not values or not cap:
        return (None, 0)
    n = len(values)
    best = (None, 0)
    for s in range(8):
        ok = sum(1 for v in values if (v >> s) < cap)
        pct = round(100 * ok / n)
        if pct == 100:
            return (s, 100)
        if pct > best[1]:
            best = (s, pct)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapsdir", required=True, help="dir of mapNN_mp.json")
    ap.add_argument("--sheets", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    sheets = json.loads(Path(args.sheets).read_text(encoding="utf-8"))
    theme_ids = sorted([int(THEME_RE.match(k).group(1)) for k in sheets if THEME_RE.match(k)])
    obj_ids = sorted([int(OBJ_RE.match(k).group(1)) for k in sheets if OBJ_RE.match(k)])
    max_theme = max(theme_ids)
    max_obj = max(obj_ids)

    # Per-byte position scoring: how often does byte[i] designate the correct theme sheet?
    # "Correct" = layer_0 fits with shift 0..7 in that sheet.
    byte_pos_theme_score = [0] * 5  # byte 0..4
    byte_pos_obj_score = [0] * 5
    n_total = 0

    per_map = {}
    files = sorted(Path(args.mapsdir).iterdir(), key=lambda p: int(MAP_RE.match(p.name).group(1)) if MAP_RE.match(p.name) else 1_000_000)
    for f in files:
        m = MAP_RE.match(f.name)
        if not m:
            continue
        key = f"map{int(m.group(1))}"
        d = json.loads(f.read_text(encoding="utf-8"))
        l0 = d.get("layer_0") or []
        l1 = d.get("layer_1") or []
        mb = parse_hex_bytes(d.get("meta_header_hex", ""))
        meta4 = d.get("meta4")

        # For each meta byte position, score theme/obj fit
        entry = {
            "name": d.get("name"),
            "meta_bytes": mb,
            "meta4": meta4,
            "byte_fits": [],
            "best_theme_sheet": None,
            "best_obj_sheet": None,
        }
        candidates_theme = []
        candidates_obj = []
        for i, b in enumerate(mb):
            row = {"byte_idx": i, "byte_val": b}
            if b <= max_theme:
                s, pct = best_shift_fit(l0, sheet_rows(sheets, f"theme_{b}_bm"))
                row["theme_fit"] = {"shift": s, "pct": pct}
                if pct == 100:
                    candidates_theme.append((i, b, s))
                    byte_pos_theme_score[i] += 1
            if b <= max_obj:
                s, pct = best_shift_fit(l1, sheet_frame_count(sheets, f"obj_{b}_bm"))
                row["obj_fit"] = {"shift": s, "pct": pct}
                if pct == 100:
                    candidates_obj.append((i, b, s))
                    byte_pos_obj_score[i] += 1
            entry["byte_fits"].append(row)
        # Prefer the lowest-shift candidate (tightest fit) at the lowest byte index
        if candidates_theme:
            candidates_theme.sort(key=lambda x: (x[2], x[0]))
            entry["best_theme_sheet"] = f"theme_{candidates_theme[0][1]}_bm"
            entry["best_theme_byte"] = candidates_theme[0][0]
            entry["best_theme_shift"] = candidates_theme[0][2]
        if candidates_obj:
            candidates_obj.sort(key=lambda x: (x[2], x[0]))
            entry["best_obj_sheet"] = f"obj_{candidates_obj[0][1]}_bm"
            entry["best_obj_byte"] = candidates_obj[0][0]
            entry["best_obj_shift"] = candidates_obj[0][2]
        per_map[key] = entry
        n_total += 1

    out = {
        "summary": {
            "n_maps": n_total,
            "theme_byte_score": byte_pos_theme_score,
            "obj_byte_score": byte_pos_obj_score,
        },
        "maps": per_map,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out}: {n_total} maps")
    print(f"  meta byte position theme-fit (100%) counts: {byte_pos_theme_score}")
    print(f"  meta byte position obj-fit   (100%) counts: {byte_pos_obj_score}")
    n_t = sum(1 for v in per_map.values() if v["best_theme_sheet"])
    n_o = sum(1 for v in per_map.values() if v["best_obj_sheet"])
    print(f"  maps with theme candidate: {n_t}/{n_total}")
    print(f"  maps with obj   candidate: {n_o}/{n_total}")
    # shift distribution among the chosen best
    shifts_t = Counter(v["best_theme_shift"] for v in per_map.values() if v.get("best_theme_shift") is not None)
    shifts_o = Counter(v["best_obj_shift"] for v in per_map.values() if v.get("best_obj_shift") is not None)
    bytes_t = Counter(v["best_theme_byte"] for v in per_map.values() if v.get("best_theme_byte") is not None)
    bytes_o = Counter(v["best_obj_byte"] for v in per_map.values() if v.get("best_obj_byte") is not None)
    print(f"  best theme shift dist: {shifts_t.most_common()}")
    print(f"  best theme byte  dist: {bytes_t.most_common()}")
    print(f"  best obj   shift dist: {shifts_o.most_common()}")
    print(f"  best obj   byte  dist: {bytes_o.most_common()}")


if __name__ == "__main__":
    main()
