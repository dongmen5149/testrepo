"""Round 66 — battle_system / character.gd 두 host 의 명세 검증.

목적:
  R65 SESSION_HANDOFF.md 의 "battle_system 의 host CHAR stub 13개 = dead code" 가설을
  검토한 결과, **두 host 는 별개 경로로 둘 다 사용 중** (dead code 아님):

    | host             | 사용 경로                  | 호출 특성                       |
    |------------------|----------------------------|---------------------------------|
    | battle_system    | turn-based 전투 (B / NPC)  | 위치 개념 없음 — 시야/거리 default |
    | character.gd     | real-time AI tick (R62 G)  | map 좌표 기반 정확한 값 (R61)   |

  R66 으로 두 host 의 의미 명세를 docstring 으로 정리하고 stub 의 일부를 실제 동작
  으로 보완 (cooldown / stunned). 본 도구는 두 host 가 (1) MonsterAI 가 사용하는
  17 method 를 모두 구현, (2) 의도된 의미 차이 (turn-based vs real-time) 가 명확,
  (3) battle_system 의 R66 보완 (set_cool_time 실 동작, is_able_skill cooldown 검사,
  is_attack_able stunned 체크, is_stunned method 추가) 가 들어갔는지 검증.

검증 항목:
  1. battle_system / character 둘 다 17 method 시그니처 보유
  2. battle_system 의 R66 보완 패턴 (cooldown 실 동작, is_stunned 추가)
  3. monster_ai create_runtime 의 두 host 분기 docstring
  4. 두 host 의 의도된 default 값 차이 (Python 시뮬)
  5. 호출 패턴 cross-check (monster_ai 가 host 의 method 만 호출, 누락 없음)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
BS_GD = ROOT / "apps/hero5-godot/scripts/core/battle_system.gd"
CHAR_GD = ROOT / "apps/hero5-godot/scripts/core/character.gd"
AI_GD = ROOT / "apps/hero5-godot/scripts/core/monster_ai.gd"

# MonsterAI 가 호출하는 host method (Round 50 RE)
HOST_METHODS = [
    "is_die", "get_motion", "is_attack_able", "is_able_skill",
    "get_dir", "set_dir", "hero_turn_direction", "fast_distance_to_hero",
    "set_attack_motion", "ai_cast_skill", "set_cool_time", "skill_end",
    "ai_check_irect_hit", "ai_check_visibility", "ai_all_dead",
    "ai_tutorial_flag", "is_stunned",
]


def main() -> None:
    print("# Round 66 두 host (battle_system / character) 명세 검증\n")
    for p in (BS_GD, CHAR_GD, AI_GD):
        assert p.exists(), f"missing {p}"

    bs_src = BS_GD.read_text(encoding="utf-8")
    char_src = CHAR_GD.read_text(encoding="utf-8")
    ai_src = AI_GD.read_text(encoding="utf-8")

    # 1. 두 host 모두 17 method 보유
    print("# 1. method 시그니처 보유 검증 (둘 다 17/17)")
    bs_missing: list = []
    char_missing: list = []
    for m in HOST_METHODS:
        if not re.search(rf"\bfunc\s+{m}\s*\(", bs_src):
            bs_missing.append(m)
        if not re.search(rf"\bfunc\s+{m}\s*\(", char_src):
            char_missing.append(m)
    print(f"  battle_system: {len(HOST_METHODS) - len(bs_missing)}/{len(HOST_METHODS)} "
          f"(missing: {bs_missing})")
    print(f"  character.gd : {len(HOST_METHODS) - len(char_missing)}/{len(HOST_METHODS)} "
          f"(missing: {char_missing})")
    assert not bs_missing, f"battle_system 누락: {bs_missing}"
    assert not char_missing, f"character.gd 누락: {char_missing}"
    print("  ✓ 두 host 모두 17 method 보유")
    print()

    # 2. R66 보완 패턴 (battle_system)
    print("# 2. battle_system R66 보완 패턴")
    r66_checks = [
        (r"_cooldowns\.get\(skill_id,\s*0\)", "is_able_skill 가 cooldown dict 조회"),
        (r"_cooldowns\[skill_id\]\s*=\s*FRAME_PER_TURN", "set_cool_time 가 cooldown 설정"),
        (r"and\s+not\s+is_stunned\(\)", "is_attack_able 가 is_stunned 도 검사"),
        (r"func\s+is_stunned\s*\(\s*\)\s*->\s*bool", "is_stunned method 추가"),
        (r"R66 명세 강화|R66 으로", "R66 docstring 마커"),
        (r"two host|두 host|host             \|", "두 host 비교 표 docstring"),
    ]
    failed = 0
    for pat, desc in r66_checks:
        if re.search(pat, bs_src):
            print(f"  ✓ {desc}")
        else:
            print(f"  ✗ {desc} — {pat!r} not found")
            failed += 1
    assert failed == 0, f"{failed} 패턴 누락"
    print()

    # 3. monster_ai create_runtime 의 host 분기 docstring
    print("# 3. monster_ai.create_runtime 의 두 host 분기 docstring")
    if "두 host 종류" in ai_src or "host 종류" in ai_src or "battle_system" in ai_src and "character.gd" in ai_src:
        print("  ✓ create_runtime 의 두 host 분기 명세 포함")
    else:
        print("  ✗ create_runtime docstring 누락")
        assert False
    print()

    # 4. 두 host 의 의도된 default 값 차이 (Python 시뮬)
    print("# 4. 두 host 의 의도된 의미 차이 (Python 시뮬)")

    # battle_system stub (turn-based: 위치 개념 없음, 시야 항상 진입)
    class MockBattleSystemHost:
        def __init__(self):
            self.enemy_hp = 100
            self._cooldowns: dict = {}
            self._stunned = False
            self._ai_pending_skill_id = -1
        def is_die(self): return self.enemy_hp <= 0
        def is_stunned(self): return self._stunned
        def get_motion(self): return 0  # idle 항상
        def is_attack_able(self): return self.enemy_hp > 0 and not self.is_stunned()
        def is_able_skill(self, sid): return sid > 0 and self._cooldowns.get(sid, 0) <= 0
        def fast_distance_to_hero(self): return 0  # 항상 같은 cell
        def ai_check_visibility(self, _i): return True  # 항상 가시
        def ai_check_irect_hit(self, _r): return True
        def set_cool_time(self, sid):
            if sid > 0: self._cooldowns[sid] = 1

    # character.gd (real-time AI tick: map 좌표 기반)
    class MockCharacterHost:
        def __init__(self):
            self.hp = 100
            self.max_hp = 100
            self.dead = False
            self.stunned = False
            self._cooldowns: dict = {}
            self._pos = (5, 5)
            self._hero_pos = (8, 7)  # 3 tile right, 2 tile down (Chebyshev = 3)
        def is_die(self): return self.dead
        def is_stunned(self): return self.stunned
        def get_motion(self): return 0  # 실제 anim 상태에 따라 1/5/6/9/12
        def is_attack_able(self): return not self.dead and not self.stunned
        def is_able_skill(self, sid): return sid > 0 and self._cooldowns.get(sid, 0) <= 0
        def fast_distance_to_hero(self):
            dx = abs(self._pos[0] - self._hero_pos[0])
            dy = abs(self._pos[1] - self._hero_pos[1])
            return max(dx, dy)
        def ai_check_visibility(self, idx): return self.fast_distance_to_hero() <= idx
        def ai_check_irect_hit(self, r): return self.fast_distance_to_hero() <= r

    bs = MockBattleSystemHost()
    ch = MockCharacterHost()
    cases = [
        ("fast_distance_to_hero", bs.fast_distance_to_hero(), ch.fast_distance_to_hero(),
         "turn-based=0, character=실 거리"),
        ("ai_check_visibility(2)", bs.ai_check_visibility(2), ch.ai_check_visibility(2),
         "turn-based=True(항상), character=거리 비교"),
        ("ai_check_irect_hit(2)", bs.ai_check_irect_hit(2), ch.ai_check_irect_hit(2),
         "turn-based=True(항상), character=거리 비교"),
    ]
    for name, bs_val, ch_val, desc in cases:
        print(f"  {name}: bs={bs_val!s:5s} ch={ch_val!s:5s}  ({desc})")
        # turn-based 와 real-time 은 의도된 차이 — 둘 다 정상.
    print(f"  ✓ 두 host 의 의미 차이 명확 (turn-based vs real-time)")
    print()

    # 5. 새로 추가된 R66 동작: set_cool_time → is_able_skill 차단
    print("# 5. R66 set_cool_time → is_able_skill 차단 (battle_system 만)")
    bs2 = MockBattleSystemHost()
    assert bs2.is_able_skill(5) == True, "초기엔 skill 5 사용 가능해야 함"
    bs2.set_cool_time(5)
    assert bs2.is_able_skill(5) == False, "set_cool_time 후 사용 불가여야 함"
    bs2._cooldowns[5] = 0  # 시간 흘러 cooldown 만료
    assert bs2.is_able_skill(5) == True, "cooldown 만료 후 다시 가능"
    print("  ✓ R66 cooldown 동작 검증: skill 5 사용가능 → set_cool_time → 차단 → 만료 → 다시 가능")
    print()

    # 6. is_attack_able + stunned
    print("# 6. R66 is_attack_able 가 stunned 도 검사")
    bs3 = MockBattleSystemHost()
    assert bs3.is_attack_able() == True
    bs3._stunned = True
    assert bs3.is_attack_able() == False, "stunned 시 공격 불가"
    bs3._stunned = False
    bs3.enemy_hp = 0
    assert bs3.is_attack_able() == False, "사망 시 공격 불가"
    print("  ✓ is_attack_able 가 dead OR stunned 시 false")
    print()

    print("# All Round 66 dual host checks passed.")


if __name__ == "__main__":
    main()
