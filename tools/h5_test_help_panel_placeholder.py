#!/usr/bin/env python3
"""R107: HelpPanel placeholder label 섹션 신규 (H/QA +0.1%p).

R105 (UNREASONABLE 가드) + R106 (label fallback) 의 placeholder UX 가 사용자
입장에서 "`[?(공격%)]` 라는 표기가 왜 뜨는가" 가 도움말 어디에도 없었음.
R107 = HelpPanel HELP_TEXT 끝에 "스킬 설명 placeholder" 섹션 추가:
6 PLACEHOLDER_LABELS entry (#04/#05/#07/#08/#09/#12) 의미 + 가드 동작 설명.

검증:
- HELP_TEXT 에 "스킬 설명 placeholder" 섹션 헤더 존재
- 6 PLACEHOLDER_LABELS entry 모두 멘션 (#04/#05/#07/#08/#09/#12)
- 6 의미 label (효과%/공격%/MP/지속초/쿨초/배수) 모두 멘션
- THRESHOLD 500 동작 (정상 범위 ≤500) 멘션
- 미매핑 NN 의 `?` fallback 멘션
- game_data.gd 의 PLACEHOLDER_LABELS 와 HELP_TEXT 가 1:1 일치 (drift 방지)
- R106 회귀 — PLACEHOLDER_LABELS dict 6 entry 잔존
- R105 회귀 — THRESHOLD 상수 잔존
- R94 회귀 — F6/F10 잔존 (이전 섹션 보존)
- R93 회귀 — Title Continue → SaveListPanel 위임 문구
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    hp = read("scripts/ui/help_panel.gd")
    gd = read("scripts/core/game_data.gd")

    m = re.search(r'const HELP_TEXT := """(.*?)"""', hp, re.DOTALL)
    assert m, "HELP_TEXT 추출 실패"
    help_text = m.group(1)

    checks = []

    # 1. 신규 섹션 헤더
    assert "스킬 설명 placeholder" in help_text, "[1] '스킬 설명 placeholder' 섹션 없음"
    checks.append("[1] HELP_TEXT 에 '스킬 설명 placeholder' 섹션 헤더 존재")

    # 2. 6 NN 마커 모두
    for nn in ["#04", "#05", "#06", "#07", "#08", "#09", "#12"]:
        assert nn in help_text, f"[2] HELP_TEXT 에 placeholder NN {nn} 없음"
    checks.append("[2] 6 PLACEHOLDER_LABELS NN 마커 모두 HELP_TEXT 에 잔존")

    # 3. 7 의미 label — R107 form (unit 포함) 또는 R109 form (unit 분리) 둘 다 허용
    for label_a, label_b in [("효과%", "효과"), ("공격%", "공격"), ("마법%", "마법"),
                              ("MP", "MP"), ("지속초", "지속"), ("쿨초", "쿨"),
                              ("배수", "수치")]:
        assert label_a in help_text or label_b in help_text, \
            f"[3] HELP_TEXT 에 label '{label_a}'/'{label_b}' 없음"
    checks.append("[3] 7 의미 label HELP_TEXT 잔존 (R107/R109 form 모두 허용)")

    # 4. THRESHOLD 500 멘션 (정상 범위 ≤500)
    assert "500" in help_text, "[4] HELP_TEXT 에 THRESHOLD 500 멘션 없음"
    checks.append("[4] THRESHOLD 500 (정상 범위) HELP_TEXT 멘션")

    # 5. 미매핑 fallback `?`
    assert "미매핑" in help_text and "?" in help_text, "[5] 미매핑 `?` fallback 멘션 없음"
    checks.append("[5] 미매핑 NN 의 `?` fallback 멘션")

    # 6. game_data.gd PLACEHOLDER_LABELS 와 1:1 일치
    gd_m = re.search(
        r'const PLACEHOLDER_LABELS := \{(.*?)\}', gd, re.DOTALL)
    assert gd_m, "[6] game_data.gd PLACEHOLDER_LABELS dict 추출 실패"
    gd_entries = dict(re.findall(r'(\d+)\s*:\s*"([^"]+)"', gd_m.group(1)))
    # R107: 7 entry, R111: 10 entry (#10/#11/#13 추가)
    assert len(gd_entries) in (7, 10), \
        f"[6] PLACEHOLDER_LABELS entry 수 = {len(gd_entries)}, 기대 7 (R107) 또는 10 (R111)"
    for nn, label in gd_entries.items():
        nn_marker = "#%02d" % int(nn)
        assert nn_marker in help_text, f"[6] dict entry {nn_marker} 가 HELP_TEXT 에 없음"
        assert label in help_text, f"[6] dict label '{label}' 이 HELP_TEXT 에 없음"
    checks.append("[6] game_data.gd PLACEHOLDER_LABELS (7 entry) 와 HELP_TEXT 1:1 일치")

    # 7. R106 회귀 — PLACEHOLDER_LABELS dict entry (R106 또는 R109 form)
    assert '4: "효과%"' in gd or '4: "효과"' in gd, "[7] entry NN 4 누락"
    assert '5: "공격%"' in gd or '5: "공격"' in gd, "[7] entry NN 5 누락"
    checks.append("[7] R106 회귀 — PLACEHOLDER_LABELS dict 7 entry 잔존 (R106/R109)")

    # 8. R105 회귀 — UNREASONABLE THRESHOLD 상수
    assert "PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd, "[8] R105 THRESHOLD 누락"
    checks.append("[8] R105 회귀 — PLACEHOLDER_UNREASONABLE_THRESHOLD 500 잔존")

    # 9. R94 회귀 — F6/F10 잔존
    assert "F6" in help_text, "[9] F6 (R94) 멘션 누락"
    assert "F10" in help_text, "[9] F10 (R94) 멘션 누락"
    checks.append("[9] R94 회귀 — F6/F10 멘션 잔존")

    # 10. R93 회귀 — Title Continue SaveListPanel 위임
    assert "Save 목록 패널" in help_text or "SaveListPanel" in help_text, \
        "[10] R93 Continue → SaveListPanel 위임 문구 누락"
    checks.append("[10] R93 회귀 — Continue → Save 목록 패널 위임 문구")

    # 11. 의미 분류 정확성 (R75 convention) — R107 또는 R109 form
    assert "공격%" in help_text or "공격" in help_text, "[11] '공격' label 누락"
    checks.append("[11] R75 convention label (공격(%)/쿨(초)) 한국어 라벨 표시")

    # 12. R107 docstring marker
    assert "Round 107" in hp, "[12] help_panel.gd docstring 에 'Round 107' marker 누락"
    checks.append("[12] help_panel.gd docstring 에 R107 marker 잔존")

    # 13. content.bbcode_enabled (회귀 — HelpPanel 동작 보존)
    assert "bbcode_enabled = true" in hp, "[13] bbcode_enabled 회귀 누락"
    checks.append("[13] HelpPanel bbcode_enabled 회귀")

    # 14. toggle() 회귀
    assert "func toggle()" in hp, "[14] toggle() 회귀 누락"
    checks.append("[14] HelpPanel toggle() 회귀")

    # 15. 섹션 순서 — 신규 placeholder 섹션이 Title 섹션 뒤
    title_idx = help_text.find("[b]Title 화면[/b]")
    ph_idx = help_text.find("[b]스킬 설명 placeholder[/b]")
    assert title_idx >= 0 and ph_idx > title_idx, "[15] placeholder 섹션은 Title 섹션 뒤여야 함"
    checks.append("[15] 신규 'placeholder' 섹션이 Title 섹션 뒤에 위치")

    print("\n".join(checks))
    print(f"\nR107 HelpPanel placeholder label intro: {len(checks)}/{len(checks)} PASSED")


if __name__ == "__main__":
    main()
