#!/usr/bin/env python3
"""R102: HUD AudioIndicator + Audio.mute_changed signal (E +0.1%p).

R101 의 bus layout 후속 — F8 또는 SettingsPanel 의 mute 체크박스로 토글한
상태가 화면 상단 HUD 에는 visible 하지 않았음. R102 = HUD 우상단에 작은
indicator (♪ 연두 ↔ 🔇 빨강) + AudioManager 의 mute_changed signal 로
polling 없이 동기화.

검증:
- audio_manager.gd: `signal mute_changed(muted: bool)` 신규.
- set_muted 가 상태 변경 시에만 mute_changed.emit (무한 cycle 방지).
- hud.tscn: AudioIndicator Label 노드 신규 (offset_right=316, 우상단,
  tooltip "F8 — 음소거 토글").
- hud.gd: @onready var audio_indicator + Audio.mute_changed.connect +
  _on_mute_changed handler + 초기 Audio.is_muted() 적용 + AUDIO_ON/OFF
  텍스트/색상 상수.
- R98-R101 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    am = read("scripts/core/audio_manager.gd")
    hud = read("scripts/ui/hud.gd")
    tscn = read("scenes/hud.tscn")
    sp = read("scripts/ui/settings_panel.gd")
    demo = read("scripts/ui/demo.gd")

    # 1. audio_manager mute_changed signal
    assert "signal mute_changed(muted: bool)" in am, \
        "mute_changed signal 누락"
    print("[PASS] AudioManager: signal mute_changed(muted: bool) 신규")

    # 2. set_muted 의 emit (changed 시에만)
    set_muted_section = am[am.find("func set_muted"):am.find("\n\n", am.find("func set_muted"))]
    assert "var changed := (_muted != mute)" in set_muted_section, \
        "set_muted 의 변화 감지 누락"
    assert "mute_changed.emit(_muted)" in set_muted_section, \
        "set_muted 의 emit 누락"
    assert "if changed:" in set_muted_section, \
        "set_muted 의 changed 가드 누락 (무한 cycle 방지)"
    print("[PASS] AudioManager.set_muted: changed 가드 + mute_changed.emit")

    # 3. hud.tscn AudioIndicator 노드
    assert '[node name="AudioIndicator" type="Label" parent="HUD"]' in tscn, \
        "hud.tscn 의 AudioIndicator 노드 누락"
    # tooltip 은 R102 시점 "F8 — 음소거 토글" / R103+ "F8 또는 클릭 — 음소거 토글".
    assert "F8" in tscn and "음소거 토글" in tscn, \
        "AudioIndicator 의 F8 tooltip 누락"
    # 우상단 배치
    ind_section = tscn[tscn.find('"AudioIndicator"'):]
    assert "offset_right = 316.0" in ind_section, "AudioIndicator 우측 배치 누락"
    print("[PASS] hud.tscn: AudioIndicator Label (offset_right=316, F8 tooltip)")

    # 4. hud.gd @onready var + signal 연결 + handler
    assert "@onready var audio_indicator: Label = $HUD/AudioIndicator" in hud
    assert "Audio.mute_changed.connect(_on_mute_changed)" in hud, \
        "hud.gd 의 mute_changed.connect 누락"
    assert "func _on_mute_changed(muted: bool)" in hud, \
        "_on_mute_changed handler 누락"
    print("[PASS] hud.gd: @onready var audio_indicator + mute_changed 연결 + handler")

    # 5. handler 의 ON/OFF 분기 (텍스트 + 색상)
    handler_section = hud[hud.find("func _on_mute_changed"):]
    for marker in [
        "AUDIO_OFF_TEXT",
        "AUDIO_ON_TEXT",
        "AUDIO_OFF_COLOR",
        "AUDIO_ON_COLOR",
        "add_theme_color_override",
    ]:
        assert marker in handler_section, f"_on_mute_changed marker 누락: {marker!r}"
    print("[PASS] hud._on_mute_changed: ON/OFF 텍스트 + 색상 override")

    # 6. ON/OFF 상수
    for const_name in [
        'const AUDIO_ON_TEXT := "♪"',
        'const AUDIO_OFF_TEXT := "🔇"',
        "const AUDIO_ON_COLOR := Color",
        "const AUDIO_OFF_COLOR := Color",
    ]:
        assert const_name in hud, f"상수 누락: {const_name!r}"
    print("[PASS] hud.gd: AUDIO_ON/OFF 텍스트/색상 4 상수")

    # 7. 초기 상태 적용 (_ready 끝에 _on_mute_changed(Audio.is_muted()))
    ready_section = hud[hud.find("func _ready"):hud.find("func _refresh")]
    assert "_on_mute_changed(Audio.is_muted())" in ready_section, \
        "_ready 의 초기 mute 상태 적용 누락"
    print("[PASS] hud._ready: 초기 Audio.is_muted() 적용")

    # 8. Python 시뮬: mute_changed 가 changed 시에만 발화
    state = {"muted": False, "emit_count": 0}
    def set_muted(mute):
        changed = state["muted"] != mute
        state["muted"] = mute
        if changed:
            state["emit_count"] += 1
    set_muted(False)  # 변화 없음
    assert state["emit_count"] == 0
    set_muted(True)   # off → on
    assert state["emit_count"] == 1
    set_muted(True)   # on → on (중복)
    assert state["emit_count"] == 1
    set_muted(False)  # on → off
    assert state["emit_count"] == 2
    print("[PASS] Python 시뮬 changed 가드: 중복 set 시 emit 안 함 (cycle 방지)")

    # 9. R101 회귀: bus layout
    bus = (GODOT / "default_bus_layout.tres").read_text(encoding='utf-8')
    assert 'bus/1/name = &"BGM"' in bus
    assert 'bus/2/name = &"SFX"' in bus
    print("[PASS] R101 회귀: default_bus_layout.tres 3 bus")

    # 10. R99 회귀
    assert "func sync_mute_check(state: bool)" in sp
    print("[PASS] R99 회귀: sync_mute_check")

    # 11. R98 회귀
    for fn in ["func is_muted()", "func set_muted(", "func toggle_mute()"]:
        assert fn in am
    print("[PASS] R98 회귀: AudioManager mute 3 API")

    # 12. R97 회귀
    assert "static func slider_to_db(v: float) -> float:" in am
    print("[PASS] R97 회귀: slider_to_db")

    # 13. R96 회귀
    assert demo.count('preload("res://scripts/ui/toast.gd").show_msg(') == 0
    print("[PASS] R96 회귀: Toast 마이그레이션")

    # 14. R102 docstring marker
    assert "Round 102" in am, "R102 marker 누락 (audio_manager)"
    assert "Round 102" in hud, "R102 marker 누락 (hud)"
    print("[PASS] R102 docstring marker (audio_manager + hud)")

    # 15. demo 의 sync_mute_check 호출 — R99 inline 또는 R103+ signal 핸들러.
    assert "_settings.sync_mute_check(muted)" in demo, \
        "demo 의 sync_mute_check 호출 누락 (F8 inline 또는 mute_changed handler)"
    print("[PASS] R99 회귀: demo 의 sync_mute_check 호출 (F8 inline 또는 signal handler)")

    print("\n[R102 ALL PASSED] 15/15")


if __name__ == "__main__":
    main()
