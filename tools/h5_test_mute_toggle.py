#!/usr/bin/env python3
"""R98: Mute 토글 F8 + ConfigFile 영속성 (E/H +0.2%p).

R97 의 AudioManager 정밀 후속. 사용자가 음소거를 원할 때 (1) 슬라이더를 0
으로 끌고 가야 했고 (2) 다음 실행 시 default 70/80 으로 reset. R98 = F8 키
또는 SettingsPanel 의 mute 상태 영속화로 즉시 토글 가능.

검증:
- AudioManager: `_muted: bool`, `is_muted()`, `set_muted(mute)`,
  `toggle_mute()` 4 API 신규.
- set_muted 가 BGM + SFX volume_db 를 MUTE_DB / target_db 사이 전환.
- play_sfx 가 _muted 시 MUTE_DB 적용.
- set_bgm/sfx_volume 이 _muted 시 volume_db 적용 안 함 (mute 유지).
- SettingsPanel: ConfigFile 의 "audio/muted" 키 read/write 추가.
- _load_config 가 Audio.set_muted(muted) 즉시 호출.
- demo.gd F8 키 바인딩 + Audio.toggle_mute() + Toast warn/info 발화 +
  SettingsPanel 의 _save_config 호출 (영속).
- HelpPanel HELP_TEXT 에 F8 명시.
- R91-R97 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    am = read("scripts/core/audio_manager.gd")
    sp = read("scripts/ui/settings_panel.gd")
    demo = read("scripts/ui/demo.gd")
    hp = read("scripts/ui/help_panel.gd")
    toast = read("scripts/ui/toast.gd")
    title = read("scripts/ui/title.gd")
    slp = read("scripts/ui/save_list_panel.gd")
    gs = read("scripts/core/game_state.gd")

    # 1. AudioManager mute API
    assert "var _muted: bool = false" in am, "_muted 상태 변수 누락"
    assert "func is_muted() -> bool:" in am, "is_muted 누락"
    assert "func set_muted(mute: bool) -> void:" in am, "set_muted 누락"
    assert "func toggle_mute() -> bool:" in am, "toggle_mute 누락"
    print("[PASS] AudioManager: _muted + is_muted + set_muted + toggle_mute API")

    # 2. set_muted 의 BGM + SFX 전환
    set_muted_section = am[am.find("func set_muted"):am.find("\n\n", am.find("func set_muted"))]
    assert "MUTE_DB if _muted else _bgm_target_db" in set_muted_section, \
        "set_muted BGM 전환 누락"
    assert "MUTE_DB if _muted else _sfx_target_db" in set_muted_section, \
        "set_muted SFX 전환 누락"
    print("[PASS] AudioManager.set_muted: BGM + SFX volume_db 전환 (MUTE_DB vs target_db)")

    # 3. play_sfx 의 _muted 분기
    play_sfx = am[am.find("func play_sfx"):am.find("\nfunc ", am.find("func play_sfx")+1)]
    assert "MUTE_DB if _muted else _sfx_target_db" in play_sfx, \
        "play_sfx 의 _muted 분기 누락"
    print("[PASS] AudioManager.play_sfx: _muted 시 MUTE_DB 적용")

    # 4. set_bgm/sfx_volume 이 _muted 일 때 volume_db 적용 안 함
    set_bgm_vol = am[am.find("func set_bgm_volume"):am.find("\n\n", am.find("func set_bgm_volume"))]
    set_sfx_vol = am[am.find("func set_sfx_volume"):am.find("\n\n", am.find("func set_sfx_volume"))]
    assert "not _muted" in set_bgm_vol, "set_bgm_volume 의 _muted 가드 누락"
    assert "not _muted" in set_sfx_vol, "set_sfx_volume 의 _muted 가드 누락"
    print("[PASS] AudioManager.set_X_volume: _muted 시 즉시 volume_db 변경 차단 (mute 유지)")

    # 5. SettingsPanel ConfigFile audio/muted key
    assert 'cfg.get_value("audio", "muted"' in sp, \
        "_load_config: audio/muted 읽기 누락"
    assert 'cfg.set_value("audio", "muted", Audio.is_muted())' in sp, \
        "_save_config: audio/muted 저장 누락"
    assert "Audio.set_muted(muted)" in sp, \
        "_load_config: AudioManager 즉시 반영 누락"
    print("[PASS] SettingsPanel: audio/muted ConfigFile read/write + 즉시 반영")

    # 6. demo.gd F8 키 바인딩. R98 시점: F8 핸들러에 toggle_mute + sync +
    # save + Toast 직접 포함. R103+ 시점: F8 = Audio.toggle_mute() 만, 나머지
    # 동작은 Audio.mute_changed signal 핸들러 (_on_audio_mute_changed) 로 이전.
    # 회귀 의도는 "F8 토글 시 sync + save + Toast 가 어딘가에서 일어남" 보장.
    assert "KEY_F8:" in demo, "demo.gd F8 키 바인딩 누락"
    f8_idx = demo.find("KEY_F8:")
    f8_section = demo[f8_idx:f8_idx + 600]
    assert "Audio.toggle_mute()" in f8_section, "F8 의 toggle_mute 누락"
    # sync + save + Toast 는 F8 자체 또는 signal 핸들러 어느 쪽이든 존재해야 함.
    has_handler = "func _on_audio_mute_changed(muted: bool)" in demo
    if has_handler:
        handler_idx = demo.find("func _on_audio_mute_changed")
        handler_section = demo[handler_idx:demo.find("\nfunc ", handler_idx + 1)]
        for marker in ["_settings.sync_mute_check(muted)", "_settings._save_config()",
                        "Toast.warn(self,", "Toast.info(self,"]:
            assert marker in handler_section, f"signal 핸들러 누락: {marker!r}"
        print("[PASS] demo.gd F8 (R103+): toggle_mute 만 호출, sync/save/Toast 는 mute_changed signal 핸들러로 이전")
    else:
        for marker in ["_settings.sync_mute_check(", "_settings._save_config()",
                        "Toast.warn(self,", "Toast.info(self,"]:
            assert marker in f8_section, f"F8 핸들러 누락: {marker!r}"
        print("[PASS] demo.gd F8 (R98 form): Audio.toggle_mute + sync + save + Toast inline")

    # 7. HelpPanel F8 명시
    m = re.search(r'const HELP_TEXT := """(.*?)"""', hp, re.DOTALL)
    help_text = m.group(1)
    assert "F8" in help_text, "HELP_TEXT 에 F8 음소거 토글 명시 누락"
    assert "음소거" in help_text, "HELP_TEXT 음소거 설명 누락"
    print("[PASS] HelpPanel: F8 음소거 토글 명시")

    # 8. mute 토글 의미 시뮬 (Python)
    state = {"muted": False, "bgm_db": -6.0, "sfx_db": -3.0}
    MUTE_DB = -80.0
    def toggle():
        state["muted"] = not state["muted"]
        if state["muted"]:
            state["actual_bgm"] = MUTE_DB
            state["actual_sfx"] = MUTE_DB
        else:
            state["actual_bgm"] = state["bgm_db"]
            state["actual_sfx"] = state["sfx_db"]
        return state["muted"]
    assert toggle() == True  # off → on
    assert state["actual_bgm"] == -80.0 and state["actual_sfx"] == -80.0
    assert toggle() == False  # on → off
    assert state["actual_bgm"] == -6.0 and state["actual_sfx"] == -3.0
    assert toggle() == True   # off → on (3rd toggle)
    print("[PASS] Python 시뮬 토글: off→on (BGM/SFX -80dB) → off (복원) → on (반복)")

    # 9. R97 회귀: slider_to_db + linear_to_db
    assert "static func slider_to_db(v: float) -> float:" in am
    assert "linear_to_db(clampf(v, 0.0, 100.0) / 100.0)" in am
    assert "Audio.set_bgm_volume(v)" in sp
    print("[PASS] R97 회귀: slider_to_db + linear_to_db + Audio.set_X_volume API")

    # 10. R96 회귀: Toast severity
    assert demo.count('preload("res://scripts/ui/toast.gd").show_msg(') == 0
    n_info = len(re.findall(r"\bToast\.info\(", demo))
    n_warn = len(re.findall(r"\bToast\.warn\(", demo))
    # R98 에서 mute on/off 시 각각 Toast.warn / Toast.info 추가 → 분포 +1 / +1.
    # R96 기준 info=8, warn=2 → R98 후 info=9, warn=3.
    assert n_info == 9, f"R98 후 info 호출 != 9 (R96 8 + F8 mute off 1): {n_info}"
    assert n_warn == 3, f"R98 후 warn 호출 != 3 (R96 2 + F8 mute on 1): {n_warn}"
    print(f"[PASS] R96 회귀 + R98 추가: info={n_info} warn={n_warn} (각 +1 from F8)")

    # 11. R95 회귀: Toast enum + helper
    assert "enum Severity { INFO, SUCCESS, WARN, ERROR }" in toast
    print("[PASS] R95 회귀: Toast Severity enum")

    # 12. R94 회귀: HelpPanel 기존 키 (F6 + F10)
    for marker in ["F6", "F10"]:
        assert marker in help_text
    print("[PASS] R94 회귀: HelpPanel 기존 키 (F6/F10) 잔존")

    # 13. R93 회귀
    assert "_save_list.slot_loaded.connect(_on_slot_loaded)" in title
    print("[PASS] R93 회귀: Title SaveListPanel 위임")

    # 14. R92 + R91 회귀
    assert "signal slot_loaded(slot: int)" in slp
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R92/R91 회귀")

    # 15. R98 docstring marker
    assert "Round 98" in am, "R98 docstring marker 누락 (audio_manager)"
    print("[PASS] R98 docstring marker (audio_manager)")

    print("\n[R98 ALL PASSED] 15/15")


if __name__ == "__main__":
    main()
