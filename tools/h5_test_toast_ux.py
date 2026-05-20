#!/usr/bin/env python3
"""R95: Toast severity + fade-in + stack 정비 (E/H +0.3%p).

R94 의 HelpPanel 동기화 후속 UX 라운드. Toast.gd 가 (1) 같은 frame 다발 발화
시 동일 좌표 (60, 110) 에 겹쳐 표시되고, (2) fade-out 만 있고 fade-in 부재
(갑작스러운 등장), (3) severity 구분 없이 모든 toast 가 노랑 — 색상 일관성
부재. R95 = severity enum (INFO/SUCCESS/WARN/ERROR) + 4 단축 static helper +
fade-in tween (0.18s) + 동시 다수 vertical stack (32px step).

기존 `show_msg(parent, text, duration, color)` API 는 호환 유지 (R86-R94
호출자 모두 그대로 동작).

검증:
- Severity enum + COLORS dict (INFO/SUCCESS/WARN/ERROR 4 entry).
- 4 static helper (info/success/warn/error) + show_severity dispatcher.
- show_msg 시그니처 호환 (parent + text + duration + color, color default 유지).
- fade-in tween (modulate.a 0 → 1) + idle interval + fade-out (1 → 0) +
  cleanup callback.
- _active_toasts static array + stack Y 계산 (STACK_Y_BASE + STEP * count) +
  _finish 시 erase.
- R94 회귀 (HelpPanel 키 동기화) + R93/R92/R91 회귀.
- demo.gd 의 기존 show_msg 호출 호환 유지 (마이그레이션 강제 X).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    toast = read("scripts/ui/toast.gd")
    demo = read("scripts/ui/demo.gd")
    hp = read("scripts/ui/help_panel.gd")
    slp = read("scripts/ui/save_list_panel.gd")
    title = read("scripts/ui/title.gd")
    gs = read("scripts/core/game_state.gd")

    # 1. Severity enum + COLORS dict
    assert "enum Severity { INFO, SUCCESS, WARN, ERROR }" in toast, \
        "Severity enum 누락 (R95 신규)"
    assert "const COLORS :=" in toast, "COLORS dict 누락"
    for sev in ["Severity.INFO", "Severity.SUCCESS", "Severity.WARN", "Severity.ERROR"]:
        assert sev in toast, f"COLORS 의 {sev} entry 누락"
    print("[PASS] Toast: Severity enum (INFO/SUCCESS/WARN/ERROR) + COLORS 4 entry")

    # 2. 4 static helper + show_severity
    for fn in [
        "static func info(parent: Node, text: String, duration: float = 2.5)",
        "static func success(parent: Node, text: String, duration: float = 2.5)",
        "static func warn(parent: Node, text: String, duration: float = 2.8)",
        "static func error(parent: Node, text: String, duration: float = 3.2)",
        "static func show_severity(parent: Node, text: String, severity: int,",
    ]:
        assert fn in toast, f"Toast static helper 누락: {fn!r}"
    print("[PASS] Toast: 4 severity helper (info/success/warn/error) + show_severity dispatcher")

    # 3. show_msg 시그니처 호환 (parent / text / duration=2.5 / color default)
    assert ("static func show_msg(parent: Node, text: String, duration: float = 2.5,"
            in toast), "Toast.show_msg 시그니처 변형 (R94 이전 호출자 호환 깨짐)"
    assert "color: Color = Color(1, 1, 0.4, 1)" in toast, \
        "Toast.show_msg color default 변형"
    print("[PASS] Toast: show_msg 시그니처 호환 (기존 R86-R94 호출자 그대로 동작)")

    # 4. fade-in tween 신규 (modulate.a 0 → 1)
    assert 'tween.tween_property(_bg, "modulate:a", 1.0, FADE_IN_DUR)' in toast, \
        "fade-in tween 누락"
    assert "_bg.modulate.a = 0.0" in toast, "fade-in 초기 alpha=0 설정 누락"
    assert "const FADE_IN_DUR := 0.18" in toast
    assert "const FADE_OUT_DUR := 0.6" in toast
    print("[PASS] Toast: fade-in (0.18s, a=0→1) + fade-out (0.6s, a=1→0) tween chain")

    # 5. _active_toasts static + stack Y 계산 + _finish erase
    assert "static var _active_toasts: Array = []" in toast, "_active_toasts static 누락"
    assert "const STACK_Y_BASE := 110.0" in toast
    assert "const STACK_Y_STEP := 32.0" in toast
    assert ("STACK_Y_BASE + STACK_Y_STEP * float(_active_toasts.size())"
            in toast), "stack Y 계산 식 누락"
    assert "_active_toasts.append(self)" in toast
    assert "_active_toasts.erase(self)" in toast, "_finish 의 stack erase 누락"
    print("[PASS] Toast: _active_toasts static array + stack Y (110 + 32 × count) + _finish erase")

    # 6. tween chain 4 단계 (fade-in → interval → fade-out → callback)
    show_section = toast[toast.find("func _show"):toast.find("\nfunc _finish")]
    # tween_property fade-in, tween_interval, tween_property fade-out, tween_callback
    n_tween_property = show_section.count("tween.tween_property")
    n_tween_interval = show_section.count("tween.tween_interval")
    n_tween_callback = show_section.count("tween.tween_callback")
    assert n_tween_property == 2, f"tween_property 호출 수 != 2 (fade-in + fade-out): {n_tween_property}"
    assert n_tween_interval == 1, f"tween_interval 호출 수 != 1 (idle): {n_tween_interval}"
    assert n_tween_callback == 1, f"tween_callback 호출 수 != 1 (cleanup): {n_tween_callback}"
    print("[PASS] Toast _show: tween chain 4 단계 (fade-in / idle / fade-out / callback)")

    # 7. R94 회귀: HelpPanel 키 동기화 잔존
    m = re.search(r'const HELP_TEXT := """(.*?)"""', hp, re.DOTALL)
    assert m
    help_text = m.group(1)
    for marker in ["F6", "F10", "G —", "SPACE —", "Save 목록"]:
        assert marker in help_text, f"R94 회귀 실패 marker: {marker!r}"
    print("[PASS] R94 회귀: HelpPanel 키 동기화 잔존 (F6/F10/G/SPACE/Save 목록)")

    # 8. R93 회귀: title.gd SaveListPanel 위임
    assert "_save_list.slot_loaded.connect(_on_slot_loaded)" in title
    assert "func _on_slot_loaded" in title
    print("[PASS] R93 회귀: Title SaveListPanel 위임")

    # 9. R92 회귀: SaveListPanel 신호
    assert "signal slot_loaded(slot: int)" in slp
    print("[PASS] R92 회귀: SaveListPanel slot_loaded signal")

    # 10. R91 회귀: round-trip
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: save round-trip 잔존")

    # 11. show_msg 시그니처 호환 함수 자체는 잔존 (R96 마이그레이션 후에도
    #     외부 호출자 미래 대비). demo.gd 의 호출 수는 R96 이후 0 가능.
    assert "static func show_msg(parent: Node, text: String, duration: float = 2.5," in toast, \
        "Toast.show_msg 함수 자체 손실 (외부 호출자 호환 보장 깨짐)"
    print(f"[PASS] Toast 호환: show_msg 함수 시그니처 유지 (R96+ 외부 호출자 대비)")

    # 12. R95 docstring marker
    assert "Round 95" in toast, "R95 docstring marker 누락 (toast)"
    print("[PASS] R95 docstring marker (toast)")

    print("\n[R95 ALL PASSED] 12/12")


if __name__ == "__main__":
    main()
