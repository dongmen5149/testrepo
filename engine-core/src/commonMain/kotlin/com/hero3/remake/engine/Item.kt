package com.hero3.remake.engine

/**
 * 아이템/장비/스킬 데이터 모델.
 *
 * 원본 _dat 에서 i0_dat / getitem_dat 등이 있으나 stat 매핑은 미해독.
 * 우선 placeholder ItemRegistry 로 인벤토리 UI 동작 검증 후 실 데이터 교체.
 */
enum class ItemKind { CONSUMABLE, WEAPON, ARMOR, ACCESSORY, KEY, MATERIAL }

data class Item(
    val id: String,
    val nameKo: String,
    val nameEn: String,
    val kind: ItemKind,
    val descKo: String = "",
    val descEn: String = "",
    val price: Int = 0,
    val power: Int = 0,
)

data class InventorySlot(
    val itemId: String,
    var count: Int,
)

object ItemRegistry {
    val all: List<Item> = listOf(
        Item("potion_s",   "회복약",      "Healing Potion",  ItemKind.CONSUMABLE,
             descKo = "HP 50 회복",  descEn = "Restores 50 HP",   price = 30,  power = 50),
        Item("potion_m",   "회복약+",     "Healing Potion+", ItemKind.CONSUMABLE,
             descKo = "HP 200 회복", descEn = "Restores 200 HP",  price = 100, power = 200),
        Item("ether_s",    "마나약",      "Mana Tonic",      ItemKind.CONSUMABLE,
             descKo = "SP 30 회복",  descEn = "Restores 30 SP",   price = 50,  power = 30),
        Item("sword_iron", "철검",        "Iron Sword",      ItemKind.WEAPON,
             descKo = "표준 검",     descEn = "Standard sword",   price = 200, power = 18),
        Item("armor_lthr", "가죽갑옷",    "Leather Armor",   ItemKind.ARMOR,
             descKo = "가벼운 방어구", descEn = "Light armor",     price = 150, power = 12),
        Item("ring_pwr",   "힘의반지",    "Ring of Power",   ItemKind.ACCESSORY,
             descKo = "STR +3",      descEn = "STR +3",           price = 500, power = 3),
        Item("key_soltia", "솔티아 열쇠", "Soltia Key",      ItemKind.KEY,
             descKo = "촌장의 집 열쇠", descEn = "Key to the elder's house"),
        Item("herb",       "약초",        "Herb",            ItemKind.MATERIAL,
             descKo = "재료",        descEn = "Crafting material", price = 5),
        // Tier 2 ---------------------------------
        Item("potion_l",   "회복약++",    "Healing Potion++",ItemKind.CONSUMABLE,
             descKo = "HP 500 회복", descEn = "Restores 500 HP",  price = 400, power = 500),
        Item("ether_m",    "마나약+",     "Mana Tonic+",     ItemKind.CONSUMABLE,
             descKo = "SP 100 회복", descEn = "Restores 100 SP",  price = 250, power = 100),
        Item("sword_steel","강철검",      "Steel Sword",     ItemKind.WEAPON,
             descKo = "강력한 검",   descEn = "Strong sword",     price = 800, power = 32),
        Item("armor_chain","사슬갑옷",    "Chain Mail",      ItemKind.ARMOR,
             descKo = "튼튼한 방어구", descEn = "Sturdy armor",   price = 700, power = 22),
        Item("ring_mana",  "마나반지",    "Ring of Mana",    ItemKind.ACCESSORY,
             descKo = "INT +5",      descEn = "INT +5",           price = 1200, power = 5),
        // Tier 3 ---------------------------------
        Item("sword_holy", "성검",        "Holy Sword",      ItemKind.WEAPON,
             descKo = "신성한 검",   descEn = "Sacred sword",     price = 2500, power = 56),
        Item("armor_drag", "용비늘갑옷",  "Dragon Scale",    ItemKind.ARMOR,
             descKo = "용의 비늘",   descEn = "Dragon scales",    price = 2200, power = 38),
        Item("ring_dest",  "운명반지",    "Ring of Destiny", ItemKind.ACCESSORY,
             descKo = "STR +8",      descEn = "STR +8",           price = 3500, power = 8),
    )
    /** R82 — catalog 등 외부에서 추가 등록되는 items. registerExtra() 로 갱신. */
    private val extras: MutableMap<String, Item> = mutableMapOf()
    private val byId = all.associateBy { it.id }

    fun get(id: String): Item? = byId[id] ?: extras[id]

    /** [extra] items 를 추가 등록. 동일 id 는 마지막 등록이 우선. R82 — Hero3CatalogBridge 사용. */
    fun registerExtra(items: List<Item>) {
        for (it in items) extras[it.id] = it
    }

    /** R82 — base + extras 합친 전체 (UI/forge name 매칭용). */
    fun allWithExtras(): List<Item> = all + extras.values
}

/** 단일 파티 인벤토리 (가방). 슬롯 순서 유지. */
class Inventory(initial: List<InventorySlot> = emptyList()) {
    private val slots: MutableList<InventorySlot> = initial.toMutableList()
    val size: Int get() = slots.size

    fun all(): List<InventorySlot> = slots.toList()
    fun get(index: Int): InventorySlot? = slots.getOrNull(index)
    fun isFull(): Boolean = slots.size >= MAX_SLOTS

    /** @return true 면 추가 성공. 가방이 가득 차고 새 슬롯이 필요하면 false. */
    fun add(itemId: String, count: Int = 1): Boolean {
        val existing = slots.firstOrNull { it.itemId == itemId }
        if (existing != null) { existing.count += count; return true }
        if (slots.size >= MAX_SLOTS) return false
        slots.add(InventorySlot(itemId, count))
        return true
    }

    fun remove(index: Int, count: Int = 1): Boolean {
        val s = slots.getOrNull(index) ?: return false
        s.count -= count
        if (s.count <= 0) slots.removeAt(index)
        return true
    }

    /** 새 게임 시작 시 기본 보급. */
    companion object {
        const val MAX_SLOTS = 20
        fun starter(): Inventory = Inventory().apply {
            add("potion_s", 5)
            add("ether_s", 2)
            add("sword_iron", 1)
            add("armor_lthr", 1)
            add("herb", 3)
        }
    }
}
