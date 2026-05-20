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
}

/** 한 entity 위의 한 상태 이상 인스턴스 (turn-based decay). */
data class StatusEffect(
    val status: Status,
    var turnsLeft: Int,
    val perTick: Int,
)
