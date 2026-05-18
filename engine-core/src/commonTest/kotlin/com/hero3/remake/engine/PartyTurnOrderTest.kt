package com.hero3.remake.engine

import kotlin.test.Test
import kotlin.test.assertEquals

class PartyTurnOrderTest {

    private fun party(vararg hps: Pair<Int, Int>): List<Character> =
        hps.mapIndexed { i, (hp, hpMax) ->
            Character(
                id = "p$i", classId = "kei_berserker", level = 1,
                hp = hp, hpMax = hpMax, sp = 0, spMax = 0, exp = 0
            )
        }

    @Test fun firstAliveFromAllAlive() {
        val p = party(10 to 10, 10 to 10)
        assertEquals(0, PartyTurnOrder.firstAliveFrom(p, 0))
        assertEquals(1, PartyTurnOrder.firstAliveFrom(p, 1))
    }

    @Test fun firstAliveFromSkipsDead() {
        val p = party(0 to 10, 5 to 10)
        assertEquals(1, PartyTurnOrder.firstAliveFrom(p, 0))
    }

    @Test fun firstAliveFromWrapsAround() {
        val p = party(5 to 10, 0 to 10)
        // start=1 dead → wrap to 0
        assertEquals(0, PartyTurnOrder.firstAliveFrom(p, 1))
    }

    @Test fun firstAliveFromAllDeadReturnsZero() {
        val p = party(0 to 10, 0 to 10)
        assertEquals(0, PartyTurnOrder.firstAliveFrom(p, 0))
    }

    @Test fun firstAliveEmptyParty() {
        assertEquals(0, PartyTurnOrder.firstAliveFrom(emptyList(), 0))
    }

    @Test fun nextAliveAfterForward() {
        val p = party(10 to 10, 10 to 10, 10 to 10)
        assertEquals(1, PartyTurnOrder.nextAliveAfter(p, 0))
        assertEquals(2, PartyTurnOrder.nextAliveAfter(p, 1))
    }

    @Test fun nextAliveAfterEndOfRound() {
        val p = party(10 to 10, 10 to 10)
        assertEquals(-1, PartyTurnOrder.nextAliveAfter(p, 1))
    }

    @Test fun nextAliveAfterSkipsDead() {
        val p = party(10 to 10, 0 to 10, 10 to 10)
        assertEquals(2, PartyTurnOrder.nextAliveAfter(p, 0))
    }

    @Test fun nextAliveAfterAllRemainingDead() {
        val p = party(10 to 10, 0 to 10)
        assertEquals(-1, PartyTurnOrder.nextAliveAfter(p, 0))
    }

    @Test fun lowestHpAliveAllyByRatio() {
        // p0 = 5/10 (50%), p1 = 30/100 (30%) — p1 lower
        val p = party(5 to 10, 30 to 100)
        assertEquals(1, PartyTurnOrder.lowestHpAliveAlly(p))
    }

    @Test fun lowestHpSkipsDead() {
        val p = party(0 to 100, 50 to 100)
        assertEquals(1, PartyTurnOrder.lowestHpAliveAlly(p))
    }

    @Test fun lowestHpAllDeadReturnsFallback() {
        val p = party(0 to 10, 0 to 10)
        assertEquals(7, PartyTurnOrder.lowestHpAliveAlly(p, fallback = 7))
    }

    @Test fun aliveCountCounts() {
        assertEquals(0, PartyTurnOrder.aliveCount(emptyList()))
        assertEquals(2, PartyTurnOrder.aliveCount(party(10 to 10, 10 to 10)))
        assertEquals(1, PartyTurnOrder.aliveCount(party(10 to 10, 0 to 10)))
    }

    @Test fun roundSimulation() {
        // 3명 파티, 라운드 시뮬레이션
        val p = party(10 to 10, 10 to 10, 10 to 10)
        var actor = PartyTurnOrder.firstAliveFrom(p, 0)
        val order = mutableListOf<Int>()
        while (actor >= 0 && actor < p.size) {
            order.add(actor)
            actor = PartyTurnOrder.nextAliveAfter(p, actor)
        }
        assertEquals(listOf(0, 1, 2), order)
    }

    @Test fun roundSimulationWithMidPartyDead() {
        // p1 죽음 — 0, 2 만 행동
        val p = party(10 to 10, 0 to 10, 10 to 10)
        var actor = PartyTurnOrder.firstAliveFrom(p, 0)
        val order = mutableListOf<Int>()
        while (actor >= 0 && actor < p.size) {
            order.add(actor)
            actor = PartyTurnOrder.nextAliveAfter(p, actor)
        }
        assertEquals(listOf(0, 2), order)
    }
}
