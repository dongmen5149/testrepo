#!/usr/bin/env python3
"""R112: skill desc decoder fix + display quirk 흡수 전수 검증.

R111 까지의 placeholder/render 시스템이 188 skill 의 ~99% 를 클린하게 렌더링.
R112 fix 4종:
1. `decode_h5_skill.py`: 한글 직전 `}` 보존 (passive desc `}<관련스킬>|` form, ~58건)
2. resolve_skill_desc_display: `}<text>}<num>|` 중첩 평탄화 (봉쇄/섬광탄 2건)
3. resolve_skill_desc_display: `{` 를 alt close marker 로 수용 (쐐기탄 bit-flip 1건)
4. resolve_skill_desc_display: 불릿 변환을 line-start 로 제한 (포격 false-positive 차단)

검증:
- decode_h5_skill.py 의 `}` backtrack 로직 잔존
- skills.json 의 sample passive 가 `}<active>|` form 으로 시작
- resolve_skill_desc_display 의 close marker 분기 (`|` 또는 `{`)
- 중첩 `}` 평탄화 로직 (replace inner)
- 불릿 line-start 가드 (out.is_empty() / out.ends_with("\\n"))
- Python 시뮬: 봉쇄/섬광탄/쐐기탄 quirk 모두 cleanly 렌더링
- R105-R111 회귀
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
    decoder = (ROOT / "tools/converter/decode_h5_skill.py").read_text(encoding="utf-8")
    skills = json.loads((GODOT / "assets/gamedata/skills.json").read_text(encoding="utf-8"))

    # 1. 디코더 backtrack 로직
    assert "b[desc_start - 1] == 0x7d" in decoder, "decoder 의 `}` backtrack 누락"
    assert "desc_start -= 1" in decoder, "decoder 의 desc_start 후퇴 누락"
    print("[PASS] decode_h5_skill.py: 한글 직전 `}` 보존 backtrack 로직")

    # 2. skills.json 의 passive 가 `}<active>|` form 으로 시작
    # class_0[11] 각력 (passive)
    geo = skills["class_0"][11]
    assert geo["name"] == "각력"
    assert geo["desc"].startswith("}돌진|"), \
        f"각력 desc 가 `}}돌진|` 로 시작 안 함: {geo['desc'][:30]!r}"
    print("[PASS] skills.json: 각력 desc 가 `}돌진|` 로 시작 (R112 decoder fix)")

    # 3. close marker `|` 또는 `{` 분기
    rsdd = gd[gd.find("func resolve_skill_desc_display(class_id"):
              gd.find("func resolve_skill_desc_first_line")]
    assert "close_pipe := raw.find" in rsdd or "close_pipe = raw.find" in rsdd, \
        "close_pipe 변수 누락"
    assert "close_brace := raw.find" in rsdd or "close_brace = raw.find" in rsdd, \
        "close_brace 변수 누락"
    assert 'raw.find("{", i + 1)' in rsdd, "{ close marker scan 누락"
    print("[PASS] resolve_skill_desc_display: `|` 또는 `{` close marker 분기 (R112 quirk)")

    # 4. 중첩 `}` 평탄화
    assert 'inner.replace("}", "")' in rsdd or '.replace("}", "")' in rsdd, \
        "중첩 `}` 평탄화 (inner.replace) 누락"
    print("[PASS] resolve_skill_desc_display: 중첩 `}` 평탄화")

    # 5. 불릿 line-start 가드
    assert "out.is_empty() or out.ends_with" in rsdd, "불릿 line-start 가드 누락"
    print("[PASS] resolve_skill_desc_display: 불릿 line-start 가드 (R112)")

    # 6. Python 시뮬 — quirk 처리
    def py_display(raw):
        out = ""
        i = 0
        while i < len(raw):
            c = raw[i]
            if c == "}":
                close_pipe = raw.find("|", i + 1)
                close_brace = raw.find("{", i + 1)
                if close_pipe == -1:
                    close = close_brace
                elif close_brace == -1:
                    close = close_pipe
                else:
                    close = min(close_pipe, close_brace)
                if close == -1:
                    out += c
                    i += 1
                    continue
                inner = raw[i + 1:close].replace("}", "")
                out += "[" + inner + "]"
                i = close + 1
            elif c == "{":
                close = raw.find("|", i + 1)
                if close == -1:
                    out += c
                    i += 1
                    continue
                header = raw[i + 1:close]
                out += "▸ 관련 특성:" if header == "관련특성" else "▸ " + header + ":"
                i = close + 1
            elif c == "#" and i + 2 < len(raw) and raw[i + 1].isdigit() and raw[i + 2].isdigit() \
                    and (not out or out.endswith("\n")):
                out += "• "
                i += 3
            elif c == ";":
                out += "\n"
                i += 1
            else:
                out += c
                i += 1
        return out

    # 봉쇄: `}시야를 }1|로` → `[시야를 1]로`
    bongseo = skills["class_0"][40]
    assert bongseo["name"] == "봉쇄"
    out = py_display(bongseo["desc"])
    assert "[시야를 1]" in out, "봉쇄 nested 닫힘없는 brace 평탄화 실패: " + repr(out[:120])
    print("[PASS] 봉쇄: `}시야를 }1|로` → `[시야를 1]로`")

    # 쐐기탄: `}민첩 12당 1{의` → `[민첩 12당 1]의`
    qjt = None
    for sk in skills["class_2"]:
        if sk["name"] == "쐐기탄":
            qjt = sk
            break
    assert qjt is not None
    out = py_display(qjt["desc"])
    assert "[민첩 12당 1]" in out, "쐐기탄 alt close marker 처리 실패: " + repr(out)
    print("[PASS] 쐐기탄: `}민첩 12당 1{의` → `[민첩 12당 1]의` (`{` alt close)")

    # 포격: 불릿 line-start 가드로 raw `|#07|` 유지 (false-positive 차단)
    pogeok = None
    for sk in skills["class_2"]:
        if sk["name"] == "포격":
            pogeok = sk
            break
    assert pogeok is not None
    out = py_display(pogeok["desc"])
    assert "|• |" not in out, f"포격 false-positive 불릿 발생: {out!r}"
    assert "|#07|" in out, f"포격 raw |#07| 보존 안 됨: {out!r}"
    print("[PASS] 포격: `사격당 |#07|의` 불릿 false-positive 차단 (line-start 가드)")

    # 7. R112 audit — 잔존 raw marker 1 개 이하 (포격 1건만 허용)
    # 시뮬 전체 — `}` `|` `{` raw 잔존 카운트
    cnt_issues = 0
    for cls_key in ("class_0", "class_1", "class_2", "class_3"):
        for sk in skills.get(cls_key, []):
            rendered = py_display(sk.get("desc", ""))
            for marker in ("}", "|", "{"):
                if marker in rendered:
                    cnt_issues += 1
                    break
    assert cnt_issues <= 1, f"R112 잔존 raw marker 이슈 {cnt_issues} > 1 (포격 외 회귀)"
    print(f"[PASS] R112 audit: 188 class skill 중 잔존 raw marker {cnt_issues}/188 (포격 1건만)")

    # 8. R111 회귀 — `{관련특성|` 섹션 헤더
    assert '"▸ 관련 특성:"' in rsdd, "R111 `▸ 관련 특성:` 변환 누락"
    print("[PASS] R111 회귀: `{관련특성|` 섹션 헤더")

    # 9. R110 회귀 — bracket-aware helper
    assert "func _replace_placeholders_in_brackets" in gd
    print("[PASS] R110 회귀: bracket-aware helper")

    # 10. R109 회귀 — PLACEHOLDER_LABELS 10 entry (R111 추가 포함)
    labels_block = gd[gd.find("const PLACEHOLDER_LABELS"):gd.find("const PLACEHOLDER_STAT_SOURCE")]
    label_count = len(re.findall(r'\d+:\s*"', labels_block))
    assert label_count == 10, f"PLACEHOLDER_LABELS entry 수 {label_count} (10 기대)"
    print("[PASS] R109/R111 회귀: PLACEHOLDER_LABELS 10 entry")

    # 11. R108 회귀 — 5 helper
    for marker in ("func eval_placeholder_stat", "func _calc_placeholder_formula"):
        assert marker in gd, f"R108 helper 누락: {marker}"
    print("[PASS] R108 회귀: helpers 잔존")

    # 12. R105 THRESHOLD
    assert "PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd
    print("[PASS] R105 회귀: THRESHOLD = 500")

    # 13. R90 회귀
    assert "func resolve_skill_desc_display(class_id" in gd
    print("[PASS] R90 회귀: resolve_skill_desc_display")

    # 14. R112 docstring marker
    assert "Round 112" in gd, "game_data.gd R112 marker 누락"
    assert "R112" in decoder, "decode_h5_skill.py R112 marker 누락"
    print("[PASS] R112 docstring marker (game_data + decoder)")

    print("\nR112 skill desc quirks 흡수: ALL PASSED")


if __name__ == "__main__":
    main()
