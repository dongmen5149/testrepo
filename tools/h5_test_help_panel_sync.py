#!/usr/bin/env python3
"""R94: HelpPanel 키 명세 동기화 (H/QA +0.3%p).

R82-R93 동안 demo.gd 에 추가된 키 (F6 SaveList, F10 Quit-to-Title, G monster
spawn, SPACE attack, R/K/O/J/L/comma 패널 등) 가 help_panel.gd 의 HELP_TEXT
에 누락되어 있었음. R93 의 인라인 slot UI 제거로 "슬롯 우클릭 → 삭제" 안내도
잘못된 상태. R94 = HELP_TEXT 를 demo.gd + title.gd 의 실 키 바인딩과
동기화.

검증:
- demo.gd 의 KEY_F6 / KEY_F10 / KEY_G / KEY_SPACE / KEY_R / KEY_K / KEY_O /
  KEY_J / KEY_L / KEY_COMMA 모두 HELP_TEXT 에 멘션.
- 잘못된 안내 ("slot 0 자동 로드" / "슬롯 우클릭" / "Shift+클릭 → 삭제")
  제거.
- R92 SaveListPanel + R93 Title 통합 회귀.
- R90/R91 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    hp = read("scripts/ui/help_panel.gd")
    demo = read("scripts/ui/demo.gd")
    title = read("scripts/ui/title.gd")
    slp = read("scripts/ui/save_list_panel.gd")
    gs = read("scripts/core/game_state.gd")
    gd = read("scripts/core/game_data.gd")

    # HELP_TEXT 영역 추출
    m = re.search(r'const HELP_TEXT := """(.*?)"""', hp, re.DOTALL)
    assert m, "HELP_TEXT 상수 추출 실패"
    help_text = m.group(1)

    # 1. demo.gd 의 KEY_* 바인딩 추출 (KEY_ 패턴)
    demo_keys = set(re.findall(r'\bKEY_([A-Z0-9_]+)\b', demo))
    # 숫자 키는 1-8 묶음으로, KEY_SHIFT 는 modifier 라 skip
    skip_keys = {"SHIFT", "1", "2", "3", "4", "5", "6", "7", "8"}
    interesting = demo_keys - skip_keys
    # 추가로 demo 에 있어야 할 R92/R93 신규 키
    must_have = {"F6", "F10", "F5", "F9", "G", "SPACE", "R", "K", "O", "J", "L",
                 "COMMA", "B", "E", "X", "H", "Q", "S", "I", "ESCAPE", "M", "N",
                 "T", "C", "V", "P"}
    missing_in_demo = must_have - demo_keys
    assert not missing_in_demo, f"demo.gd 에 누락된 KEY 바인딩: {missing_in_demo}"
    print(f"[PASS] demo.gd 의 {len(interesting)} 종 KEY_ 바인딩 확인 (필수 {len(must_have)} 모두 포함)")

    # 2. HELP_TEXT 가 R94 추가 키 명시 (라벨 문자열 기준)
    new_in_r94 = [
        ("F6", "F6"),
        ("F10", "F10"),
        ("G", "G —"),
        ("SPACE", "SPACE —"),
        ("R 강화", "R — 강화"),
        ("K 합성", "K — 합성"),
        ("O Orb", "O — Orb"),
        ("J 대장간", "J — 대장간"),
        ("L 스킬북", "L — 스킬북"),
        (", 미션", ", — 미션"),
    ]
    missing_help = [name for (name, marker) in new_in_r94 if marker not in help_text]
    assert not missing_help, f"HELP_TEXT 에 R94 추가 키 누락: {missing_help}"
    print(f"[PASS] HELP_TEXT: 10 R94 신규/누락 키 모두 명시 (F6 / F10 / G / SPACE / R/K/O/J/L/,)")

    # 3. R93 으로 폐기된 잘못된 안내 제거
    obsolete = [
        "slot 0 자동 로드",
        "슬롯 우클릭",
        "Shift+클릭 → 삭제",
    ]
    leftover_obsolete = [s for s in obsolete if s in help_text]
    assert not leftover_obsolete, f"R93 으로 폐기된 잘못된 안내 잔존: {leftover_obsolete}"
    print("[PASS] HELP_TEXT: R93 으로 폐기된 잘못된 안내 모두 제거")

    # 4. F6 = Save 목록 패널 설명 정확
    assert "Save 목록 패널" in help_text or "Save 목록" in help_text, \
        "F6 의 SaveListPanel 설명 누락"
    print("[PASS] HELP_TEXT: F6 = Save 목록 패널 설명 포함")

    # 5. Title 화면 안내가 SaveListPanel 위임으로 갱신
    title_section_match = re.search(r"\[b\]Title 화면\[/b\](.*?)(?=\[b\]|\Z)",
                                     help_text, re.DOTALL)
    assert title_section_match, "HELP_TEXT 의 Title 화면 섹션 누락"
    title_section = title_section_match.group(1)
    assert "Save 목록" in title_section or "슬롯 선택" in title_section, \
        "Title Continue 의 SaveListPanel 위임 안내 누락"
    assert "Delete 버튼" in title_section or "삭제" in title_section, \
        "Title 의 슬롯 삭제 안내 누락"
    print("[PASS] HELP_TEXT Title 섹션: SaveListPanel 위임 + Delete 버튼 안내")

    # 6. R94 docstring marker
    assert "Round 94" in hp, "R94 docstring marker 누락 (help_panel)"
    print("[PASS] R94 docstring marker (help_panel)")

    # 7. R93 회귀: title.gd 의 SaveListPanel 위임 잔존
    assert "_save_list.slot_loaded.connect(_on_slot_loaded)" in title
    assert "func _on_slot_loaded" in title
    assert "_save_list.toggle()" in title
    print("[PASS] R93 회귀: title.gd 의 SaveListPanel 위임 + _on_slot_loaded")

    # 8. R92 회귀: SaveListPanel signal + demo F6
    assert "signal slot_loaded(slot: int)" in slp
    assert "KEY_F6" in demo
    print("[PASS] R92 회귀: SaveListPanel signal + demo F6")

    # 9. R91 회귀: round-trip
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: save round-trip 잔존")

    # 10. R90 회귀: desc helper
    assert "func resolve_skill_desc_display(class_id: int, skill_id: int) -> String:" in gd
    print("[PASS] R90 회귀: resolve_skill_desc_display 잔존")

    # 11. HelpPanel 의 toggle / _ready 잔존 (구조 안 깨짐)
    assert "func toggle()" in hp
    assert "func _ready()" in hp
    assert "content.bbcode_enabled = true" in hp
    print("[PASS] HelpPanel 구조 (toggle / _ready / bbcode) 잔존")

    print("\n[R94 ALL PASSED] 11/11")


if __name__ == "__main__":
    main()
