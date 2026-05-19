#!/usr/bin/env python3
"""R82: SceneRouter autoload + GameOver scene 검증 (Scene 흐름 정비).

검증 항목:
- SceneRouter autoload 등록 (project.godot)
- SceneRouter 의 State enum (TITLE/CLASS_SELECT/DEMO/GAME_OVER) + 4 scene path
- to_title / to_class_select / to_demo / to_demo_with_load / to_game_over / quit_to_title 6 method
- GameOver scene + 스크립트 존재 (scenes/game_over.tscn + scripts/ui/game_over.gd)
- demo.gd 의 hero death 가 SceneRouter.to_game_over 호출 (이전 silent quick_load 제거)
- demo.gd 의 F10 = SceneRouter.quit_to_title 호출
- title.gd / class_select.gd 의 SceneFader.change_scene 직접 호출 → SceneRouter 경로로 마이그레이션
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(path):
    return (GODOT / path).read_text(encoding='utf-8')


def main():
    # 1. project.godot 에 SceneRouter autoload 등록
    project = read("project.godot")
    assert 'SceneRouter="*res://scripts/core/scene_router.gd"' in project, \
        "missing SceneRouter autoload registration"
    print("[PASS] SceneRouter autoload registered in project.godot")

    # 2. scene_router.gd structure
    sr = read("scripts/core/scene_router.gd")
    assert "enum State" in sr and "TITLE" in sr and "CLASS_SELECT" in sr and "DEMO" in sr and "GAME_OVER" in sr, \
        "missing State enum with 4 states"
    assert 'res://scenes/title.tscn' in sr, "missing title scene path"
    assert 'res://scenes/class_select.tscn' in sr, "missing class_select scene path"
    assert 'res://scenes/demo.tscn' in sr, "missing demo scene path"
    assert 'res://scenes/game_over.tscn' in sr, "missing game_over scene path"
    print("[PASS] SceneRouter State enum (4 states) + 4 scene paths")

    # 3. SceneRouter 6 methods
    methods = ["to_title", "to_class_select", "to_demo", "to_demo_with_load",
               "to_game_over", "quit_to_title"]
    for m in methods:
        assert f"func {m}" in sr, f"missing SceneRouter.{m}"
    print(f"[PASS] SceneRouter {len(methods)} public transition methods")

    # 4. SceneRouter signals
    assert "signal scene_changing" in sr, "missing scene_changing signal"
    assert "signal scene_changed" in sr, "missing scene_changed signal"
    print("[PASS] SceneRouter 2 signals (scene_changing + scene_changed)")

    # 5. Transition guard
    assert "_transitioning" in sr, "missing transition guard variable"
    assert "is_transitioning" in sr, "missing is_transitioning() method"
    print("[PASS] SceneRouter transition guard (중복 전환 방지)")

    # 6. GameOver scene 파일
    assert (GODOT / "scenes/game_over.tscn").exists(), "missing game_over.tscn"
    assert (GODOT / "scripts/ui/game_over.gd").exists(), "missing game_over.gd"
    go_tscn = read("scenes/game_over.tscn")
    assert 'res://scripts/ui/game_over.gd' in go_tscn, "game_over.tscn missing script ref"
    print("[PASS] GameOver scene files exist (scenes/game_over.tscn + scripts/ui/game_over.gd)")

    # 7. GameOver scene 동작
    go = read("scripts/ui/game_over.gd")
    assert "Continue" in go, "missing Continue button"
    assert "Title" in go and "Give up" in go, "missing Title/Give up button"
    assert "to_demo_with_load" in go, "missing slot load on Continue"
    assert "to_title" in go, "missing title transition on Give up"
    assert "last_game_over_reason" in go, "missing reason display"
    print("[PASS] GameOver scene: Continue + Title 2 buttons + reason display + slot load")

    # 8. demo.gd: hero death → GameOver scene
    demo = read("scripts/ui/demo.gd")
    assert "SceneRouter.to_game_over" in demo, \
        "demo.gd missing hero-death → to_game_over transition"
    # 기존 silent quick_load 패턴 제거 검증 (death 컨텍스트에서)
    assert "쓰러졌다... (slot 0 자동 로드)" not in demo, \
        "demo.gd still has old silent quick_load on death"
    print("[PASS] demo.gd: hero death → SceneRouter.to_game_over (explicit, not silent)")

    # 9. demo.gd: F10 Quit-to-Title
    assert "KEY_F10" in demo, "demo.gd missing F10 binding"
    assert "SceneRouter.quit_to_title" in demo, "demo.gd missing quit_to_title call"
    print("[PASS] demo.gd: F10 → SceneRouter.quit_to_title (confirm popup)")

    # 10. title.gd / class_select.gd → SceneRouter 마이그레이션
    title = read("scripts/ui/title.gd")
    cs = read("scripts/ui/class_select.gd")
    assert "SceneRouter.to_class_select" in title, "title.gd missing SceneRouter.to_class_select"
    assert "SceneRouter.to_demo_with_load" in title, "title.gd missing to_demo_with_load on Continue"
    assert "SceneRouter.to_demo" in cs, "class_select.gd missing SceneRouter.to_demo on start"
    # Direct SceneFader.change_scene 호출 제거 검증 (title.gd 의 New Game / Continue 흐름)
    assert title.count("SceneFader.change_scene") == 0, \
        "title.gd still has direct SceneFader.change_scene (should be SceneRouter)"
    assert cs.count("SceneFader.change_scene") == 0, \
        "class_select.gd still has direct SceneFader.change_scene"
    print("[PASS] title.gd + class_select.gd 마이그레이션 (SceneFader 직접 호출 0개)")

    # 11. notify_ready hook (scene 이 ready 시 알림)
    assert "notify_ready" in sr, "missing notify_ready in SceneRouter"
    assert "SceneRouter.notify_ready" in go, "GameOver missing notify_ready call"
    print("[PASS] notify_ready hook 존재 (GameOver scene 호출)")

    print("\n=== R82 SceneRouter + GameOver + Scene flow: ALL PASSED ===")


if __name__ == "__main__":
    main()
