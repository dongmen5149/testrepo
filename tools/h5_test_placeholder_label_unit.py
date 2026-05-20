#!/usr/bin/env python3
"""R109: PLACEHOLDER_LABELS 단위 분리 + #12 primary_u16 매핑 제거.

R106 의 `"공격%"` / `"지속초"` 처럼 label 이 unit 을 포함 → desc 본문의 unit 과
중복 노출 (`[?(공격%)%]`, `[?(지속초)초]`). R109: label 에서 unit 제거 — desc 의
`}#NN<unit>|` 가 unit 을 보유.

또한 #12 의 `primary_u16` 매핑은 spirit #6 폭발 `}#12초|` 가 damage% (300) 으로
잘못 노출되던 케이스 — R109 에서 제거 → stats_u16[12] fallback → 대부분 garbage
가드로 `[?(수치)초]` 안전 노출.

검증:
- PLACEHOLDER_LABELS 7 entry 단위 제거 (효과/공격/마법/MP/지속/쿨/수치)
- PLACEHOLDER_STAT_SOURCE 에서 12 제거 (6 entry: 4/5/6/7/8/9)
- resolve_skill_desc Python 시뮬: 폭발 `}#12초|` → `[?(수치)초]` (이전 `[300초]`)
- spirit #0 #05 → 400% 회귀 (R108 보존)
- help_panel R109 label 갱신
- R105-R108 회귀
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"

THRESHOLD = 500


def read(p):
    return (GODOT / p).read_text(encoding="utf-8")


def main():
    gd = read("scripts/core/game_data.gd")
    spirit_path = GODOT / "assets/gamedata/c_csv_skill_05.json"
    spirits = json.loads(spirit_path.read_text(encoding="utf-8"))["records"]

    # 1. PLACEHOLDER_LABELS 단위 제거
    labels_block = gd[gd.find("const PLACEHOLDER_LABELS"):gd.find("const PLACEHOLDER_STAT_SOURCE")]
    for nn, label in [(4, "효과"), (5, "공격"), (6, "마법"),
                      (7, "MP"), (8, "지속"), (9, "쿨"), (12, "수치")]:
        assert re.search(rf'^\s*{nn}:\s*"{label}",?\s*$', labels_block, re.M), \
            f"PLACEHOLDER_LABELS[{nn}] = \"{label}\" 누락"
    print("[PASS] PLACEHOLDER_LABELS: 7 entry 단위 제거 (효과/공격/마법/MP/지속/쿨/수치)")

    # 2. 이전 R106 label (unit 포함) 잔존 0
    for old_label in ['"효과%"', '"공격%"', '"마법%"', '"지속초"', '"쿨초"', '"배수"']:
        assert old_label not in labels_block, \
            f"R106 unit-포함 label `{old_label}` 잔존 — R109 분리 미적용"
    print("[PASS] R106 unit-포함 label (효과%/공격%/지속초/쿨초/배수) 잔존 0")

    # 3. PLACEHOLDER_STAT_SOURCE 6 entry (12 제거)
    src_block = gd[gd.find("const PLACEHOLDER_STAT_SOURCE"):gd.find("func _ensure_skills_cache_loaded")]
    for nn in (4, 5, 6, 7, 8, 9):
        assert re.search(rf"^\s*{nn}:\s*\{{", src_block, re.M), \
            f"PLACEHOLDER_STAT_SOURCE NN {nn} 누락"
    assert not re.search(r"^\s*12:\s*\{", src_block, re.M), \
        "PLACEHOLDER_STAT_SOURCE 에 NN 12 잔존 — R109 제거 미적용"
    print("[PASS] PLACEHOLDER_STAT_SOURCE: 6 entry (4/5/6/7/8/9, 12 제거)")

    # 4. Python 시뮬 — 폭발 `}#12초|` 동작
    sp6 = spirits[6]
    assert sp6["name"] == "폭발"
    b6 = bytes.fromhex(sp6["extra_hex"])
    primary6 = b6[0x22] | (b6[0x23] << 8)
    assert primary6 == 300, f"폭발 primary_u16 기대 300, got {primary6}"
    # R108 시점: #12 → primary_u16 → 300 (오해석)
    # R109 시점: #12 → stats_u16[12] (= bytes[0x19]<<8 | bytes[0x18] = 0x7f39 = 32569) → > 500 → ?(수치)
    stats12 = (b6[0x19] << 8) | b6[0x18]
    assert stats12 > THRESHOLD, f"폭발 stats_u16[12]={stats12} ≤ THRESHOLD — garbage 가드 검증 실패"
    print(f"[PASS] 폭발 #12 fallback: stats_u16[12]={stats12} > {THRESHOLD} → ?(수치) 안전")

    # 5. spirit #0 #05 회귀 (R108)
    sp0 = spirits[0]
    b0 = bytes.fromhex(sp0["extra_hex"])
    primary0 = b0[0x22] | (b0[0x23] << 8)
    assert primary0 == 400
    print("[PASS] R108 회귀: 암흑탄 primary_u16=400 (#05 → 400%) 보존")

    # 6. resolve_skill_desc 분기 (PLACEHOLDER_STAT_SOURCE.has(i)) 잔존
    rsd = gd[gd.find("func resolve_skill_desc(class_id"):gd.find("func resolve_skill_desc_display")]
    assert "PLACEHOLDER_STAT_SOURCE.has(i)" in rsd, "R108 분기 누락"
    print("[PASS] resolve_skill_desc 분기 보존")

    # 7. _format_placeholder_display: `?(%s)` form (R109 단위 본문에서)
    fmt_block = gd[gd.find("func _format_placeholder_display"):
                   gd.find("func eval_placeholder_stat")]
    assert '"?(%s)" % PLACEHOLDER_LABELS[nn]' in fmt_block, \
        "?(label) form 누락 — R109 label 적용 경로 차단"
    print("[PASS] _format_placeholder_display: `?(label)` form 유지")

    # 8. help_panel R109 label 갱신
    hp = read("scripts/ui/help_panel.gd")
    # R109 label 키 (unit 없는 형태) 멘션
    for label in ["효과", "공격", "마법", "MP", "지속", "쿨", "수치"]:
        assert label in hp, f"help_panel R109 label `{label}` 누락"
    # `?(공격)%` 형식 안내 (R109 단위 분리 표기 예)
    assert "공격)%" in hp or "(공격)%" in hp, "help_panel: R109 단위 분리 표기 예 누락"
    print("[PASS] help_panel: R109 7 label + 단위 분리 표기 예")

    # 9. R109 단위-중복 시나리오 차단 (label + desc unit) — 시뮬
    LABELS = {4: "효과", 5: "공격", 6: "마법", 7: "MP", 8: "지속", 9: "쿨", 12: "수치"}

    def sim(nn, val, desc_unit):
        if val < 0 or val > THRESHOLD:
            label = LABELS.get(nn, "?")
            disp = f"?({label})" if nn in LABELS else "?"
        else:
            disp = str(val)
        # `}#NN<unit>|` → `}<disp><unit>|` → `[<disp><unit>]`
        return f"[{disp}{desc_unit}]"

    # 정상 케이스
    assert sim(5, 400, "%") == "[400%]"
    # 미해결 / 가드: label 만 노출, unit 본문에서
    assert sim(5, -1, "%") == "[?(공격)%]", f"R109 form 불일치: {sim(5, -1, '%')}"
    assert sim(8, -1, "초") == "[?(지속)초]", f"R109 form 불일치: {sim(8, -1, '초')}"
    assert sim(12, 32569, "초") == "[?(수치)초]", f"폭발 R109 시뮬 불일치: {sim(12, 32569, '초')}"
    # R106 시점 form (단위 중복) 미발생 확인
    assert sim(5, -1, "%") != "[?(공격%)%]"
    assert sim(8, -1, "초") != "[?(지속초)초]"
    print("[PASS] Python 시뮬: R109 단위 분리 형식 — `[?(공격)%]` / `[?(지속)초]` / `[?(수치)초]`")

    # 10. R105 THRESHOLD 회귀
    assert "PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd
    print("[PASS] R105 회귀: UNREASONABLE_THRESHOLD = 500")

    # 11. R107 회귀 — help_panel placeholder 섹션 잔존
    assert "스킬 설명 placeholder" in hp
    print("[PASS] R107 회귀: help_panel placeholder 섹션 유지")

    # 12. R108 helpers 잔존 회귀
    for marker in (
        "func eval_placeholder_stat",
        "func _calc_placeholder_formula",
        "func _placeholder_player_ctx",
        "func _placeholder_formula_ctx",
        "fvm.calc(formula_id, ctx)",
    ):
        assert marker in gd, f"R108 helper 누락: {marker}"
    print("[PASS] R108 회귀: 5 helper 유지")

    # 13. R109 docstring marker
    assert "Round 109" in gd or "R109" in gd, "game_data.gd 에 R109 marker 누락"
    assert "Round 109" in hp or "R109" in hp, "help_panel.gd 에 R109 marker 누락"
    print("[PASS] R109 docstring marker (game_data + help_panel)")

    # 14. RE 문서 §6 R109 섹션
    re_doc = (ROOT / "docs/h5/RE/skill_desc_placeholder.md").read_text(encoding="utf-8")
    assert "R109" in re_doc and "단위 분리" in re_doc, "RE 문서 §6 R109 단위 분리 섹션 누락"
    assert "spirit 16 record 실 값" in re_doc, "RE 문서 spirit 16 표 누락"
    print("[PASS] RE 문서 §6 R109 단위 분리 + spirit 16 표")

    print("\nR109 placeholder label/unit 분리: ALL PASSED")


if __name__ == "__main__":
    main()
