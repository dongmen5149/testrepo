"""Round 62: skill rank/tier precise decode.

R61 에서 4-category 분류 완료. R62 에서 weapon_passive 7-tier 내부의
byte-by-byte diff 를 통해 어느 byte 가 tier-up 시 변하는지 식별한다.

방법:
  - s4~s10 각 파일에서 첫 7 entries (weapon_passive) 의 30B tail 을
    column 별로 비교 → variable column 만 표시
  - rank 8-10 (active_attack 3) / 11-12 (active_buff 2) / 13-15 (passive_bonus 3)
    도 동일하게 col diff
  - 발견한 variable column → "rank_value / spell_id / sp_cost" 등 매핑 시도

입력  : work/h3/recon/skill_decoded.json
출력  : work/h3/recon/skill_rank_decoded.{json,log}
"""
import json
import sys
import struct
from pathlib import Path
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


WEAPON = {
    "s4_dat": "창",   "s5_dat": "대검", "s6_dat": "단검",
    "s7_dat": "건",   "s8_dat": "라이플",
    "s9_dat": "다크석", "s10_dat": "홀리석",
}


def hex_bytes(hex_str: str) -> list[int]:
    return [int(x, 16) for x in hex_str.split()]


def find_diff_cols(rows: list[list[int]]) -> list[int]:
    """Return column indices where bytes vary across rows."""
    if not rows:
        return []
    n = len(rows[0])
    out = []
    for c in range(n):
        col = [r[c] for r in rows if c < len(r)]
        if len(set(col)) > 1:
            out.append(c)
    return out


def analyze_group(name: str, entries: list[dict]) -> dict:
    """One category-group analysis (weapon_passive / active_attack / etc)."""
    if not entries:
        return {}
    rows = [hex_bytes(e["tail_hex"]) for e in entries]
    diff_cols = find_diff_cols(rows)
    common_cols = [c for c in range(len(rows[0])) if c not in diff_cols]

    # variable byte sequence per skill (rank progression)
    variable_seq = []
    for i, e in enumerate(entries):
        row = rows[i]
        vb = {f"+{c:02x}": row[c] for c in diff_cols}
        variable_seq.append({
            "name": e["name"],
            "rank": e.get("rank_or_level", 0),
            "variable_bytes": vb,
        })

    return {
        "n_entries": len(entries),
        "diff_cols": [f"+{c:02x}" for c in diff_cols],
        "common_template": " ".join(f"{rows[0][c]:02x}" if c not in diff_cols else "??"
                                    for c in range(len(rows[0]))),
        "variable_seq": variable_seq,
    }


def main() -> None:
    src = Path("work/h3/recon/skill_decoded.json")
    out_dir = Path("work/h3/recon")
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(src.read_text(encoding="utf-8"))
    results: dict = {}

    print("=" * 78)
    print("Round 62 — skill rank precise decode")
    print("=" * 78)

    for fn, weapon in WEAPON.items():
        if fn not in data:
            continue
        entries = data[fn]
        # group by category
        groups = defaultdict(list)
        for e in entries:
            groups[e.get("category_name", "?")].append(e)

        print(f"\n{'#' * 78}")
        print(f"# {fn} ({weapon}) — {len(entries)} skills total")
        print(f"{'#' * 78}")

        file_result = {}
        for cat in ("weapon_passive", "active_attack", "active_buff", "passive_bonus"):
            grp = groups.get(cat, [])
            if not grp:
                continue
            r = analyze_group(cat, grp)
            file_result[cat] = r
            print(f"\n--- {cat} ({len(grp)} entries) ---")
            print(f"  diff cols  : {r['diff_cols']}")
            print(f"  template   : {r['common_template']}")
            for s in r["variable_seq"]:
                print(f"    {s['name']:<12} rank={s['rank']}  {s['variable_bytes']}")

        results[fn] = {"weapon": weapon, "groups": file_result}

    # Cross-file: tier-equivalent passive in different weapons
    print("\n" + "=" * 78)
    print("CROSS-WEAPON tier-1 passive comparison")
    print("=" * 78)
    tier1_rows = []
    for fn, weapon in WEAPON.items():
        if fn not in data:
            continue
        first = data[fn][0]  # first entry = tier 1 passive
        row = hex_bytes(first["tail_hex"])
        tier1_rows.append((fn, weapon, first["name"], row))
        print(f"  {fn:<8} {weapon:<6} {first['name']:<8} {' '.join(f'{b:02x}' for b in row)}")

    # Discover columns that encode weapon-type
    if tier1_rows:
        rows_only = [r[3] for r in tier1_rows]
        weapon_diff_cols = find_diff_cols(rows_only)
        print(f"\n  weapon-discriminator cols (tier 1): {[f'+{c:02x}' for c in weapon_diff_cols]}")
        # value table
        for c in weapon_diff_cols:
            vals = [(r[0], r[1], r[3][c]) for r in tier1_rows]
            print(f"  col +{c:02x}: {vals}")

    out_path = out_dir / "skill_rank_decoded.json"
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out_path}")


if __name__ == "__main__":
    main()
