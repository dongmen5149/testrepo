package com.hero3.remake.engine

/**
 * R94/R95 — 전투 중 적/아군에게 부여되는 상태 이상.
 *
 * Hero3 catalog skill effectV2 의 `nDebuffs > 0` 인 skill 을 사용했을 때 BattleScene
 * 이 대상에게 부여한다. 매 턴 시작 시 [StatusEffect.perTick] 만큼 효과 적용 +
 * `turnsLeft` 감소, 0 도달 시 제거.
 *
 * R95: BURN/SLOW/STUN 3종 추가.
 */
enum class Status {
    /** 매 턴 시작 시 HP -[StatusEffect.perTick]. */
    POISON,
    /** 매 턴 시작 시 HP -[StatusEffect.perTick] (POISON 와 효과 동일, 별개 stack). */
    BURN,
    /** 적 행동 50% skip. perTick 미사용. */
    SLOW,
    /** 적 행동 100% skip. perTick 미사용. */
    STUN,
    /**
     * R96 — 받는 crit 데미지 감쇄 buff. perTick = percent (예: 30 → crit ×1.7 → ×1.4).
     * BattleScene 이 적 공격 결과에서 합산하여 multiplier 차감.
     */
    CRIT_DEF_BUFF,
    /**
     * R96 — 받는 데미지 reduction buff. perTick = percent (예: 20 → 받는 데미지 ×0.8).
     * BattleScene.doEnemyAttack 가 최종 데미지에 곱셈 적용.
     */
    DEFENSE_BUFF,
}

/** 한 entity 위의 한 상태 이상 인스턴스 (turn-based decay). */
data class StatusEffect(
    val status: Status,
    var turnsLeft: Int,
    val perTick: Int,
)
