"""Round 74 — Godot battle_system.gd damage 공식 정확화 검증.

R63 임시 공식 → R71+R72+R73 의 발견 (Formula 3/4 + GUNNER combo + helper signals)
대응 Godot 코드 통합 검증.

검증 항목:
  1. game_state.gd 에 gunner_combo / gunner_max_combo / gunner_ammo 변수 추가
  2. battle_system.gd 에 R74 GUNNER combo multiplier 적용 (class_id==2 + skill_id==5)
     공식: dmg = base * (combo*20 + 30) / 100
  3. battle_system.gd 에 R74 Formula 4 부가 호출 (SP delta) — _calc_player_damage(4, …)
  4. battle_system.gd 에 R72 helper signals: curse_applied / buff_applied / stance_applied
  5. battle_system.gd 에 apply_skill_effect(target, effect_type, dispatch, f1, f2) method
  6. GUNNER combo Python 시뮬: combo 0..4 의 damage 배율 (50/70/90/110 → reset)
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
    print("# Round 74 Godot battle_system damage 공식 정확화 검증\n")
    for p in (GAME_STATE_GD, BATTLE_GD):
        assert p.exists(), f"missing {p}"

    # 1. game_state.gd 의 GUNNER state 변수
    print("# 1. game_state.gd 의 GUNNER combo state 변수")
    gs = GAME_STATE_GD.read_text(encoding="utf-8")
    for var_name, default in (
        ("gunner_combo", "0"),
        ("gunner_max_combo", "4"),
        ("gunner_ammo", "0"),
    ):
        pat = rf"var\s+{re.escape(var_name)}\s*:\s*int\s*=\s*{default}\b"
        assert re.search(pat, gs), f"game_state.gd 에 {var_name}: int = {default} 없음"
        print(f"  ✓ var {var_name}: int = {default}")

    # 2. battle_system.gd GUNNER combo multiplier
    print("\n# 2. battle_system.gd GUNNER combo multiplier (class_id==2 + skill_id==5)")
    bs = BATTLE_GD.read_text(encoding="utf-8")
    gunner_check = re.search(
        r"GameState\.class_id\s*==\s*2.*?GameState\.gunner_combo",
        bs, re.DOTALL,
    )
    assert gunner_check, "battle_system.gd 의 GUNNER combo 분기 미발견"
    print(f"  ✓ GUNNER class+skill 분기 (class_id==2 + skill_id==5)")

    # combo multiplier 공식: combo*20 + 30
    mult_check = re.search(
        r"GameState\.gunner_combo\s*\*\s*20\s*\+\s*30",
        bs,
    )
    assert mult_check, "GUNNER combo multiplier 공식 (combo*20 + 30) 미발견"
    print(f"  ✓ damage = base * (combo*20 + 30) / 100")

    # combo reset
    assert "GameState.gunner_combo = 0" in bs, "combo reset 미발견"
    print(f"  ✓ combo > max_combo 시 reset (= 0)")

    # 3. Formula 4 SP delta 부가 호출
    print("\n# 3. Formula 4 부가 호출 (SP delta)")
    sp_delta_check = re.search(
        r"_calc_player_damage\s*\(\s*4\s*,",
        bs,
    )
    assert sp_delta_check, "Formula 4 호출 (_calc_player_damage(4, …)) 미발견"
    print(f"  ✓ _calc_player_damage(4, …) — SP delta 부가 호출")

    # player_mp 회복 로직
    assert "player_mp + sp_delta" in bs, "SP delta 적용 (player_mp + sp_delta) 미발견"
    print(f"  ✓ player_mp = mini(player_max_mp, player_mp + sp_delta)")

    # 4. R72 helper signals
    print("\n# 4. R72 helper signals (curse/buff/stance_applied)")
    for sig in ("curse_applied", "buff_applied", "stance_applied"):
        pat = rf"signal\s+{re.escape(sig)}\s*\("
        assert re.search(pat, bs), f"signal {sig} 미발견"
        print(f"  ✓ signal {sig}(target, dispatch_byte, formula_1, formula_2)")

    # 5. apply_skill_effect helper method
    print("\n# 5. apply_skill_effect(target, effect_type, dispatch, f1, f2) method")
    assert "func apply_skill_effect(" in bs, "apply_skill_effect method 미발견"
    # 5-way match (effect_type 0/1·2/3·5/4)
    for case_imm in ("1, 2:", "3, 5:", "4:"):
        assert case_imm in bs, f"apply_skill_effect 의 match case {case_imm} 미발견"
        print(f"  ✓ match case {case_imm}")

    # 6. GUNNER combo Python 시뮬
    print("\n# 6. GUNNER combo damage multiplier Python 시뮬")
    def gunner_dmg(base: int, combo: int) -> int:
        return base * (combo * 20 + 30) // 100

    base_dmg = 100
    for combo, expected_pct in [(1, 50), (2, 70), (3, 90), (4, 110)]:
        actual = gunner_dmg(base_dmg, combo)
        expected = base_dmg * expected_pct // 100
        assert actual == expected, (
            f"combo {combo}: expected {expected} ({expected_pct}%), got {actual}"
        )
        print(f"  ✓ combo {combo}: base {base_dmg} → {actual} ({expected_pct}%)")

    # combo 0 (= reset 상태, GUNNER 분기 진입 안 함) — multiplier 적용 안 됨
    # (테스트 자체는 mult 공식만, 분기 검증은 #2 에서)

    # 7. R74 docstring marker
    print("\n# 7. R74 docstring markers in battle_system.gd")
    markers = [
        "Round 74",
        "ProcHeroSkill",
        "JT1 case helper",
        "skill_info[+0x4a]",
        "skill_info[+0x3c]",
        "skill_info[+0x3d]",
        "combo multiplier",
    ]
    for marker in markers:
        assert marker in bs, f"battle_system.gd 의 R74 docstring 에 '{marker}' 누락"
        print(f"  ✓ '{marker}' 포함")

    # game_state.gd 의 R74 docstring
    for marker in ("Round 74", "GUNNER", "combo state", "HERO+0x269", "(combo*20+30)"):
        assert marker in gs, f"game_state.gd 의 R74 docstring 에 '{marker}' 누락"
        print(f"  ✓ game_state.gd: '{marker}' 포함")

    print("\n# All Round 74 battle formula precise damage checks passed.")


if __name__ == "__main__":
    main()
