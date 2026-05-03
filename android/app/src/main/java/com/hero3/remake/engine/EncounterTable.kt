package com.hero3.remake.engine

/**
 * 맵별 랜덤 인카운터 — 이동 시 일정 확률로 BattleScene 트리거.
 *
 * `_scn` / `_mp` 의 진짜 인카운터 테이블이 디코드되면 이 휴리스틱을 교체.
 */
object EncounterTable {

    data class Encounter(val rate: Float, val pool: List<String>)

    private val byMap: Map<Int, Encounter> = mapOf(
        // map0 (NEOSOLTIA) — 마을이라 인카운터 없음
        1 to Encounter(0.10f, listOf("thief", "soltian_rogue", "soltian_warrior")),
        10 to Encounter(0.15f, listOf("askran_guard", "corvus_warrior", "askran_warrior",
                                      "askran_templar", "corvus_assassin")),
        11 to Encounter(0.20f, listOf("askran_templar", "corvus_assassin", "askran_chaser")),
        12 to Encounter(0.25f, listOf("corvus_assassin", "askran_templar", "askran_chaser")),
    )

    fun shouldEncounter(mapId: Int, rng: Float): Boolean {
        val e = byMap[mapId] ?: return false
        return rng < e.rate
    }

    fun rollEnemy(mapId: Int): EnemyDef? {
        val e = byMap[mapId] ?: return null
        val id = e.pool.random()
        return EnemyRegistry.get(id)
    }
}
