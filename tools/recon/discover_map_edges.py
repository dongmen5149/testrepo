"""R110c — auto-discover exit positions and pair maps.

Scans each map's edges (N/S/E/W) for walkable tiles (layer_1[i] == 0)
and clusters contiguous walkable tiles into exit "openings."

Maps without any walkable edges (enclosed rooms) are noted — they
must use door/teleport mechanism not edge-walk.

Then pair candidate exits across maps:
  map A's south opening at x∈[a,b] = exit O_A.
  Look for map B with NORTH opening at x∈[a,b] with matching width.
  If unique match, add Edge(A, S, B) + Edge(B, N, A).
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

MAP_RE = re.compile(r"map(\d+)_mp\.json")


def edge_walkable(d: dict) -> dict[str, list[tuple[int, int]]]:
    """Returns {side: [(start, end), ...]} of consecutive walkable runs."""
    W, H = d["width"], d["height"]
    l1 = d.get("layer_1") or []
    if len(l1) < W * H:
        return {"N": [], "S": [], "W": [], "E": []}
    sides = {
        "N": [x for x in range(W) if l1[0 * W + x] == 0],
        "S": [x for x in range(W) if l1[(H - 1) * W + x] == 0],
        "W": [y for y in range(H) if l1[y * W + 0] == 0],
        "E": [y for y in range(H) if l1[y * W + (W - 1)] == 0],
    }
    out = {}
    for k, vals in sides.items():
        groups: list[tuple[int, int]] = []
        if vals:
            cur = [vals[0]]
            for v in vals[1:]:
                if v == cur[-1] + 1:
                    cur.append(v)
                else:
                    groups.append((cur[0], cur[-1])); cur = [v]
            groups.append((cur[0], cur[-1]))
        out[k] = groups
    return out


def opposite(side: str) -> str:
    return {"N": "S", "S": "N", "W": "E", "E": "W"}[side]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mapsdir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    maps_dir = Path(args.mapsdir)
    by_map: dict[int, dict] = {}
    for f in sorted(maps_dir.iterdir(), key=lambda p: int(MAP_RE.match(p.name).group(1)) if MAP_RE.match(p.name) else 1_000_000):
        m = MAP_RE.match(f.name)
        if not m:
            continue
        mid = int(m.group(1))
        d = json.loads(f.read_text(encoding="utf-8"))
        e = edge_walkable(d)
        by_map[mid] = {
            "name": d.get("name", ""),
            "w": d["width"], "h": d["height"],
            "edges": e,
        }

    # Stats
    enclosed = sum(1 for v in by_map.values() if sum(len(v["edges"][s]) for s in "NSEW") == 0)
    print(f"{len(by_map)} maps, {enclosed} fully enclosed (no walkable edge tiles)")
    n_exits = sum(sum(len(v["edges"][s]) for s in "NSEW") for v in by_map.values())
    print(f"  total exit-openings (distinct runs): {n_exits}")

    # Pair candidates — refined heuristic:
    #   1. Skip "wildcard" maps where 90%+ of edge tiles are walkable (rooms/halls with full open boundary).
    #   2. Require width/height equal (or differ by <= 2) along shared axis (geometric continuity).
    #   3. Require run length match (or differ by <= 1) — a 1-tile exit must pair with a 1-tile exit.
    #   4. Require run START position equal (or differ by <= 1) — exits must be at similar x/y on both maps.
    def is_wildcard(m: dict, side: str) -> bool:
        # If 90%+ of this edge's tiles are walkable, treat as fully open (likely indoor room).
        runs = m["edges"][side]
        total = m["w"] if side in ("N", "S") else m["h"]
        walkable = sum(r1 - r0 + 1 for r0, r1 in runs)
        return total > 0 and walkable / total >= 0.9

    def axis_equal(a: dict, b: dict, side: str) -> bool:
        # N/S share width; W/E share height.
        if side in ("N", "S"):
            return abs(a["w"] - b["w"]) <= 2
        return abs(a["h"] - b["h"]) <= 2

    edges: list[dict] = []
    ambiguous: list[dict] = []
    unmatched: list[dict] = []
    used: set[tuple[int, str, int, int]] = set()
    for a_id, a in by_map.items():
        for side, runs in a["edges"].items():
            if is_wildcard(a, side):
                continue
            for (s0, s1) in runs:
                key = (a_id, side, s0, s1)
                if key in used:
                    continue
                run_len = s1 - s0 + 1
                cands = []
                for b_id, b in by_map.items():
                    if b_id == a_id:
                        continue
                    opp = opposite(side)
                    if is_wildcard(b, opp):
                        continue
                    if not axis_equal(a, b, side):
                        continue
                    for (t0, t1) in b["edges"][opp]:
                        t_len = t1 - t0 + 1
                        if abs(t_len - run_len) > 1:
                            continue
                        if abs(t0 - s0) > 1:
                            continue
                        cands.append((b_id, opp, t0, t1))
                if len(cands) == 1:
                    b_id, _, t0, t1 = cands[0]
                    edges.append({
                        "from": a_id, "side": side, "to": b_id,
                        "fromRun": [s0, s1], "toRun": [t0, t1],
                    })
                    used.add(key)
                    used.add((b_id, opposite(side), t0, t1))
                elif len(cands) > 1:
                    ambiguous.append({
                        "from": a_id, "side": side, "run": [s0, s1],
                        "candidates": cands,
                    })
                else:
                    unmatched.append({"from": a_id, "side": side, "run": [s0, s1]})

    out_dir = Path(args.out)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "stats": {
            "n_maps": len(by_map),
            "n_enclosed": enclosed,
            "n_exits": n_exits,
            "n_edges_unique": len(edges),
            "n_ambiguous": len(ambiguous),
            "n_unmatched": len(unmatched),
        },
        "edges": edges,
        "ambiguous": ambiguous,
        "unmatched": unmatched,
        "per_map": {f"map{k}": v for k, v in by_map.items()},
    }
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"  unique-match edges: {len(edges)}")
    print(f"  ambiguous (multiple candidates): {len(ambiguous)}")
    print(f"  unmatched (no candidate): {len(unmatched)}")
    # Show first few edges
    print("\nFirst 15 unique-match edges:")
    for e in edges[:15]:
        a = by_map[e["from"]]["name"]
        b = by_map[e["to"]]["name"]
        print(f"  {e['from']:>3} {a:<20} {e['side']} → {e['to']:<3} {b}  (run {e['fromRun']} ↔ {e['toRun']})")


if __name__ == "__main__":
    main()
