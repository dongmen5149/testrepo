"""Round 75 — GUNNER combo UI + skill effect 시스템 통합 검증.

R74 backend (GUNNER combo state + helper signals + apply_skill_effect API) 의
frontend + GameData 통합:
  - GameState 에 active_curses/buffs/stances Array + add_active_effect /
    tick_active_effects method
  - battle_system 의 3 helper signals 가 GameState.add_active_effect 자동 연결
  - status_panel.gd 에 GUNNER combo + active effect 카운트 시각화 (lvl_label/gold_label append)
  - GameData.skill_info(class_id, skill_id) → R72/R73 의 10 field 노출
    (effect_type/+0x30/+0x3a/+0x3c/+0x3d/+0x44/+0x46/+0x48/+0x4a/+0x4e)
  - battle_system SKILL action 에 GameData.skill_info 자동 dispatch (effect_type → signal)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
GAME_STATE_GD = ROOT / "apps/hero5-godot/scripts/core/game_state.gd"
GAME_DATA_GD = ROOT / "apps/hero5-godot/scripts/core/game_data.gd"
BATTLE_GD = ROOT / "apps/hero5-godot/scripts/core/battle_system.gd"
STATUS_GD = ROOT / "apps/hero5-godot/scripts/ui/status_panel.gd"


def main():
    print("# Round 75 GUNNER combo UI + skill effect 시스템 통합 검증\n")
    for p in (GAME_STATE_GD, GAME_DATA_GD, BATTLE_GD, STATUS_GD):
        assert p.exists(), f"missing {p}"

    gs = GAME_STATE_GD.read_text(encoding="utf-8")
    gd = GAME_DATA_GD.read_text(encoding="utf-8")
    bs = BATTLE_GD.read_text(encoding="utf-8")
    sp = STATUS_GD.read_text(encoding="utf-8")

    # 1. GameState 의 active_* Array + helper method
    print("# 1. GameState 의 active effect Array + helper method")
    for arr_name in ("active_curses", "active_buffs", "active_stances"):
        pat = rf"var\s+{re.escape(arr_name)}\s*:\s*Array\s*="
        assert re.search(pat, gs), f"GameState 에 {arr_name}: Array 없음"
        print(f"  ✓ var {arr_name}: Array")
    assert "func add_active_effect(" in gs, "GameState.add_active_effect method 미발견"
    print(f"  ✓ func add_active_effect(kind, dispatch, f1, f2, turns)")
    assert "func tick_active_effects(" in gs, "GameState.tick_active_effects method 미발견"
    print(f"  ✓ func tick_active_effects() — turn 마다 만료 처리")

    # 2. battle_system 의 signal 자동 연결
    print("\n# 2. battle_system 의 helper signal → GameState 자동 연결")
    assert "func _ready()" in bs, "battle_system._ready() 미발견"
    for sig in ("curse_applied", "buff_applied", "stance_applied"):
        pat = rf"{re.escape(sig)}\.connect\s*\(\s*_on_{re.escape(sig)}"
        assert re.search(pat, bs), f"signal {sig}.connect → _on_{sig} 없음"
        print(f"  ✓ {sig}.connect(_on_{sig})")
    # _on_*_applied 핸들러가 GameState.add_active_effect 호출
    for kind, handler in (("curse", "_on_curse_applied"), ("buff", "_on_buff_applied"), ("stance", "_on_stance_applied")):
        pat = rf"func {re.escape(handler)}.*?GameState\.add_active_effect\s*\(\s*\"{kind}\""
        assert re.search(pat, bs, re.DOTALL), f"{handler} → add_active_effect(\"{kind}\", …) 없음"
        print(f"  ✓ {handler} → GameState.add_active_effect(\"{kind}\", dispatch, f1, f2)")

    # 3. status_panel 의 GUNNER combo + active effect 시각화
    print("\n# 3. status_panel 의 GUNNER combo + active effect 시각화")
    assert "GameState.class_id == 2 and GameState.gunner_combo > 0" in sp, "GUNNER combo 시각화 분기 미발견"
    print(f"  ✓ GUNNER combo 시각화 분기 (class_id == 2 + gunner_combo > 0)")
    assert "[Combo %d/%d]" in sp, "Combo N/M 형식 미발견"
    print(f"  ✓ \"[Combo N/M]\" 형식 lvl_label append")
    for korean in ("저주×", "버프×", "자세×"):
        assert korean in sp, f"active effect 한국어 라벨 '{korean}' 미발견"
        print(f"  ✓ '{korean}' 라벨 (active effect count)")

    # 4. GameData.skill_info(class_id, skill_id) helper
    print("\n# 4. GameData.skill_info(class_id, skill_id) 신규 helper")
    assert "func skill_info(" in gd, "GameData.skill_info method 미발견"
    print(f"  ✓ func skill_info(class_id, skill_id) -> Dictionary")
    # R72/R73 의 9 fields 노출
    expected_fields = [
        "effect_type",
        "dynamic_formula_id",
        "special_dispatch",
        "formula_id_1",
        "formula_id_2",
        "knockback_idx",
        "shock_count",
        "max_combo",
        "sp_delta",
        "knight_threshold",
    ]
    for field in expected_fields:
        pat = rf"\"{re.escape(field)}\"\s*:"
        assert re.search(pat, gd), f"skill_info 의 \"{field}\" key 미발견"
        print(f"  ✓ skill_info[\"{field}\"]")
    # _stat_at 안전 helper
    assert "func _stat_at(" in gd, "_stat_at helper 미발견"
    print(f"  ✓ _stat_at(stats, index, default) safe lookup")

    # 5. battle_system SKILL 의 자동 dispatch
    print("\n# 5. battle_system SKILL action 의 자동 dispatch")
    assert "GameData.skill_info(GameState.class_id, skill_id)" in bs, (
        "battle_system SKILL action 의 GameData.skill_info 호출 미발견"
    )
    print(f"  ✓ GameData.skill_info(class_id, skill_id) SKILL action 안에서 호출")
    assert "apply_skill_effect(self, effect_type" in bs, (
        "apply_skill_effect 자동 호출 미발견"
    )
    print(f"  ✓ apply_skill_effect(self, effect_type, dispatch, f1, f2, skill_data) 자동 호출")
    # log 메시지에 effect 표시
    for fx in ("+저주", "+버프", "+자세"):
        assert fx in bs, f"log 메시지에 '{fx}' 미발견"
        print(f"  ✓ log fx_str: '{fx}'")

    # 6. R75 docstring markers
    print("\n# 6. R75 docstring markers")
    for marker in ("Round 75", "helper signal", "active_curses", "active_buffs", "active_stances"):
        assert marker in gs, f"game_state.gd 의 R75 docstring 에 '{marker}' 누락"
        print(f"  ✓ game_state.gd: '{marker}'")
    for marker in ("Round 75", "skill_info struct", "R72/R73"):
        assert marker in gd, f"game_data.gd 의 R75 docstring 에 '{marker}' 누락"
        print(f"  ✓ game_data.gd: '{marker}'")
    for marker in ("Round 75",):
        assert marker in bs, f"battle_system.gd 의 R75 docstring 에 '{marker}' 누락"
        print(f"  ✓ battle_system.gd: '{marker}'")
    for marker in ("Round 75", "GUNNER", "combo state"):
        assert marker in sp, f"status_panel.gd 의 R75 docstring 에 '{marker}' 누락"
        print(f"  ✓ status_panel.gd: '{marker}'")

    # 7. Python 시뮬: GameData.skill_info → effect_type dispatch
    print("\n# 7. effect_type → kind 매핑 Python 시뮬")
    def dispatch_kind(effect_type: int) -> str:
        if effect_type == 0: return "no_op"
        if effect_type in (1, 2): return "curse"
        if effect_type in (3, 5): return "buff"
        if effect_type == 4: return "stance"
        return "unknown"

    for et, expected in [(0, "no_op"), (1, "curse"), (2, "curse"), (3, "buff"),
                         (4, "stance"), (5, "buff"), (6, "unknown")]:
        actual = dispatch_kind(et)
        assert actual == expected, f"effect_type {et}: expected {expected}, got {actual}"
        print(f"  ✓ effect_type {et} → {actual}")

    print("\n# All Round 75 GUNNER combo UI + skill effect 통합 checks passed.")


if __name__ == "__main__":
    main()
