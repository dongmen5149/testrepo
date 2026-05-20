#!/usr/bin/env python3
"""R106: Placeholder NN → 의미 label 매핑 (RE +0.2%p).

R105 의 garbage `[?%]` fallback 후속 — `?` 대신 R75 convention 기반의 의미
label (e.g. "공격%", "쿨초", "지속초") 노출. 사용자가 "이 자리에 어떤 stat 이
들어가는지" 를 알 수 있음.

검증:
- game_data.gd 의 PLACEHOLDER_LABELS dict (7 entry: 4/5/6/7/8/9/12).
- resolve_skill_desc 의 display_val 분기 — unreasonable 시 label 사용.
- Python 시뮬: stats[5]=7728 + #05%| → "?(공격%)%" / stats[5]=120 → "120%".
- RE 문서의 §4 갱신 (R106 label 매핑 표).
- R105 가드 자체는 유지 (THRESHOLD=500).
- R90-R104 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    gd = read("scripts/core/game_data.gd")
    doc = (ROOT / "docs/h5/RE/skill_desc_placeholder.md").read_text(encoding='utf-8')

    # 1. PLACEHOLDER_LABELS dict — R106 form (unit 포함) 또는 R109 form (unit 분리) 둘 다 허용
    assert "const PLACEHOLDER_LABELS := {" in gd, "PLACEHOLDER_LABELS 상수 누락"
    label_options = [
        (4, ["효과%", "효과"]), (5, ["공격%", "공격"]), (6, ["마법%", "마법"]),
        (7, ["MP"]), (8, ["지속초", "지속"]), (9, ["쿨초", "쿨"]),
        (12, ["배수", "수치"]),
    ]
    for nn, labels in label_options:
        assert any(f'{nn}: "{lab}"' in gd for lab in labels), \
            f"PLACEHOLDER_LABELS NN {nn} 누락 (허용: {labels})"
    print("[PASS] PLACEHOLDER_LABELS: 7 NN (R106/R109 form 모두 허용)")

    # 2. resolve_skill_desc — R106 label 또는 R108 Formula 분기
    rsd = gd[gd.find("func resolve_skill_desc(class_id"):gd.find("\n\n\n## Round 90:")]
    r108 = "PLACEHOLDER_STAT_SOURCE.has(i)" in rsd and "_resolve_placeholder_stat" in rsd
    r106 = "PLACEHOLDER_LABELS.has(i)" in rsd or "_format_placeholder_display" in gd
    assert r108 or r106, "label/Formula placeholder 분기 누락"
    print("[PASS] resolve_skill_desc: R108 Formula 분기 또는 R106 label fallback")

    # 3. R105 가드 잔존
    assert "PLACEHOLDER_UNREASONABLE_THRESHOLD" in gd
    assert "const PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd
    print("[PASS] R105 가드 잔존: UNREASONABLE_THRESHOLD = 500")

    # 4. Python 시뮬: label fallback — R106 form 또는 R109 form 둘 다 허용
    # game_data.gd 에서 실 사용 중인 label 추출
    labels_block = gd[gd.find("const PLACEHOLDER_LABELS"):gd.find("const PLACEHOLDER_STAT_SOURCE")]
    LABELS = {}
    for m in re.finditer(r'^\s*(\d+):\s*"([^"]+)",?\s*$', labels_block, re.M):
        LABELS[int(m.group(1))] = m.group(2)
    assert set(LABELS.keys()) >= {4, 5, 6, 7, 8, 9, 12}, f"LABELS keys 부족: {LABELS.keys()}"
    THRESHOLD = 500
    def disp(i, raw):
        if raw > THRESHOLD:
            return f"?({LABELS[i]})" if i in LABELS else "?"
        return str(raw)
    assert disp(5, 7728) == f"?({LABELS[5]})", f"5+7728 → ?({LABELS[5]})"
    assert disp(9, 32569) == f"?({LABELS[9]})", f"9+32569 → ?({LABELS[9]})"
    assert disp(8, 1000) == f"?({LABELS[8]})", f"8+1000 → ?({LABELS[8]})"
    assert disp(5, 120) == "120", "5+120 → '120' (정상)"
    assert disp(99, 7728) == "?", "99(미매핑)+7728 → '?'"
    assert disp(12, 5000) == f"?({LABELS[12]})", f"12+5000 → ?({LABELS[12]})"
    print(f"[PASS] Python 시뮬 label fallback: 6 case (LABELS={LABELS})")

    # 5. RE 문서 §4 의 label 표 — R106 form 또는 R109 form
    assert "PLACEHOLDER_LABELS" in doc or "의미 매핑" in doc, "RE 문서 §4 label 매핑 추가 누락"
    for label_a, label_b in [("효과%", "효과"), ("공격%", "공격"), ("MP", "MP"),
                              ("지속초", "지속"), ("쿨초", "쿨"), ("배수", "수치")]:
        assert label_a in doc or label_b in doc, \
            f"RE 문서 label {label_a}/{label_b} 누락"
    print("[PASS] RE 문서: 6 label 매핑 표 (R106/R109 form 허용)")

    # 6. R105 회귀: garbage 차단
    assert "const PLACEHOLDER_UNREASONABLE_THRESHOLD := 500" in gd
    print("[PASS] R105 회귀: garbage 차단 가드")

    # 7. R104 회귀
    sp = read("scripts/ui/settings_panel.gd")
    handler = sp[sp.find("func _on_mute_toggled"):sp.find("\n\n\nfunc ", sp.find("func _on_mute_toggled"))]
    assert "_save_config()" not in handler
    print("[PASS] R104 회귀: 중복 save 제거 유지")

    # 8. R103 회귀
    demo = read("scripts/ui/demo.gd")
    assert "Audio.mute_changed.connect(_on_audio_mute_changed)" in demo
    print("[PASS] R103 회귀: mute_changed 연결")

    # 9. R102 회귀
    am = read("scripts/core/audio_manager.gd")
    assert "signal mute_changed(muted: bool)" in am
    print("[PASS] R102 회귀: mute_changed signal")

    # 10. R101 회귀
    bus = (GODOT / "default_bus_layout.tres").read_text(encoding='utf-8')
    assert 'bus/1/name = &"BGM"' in bus
    print("[PASS] R101 회귀: bus layout")

    # 11. R90 회귀: display + first_line
    assert "func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:" in gd
    assert "func resolve_skill_desc_first_line(class_id: int, skill_id: int) -> String:" in gd
    print("[PASS] R90 회귀: display + first_line")

    # 12. R91 회귀
    gs = (GODOT / "scripts/core/game_state.gd").read_text(encoding='utf-8')
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: round-trip")

    # 13. R106 docstring marker
    assert "Round 106" in gd, "R106 docstring marker 누락 (game_data)"
    print("[PASS] R106 docstring marker (game_data)")

    # 14. 미매핑 NN 안전 fallback (label dict.has 검사)
    # display_val 표현이 label 미정의 시 `?` 유지하는지
    expr_match = (
        "PLACEHOLDER_LABELS.has(i)" in rsd
        or 'PLACEHOLDER_LABELS.get(i, "?")' in rsd
        or "_format_placeholder_display" in gd
    )
    assert expr_match, "미매핑 NN 의 ? fallback 보존 누락"
    print("[PASS] resolve_skill_desc: 미매핑 NN 의 '?' fallback 보존")

    # 15. 합성 시뮬 — full string replace flow
    def simulate_resolve(desc, stats):
        result = desc
        for i, raw in enumerate(stats):
            if raw > THRESHOLD:
                disp_v = f"?({LABELS[i]})" if i in LABELS else "?"
            else:
                disp_v = str(raw)
            result = result.replace(f"}}#{i:02d}", f"}}{disp_v}")
            result = result.replace(f"#{i:02d}", disp_v)
        return result
    out = simulate_resolve("정령마력 }#05%|의 피해", [0]*10 + [7728])
    # i=5 missing — stats has only 11 elements (idx 0..10), idx 5 = 0 (정상)
    # 다시 작성
    stats_test = [0, 0, 0, 0, 0, 7728, 0, 30, 0, 32569, 0, 0]
    out2 = simulate_resolve("정령마력 }#05%|의", stats_test)
    assert f"?({LABELS[5]})" in out2, f"공격 label 미적용: {out2}"
    out3 = simulate_resolve("재사용대기 }#09초|", stats_test)
    assert f"?({LABELS[9]})" in out3, f"쿨 label 미적용: {out3}"
    out4 = simulate_resolve("MP }#07|", stats_test)  # stats[7]=30 < 500 → 정상
    assert "30" in out4 and "?" not in out4, f"정상 값 표시 실패: {out4}"
    print(f"[PASS] 합성 시뮬 (LABELS[5]={LABELS[5]} / LABELS[9]={LABELS[9]} / 정상값 30): 모두 의도대로 표시")

    print(f"\n[R106 (R109 form 호환) ALL PASSED] 15/15")


if __name__ == "__main__":
    main()
