"""SkillBook 학습 시스템 정합성 검증 (Round 57).

`apps/hero5-godot/scripts/core/game_state.gd::learn_skill_book` +
`game_data.gd::skill_books_for_class` + `skill_book_panel.gd` 의 GDScript 로직과
동등한 Python sweep. items.json slot_16/17 의 skill_book records 의:

1. slot_16 = 95 records (Warrior+Rogue), slot_17 = 98 records (Gunslinger+Knight).
2. (class_id / 2) + 16 = slot 매핑 정확성 (Round 21 IfLearnSkill 공식).
3. 각 book 의 class_id ∈ {0,1,2,3} (Sorcerer=4 는 stub).
4. skill_level ∈ [1..7], required_level ∈ [0..99] (data sweep 결과 74 까지 존재).
5. learn 시뮬레이션:
   - 같은 skill 더 높은 LV 책 학습 시 갱신 ✓
   - 같은 skill 같거나 낮은 LV 책 학습 시 거부 ✓
   - 다른 class 책 학습 시 거부 ✓
   - 레벨 부족 시 거부 ✓
6. 클래스별 skill_index 분포 (43 스킬/클래스 가정).
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ITEMS_JSON = Path("apps/hero5-godot/assets/gamedata/items.json")

CLASS_NAMES = ["워리어", "로그", "건슬링어", "나이트", "소서러"]


def skill_book_slot(class_id: int) -> int:
    """game_data.gd::skill_book_slot_for_class — Round 21 의 IfLearnSkill 공식."""
    return (class_id // 2) + 16


def can_learn(player_class: int, player_level: int, current_skill_levels: dict,
              book: dict) -> tuple[bool, str]:
    """game_state.gd::can_learn_skill_book 와 동등 (Round 57)."""
    book_class = int(book.get("class_id", -1))
    if book_class != player_class:
        return False, f"다른 클래스 (책={book_class}, 플레이어={player_class})"
    req = int(book.get("required_level", 0))
    if player_level < req:
        return False, f"레벨 부족 (필요 {req}, 보유 {player_level})"
    sidx = int(book.get("skill_index", 0))
    have = int(current_skill_levels.get(sidx, 0))
    book_lvl = int(book.get("skill_level", 1))
    if have >= book_lvl:
        return False, f"이미 LV{have} 보유"
    return True, ""


def main() -> None:
    if not ITEMS_JSON.exists():
        print(f"[skip] {ITEMS_JSON} 미발견")
        return
    data = json.loads(ITEMS_JSON.read_text(encoding="utf-8"))

    slot_16 = data.get("slot_16", [])
    slot_17 = data.get("slot_17", [])
    print(f"# Round 57 SkillBook 검증 — slot_16={len(slot_16)} / slot_17={len(slot_17)}")
    assert len(slot_16) == 95, f"slot_16 (W/R) = {len(slot_16)} (95 기대)"
    assert len(slot_17) == 98, f"slot_17 (G/K) = {len(slot_17)} (98 기대)"

    # 1. (class_id // 2) + 16 슬롯 매핑 정확성
    for cid in range(4):
        expected = (cid // 2) + 16
        actual_slot = data.get(f"slot_{expected}", [])
        cls_books = [b for b in actual_slot if int(b.get("class_id", -1)) == cid]
        print(f"  class {cid} ({CLASS_NAMES[cid]:5s}) → slot_{expected} : {len(cls_books)} books")
        # 해당 클래스 책이 자신 슬롯에 모두 있는지 (다른 슬롯에 침범 없는지)
        other_slot = data.get(f"slot_{(1 - cid // 2) + 16}", [])
        wrong_slot = [b for b in other_slot if int(b.get("class_id", -1)) == cid]
        assert not wrong_slot, f"class {cid} 책 {len(wrong_slot)} 개가 잘못된 slot 에 있음"

    # Sorcerer (cid=4) 책 = 없어야 함
    sorc_books = [b for b in slot_16 + slot_17 if int(b.get("class_id", -1)) == 4]
    print(f"  class 4 (소서러) — stub. 책 count: {len(sorc_books)} (0 기대)")
    assert len(sorc_books) == 0, "Sorcerer 책이 존재 — Round 22 의 stub 가설 위반"

    # 2. 모든 book 필드 range
    all_books = slot_16 + slot_17
    bad_class = 0
    bad_lvl = 0
    bad_req = 0
    skill_idx_dist: dict[int, Counter] = {0: Counter(), 1: Counter(), 2: Counter(), 3: Counter()}
    skill_lvl_dist: Counter = Counter()
    req_lvl_dist: Counter = Counter()
    for b in all_books:
        cid = int(b.get("class_id", -1))
        if cid not in (0, 1, 2, 3): bad_class += 1
        lvl = int(b.get("skill_level", 0))
        if lvl < 1 or lvl > 7: bad_lvl += 1
        req = int(b.get("required_level", -1))
        if req < 0 or req > 99: bad_req += 1
        sidx = int(b.get("skill_index", -1))
        if cid in skill_idx_dist:
            skill_idx_dist[cid][sidx] += 1
        skill_lvl_dist[lvl] += 1
        req_lvl_dist[req] += 1

    print(f"  bad class_id (∉ 0..3): {bad_class}")
    print(f"  bad skill_level (∉ 1..7): {bad_lvl}")
    print(f"  bad required_level (∉ 0..99): {bad_req}")
    print(f"  skill_level 분포: {dict(sorted(skill_lvl_dist.items()))}")
    print(f"  required_level 분포 (top 10): {dict(req_lvl_dist.most_common(10))}")
    for cid in (0, 1, 2, 3):
        unique = len(skill_idx_dist[cid])
        print(f"  class {cid} unique skill_index: {unique}")
    assert bad_class == 0
    assert bad_lvl == 0
    assert bad_req == 0

    # 3. learn 시뮬레이션 — Warrior (class 0) 의 첫 책 학습 → 같은 책 재학습 거부 → 다른 클래스 거부
    print("\n# learn 시뮬레이션 (Warrior, Lv.40):")
    warrior_books = [b for b in slot_16 if int(b.get("class_id", -1)) == 0]
    assert warrior_books, "Warrior 책 없음"
    levels: dict = {}   # 갓 시작한 캐릭 — 책으로 학습 가능
    first = warrior_books[0]
    ok, reason = can_learn(0, 40, levels, first)
    print(f"  case 1 (첫 책 학습): ok={ok} reason='{reason}'")
    assert ok, f"첫 책 학습이 거부됨: {reason}"
    levels[int(first["skill_index"])] = int(first["skill_level"])

    # 같은 책 재학습 — 거부
    ok, reason = can_learn(0, 40, levels, first)
    print(f"  case 2 (같은 책 재학습): ok={ok} reason='{reason}'")
    assert not ok, "같은 책 재학습이 허용됨 (거부 기대)"

    # 다른 클래스 책 (Rogue) — 거부
    rogue_book = next((b for b in slot_16 if int(b.get("class_id", -1)) == 1), None)
    assert rogue_book, "Rogue 책 없음"
    ok, reason = can_learn(0, 40, levels, rogue_book)
    print(f"  case 3 (다른 클래스 책): ok={ok} reason='{reason}'")
    assert not ok, "다른 클래스 책 학습이 허용됨 (거부 기대)"

    # 레벨 부족 — 가장 높은 required_level 책
    high_req = max(warrior_books, key=lambda b: int(b.get("required_level", 0)))
    if int(high_req["required_level"]) > 1:
        ok, reason = can_learn(0, 1, {0: 1}, high_req)
        print(f"  case 4 (레벨 부족, req={high_req['required_level']}): ok={ok} reason='{reason}'")
        assert not ok, "레벨 부족인데 학습 허용됨"

    # 같은 skill 더 높은 LV — 허용
    upgrade_book = None
    for b in warrior_books:
        if int(b["skill_index"]) == int(first["skill_index"]) and int(b["skill_level"]) > int(first["skill_level"]):
            upgrade_book = b
            break
    if upgrade_book:
        ok, reason = can_learn(0, 40, levels, upgrade_book)
        print(f"  case 5 (같은 skill LV{first['skill_level']}→LV{upgrade_book['skill_level']}): ok={ok} reason='{reason}'")
        assert ok, f"upgrade 책 학습이 거부됨: {reason}"
    else:
        print("  case 5: 같은 skill 의 upgrade 책 없음 (skip)")

    # 4. 첫 3 책 샘플
    print("\n# 첫 3 책 sample (Warrior):")
    for b in warrior_books[:3]:
        print(f"  '{b['name']}' — skill #{b['skill_index']} LV{b['skill_level']}  필요 Lv.{b['required_level']}  가격 {b['price']} G")

    print("\n# All checks passed.")


if __name__ == "__main__":
    main()
