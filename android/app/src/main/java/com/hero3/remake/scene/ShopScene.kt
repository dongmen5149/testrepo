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
import com.hero3.remake.engine.ItemKind
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

    // R80: "region_shop_N" 패턴 시 R74 의 5 catalog shops 사용. 그 외는 기존 ShopRegistry.
    private val stock: List<Item> = regionShopStock(npcId) ?: ShopRegistry.stock(npcId, gameState)
    private val inventory: Inventory = gameState.loadInventory()

    private fun regionShopStock(id: String): List<Item>? {
        if (!id.startsWith("region_shop_")) return null
        val idx = id.removePrefix("region_shop_").toIntOrNull() ?: return null
        val catalog = com.hero3.remake.catalog.Hero3CatalogProvider.get() ?: return null
        val items = com.hero3.remake.catalog.Hero3CatalogBridge.shopStockFromCatalog(catalog, idx)
        return items.takeIf { it.isNotEmpty() }
    }
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
            flash(settings.lang("골드가 부족합니다.", "Not enough gold."))
            return
        }
        gameState.gold -= item.price
        inventory.add(item.id, 1)
        gameState.saveInventory(inventory)
        flash(settings.lang("${item.nameKo} 구입.", "Bought ${item.nameEn}."))
    }

    private fun trySell() {
        val slot = inventory.get(cursor) ?: return
        val item = ItemRegistry.get(slot.itemId) ?: return
        if (item.kind == ItemKind.KEY) {
            flash(settings.lang("열쇠 아이템은 판매 불가.", "Cannot sell key items."))
            return
        }
        val price = ShopRegistry.sellPrice(item)
        gameState.gold += price
        inventory.remove(cursor, 1)
        gameState.saveInventory(inventory)
        if (cursor >= inventory.size && cursor > 0) cursor--
        flash(settings.lang("${item.nameKo} 판매 (+${price}G).",
                            "Sold ${item.nameEn} (+${price}G)."))
    }

    private fun flash(s: String) { message = s; messageTtl = 1500L }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val title = npc?.let { settings.lang(it.nameKo, it.nameEn) } ?: "SHOP"
        UiKit.drawHeader(canvas, virtualWidth, title)

        // 탭 + 골드
        val buyLabel  = settings.lang("구입", "BUY")
        val sellLabel = settings.lang("판매", "SELL")
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
                    canvas.drawText(settings.lang("(재고 없음)", "(out of stock)"),
                        16f, listTop + 12f, UiKit.muted)
                }
                val end = minOf(stock.size, scrollStart + visibleRows)
                for (i in scrollStart until end) {
                    val item = stock[i]
                    val y = listTop + (i - scrollStart) * rowH + 12f
                    if (i == cursor) {
                        canvas.drawRect(10f, y - 11f, virtualWidth - 18f, y + 2f, rowSelected)
                    }
                    canvas.drawText(settings.lang(item.nameKo, item.nameEn), 16f, y, UiKit.body)
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
                    canvas.drawText(settings.lang("(비어 있음)", "(empty)"),
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
                    val name = settings.lang(item.nameKo, item.nameEn)
                    canvas.drawText("$name ×${slot.count}", 16f, y, UiKit.body)
                    canvas.drawText("${ShopRegistry.sellPrice(item)} G", virtualWidth - 60f, y, UiKit.body)
                }
                if (slots.size > visibleRows) {
                    canvas.drawText("${cursor + 1}/${slots.size}",
                        virtualWidth - 36f, listTop + visibleRows * rowH + 4f, UiKit.muted)
                }
            }
        }

        // 선택된 아이템 설명 (메시지 영역과 동일 위치, 메시지 우선)
        if (messageTtl > 0 && message.isNotEmpty()) {
            UiKit.drawBox(canvas, 8f, virtualHeight - 60f, virtualWidth - 16f, 22f)
            canvas.drawText(message, 14f, virtualHeight - 46f, UiKit.body)
        } else {
            val descItem: Item? = when (mode) {
                Mode.BUY -> stock.getOrNull(cursor)
                Mode.SELL -> inventory.get(cursor)?.let { ItemRegistry.get(it.itemId) }
            }
            if (descItem != null) {
                UiKit.drawBox(canvas, 8f, virtualHeight - 60f, virtualWidth - 16f, 22f)
                val d = settings.lang(descItem.descKo, descItem.descEn)
                if (d.isNotEmpty()) canvas.drawText(d, 14f, virtualHeight - 46f, UiKit.muted)
            }
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "L tab  OK ${settings.lang("거래", "trade")}  R back")
    }
}
