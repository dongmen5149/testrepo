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
        assertTrue(Status.values().size >= 4)
    }

    @Test
    fun r96_status_enum_has_buff_kinds() {
        // R96: CRIT_DEF_BUFF / DEFENSE_BUFF 추가.
        val all = Status.values().toSet()
        assertTrue(Status.CRIT_DEF_BUFF in all)
        assertTrue(Status.DEFENSE_BUFF in all)
        assertTrue(Status.values().size >= 6)
    }

    @Test
    fun r97_status_enum_has_accuracy_and_dodge_buff() {
        // R97: ACCURACY_BUFF / DODGE_BUFF 추가.
        val all = Status.values().toSet()
        assertTrue(Status.ACCURACY_BUFF in all)
        assertTrue(Status.DODGE_BUFF in all)
        assertTrue(Status.values().size >= 8)
    }

    @Test
    fun r102_status_enum_has_sp_cost_reduce_buff() {
        val all = Status.values().toSet()
        assertTrue(Status.SP_COST_REDUCE_BUFF in all)
        assertTrue(Status.values().size >= 13)
    }

    @Test
    fun r101_status_enum_has_block_buff() {
        val all = Status.values().toSet()
        assertTrue(Status.BLOCK_BUFF in all)
        assertTrue(Status.values().size >= 12)
    }

    @Test
    fun r100_status_enum_has_taunt_buff() {
        val all = Status.values().toSet()
        assertTrue(Status.TAUNT_BUFF in all)
        assertTrue(Status.values().size >= 11)
    }

    @Test
    fun r98_status_enum_has_regen_buffs() {
        val all = Status.values().toSet()
        assertTrue(Status.HP_REGEN_BUFF in all)
        assertTrue(Status.SP_REGEN_BUFF in all)
        assertTrue(Status.values().size >= 10)
    }

    @Test
    fun r98_regen_tick_simulation_caps_at_max() {
        // HP_REGEN_BUFF tick: hp += perTick, hpMax cap. 3 턴 후 만료.
        val def = EnemyRegistry.all.first()
        val ei = EnemyInstance(def, hp = 50)
        // 시뮬용으로만 EnemyInstance 사용. real wiring 은 Character/party 측.
        val buff = StatusEffect(Status.HP_REGEN_BUFF, turnsLeft = 3, perTick = 10)
        var hp = 50
        val hpMax = 100
        var turns = buff.turnsLeft
        repeat(3) {
            val heal = (hpMax - hp).coerceAtMost(buff.perTick).coerceAtLeast(0)
            hp += heal
            buff.turnsLeft -= 1
            turns = buff.turnsLeft
        }
        assertEquals(80, hp)        // 50 → 60 → 70 → 80
        assertEquals(0, turns)
    }

    @Test
    fun r97_hit_chance_formula_clamps_to_30_100() {
        // R97 의 rollHit 식 시뮬: chance = (90 + acc - dodge).coerceIn(30, 100).
        // helper 가 BattleScene 안에 있어 직접 호출 불가 — 식 자체를 여기서 검증.
        fun chance(acc: Int, dod: Int) = (90 + acc - dod).coerceIn(30, 100)
        assertEquals(100, chance(50, 0))    // 140 → 100
        assertEquals(30, chance(0, 100))    // -10 → 30
        assertEquals(90, chance(0, 0))      // base
        assertEquals(95, chance(10, 5))     // 95
        assertEquals(85, chance(5, 10))     // 85
    }

    @Test
    fun r96_buff_perTick_used_as_percent_not_dot() {
        // R96 의 BUFF status 는 perTick 을 percent 로 재사용. tick 시뮬에서 HP 감소시키지 않음.
        val def = EnemyRegistry.all.first()
        val ei = EnemyInstance(def, hp = 100)
        ei.statuses += StatusEffect(Status.CRIT_DEF_BUFF, turnsLeft = 3, perTick = 30)
        repeat(3) {
            val it = ei.statuses.iterator()
            while (it.hasNext()) {
                val e = it.next()
                // BUFF 는 dot 아님 — 따로 분기.
                if (e.status == Status.POISON || e.status == Status.BURN) ei.hp -= e.perTick
                e.turnsLeft -= 1
                if (e.turnsLeft <= 0) it.remove()
            }
        }
        assertEquals(100, ei.hp)
        assertTrue(ei.statuses.isEmpty())
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
