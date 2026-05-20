#!/usr/bin/env python3
"""R92: SaveListPanel UI — 8 slot 선택 + 메타 표시 + 액션 버튼 (G/E +0.5%p).

R91 의 round-trip 정합성 후속. 그동안 demo.gd 의 1-8 숫자 키 + Shift 조합
만으로 slot 저장/로드가 가능했고 어느 슬롯이 어떤 상태인지 보이지 않았음.
F6 으로 열리는 SaveListPanel 이 8 슬롯 (+ AUTO 7) 의 메타 (timestamp /
class / level / gold / playtime) 와 행마다 Load / Save / Delete 버튼.

검증:
- save_list_panel.gd 의 핵심 구조 (class_name, CanvasLayer, refresh,
  _build_slot_row, _format_slot, _on_load/save/delete, slot_loaded signal).
- save_list_panel.tscn 의 6 노드 (BG / Title / SlotList / StatusLabel /
  CloseButton + uid).
- demo.gd 의 _save_list var, instantiation, slot_loaded 연결, F6 key 바인딩.
- AUTO_SLOT (7) 의 save 버튼 비활성화.
- H5SaveManager 의 list_slots() / load_slot() / delete_slot() 활용.
- R90/R91 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    slp = read("scripts/ui/save_list_panel.gd")
    tscn = read("scenes/save_list_panel.tscn")
    demo = read("scripts/ui/demo.gd")
    sm = read("scripts/core/save_manager.gd")
    gs = read("scripts/core/game_state.gd")
    gd = read("scripts/core/game_data.gd")

    # 1. save_list_panel.gd 핵심 구조
    for marker in [
        "class_name SaveListPanel",
        "extends CanvasLayer",
        "func toggle()",
        "func refresh()",
        "func _build_slot_row(slot: int)",
        "func _format_slot(slot: int)",
        "func _on_load(slot: int)",
        "func _on_save(slot: int)",
        "func _on_delete(slot: int)",
        "signal slot_loaded(slot: int)",
        "CLASS_NAMES :=",
    ]:
        assert marker in slp, f"save_list_panel.gd 누락: {marker!r}"
    print("[PASS] save_list_panel.gd 핵심 구조 (class_name, 7 func, 1 signal, CLASS_NAMES)")

    # 2. H5SaveManager API 활용
    for marker in [
        "H5SaveManager.MAX_SLOTS",
        "H5SaveManager.AUTO_SLOT",
        "H5SaveManager.load_slot(slot)",
        "H5SaveManager.delete_slot(slot)",
    ]:
        assert marker in slp, f"save_list_panel.gd save_manager API 미사용: {marker!r}"
    # GameState quick_save/load
    assert "GameState.quick_save(slot)" in slp
    assert "GameState.quick_load(slot)" in slp
    print("[PASS] save_list_panel.gd: H5SaveManager API (MAX_SLOTS/AUTO_SLOT/load/delete) + GameState quick_save/load")

    # 3. AUTO_SLOT 의 save 버튼 비활성화 — disabled = (slot == AUTO_SLOT)
    assert "save_btn.disabled = (slot == H5SaveManager.AUTO_SLOT)" in slp, \
        "AUTO_SLOT save 버튼 비활성화 누락"
    print("[PASS] save_list_panel.gd: AUTO_SLOT 의 수동 저장 비활성화")

    # 4. tscn 노드 구조
    for marker in [
        '[node name="SaveListPanel" type="CanvasLayer"]',
        '[node name="BG" type="ColorRect" parent="."]',
        '[node name="Title" type="Label" parent="BG"]',
        '[node name="SlotList" type="VBoxContainer" parent="BG"]',
        '[node name="StatusLabel" type="Label" parent="BG"]',
        '[node name="CloseButton" type="Button" parent="BG"]',
        'script = ExtResource("1_savelist")',
        'uid="uid://hero5_savelist"',
    ]:
        assert marker in tscn, f"save_list_panel.tscn 누락: {marker!r}"
    print("[PASS] save_list_panel.tscn: 6 node + uid")

    # 5. demo.gd 통합
    assert "var _save_list: CanvasLayer" in demo, "demo._save_list var 누락"
    assert 'preload("res://scenes/save_list_panel.tscn").instantiate()' in demo, \
        "demo SaveListPanel preload 누락"
    assert "_save_list.slot_loaded.connect" in demo, "demo slot_loaded 시그널 연결 누락"
    assert "KEY_F6" in demo, "demo F6 키 바인딩 누락"
    assert "_save_list.toggle()" in demo, "demo F6 토글 호출 누락"
    print("[PASS] demo.gd 통합: var + preload + slot_loaded 연결 + F6 토글")

    # 6. F6 핸들러가 현재 scene/map/pos 를 GameState 에 sync 후 toggle
    f6_idx = demo.find("KEY_F6")
    assert f6_idx > 0
    f6_section = demo[f6_idx:f6_idx + 400]
    for marker in [
        "GameState.current_scene_id = _scene_idx",
        "GameState.map_id = _map.map_id",
        "GameState.player_x = int(_hero.position.x)",
        "GameState.player_y = int(_hero.position.y)",
        "_save_list.toggle()",
    ]:
        assert marker in f6_section, f"F6 핸들러 누락: {marker!r}"
    print("[PASS] demo.gd F6 핸들러: scene/map/pos sync + toggle")

    # 7. slot_loaded 연결의 callback 이 scene_idx 갱신 + _apply_scene 호출
    sl_idx = demo.find("_save_list.slot_loaded.connect")
    callback_section = demo[sl_idx:sl_idx + 300]
    assert "_scene_idx = GameState.current_scene_id" in callback_section
    assert "_apply_scene()" in callback_section
    print("[PASS] demo.gd slot_loaded callback: scene_idx 갱신 + _apply_scene")

    # 8. _format_slot 의 metadata 표시 필드
    for marker in [
        '(빈 슬롯)',
        'CLASS_NAMES[cid]',
        '"AUTO  "',
        'data.get("timestamp"',
        'data.get("play_time_sec"',
        'p.get("class_id"',
        'p.get("level"',
        'p.get("gold"',
    ]:
        assert marker in slp, f"_format_slot metadata 누락: {marker!r}"
    print("[PASS] save_list_panel.gd _format_slot: empty/AUTO/timestamp/playtime/class/level/gold 표시")

    # 9. R91 회귀: save_manager.make_payload + game_state.apply_save 잔존
    assert '"skill_levels": state.get("skill_levels", {})' in sm
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    assert "Quest.from_save" in gs and "Mission.from_save" in gs
    print("[PASS] R91 회귀: round-trip 정합성 유지 (skill_levels / Quest / Mission)")

    # 10. R90 회귀: resolve_skill_desc_display + first_line
    assert "func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:" in gd
    assert "func resolve_skill_desc_first_line(class_id: int, skill_id: int) -> String:" in gd
    print("[PASS] R90 회귀: resolve_skill_desc_display + first_line")

    # 11. R92 docstring marker
    assert "Round 92" in slp, "R92 docstring marker 누락 (save_list_panel)"
    assert "Round 92" in demo, "R92 docstring marker 누락 (demo)"
    print("[PASS] R92 docstring marker (save_list_panel + demo)")

    print("\n[R92 ALL PASSED] 11/11")


if __name__ == "__main__":
    main()
