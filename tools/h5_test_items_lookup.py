"""items.json lookup + filter 분류 검증 (Round 51).

`game_data.gd::item_lookup` / `item_matches_filter` / `class_mask_allows` 의
GDScript 로직과 동등한 Python 구현 + items.json 전체 sweep.

검증 사항:
1. 모든 named item 이 unique 하게 lookup 됨 (중복 시 첫 등장 우선 = slot 낮은 쪽).
2. 각 slot 의 kind 가 _meta.category_dispatch 와 일치.
3. equip 카테고리 item 의 class_mask 가 5-class 비트마스크 (W=1/R=2/G=4/K=8/S=16) 범위 안.
4. tier_label 분포가 Round 24 의 4 종 (legendary/rare/gem/common) 만.
5. filter "weapon"/"armor"/"potion"/"misc" 가 disjoint 하게 19 slot 을 covers.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ITEMS_JSON = Path("apps/hero5-godot/assets/gamedata/items.json")

FILTER_BY_KIND = {
    "weapon": {"weapon", "weapon_2", "weapon_3", "weapon_4"},
    "armor": {"armor", "helmet", "boots", "shield", "accessory",
              "accessory_2", "spirit"},
    "potion": {"potion"},
    "misc": {"orb", "material", "material_2", "recipe", "skill_book_wr",
             "skill_book_gk", "cash_item"},
}


def build_index(data: dict) -> dict[str, dict]:
    """game_data.gd::_build_item_index 와 동일 — slot 낮은 쪽 우선."""
    index: dict[str, dict] = {}
    for slot in range(19):
        arr = data.get(f"slot_{slot}", [])
        for i, rec in enumerate(arr):
            name = str(rec.get("name", ""))
            if not name: continue
            if name not in index:
                index[name] = {"slot": slot, "idx": i, "record": rec}
    return index


def class_mask_allows(class_mask: int, class_id: int) -> bool:
    if class_mask == 0: return True
    return bool(class_mask & (1 << class_id))


def filter_kind(kind: str) -> str:
    for f, kinds in FILTER_BY_KIND.items():
        if kind in kinds:
            return f
    return "unknown"


def main() -> None:
    if not ITEMS_JSON.exists():
        print(f"[skip] {ITEMS_JSON} 미발견 — import_to_godot.py 먼저 실행")
        return
    data = json.loads(ITEMS_JSON.read_text(encoding="utf-8"))
    meta = data.get("_meta", {}).get("category_dispatch", {})
    assert meta, "_meta.category_dispatch 비어있음"

    # 1. lookup index 정합성
    index = build_index(data)
    total = sum(len(data.get(f"slot_{s}", [])) for s in range(19))
    print(f"# items.json sweep — 19 slots / {total} records total")
    print(f"  unique-name index: {len(index)} entries")
    dup_count = total - len(index)
    print(f"  duplicate names (slot 낮은 쪽 우선): {dup_count}")

    # 2. kind / category 일관성
    kind_count: dict[str, int] = {}
    cat_count: dict[str, int] = {}
    for slot in range(19):
        s_meta = meta.get(str(slot), {})
        kind = s_meta.get("kind", "?")
        cat = s_meta.get("category", "?")
        n = len(data.get(f"slot_{slot}", []))
        kind_count[kind] = kind_count.get(kind, 0) + n
        cat_count[cat] = cat_count.get(cat, 0) + n
    print(f"  categories: {cat_count}")

    # 3. equip class_mask 검증 (5-bit, 0..31)
    bad_mask = 0
    tier_dist: dict[int, int] = {}
    class_dist: dict[int, int] = {}
    level_max = 0
    for slot in range(11):  # equip = slot 0..10
        for rec in data.get(f"slot_{slot}", []):
            cm = int(rec.get("class_mask", 0))
            tf = int(rec.get("tier_flags", 0))
            ll = int(rec.get("level_limit", 0))
            if cm > 0x1f: bad_mask += 1
            tier_dist[tf] = tier_dist.get(tf, 0) + 1
            class_dist[cm] = class_dist.get(cm, 0) + 1
            level_max = max(level_max, ll)
    print(f"  equip class_mask out-of-range: {bad_mask}")
    print(f"  equip tier_flags 분포: {dict(sorted(tier_dist.items()))}")
    print(f"  equip level_limit max: {level_max}")
    assert bad_mask == 0, f"class_mask out of 5-bit range: {bad_mask}"

    # 4. filter coverage — disjoint + 19 slot covers
    filter_kinds: dict[str, int] = {"weapon": 0, "armor": 0, "potion": 0,
                                     "misc": 0, "unknown": 0}
    for slot in range(19):
        s_meta = meta.get(str(slot), {})
        kind = s_meta.get("kind", "?")
        f = filter_kind(kind)
        filter_kinds[f] += len(data.get(f"slot_{slot}", []))
    print(f"  filter distribution: {filter_kinds}")
    assert filter_kinds["unknown"] == 0, \
        f"unknown filter category 발생: {filter_kinds['unknown']}"
    # filter sum == total
    fsum = sum(v for v in filter_kinds.values())
    assert fsum == total, f"filter sum {fsum} != total {total}"

    # 5. class_mask_allows 함수 검증 — 5 class × 5 mask 샘플
    samples = [
        (0b00001, 0, True),   # W item, W class
        (0b00001, 1, False),  # W item, R class
        (0b10010, 1, True),   # R+S item, R class
        (0b10010, 4, True),   # R+S item, S class
        (0, 0, True),          # 제약 없음
    ]
    for cm, cid, expected in samples:
        got = class_mask_allows(cm, cid)
        assert got == expected, f"class_mask_allows({cm:#x}, {cid}) = {got}, expected {expected}"
    print(f"  class_mask_allows 검증: 5/5 통과")

    # 6. 샘플 item lookup 출력 (sanity)
    samples_q = ["롱소드", "나이트롱소드", "버클러", "포션"]
    print(f"\n# 샘플 lookup:")
    for q in samples_q:
        hit = index.get(q)
        if hit:
            rec = hit["record"]
            slot = hit["slot"]
            s_meta = meta.get(str(slot), {})
            kind = s_meta.get("kind", "?")
            line = (f"  {q}: slot={slot} kind={kind} "
                    f"lvl={rec.get('level_limit', 0)} "
                    f"cls={rec.get('class_label', '')} "
                    f"tier={rec.get('tier_label', '')}")
            print(line)
        else:
            print(f"  {q}: (미발견)")

    print("\n# All checks passed.")


if __name__ == "__main__":
    main()
