package com.hero3.remake.engine

/**
 * 멀티파티 전투 라운드 순서 계산 — Android 의존성 없는 pure 헬퍼.
 *
 * 라운드 = 살아있는(HP > 0) 모든 멤버가 파티 순서대로 1회씩 행동.
 * 마지막 살아있는 멤버 이후엔 적 턴.
 */
object PartyTurnOrder {

    /** start 부터 시작해 wrap-around 하지 않고 살아있는 첫 인덱스. 없으면 0. */
    fun firstAliveFrom(party: List<Character>, start: Int): Int {
        if (party.isEmpty()) return 0
        for (i in 0 until party.size) {
            val k = (start + i) % party.size
            if (party[k].hp > 0) return k
        }
        return 0
    }

    /** cur 다음 인덱스부터 살아있는 멤버. 없으면 -1 (라운드 끝). */
    fun nextAliveAfter(party: List<Character>, cur: Int): Int {
        for (i in cur + 1 until party.size) if (party[i].hp > 0) return i
        return -1
    }

    /** 살아있는 멤버 중 HP 비율(현재/최대) 가장 낮은 인덱스. 없으면 fallback 반환. */
    fun lowestHpAliveAlly(party: List<Character>, fallback: Int = 0): Int {
        var bestIdx = -1
        var bestRatio = Float.MAX_VALUE
        for ((i, c) in party.withIndex()) {
            if (c.hp <= 0) continue
            val r = c.hp.toFloat() / c.hpMax.coerceAtLeast(1)
            if (r < bestRatio) { bestRatio = r; bestIdx = i }
        }
        return if (bestIdx < 0) fallback else bestIdx
    }

    /** 살아있는 멤버 수. */
    fun aliveCount(party: List<Character>): Int = party.count { it.hp > 0 }
}
