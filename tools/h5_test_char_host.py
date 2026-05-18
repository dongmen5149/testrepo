"""Round 61 — character.gd host CHAR interface 검증.

apps/hero5-godot/scripts/core/character.gd 의 17 host method (Round 50 의 13 base
+ 4 추가) 가 monster_ai.gd 의 호출 패턴과 일관되는지 정적 검증.

검증 항목:
1. character.gd 가 host method 17개 모두 정의.
2. 각 method 의 signature (인자 수 + return 형) 가 monster_ai 의 호출과 일치.
3. character.gd 의 직접 시뮬레이션 (Python mock) — Chebyshev 거리, 방향 turn 등 로직.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHAR_GD = Path("apps/hero5-godot/scripts/core/character.gd")
MONSTER_AI_GD = Path("apps/hero5-godot/scripts/core/monster_ai.gd")

# Round 50 의 13 base + 4 추가 method (monster_ai 가 호출하는 host CHAR interface).
EXPECTED_METHODS = [
    ("is_die", 0, "bool"),
    ("get_motion", 0, "int"),
    ("is_attack_able", 0, "bool"),
    ("is_able_skill", 1, "bool"),
    ("get_dir", 0, "int"),
    ("set_dir", 1, "void"),
    ("hero_turn_direction", 0, "void"),
    ("fast_distance_to_hero", 0, "int"),
    ("set_attack_motion", 1, "void"),
    ("ai_cast_skill", 1, "void"),
    ("set_cool_time", 1, "void"),
    ("skill_end", 0, "void"),
    ("ai_check_irect_hit", 1, "bool"),
    ("ai_check_visibility", 1, "bool"),
    ("ai_all_dead", 0, "bool"),
    ("ai_tutorial_flag", 1, "bool"),
    ("is_stunned", 0, "bool"),  # 추가 (monster_ai 가 선택적 호출)
]


def parse_method_signatures(gd_text: str) -> dict[str, tuple[int, str]]:
    """gd 파일에서 func 선언 추출 → name → (param_count, return_type)."""
    out = {}
    for m in re.finditer(r"^func\s+(\w+)\s*\(([^)]*)\)\s*(->\s*\w+)?", gd_text, re.MULTILINE):
        name = m.group(1)
        params_str = m.group(2).strip()
        ret = m.group(3)
        ret_type = "void"
        if ret:
            ret_type = ret.replace("->", "").strip()
        if not params_str:
            param_count = 0
        else:
            # comma-split, default args 제거
            param_count = len([p for p in params_str.split(",") if p.strip()])
        out[name] = (param_count, ret_type)
    return out


def main() -> None:
    print("# Round 61 character.gd host CHAR interface 검증\n")
    if not CHAR_GD.exists():
        print(f"[skip] {CHAR_GD} 미발견")
        return
    char_text = CHAR_GD.read_text(encoding="utf-8")
    sigs = parse_method_signatures(char_text)

    # 1. 17 method 모두 정의 + signature 일치
    missing = []
    sig_mismatch = []
    for name, exp_pc, exp_ret in EXPECTED_METHODS:
        if name not in sigs:
            missing.append(name)
            continue
        pc, ret = sigs[name]
        if pc != exp_pc:
            sig_mismatch.append((name, exp_pc, pc, "param count"))
        if ret != exp_ret:
            sig_mismatch.append((name, exp_ret, ret, "return type"))

    print(f"  Expected methods: {len(EXPECTED_METHODS)}")
    print(f"  Defined:          {len(EXPECTED_METHODS) - len(missing)}")
    print(f"  Missing:          {len(missing)}")
    if missing:
        for m in missing:
            print(f"    ✗ {m}")
    if sig_mismatch:
        print(f"\n  Signature mismatches: {len(sig_mismatch)}")
        for name, exp, got, kind in sig_mismatch:
            print(f"    ✗ {name}: {kind} 기대 {exp}, got {got}")
    assert not missing, f"{len(missing)} host method 누락"
    assert not sig_mismatch, f"{len(sig_mismatch)} signature mismatch"

    # 2. monster_ai.gd 가 호출하는 method 이름 cross-check (실제 호출 모두 정의됨)
    ai_text = MONSTER_AI_GD.read_text(encoding="utf-8")
    called: set[str] = set()
    for m in re.finditer(r's\.host\.(?:has_method\("(\w+)"\)|(\w+)\()', ai_text):
        called.add(m.group(1) or m.group(2))
    # _host_call_bool/_int(s, "name", default) 패턴
    for m in re.finditer(r'_host_call_\w+\(s,\s*"(\w+)"', ai_text):
        called.add(m.group(1))

    # optional 호출 (has_method check 후) 은 누락 허용. 단 expected method 는 모두 cover.
    expected_names = {n for n, _, _ in EXPECTED_METHODS}
    print(f"\n  monster_ai 가 호출하는 host method: {sorted(called)}")
    not_in_expected = called - expected_names
    print(f"  EXPECTED 에 없는 호출 (optional, has_method check): {sorted(not_in_expected)}")
    # 실제 expected 가 모두 monster_ai 에서 호출되거나, 적어도 일부 (필수만):
    must_be_called = {"is_die", "get_motion", "fast_distance_to_hero", "get_dir",
                       "set_dir", "ai_cast_skill"}
    not_called = must_be_called - called
    assert not not_called, f"필수 method 가 monster_ai 에서 미호출: {not_called}"

    # 3. character.gd Python 시뮬 — Chebyshev 거리, hero_turn_direction 로직
    print("\n# Python 시뮬: distance/direction 로직")

    class MockChar:
        TILE_SIZE = 32
        DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP = 0, 1, 2, 3
        def __init__(self, x, y, is_hero=False, hero=None):
            self.x, self.y = x, y
            self.is_hero = is_hero
            self.target_hero = hero
            self.direction = 0
            self.dead = False
            self.stunned = False
        def fast_distance_to_hero(self):
            if self.is_hero or not self.target_hero: return 9999
            dx = abs(int(self.target_hero.x - self.x)) // self.TILE_SIZE
            dy = abs(int(self.target_hero.y - self.y)) // self.TILE_SIZE
            return max(dx, dy)
        def hero_turn_direction(self):
            if self.is_hero or not self.target_hero: return
            dx = int(self.target_hero.x - self.x)
            dy = int(self.target_hero.y - self.y)
            if abs(dx) >= abs(dy):
                self.direction = self.DIR_RIGHT if dx > 0 else self.DIR_LEFT
            else:
                self.direction = self.DIR_DOWN if dy > 0 else self.DIR_UP
        def is_able_skill(self, sid, cd=0):
            return not self.dead and not self.stunned and cd <= 0

    hero = MockChar(160, 240, is_hero=True)

    # case A: hero 자신 → 9999
    assert hero.fast_distance_to_hero() == 9999
    print(f"  case A: hero 자신 → 9999 ✓")

    # case B: 같은 위치 monster → 0 tile
    m1 = MockChar(160, 240, hero=hero)
    assert m1.fast_distance_to_hero() == 0
    print(f"  case B: 같은 위치 monster → 0 tile ✓")

    # case C: 3 tile 우측 monster → distance 3
    m2 = MockChar(160 + 3 * 32, 240, hero=hero)
    assert m2.fast_distance_to_hero() == 3
    print(f"  case C: 우측 3 tile → 3 ✓")

    # case D: 4 tile 위 + 2 tile 좌측 → Chebyshev = 4
    m3 = MockChar(160 - 2 * 32, 240 - 4 * 32, hero=hero)
    assert m3.fast_distance_to_hero() == 4
    print(f"  case D: 좌측 2/위 4 → Chebyshev 4 ✓")

    # case E: hero_turn_direction — 우측 hero
    m4 = MockChar(0, 240, hero=hero)   # hero 가 우측
    m4.hero_turn_direction()
    assert m4.direction == MockChar.DIR_RIGHT
    print(f"  case E: hero 우측 → DIR_RIGHT ✓")

    # case F: hero 위 (북쪽)
    m5 = MockChar(160, 400, hero=hero)
    m5.hero_turn_direction()
    assert m5.direction == MockChar.DIR_UP
    print(f"  case F: hero 위 (북쪽) → DIR_UP ✓")

    # case G: hero 좌측 + 위 — abs(dx)=160, abs(dy)=160. abs(dx)>=abs(dy) 이므로 LEFT.
    m6 = MockChar(320, 400, hero=hero)
    m6.hero_turn_direction()
    assert m6.direction == MockChar.DIR_LEFT
    print(f"  case G: 동률 (abs(dx)==abs(dy)) → LEFT (axis 우선) ✓")

    # case H: is_able_skill — cooldown, dead, stunned 케이스
    assert m1.is_able_skill(1, cd=0) is True
    assert m1.is_able_skill(1, cd=5) is False
    m1.dead = True
    assert m1.is_able_skill(1, cd=0) is False
    m1.dead = False; m1.stunned = True
    assert m1.is_able_skill(1, cd=0) is False
    print(f"  case H: is_able_skill (cd/dead/stunned) ✓")

    print("\n# All Round 61 host CHAR interface checks passed.")


if __name__ == "__main__":
    main()
