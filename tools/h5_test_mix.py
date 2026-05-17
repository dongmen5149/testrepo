"""Mix(합성) recipe 정합성 검증 (Round 53).

`apps/hero5-godot/scripts/ui/mix_panel.gd` + `game_data.gd::parse_recipe` 의
GDScript 로직과 등동등한 Python sweep. items.json slot_15 의 116 recipe 의:

1. ingredient (1-3 entries, cat ∈ [0..18], idx valid) 가 모든 record 에 존재.
2. result (cat ∈ [0..18], idx valid) 가 모든 record 에 존재 — 실제 item 으로 매핑.
3. success_rate ∈ [0, 100].
4. 카테고리 분포 — 어떤 cat 이 ingredient/result 로 많이 쓰이는지.
5. parse_recipe 의 ingredient.name lookup 이 0 miss.
6. 통계: 평균 ingredient 수, success_rate 분포 (legendary/일반).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ITEMS_JSON = Path("apps/hero5-godot/assets/gamedata/items.json")


def item_name_at(data: dict, cat: int, idx: int) -> str:
    arr = data.get(f"slot_{cat}", [])
    if idx < 0 or idx >= len(arr): return ""
    return str(arr[idx].get("name", ""))


def parse_recipe(rec: dict, data: dict) -> dict:
    """game_data.gd::parse_recipe 와 동등."""
    recipe = rec.get("recipe", {})
    if not recipe: return {}
    ings = []
    for key in ["ing1", "ing2", "ing3"]:
        ing = recipe.get(key)
        if ing is None or not isinstance(ing, dict): continue
        c = int(ing.get("cat", 0))
        i = int(ing.get("idx", 0))
        ings.append({
            "cat": c, "idx": i,
            "count": int(ing.get("count", 1)),
            "name": item_name_at(data, c, i),
        })
    rc = int(recipe.get("result_cat", 0))
    ri = int(recipe.get("result_idx", 0))
    return {
        "ingredients": ings,
        "result": {"cat": rc, "idx": ri, "name": item_name_at(data, rc, ri)},
        "success_rate": int(recipe.get("success_rate", 100)),
    }


def main() -> None:
    if not ITEMS_JSON.exists():
        print(f"[skip] {ITEMS_JSON} 미발견")
        return
    data = json.loads(ITEMS_JSON.read_text(encoding="utf-8"))
    recipes = data.get("slot_15", [])
    print(f"# Round 53 Mix recipe 검증 — {len(recipes)} entries")
    assert len(recipes) == 116, f"recipe 갯수 116 기대, got {len(recipes)}"

    bad_ing_name = 0
    bad_result_name = 0
    sr_out_of_range = 0
    ing_count_dist: dict[int, int] = {}
    sr_dist: list[int] = []
    ing_cat_dist: dict[int, int] = {}
    result_cat_dist: dict[int, int] = {}
    samples = []

    for i, rec in enumerate(recipes):
        parsed = parse_recipe(rec, data)
        if not parsed:
            print(f"  ✗ recipe[{i}] = empty parse")
            bad_result_name += 1
            continue
        n_ing = len(parsed["ingredients"])
        ing_count_dist[n_ing] = ing_count_dist.get(n_ing, 0) + 1
        for ing in parsed["ingredients"]:
            if not ing["name"]:
                bad_ing_name += 1
            ing_cat_dist[ing["cat"]] = ing_cat_dist.get(ing["cat"], 0) + 1
        r = parsed["result"]
        if not r["name"]:
            bad_result_name += 1
        result_cat_dist[r["cat"]] = result_cat_dist.get(r["cat"], 0) + 1
        sr = parsed["success_rate"]
        if sr < 0 or sr > 100:
            sr_out_of_range += 1
        sr_dist.append(sr)
        if i < 3 or i in (50, 115):
            samples.append((i, parsed))

    print(f"  ingredient name miss: {bad_ing_name}")
    print(f"  result name miss: {bad_result_name}")
    print(f"  success_rate out of [0,100]: {sr_out_of_range}")
    print(f"  ingredient 갯수 분포: {dict(sorted(ing_count_dist.items()))}")
    print(f"  ingredient 카테고리 분포: {dict(sorted(ing_cat_dist.items()))}")
    print(f"  result 카테고리 분포: {dict(sorted(result_cat_dist.items()))}")
    avg_sr = sum(sr_dist) / len(sr_dist)
    high_sr = sum(1 for s in sr_dist if s >= 90)
    low_sr = sum(1 for s in sr_dist if s <= 30)
    print(f"  success_rate avg={avg_sr:.1f} / >=90% count={high_sr} / <=30% count={low_sr}")
    print(f"  success_rate min={min(sr_dist)} max={max(sr_dist)}")

    assert bad_ing_name == 0, f"{bad_ing_name} ingredient name miss"
    assert bad_result_name == 0, f"{bad_result_name} result name miss"
    assert sr_out_of_range == 0, f"{sr_out_of_range} success_rate out of range"

    print("\n# 샘플 recipe parse:")
    for i, parsed in samples:
        ing_strs = [f"{ing['name']}×{ing['count']}" for ing in parsed["ingredients"]]
        print(f"  [{i}] {' + '.join(ing_strs)} → {parsed['result']['name']}  ({parsed['success_rate']}%)")

    # 카테고리화 — Round 25 의 4 카테고리 (쿠킹/포션 합성/재료 정제/무기 제작)
    # 추정: result_cat 14 = mix_material (재료 정제), 11 = potion (포션 합성),
    # 5-9 = equip (무기/방어구 제작), 13 = mix material (재료끼리 합치기)
    cat_label = {5: "helmet 제작", 6: "boots 제작", 7: "accessory 제작",
                 8: "accessory_2 제작", 9: "shield 제작",
                 11: "포션 합성", 13: "재료 합성", 14: "재료 정제"}
    print("\n# result_cat 별 카테고리화:")
    for cat in sorted(result_cat_dist.keys()):
        label = cat_label.get(cat, "?")
        cnt = result_cat_dist[cat]
        print(f"  slot_{cat} ({label}): {cnt} recipes")

    print("\n# All checks passed.")


if __name__ == "__main__":
    main()
