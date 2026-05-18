"""Round 76 — active effect stat modifier 통합 검증.

R75 의 GameState.active_buffs/curses/stances Array 가 GameState.total_attack /
total_defense 에 영향. R74 helper signal → GameState.add_active_effect → stat 적용.

검증 항목:
  1. GameState.total_attack 가 active_buffs 의 f1 을 % bonus 로 적용 (clamp 0..200)
  2. GameState.total_defense 가 active_stances 의 f1 을 % bonus 로 적용 (clamp 0..150)
  3. GameState.total_defense 가 active_curses 의 f1 을 % reduction 으로 적용 (clamp 0..80)
  4. battle_system._enemy_turn 끝에서 GameState.tick_active_effects() 자동 호출
  5. R76 docstring markers (4 files — game_state.gd, battle_system.gd)
  6. Python 시뮬: stat modifier 의 정확한 산출 (buff/stance/curse 누적)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
GAME_STATE_GD = ROOT / "apps/hero5-godot/scripts/core/game_state.gd"
BATTLE_GD = ROOT / "apps/hero5-godot/scripts/core/battle_system.gd"


def main():
    print("# Round 76 active effect stat modifier 통합 검증\n")
    for p in (GAME_STATE_GD, BATTLE_GD):
        assert p.exists(), f"missing {p}"

    gs = GAME_STATE_GD.read_text(encoding="utf-8")
    bs = BATTLE_GD.read_text(encoding="utf-8")

    # 1. total_attack 에 active_buffs 반영
    print("# 1. GameState.total_attack 에 active_buffs % bonus 반영")
    # active_buffs loop in total_attack
    pat_buff_loop = r"func total_attack\(\)[\s\S]*?for entry in active_buffs:[\s\S]*?buff_pct\s*\+=[\s\S]*?return\s+raw\s*\*\s*\(100\s*\+\s*buff_pct\)\s*/\s*100"
    assert re.search(pat_buff_loop, gs), "total_attack 의 active_buffs loop + raw*(100+pct)/100 미발견"
    print(f"  ✓ total_attack(): for entry in active_buffs: buff_pct += entry.f1")
    print(f"  ✓ return raw × (100 + buff_pct) / 100")
    # clamp 0..200
    assert "clamp(buff_pct, 0, 200)" in gs, "buff_pct clamp(0, 200) 미발견"
    print(f"  ✓ buff_pct clamp 0..200")

    # 2. total_defense 에 active_stances + active_curses 반영
    print("\n# 2. GameState.total_defense 에 stance + curse % 반영")
    pat_def = r"func total_defense\(\)[\s\S]*?for entry in active_stances:[\s\S]*?stance_pct\s*\+=[\s\S]*?for entry in active_curses:[\s\S]*?curse_pct\s*\+=[\s\S]*?net_pct\s*=\s*100\s*\+\s*stance_pct\s*-\s*curse_pct"
    assert re.search(pat_def, gs), "total_defense 의 stance/curse loop + net_pct 계산 미발견"
    print(f"  ✓ total_defense(): stance_pct += active_stances.f1")
    print(f"  ✓ total_defense(): curse_pct += active_curses.f1")
    print(f"  ✓ net_pct = 100 + stance_pct - curse_pct")
    assert "clamp(stance_pct, 0, 150)" in gs, "stance_pct clamp(0, 150) 미발견"
    print(f"  ✓ stance_pct clamp 0..150")
    assert "clamp(curse_pct, 0, 80)" in gs, "curse_pct clamp(0, 80) 미발견"
    print(f"  ✓ curse_pct clamp 0..80")

    # 3. battle_system._enemy_turn 에서 tick_active_effects 자동 호출
    print("\n# 3. battle_system._enemy_turn 끝에서 tick_active_effects() 자동 호출")
    pat_tick = r"func _enemy_turn[\s\S]*?GameState\.tick_active_effects\(\)"
    assert re.search(pat_tick, bs), "_enemy_turn 안에서 GameState.tick_active_effects() 호출 미발견"
    print(f"  ✓ _enemy_turn() → GameState.tick_active_effects()")

    # 4. R76 docstring markers
    print("\n# 4. R76 docstring markers")
    for marker in ("Round 76", "active_buffs", "ATK % bonus", "stance", "curse"):
        assert marker in gs, f"game_state.gd 의 R76 docstring 에 '{marker}' 누락"
        print(f"  ✓ game_state.gd: '{marker}'")
    for marker in ("Round 76", "tick_active_effects"):
        assert marker in bs, f"battle_system.gd 의 R76 docstring 에 '{marker}' 누락"
        print(f"  ✓ battle_system.gd: '{marker}'")

    # 5. Python 시뮬: stat modifier 산출
    print("\n# 5. Python 시뮬: stat modifier 정확 산출")

    def compute_total_attack(base: int, equip: int, buffs: list[int]) -> int:
        raw = base + equip
        buff_pct = sum(buffs)
        buff_pct = max(0, min(200, buff_pct))
        return raw * (100 + buff_pct) / 100

    def compute_total_defense(base: int, equip: int, stances: list[int], curses: list[int]) -> int:
        raw = base + equip
        stance_pct = max(0, min(150, sum(stances)))
        curse_pct = max(0, min(80, sum(curses)))
        net_pct = 100 + stance_pct - curse_pct
        return raw * net_pct / 100

    # buff: 100 base × (100+20)% = 120
    actual = compute_total_attack(80, 20, [20])
    expected = 120
    assert int(actual) == expected, f"buff 20%: expected {expected}, got {actual}"
    print(f"  ✓ buff 20%: base 80 + equip 20 = 100 → 100×120%=120")

    # 누적 buff: 100 × (100+30+20)% = 150
    actual = compute_total_attack(50, 50, [30, 20])
    expected = 150
    assert int(actual) == expected, f"buff 30+20%: expected {expected}, got {actual}"
    print(f"  ✓ buff 누적 30+20%: 100 → 150")

    # buff clamp 200: 100 × (100+200)% = 300 (입력 250 → clamp 200)
    actual = compute_total_attack(50, 50, [250])
    expected = 300
    assert int(actual) == expected, f"buff clamp 200%: expected {expected}, got {actual}"
    print(f"  ✓ buff clamp 200%: 입력 250% → 적용 200% (100→300)")

    # stance: 50 base × (100+50)% = 75
    actual = compute_total_defense(30, 20, [50], [])
    expected = 75
    assert int(actual) == expected, f"stance 50%: expected {expected}, got {actual}"
    print(f"  ✓ stance 50%: 50 → 75")

    # curse: 50 base × (100-30)% = 35
    actual = compute_total_defense(30, 20, [], [30])
    expected = 35
    assert int(actual) == expected, f"curse 30%: expected {expected}, got {actual}"
    print(f"  ✓ curse 30%: 50 → 35")

    # stance + curse 동시: 100 × (100+50-30)% = 120
    actual = compute_total_defense(50, 50, [50], [30])
    expected = 120
    assert int(actual) == expected, f"stance+curse: expected {expected}, got {actual}"
    print(f"  ✓ stance 50% + curse 30%: 100 → 120 (net +20%)")

    # curse clamp 80: 100 × (100-80)% = 20 (입력 120 → clamp 80)
    actual = compute_total_defense(50, 50, [], [120])
    expected = 20
    assert int(actual) == expected, f"curse clamp 80%: expected {expected}, got {actual}"
    print(f"  ✓ curse clamp 80%: 입력 120% → 적용 80% (100→20)")

    # 6. game_state.gd 의 tick_active_effects 가 state_changed emit
    print("\n# 6. tick_active_effects 가 state_changed.emit() 호출")
    pat_tick_emit = r"func tick_active_effects[\s\S]*?state_changed\.emit\(\)"
    assert re.search(pat_tick_emit, gs), "tick_active_effects 가 state_changed emit 안 함"
    print(f"  ✓ tick_active_effects() → state_changed.emit()")

    # 7. status_panel.gd 가 state_changed 를 listen
    print("\n# 7. status_panel 의 state_changed listener")
    sp = (ROOT / "apps/hero5-godot/scripts/ui/status_panel.gd").read_text(encoding="utf-8")
    assert "GameState.state_changed.connect" in sp, "status_panel 가 state_changed 에 connect 안 함"
    print(f"  ✓ status_panel._ready(): GameState.state_changed.connect(_on_state_changed)")
    assert "func _on_state_changed()" in sp, "status_panel._on_state_changed() handler 미발견"
    print(f"  ✓ status_panel._on_state_changed() handler")
    assert "if visible: _apply()" in sp, "_on_state_changed 의 visible guard 미발견"
    print(f"  ✓ _on_state_changed: visible 일 때만 _apply() — redraw 회피")

    print("\n# All Round 76 active effect stat modifier checks passed.")


if __name__ == "__main__":
    main()
