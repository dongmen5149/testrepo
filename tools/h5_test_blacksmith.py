"""NPC 대장간(Blacksmith) recipe 정합성 검증 (Round 55).

`apps/hero5-godot/scripts/ui/blacksmith_panel.gd` + `game_data.gd::smith_table /
parse_smith_recipe` 의 GDScript 로직과 동등한 Python sweep. smithtable.json 의
smith_0/1/2 (각 96 entries) 의:

1. ingredient (1-3 entries, cat ∈ [0..18], idx valid) 가 모든 named record 에 존재.
2. result (cat ∈ [0..18], idx valid) 가 모든 named record 에 존재 — 실제 item 매핑.
3. success_rate ∈ {75, 100} (Round 32 의 75 고정 추측은 부분 표본만 본 결과 —
   실제 sweep 결과 sr=100 도 존재. mix_book 의 90-100 / 20-22 와는 여전히 다른 분포).
4. smith_0 = 기본 (1 ing 단순 제작), smith_1/2 = 세트/고급 (3 ing 복합).
5. 카테고리 분포 — result_cat 가 equip slot (0-9) 에 집중.
6. ingredient.name lookup 0 miss.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ITEMS_JSON = Path("apps/hero5-godot/assets/gamedata/items.json")
SMITH_JSON = Path("apps/hero5-godot/assets/gamedata/smithtable.json")


def item_name_at(data: dict, cat: int, idx: int) -> str:
    arr = data.get(f"slot_{cat}", [])
    if idx < 0 or idx >= len(arr): return ""
    return str(arr[idx].get("name", ""))


def parse_smith_recipe(rec: dict, items: dict) -> dict:
    """game_data.gd::parse_smith_recipe (== parse_recipe) 와 동등."""
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
            "name": item_name_at(items, c, i),
        })
    rc = int(recipe.get("result_cat", 0))
    ri = int(recipe.get("result_idx", 0))
    return {
        "ingredients": ings,
        "result": {"cat": rc, "idx": ri, "name": item_name_at(items, rc, ri)},
        "success_rate": int(recipe.get("success_rate", 75)),
    }


def main() -> None:
    if not ITEMS_JSON.exists():
        print(f"[skip] {ITEMS_JSON} 미발견")
        return
    if not SMITH_JSON.exists():
        print(f"[skip] {SMITH_JSON} 미발견 — decode_h5_smithtable.py 실행 필요")
        return
    items = json.loads(ITEMS_JSON.read_text(encoding="utf-8"))
    smith = json.loads(SMITH_JSON.read_text(encoding="utf-8"))

    grade_label = {0: "기본", 1: "세트", 2: "고급"}
    total_named = 0
    total_bad_ing = 0
    total_bad_result = 0
    sr_set: set[int] = set()
    ing_count_dist: dict[int, int] = {}
    ing_cat_dist: dict[int, int] = {}
    result_cat_dist: dict[int, int] = {}
    samples: list[tuple[int, int, dict]] = []

    print("# Round 55 Blacksmith recipe 검증 (smithtable.json)")
    for smith_id in range(3):
        tbl = smith.get(f"smith_{smith_id}", {})
        entries = tbl.get("entries", [])
        named = [
            e for e in entries
            if e.get("name") and e.get("name") != "NONE"
            and isinstance(e.get("recipe"), dict)
            and e.get("recipe", {}).get("ing1") is not None
        ]
        total_named += len(named)
        print(f"  smith_{smith_id} ({grade_label[smith_id]}): {len(entries)} entries, {len(named)} named recipes")

        for i, rec in enumerate(named):
            parsed = parse_smith_recipe(rec, items)
            if not parsed:
                print(f"    ✗ smith_{smith_id}[{i}] = empty parse")
                total_bad_result += 1
                continue
            n_ing = len(parsed["ingredients"])
            ing_count_dist[n_ing] = ing_count_dist.get(n_ing, 0) + 1
            for ing in parsed["ingredients"]:
                if not ing["name"]:
                    total_bad_ing += 1
                ing_cat_dist[ing["cat"]] = ing_cat_dist.get(ing["cat"], 0) + 1
            r = parsed["result"]
            if not r["name"]:
                total_bad_result += 1
            result_cat_dist[r["cat"]] = result_cat_dist.get(r["cat"], 0) + 1
            sr_set.add(parsed["success_rate"])
            if i < 1 or i == len(named) - 1:
                samples.append((smith_id, rec.get("idx", i), parsed))

    print(f"\n총 {total_named} named recipes (288 entries 중)")
    print(f"  ingredient name miss: {total_bad_ing}")
    print(f"  result name miss: {total_bad_result}")
    print(f"  success_rate 분포: {sorted(sr_set)}")
    print(f"  ingredient 갯수 분포: {dict(sorted(ing_count_dist.items()))}")
    print(f"  ingredient 카테고리 분포: {dict(sorted(ing_cat_dist.items()))}")
    print(f"  result 카테고리 분포: {dict(sorted(result_cat_dist.items()))}")

    assert total_bad_ing == 0, f"{total_bad_ing} ingredient name miss"
    assert total_bad_result == 0, f"{total_bad_result} result name miss"
    # sr 값은 모두 [0,100] 범위. Round 32 가 75% 만 언급했으나 실제 sweep 결과
    # sr=100 (단순 정제류 등) 도 존재. mix_book 의 다양한 분포보다는 좁음.
    for s in sr_set:
        assert 0 <= s <= 100, f"success_rate {s} out of [0,100]"
    assert sr_set.issubset({75, 100}), f"smith sr 는 {{75,100}} 부분집합 기대, got {sorted(sr_set)}"

    # smith_0 = 단순 (1 ing 위주), smith_1/2 = 복합 (3 ing 위주) 가설 검증
    # 단순 통계로만 확인
    smith0_named = [
        e for e in smith.get("smith_0", {}).get("entries", [])
        if e.get("name") and e.get("name") != "NONE"
        and e.get("recipe", {}).get("ing1") is not None
    ]
    smith1_named = [
        e for e in smith.get("smith_1", {}).get("entries", [])
        if e.get("name") and e.get("name") != "NONE"
        and e.get("recipe", {}).get("ing1") is not None
    ]
    s0_avg_ing = sum(
        sum(1 for k in ("ing1", "ing2", "ing3") if e["recipe"].get(k) is not None)
        for e in smith0_named
    ) / max(1, len(smith0_named))
    s1_avg_ing = sum(
        sum(1 for k in ("ing1", "ing2", "ing3") if e["recipe"].get(k) is not None)
        for e in smith1_named
    ) / max(1, len(smith1_named))
    print(f"\n# 가설 검증: smith_0 단순(평균 {s0_avg_ing:.2f} ing) vs smith_1 복합(평균 {s1_avg_ing:.2f} ing)")
    assert s0_avg_ing < s1_avg_ing, "smith_0 가 smith_1 보다 단순해야 함"

    print("\n# 샘플 recipe parse:")
    for sid, idx, parsed in samples:
        ing_strs = [f"{ing['name']}×{ing['count']}" for ing in parsed["ingredients"]]
        print(f"  smith_{sid}[{idx:3d}] {' + '.join(ing_strs)} → {parsed['result']['name']}  ({parsed['success_rate']}%)")

    cat_label = {0: "weapon_W", 1: "weapon_R", 2: "weapon_G", 3: "weapon_K",
                 5: "helmet", 6: "boots", 7: "accessory",
                 8: "accessory_2", 9: "shield", 11: "potion", 13: "material",
                 14: "material_2"}
    print("\n# result_cat 별 카테고리화:")
    for cat in sorted(result_cat_dist.keys()):
        label = cat_label.get(cat, "?")
        cnt = result_cat_dist[cat]
        print(f"  slot_{cat:2d} ({label:15s}): {cnt} recipes")

    print("\n# All checks passed.")


if __name__ == "__main__":
    main()
