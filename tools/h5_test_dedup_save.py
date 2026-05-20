#!/usr/bin/env python3
"""R104: SettingsPanel _on_mute_toggled 의 중복 _save_config 제거 (E +0.05%p).

R103 의 mute_changed 단일 핸들러 중앙화 후속. R99 시점 `_on_mute_toggled` 가
`Audio.set_muted(on) + _save_config()` 둘 다 호출했고, R103 부터는 set_muted
→ mute_changed.emit → demo._on_audio_mute_changed → _settings._save_config()
signal chain 이 자동 저장. _on_mute_toggled 의 inline _save_config 는 중복.

R104 = inline _save_config 제거 → 단일 source of truth (signal chain 이 유일
save 경로). _on_mute_toggled 가 set_muted 만 호출.

검증:
- settings_panel._on_mute_toggled 가 _save_config 호출 안 함 (Audio.set_muted 만).
- demo._on_audio_mute_changed 의 _save_config 호출 잔존 (signal chain 보존).
- 사용자가 MuteCheck 토글 → _on_mute_toggled → set_muted → mute_changed →
  demo handler → save 단일 경로 검증.
- R98-R103 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    sp = read("scripts/ui/settings_panel.gd")
    demo = read("scripts/ui/demo.gd")
    am = read("scripts/core/audio_manager.gd")
    hud = read("scripts/ui/hud.gd")

    # 1. _on_mute_toggled 의 _save_config inline 제거
    handler = sp[sp.find("func _on_mute_toggled"):sp.find("\n\n\nfunc ", sp.find("func _on_mute_toggled"))]
    assert "Audio.set_muted(on)" in handler, "_on_mute_toggled 의 set_muted 호출 누락"
    assert "_save_config()" not in handler, \
        "_on_mute_toggled 의 inline _save_config 잔존 (R104 미정리)"
    print("[PASS] settings_panel._on_mute_toggled: set_muted 만 호출, 중복 _save_config 제거")

    # 2. demo._on_audio_mute_changed 의 _save_config 잔존 (signal chain)
    demo_handler = demo[demo.find("func _on_audio_mute_changed"):demo.find("\nfunc _input")]
    assert "_settings._save_config()" in demo_handler, \
        "demo._on_audio_mute_changed 의 _save_config 누락 (signal chain save 깨짐)"
    assert "_settings.sync_mute_check(muted)" in demo_handler, \
        "demo._on_audio_mute_changed 의 sync_mute_check 누락"
    print("[PASS] demo._on_audio_mute_changed: signal chain 의 _save_config + sync_mute_check 잔존")

    # 3. 다른 _save_config 호출 경로 (volume slider) 잔존
    bgm_handler = sp[sp.find("func _on_bgm_volume"):sp.find("\n\n", sp.find("func _on_bgm_volume"))]
    sfx_handler = sp[sp.find("func _on_sfx_volume"):sp.find("\n\n", sp.find("func _on_sfx_volume"))]
    assert "_save_config()" in bgm_handler, "BGM 슬라이더의 _save_config 손실"
    assert "_save_config()" in sfx_handler, "SFX 슬라이더의 _save_config 손실"
    print("[PASS] settings_panel: BGM/SFX 슬라이더의 _save_config 잔존 (변경 영향 없음)")

    # 4. fps_check / fullscreen_check 의 _save_config 잔존
    assert "_show_fps = on; fps_label.visible = on; _save_config()" in sp, \
        "FPSCheck handler 의 _save_config 손실"
    fs_handler = sp[sp.find("func _on_fullscreen"):sp.find("\n\n", sp.find("func _on_fullscreen"))]
    assert "_save_config()" in fs_handler, "Fullscreen handler 의 _save_config 손실"
    print("[PASS] settings_panel: FPS/Fullscreen handler 의 _save_config 잔존")

    # 5. R103 회귀: demo mute_changed signal 연결 + handler
    assert "Audio.mute_changed.connect(_on_audio_mute_changed)" in demo
    print("[PASS] R103 회귀: demo Audio.mute_changed 연결")

    # 6. R103 회귀: HUD AudioIndicator gui_input
    assert "audio_indicator.gui_input.connect(_on_audio_indicator_input)" in hud
    print("[PASS] R103 회귀: HUD gui_input 연결")

    # 7. R102 회귀: AudioManager mute_changed signal + changed 가드
    assert "signal mute_changed(muted: bool)" in am
    assert "var changed := (_muted != mute)" in am
    print("[PASS] R102 회귀: AudioManager signal + changed 가드")

    # 8. R99 회귀: sync_mute_check
    assert "func sync_mute_check(state: bool)" in sp
    print("[PASS] R99 회귀: sync_mute_check")

    # 9. R98 회귀: mute 3 API
    for fn in ["func is_muted()", "func set_muted(", "func toggle_mute()"]:
        assert fn in am
    print("[PASS] R98 회귀: AudioManager mute 3 API")

    # 10. Python 시뮬: MuteCheck 클릭 시 save 경로
    # _on_mute_toggled → Audio.set_muted → mute_changed.emit → demo handler →
    # sync_mute_check (silent) + _save_config + Toast
    log = []
    state = {"muted": False, "saved_count": 0}
    def audio_set_muted(mute):
        changed = state["muted"] != mute
        state["muted"] = mute
        if changed:
            demo_on_audio_mute_changed(mute)
    def demo_on_audio_mute_changed(muted):
        log.append("sync_mute_check")
        log.append("save_config")
        state["saved_count"] += 1
        log.append("toast")
    def settings_on_mute_toggled(on):
        log.append("on_mute_toggled enter")
        audio_set_muted(on)
        log.append("on_mute_toggled exit")

    settings_on_mute_toggled(True)
    # 기대: enter → sync + save + toast (signal chain) → exit
    assert log == ["on_mute_toggled enter", "sync_mute_check", "save_config", "toast",
                    "on_mute_toggled exit"], f"signal chain 순서 시뮬 실패: {log}"
    assert state["saved_count"] == 1, f"중복 save 발생: {state['saved_count']}"
    print(f"[PASS] Python 시뮬: MuteCheck 클릭 → 단일 save (signal chain, 중복 없음)")

    # 11. 같은 값 재토글 (cycle 방지) 검증
    log.clear()
    settings_on_mute_toggled(True)  # 이미 muted=True 인데 다시 True
    assert state["saved_count"] == 1, "동일 값 재토글 시 save 가 추가로 발생 (changed 가드 깨짐)"
    print("[PASS] Python 시뮬: 동일 값 재토글 시 save 안 됨 (R102 changed 가드 효과)")

    # 12. R96 회귀
    assert demo.count('preload("res://scripts/ui/toast.gd").show_msg(') == 0
    print("[PASS] R96 회귀: Toast 마이그레이션")

    # 13. R91 회귀
    gs = (GODOT / "scripts/core/game_state.gd").read_text(encoding='utf-8')
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: save round-trip")

    # 14. R104 docstring marker
    assert "Round 104" in sp, "R104 docstring marker 누락 (settings_panel)"
    print("[PASS] R104 docstring marker (settings_panel)")

    print("\n[R104 ALL PASSED] 14/14")


if __name__ == "__main__":
    main()
