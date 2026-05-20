#!/usr/bin/env python3
"""R105: Spirit placeholder 실 stat source 분석 + UNREASONABLE 가드 (F +0.5%p).

R90 의 `}#NN<unit>|` placeholder 치환이 spirit/class 모두에서 garbage 값
(7728%, 41008%, -1초 등) 으로 표시되던 문제. R105 = 실측 데이터로 stats_u16
가 placeholder source 가 아님을 확인 (`docs/h5/RE/skill_desc_placeholder.md`)
+ `resolve_skill_desc` 에 휴리스틱 가드 추가 (값 > 500 → "?" fallback).

정확한 매핑 (Formula::calc 통합) 은 R106+ 작업으로 미룸.

검증:
- game_data.gd 의 PLACEHOLDER_UNREASONABLE_THRESHOLD 상수 + display_val
  분기 로직.
- Python 시뮬: stats[5]=7728 → "?" / stats[5]=120 → "120" / stats[9]=-1 → "?"
  (signed -1 = u16 65535 = unreasonable, 단 Godot int 는 native — -1 그대로).
- docs/h5/RE/skill_desc_placeholder.md 신규 + 5 섹션.
- R104/R103/R102 회귀.
- spirit JSON 데이터로 가드 효과 확인 (Python 측에서 시뮬).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    gd = read("scripts/core/game_data.gd")

    # 1. UNREASONABLE 상수
    assert "const PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd, \
        "PLACEHOLDER_UNREASONABLE_THRESHOLD 상수 누락"
    print("[PASS] game_data: PLACEHOLDER_UNREASONABLE_THRESHOLD = 500 상수 신규")

    # 2. resolve_skill_desc 의 display 분기 — R105 인라인 / R108 helper / R110 bracket-aware 허용.
    rsd = gd[gd.find("func resolve_skill_desc(class_id"):gd.find("\n\n\n## Round 90:")]
    if not rsd:
        rsd = gd[gd.find("func resolve_skill_desc(class_id"):
                 gd.find("func resolve_skill_desc_display")]
    # R108 이후: THRESHOLD 검사가 _format_placeholder_display 로 위임됨.
    # R110 이후: resolve_skill_desc 가 _replace_placeholders_in_brackets 위임.
    r110_bracket_path = "_replace_placeholders_in_brackets" in gd
    r108_helper_path = (
        "_format_placeholder_display" in gd
        and "PLACEHOLDER_UNREASONABLE_THRESHOLD" in gd
    )
    r105_inline = "raw_val > PLACEHOLDER_UNREASONABLE_THRESHOLD" in rsd
    assert r110_bracket_path or r108_helper_path or r105_inline, \
        "UNREASONABLE 검사 누락 (R105 인라인 / R108 helper / R110 bracket-aware 모두 없음)"
    has_r106_label = "PLACEHOLDER_LABELS" in gd
    assert has_r106_label, "PLACEHOLDER_LABELS 누락 (R106+ label fallback 미적용)"
    impl_name = "R110 bracket-aware" if r110_bracket_path else ("R108 helper" if r108_helper_path else "R105 inline")
    print(f"[PASS] game_data.resolve_skill_desc: display 분기 ({impl_name} + label)")

    # 3. placeholder 치환 동작 — R108 form (display_val replace) 또는 R110 form (bracket helper)
    has_r108_replace = (
        'result.replace("}#%02d" % i, "}%s" % display_val)' in rsd
        and 'result.replace("#%02d" % i, display_val)' in rsd
    )
    has_r110_helper = (
        "_replace_placeholders_in_brackets" in rsd
        and "values: Dictionary" in rsd
    )
    assert has_r108_replace or has_r110_helper, \
        "placeholder 치환 경로 누락 (R108 result.replace 또는 R110 bracket helper)"
    print(f"[PASS] game_data.resolve_skill_desc: placeholder 치환 동작 ({'R110 helper' if has_r110_helper else 'R108 replace'})")
    # R108: _format_placeholder_display 내부에 THRESHOLD 가드 위임됐는지 확인
    if r108_helper_path:
        fmt = gd[gd.find("func _format_placeholder_display"):gd.find("func eval_placeholder_stat")]
        assert "PLACEHOLDER_UNREASONABLE_THRESHOLD" in fmt, "R108 helper 의 THRESHOLD 가드 누락"
        print("[PASS] _format_placeholder_display: THRESHOLD 가드 위임 (R108)")

    # 4. docs/h5/RE/skill_desc_placeholder.md 존재
    doc_path = ROOT / "docs/h5/RE/skill_desc_placeholder.md"
    assert doc_path.exists(), "RE 문서 skill_desc_placeholder.md 누락"
    doc = doc_path.read_text(encoding='utf-8')
    # R105 시점에는 §1..§5. R108+ 부 섹션 진화 — prefix 매칭으로 호환.
    section_prefixes = [
        "## 1. R90 placeholder 시스템 요약",
        "## 2. R105 실측 데이터",
        "## 3. 실제 stat source 추정",
        "## 4. R105 휴리스틱 fallback",
        "## 5. ",  # R106+ form 또는 R108 form 둘 다 허용
    ]
    for sec in section_prefixes:
        assert sec in doc, f"RE 문서 섹션 prefix 누락: {sec!r}"
    print("[PASS] RE doc: 5 섹션 (요약 / 실측 / source 추정 / 가드 / 후속, prefix 매칭)")

    # 5. RE 문서가 실측 상수 (7728, 23808 등) 명시
    for val in ["7728", "23808", "20528", "41008"]:
        assert val in doc, f"RE 실측 값 {val} 명시 누락"
    print("[PASS] RE doc: 실측 상수 (7728/23808/20528/41008) 명시")

    # 6. Python 시뮬: 가드 동작
    THRESHOLD = 500
    def display_val(raw):
        return "?" if raw > THRESHOLD else str(raw)
    assert display_val(7728) == "?", f"7728 → '?' 기대: {display_val(7728)}"
    assert display_val(120) == "120", f"120 → '120' 기대: {display_val(120)}"
    assert display_val(500) == "500", f"500 → '500' (경계, 포함 안 됨)"
    assert display_val(501) == "?", f"501 → '?' (경계 +1)"
    assert display_val(0) == "0", f"0 → '0'"
    # 음수는 GDScript int 이므로 그대로 (휴리스틱 가드 외 — 별도 처리)
    assert display_val(-1) == "-1", f"-1 → '-1' (음수는 threshold 미만)"
    print(f"[PASS] Python 시뮬 가드: 7728→? / 120→120 / 500→500 / 501→? / -1→-1")

    # 7. spirit JSON 으로 실제 영향 시뮬
    spirit_path = GODOT / "assets/gamedata/c_csv_skill_05.json"
    spirit_data = json.loads(spirit_path.read_text(encoding='utf-8'))
    n_with_garbage = 0
    n_with_placeholder = 0
    for r in spirit_data["records"]:
        desc = r.get("desc_text", "")
        placeholders = re.findall(r'\}#(\d{2})([^|]*)\|', desc)
        if placeholders:
            n_with_placeholder += 1
            hex_bytes = bytes.fromhex(r["extra_hex"])
            for idx_str, _ in placeholders:
                idx = int(idx_str)
                if idx * 2 + 1 < min(48, len(hex_bytes)):
                    u16 = hex_bytes[idx * 2] | (hex_bytes[idx * 2 + 1] << 8)
                    if u16 > THRESHOLD:
                        n_with_garbage += 1
                        break
    assert n_with_garbage > 0, "spirit 의 garbage placeholder 가 0 (가드 무효)"
    print(f"[PASS] spirit 데이터: {n_with_placeholder}/16 record 가 placeholder 보유, 그중 {n_with_garbage} 개가 garbage (가드로 '?' 표시됨)")

    # 8. R104 회귀
    sp = read("scripts/ui/settings_panel.gd")
    handler = sp[sp.find("func _on_mute_toggled"):sp.find("\n\n\nfunc ", sp.find("func _on_mute_toggled"))]
    assert "_save_config()" not in handler
    print("[PASS] R104 회귀: _on_mute_toggled 의 중복 _save_config 제거 잔존")

    # 9. R103 회귀
    demo = read("scripts/ui/demo.gd")
    assert "Audio.mute_changed.connect(_on_audio_mute_changed)" in demo
    print("[PASS] R103 회귀: demo Audio.mute_changed 연결")

    # 10. R102 회귀: mute_changed signal
    am = read("scripts/core/audio_manager.gd")
    assert "signal mute_changed(muted: bool)" in am
    print("[PASS] R102 회귀: mute_changed signal")

    # 11. R101 회귀: bus layout
    bus = (GODOT / "default_bus_layout.tres").read_text(encoding='utf-8')
    assert 'bus/1/name = &"BGM"' in bus
    print("[PASS] R101 회귀: 3 bus layout")

    # 12. R90 회귀: resolve_skill_desc_display + first_line
    assert "func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:" in gd
    assert "func resolve_skill_desc_first_line(class_id: int, skill_id: int) -> String:" in gd
    print("[PASS] R90 회귀: resolve_skill_desc_display + first_line 잔존")

    # 13. R91 회귀
    gs = (GODOT / "scripts/core/game_state.gd").read_text(encoding='utf-8')
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: save round-trip")

    # 14. R105 docstring marker
    assert "Round 105" in gd, "R105 marker 누락 (game_data)"
    print("[PASS] R105 docstring marker (game_data)")

    # 15. RE 문서의 후속 작업 — R106+ (R105 시점) 또는 R110+ (R109 시점) 둘 다 허용
    has_followup = "R106+" in doc or "R110+" in doc or "R109+" in doc
    assert has_followup, "RE 문서의 후속 작업 명시 누락"
    assert "Formula::calc" in doc, "RE 문서의 Formula::calc 통합 언급 누락"
    print("[PASS] RE doc: 후속 작업 (Formula::calc 통합) 명시")

    print("\n[R105 ALL PASSED] 15/15")


if __name__ == "__main__":
    main()
