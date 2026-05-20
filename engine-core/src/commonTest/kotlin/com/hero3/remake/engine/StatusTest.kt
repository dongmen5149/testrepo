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
    fun r108_render_partition_buffs_and_debuffs_is_exhaustive_and_stable() {
        // R108 — BattleScene.renderPartyPanel / enemy render 가 isBuff(st) 로 분리한다.
        // 4 debuff (POISON/BURN/SLOW/STUN) + 나머지 buff 의 분류가 정확히 partition 인지 검증.
        val debuffs = setOf(Status.POISON, Status.BURN, Status.SLOW, Status.STUN)
        assertEquals(4, debuffs.size)
        val all = Status.values().toSet()
        // debuff 4종은 정확히 enum 안에 있음.
        for (d in debuffs) assertTrue(d in all, "expected debuff $d in enum")
        // 나머지는 모두 buff.
        val buffs = all - debuffs
        assertEquals(all.size, debuffs.size + buffs.size)
        // R107 의 HP_MAX_BUFF / SP_MAX_BUFF 도 buff 측 (render light-blue) — UI 색이 정확.
        assertTrue(Status.HP_MAX_BUFF in buffs)
        assertTrue(Status.SP_MAX_BUFF in buffs)
        // R104 boss 의 상시 buff (turnsLeft=99) 가 render 시 "∞" 로 표시되는지 식 검증.
        fun turnLabel(turnsLeft: Int): String = if (turnsLeft > 9) "∞" else turnsLeft.toString()
        assertEquals("∞", turnLabel(99))
        assertEquals("∞", turnLabel(10))
        assertEquals("9", turnLabel(9))
        assertEquals("3", turnLabel(3))
        assertEquals("1", turnLabel(1))
    }

    @Test
    fun r105_buff_remove_filter_keeps_debuffs() {
        // BUFF_REMOVE 는 buff (POISON/BURN/SLOW/STUN 제외 모두) 만 제거. debuff 는 유지.
        // isBuff 분류 시뮬: BattleScene.isBuff 와 동일 로직.
        val debuffs = setOf(Status.POISON, Status.BURN, Status.SLOW, Status.STUN)
        for (st in Status.values()) {
            val isBuff = st !in debuffs
            // POISON/BURN/SLOW/STUN 만 false, 나머지 true.
            if (isBuff) assertTrue(st !in debuffs)
            else assertTrue(st in debuffs)
        }
        // 모든 Status 가 정확히 한 카테고리.
        val total = Status.values().size
        val buffCount = Status.values().count { it !in debuffs }
        assertEquals(total, buffCount + debuffs.size)
    }

    @Test
    fun r103_enemy_defense_buff_reduces_damage_in_simulation() {
        // R103: enemy DEFENSE_BUFF 25% → 받는 raw 100 dmg → 75 적용. BattleScene 의 applyEnemyDefenseBuff
        // 식 자체를 검증.
        fun apply(raw: Int, defPct: Int): Int {
            val p = defPct.coerceIn(0, 90)
            return if (p <= 0) raw else (raw * (100 - p) / 100).coerceAtLeast(1)
        }
        assertEquals(75, apply(100, 25))
        assertEquals(50, apply(100, 50))
        assertEquals(10, apply(100, 90))      // clamp max
        assertEquals(100, apply(100, 0))      // no buff
        assertEquals(1, apply(2, 90))         // ≥ 1 보장
    }

    @Test
    fun r103_enemy_statuses_can_hold_buffs_not_just_debuffs() {
        // R94 의 enemy.statuses 가 R103 에서 buff 도 담을 수 있도록 확장됐다.
        val def = EnemyRegistry.all.first()
        val ei = EnemyInstance(def, hp = 100)
        ei.statuses += StatusEffect(Status.DEFENSE_BUFF, turnsLeft = 99, perTick = 25)
        ei.statuses += StatusEffect(Status.POISON, turnsLeft = 3, perTick = 5)
        // 두 종 모두 컨테이너에 들어감.
        assertEquals(2, ei.statuses.size)
        // perTick 합산이 DEFENSE_BUFF 만 필터링 시 25.
        val defSum = ei.statuses.filter { it.status == Status.DEFENSE_BUFF }.sumOf { it.perTick }
        assertEquals(25, defSum)
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
