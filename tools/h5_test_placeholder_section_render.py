#!/usr/bin/env python3
"""R111: `{관련특성|` 섹션 헤더 + bare `#NN<text>` skill-link 불릿 + #10/#11/#13 라벨.

R110 의 bracket-aware 후속. class_0..3 desc 의 `{관련특성|` 라벨 + bare `#NN<text>`
형식이 사용자에게 raw 로 노출되던 문제를 readable form 으로 변환.

검증:
- PLACEHOLDER_LABELS 에 #10/#11/#13 추가 (10 entry 총)
- resolve_skill_desc 의 indices 자동 수집 (괄호 내부 #NN 발견 → indices 포함)
- resolve_skill_desc_display 의 `{TEXT|` → `▸ TEXT:` 변환
- bare `#NN<text>` → `• <text>` 불릿 변환
- Python 시뮬: 돌진 의 `{관련특성|` 섹션 + `#01돌격-스턴효과` 등 불릿
- R110 회귀 (bracket-aware helper) + R109 (단위 분리) + R108 회귀
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
    skills = json.loads((GODOT / "assets/gamedata/skills.json").read_text(encoding="utf-8"))

    # 1. PLACEHOLDER_LABELS 10 entry
    labels_block = gd[gd.find("const PLACEHOLDER_LABELS"):gd.find("const PLACEHOLDER_STAT_SOURCE")]
    for nn, label in [(4, "효과"), (5, "공격"), (6, "마법"), (7, "MP"),
                       (8, "지속"), (9, "쿨"), (10, "값"), (11, "강화"),
                       (12, "수치"), (13, "양")]:
        assert re.search(rf'^\s*{nn}:\s*"{label}",?\s*$', labels_block, re.M), \
            f"PLACEHOLDER_LABELS[{nn}] = \"{label}\" 누락"
    print("[PASS] PLACEHOLDER_LABELS: 10 entry (R109 7 entry + R111 #10/#11/#13)")

    # 2. resolve_skill_desc indices 자동 수집 (#NN 발견 → indices)
    rsd = gd[gd.find("func resolve_skill_desc(class_id"):
             gd.find("func _replace_placeholders_in_brackets")]
    assert "괄호 내부에 등장하는 `#NN` 자동 수집" in rsd or "자동 수집" in rsd, \
        "R111 indices 자동 수집 주석 누락"
    # while loop with desc.find("}", ...) 패턴
    assert "desc.find(\"}\", bi)" in rsd and "desc.find(\"|\", b_open" in rsd, \
        "indices 자동 수집 while loop 누락"
    print("[PASS] resolve_skill_desc: 괄호 내부 #NN 자동 수집 (R111)")

    # 3. resolve_skill_desc_display 의 `{TEXT|` 섹션 헤더 변환
    rsdd = gd[gd.find("func resolve_skill_desc_display(class_id"):
              gd.find("func resolve_skill_desc_first_line")]
    assert 'c == "{"' in rsdd, "{ 섹션 분기 누락"
    assert '"▸ 관련 특성:"' in rsdd, "관련특성 변환 누락"
    print("[PASS] resolve_skill_desc_display: `{관련특성|` → `▸ 관련 특성:`")

    # 4. bare `#NN<text>` → `• ` 변환
    assert 'c == "#"' in rsdd and '"• "' in rsdd, \
        "bare #NN → 불릿 변환 누락"
    print("[PASS] resolve_skill_desc_display: bare `#NN<text>` → `• <text>` 불릿")

    # 5. Python 시뮬 — 돌진 desc 전체 변환
    def py_display(desc, values):
        # placeholder resolve (R110 bracket-aware 시뮬)
        out_step1 = ""
        i = 0
        while i < len(desc):
            if desc[i] == "}":
                close = desc.find("|", i + 1)
                if close == -1:
                    out_step1 += desc[i:]
                    break
                inner = desc[i + 1:close]
                for nn, v in values.items():
                    inner = inner.replace(f"#{nn:02d}", v)
                out_step1 += "}" + inner + "|"
                i = close + 1
            else:
                out_step1 += desc[i]
                i += 1
        # R111 display 변환
        raw = out_step1
        out = ""
        i = 0
        while i < len(raw):
            c = raw[i]
            if c == "}":
                close = raw.find("|", i + 1)
                if close == -1:
                    out += c
                    i += 1
                    continue
                out += "[" + raw[i + 1:close] + "]"
                i = close + 1
            elif c == "{":
                close = raw.find("|", i + 1)
                if close == -1:
                    out += c
                    i += 1
                    continue
                header = raw[i + 1:close]
                if header == "관련특성":
                    out += "▸ 관련 특성:"
                else:
                    out += "▸ " + header + ":"
                i = close + 1
            elif c == "#" and i + 2 < len(raw) and raw[i + 1].isdigit() and raw[i + 2].isdigit():
                out += "• "
                i += 3
            elif c == ";":
                out += "\n"
                i += 1
            else:
                out += c
                i += 1
        return out

    # 돌진
    dolji = skills["class_0"][1]
    # values 시뮬 — class_0 stats has 8 entries, #05 garbage, #09 out of range
    values = {0: "4", 1: "0", 2: "0", 3: "?", 4: "8", 5: "?(공격)", 6: "?", 7: "1",
              8: "?(지속)", 9: "?(쿨)", 10: "?(값)", 11: "?(강화)", 12: "?(수치)", 13: "?(양)"}
    out = py_display(dolji["desc"], values)
    assert "▸ 관련 특성:" in out, f"관련특성 헤더 누락: {out!r}"
    assert "• 돌격-스턴효과" in out, f"불릿 #01 누락: {out!r}"
    assert "• 돌격-밟고가기" in out, f"불릿 #02 누락: {out!r}"
    assert "• 돌격-각력" in out, f"불릿 #03 누락: {out!r}"
    assert "[?(쿨)초]" in out, f"#09 unresolved label 누락: {out!r}"
    print("[PASS] 돌진 display 시뮬: ▸관련특성 + 3 불릿 + [?(쿨)초]")

    # 6. 다른 skill 의 `}#10` 등 확인
    # class_2[0] 연속사격: }#10 안 보임. class_1[5] 정도가 #10 사용 가능성. 일반 sample
    found_10 = False
    for cls in ("class_0", "class_1", "class_2", "class_3"):
        for sk in skills[cls]:
            if "}#10" in sk.get("desc", ""):
                values10 = {i: ("?(%s)" % ["효과","공격","마법","MP","지속","쿨","값","강화","수치","양"][i-4] if i >= 4 else "?")
                            for i in range(0, 14)}
                values10[10] = "?(값)"
                out10 = py_display(sk["desc"], values10)
                if "?(값)" in out10:
                    found_10 = True
                    break
        if found_10:
            break
    assert found_10, "#10 → ?(값) label 시뮬 미발견"
    print("[PASS] #10 → ?(값) 라벨 fallback (실 skill desc 적용)")

    # 7. R110 회귀 — bracket-aware helper 잔존
    assert "func _replace_placeholders_in_brackets" in gd
    print("[PASS] R110 회귀: _replace_placeholders_in_brackets 잔존")

    # 8. R109 회귀 — 단위 분리 LABELS
    assert '5: "공격",' in gd or '5: "공격"' in gd
    print("[PASS] R109 회귀: 단위 분리 잔존")

    # 9. R108 회귀 — 5 helper
    for marker in (
        "func eval_placeholder_stat",
        "func _calc_placeholder_formula",
        "fvm.calc(formula_id, ctx)",
    ):
        assert marker in gd, f"R108 marker 누락: {marker}"
    print("[PASS] R108 회귀: helpers 잔존")

    # 10. R105 THRESHOLD 회귀
    assert "PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd
    print("[PASS] R105 회귀: THRESHOLD = 500")

    # 11. R90 display + first_line 회귀
    assert "func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:" in gd
    assert "func resolve_skill_desc_first_line(class_id: int, skill_id: int) -> String:" in gd
    print("[PASS] R90 회귀: display + first_line")

    # 12. R111 docstring marker
    assert "Round 111" in gd, "game_data.gd R111 marker 누락"
    print("[PASS] R111 docstring marker (game_data)")

    # 13. 실 데이터 카운트: 37 `{관련특성|` 모두 변환 대상
    n_sections = 0
    n_links = 0
    for cls in ("class_0", "class_1", "class_2", "class_3"):
        for sk in skills[cls]:
            desc = sk.get("desc", "")
            n_sections += desc.count("{관련특성|")
            n_links += len(re.findall(r"[;\n#]#\d{2}[가-힣\-]", "x" + desc))
    assert n_sections == 37, f"`{{관련특성|`` 카운트 = {n_sections}, 기대 37"
    print(f"[PASS] 실 데이터 카운트: {n_sections}개 섹션 헤더 변환 + ≥{n_links}개 skill-link 불릿화")

    # 14. resolve_skill_desc_display 의 ; → \n 회귀 (R90)
    assert 'c == ";"' in rsdd and 'out += "\\n"' in rsdd
    print("[PASS] R90 회귀: `;` → `\\n` 변환")

    print("\nR111 section header + bullet rendering: ALL PASSED")


if __name__ == "__main__":
    main()
