package com.hero3.remake.engine

/**
 * 보물상자 — 맵 위의 고정 좌표에서 1회 한정 획득.
 * `_mp` extras 디코드 후 자동 생성으로 교체 예정.
 */
data class Chest(
    val id: String,
    val mapId: Int,
    val x: Int,
    val y: Int,
    val itemId: String,
    val count: Int = 1,
    val gold: Int = 0,
)

object ChestRegistry {
    val all: List<Chest> = listOf(
        Chest("chest_soltia_a", 0, 28, 8,  "potion_s", count = 3),
        Chest("chest_soltia_b", 0, 6,  6,  "herb",     count = 5),
        Chest("chest_outskirt", 1, 17, 11, "ether_s",  count = 2),
        Chest("chest_cave_a",   10, 14, 8, "potion_m", count = 1),
        Chest("chest_cave_b",   10, 2,  10, "sword_iron"),
        Chest("chest_chaos_a",  11, 9,  3, "armor_lthr"),
        Chest("chest_chaos_b",  11, 14, 12, "potion_l"),
        Chest("chest_chaos_g",  11, 2,  2, "potion_s", gold = 300),
    )
    fun forMap(mapId: Int): List<Chest> = all.filter { it.mapId == mapId }
    fun at(mapId: Int, x: Int, y: Int): Chest? =
        all.firstOrNull { it.mapId == mapId && it.x == x && it.y == y }
}
