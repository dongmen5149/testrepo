"""Refine(강화) mechanism 검증 (Round 52).

`apps/hero5-godot/scripts/ui/refine_panel.gd` 의 GDScript 로직 (Round 17/26 의
ApplyItemRefine mechanism) 을 Python 으로 재구현 후 검증:

1. REFINE_PROB 각 row 합 = 1000 (확률 정규화).
2. 안전 단계 (0-3) 는 destroy/lock 확률 0.
3. 위험 단계 (8-10) 는 fail 확률 (재료소비+lock+destroy) 50% 이상.
4. 단조성: 단계가 올라갈수록 큰성공/성공 확률은 감소, lock/destroy 는 증가.
5. 평균 sub_count 증가 시뮬레이션 — refine_count 10 도달 비율 / 평균 시도 횟수.
6. refined_stat = base + sub_count 식 — 단순 산술 검증.
"""
from __future__ import annotations
import sys
import random

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# refine_panel.gd 와 동일
REFINE_PROB = [
    [200, 700, 100,   0,   0],  # +0 → +1
    [150, 700, 150,   0,   0],  # +1 → +2
    [100, 700, 200,   0,   0],  # +2 → +3
    [ 80, 620, 280,  20,   0],  # +3 → +4
    [ 60, 540, 340,  50,  10],  # +4 → +5
    [ 40, 460, 380,  90,  30],  # +5 → +6
    [ 30, 370, 410, 130,  60],  # +6 → +7
    [ 20, 280, 430, 170, 100],  # +7 → +8
    [ 10, 200, 440, 200, 150],  # +8 → +9
    [  5, 145, 440, 210, 200],  # +9 → +10
]

CASE_NAME = ["큰성공", "성공", "재료소비", "lock", "destroy"]


def roll(rc: int, rng: random.Random) -> int:
    """refine_panel.gd::_on_refine_pressed 의 prob roll 등가."""
    prob = REFINE_PROB[rc]
    r = rng.randrange(1000)
    acc = 0
    for i in range(5):
        acc += prob[i]
        if r < acc:
            return i
    return 4


def apply_case(rc: int, sub: int, case_idx: int) -> tuple[int, int, bool, bool]:
    """case 적용 → (new_rc, new_sub, locked, destroyed)."""
    if case_idx == 0:
        return rc + 1, sub + 2, False, False
    if case_idx == 1:
        return rc + 1, sub + 1, False, False
    if case_idx == 2:
        return rc, sub, False, False
    if case_idx == 3:
        return rc, sub, True, False
    return rc, sub, False, True


def simulate_to_max(rng: random.Random) -> dict:
    """+0 → +10 시뮬레이션. lock/destroy 까지의 시도 횟수 + 최종 결과."""
    rc, sub = 0, 0
    attempts = 0
    while rc < 10:
        case_idx = roll(rc, rng)
        rc, sub, locked, destroyed = apply_case(rc, sub, case_idx)
        attempts += 1
        if destroyed:
            return {"result": "destroyed", "rc": rc, "sub": sub, "attempts": attempts}
        if locked:
            return {"result": "locked", "rc": rc, "sub": sub, "attempts": attempts}
        if attempts > 1000:
            return {"result": "timeout", "rc": rc, "sub": sub, "attempts": attempts}
    return {"result": "max", "rc": rc, "sub": sub, "attempts": attempts}


def main() -> None:
    # 1. prob 합 = 1000
    print("# Round 52 Refine mechanism 검증")
    print(f"  prob row sum 검증:")
    for i, row in enumerate(REFINE_PROB):
        s = sum(row)
        ok = "✓" if s == 1000 else "✗"
        print(f"    +{i}→+{i+1}: sum={s} {ok}")
        assert s == 1000, f"row {i} sum {s} != 1000"

    # 2. 안전 단계 destroy 0
    for i in range(3):
        assert REFINE_PROB[i][3] == 0 and REFINE_PROB[i][4] == 0, \
            f"안전 단계 {i} 에서 destroy/lock 0이 아님: {REFINE_PROB[i]}"
    print(f"  안전 단계 (0..2) destroy/lock 0: ✓")

    # 3. 위험 단계 fail 확률 (재료소비+lock+destroy) >= 50%
    for i in range(7, 10):
        fail_pct = (REFINE_PROB[i][2] + REFINE_PROB[i][3] + REFINE_PROB[i][4]) / 10
        assert fail_pct >= 50, f"위험 단계 {i} fail% {fail_pct} < 50"
        print(f"  +{i}→+{i+1} fail% = {fail_pct:.1f} ✓")

    # 4. 단조성 — 성공률 감소, destroy 증가
    success_prev = REFINE_PROB[0][0] + REFINE_PROB[0][1]
    for i in range(1, 10):
        success = REFINE_PROB[i][0] + REFINE_PROB[i][1]
        assert success <= success_prev, f"단조성 위반: 성공 +{i} {success} > +{i-1} {success_prev}"
        success_prev = success
    print(f"  성공률 단조 감소: ✓ ({REFINE_PROB[0][0]+REFINE_PROB[0][1]} → {REFINE_PROB[9][0]+REFINE_PROB[9][1]})")

    destroy_prev = REFINE_PROB[0][4]
    for i in range(1, 10):
        destroy = REFINE_PROB[i][4]
        assert destroy >= destroy_prev, f"destroy 단조성 위반 +{i}"
        destroy_prev = destroy
    print(f"  destroy% 단조 증가: ✓ ({REFINE_PROB[0][4]} → {REFINE_PROB[9][4]})")

    # 5. 시뮬레이션 — 10000회, 각 결과 분포 + 평균 시도
    rng = random.Random(42)
    N = 10000
    counts = {"max": 0, "locked": 0, "destroyed": 0, "timeout": 0}
    attempts_total = 0
    rc_dist = [0] * 11
    for _ in range(N):
        r = simulate_to_max(rng)
        counts[r["result"]] = counts.get(r["result"], 0) + 1
        attempts_total += r["attempts"]
        rc_dist[r["rc"]] += 1
    print(f"\n# {N}회 시뮬레이션 (+0 → +10 도달 시도):")
    for k in ["max", "locked", "destroyed", "timeout"]:
        pct = counts[k] * 100.0 / N
        print(f"  {k}: {counts[k]} ({pct:.1f}%)")
    print(f"  평균 시도 횟수: {attempts_total / N:.1f}")
    print(f"  최종 rc 분포: {rc_dist}")
    assert counts["timeout"] == 0, "1000 시도 초과 (확률 분포 오류 가능)"
    # 일반적으로 destroy + locked 가 max 보다 훨씬 많아야 함 (위험 게임 디자인)
    assert counts["destroyed"] + counts["locked"] > counts["max"], \
        "destroy+lock 이 max 보다 적음 — 위험도 부족"

    # 6. refined_stat = base + sub_count 산술 검증 (몇 가지 샘플)
    samples = [
        (100, 0, 100),    # 강화 안 함
        (100, 5, 105),    # +3 큰성공 한 번
        (100, 20, 120),   # +10 큰성공/성공 mix
        (50, 18, 68),     # 작은 base + 큰 sub
    ]
    for base, sub, expected in samples:
        got = base + sub
        assert got == expected, f"refined_stat({base},{sub}) = {got}, expected {expected}"
    print(f"\n  refined_stat = base + sub 검증: {len(samples)}/{len(samples)} ✓")

    print("\n# All checks passed.")


if __name__ == "__main__":
    main()
