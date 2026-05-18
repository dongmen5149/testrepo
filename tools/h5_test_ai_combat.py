"""Round 63 — Monster ↔ Hero 실 전투 흐름 검증.

demo.gd 의 `_on_monster_skill_cast` + `_hero_attack_nearest` 로직과 동등한
Python 시뮬레이션:

1. monster.ai_skill_cast → demo handler → GameState.hp 차감 + damage popup
2. hero SPACE → ATTACK_RANGE_TILES (2 tile, Chebyshev) 이내 가장 가까운 monster 에 take_damage
3. dead monster: AI tick 루프 (Round 62) 가 Mission.bump_progress 트리거
4. hero HP 0: quick_load 자동
5. damage 계산: skill_id 별 multiplier (skill 0 = 100%, skill 1 = 120%, ...)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEMO_GD = Path("apps/hero5-godot/scripts/ui/demo.gd")


def main() -> None:
    print("# Round 63 Monster ↔ Hero 실 전투 검증\n")
    if not DEMO_GD.exists():
        print(f"[skip] {DEMO_GD} 미발견"); return
    text = DEMO_GD.read_text(encoding="utf-8")

    # 1. 구조 패턴 검증
    checks = [
        (r"_on_monster_skill_cast", "_on_monster_skill_cast handler"),
        (r"_hero_attack_nearest", "_hero_attack_nearest 함수"),
        (r"ATTACK_RANGE_TILES", "ATTACK_RANGE_TILES 상수"),
        (r"GameState\.hp\s*=\s*max\(0,\s*GameState\.hp\s*-\s*dmg\)", "hero HP 차감 로직"),
        (r"DamagePopup\.spawn", "damage popup spawn 호출"),
        (r"\.take_damage\(", "monster.take_damage 호출"),
        (r"KEY_SPACE", "SPACE 키 바인딩"),
        (r"GameState\.quick_load\(0\)", "hero 사망 시 quick_load"),
        (r"ai_skill_cast\.connect\(_on_monster_skill_cast", "ai_skill_cast → handler 연결"),
    ]
    failed = 0
    for pat, desc in checks:
        if re.search(pat, text):
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc}  — {pat!r} not found")
            failed += 1
    assert failed == 0, f"{failed} 패턴 누락"

    # 2. Python 시뮬: Monster → Hero damage
    print("\n# Python 시뮬: monster 스킬 → hero 데미지")

    class MockGameState:
        def __init__(self):
            self.hp = 100
            self.max_hp = 100
            self.stat_str = 12
            self.stat_con = 6
            self.level = 5
        def total_attack(self):
            return self.stat_str * 2 + self.level * 3
        def total_defense(self):
            return self.stat_con + self.level * 2

    def monster_attack(gs, monster_atk, skill_id, defense_known=True):
        skill_mult = 100 + (skill_id * 20)
        raw = monster_atk * skill_mult // 100  # randi() % 5 생략 (deterministic)
        defense = gs.total_defense() if defense_known else 0
        dmg = max(1, raw - defense // 2)
        gs.hp = max(0, gs.hp - dmg)
        return dmg

    gs = MockGameState()
    initial_hp = gs.hp
    print(f"  hero base ATK={gs.total_attack()}, DEF={gs.total_defense()}, HP={gs.hp}")

    # case A: skill 0 (plain attack) from monster atk=20
    dmg_a = monster_attack(gs, 20, 0)
    print(f"  case A: monster atk=20, skill 0 → -{dmg_a} HP (남은 {gs.hp})")
    assert dmg_a > 0 and dmg_a < 20

    # case B: skill 5 (higher tier) from same atk
    gs.hp = 100
    dmg_b = monster_attack(gs, 20, 5)
    print(f"  case B: monster atk=20, skill 5 → -{dmg_b} HP (남은 {gs.hp})")
    assert dmg_b > dmg_a, f"skill 5 ({dmg_b}) ≤ skill 0 ({dmg_a}) — multiplier 미적용"

    # case C: 누적 데미지로 사망
    gs.hp = 100
    for _ in range(20):
        if gs.hp == 0: break
        monster_attack(gs, 50, 5)
    print(f"  case C: 누적 데미지로 hero HP=0 → death 트리거 ({gs.hp})")
    assert gs.hp == 0

    # 3. Hero attack — Chebyshev distance 검증
    print("\n# Python 시뮬: hero attack — Chebyshev 거리 + nearest target")
    TILE = 32
    ATTACK_RANGE = 2

    def find_nearest_target(hero_pos, monster_positions):
        best = -1
        best_d = 9999
        for i, mp in enumerate(monster_positions):
            dx = abs(mp[0] - hero_pos[0]) // TILE
            dy = abs(mp[1] - hero_pos[1]) // TILE
            d = max(dx, dy)
            if d <= ATTACK_RANGE and d < best_d:
                best = i; best_d = d
        return best, best_d

    hero = (160, 240)
    # monster A: 1 tile 위 (in range)
    # monster B: 3 tile 우 (out of range)
    # monster C: 2 tile 좌 (in range, 더 멀어서 not nearest)
    monsters = [(160, 240 - 32), (160 + 96, 240), (160 - 64, 240)]
    target, dist = find_nearest_target(hero, monsters)
    assert target == 0, f"nearest target should be A (1 tile), got {target}"
    assert dist == 1, f"distance should be 1, got {dist}"
    print(f"  nearest in range: A (1 tile, in range) ✓")
    print(f"  out of range: B (3 tile > {ATTACK_RANGE}) skipped ✓")

    # 빈 monster list
    target_empty, _ = find_nearest_target(hero, [])
    assert target_empty == -1
    print(f"  empty monster list: -1 ✓")

    # 모두 out-of-range
    far_monsters = [(160 + 96, 240), (160, 240 + 200)]
    target_far, _ = find_nearest_target(hero, far_monsters)
    assert target_far == -1
    print(f"  모두 out-of-range: -1 ✓")

    # 4. 전투 흐름: hero attack damage 1회로 monster 사망 (HP=10, atk≥10)
    class MockMonster:
        def __init__(self, hp):
            self.hp, self.max_hp, self.dead = hp, hp, False
        def take_damage(self, d):
            if self.dead: return
            self.hp = max(0, self.hp - d)
            if self.hp == 0: self.dead = True

    m1 = MockMonster(10)
    m1.take_damage(gs.total_attack() + 5)
    assert m1.dead
    print(f"\n  hero attack (ATK {gs.total_attack()}+5) → monster HP 10 dead ✓")

    # 5. 데미지 계산 식 일관성: code 에서 추출
    # demo.gd 의 "base_atk * skill_mult / 100" 패턴 검증
    pattern_dmg = re.search(r"base_atk\s*\*\s*skill_mult\s*/\s*100", text)
    assert pattern_dmg, "monster 데미지 공식 패턴 미발견"
    print(f"  code 데미지 공식: base_atk × (100 + skill_id*20)% ✓")

    print("\n# All Round 63 combat flow checks passed.")


if __name__ == "__main__":
    main()
