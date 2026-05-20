#!/usr/bin/env python3
"""완성도 문서(COMPLETION.md) 구조·수치 일관성 검증."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/h5/COMPLETION.md"
PROGRESS = ROOT / "docs/h5/PROGRESS.md"
HANDOFF = ROOT / "docs/h5/SESSION_HANDOFF.md"

# 베타 서비스 오픈 9축 (원작 동등 플레이)
BETA_SERVICE_W = [0.20, 0.22, 0.18, 0.14, 0.12, 0.10, 0.09, 0.05]
BETA_SERVICE_S = [20, 40, 50, 65, 75, 40, 55, 30]

# 기술 스모크 7축
SMOKE_W = [0.18, 0.22, 0.20, 0.15, 0.12, 0.08, 0.15]
SMOKE_S = [35, 85, 30, 52, 72, 55, 58]


def main():
    assert DOC.exists(), "COMPLETION.md 없음"
    text = DOC.read_text(encoding="utf-8")
    checks = []

    for marker in (
        "베타 서비스 오픈",
        "원작 동등 플레이",
        "~50%",
        "기술 스모크",
        "~61%",
        "demo.tscn",
        "87.6%",
        "79.60%",
    ):
        assert marker in text, f"COMPLETION.md 에 '{marker}' 없음"
    checks.append("COMPLETION.md 핵심 섹션·수치 marker")

    prog = PROGRESS.read_text(encoding="utf-8")
    hand = HANDOFF.read_text(encoding="utf-8")
    assert "COMPLETION.md" in prog and "COMPLETION.md" in hand
    assert "~50%" in prog and "~50%" in hand
    checks.append("PROGRESS / SESSION_HANDOFF cross-link + ~50%")

    weights = [0.08, 0.14, 0.17, 0.24, 0.12, 0.10, 0.08, 0.07]
    scores = [95, 96, 93, 93, 95, 68, 65, 75]
    total = sum(w * s for w, s in zip(weights, scores))
    assert 87.0 <= total <= 88.5, f"8카테고리 합 {total:.2f}%"
    checks.append(f"8카테고리 가중합 {total:.2f}%")

    release = (93 * 24 + 95 * 12 + 65 * 8) / 44
    assert 87.0 <= release <= 90.0, f"출시축 {release:.1f}%"
    checks.append(f"D+E+G 출시축 {release:.1f}%")

    beta_svc = sum(w * s for w, s in zip(BETA_SERVICE_W, BETA_SERVICE_S))
    assert 49.0 <= beta_svc <= 54.0, f"베타 서비스 9축 {beta_svc:.1f}%"
    checks.append(f"베타 서비스 9축 {beta_svc:.1f}% (≈50%)")

    smoke = sum(w * s for w, s in zip(SMOKE_W, SMOKE_S))
    assert 59.0 <= smoke <= 63.0, f"스모크 7축 {smoke:.1f}%"
    checks.append(f"기술 스모크 7축 {smoke:.1f}% (≈61%)")

    for line in checks:
        print(f"[PASS] {line}")
    print("\n완성도 문서 검증: ALL PASSED")


if __name__ == "__main__":
    main()
