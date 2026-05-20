#!/usr/bin/env python3
"""R93: Title Continue → SaveListPanel 통합 (E +0.3%p).

R92 SaveListPanel 의 자연스러운 후속. Title.gd 가 인라인 slot 버튼 + 우클릭
삭제 popup 을 직접 렌더링하던 코드 (~50 줄) 를 제거하고 R92 SaveListPanel 로
위임. Continue 버튼 = SaveListPanel toggle. slot_loaded 시그널 처리 시
quick_load 는 SaveListPanel 이 이미 수행했으므로 Title 은 SceneRouter.to_demo
직행 (중복 호출 없음).

검증:
- title.gd 의 _refresh_slots / _confirm_delete / _on_slot_selected /
  _selected_slot 모두 제거 (~50 줄 deletion).
- _save_list 인스턴스 + slot_loaded 시그널 연결.
- _on_continue 가 _save_list.toggle() 호출 (SceneRouter.to_demo_with_load
  직접 호출 X).
- _on_slot_loaded 핸들러 신규: GameState 가 이미 로드된 상태이므로
  SceneRouter.to_demo(self) 만 호출 (중복 quick_load 없음).
- _refresh_status 신규 (slots Label 의 fallback 메시지만).
- title.tscn 변경 없음 (인라인 Slot_* 버튼은 동적 생성이므로 scene 불필요).
- R90/R91/R92 회귀.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    title = read("scripts/ui/title.gd")
    slp = read("scripts/ui/save_list_panel.gd")
    demo = read("scripts/ui/demo.gd")
    gs = read("scripts/core/game_state.gd")
    gd = read("scripts/core/game_data.gd")

    # 1. R92 이전 인라인 슬롯 코드 제거 검증
    removed_markers = [
        "func _refresh_slots()",
        "func _confirm_delete(",
        "func _on_slot_selected(",
        "var _selected_slot",
        "AcceptDialog.new()",
        'c.name.begins_with("Slot_")',
        'btn.name = "Slot_%d"',
        "MOUSE_BUTTON_RIGHT",
    ]
    leftover = [m for m in removed_markers if m in title]
    assert not leftover, f"R92 이전 인라인 슬롯 코드 잔존 (R93 미정리): {leftover}"
    print("[PASS] title.gd: 인라인 slot 버튼/popup 코드 8 marker 모두 제거 (~50 줄 deletion)")

    # 2. _save_list 인스턴스
    assert "var _save_list: CanvasLayer" in title, "title._save_list var 누락"
    assert 'preload("res://scenes/save_list_panel.tscn").instantiate()' in title, \
        "title SaveListPanel preload 누락"
    assert "_save_list.slot_loaded.connect(_on_slot_loaded)" in title, \
        "title slot_loaded 시그널 연결 누락"
    print("[PASS] title.gd: _save_list var + preload + slot_loaded 연결")

    # 3. _on_continue 가 SaveListPanel 위임 (직접 SceneRouter 호출 X)
    cont_idx = title.find("func _on_continue")
    cont_section = title[cont_idx:cont_idx + 400]
    assert "_save_list.toggle()" in cont_section, "_on_continue 의 SaveListPanel toggle 누락"
    assert "SceneRouter.to_demo_with_load(self, slot)" not in cont_section, \
        "_on_continue 가 여전히 to_demo_with_load 직접 호출 (위임 안 함)"
    print("[PASS] title.gd _on_continue: SaveListPanel toggle 위임 (to_demo_with_load 직접 호출 X)")

    # 4. _on_slot_loaded 핸들러 신규
    sl_idx = title.find("func _on_slot_loaded")
    assert sl_idx > 0, "_on_slot_loaded 핸들러 누락"
    sl_section = title[sl_idx:sl_idx + 300]
    assert "SceneRouter.to_demo(self)" in sl_section, \
        "_on_slot_loaded 가 to_demo 미호출"
    # quick_load 중복 호출 없음 확인 (주석 내 멘션은 허용, 실 호출만 검사)
    # 함수 호출 패턴: GameState.quick_load(slot 또는 변수)
    sl_code_lines = [ln for ln in sl_section.split("\n") if not ln.strip().startswith("#")]
    sl_code = "\n".join(sl_code_lines)
    assert "GameState.quick_load(" not in sl_code, \
        "_on_slot_loaded 가 quick_load 중복 호출 (SaveListPanel 이 이미 수행)"
    print("[PASS] title.gd _on_slot_loaded: SceneRouter.to_demo + quick_load 중복 호출 없음")

    # 5. _refresh_status 신규 (status label 만)
    assert "func _refresh_status()" in title, "_refresh_status 함수 누락"
    rs_idx = title.find("func _refresh_status")
    rs_section = title[rs_idx:rs_idx + 500]
    assert "저장 데이터 없음" in rs_section, "_refresh_status 의 빈 슬롯 메시지 누락"
    assert "cont_btn.disabled" in rs_section, "_refresh_status 의 Continue 버튼 비활성 처리 누락"
    print("[PASS] title.gd _refresh_status: 빈 슬롯 fallback + Continue 비활성")

    # 6. SaveListPanel 의 slot_loaded signal 잔존 (R92)
    assert "signal slot_loaded(slot: int)" in slp, "R92 slot_loaded signal 손실"
    assert "func _on_load(slot: int)" in slp, "R92 _on_load 손실"
    # SaveListPanel 의 _on_load 가 quick_load 후 slot_loaded.emit
    on_load = slp[slp.find("func _on_load"):]
    on_load = on_load[:on_load.find("\nfunc ")]
    assert "GameState.quick_load(slot)" in on_load
    assert "slot_loaded.emit(slot)" in on_load
    print("[PASS] R92 회귀: SaveListPanel slot_loaded signal + _on_load (quick_load + emit)")

    # 7. demo.gd 의 F6 + SaveListPanel 통합 잔존 (R92)
    assert "var _save_list: CanvasLayer" in demo
    assert "KEY_F6" in demo
    assert "_save_list.slot_loaded.connect" in demo
    print("[PASS] R92 회귀: demo.gd F6 + SaveListPanel 통합 잔존")

    # 8. R91 회귀: round-trip
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    assert "Quest.from_save" in gs
    print("[PASS] R91 회귀: save round-trip 정합성 잔존")

    # 9. R90 회귀: spirit desc helper
    assert "func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:" in gd
    print("[PASS] R90 회귀: resolve_skill_desc_display 잔존")

    # 10. R93 docstring marker
    assert "Round 93" in title, "R93 docstring marker 누락 (title)"
    print("[PASS] R93 docstring marker (title)")

    # 11. _on_continue 이 _selected_slot 의존 제거됨 (R92 이전 코드)
    assert "_selected_slot" not in title, "_selected_slot 변수 잔존"
    print("[PASS] _selected_slot 변수 완전 제거 (R92 이전 코드 정리)")

    print("\n[R93 ALL PASSED] 11/11")


if __name__ == "__main__":
    main()
