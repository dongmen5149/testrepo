package com.hero3.remake.engine

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertTrue

/**
 * R81 — region_shop NPCs 등록 검증.
 */
class NpcRegistryTest {

    @Test fun region_shop_npcs_registered_for_all_5_tiers() {
        for (idx in 0..4) {
            val id = "region_shop_$idx"
            val matches = (0..20).flatMap { NpcRegistry.forMap(it) }.filter { it.id == id }
            assertEquals(1, matches.size, "expected exactly 1 NPC with id=$id")
        }
    }

    @Test fun region_shop_npcs_have_korean_names() {
        for (idx in 0..4) {
            val id = "region_shop_$idx"
            val npc = (0..20).flatMap { NpcRegistry.forMap(it) }.firstOrNull { it.id == id }
            assertNotNull(npc)
            assertTrue(npc.nameKo.contains("상인"), "NPC $id name should contain 상인: ${npc.nameKo}")
        }
    }
}
