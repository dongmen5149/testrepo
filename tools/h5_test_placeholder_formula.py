#!/usr/bin/env python3
"""R108: Placeholder Formula::calc + explicit field 통합 (F +1.0%p).

R105-R107 의 `?`(label) fallback 후속. stats_u16[NN] 대신:
  1) FormulaVM.calc(formula_id_1/2) — JSON 있을 때
  2) spirit explicit field (primary_u16, mp_cost, …)
  3) reasonable stats_u16[NN]
  4) ?(label)

검증:
- PLACEHOLDER_STAT_SOURCE 7 NN
- eval_placeholder_stat / _calc_placeholder_formula / _placeholder_player_ctx
- resolve_skill_desc 가 PLACEHOLDER_STAT_SOURCE 분기
- Python 시뮬: spirit #0 #05 → primary 400
- R105-R107 회귀
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding="utf-8")


def main():
    gd = read("scripts/core/game_data.gd")
    spirit_path = GODOT / "assets/gamedata/c_csv_skill_05.json"
    assert spirit_path.exists(), "c_csv_skill_05.json 없음"
    spirits = json.loads(spirit_path.read_text(encoding="utf-8"))["records"]

    # 1. R108 constants (R109 에서 #12 제거 → 6 NN 도 허용)
    assert "const PLACEHOLDER_STAT_SOURCE" in gd, "PLACEHOLDER_STAT_SOURCE 누락"
    src_block = gd[gd.find("const PLACEHOLDER_STAT_SOURCE"):gd.find("func _ensure_skills_cache_loaded")]
    for nn in (4, 5, 6, 7, 8, 9):
        assert re.search(rf"^\s*{nn}:\s*\{{", src_block, re.M), \
            f"PLACEHOLDER_STAT_SOURCE NN {nn} 누락"
    print("[PASS] PLACEHOLDER_STAT_SOURCE: 6+ NN (4/5/6/7/8/9, #12 는 R109 제거 허용)")

    # R109: PLACEHOLDER_LABELS 의 #06 label 은 "마법%" (R108) 또는 "마법" (R109) 둘 다 허용
    assert ("6: \"마법%\"" in gd) or ("6: \"마법\"" in gd), \
        "PLACEHOLDER_LABELS #06 마법(%) 누락"
    print("[PASS] PLACEHOLDER_LABELS: #06 마법(%) 존재 (R108/R109 form 모두 허용)")

    # 2. eval + formula helpers
    for marker in (
        "func eval_placeholder_stat",
        "func _calc_placeholder_formula",
        "func _placeholder_player_ctx",
        "func _placeholder_formula_ctx",
        "func _resolve_placeholder_stat",
        "PLACEHOLDER_STAT_SOURCE.has(i)",
    ):
        assert marker in gd, f"R108 marker 누락: {marker}"
    print("[PASS] R108 helpers: eval_placeholder_stat + Formula ctx + 분기")

    # 3. FormulaVM path
    assert "_formula_vm()" in gd and "fvm.calc(formula_id, ctx)" in gd
    print("[PASS] FormulaVM.calc 연동")

    # 4. Python 시뮬 — spirit #0 primary_u16 → #05
    b = bytes.fromhex(spirits[0]["extra_hex"])
    primary = b[0x22] | (b[0x23] << 8)
    assert primary == 400, f"spirit #0 primary_u16 기대 400, got {primary}"
    THRESHOLD = 500

    def sim_eval(nn, primary_u16, stats5):
        if nn == 5:
            if 0 <= primary_u16 <= THRESHOLD:
                return primary_u16
        return -1

    assert sim_eval(5, primary, 7728) == 400
    assert sim_eval(5, primary, 7728) != 7728
    print("[PASS] Python 시뮬: spirit #0 #05 → 400 (primary_u16, not stats[5]=7728)")

    # 5. spirit #2 #08 — secondary=0 → unresolved
    b2 = bytes.fromhex(spirits[2]["extra_hex"])
    sec = b2[0x24] | (b2[0x25] << 8)
    assert sec == 0
    print("[PASS] spirit #2 secondary_u16=0 (#08 duration 미해결 가정)")

    # 6. R107 docstring marker (optional in game_data — check help)
    hp = read("scripts/ui/help_panel.gd")
    assert "R108" in hp or "Formula::calc" in hp
    print("[PASS] help_panel: R108 Formula 언급")

    # 7. R106 회귀
    assert "const PLACEHOLDER_LABELS" in gd
    assert "PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd
    rsd = gd[gd.find("func resolve_skill_desc"):gd.find("func resolve_skill_desc_display")]
    assert "_resolve_placeholder_stat" in rsd
    print("[PASS] R105-R106 회귀: THRESHOLD + label fallback 경로 유지")

    # 8. R107/R109 help 7 labels — R108 form (unit 포함) 또는 R109 form (unit 분리) 허용
    # R108: 효과%/공격%/마법%/MP/지속초/쿨초/배수
    # R109: 효과/공격/마법/MP/지속/쿨/수치
    label_pairs = [
        ("효과%", "효과"), ("공격%", "공격"), ("마법%", "마법"),
        ("MP", "MP"), ("지속초", "지속"), ("쿨초", "쿨"), ("배수", "수치"),
    ]
    for r108_form, r109_form in label_pairs:
        assert (r108_form in hp) or (r109_form in hp), \
            f"help_panel label {r108_form}/{r109_form} 누락"
    print("[PASS] help_panel: 7 label 멘션 (R108/R109 form 허용)")

    print("\nR108 placeholder Formula 통합: ALL PASSED")


if __name__ == "__main__":
    main()
