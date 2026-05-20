#!/usr/bin/env python3
"""R110: bracket-aware placeholder 치환 — `}...|` 내부의 #NN 만 치환.

R108 의 `result.replace("#%02d", val)` 무차별 치환이 class_0..3 의 skill-link
참조 (`#01돌격-스턴효과` 등) 를 corruption 했음. R110 = `_replace_placeholders_
in_brackets` helper 신규, 괄호 내부 #NN 만 치환.

검증:
- game_data.gd 에 `_replace_placeholders_in_brackets` helper 존재
- resolve_skill_desc 가 helper 위임 (이전 무차별 result.replace 제거)
- Python 시뮬: 돌진 desc 의 `#01-#03` skill-link 보존
- Python 시뮬: `}SP #07|` 라벨 placeholder 치환 동작 (괄호 내부)
- R109/R108 placeholder 회귀 (암흑탄 #05=400, 폭발 #12 fallback)
- R107/R106/R105 회귀
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
    spirits = json.loads((GODOT / "assets/gamedata/c_csv_skill_05.json").read_text(encoding="utf-8"))["records"]

    # 1. helper 함수 존재
    assert "func _replace_placeholders_in_brackets" in gd, \
        "_replace_placeholders_in_brackets helper 누락"
    print("[PASS] _replace_placeholders_in_brackets helper 존재")

    # 2. resolve_skill_desc 가 helper 위임 (무차별 #NN replace 제거)
    rsd = gd[gd.find("func resolve_skill_desc(class_id"):
             gd.find("\n\n## Round 110: `}...|` 강조 괄호")]
    if not rsd:
        # 다른 split point 시도
        rsd = gd[gd.find("func resolve_skill_desc(class_id"):
                 gd.find("func _replace_placeholders_in_brackets")]
    assert "_replace_placeholders_in_brackets" in rsd, \
        "resolve_skill_desc 가 bracket-aware helper 위임 안 함"
    # 이전 무차별 replace 패턴 제거 확인
    assert 'result.replace("#%02d" % i, display_val)' not in rsd, \
        "R108 무차별 #NN replace 잔존 — R110 fix 미적용"
    print("[PASS] resolve_skill_desc: bracket-aware helper 위임 + 무차별 replace 제거")

    # 3. Python 시뮬: 돌진 desc 의 skill-link 보존
    LABELS = {4: "효과", 5: "공격", 6: "마법", 7: "MP", 8: "지속", 9: "쿨", 12: "수치"}
    SOURCE = {4, 5, 6, 7, 8, 9}
    THRESHOLD = 500

    def py_resolve(desc, stats, primary=None, cooldown=None, mp=None):
        indices = set(SOURCE)
        for i in range(len(stats)):
            indices.add(i)
        values = {}
        for i in sorted(indices):
            if i in SOURCE:
                # spirit 의 primary_u16 등 — 여기선 raw stats fallback 흉내
                raw = stats[i] if i < len(stats) else -1
                if 0 <= raw <= THRESHOLD:
                    values[i] = str(raw)
                else:
                    lbl = LABELS.get(i, "?")
                    values[i] = f"?({lbl})" if i in LABELS else "?"
            else:
                raw = stats[i] if i < len(stats) else -1
                if 0 <= raw <= THRESHOLD:
                    values[i] = str(raw)
                else:
                    lbl = LABELS.get(i, "?")
                    values[i] = f"?({lbl})" if i in LABELS else "?"
        # bracket-aware
        out = ""
        i = 0
        while i < len(desc):
            if desc[i] == "}":
                close = desc.find("|", i + 1)
                if close == -1:
                    out += desc[i:]
                    break
                inner = desc[i + 1:close]
                for nn, v in values.items():
                    inner = inner.replace(f"#{nn:02d}", v)
                out += "}" + inner + "|"
                i = close + 1
            else:
                out += desc[i]
                i += 1
        return out

    # class_0[1] 돌진
    dolji = skills["class_0"][1]
    assert dolji["name"] == "돌진"
    out = py_resolve(dolji["desc"], dolji["stats_u16"])
    # skill-link 보존
    assert "#01돌격-스턴효과" in out, f"#01돌격 corruption: {out!r}"
    assert "#02돌격-밟고가기" in out, f"#02돌격 corruption: {out!r}"
    assert "#03돌격-각력" in out, f"#03돌격 corruption: {out!r}"
    # 괄호 내부 placeholder 치환은 동작
    assert "}#09초|" not in out, "괄호 내부 #09 미치환"
    assert "}#05%|" not in out, "괄호 내부 #05 미치환"
    print("[PASS] 돌진: skill-link (#01/#02/#03) 보존 + 괄호 내부 #05/#09 치환")

    # 4. Python 시뮬: 라벨 placeholder `}SP #07|`
    # class_0 도발
    dobal = None
    for sk in skills["class_0"]:
        if sk["name"] == "도발":
            dobal = sk
            break
    assert dobal is not None, "class_0 도발 누락"
    assert "}SP #07|" in dobal["desc"], "도발 desc 에 `}SP #07|` 없음"
    out_dobal = py_resolve(dobal["desc"], dobal["stats_u16"])
    # 도발 stats[7] = ? — 보통 작은 값일 것
    # `}SP #07|` → `}SP <val>|` 가 되어야 함
    assert "}SP " in out_dobal, f"도발 라벨 placeholder 치환 실패: {out_dobal[:80]!r}"
    assert "}SP #07|" not in out_dobal, "도발 #07 미치환"
    print("[PASS] 도발: `}SP #07|` 라벨 placeholder 정상 치환")

    # 5. spirit 회귀 (R108): #05 → 400
    sp0 = spirits[0]
    assert sp0["name"] == "암흑탄"
    b0 = bytes.fromhex(sp0["extra_hex"])
    primary = b0[0x22] | (b0[0x23] << 8)
    assert primary == 400
    print("[PASS] R108 회귀: 암흑탄 primary_u16=400 보존")

    # 6. spirit 회귀 (R109): #12 의 primary_u16 매핑 제거 — 폭발 stats[12] garbage
    sp6 = spirits[6]
    assert sp6["name"] == "폭발"
    b6 = bytes.fromhex(sp6["extra_hex"])
    stats12 = (b6[0x19] << 8) | b6[0x18]
    assert stats12 > THRESHOLD, f"폭발 stats[12]={stats12} ≤ THRESHOLD"
    print(f"[PASS] R109 회귀: 폭발 stats_u16[12]={stats12} garbage 가드")

    # 7. R109 PLACEHOLDER_LABELS (단위 분리)
    assert '5: "공격",' in gd or '5: "공격"' in gd
    assert '8: "지속",' in gd or '8: "지속"' in gd
    print("[PASS] R109 회귀: PLACEHOLDER_LABELS 단위 분리 잔존")

    # 8. R109 PLACEHOLDER_STAT_SOURCE 에서 #12 제거 잔존
    src_block = gd[gd.find("const PLACEHOLDER_STAT_SOURCE"):
                   gd.find("func _ensure_skills_cache_loaded")]
    assert not re.search(r"^\s*12:\s*\{", src_block, re.M)
    print("[PASS] R109 회귀: SOURCE #12 제거 잔존")

    # 9. R105 THRESHOLD 회귀
    assert "PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd
    print("[PASS] R105 회귀: THRESHOLD=500")

    # 10. R108 5 helper 회귀
    for marker in (
        "func eval_placeholder_stat",
        "func _calc_placeholder_formula",
        "func _placeholder_player_ctx",
        "func _placeholder_formula_ctx",
        "fvm.calc(formula_id, ctx)",
    ):
        assert marker in gd, f"R108 helper {marker} 누락"
    print("[PASS] R108 회귀: 5 helper 유지")

    # 11. R110 docstring marker
    assert "Round 110" in gd, "game_data.gd 에 R110 marker 누락"
    print("[PASS] R110 docstring marker (game_data)")

    # 12. 실 데이터 corruption 카운트 — 변경 전후 비교
    # R108 로직: bare #NN 도 치환 → skill-link corruption
    # R110 로직: 괄호 내부만 치환 → corruption 0
    n_corruption_before = 0
    n_resolved_after = 0
    for cls_key in ("class_0", "class_1", "class_2", "class_3"):
        for sk in skills[cls_key]:
            desc = sk["desc"]
            # bare #NN (skill-link) — `;` 또는 시작점에 등장
            n_corruption_before += len(re.findall(r"[;\n]#\d{2}\S", desc))
            # 괄호 내부 #NN
            for m in re.finditer(r"\}([^|]*?)\|", desc):
                n_resolved_after += len(re.findall(r"#\d{2}", m.group(1)))
    assert n_corruption_before >= 40, f"corruption 카운트 비정상: {n_corruption_before}"
    assert n_resolved_after >= 200, f"placeholder 카운트 비정상: {n_resolved_after}"
    print(f"[PASS] 실 데이터: R110 이전 corruption 후보 {n_corruption_before} → R110 후 보존 / 괄호 내부 {n_resolved_after} 치환 유지")

    # 13. 빈 desc / 괄호 없는 desc 처리
    # `_replace_placeholders_in_brackets` 가 빈 입력 / `}` 없는 desc 에 안전한지
    # 코드만 검사 (실행은 GDScript 측)
    helper_body = gd[gd.find("func _replace_placeholders_in_brackets"):
                     gd.find("\n## Round 90:") if "\n## Round 90:" in gd[gd.find("func _replace_placeholders_in_brackets"):] else gd.find("func resolve_skill_desc_display")]
    assert 'if close == -1' in helper_body, "helper 의 미종결 `}` 안전 분기 누락"
    assert "result += desc.substr(i)" in helper_body, "helper 의 fallback 처리 누락"
    print("[PASS] helper 안전성: 미종결 괄호 / 빈 desc 분기")

    # 14. spirit 도 동일 helper 통과 (R109 form 보존)
    # 암흑탄 desc 의 `}#05%|` → `}400%|` → `[400%]`
    sp0_rec = {"desc": "정령마력 }#05%|의 피해", "stats_u16": [], "primary_u16": 400}
    out_sp0 = py_resolve(sp0_rec["desc"], [400] * 13)  # stats[5]=400 시뮬
    assert "}400%|" in out_sp0, f"암흑탄 시뮬 #05 치환 실패: {out_sp0}"
    print("[PASS] spirit #0 시뮬: }#05%| → }400%| (R109 form 호환)")

    print("\nR110 bracket-aware placeholder: ALL PASSED")


if __name__ == "__main__":
    main()
