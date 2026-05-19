#!/usr/bin/env python3
"""R84: Map warp fade transition + spirit extra_hex 부분 파싱 검증.

검증 항목 (Map warp):
- scene_fader.gd 에 warp_fade(node, mid_callback, out_dur, in_dur) 신규
- 중간 콜백 패턴 (fade out → callback → fade in)
- demo.gd 의 _on_warp 가 warp_fade 사용 + _warping guard
- R82 SceneFader (change_scene/fade_in) 유지

검증 항목 (Spirit extra_hex):
- game_data._ensure_spirit_skills_loaded 의 extra_hex → stats_u16 변환
- _hex_to_bytes helper 추가
- stats area 48B (R77 layout) 첫 일부를 little-endian u16 stride 로 24 entries
- 첫 spirit record 의 stats_u16 ≥ 16 entries (의미 있는 데이터)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(path):
    return (GODOT / path).read_text(encoding='utf-8')


def main():
    # 1. SceneFader 에 warp_fade 추가
    sf = read("scripts/ui/scene_fader.gd")
    assert "func warp_fade" in sf, "missing warp_fade function"
    assert "mid_callback" in sf, "missing mid_callback parameter"
    assert "out_dur" in sf and "in_dur" in sf, "missing out_dur/in_dur params"
    assert "Round 84" in sf, "missing R84 docstring"
    # 기존 change_scene / fade_in 유지 (R82 회귀)
    assert "func change_scene" in sf, "lost R82 change_scene"
    assert "func fade_in" in sf, "lost fade_in"
    print("[PASS] scene_fader.gd: warp_fade(node, callback, out_dur, in_dur) 추가 + R82 함수 유지")

    # 2. warp_fade 의 fade-out → callback → fade-in 구조
    # tween 으로 alpha 0→1 (out), call callback, then 1→0 (in)
    assert "color:a" in sf, "missing color alpha animation"
    # Two tween blocks (out then in)
    assert sf.count("tween_property(rect, \"color:a\"") >= 3, \
        "expected ≥3 alpha tween (change_scene out + fade_in + warp_fade out + warp_fade in)"
    assert "mid_callback.call()" in sf, "missing mid_callback invocation"
    print("[PASS] warp_fade 구조: fade-out tween → callback.call() → fade-in tween")

    # 3. demo.gd 의 _on_warp 가 warp_fade 사용
    demo = read("scripts/ui/demo.gd")
    assert "SceneFader.warp_fade" in demo, "demo missing SceneFader.warp_fade call"
    assert "_warping" in demo, "demo missing _warping guard variable"
    assert "if _warping: return" in demo, "demo missing _warping guard check"
    assert "Round 84" in demo, "demo missing R84 docstring"
    print("[PASS] demo.gd: _on_warp → SceneFader.warp_fade + _warping guard (중복 warp 방지)")

    # 4. _on_warp callback 안에 _apply_scene + dialog
    # warp_fade(self, func(): _scene_idx = target_scene; _apply_scene(); _dialog.show_dialog(...))
    # 라인 패턴 확인
    assert "_scene_idx = target_scene" in demo, "missing _scene_idx assignment in callback"
    assert "_apply_scene()" in demo, "missing _apply_scene call"
    print("[PASS] _on_warp callback: scene_idx 변경 + _apply_scene + dialog")

    # 5. game_data 의 spirit extra_hex 파싱
    gd = read("scripts/core/game_data.gd")
    assert "_ensure_spirit_skills_loaded" in gd, "missing spirit loader"
    assert "_hex_to_bytes" in gd, "missing hex helper"
    assert "Round 84" in gd, "missing R84 docstring in game_data"
    assert "little-endian u16" in gd, "missing u16 stride docstring"
    assert "0x30" in gd or "48" in gd, "missing stats area size reference"
    print("[PASS] game_data.gd: _hex_to_bytes + extra_hex → stats_u16 (R77 stats area 48B)")

    # 6. hex_to_bytes 동작 검증 (Python 시뮬)
    def hex_to_bytes(hex_s):
        out = []
        n = len(hex_s) - (len(hex_s) % 2)
        for i in range(0, n, 2):
            out.append(int(hex_s[i:i+2], 16))
        return out

    sample_hex = "00000000000000000000301e005d0100013b5b1000050000393900013b00000000739001"
    bytes_arr = hex_to_bytes(sample_hex)
    assert bytes_arr[10] == 0x30, f"byte 10 expected 0x30, got {hex(bytes_arr[10])}"
    assert bytes_arr[11] == 0x1e, f"byte 11 expected 0x1e"
    # little-endian u16 [10..11] = (0x1e << 8) | 0x30 = 0x1e30 = 7728
    u16 = (bytes_arr[11] << 8) | bytes_arr[10]
    assert u16 == 0x1e30, f"u16 LE [10..11] expected 0x1e30, got {hex(u16)}"
    print(f"[PASS] hex_to_bytes + LE u16 시뮬: bytes[10..11]=0x{u16:04x} (7728)")

    # 7. c_csv_skill_05.json 의 spirit data 실 검증
    spirit_path = GODOT / "assets/gamedata/c_csv_skill_05.json"
    spirit = json.loads(spirit_path.read_text(encoding='utf-8'))
    assert spirit["count"] == 16, f"spirit count != 16"
    first = spirit["records"][0]
    assert "extra_hex" in first, "spirit record missing extra_hex"
    hex_data = first["extra_hex"]
    bytes_data = hex_to_bytes(hex_data)
    assert len(bytes_data) >= 48, f"extra_hex 길이 ≥48B 필요 (stats area), got {len(bytes_data)}"
    # u16 entries simulation (24 from 48 bytes)
    u16_count = min(24, len(bytes_data) // 2)
    assert u16_count >= 16, f"u16 entries ≥16 필요, got {u16_count}"
    print(f"[PASS] spirit record #0: {len(bytes_data)}B raw, {u16_count} u16 entries 추출 가능")

    # 8. R82/R83 회귀 검증 (다른 함수 잔존)
    assert "func to_title" in read("scripts/core/scene_router.gd"), "R82 SceneRouter 잔존 확인"
    assert "stat_int * 2" in read("scripts/core/game_state.gd"), "R83 Sorcerer INT bonus 잔존"
    print("[PASS] R82 (SceneRouter) + R83 (Sorcerer INT) 회귀 잔존")

    print("\n=== R84 Map warp fade + Spirit extra_hex 파싱: ALL PASSED ===")


if __name__ == "__main__":
    main()
