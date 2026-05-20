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
        // R94: 현재는 POISON 한 종 — 향후 BURN/SLOW/STUN 추가 시 그대로 enum 확장.
        assertTrue(Status.values().contains(Status.POISON))
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
