package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Inventory
import com.hero3.remake.engine.Item
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.NpcRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.ShopRegistry
import com.hero3.remake.engine.UiKit

/**
 * 상점 — 매도(BUY) / 매입(SELL) 탭.
 *
 * UP/DOWN 으로 행 이동, OK = 1개 거래, SOFT1 = BUY/SELL 탭 전환, SOFT2 = 닫기.
 */
class ShopScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val npcId: String,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private enum class Mode { BUY, SELL }
    private var mode = Mode.BUY
    private var cursor = 0
    private var message: String = ""
    private var messageTtl = 0L

    private val stock: List<Item> = ShopRegistry.stock(npcId, gameState)
    private val inventory: Inventory = gameState.loadInventory()
    private val npc = NpcRegistry.forMap(0).firstOrNull { it.id == npcId }
        ?: NpcRegistry.forMap(1).firstOrNull { it.id == npcId }

    private val bg = Paint().apply { color = Color.rgb(20, 18, 30) }
    private val rowSelected = Paint().apply { color = Color.argb(120, 255, 220, 90) }
    private val goldPaint = Paint(UiKit.body).apply { color = Color.rgb(255, 220, 90) }

    private fun rowsCount(): Int = if (mode == Mode.BUY) stock.size else inventory.size

    override fun update(deltaMs: Long) {
        if (messageTtl > 0) messageTtl -= deltaMs

        if (input.pressedOnce(InputController.K_SOFT2)) {
            onRequest(MainActivity.SceneRequest.Pop)
            return
        }
        if (input.pressedOnce(InputController.K_SOFT1)) {
            mode = if (mode == Mode.BUY) Mode.SELL else Mode.BUY
            cursor = 0
            return
        }
        val n = rowsCount()
        if (n > 0) {
            if (input.pressedOnce(InputController.K_UP))   cursor = (cursor - 1 + n) % n
            if (input.pressedOnce(InputController.K_DOWN)) cursor = (cursor + 1) % n
        }
        if (input.pressedOnce(InputController.K_OK)) {
            when (mode) {
                Mode.BUY  -> tryBuy()
                Mode.SELL -> trySell()
            }
        }
    }

    private fun tryBuy() {
        val item = stock.getOrNull(cursor) ?: return
        if (gameState.gold < item.price) {
            flash(if (settings.language == "en") "Not enough gold." else "골드가 부족합니다.")
            return
        }
        gameState.gold -= item.price
        inventory.add(item.id, 1)
        gameState.saveInventory(inventory)
        flash(if (settings.language == "en") "Bought ${item.nameEn}." else "${item.nameKo} 구입.")
    }

    private fun trySell() {
        val slot = inventory.get(cursor) ?: return
        val item = ItemRegistry.get(slot.itemId) ?: return
        if (item.kind == com.hero3.remake.engine.ItemKind.KEY) {
            flash(if (settings.language == "en") "Cannot sell key items." else "열쇠 아이템은 판매 불가.")
            return
        }
        val price = ShopRegistry.sellPrice(item)
        gameState.gold += price
        inventory.remove(cursor, 1)
        gameState.saveInventory(inventory)
        if (cursor >= inventory.size && cursor > 0) cursor--
        flash(if (settings.language == "en") "Sold ${item.nameEn} (+${price}G)."
              else "${item.nameKo} 판매 (+${price}G).")
    }

    private fun flash(s: String) { message = s; messageTtl = 1500L }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val isEn = settings.language == "en"
        val title = (if (isEn) npc?.nameEn else npc?.nameKo) ?: "SHOP"
        UiKit.drawHeader(canvas, virtualWidth, title)

        // 탭 + 골드
        val buyLabel  = if (isEn) "BUY"  else "구입"
        val sellLabel = if (isEn) "SELL" else "판매"
        UiKit.drawMenuItem(canvas, 8f, 28f, 60f, 18f, buyLabel,  mode == Mode.BUY)
        UiKit.drawMenuItem(canvas, 72f, 28f, 60f, 18f, sellLabel, mode == Mode.SELL)
        canvas.drawText("${gameState.gold} G", virtualWidth - 60f, 42f, goldPaint)

        // 목록
        val listTop = 56f
        val rowH = 14f
        val visibleRows = 12
        UiKit.drawBox(canvas, 8f, listTop - 4f, virtualWidth - 16f, rowH * visibleRows + 8f)
        val scrollStart = (cursor - visibleRows + 1).coerceAtLeast(0)
        when (mode) {
            Mode.BUY -> {
                if (stock.isEmpty()) {
                    canvas.drawText(if (isEn) "(out of stock)" else "(재고 없음)",
                        16f, listTop + 12f, UiKit.muted)
                }
                val end = minOf(stock.size, scrollStart + visibleRows)
                for (i in scrollStart until end) {
                    val item = stock[i]
                    val y = listTop + (i - scrollStart) * rowH + 12f
                    if (i == cursor) {
                        canvas.drawRect(10f, y - 11f, virtualWidth - 18f, y + 2f, rowSelected)
                    }
                    val name = if (isEn) item.nameEn else item.nameKo
                    canvas.drawText(name, 16f, y, UiKit.body)
                    canvas.drawText("${item.price} G", virtualWidth - 60f, y, UiKit.body)
                }
                if (stock.size > visibleRows) {
                    canvas.drawText("${cursor + 1}/${stock.size}",
                        virtualWidth - 36f, listTop + visibleRows * rowH + 4f, UiKit.muted)
                }
            }
            Mode.SELL -> {
                val slots = inventory.all()
                if (slots.isEmpty()) {
                    canvas.drawText(if (isEn) "(empty)" else "(비어 있음)",
                        16f, listTop + 12f, UiKit.muted)
                }
                val end = minOf(slots.size, scrollStart + visibleRows)
                for (i in scrollStart until end) {
                    val slot = slots[i]
                    val item = ItemRegistry.get(slot.itemId) ?: continue
                    val y = listTop + (i - scrollStart) * rowH + 12f
                    if (i == cursor) {
                        canvas.drawRect(10f, y - 11f, virtualWidth - 18f, y + 2f, rowSelected)
                    }
                    val name = if (isEn) item.nameEn else item.nameKo
                    canvas.drawText("$name ×${slot.count}", 16f, y, UiKit.body)
                    canvas.drawText("${ShopRegistry.sellPrice(item)} G", virtualWidth - 60f, y, UiKit.body)
                }
                if (slots.size > visibleRows) {
                    canvas.drawText("${cursor + 1}/${slots.size}",
                        virtualWidth - 36f, listTop + visibleRows * rowH + 4f, UiKit.muted)
                }
            }
        }

        // 메시지
        if (messageTtl > 0 && message.isNotEmpty()) {
            UiKit.drawBox(canvas, 8f, virtualHeight - 60f, virtualWidth - 16f, 22f)
            canvas.drawText(message, 14f, virtualHeight - 46f, UiKit.body)
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "L tab  OK ${if (isEn) "trade" else "거래"}  R back")
    }
}
