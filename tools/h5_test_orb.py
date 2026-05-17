"""Orb socket mechanism 검증 (Round 54).

`apps/hero5-godot/scripts/core/game_data.gd::orb_bonus_for` /
`game_state.gd::add_orb_to_socket/remove_orb_from_socket` 의 GDScript 로직과
동등한 Python 구현 + items.json slot_12 sweep.

검증 사항:
1. slot_12 (orb) 53 entries 모두 정확 parse + 한국어 이름 0 miss.
2. orb_bonus_for 가 모든 orb 에 대해 음수 안 나옴 / 0..5 범위.
3. orb_group (idx/13) 분포 — 53 / 13 = 4 그룹 (Round 26 의 "3 그룹 × 13" 일부 일치).
4. socket encoding 검증 — 0 = 빈, n>0 = orb_idx (n-1) 매핑.
5. 5-socket fill 시 강도 2x rule (R26) 산술 검증.
6. add/remove 동작 — 빈 socket 검색 + 채워진 socket 제거 시퀀스.
"""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ITEMS_JSON = Path("apps/hero5-godot/assets/gamedata/items.json")


def orb_bonus_for(orb: dict) -> int:
    """game_data.gd::orb_bonus_for 와 동등."""
    price = int(orb.get("price", 0))
    if price <= 0: return 0
    return max(1, int(round(math.log10(max(1, price)))))


def add_orb_to_socket(sockets: list, orb_idx: int) -> int:
    """game_state.gd::add_orb_to_socket 등가."""
    for i in range(5):
        if sockets[i] == 0:
            sockets[i] = orb_idx + 1
            return i
    return -1


def remove_orb_from_socket(sockets: list, slot_idx: int) -> int:
    if slot_idx < 0 or slot_idx >= 5: return -1
    encoded = sockets[slot_idx]
    if encoded == 0: return -1
    sockets[slot_idx] = 0
    return encoded - 1


def compute_bonus(sockets: list, orbs: list) -> int:
    """equipment_bonus 안의 orb 계산 부분 등가."""
    total = 0
    for encoded in sockets:
        if encoded == 0: continue
        total += orb_bonus_for(orbs[encoded - 1])
    populated = sum(1 for s in sockets if s != 0)
    if populated >= 5:
        total *= 2
    return total


def main() -> None:
    if not ITEMS_JSON.exists():
        print(f"[skip] {ITEMS_JSON} 미발견")
        return
    data = json.loads(ITEMS_JSON.read_text(encoding="utf-8"))
    orbs = data.get("slot_12", [])
    print(f"# Round 54 Orb socket 검증 — {len(orbs)} orbs")
    assert len(orbs) == 53, f"orb 갯수 53 기대, got {len(orbs)}"

    # 1. 이름 / bonus / group 분포
    name_miss = 0
    bonus_dist: dict[int, int] = {}
    group_dist: dict[int, int] = {}
    price_dist: dict[int, int] = {}
    for i, orb in enumerate(orbs):
        nm = str(orb.get("name", ""))
        if not nm: name_miss += 1
        b = orb_bonus_for(orb)
        bonus_dist[b] = bonus_dist.get(b, 0) + 1
        g = i // 13
        group_dist[g] = group_dist.get(g, 0) + 1
        p = int(orb.get("price", 0))
        price_dist[p] = price_dist.get(p, 0) + 1
    print(f"  name miss: {name_miss}")
    print(f"  orb_bonus 분포: {dict(sorted(bonus_dist.items()))}")
    print(f"  orb_group 분포: {dict(sorted(group_dist.items()))}")
    print(f"  price 분포: {dict(sorted(price_dist.items()))}")
    assert name_miss == 0, f"{name_miss} orbs 이름 없음"
    for b in bonus_dist:
        assert b >= 0, f"음수 bonus: {b}"
        assert b <= 5, f"bonus 너무 큼: {b}"

    # 2. socket encoding 검증
    sockets = [0, 0, 0, 0, 0]
    assert add_orb_to_socket(sockets, 5) == 0, "첫 빈 socket 은 0"
    assert sockets == [6, 0, 0, 0, 0], f"encoding 오류: {sockets}"
    assert add_orb_to_socket(sockets, 10) == 1
    assert add_orb_to_socket(sockets, 15) == 2
    assert add_orb_to_socket(sockets, 20) == 3
    assert add_orb_to_socket(sockets, 25) == 4
    # 5 socket 다 채움 — 6번째는 -1
    assert add_orb_to_socket(sockets, 30) == -1
    assert sockets == [6, 11, 16, 21, 26], f"final sockets: {sockets}"
    print(f"  socket encoding: 5/5 fill OK, 6번째 -1 ✓")

    # 3. remove 동작
    removed = remove_orb_from_socket(sockets, 2)
    assert removed == 15, f"remove returned {removed}, expected 15"
    assert sockets == [6, 11, 0, 21, 26]
    # 비어있는 socket 제거 시도 → -1
    assert remove_orb_from_socket(sockets, 2) == -1
    # 잘못된 slot
    assert remove_orb_from_socket(sockets, 5) == -1
    assert remove_orb_from_socket(sockets, -1) == -1
    print(f"  remove 동작: 3/3 케이스 ✓")

    # 4. 강도 2x rule
    sockets = [6, 11, 16, 21, 0]  # 4 채움
    bonus_4 = compute_bonus(sockets, orbs)
    sockets[4] = 30
    bonus_5 = compute_bonus(sockets, orbs)
    # 5 채움 = 4채움 + (orb 30 bonus) 의 2x
    raw_5 = bonus_4 + orb_bonus_for(orbs[29])
    assert bonus_5 == raw_5 * 2, \
        f"5-socket 2x rule 위반: bonus_5={bonus_5}, raw*2={raw_5*2}"
    print(f"  5-socket 2x rule: {bonus_4} → {bonus_5} (raw {raw_5}) ✓")

    # 5. 4 vs 5 socket — 4 는 raw 그대로, 5 는 2x
    assert bonus_5 > bonus_4, "5-socket bonus 가 4-socket 보다 커야 함"

    # 6. 샘플 orb 이름 출력
    print("\n# 샘플 orb (15개):")
    for i in [0, 5, 10, 13, 20, 26, 30, 39, 50, 52]:
        nm = orbs[i].get("name", "")
        b = orb_bonus_for(orbs[i])
        g = i // 13
        p = orbs[i].get("price", 0)
        print(f"  [{i}] {nm}  bonus +{b}  group {g}  price {p}")

    print("\n# All checks passed.")


if __name__ == "__main__":
    main()
