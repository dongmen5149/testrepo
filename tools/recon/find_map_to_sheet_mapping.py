"""Phase 2 (R109) — discover the mapping from _mp metadata to tile sheets.

Hypotheses (revised after Phase 1):
  - meta_bytes[0] (range 0..46, 23 unique)  ↦ theme sheet ID (47 sheets)
  - meta_bytes[1] (range 1..46, 22 unique)  ↦ obj sheet ID (44 sheets)
  - layer_0 raw value may encode (tile_idx | flip_flag<<N).
    Test multiple right-shifts and check if all values fit inside the
    candidate theme sheet's strip_rows.

For each map and for each candidate byte position (0..4), and right-shift
in {0, 1, 2, 3, 4, 6, 7}, compute the fit ratio.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

THEME_RE = re.compile(r"theme_(\d+)_bm")
OBJ_RE = re.compile(r"obj_(\d+)_bm")


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def sheet_rows(sheets: dict, name: str) -> int | None:
    s = sheets.get(name)
    if not s or not s["frames"]:
        return None
    f0 = s["frames"][0]
    return f0.get("strip_rows") or 1  # default 1 if no strip


def sheet_frame_count(sheets: dict, name: str) -> int | None:
    s = sheets.get(name)
    return None if not s else s["frame_count"]


def evaluate_layer_fit(values: list[int], capacity: int, shifts=(0, 1, 2, 3, 4, 6, 7)) -> tuple[int, int]:
    """For each shift S, compute fraction of values where (v >> S) < capacity.
    Returns (best_shift, fraction_in_pct).
    """
    if not values or capacity is None or capacity <= 0:
        return (-1, 0)
    best = (-1, 0)
    n = len(values)
    for s in shifts:
        ok = sum(1 for v in values if (v >> s) < capacity)
        pct = round(100 * ok / n)
        if pct > best[1]:
            best = (s, pct)
    return best


def evaluate_layer_mask(values: list[int], capacity: int) -> tuple[int, int]:
    """Test low-bit masks: capacity rounded up to next power-of-2 worth of bits.
    Returns (mask_bits, pct_unique_in_capacity).
    """
    if not values or not capacity:
        return (-1, 0)
    best = (-1, 0)
    for bits in (4, 5, 6, 7, 8):
        mask = (1 << bits) - 1
        ok = sum(1 for v in values if (v & mask) < capacity)
        pct = round(100 * ok / len(values))
        if pct > best[1]:
            best = (bits, pct)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", required=True)
    ap.add_argument("--sheets", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    maps = load(Path(args.maps))
    sheets = load(Path(args.sheets))

    theme_ids = sorted([int(THEME_RE.match(k).group(1)) for k in sheets if THEME_RE.match(k)])
    obj_ids = sorted([int(OBJ_RE.match(k).group(1)) for k in sheets if OBJ_RE.match(k)])
    print(f"theme IDs: 0..{max(theme_ids)} ({len(theme_ids)} sheets)")
    print(f"obj   IDs: 0..{max(obj_ids)} ({len(obj_ids)} sheets)")

    # === Test 1: which meta byte index gives the best theme-sheet ID ===
    # Score = sum over maps of (layer_0 best fit pct) when treating that byte as theme ID.
    byte_scores = []
    for byte_idx in range(5):
        total_score = 0
        valid_maps = 0
        for k, v in maps.items():
            if "error" in v:
                continue
            mb = v.get("meta_bytes") or []
            if len(mb) <= byte_idx:
                continue
            sheet_name = f"theme_{mb[byte_idx]}_bm"
            cap = sheet_rows(sheets, sheet_name)
            if cap is None:
                continue
            l0 = []  # we don't have l0 raw values here; use stats max as upper bound proxy
            # Use palette_stats.max & layer_0_stats.max as approximation
            l0_max = (v.get("layer_0_stats") or {}).get("max", 0)
            # If l0_max < cap → 100% fit at shift=0; else try shift up to 4
            fit_pct = 0
            for s in (0, 1, 2, 3, 4):
                if (l0_max >> s) < cap:
                    fit_pct = 100
                    break
            total_score += fit_pct
            valid_maps += 1
        byte_scores.append((byte_idx, total_score, valid_maps))
    print("\nTheme-sheet-ID candidate (by meta byte index):")
    for bi, score, valid in byte_scores:
        pct = round(score / max(valid, 1), 1)
        print(f"  meta_bytes[{bi}] → avg fit_pct {pct}% over {valid} maps")

    # === Per-map detailed mapping using the proxy approach ===
    mapping = {}
    for k, v in maps.items():
        if "error" in v:
            continue
        mb = v.get("meta_bytes") or []
        l0_max = (v.get("layer_0_stats") or {}).get("max", 0)
        l1_max = (v.get("layer_1_stats") or {}).get("max", 0)
        # theme candidate: byte[0]; obj candidate: byte[1]
        theme_id = mb[0] if len(mb) > 0 else None
        obj_id = mb[1] if len(mb) > 1 else None
        theme_name = f"theme_{theme_id}_bm" if theme_id is not None else None
        obj_name = f"obj_{obj_id}_bm" if obj_id is not None else None
        theme_rows = sheet_rows(sheets, theme_name) if theme_name else None
        obj_frames = sheet_frame_count(sheets, obj_name) if obj_name else None
        # Best shift for layer_0 max < theme_rows
        l0_fit = None
        if theme_rows:
            for s in range(8):
                if (l0_max >> s) < theme_rows:
                    l0_fit = s
                    break
        # Same for layer_1 / obj_frames
        l1_fit = None
        if obj_frames:
            for s in range(8):
                if (l1_max >> s) < obj_frames:
                    l1_fit = s
                    break
        mapping[k] = {
            "name": v.get("name"),
            "meta_bytes": mb,
            "theme_sheet": theme_name,
            "theme_rows": theme_rows,
            "l0_max": l0_max,
            "l0_shift_to_fit": l0_fit,
            "obj_sheet": obj_name,
            "obj_frames": obj_frames,
            "l1_max": l1_max,
            "l1_shift_to_fit": l1_fit,
        }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nwrote {args.out}: {len(mapping)} maps")

    # Aggregate fits
    n = len(mapping)
    l0_fits = [v["l0_shift_to_fit"] for v in mapping.values() if v["l0_shift_to_fit"] is not None]
    l1_fits = [v["l1_shift_to_fit"] for v in mapping.values() if v["l1_shift_to_fit"] is not None]
    miss_l0 = [k for k, v in mapping.items() if v["l0_shift_to_fit"] is None]
    miss_l1 = [k for k, v in mapping.items() if v["l1_shift_to_fit"] is None]
    print(f"  layer_0 fits theme (under any shift 0..7): {len(l0_fits)}/{n}, miss={len(miss_l0)} {miss_l0[:10]}")
    if l0_fits:
        from collections import Counter
        print(f"    shift dist: {Counter(l0_fits).most_common()}")
    print(f"  layer_1 fits obj (under any shift 0..7):   {len(l1_fits)}/{n}, miss={len(miss_l1)} {miss_l1[:10]}")
    if l1_fits:
        from collections import Counter
        print(f"    shift dist: {Counter(l1_fits).most_common()}")


if __name__ == "__main__":
    main()
