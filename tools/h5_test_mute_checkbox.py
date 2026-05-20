#!/usr/bin/env python3
"""R99: SettingsPanel mute 체크박스 UI (E +0.1%p).

R98 F8 토글의 자연스러운 후속. R98 시점 사용자가 음소거 상태를 시각적으로
확인하려면 F8 직후 Toast 메시지만 보였고, SettingsPanel 을 열어도 BGM/SFX
슬라이더만 있어 mute 여부 불명. R99 = settings_panel.tscn 에 MuteCheck
체크박스 추가 + 양방향 동기화 (F8 ↔ 체크박스).

검증:
- settings_panel.tscn 에 MuteCheck CheckBox 노드 신규 + 기존 노드 (FPS/
  Fullscreen/FPSLabel) 의 offset_top 재배치.
- settings_panel.gd:
  - @onready var mute_check 신규.
  - _ready 에서 mute_check.toggled → _on_mute_toggled 연결.
  - _load_config 후 mute_check.set_pressed_no_signal(muted) 초기화.
  - _on_mute_toggled(on): Audio.set_muted(on) + _save_config.
  - sync_mute_check(state) helper (F8 외부 호출 시 silent update).
- demo.gd F8 핸들러: _settings.sync_mute_check(muted) 호출 추가.
- R98 회귀 (toggle_mute, Audio.set_muted, ConfigFile audio/muted).
- R91-R97 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    sp = read("scripts/ui/settings_panel.gd")
    tscn = read("scenes/settings_panel.tscn")
    demo = read("scripts/ui/demo.gd")
    am = read("scripts/core/audio_manager.gd")
    hp = read("scripts/ui/help_panel.gd")
    toast = read("scripts/ui/toast.gd")
    title = read("scripts/ui/title.gd")
    slp = read("scripts/ui/save_list_panel.gd")
    gs = read("scripts/core/game_state.gd")

    # 1. tscn 에 MuteCheck 노드
    assert '[node name="MuteCheck" type="CheckBox" parent="BG"]' in tscn, \
        "settings_panel.tscn 의 MuteCheck 노드 누락"
    assert 'text = "음소거 (F8)"' in tscn, "MuteCheck 의 라벨 누락"
    print("[PASS] settings_panel.tscn: MuteCheck CheckBox 노드 + '음소거 (F8)' 라벨")

    # 2. MuteCheck 배치 후 FPSCheck / FullscreenCheck / FPSLabel 의 offset_top 재배치
    # 새 배치: MuteCheck=92, FPSCheck=120, FullscreenCheck=148, FPSLabel=180
    mute_section = tscn[tscn.find('"MuteCheck"'):tscn.find('"FPSCheck"')]
    assert "offset_top = 92.0" in mute_section, "MuteCheck offset_top 누락"
    fps_section = tscn[tscn.find('"FPSCheck"'):tscn.find('"FullscreenCheck"')]
    assert "offset_top = 120.0" in fps_section, "FPSCheck offset_top 재배치 누락"
    fullscreen_section = tscn[tscn.find('"FullscreenCheck"'):tscn.find('"FPSLabel"')]
    assert "offset_top = 148.0" in fullscreen_section, \
        "FullscreenCheck offset_top 재배치 누락"
    fps_label_section = tscn[tscn.find('"FPSLabel"'):tscn.find('"CloseButton"')]
    assert "offset_top = 180.0" in fps_label_section, "FPSLabel offset_top 재배치 누락"
    print("[PASS] settings_panel.tscn: MuteCheck=92 / FPSCheck=120 / Fullscreen=148 / FPSLabel=180")

    # 3. settings_panel.gd @onready var mute_check
    assert "@onready var mute_check: CheckBox = $BG/MuteCheck" in sp, \
        "@onready var mute_check 누락"
    print("[PASS] settings_panel.gd: @onready var mute_check 신규")

    # 4. _ready 의 mute_check.toggled 연결
    ready_section = sp[sp.find("func _ready"):sp.find("\n\n\nfunc ", sp.find("func _ready"))]
    assert "mute_check.toggled.connect(_on_mute_toggled)" in ready_section, \
        "mute_check.toggled signal 연결 누락"
    print("[PASS] settings_panel._ready: mute_check.toggled → _on_mute_toggled 연결")

    # 5. _load_config 후 mute_check 초기화 (signal 발화 없이)
    load_section = sp[sp.find("func _load_config"):sp.find("\n\n\nfunc ", sp.find("func _load_config"))]
    assert "mute_check.set_pressed_no_signal(muted)" in load_section, \
        "_load_config 의 mute_check 초기화 누락 (set_pressed_no_signal 사용)"
    print("[PASS] settings_panel._load_config: set_pressed_no_signal 로 체크박스 초기화 (signal 재발화 방지)")

    # 6. _on_mute_toggled handler. R99 시점: set_muted + _save_config inline.
    # R104+: set_muted 만 (save 는 demo 의 mute_changed signal chain 이 처리).
    assert "func _on_mute_toggled(on: bool) -> void:" in sp, \
        "_on_mute_toggled handler 누락"
    mute_handler = sp[sp.find("func _on_mute_toggled"):sp.find("\n\n\nfunc ", sp.find("func _on_mute_toggled"))]
    assert "Audio.set_muted(on)" in mute_handler, "_on_mute_toggled 가 set_muted 미호출"
    # _save_config 는 inline 또는 signal chain (demo._on_audio_mute_changed) 어느 쪽이든.
    demo = read("scripts/ui/demo.gd")
    has_chain_save = "func _on_audio_mute_changed(muted: bool)" in demo and \
                     "_settings._save_config()" in demo[demo.find("func _on_audio_mute_changed"):]
    has_inline_save = "_save_config()" in mute_handler
    assert has_chain_save or has_inline_save, \
        "_on_mute_toggled save 경로 누락 (inline 또는 mute_changed chain 어느 쪽이든)"
    print(f"[PASS] settings_panel._on_mute_toggled: Audio.set_muted + save ({'chain' if has_chain_save and not has_inline_save else 'inline'})")

    # 7. sync_mute_check public helper (F8 외부 호출자 동기화용)
    assert "func sync_mute_check(state: bool) -> void:" in sp, \
        "sync_mute_check helper 누락"
    sync_section = sp[sp.find("func sync_mute_check"):sp.find("\n\n", sp.find("func sync_mute_check"))]
    assert "mute_check.set_pressed_no_signal(state)" in sync_section, \
        "sync_mute_check 가 set_pressed_no_signal 사용 안 함"
    print("[PASS] settings_panel.sync_mute_check: F8 외부 호출자용 silent 동기화 helper")

    # 8. demo.gd 어딘가에서 sync_mute_check 가 호출되어야 함 (R99 시점 F8 inline,
    # R103+ 는 mute_changed signal 핸들러로 이전).
    assert "_settings.sync_mute_check(muted)" in demo, \
        "demo 의 sync_mute_check 호출 누락 (F8 inline 또는 signal 핸들러 어느 쪽이든)"
    print("[PASS] demo.gd: _settings.sync_mute_check(muted) 호출 (F8 inline 또는 signal 핸들러)")

    # 9. R98 회귀: AudioManager mute API
    for fn in ["func is_muted()", "func set_muted(", "func toggle_mute()"]:
        assert fn in am, f"R98 mute API 손실: {fn!r}"
    assert "var _muted: bool = false" in am
    # ConfigFile audio/muted key
    assert 'cfg.get_value("audio", "muted"' in sp
    assert 'cfg.set_value("audio", "muted", Audio.is_muted())' in sp
    print("[PASS] R98 회귀: AudioManager mute API + ConfigFile audio/muted")

    # 10. R97 회귀
    assert "static func slider_to_db(v: float) -> float:" in am
    print("[PASS] R97 회귀: slider_to_db")

    # 11. R96 회귀: Toast.severity 분포 (R98 에서 +1/+1 한 상태 유지)
    n_info = len(re.findall(r"\bToast\.info\(", demo))
    n_warn = len(re.findall(r"\bToast\.warn\(", demo))
    assert n_info >= 9, f"R98 후 Toast.info >= 9 기대: {n_info}"
    assert n_warn >= 3, f"R98 후 Toast.warn >= 3 기대: {n_warn}"
    print(f"[PASS] R96/R98 회귀: Toast 분포 info={n_info} warn={n_warn}")

    # 12. R95 회귀
    assert "enum Severity { INFO, SUCCESS, WARN, ERROR }" in toast
    print("[PASS] R95 회귀: Severity enum")

    # 13. R94 회귀: HELP_TEXT F8
    m = re.search(r'const HELP_TEXT := """(.*?)"""', hp, re.DOTALL)
    help_text = m.group(1)
    assert "F8" in help_text
    print("[PASS] R94 회귀: HelpPanel F8")

    # 14. R93 / R92 / R91 회귀
    assert "_save_list.slot_loaded.connect(_on_slot_loaded)" in title
    assert "signal slot_loaded(slot: int)" in slp
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R93/R92/R91 회귀")

    # 15. R99 docstring marker
    assert "Round 99" in sp, "R99 docstring marker 누락 (settings_panel)"
    print("[PASS] R99 docstring marker (settings_panel)")

    print("\n[R99 ALL PASSED] 15/15")


if __name__ == "__main__":
    main()
