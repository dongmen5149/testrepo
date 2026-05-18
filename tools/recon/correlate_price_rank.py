"""Round 63: rarity → 가격 modifier + skill rank ↔ equip req_level correlation.

R62 에서 7-tier rarity prefix 식별. 가설:
  normal       : base price
  | magic      : ×1.0 (base)
  ' legendary  : ×1.2~1.5
  $ epic       : ×1.5~2.0
  { boss_drop  : ×2.5~3.0
  @ endgame    : 매우 낮음 (event reward) 또는 ×0.5
  } quest_reward: 0 또는 reward only

또한:
  skill rank @ +0x1d (1/2/3) ↔ equip req_level (1~70) 매핑 시도.
  가설: rank 1 ↔ lvl 1-10, rank 2 ↔ lvl 11-30, rank 3 ↔ lvl 31+

출력: work/h3/recon/price_rank_corr.{json,log}
"""
import json
import sys
import statistics as stats
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


PREFIX_CLASS = {
    "|": "magic", "'": "legendary", "$": "epic",
    "{": "boss_drop", "@": "endgame", "}": "quest_reward",
}


def classify_prefix(name: str) -> str:
    if not name:
        return "normal"
    return PREFIX_CLASS.get(name[0], "normal")


def main() -> None:
    item_json = Path("work/h3/recon/item_decoded.json")
    skill_rank_json = Path("work/h3/recon/skill_rank_decoded.json")
    out_dir = Path("work/h3/recon")

    items = json.loads(item_json.read_text(encoding="utf-8"))
    skill_rank = json.loads(skill_rank_json.read_text(encoding="utf-8"))

    print("=" * 78)
    print("Round 63 — rarity 가격 modifier + skill rank ↔ req_level")
    print("=" * 78)

    # === Part 1: rarity vs price 분포 (per slot) ===
    # base price = 동일 tier (req_level 비슷) 의 normal item 가격
    EQUIP_CATS = ("i0_dat", "i1_dat", "i2_dat", "i3_dat",
                  "i4_dat", "i5_dat", "i6_dat", "i7_dat",
                  "i8_dat", "i9_dat", "i10_dat", "i11_dat")

    print("\n--- Part 1: rarity → 가격 modifier ---")
    # bucket by req_level (5-level bins): rarity → list[(name, price)]
    all_ratio_data = defaultdict(list)  # rarity → list[ratio]

    for fn in EQUIP_CATS:
        cat = items.get(fn)
        if not cat:
            continue
        # normal 만 모아 req_level → price 학습
        normal_curve = []  # (lvl, price)
        for it in cat.get("items", []):
            if it.get("layout") != "equip20":
                continue
            if classify_prefix(it["name"]) == "normal":
                normal_curve.append((it.get("req_level", 0), it.get("price", 0)))
        if not normal_curve:
            continue

        def base_price_for(lvl: int) -> float | None:
            # 같은 또는 가까운 lvl 의 normal price 찾기
            close = [p for l, p in normal_curve if abs(l - lvl) <= 5]
            if not close:
                close = [p for l, p in normal_curve if abs(l - lvl) <= 10]
            return stats.mean(close) if close else None

        ratios = defaultdict(list)
        for it in cat.get("items", []):
            if it.get("layout") != "equip20":
                continue
            rarity = classify_prefix(it["name"])
            if rarity == "normal":
                continue
            base = base_price_for(it.get("req_level", 0))
            if not base or base == 0:
                continue
            r = it.get("price", 0) / base
            ratios[rarity].append(r)
            all_ratio_data[rarity].append(r)

        cat_name = cat.get("category", "?")
        n_items = len(cat.get("items", []))
        line_parts = []
        for rarity in ("magic", "legendary", "epic", "boss_drop", "endgame", "quest_reward"):
            rs = ratios.get(rarity, [])
            if rs:
                line_parts.append(f"{rarity[:5]}={stats.mean(rs):.2f}x(n={len(rs)})")
        print(f"  {fn:<8} ({cat_name:<8}, {n_items:>3} items): {' / '.join(line_parts)}")

    print("\n--- 전체 평균 (모든 slot 통합) ---")
    print(f"  {'rarity':<14} {'mean':>6} {'median':>7} {'stdev':>6} {'n':>4}")
    for rarity in ("magic", "legendary", "epic", "boss_drop", "endgame", "quest_reward"):
        rs = all_ratio_data.get(rarity, [])
        if not rs:
            continue
        m = stats.mean(rs)
        med = stats.median(rs)
        sd = stats.stdev(rs) if len(rs) > 1 else 0
        print(f"  {rarity:<14} {m:>6.2f} {med:>7.2f} {sd:>6.2f} {len(rs):>4}")

    # === Part 2: skill rank ↔ req_level correlation ===
    print("\n\n--- Part 2: skill rank @ +0x1d 분포 ---")
    print(f"  {'weapon':<10} {'category':<14} {'rank distribution':<30} {'예':<40}")

    rank_dist = defaultdict(lambda: defaultdict(list))
    for fn, info in skill_rank.items():
        weapon = info.get("weapon", "?")
        for cat_name, cat_info in info.get("groups", {}).items():
            for entry in cat_info.get("variable_seq", []):
                rank = entry.get("rank", 0)
                if rank:
                    rank_dist[(fn, weapon)][cat_name].append((entry["name"], rank))

    for (fn, weapon), cats in rank_dist.items():
        for cat_name, names_ranks in cats.items():
            ranks = [r for _, r in names_ranks]
            from collections import Counter
            rc = Counter(ranks)
            dist_str = ", ".join(f"r{k}:{v}" for k, v in sorted(rc.items()))
            ex = ", ".join(f"{n}(r{r})" for n, r in names_ranks[:3])
            print(f"  {fn:<10} {cat_name:<14} {dist_str:<30} {ex}")

    print("\n--- skill rank 와 equip req_level 매핑 가설 ---")
    print("  rank 1 (대부분 weapon_passive 1-5 tier) ↔ equip req_level 1-30")
    print("  rank 2 (weapon_passive 6 tier) ↔ equip req_level 31-50")
    print("  rank 3 (weapon_passive 7 tier) ↔ equip req_level 51-70")
    print("  단, active 스킬은 SP cost 가 별도 rank 기준이라 +0x1d 와 무관.")

    # SAVE
    out = {
        "rarity_price_ratio_per_slot": {},  # filled per cat above (already printed)
        "rarity_price_ratio_overall": {
            r: {
                "mean": stats.mean(rs),
                "median": stats.median(rs),
                "stdev": stats.stdev(rs) if len(rs) > 1 else 0,
                "n": len(rs),
            } for r, rs in all_ratio_data.items() if rs
        },
        "skill_rank_distribution": {
            f"{fn}|{weapon}": {
                cat: [{"name": n, "rank": r} for n, r in nr]
                for cat, nr in cats.items()
            } for (fn, weapon), cats in rank_dist.items()
        },
    }
    (out_dir / "price_rank_corr.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out_dir / 'price_rank_corr.json'}")


if __name__ == "__main__":
    main()
