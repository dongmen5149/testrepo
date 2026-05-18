"""Round 62: item variant / tier / name-prefix / trailer 정밀 분석.

R61 에서 20B equip body 매핑 완료. R62 에서 추가 발견:
  1. 이름 prefix (|, ', $, {, @, }, ") = rarity/source 분류
  2. trailer (+16..+19) — R61 에서 padding 으로 가정했으나,
     특수 이름의 경우 (type, value, type, value) 2 bonus pair (반지와 동일 인코딩)
  3. variant byte 0xff = default 외에 0x70~0xa0 (sprite/color override)

bonus_type 매핑 (반지 R61 에서 학습 + 트레일러에서 확장 후보):
   2 = HP            5 = STR             6 = INT
   7 = VIT          10 = AGI            12 = DEF ?
  13 = MDEF ?       14 = 명중           15 = 회피
  18 = ATK          25 = 크리티컬 ?

Input  : work/h3/recon/item_decoded.json (R61 산출물)
Output : work/h3/recon/item_variants.{json,log}
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


# Name-prefix → rarity / category 분류 (R62 가설)
PREFIX_CLASS = {
    "|": "magic",        # 매직 (1쌍 bonus 적용)
    "'": "legendary",    # 레전더리
    "$": "epic",         # 에픽 (2쌍 bonus)
    "{": "boss_drop",    # 보스 드롭
    "@": "endgame",      # 엔드게임 (high tier, low price)
    "}": "quest_reward", # 퀘스트 보상
    '"': "hidden",       # 은닉
    "#": "set_bonus",    # 세트
}

# bonus_type code → meaning (R61 ring + R62 trailer)
BONUS_TYPE = {
    0x02: "HP",   0x05: "STR",  0x06: "INT",  0x07: "VIT",
    0x0a: "AGI",  0x0c: "DEF?", 0x0d: "MDEF?",
    0x0e: "HIT",  0x0f: "EVA",  0x12: "ATK",  0x14: "MATK?",
    0x19: "CRIT?",
}


def classify_prefix(name: str) -> tuple[str, str]:
    """Return (rarity_class, clean_name)."""
    if not name:
        return "normal", name
    p = name[0]
    if p in PREFIX_CLASS:
        return PREFIX_CLASS[p], name[1:]
    return "normal", name


def parse_trailer(hex_str: str) -> dict | None:
    """Parse 4-byte trailer as 2 (bonus_type, value) pairs.

    Returns None if all zeros (= true padding).
    """
    if not hex_str:
        return None
    b = bytes.fromhex(hex_str.replace(" ", ""))
    if len(b) < 4 or b == b"\x00\x00\x00\x00":
        return None
    t1, v1, t2, v2 = b[0], b[1], b[2], b[3]
    out = {"raw": hex_str}
    if t1 != 0 or v1 != 0:
        out["b1"] = {"type": t1, "type_name": BONUS_TYPE.get(t1, f"?{t1:02x}"), "value": v1}
    if t2 != 0 or v2 != 0:
        out["b2"] = {"type": t2, "type_name": BONUS_TYPE.get(t2, f"?{t2:02x}"), "value": v2}
    return out


def analyze_category(fn: str, items: list[dict]) -> dict:
    """Per-category analysis."""
    variant_counts = Counter()
    tier_counts = Counter()
    prefix_counts = Counter()
    trailer_bonus_types = Counter()
    trailer_examples = defaultdict(list)
    items_with_bonus: list[dict] = []

    for it in items:
        if it.get("layout") != "equip20":
            continue
        v = it.get("variant", 0)
        t = it.get("tier", 0)
        variant_counts[v] += 1
        tier_counts[t] += 1
        rarity, clean = classify_prefix(it["name"])
        prefix_counts[rarity] += 1

        tb = parse_trailer(it.get("trailer", ""))
        if tb is not None:
            entry = {
                "name": it["name"],
                "clean_name": clean,
                "rarity": rarity,
                "tier": t,
                "variant": v,
                "req_level": it.get("req_level", 0),
                "trailer": tb,
            }
            items_with_bonus.append(entry)
            for k in ("b1", "b2"):
                if k in tb:
                    trailer_bonus_types[tb[k]["type_name"]] += 1
                    if len(trailer_examples[tb[k]["type_name"]]) < 4:
                        trailer_examples[tb[k]["type_name"]].append(
                            f"{it['name']} ({tb[k]['type_name']}+{tb[k]['value']})"
                        )

    return {
        "variant_counts": dict(variant_counts.most_common()),
        "tier_counts": dict(sorted(tier_counts.items())),
        "prefix_counts": dict(prefix_counts.most_common()),
        "trailer_bonus_types": dict(trailer_bonus_types.most_common()),
        "trailer_examples": dict(trailer_examples),
        "items_with_bonus": items_with_bonus,
    }


def main() -> None:
    src = Path("work/h3/recon/item_decoded.json")
    out_dir = Path("work/h3/recon")
    out_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(src.read_text(encoding="utf-8"))

    overall = {
        "summary": {},
        "categories": {},
    }
    g_variant = Counter()
    g_prefix = Counter()
    g_bonus_types = Counter()
    g_items_with_bonus = 0
    g_items_total = 0

    print("=" * 78)
    print("Round 62 — item variant / prefix / trailer analysis")
    print("=" * 78)

    # equip-only categories (20B layout)
    EQUIP_CATS = ("i0_dat", "i1_dat", "i2_dat", "i3_dat",
                  "i4_dat", "i5_dat", "i6_dat", "i7_dat",
                  "i8_dat", "i9_dat", "i10_dat", "i11_dat")

    for fn in EQUIP_CATS:
        if fn not in data:
            continue
        cat = data[fn]
        items = cat.get("items", [])
        if not items:
            continue
        a = analyze_category(fn, items)
        overall["categories"][fn] = {
            "category": cat.get("category"),
            "n_items": sum(a["tier_counts"].values()),
            **a,
        }
        for v, c in a["variant_counts"].items():
            g_variant[v] += c
        for p, c in a["prefix_counts"].items():
            g_prefix[p] += c
        for t, c in a["trailer_bonus_types"].items():
            g_bonus_types[t] += c
        g_items_with_bonus += len(a["items_with_bonus"])
        g_items_total += sum(a["tier_counts"].values())

        print(f"\n--- {fn} ({cat.get('category')}) — {sum(a['tier_counts'].values())} items ---")
        print(f"  variant top  : {list(a['variant_counts'].items())[:8]}")
        print(f"  tier range   : {min(a['tier_counts']) if a['tier_counts'] else '-'}..{max(a['tier_counts']) if a['tier_counts'] else '-'}")
        print(f"  prefix       : {a['prefix_counts']}")
        if a["trailer_bonus_types"]:
            print(f"  bonus types  : {a['trailer_bonus_types']}")
            for bt, exs in a["trailer_examples"].items():
                print(f"    {bt:<8}: {exs[:3]}")

    overall["summary"] = {
        "total_equip_items": g_items_total,
        "items_with_trailer_bonus": g_items_with_bonus,
        "trailer_bonus_pct": round(g_items_with_bonus / max(g_items_total, 1) * 100, 1),
        "variant_top": dict(g_variant.most_common(20)),
        "prefix_distribution": dict(g_prefix.most_common()),
        "bonus_type_distribution": dict(g_bonus_types.most_common()),
    }

    print("\n" + "=" * 78)
    print("OVERALL SUMMARY")
    print("=" * 78)
    print(f"Total equip items   : {g_items_total}")
    print(f"With trailer bonus  : {g_items_with_bonus} ({overall['summary']['trailer_bonus_pct']}%)")
    print(f"\nVariant byte top 20 (0xff = default sprite):")
    for v, c in g_variant.most_common(20):
        flag = "  (default)" if v == 255 else ""
        print(f"  0x{v:02x} = {v:>3} : {c:>4} occurrences{flag}")
    print(f"\nName-prefix distribution (rarity classes):")
    for p, c in g_prefix.most_common():
        print(f"  {p:<14}: {c:>4}")
    print(f"\nTrailer bonus_type frequency:")
    for t, c in g_bonus_types.most_common():
        print(f"  {t:<10}: {c:>4}")

    out_json = out_dir / "item_variants.json"
    out_json.write_text(json.dumps(overall, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out_json}")


if __name__ == "__main__":
    main()
