package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Inventory
import com.hero3.remake.engine.ItemKind
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * 인벤토리 — GameState 의 Inventory 를 5×4 슬롯 그리드로 표시.
 * 탭: 가방(전체/소비) / 장비(무기·방어구·악세) / 스킬(미구현).
 */
class InventoryScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
    startTab: Int = 0,
) : Scene {

    override val consumesPoundKey: Boolean = true
    private val tabs = listOf(R.string.txt_008, R.string.txt_009, R.string.txt_010)
    private var tabIdx = startTab.coerceIn(0, 2)
    private var slotIdx = 0
    private val cols = 5
    private val rows = 4
    private val totalSlots = cols * rows

    private val inventory: Inventory = gameState.loadInventory()
    private val party = gameState.loadParty().toMutableList()
    private val hero get() = party.getOrNull(0)

    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }
    private val slotEmpty = Paint().apply { color = Color.argb(120, 80, 80, 100) }
    private val slotFilled = Paint().apply { color = Color.argb(180, 60, 90, 130) }
    private val slotKey    = Paint().apply { color = Color.argb(180, 130, 80, 60) }
    private val slotEmptyBorder = Paint().apply {
        color = Color.argb(120, 140, 140, 160); style = Paint.Style.STROKE; strokeWidth = 1f
    }
    private val slotSelected = Paint().apply {
        color = Color.rgb(255, 220, 90); style = Paint.Style.STROKE; strokeWidth = 2f
    }
    private val countPaint = Paint(UiKit.body).apply {
        textSize = 9f; color = Color.rgb(255, 240, 180); textAlign = Paint.Align.RIGHT
    }
    private val itemNamePaint = Paint(UiKit.body).apply {
        textSize = 9f; color = Color.WHITE; textAlign = Paint.Align.CENTER
    }

    /** 현재 탭에 해당하는 아이템 슬롯 인덱스 (inventory.all() 기준).
     *  ItemRegistry 의 정의 순서로 정렬 → kind 그룹핑 + 일관된 노출. */
    private fun visibleSlots(): List<Int> {
        val all = inventory.all()
        val registryOrder = ItemRegistry.all.withIndex().associate { (idx, it) -> it.id to idx }
        return all.indices.filter { i ->
            val item = ItemRegistry.get(all[i].itemId) ?: return@filter false
            when (tabIdx) {
                0 -> item.kind == ItemKind.CONSUMABLE || item.kind == ItemKind.MATERIAL || item.kind == ItemKind.KEY
                1 -> item.kind == ItemKind.WEAPON || item.kind == ItemKind.ARMOR || item.kind == ItemKind.ACCESSORY
                else -> false
            }
        }.sortedBy { registryOrder[all[it].itemId] ?: Int.MAX_VALUE }
    }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2)) onRequest(MainActivity.SceneRequest.Pop)
        if (input.pressedOnce(InputController.K_SOFT1)) {
            tabIdx = (tabIdx + 1) % tabs.size
            slotIdx = 0
        }
        if (input.pressedOnce(InputController.K_LEFT))  slotIdx = (slotIdx - 1 + totalSlots) % totalSlots
        if (input.pressedOnce(InputController.K_RIGHT)) slotIdx = (slotIdx + 1) % totalSlots
        if (input.pressedOnce(InputController.K_UP))    slotIdx = (slotIdx - cols + totalSlots) % totalSlots
        if (input.pressedOnce(InputController.K_DOWN))  slotIdx = (slotIdx + cols) % totalSlots

        // # 키: 선택 아이템 1개 버리기 (가방 탭만, 열쇠 아이템은 제외)
        if (input.pressedOnce(InputController.K_POUND) && tabIdx == 0) {
            val visible = visibleSlots()
            val invIdx = visible.getOrNull(slotIdx)
            if (invIdx != null) {
                val slot = inventory.get(invIdx)
                val item = slot?.let { ItemRegistry.get(it.itemId) }
                if (item != null && item.kind != ItemKind.KEY) {
                    inventory.remove(invIdx, 1)
                    gameState.saveInventory(inventory)
                    com.hero3.remake.engine.EventBus.push(
                        if (settings.language == "en") "Dropped: ${item.nameEn}"
                        else "버림: ${item.nameKo}")
                }
            }
        }
        // OK: 탭별 동작
        if (input.pressedOnce(InputController.K_OK)) {
            val visible = visibleSlots()
            val invIdx = visible.getOrNull(slotIdx) ?: return
            val slot = inventory.get(invIdx) ?: return
            val item = ItemRegistry.get(slot.itemId) ?: return
            when (tabIdx) {
                0 -> if (item.kind == ItemKind.CONSUMABLE) {
                    val leader = hero
                    if (leader == null) return
                    val isEn = settings.language == "en"
                    val nm = if (isEn) item.nameEn else item.nameKo
                    when (item.id) {
                        "potion_s", "potion_m", "potion_l" -> {
                            if (leader.hp >= leader.hpMax) {
                                com.hero3.remake.engine.EventBus.push(
                                    if (isEn) "HP already full." else "HP 가 이미 최대입니다.")
                                return
                            }
                            val healed = (leader.hpMax - leader.hp).coerceAtMost(item.power)
                            leader.hp += healed
                            gameState.saveParty(party)
                            com.hero3.remake.engine.EventBus.push(
                                if (isEn) "$nm +$healed HP" else "$nm +$healed HP")
                        }
                        "ether_s", "ether_m" -> {
                            if (leader.sp >= leader.spMax) {
                                com.hero3.remake.engine.EventBus.push(
                                    if (isEn) "SP already full." else "SP 가 이미 최대입니다.")
                                return
                            }
                            val gained = (leader.spMax - leader.sp).coerceAtMost(item.power)
                            leader.sp += gained
                            gameState.saveParty(party)
                            com.hero3.remake.engine.EventBus.push(
                                if (isEn) "$nm +$gained SP" else "$nm +$gained SP")
                        }
                        else -> {
                            com.hero3.remake.engine.EventBus.push(
                                if (isEn) "Cannot use here." else "여기서 사용 불가.")
                            return
                        }
                    }
                    inventory.remove(invIdx, 1)
                    gameState.saveInventory(inventory)
                }
                1 -> {
                    val h = hero ?: return
                    when (item.kind) {
                        ItemKind.WEAPON    -> h.equipWeapon    = if (h.equipWeapon    == item.id) null else item.id
                        ItemKind.ARMOR     -> h.equipArmor     = if (h.equipArmor     == item.id) null else item.id
                        ItemKind.ACCESSORY -> h.equipAccessory = if (h.equipAccessory == item.id) null else item.id
                        else -> {}
                    }
                    gameState.saveParty(party)
                }
            }
        }
    }

    private fun isEquipped(itemId: String): Boolean {
        val h = hero ?: return false
        return h.equipWeapon == itemId || h.equipArmor == itemId || h.equipAccessory == itemId
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth, context.getString(R.string.txt_002))

        // 탭
        var x = 8f
        for ((i, t) in tabs.withIndex()) {
            UiKit.drawMenuItem(canvas, x, 28f, 70f, 18f, context.getString(t), i == tabIdx)
            x += 74f
        }
        // 슬롯 카운트
        val visCount = visibleSlots().size
        canvas.drawText("$visCount/$totalSlots", virtualWidth - 40f, 42f, UiKit.muted)

        val visible = visibleSlots()
        val isEn = settings.language == "en"

        val gridTop = 56f
        val slotSize = 36f
        val gap = 4f
        val gridW = cols * slotSize + (cols - 1) * gap
        val gridLeft = (virtualWidth - gridW) / 2f
        for (r in 0 until rows) {
            for (c in 0 until cols) {
                val sx = gridLeft + c * (slotSize + gap)
                val sy = gridTop + r * (slotSize + gap)
                val rect = android.graphics.RectF(sx, sy, sx + slotSize, sy + slotSize)
                val gridIdx = r * cols + c
                val invIdx = visible.getOrNull(gridIdx)
                val filled = invIdx != null
                val isKey = invIdx?.let {
                    ItemRegistry.get(inventory.get(it)?.itemId ?: "")?.kind == ItemKind.KEY
                } ?: false
                val fillP = when {
                    isKey -> slotKey
                    filled -> slotFilled
                    else -> slotEmpty
                }
                canvas.drawRoundRect(rect, 4f, 4f, fillP)
                canvas.drawRoundRect(rect, 4f, 4f, slotEmptyBorder)

                if (invIdx != null) {
                    val slot = inventory.get(invIdx)!!
                    val item = ItemRegistry.get(slot.itemId)
                    val short = (if (isEn) item?.nameEn else item?.nameKo) ?: slot.itemId
                    val label = if (short.length > 5) short.substring(0, 5) else short
                    canvas.drawText(label, sx + slotSize / 2f, sy + slotSize / 2f + 3f, itemNamePaint)
                    if (slot.count > 1) {
                        canvas.drawText("×${slot.count}", sx + slotSize - 3f, sy + slotSize - 3f, countPaint)
                    }
                    if (tabIdx == 1 && isEquipped(slot.itemId)) {
                        canvas.drawText("E", sx + 3f, sy + 11f, countPaint)
                    }
                }
                if (gridIdx == slotIdx) {
                    canvas.drawRoundRect(rect, 4f, 4f, slotSelected)
                }
            }
        }

        // 선택된 슬롯 정보
        UiKit.drawBox(canvas, 8f, virtualHeight - 60f, virtualWidth - 16f, 36f)
        val invIdx = visible.getOrNull(slotIdx)
        if (invIdx != null) {
            val slot = inventory.get(invIdx)!!
            val item = ItemRegistry.get(slot.itemId)
            val name = (if (isEn) item?.nameEn else item?.nameKo) ?: slot.itemId
            val desc = (if (isEn) item?.descEn else item?.descKo) ?: ""
            canvas.drawText("$name ×${slot.count}", 14f, virtualHeight - 44f, UiKit.body)
            canvas.drawText(desc, 14f, virtualHeight - 30f, UiKit.muted)
        } else {
            canvas.drawText(context.getString(R.string.txt_127), 14f, virtualHeight - 44f, UiKit.muted)
            canvas.drawText("Slot ${slotIdx + 1}/$totalSlots", 14f, virtualHeight - 30f, UiKit.muted)
        }

        val drop = if (tabIdx == 0) (if (isEn) "# drop  " else "# 버림  ") else ""
        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "L tab  $drop${context.getString(R.string.hint_dpad_navigate)}  ${context.getString(R.string.hint_back_cancel)}")
    }
}
