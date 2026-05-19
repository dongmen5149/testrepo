#!/usr/bin/env python3
"""R85: Battle UI start/end fade transition 검증 (E 카테고리 70→80%).

검증 항목:
- battle_ui.start() 가 SceneFader.warp_fade 로 fade-in
- battle 데이터 setup 이 mid-callback 으로 분리 (_setup_and_show)
- 이미 visible 시 중복 start 방지 (guard)
- _on_ended 가 fade-out → visible=false + cleanup → battle_completed.emit
- R82 (SceneRouter) / R84 (warp_fade) 회귀 유지
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(path):
    return (GODOT / path).read_text(encoding='utf-8')


def main():
    bu = read("scripts/ui/battle_ui.gd")

    # 1. SceneFader preload (CanvasLayer 라 autoload 못 받음 → preload)
    assert "preload(\"res://scripts/ui/scene_fader.gd\")" in bu, \
        "battle_ui missing SceneFader preload"
    assert "SceneFaderRef" in bu, "missing SceneFaderRef const"
    print("[PASS] battle_ui.gd: SceneFader preload 추가 (CanvasLayer 환경)")

    # 2. start() 가 warp_fade 사용 + 중복 진입 guard
    assert "if visible: return" in bu, "missing duplicate start guard"
    assert "SceneFaderRef.warp_fade" in bu, "start() missing warp_fade call"
    assert "_setup_and_show" in bu, "missing _setup_and_show mid-callback split"
    assert "Round 85" in bu, "missing R85 docstring"
    print("[PASS] start(): warp_fade(0.25, 0.25) + duplicate guard + _setup_and_show split")

    # 3. _setup_and_show 가 기존 setup logic 보유
    assert "GameState.in_combat = true" in bu, "missing in_combat=true"
    assert "_battle.start_battle(monster_id)" in bu, "missing _battle.start_battle"
    assert "visible = true" in bu, "missing visible=true in mid-callback"
    assert "_load_enemy_sprite" in bu, "missing enemy sprite load"
    print("[PASS] _setup_and_show: in_combat=true + start_battle + visible=true + sprite")

    # 4. _on_ended fade-out 적용
    end_section_start = bu.find("func _on_ended")
    assert end_section_start > 0, "missing _on_ended"
    end_section = bu[end_section_start:end_section_start + 800]
    # _on_ended 안에 두 번째 warp_fade 호출 (R85 exit fade)
    fade_count = end_section.count("SceneFaderRef.warp_fade")
    assert fade_count == 1, f"_on_ended expected 1 warp_fade call, got {fade_count}"
    assert "visible = false" in end_section, "missing visible=false in _on_ended"
    assert "GameState.in_combat = false" in end_section, "missing in_combat=false"
    assert "_battle.queue_free()" in end_section, "missing _battle cleanup"
    assert "battle_completed.emit" in end_section, "missing battle_completed signal"
    print("[PASS] _on_ended: popup 끝 → fade-out → visible=false + cleanup → battle_completed.emit")

    # 5. battle_completed.emit 가 fade 끝난 후 발생 (timing 검증)
    # Code 순서: await warp_fade(...) 다음에 emit
    emit_idx = end_section.find("battle_completed.emit")
    fade_idx = end_section.find("SceneFaderRef.warp_fade")
    assert emit_idx > fade_idx, \
        "battle_completed.emit must come AFTER fade-out await (otherwise demo receives signal during fade)"
    print("[PASS] battle_completed.emit: fade-out 완료 후 발생 (demo 가 fade 완료된 상태에서 처리)")

    # 6. start() callback closure 가 monster_id + player_state 캡처
    start_section_start = bu.find("func start(")
    start_section = bu[start_section_start:start_section_start + 400]
    # callback 안에 _setup_and_show(monster_id, player_state)
    assert "_setup_and_show(monster_id, player_state)" in start_section, \
        "callback missing monster_id/player_state forward"
    print("[PASS] start callback: monster_id + player_state forward to _setup_and_show")

    # 7. scene_fader.gd 의 warp_fade 회귀 (R84 추가됨)
    sf = read("scripts/ui/scene_fader.gd")
    assert "func warp_fade" in sf, "R84 warp_fade 손실"
    assert "mid_callback.call()" in sf, "R84 warp_fade structure 손실"
    print("[PASS] R84 SceneFader.warp_fade 회귀")

    # 8. R82 SceneRouter + R83 Sorcerer 회귀
    assert "func to_title" in read("scripts/core/scene_router.gd"), "R82 SceneRouter 손실"
    assert "stat_int * 2" in read("scripts/core/game_state.gd"), "R83 Sorcerer INT bonus 손실"
    print("[PASS] R82 (SceneRouter) + R83 (Sorcerer INT bonus) 회귀")

    print("\n=== R85 Battle UI fade transition: ALL PASSED ===")


if __name__ == "__main__":
    main()
