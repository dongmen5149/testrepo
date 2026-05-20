#!/usr/bin/env python3
"""R96: demo.gd 의 Toast.severity helper 마이그레이션 (E/H +0.2%p).

R95 Toast 정비 후속. R95 시점 demo.gd 가 R86-R94 시절 부터 누적된 12 호출의
`preload("res://scripts/ui/toast.gd").show_msg(self, text, ...)` 패턴으로
모든 toast 가 노랑 + 의미 불명. R96 = 12 호출 전부 R95 의 severity helper
(`Toast.info / success / warn / error`) 로 마이그레이션 + preload 패턴 제거.

분류 기준:
- info: 일반 알림/디버그 (8 호출) — 퀘스트 시작 / 몬스터 skill 정보 /
  monster spawn 로그 / 타일/충돌 변경 디버그 / 화면 흔들림 / 시스템 메시지 /
  BGM 변경.
- success: 긍정적 결과 (2 호출) — 퀘스트 완료 + 아이템 획득.
- warn: 사용자 입력 부정 (2 호출) — 공격할 적 없음 / 공격 범위 내 적 없음.
- error: 0 호출 (demo 에 치명적 에러 toast 없음).

검증:
- demo.gd 의 preload 패턴 0 회 잔존.
- Toast.info / success / warn 호출 분포 (8 / 2 / 2 = 12).
- 분류 정확성 (퀘스트 시작 info / 퀘스트 완료 success / 아이템 획득 success /
  공격할 적 warn / 공격 범위 warn).
- 기존 호출 12 → severity helper 12 (총 합 유지).
- R95 Toast.gd 의 4 helper 잔존 + show_msg 호환 (다른 호출자 미래 대비).
- R91-R94 회귀.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"


def read(p):
    return (GODOT / p).read_text(encoding='utf-8')


def main():
    demo = read("scripts/ui/demo.gd")
    toast = read("scripts/ui/toast.gd")
    hp = read("scripts/ui/help_panel.gd")
    slp = read("scripts/ui/save_list_panel.gd")
    title = read("scripts/ui/title.gd")
    gs = read("scripts/core/game_state.gd")

    # 1. demo.gd 의 preload show_msg 패턴 0 회
    leftover = demo.count('preload("res://scripts/ui/toast.gd").show_msg(')
    assert leftover == 0, f"preload show_msg 패턴 잔존: {leftover} (마이그레이션 미완)"
    print("[PASS] demo.gd: preload show_msg 패턴 0 회 (R86-R94 12 호출 모두 정리)")

    # 2. Toast.info / success / warn / error 호출 분포
    n_info = len(re.findall(r"\bToast\.info\(", demo))
    n_success = len(re.findall(r"\bToast\.success\(", demo))
    n_warn = len(re.findall(r"\bToast\.warn\(", demo))
    n_error = len(re.findall(r"\bToast\.error\(", demo))
    total = n_info + n_success + n_warn + n_error
    # R96 시점 = 12 (info=8/success=2/warn=2/error=0). R97+ 라운드에서 추가 호출
    # 가능 (예: R98 mute on/off → +1 info +1 warn). 하한만 검사.
    assert total >= 12, f"마이그레이션 후 Toast 호출 합 < 12: {total}"
    assert n_info >= 8, f"info 호출 < 8: {n_info}"
    assert n_success == 2, f"success 호출 != 2: {n_success}"
    assert n_warn >= 2, f"warn 호출 < 2: {n_warn}"
    print(f"[PASS] demo.gd Toast 분포: info={n_info} / success={n_success} / warn={n_warn} / error={n_error} (총 {total}, R96 기준 12 이상)")

    # 3. 분류 정확성 — 특정 메시지 → 특정 severity
    classifications = [
        ('Toast.info(self, "퀘스트 시작', "퀘스트 시작 (info)"),
        ('Toast.success(self, "퀘스트 완료', "퀘스트 완료 (success)"),
        ('Toast.success(self, "획득: %s"', "아이템 획득 (success)"),
        ('Toast.warn(self, "공격할 적 없음")', "공격할 적 없음 (warn)"),
        ('Toast.warn(self, "공격 범위 내 적 없음', "공격 범위 (warn)"),
        ('Toast.info(self, "BGM 변경', "BGM 변경 (info)"),
        ('Toast.info(self, "시스템 메시지', "시스템 메시지 (info)"),
        ('Toast.info(self, "화면 흔들림', "화면 흔들림 (info)"),
        ('Toast.info(self, "타일 변경', "타일 변경 (info)"),
        ('Toast.info(self, "충돌 변경', "충돌 변경 (info)"),
        ('Toast.info(self,\n\t\t\t\t\t"monster #', "monster spawn (info)"),
        ('Toast.info(self, "#%d → skill', "skill 발동 (info)"),
    ]
    for marker, desc in classifications:
        assert marker in demo, f"분류 마이그레이션 누락: {desc} → marker {marker!r}"
    print(f"[PASS] demo.gd 분류 정확성: 12/12 메시지가 의도된 severity 로 분류")

    # 4. R95 Toast 의 4 helper + show_msg 호환 잔존
    for fn in [
        "static func info(parent: Node, text: String,",
        "static func success(parent: Node, text: String,",
        "static func warn(parent: Node, text: String,",
        "static func error(parent: Node, text: String,",
        "static func show_msg(parent: Node, text: String,",
    ]:
        assert fn in toast, f"R95 Toast helper 손실: {fn!r}"
    print("[PASS] R95 회귀: Toast.gd 4 severity helper + show_msg 호환 잔존")

    # 5. R95 stack + fade 잔존
    assert "static var _active_toasts: Array = []" in toast
    assert 'tween.tween_property(_bg, "modulate:a", 1.0, FADE_IN_DUR)' in toast
    print("[PASS] R95 회귀: Toast stack + fade-in tween 잔존")

    # 6. R96 docstring marker
    assert "Round 96" in demo, "R96 docstring marker 누락 (demo)"
    print("[PASS] R96 docstring marker (demo)")

    # 7. R94 회귀: HelpPanel 키 동기화
    m = re.search(r'const HELP_TEXT := """(.*?)"""', hp, re.DOTALL)
    help_text = m.group(1)
    for marker in ["F6", "F10", "Save 목록"]:
        assert marker in help_text
    print("[PASS] R94 회귀: HelpPanel 키 동기화")

    # 8. R93 회귀: title.gd SaveListPanel 위임
    assert "_save_list.slot_loaded.connect(_on_slot_loaded)" in title
    print("[PASS] R93 회귀: title.gd SaveListPanel 위임")

    # 9. R92 회귀: SaveListPanel signal
    assert "signal slot_loaded(slot: int)" in slp
    print("[PASS] R92 회귀: SaveListPanel slot_loaded signal")

    # 10. R91 회귀: round-trip
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: save round-trip")

    # 11. 추가: Quest.quest_completed connect 의 R96 form 확인 (3.0 duration 유지)
    assert "Toast.success(self, \"퀘스트 완료: \" + Quest.quest_name(qid), 3.0)" in demo, \
        "퀘스트 완료의 3.0초 duration override 손실"
    print("[PASS] 퀘스트 완료 Toast.success 의 3.0s duration override 유지")

    # 12. 아이템 획득의 2.0s duration override 유지
    assert 'Toast.success(self, "획득: %s" % item_name, 2.0)' in demo, \
        "아이템 획득의 2.0s duration override 손실"
    print("[PASS] 아이템 획득 Toast.success 의 2.0s duration override 유지")

    print("\n[R96 ALL PASSED] 12/12")


if __name__ == "__main__":
    main()
