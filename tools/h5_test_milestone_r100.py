#!/usr/bin/env python3
"""R100: 밀레스톤 결산 문서 검증 (H/QA +0.2%p).

R82-R99 18 라운드 누적 변화 + 잔여 큰 덩어리를 한 페이지로 정리.
docs/h5/MILESTONE_R100.md 의 5 섹션 (누적 변화 / 카테고리 마일스톤 /
잔여 덩어리 / 18 라운드 라인업 / 핵심 RE 종결) 검증.

검증:
- MILESTONE_R100.md 존재 + 5 섹션 모두 보유.
- R82 시작 (73.01%) → R99 종료 (86.07%) 정확 매칭.
- 18 라운드 라인업의 각 라운드 entry (R82-R99) 존재.
- 카테고리 Δ 8 entry (A/B/C/D/E/F/G/H).
- R100+ 잔여 4 옵션 (A/B/C/D) 명시.
- R91-R99 회귀 (자동 테스트 모두 PASS).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT = ROOT / "apps/hero5-godot"
DOCS = ROOT / "docs/h5"


def main():
    ms_path = DOCS / "MILESTONE_R100.md"
    assert ms_path.exists(), "MILESTONE_R100.md 누락"
    ms = ms_path.read_text(encoding='utf-8')

    # 1. 5 섹션 헤더
    sections = [
        "## 1. 누적 변화",
        "## 2. 카테고리별 주요 마일스톤",
        "## 3. 잔여 큰 덩어리",
        "## 4. 18 라운드 라인업",
        "## 5. 핵심 RE/구현 종결 사실",
    ]
    for sec in sections:
        assert sec in ms, f"섹션 누락: {sec!r}"
    print("[PASS] MILESTONE_R100.md: 5 섹션 (누적 변화 / 카테고리 마일스톤 / 잔여 / 라인업 / 종결 사실)")

    # 2. 시작/종료 종합 수치
    assert "73.01%" in ms, "R82 시작 종합 73.01% 누락"
    assert "86.07%" in ms, "R99 종료 종합 86.07% 누락"
    assert "+13.90%p" in ms or "+13.06" in ms, "누적 Δ 13.06~13.90 명시 누락"
    print("[PASS] MILESTONE_R100.md: R82 73.01% → R99 86.07% 종합 추이 명시")

    # 3. 18 라운드 모두 lineup 섹션에 entry
    lineup_idx = ms.find("## 4. 18 라운드 라인업")
    lineup = ms[lineup_idx:lineup_idx + 3000]
    missing_rounds = []
    for r in range(82, 100):
        if f"R{r} " not in lineup:
            missing_rounds.append(f"R{r}")
    assert not missing_rounds, f"18 라운드 라인업 누락: {missing_rounds}"
    print(f"[PASS] MILESTONE_R100.md: R82-R99 18 라운드 모두 라인업에 entry")

    # 4. 카테고리 Δ 8 entry (R99 종료 수치)
    cat_idx = ms.find("## 1. 누적 변화")
    cat_section = ms[cat_idx:ms.find("## 2.")]
    for cat in ["A.", "B.", "C.", "D.", "E.", "F.", "G.", "H."]:
        assert cat in cat_section, f"카테고리 {cat} entry 누락"
    # Δ +37 (E) / +54 (F) 큰 도약
    assert "+37" in cat_section, "E 카테고리 +37 도약 명시 누락"
    assert "+54" in cat_section, "F 카테고리 +54 도약 명시 누락"
    print("[PASS] MILESTONE_R100.md: 8 카테고리 + E(+37%p) / F(+54%p) 큰 도약 강조")

    # 5. R100+ 잔여 4 옵션
    rem_idx = ms.find("## 3. 잔여 큰 덩어리")
    rem = ms[rem_idx:ms.find("## 4.")]
    for opt in ["옵션 A", "옵션 B", "옵션 C", "옵션 D"]:
        assert opt in rem, f"잔여 {opt} 누락"
    # 이론 천장 ≈ 88%
    assert "88." in rem, "이론 천장 88% 명시 누락"
    print("[PASS] MILESTONE_R100.md: R100+ 잔여 4 옵션 (A/B/C/D) + 이론 천장 명시")

    # 6. 핵심 RE 사실 (HSI, TEM, DES, Save, Toast, Mute)
    facts_idx = ms.find("## 5. 핵심 RE")
    facts = ms[facts_idx:]
    for keyword in ["HeroSkillInfo", "TEM", "DES blocker", "Save round-trip 31 필드",
                     "Toast severity", "Mute 4 layer"]:
        assert keyword in facts, f"핵심 사실 {keyword!r} 누락"
    print("[PASS] MILESTONE_R100.md: 핵심 RE 6 사실 (HSI / TEM / DES / Save / Toast / Mute)")

    # 7. PROGRESS.md / SESSION_HANDOFF.md 인용 (cross-link)
    assert "PROGRESS.md" in ms, "PROGRESS.md 링크 누락"
    assert "SESSION_HANDOFF.md" in ms, "SESSION_HANDOFF.md 링크 누락"
    print("[PASS] MILESTONE_R100.md: PROGRESS / SESSION_HANDOFF cross-link")

    # 8. R99 회귀 (Mute 체크박스)
    sp = (GODOT / "scripts/ui/settings_panel.gd").read_text(encoding='utf-8')
    tscn = (GODOT / "scenes/settings_panel.tscn").read_text(encoding='utf-8')
    assert "func sync_mute_check(state: bool)" in sp
    assert "MuteCheck" in tscn
    print("[PASS] R99 회귀: SettingsPanel Mute 체크박스 + sync_mute_check")

    # 9. R98 회귀
    am = (GODOT / "scripts/core/audio_manager.gd").read_text(encoding='utf-8')
    for fn in ["func is_muted()", "func set_muted(", "func toggle_mute()"]:
        assert fn in am
    print("[PASS] R98 회귀: AudioManager mute 3 API")

    # 10. R97 회귀
    assert "static func slider_to_db(v: float) -> float:" in am
    print("[PASS] R97 회귀: slider_to_db")

    # 11. R96 회귀 (Toast severity migration)
    demo = (GODOT / "scripts/ui/demo.gd").read_text(encoding='utf-8')
    assert demo.count('preload("res://scripts/ui/toast.gd").show_msg(') == 0
    print("[PASS] R96 회귀: Toast 마이그레이션 (preload 0)")

    # 12. R91 회귀 (round-trip)
    gs = (GODOT / "scripts/core/game_state.gd").read_text(encoding='utf-8')
    assert "skill_levels[int(k)] = int(sl_raw[k])" in gs
    print("[PASS] R91 회귀: save round-trip")

    # 13. 누적 라인업 헤더 ASCII 박스
    assert "─" in lineup or "-----" in lineup, "ASCII 박스 구분 누락"
    assert "+13" in lineup, "라인업 끝의 누적 합계 표기 누락"
    print("[PASS] MILESTONE_R100.md 라인업: ASCII 박스 + 누적 합계 표기")

    # 14. 이론 천장 산출 표기 (R100+ 4 옵션 합산)
    assert "88." in ms, "이론 천장 ≈ 88.X% 산출 누락"
    print("[PASS] MILESTONE_R100.md: 이론 천장 ≈ 88% 산출 표기")

    # 15. R100 docstring marker (PROGRESS / SESSION_HANDOFF 갱신은 별도)
    # MILESTONE 문서 자체에 R100 명시
    assert "Round 100" in ms or "R100" in ms, "R100 마커 누락"
    print("[PASS] MILESTONE_R100.md: R100 마커")

    print("\n[R100 ALL PASSED] 15/15")


if __name__ == "__main__":
    main()
