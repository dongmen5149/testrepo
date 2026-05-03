package com.hero3.remake.engine

/**
 * NPC 별 상점 재고. id 는 NpcRegistry 의 npc id 와 일치.
 *
 * 가격은 ItemRegistry 의 item.price 를 그대로 사용. 매입은 50% 가.
 */
object ShopRegistry {
    /** 매도가 (NPC → 플레이어). gameState=null 이면 base 재고만. */
    fun stock(npcId: String, gameState: GameState? = null): List<Item> = when (npcId) {
        "merchant_bo" -> {
            val base = listOf("potion_s", "potion_m", "ether_s", "sword_iron", "armor_lthr", "herb")
            val tier2 = if (gameState?.isBossDefeated("boss_guardian") == true)
                listOf("potion_l", "ether_m", "sword_steel", "armor_chain", "ring_mana")
            else emptyList()
            val tier3 = if (gameState?.isBossDefeated("boss_chaos") == true)
                listOf("sword_holy", "armor_drag", "ring_dest")
            else emptyList()
            (base + tier2 + tier3).mapNotNull { ItemRegistry.get(it) }
        }
        "merchant_jin" -> listOf("potion_s", "potion_m", "potion_l", "ether_s", "ether_m")
            .mapNotNull { ItemRegistry.get(it) }
        else -> emptyList()
    }

    /** 플레이어 인벤토리에서 NPC 가 사 줄 가격 (item.price 의 절반, 0 이상). */
    fun sellPrice(item: Item): Int = (item.price / 2).coerceAtLeast(0)
}
