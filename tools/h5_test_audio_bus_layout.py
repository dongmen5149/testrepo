#!/usr/bin/env python3
"""R101: Audio bus layout — Master 단일 → Master + BGM + SFX 3 bus (E +0.2%p).

R97-R99 의 audio 정밀 후속 — 모든 player 가 Master 단일 bus 에 묶여 있어
독립 dB / mute 제어 불가능했고, `player.volume_db` 만 변경하는 방식이라
`_fade_swap` 등에서 reset 위험 존재. R101 = default_bus_layout.tres 신규로
BGM/SFX bus 를 Master 의 child 로 분리, AudioServer.set_bus_volume_db /
set_bus_mute 로 깨끗한 bus-level 관리.

검증:
- default_bus_layout.tres 신규 + Master/BGM/SFX 3 bus 정의 + BGM/SFX 가
  Master 로 send.
- project.godot 의 [audio] 섹션에 buses/default_bus_layout 설정.
- audio_manager.gd 의 BGM_BUS_NAME / SFX_BUS_NAME 상수.
- _ready 에서 AudioServer.get_bus_index 호출 + bus 미적용 fallback.
- set_bgm/sfx_volume 이 AudioServer.set_bus_volume_db 사용 (bus 적용 시).
- set_muted 이 AudioServer.set_bus_mute 사용 (bus 적용 시).
- play_bgm/sfx 가 bus 적용 시 player.volume_db = 0 (bus 가 dB 관리).
- _fade_swap 의 fade-in target 이 bus 적용 시 0.0 (player 상대).
- R91-R99 회귀 (외부 API 호환 유지).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    bus_path = GODOT / "default_bus_layout.tres"
    proj_path = GODOT / "project.godot"
    am_path = GODOT / "scripts/core/audio_manager.gd"

    # 1. default_bus_layout.tres 존재 + 3 bus
    assert bus_path.exists(), "default_bus_layout.tres 누락"
    bus = bus_path.read_text(encoding='utf-8')
    assert '[gd_resource type="AudioBusLayout"' in bus, "AudioBusLayout 리소스 타입 누락"
    assert 'bus/0/name = &"Master"' in bus, "Master bus 누락"
    assert 'bus/1/name = &"BGM"' in bus, "BGM bus 누락"
    assert 'bus/2/name = &"SFX"' in bus, "SFX bus 누락"
    print("[PASS] default_bus_layout.tres: 3 bus (Master / BGM / SFX) 정의")

    # 2. BGM/SFX 가 Master 로 send
    assert 'bus/1/send = &"Master"' in bus, "BGM bus 의 Master send 누락"
    assert 'bus/2/send = &"Master"' in bus, "SFX bus 의 Master send 누락"
    # 초기 dB (BGM -6, SFX -3) 보존
    assert "bus/1/volume_db = -6.0" in bus, "BGM 초기 dB -6 누락"
    assert "bus/2/volume_db = -3.0" in bus, "SFX 초기 dB -3 누락"
    print("[PASS] default_bus_layout.tres: BGM/SFX → Master send + 초기 dB (-6/-3) 보존")

    # 3. project.godot 의 audio 섹션
    proj = proj_path.read_text(encoding='utf-8')
    assert "[audio]" in proj, "project.godot [audio] 섹션 누락"
    assert 'buses/default_bus_layout="res://default_bus_layout.tres"' in proj, \
        "buses/default_bus_layout 설정 누락"
    print("[PASS] project.godot: [audio] buses/default_bus_layout 설정")

    # 4. audio_manager.gd 의 bus name 상수
    am = am_path.read_text(encoding='utf-8')
    assert 'const BGM_BUS_NAME := "BGM"' in am, "BGM_BUS_NAME 상수 누락"
    assert 'const SFX_BUS_NAME := "SFX"' in am, "SFX_BUS_NAME 상수 누락"
    print("[PASS] audio_manager.gd: BGM_BUS_NAME / SFX_BUS_NAME 상수")

    # 5. _ready 에서 bus index lookup + fallback
    ready_section = am[am.find("func _ready"):am.find("\n\n@export", am.find("func _ready"))]
    assert "AudioServer.get_bus_index(BGM_BUS_NAME)" in ready_section, \
        "_ready 의 BGM bus index lookup 누락"
    assert "AudioServer.get_bus_index(SFX_BUS_NAME)" in ready_section, \
        "_ready 의 SFX bus index lookup 누락"
    assert "_bgm_bus_idx >= 0 else \"Master\"" in ready_section, \
        "_ready 의 BGM fallback (Master) 누락"
    assert "_sfx_bus_idx >= 0 else \"Master\"" in ready_section, \
        "_ready 의 SFX fallback 누락"
    print("[PASS] audio_manager._ready: AudioServer.get_bus_index + Master fallback")

    # 6. set_bgm/sfx_volume 이 AudioServer.set_bus_volume_db 사용
    set_bgm = am[am.find("func set_bgm_volume"):am.find("\n\n", am.find("func set_bgm_volume"))]
    set_sfx = am[am.find("func set_sfx_volume"):am.find("\n\n", am.find("func set_sfx_volume"))]
    assert "AudioServer.set_bus_volume_db(_bgm_bus_idx, _bgm_target_db)" in set_bgm, \
        "set_bgm_volume 의 bus-level 적용 누락"
    assert "AudioServer.set_bus_volume_db(_sfx_bus_idx, _sfx_target_db)" in set_sfx, \
        "set_sfx_volume 의 bus-level 적용 누락"
    # fallback 도 유지
    assert "elif _bgm and not _muted" in set_bgm, "set_bgm_volume fallback 누락"
    print("[PASS] audio_manager.set_X_volume: AudioServer.set_bus_volume_db + fallback")

    # 7. set_muted 이 AudioServer.set_bus_mute 사용
    set_muted = am[am.find("func set_muted"):am.find("\n\n", am.find("func set_muted"))]
    assert "AudioServer.set_bus_mute(_bgm_bus_idx, _muted)" in set_muted, \
        "set_muted 의 BGM bus mute 누락"
    assert "AudioServer.set_bus_mute(_sfx_bus_idx, _muted)" in set_muted, \
        "set_muted 의 SFX bus mute 누락"
    print("[PASS] audio_manager.set_muted: AudioServer.set_bus_mute (BGM + SFX bus)")

    # 8. play_bgm 의 player.volume_db = 0 (bus 적용 시)
    play_bgm = am[am.find("func play_bgm"):am.find("\n\n## ", am.find("func play_bgm"))]
    assert "0.0 if _bgm_bus_idx >= 0 else _bgm_target_db" in play_bgm, \
        "play_bgm 의 bus 적용 시 player.volume_db = 0 누락"
    print("[PASS] audio_manager.play_bgm: bus 적용 시 player.volume_db = 0 (bus 가 dB 관리)")

    # 9. play_sfx 의 player.volume_db = 0 (bus 적용 시)
    play_sfx = am[am.find("func play_sfx"):]
    assert "0.0 if _sfx_bus_idx >= 0" in play_sfx, \
        "play_sfx 의 bus 적용 시 player.volume_db = 0 누락"
    print("[PASS] audio_manager.play_sfx: bus 적용 시 player.volume_db = 0")

    # 10. _fade_swap 의 fade-in target 이 bus 적용 시 0.0
    fade_swap = am[am.find("func _fade_swap"):am.find("\n\nfunc ", am.find("func _fade_swap"))]
    assert "0.0 if _bgm_bus_idx >= 0 else _bgm_target_db" in fade_swap, \
        "_fade_swap 의 fade-in target = 0 (bus 적용 시) 누락"
    assert "fade_out_target := -40.0" in fade_swap, "_fade_swap fade_out_target 누락"
    print("[PASS] audio_manager._fade_swap: fade-in/out target = bus-aware (0 vs target_db)")

    # 11. R99 회귀
    sp = read("scripts/ui/settings_panel.gd")
    assert "func sync_mute_check(state: bool)" in sp
    print("[PASS] R99 회귀: sync_mute_check")

    # 12. R98 회귀
    for fn in ["func is_muted()", "func set_muted(", "func toggle_mute()"]:
        assert fn in am, f"R98 mute API 손실: {fn!r}"
    print("[PASS] R98 회귀: AudioManager mute 3 API")

    # 13. R97 회귀
    assert "static func slider_to_db(v: float) -> float:" in am
    assert "linear_to_db(clampf(v, 0.0, 100.0) / 100.0)" in am
    print("[PASS] R97 회귀: slider_to_db linear_to_db")

    # 14. R96 회귀 (Toast 마이그레이션)
    demo = read("scripts/ui/demo.gd")
    assert demo.count('preload("res://scripts/ui/toast.gd").show_msg(') == 0
    print("[PASS] R96 회귀: Toast 마이그레이션")

    # 15. R91 회귀
    gs = read("scripts/core/game_state.gd")
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: save round-trip")

    # 16. R101 docstring marker
    assert "Round 101" in am, "R101 docstring marker 누락 (audio_manager)"
    print("[PASS] R101 docstring marker (audio_manager)")

    print("\n[R101 ALL PASSED] 16/16")


if __name__ == "__main__":
    main()
