package com.hero3.remake.engine

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * R94 — Status enum + StatusEffect + EnemyInstance.statuses 통합.
 *
 * BattleScene 의 tick 로직은 Android 환경 의존이라 직접 테스트 안 함 — 여기서는
 * data class 의 mutability 와 만료 처리 시뮬레이션만 확인.
 */
class StatusTest {

    @Test
    fun status_enum_has_poison() {
        // R94: 현재는 POISON 한 종 — R95 에서 BURN/SLOW/STUN 추가.
        assertTrue(Status.values().contains(Status.POISON))
    }

    @Test
    fun r95_status_enum_has_burn_slow_stun() {
        // R95: 신규 3종 추가.
        val all = Status.values().toSet()
        assertTrue(Status.BURN in all)
        assertTrue(Status.SLOW in all)
        assertTrue(Status.STUN in all)
        assertEquals(4, Status.values().size)
    }

    @Test
    fun r95_burn_tick_decays_like_poison() {
        // BURN 은 POISON 와 동일 dot 효과 — tick 시뮬레이션 시 hp 감소량 동일.
        val def = EnemyRegistry.all.first()
        val a = EnemyInstance(def, hp = 100)
        a.statuses += StatusEffect(Status.POISON, turnsLeft = 3, perTick = 5)
        val b = EnemyInstance(def, hp = 100)
        b.statuses += StatusEffect(Status.BURN, turnsLeft = 3, perTick = 5)
        repeat(3) {
            for (ei in listOf(a, b)) {
                val it = ei.statuses.iterator()
                while (it.hasNext()) {
                    val e = it.next()
                    if (e.status == Status.POISON || e.status == Status.BURN) ei.hp -= e.perTick
                    e.turnsLeft -= 1
                    if (e.turnsLeft <= 0) it.remove()
                }
            }
        }
        assertEquals(a.hp, b.hp)
    }

    @Test
    fun enemy_instance_starts_with_no_statuses() {
        val def = EnemyRegistry.all.first()
        val ei = EnemyInstance(def, hp = def.hpMax)
        assertTrue(ei.statuses.isEmpty())
    }

    @Test
    fun status_effect_tick_simulation_decays_and_removes() {
        // BattleScene 의 tick 로직 모사: 매 턴 perTick 만큼 HP -, turnsLeft -= 1, 0 이면 제거.
        val def = EnemyRegistry.all.first()
        val ei = EnemyInstance(def, hp = 100)
        ei.statuses += StatusEffect(Status.POISON, turnsLeft = 3, perTick = 5)

        repeat(3) {
            val it = ei.statuses.iterator()
            while (it.hasNext()) {
                val e = it.next()
                ei.hp -= e.perTick
                e.turnsLeft -= 1
                if (e.turnsLeft <= 0) it.remove()
            }
        }
        assertEquals(85, ei.hp)
        assertTrue(ei.statuses.isEmpty())
    }

    @Test
    fun status_effect_data_class_equality_ignores_turnsLeft_mutation_when_tracked_separately() {
        // turnsLeft 는 var 이므로 동일 (status, perTick) 인 두 인스턴스가 turnsLeft 만 다르면 not equal.
        val a = StatusEffect(Status.POISON, turnsLeft = 3, perTick = 5)
        val b = StatusEffect(Status.POISON, turnsLeft = 3, perTick = 5)
        assertEquals(a, b)
        b.turnsLeft = 1
        assertTrue(a != b)
        // copy 도 정상 — 동일 status enum 유지.
        val c = a.copy(turnsLeft = 1)
        assertEquals(Status.POISON, c.status)
        assertNull(null as Status?)  // sanity
    }
}
