#!/usr/bin/env python3
"""R103: HUD AudioIndicator 클릭 토글 + mute_changed 단일 핸들러 중앙화 (E +0.1%p).

R102 의 indicator + signal 후속. 사용자가 indicator 를 봐도 클릭으로 토글할
수 없었고, F8 핸들러 / SettingsPanel _on_mute_toggled / HUD 가 각각 다른
경로로 처리하던 sync 로직을 한 핸들러에 모음.

검증:
- hud.tscn AudioIndicator: mouse_filter=0 (STOP) + tooltip 갱신.
- hud.gd: audio_indicator.gui_input.connect(_on_audio_indicator_input) +
  handler 가 좌클릭 release 시 Audio.toggle_mute() 호출.
- demo.gd: _ready 끝에 Audio.mute_changed.connect(_on_audio_mute_changed) +
  handler 가 sync_mute_check + _save_config + Toast warn/info 통합.
- demo.gd F8 핸들러 단순화: Audio.toggle_mute() 단일 호출, 별도 sync/Toast
  로직 제거 (signal 핸들러가 모두 담당).
- R98-R102 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    hud = read("scripts/ui/hud.gd")
    tscn = read("scenes/hud.tscn")
    demo = read("scripts/ui/demo.gd")
    am = read("scripts/core/audio_manager.gd")
    sp = read("scripts/ui/settings_panel.gd")

    # 1. tscn mouse_filter=0 + tooltip 갱신
    ind = tscn[tscn.find('"AudioIndicator"'):]
    assert "mouse_filter = 0" in ind, "AudioIndicator mouse_filter=0 누락"
    assert 'tooltip_text = "F8 또는 클릭 — 음소거 토글"' in ind, \
        "AudioIndicator tooltip 갱신 누락 (클릭 가능 명시)"
    print("[PASS] hud.tscn AudioIndicator: mouse_filter=0 (STOP) + tooltip 'F8 또는 클릭'")

    # 2. hud.gd gui_input 연결 + handler
    assert "audio_indicator.gui_input.connect(_on_audio_indicator_input)" in hud, \
        "audio_indicator.gui_input 연결 누락"
    assert "func _on_audio_indicator_input(event: InputEvent)" in hud, \
        "_on_audio_indicator_input handler 누락"
    handler = hud[hud.find("func _on_audio_indicator_input"):]
    assert "InputEventMouseButton" in handler, "InputEventMouseButton 검사 누락"
    assert "MOUSE_BUTTON_LEFT" in handler, "좌클릭 검사 누락"
    assert "not event.pressed" in handler, "release 시점 (not pressed) 검사 누락"
    assert "Audio.toggle_mute()" in handler, "Audio.toggle_mute() 호출 누락"
    print("[PASS] hud.gd: gui_input 연결 + _on_audio_indicator_input (좌클릭 release → toggle_mute)")

    # 3. demo.gd 의 mute_changed 단일 핸들러
    assert "Audio.mute_changed.connect(_on_audio_mute_changed)" in demo, \
        "demo Audio.mute_changed 연결 누락"
    assert "func _on_audio_mute_changed(muted: bool)" in demo, \
        "_on_audio_mute_changed handler 누락"
    demo_handler = demo[demo.find("func _on_audio_mute_changed"):demo.find("\nfunc _input")]
    assert "_settings.sync_mute_check(muted)" in demo_handler
    assert "_settings._save_config()" in demo_handler
    assert "Toast.warn(self," in demo_handler
    assert "Toast.info(self," in demo_handler
    print("[PASS] demo.gd: _on_audio_mute_changed 단일 핸들러 (sync + save + Toast 통합)")

    # 4. F8 핸들러 단순화 — Audio.toggle_mute() 만, 별도 sync/save/Toast 제거
    f8_idx = demo.find("KEY_F8:")
    # 다음 case 까지의 영역
    next_case = demo.find("KEY_", f8_idx + 10)
    f8_block = demo[f8_idx:next_case] if next_case > 0 else demo[f8_idx:f8_idx + 500]
    assert "Audio.toggle_mute()" in f8_block, "F8 의 toggle_mute 호출 누락"
    # F8 자체에서는 sync_mute_check / _save_config / Toast 호출 제거됨
    assert "_settings.sync_mute_check(" not in f8_block, \
        "F8 자체에 sync_mute_check 잔존 (R103 중앙화 미적용)"
    assert "Toast.warn(self," not in f8_block, "F8 자체에 Toast.warn 잔존"
    assert "Toast.info(self,\n					\"🔊" not in f8_block, "F8 자체에 음소거 해제 Toast 잔존"
    print("[PASS] demo.gd F8: 단순화 (toggle_mute 만, sync/save/Toast 는 signal 핸들러로)")

    # 5. R102 회귀: mute_changed signal + set_muted 의 changed 가드
    assert "signal mute_changed(muted: bool)" in am
    assert "var changed := (_muted != mute)" in am
    assert "mute_changed.emit(_muted)" in am
    print("[PASS] R102 회귀: mute_changed signal + changed 가드")

    # 6. R102 회귀: HUD AudioIndicator + handler 잔존
    assert "@onready var audio_indicator: Label = $HUD/AudioIndicator" in hud
    assert "Audio.mute_changed.connect(_on_mute_changed)" in hud
    assert "func _on_mute_changed(muted: bool)" in hud
    print("[PASS] R102 회귀: HUD AudioIndicator + signal handler 잔존")

    # 7. R101 회귀: bus layout
    bus = (GODOT / "default_bus_layout.tres").read_text(encoding='utf-8')
    assert 'bus/1/name = &"BGM"' in bus and 'bus/2/name = &"SFX"' in bus
    print("[PASS] R101 회귀: 3 bus")

    # 8. R99 회귀: sync_mute_check + _on_mute_toggled
    assert "func sync_mute_check(state: bool)" in sp
    assert "func _on_mute_toggled(on: bool)" in sp
    print("[PASS] R99 회귀: sync_mute_check + _on_mute_toggled")

    # 9. R98 회귀: AudioManager mute 3 API
    for fn in ["func is_muted()", "func set_muted(", "func toggle_mute()"]:
        assert fn in am
    print("[PASS] R98 회귀: mute 3 API")

    # 10. R96 회귀: Toast 마이그레이션
    assert demo.count('preload("res://scripts/ui/toast.gd").show_msg(') == 0
    print("[PASS] R96 회귀: Toast 마이그레이션")

    # 11. R91 회귀
    gs = (GODOT / "scripts/core/game_state.gd").read_text(encoding='utf-8')
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: save round-trip")

    # 12. R103 docstring marker
    assert "Round 103" in hud, "R103 marker 누락 (hud)"
    assert "Round 103" in demo, "R103 marker 누락 (demo)"
    print("[PASS] R103 docstring marker (hud + demo)")

    # 13. 통합 시뮬: 3 토글 경로 모두 같은 signal chain
    # F8: Audio.toggle_mute → set_muted → mute_changed.emit → demo handler
    # HUD click: gui_input → Audio.toggle_mute → ... → demo handler (동일)
    # SettingsPanel checkbox: _on_mute_toggled → Audio.set_muted → ... → demo handler
    # 모두 demo._on_audio_mute_changed 도달
    # 코드에서 검증: 3 entry point 가 Audio.set_muted 또는 toggle_mute 호출
    assert "Audio.toggle_mute()" in handler  # HUD
    assert "Audio.toggle_mute()" in f8_block  # F8
    sp_handler = sp[sp.find("func _on_mute_toggled"):sp.find("\n\n", sp.find("func _on_mute_toggled"))]
    assert "Audio.set_muted(on)" in sp_handler  # SettingsPanel
    print("[PASS] 3 토글 entry point (F8 / HUD click / SettingsPanel) 모두 Audio API 로 수렴")

    print("\n[R103 ALL PASSED] 13/13")


if __name__ == "__main__":
    main()
