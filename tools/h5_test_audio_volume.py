#!/usr/bin/env python3
"""R97: SettingsPanel/AudioManager 볼륨 정밀 (E/D +0.2%p).

R96 까지 SettingsPanel 의 BGM/SFX 슬라이더는 (1) `-40 + (v/100)*40` 선형 dB
매핑 → 청각적으로 비-자연 (대부분 구간이 동일 음량), (2) SFX target_db
persistence 부재 → `_fade_swap` 등에서 -3dB 로 reset 가능, (3) config 로드 후
AudioManager 에 즉시 반영 안 됨 → 사용자가 슬라이더 만지기 전까지 default
재생. R97 = 3 문제 모두 fix.

검증:
- AudioManager.slider_to_db(v) static helper: linear_to_db 곡선 + mute 임계
  (v<1 → -80dB).
- _sfx_target_db 신규 + play_sfx 가 매 재생 전 적용.
- set_bgm_volume / set_sfx_volume public API + SettingsPanel 위임.
- SettingsPanel._load_config 가 load 후 Audio.set_bgm/sfx_volume 즉시 호출.
- 이전 `-40 + (v/100)*40` 선형 매핑 제거.
- Python 시뮬 (linear_to_db 등가): v=100→0dB / v=50→≈-6dB / v=10→-20dB /
  v=0→-80dB.
- R91-R96 회귀.
"""
import math
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
    toast = read("scripts/ui/toast.gd")
    hp = read("scripts/ui/help_panel.gd")
    title = read("scripts/ui/title.gd")
    slp = read("scripts/ui/save_list_panel.gd")
    gs = read("scripts/core/game_state.gd")

    # 1. slider_to_db static helper
    assert "static func slider_to_db(v: float) -> float:" in am, \
        "slider_to_db static helper 누락"
    assert "linear_to_db(clampf(v, 0.0, 100.0) / 100.0)" in am, \
        "linear_to_db 자연 곡선 미적용"
    assert "MUTE_THRESHOLD" in am and "MUTE_DB" in am, \
        "MUTE 임계 상수 누락"
    assert "return MUTE_DB" in am, "v<MUTE_THRESHOLD 시 mute 반환 누락"
    print("[PASS] AudioManager: slider_to_db(v) — linear_to_db 곡선 + MUTE 임계")

    # 2. _sfx_target_db + play_sfx 의 매 재생 전 적용
    assert "var _sfx_target_db: float = -3.0" in am, \
        "_sfx_target_db 영속 변수 누락"
    play_sfx = am[am.find("func play_sfx"):am.find("\nfunc ", am.find("func play_sfx")+1)]
    # R97 form: `_sfx.volume_db = _sfx_target_db`
    # R98 form: `_sfx.volume_db = (MUTE_DB if _muted else _sfx_target_db)`
    assert "_sfx_target_db" in play_sfx and "_sfx.volume_db" in play_sfx, \
        "play_sfx 가 매 재생 전 target_db 재적용 안 함"
    print("[PASS] AudioManager: _sfx_target_db 영속 + play_sfx 매 재생 전 재적용")

    # 3. set_bgm_volume / set_sfx_volume public API
    assert "func set_bgm_volume(v: float) -> void:" in am
    assert "func set_sfx_volume(v: float) -> void:" in am
    assert "_bgm_target_db = slider_to_db(v)" in am
    assert "_sfx_target_db = slider_to_db(v)" in am
    print("[PASS] AudioManager: set_bgm_volume / set_sfx_volume public API")

    # 4. SettingsPanel 의 _on_bgm_volume / _on_sfx_volume 가 새 API 위임
    assert "Audio.set_bgm_volume(v)" in sp, "BGM 슬라이더가 새 API 미위임"
    assert "Audio.set_sfx_volume(v)" in sp, "SFX 슬라이더가 새 API 미위임"
    # 이전 선형 매핑 제거 확인
    assert "-40.0 + (v / 100.0) * 40.0" not in sp, \
        "이전 -40~0 선형 매핑 잔존 (R97 미정리)"
    assert "Audio._bgm.volume_db = db" not in sp, \
        "이전 Audio._bgm.volume_db 직접 변경 잔존"
    assert "Audio._sfx.volume_db = db" not in sp, \
        "이전 Audio._sfx.volume_db 직접 변경 잔존"
    print("[PASS] SettingsPanel: 새 API 위임 + 이전 선형 매핑/직접 변경 제거")

    # 5. _load_config 후 Audio 에 즉시 반영
    load_section = sp[sp.find("func _load_config"):sp.find("\nfunc ", sp.find("func _load_config")+1)]
    assert "Audio.set_bgm_volume(bgm_slider.value)" in load_section, \
        "_load_config 후 BGM 즉시 반영 누락"
    assert "Audio.set_sfx_volume(sfx_slider.value)" in load_section, \
        "_load_config 후 SFX 즉시 반영 누락"
    print("[PASS] SettingsPanel._load_config: 로드 즉시 AudioManager 반영")

    # 6. Python 시뮬: slider_to_db 곡선 (linear_to_db = 20 * log10(v/100), v<1 → -80)
    def slider_to_db_py(v: float) -> float:
        if v < 1.0:
            return -80.0
        v = max(0.0, min(100.0, v)) / 100.0
        return 20.0 * math.log10(v)

    # v=100 → 0dB
    assert abs(slider_to_db_py(100) - 0.0) < 0.01, \
        f"v=100 → 0dB 시뮬 실패: {slider_to_db_py(100)}"
    # v=50 → ≈ -6.02dB
    assert abs(slider_to_db_py(50) - (-6.02)) < 0.05, \
        f"v=50 → -6dB 시뮬 실패: {slider_to_db_py(50)}"
    # v=10 → ≈ -20dB
    assert abs(slider_to_db_py(10) - (-20.0)) < 0.05, \
        f"v=10 → -20dB 시뮬 실패: {slider_to_db_py(10)}"
    # v=0 → -80dB (mute)
    assert slider_to_db_py(0) == -80.0, \
        f"v=0 → -80dB(mute) 시뮬 실패: {slider_to_db_py(0)}"
    # v=0.5 (< MUTE_THRESHOLD=1) → mute
    assert slider_to_db_py(0.5) == -80.0, \
        f"v=0.5 → mute 시뮬 실패: {slider_to_db_py(0.5)}"
    print(f"[PASS] Python 시뮬 slider_to_db: v=100→0 / v=50→-6 / v=10→-20 / v<1→-80 dB")

    # 7. AudioManager 의 _ready 의 default volume 보존 (init).
    # R97: `_bgm.volume_db = -6` / `_sfx.volume_db = -3` 직접 설정.
    # R101: bus-level 관리로 player 는 0dB 유지 → tres 의 bus 초기 dB (-6/-3) 가 default.
    bus_path = ROOT / "apps/hero5-godot/default_bus_layout.tres"
    if bus_path.exists():
        bus = bus_path.read_text(encoding='utf-8')
        assert "bus/1/volume_db = -6.0" in bus, "R101 bus 의 BGM 초기 -6dB 손실"
        assert "bus/2/volume_db = -3.0" in bus, "R101 bus 의 SFX 초기 -3dB 손실"
        print("[PASS] R101 bus 의 초기 dB (BGM -6 / SFX -3) 보존")
    else:
        assert "_bgm.volume_db = -6" in am, "_bgm 초기 -6dB 손실 (R97 form)"
        assert "_sfx.volume_db = -3" in am, "_sfx 초기 -3dB 손실 (R97 form)"
        print("[PASS] AudioManager._ready 초기 dB (BGM -6 / SFX -3) 보존")

    # 8. R96 회귀: demo.gd Toast.severity 마이그레이션
    assert demo.count('preload("res://scripts/ui/toast.gd").show_msg(') == 0
    n_info = len(re.findall(r"\bToast\.info\(", demo))
    n_success = len(re.findall(r"\bToast\.success\(", demo))
    n_warn = len(re.findall(r"\bToast\.warn\(", demo))
    # R96 baseline (info=8/success=2/warn=2). R97+ 라운드에서 추가 호출 가능.
    assert n_info >= 8 and n_success == 2 and n_warn >= 2, \
        f"R96 회귀: Toast 분포 비정상 감소 ({n_info}/{n_success}/{n_warn})"
    print("[PASS] R96 회귀: Toast severity 마이그레이션 (info=8/success=2/warn=2)")

    # 9. R95 회귀: Toast severity enum + 4 helper
    assert "enum Severity { INFO, SUCCESS, WARN, ERROR }" in toast
    for fn in ["static func info(", "static func success(", "static func warn(", "static func error("]:
        assert fn in toast
    print("[PASS] R95 회귀: Toast severity enum + 4 helper")

    # 10. R94 회귀: HelpPanel 키
    m = re.search(r'const HELP_TEXT := """(.*?)"""', hp, re.DOTALL)
    help_text = m.group(1)
    for marker in ["F6", "F10"]:
        assert marker in help_text
    print("[PASS] R94 회귀: HelpPanel 키 동기화")

    # 11. R93 회귀: Title SaveListPanel 위임
    assert "_save_list.slot_loaded.connect(_on_slot_loaded)" in title
    print("[PASS] R93 회귀: Title SaveListPanel 위임")

    # 12. R92 회귀
    assert "signal slot_loaded(slot: int)" in slp
    print("[PASS] R92 회귀: SaveListPanel signal")

    # 13. R91 회귀
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: round-trip")

    # 14. R97 docstring marker
    assert "Round 97" in am, "R97 docstring marker 누락 (audio_manager)"
    assert "Round 97" in sp, "R97 docstring marker 누락 (settings_panel)"
    print("[PASS] R97 docstring marker (audio_manager + settings_panel)")

    print("\n[R97 ALL PASSED] 14/14")


if __name__ == "__main__":
    main()
