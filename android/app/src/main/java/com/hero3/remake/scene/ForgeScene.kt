package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.catalog.Hero3CatalogBridge
import com.hero3.remake.catalog.Hero3CatalogProvider
import com.hero3.remake.engine.EventBus
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * R81 — 단조(forge) scene.
 *
 * R74 의 80 recipes 를 화면에 표시하고, 사용자가 OK 로 선택 시 input 들이 인벤토리에
 * 있으면 소비 + output 추가. 실제 crafting tx 가 첫 동작하는 scene.
 *
 * Hero3 catalog item ↔ engine-core Item 매핑은 cleanName 기반.
 * ItemRegistry 에 동일 이름 entry 가 없으면 craft 불가 (다음 라운드 mapping 확장).
 *
 * R74 catalog 가 install 되어 있어야 함. 없으면 빈 list + 안내 메시지.
 */
class ForgeScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val isEn: Boolean get() = settings.isEn
    private fun lang(ko: String, en: String): String = settings.lang(ko, en)

    private val recipes = Hero3CatalogProvider.get()?.let {
        Hero3CatalogBridge.forgeRecipesFromCatalog(it)
    } ?: emptyList()

    private var cursor = 0
    private var scroll = 0
    private val rowsVisible = 9

    private val bg = Paint().apply { color = Color.rgb(20, 18, 30) }
    private val rowSelected = Paint().apply { color = Color.argb(120, 255, 220, 90) }
    private val titlePaint = Paint(UiKit.body).apply { color = Color.rgb(255, 230, 120) }
    private val msgPaint = Paint(UiKit.body).apply { color = Color.rgb(200, 240, 200) }
    private val errPaint = Paint(UiKit.body).apply { color = Color.rgb(240, 160, 160) }

    private var message: String = ""
    private var messageIsError: Boolean = false
    private var messageTtl: Long = 0L

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2)) { onRequest(MainActivity.SceneRequest.Pop); return }
        if (recipes.isEmpty()) return

        if (input.pressedOnce(InputController.K_UP))   cursor = (cursor - 1 + recipes.size) % recipes.size
        if (input.pressedOnce(InputController.K_DOWN)) cursor = (cursor + 1) % recipes.size

        // scroll window
        if (cursor < scroll) scroll = cursor
        if (cursor >= scroll + rowsVisible) scroll = cursor - rowsVisible + 1

        if (input.pressedOnce(InputController.K_OK)) attemptCraft()

        if (messageTtl > 0) {
            messageTtl -= deltaMs
            if (messageTtl <= 0) message = ""
        }
    }

    private fun attemptCraft() {
        val r = recipes.getOrNull(cursor) ?: return
        val output = r.output
        if (output == null) {
            showMsg(lang("이 레시피는 출력 미정.", "Recipe output missing."), error = true); return
        }
        // engine-core ItemRegistry 의 동일 이름 item id 매핑
        val outItem = ItemRegistry.allWithExtras().firstOrNull { it.nameKo == output.cleanName }
        if (outItem == null) {
            showMsg(lang("출력 '${output.cleanName}' 가 인벤토리 정의에 없음.",
                          "Output '${output.cleanName}' not in inventory registry."), error = true)
            return
        }
        // 입력 인벤토리 확인
        val inv = gameState.loadInventory()
        val inputIds = r.inputs.mapNotNull { ref ->
            ItemRegistry.allWithExtras().firstOrNull { it.nameKo == ref.cleanName }?.id
        }
        if (inputIds.size != r.inputs.size) {
            showMsg(lang("재료가 인벤토리 정의에 없음.", "Inputs not in inventory registry."), error = true)
            return
        }
        // 1개씩 소비 가정 (R82+ qty 확장)
        val invAll = inv.all()
        val missing = inputIds.filter { id -> invAll.none { it.itemId == id && it.count >= 1 } }
        if (missing.isNotEmpty()) {
            showMsg(lang("재료 부족: ${missing.size}종", "Missing inputs: ${missing.size}"), error = true)
            return
        }
        // 소비
        for (id in inputIds) {
            val invIdx = inv.all().indexOfFirst { it.itemId == id }
            if (invIdx >= 0) inv.remove(invIdx, 1)
        }
        // 추가
        inv.add(outItem.id, 1)
        gameState.saveInventory(inv)
        showMsg(lang("제작 성공: ${outItem.nameKo}", "Crafted: ${outItem.nameEn}"), error = false)
        EventBus.push(lang("단조: ${outItem.nameKo} 획득", "Forge: got ${outItem.nameEn}"))
    }

    private fun showMsg(s: String, error: Boolean) {
        message = s; messageIsError = error; messageTtl = 2500L
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth,
            if (isEn) "FORGE" else "단조",
            "${recipes.size} ${if (isEn) "recipes" else "레시피"}")

        if (recipes.isEmpty()) {
            canvas.drawText(
                if (isEn) "Catalog not loaded — R74 data unavailable."
                else "카탈로그 미로딩 — R74 데이터 사용 불가.",
                10f, 60f, errPaint)
            UiKit.drawHints(canvas, virtualWidth, virtualHeight,
                if (isEn) "R back" else "R 뒤로")
            return
        }

        // recipe rows
        val rowH = 12f
        val left = 6f
        for (j in 0 until rowsVisible) {
            val i = scroll + j
            if (i >= recipes.size) break
            val r = recipes[i]
            val y = 32f + j * rowH
            if (i == cursor) canvas.drawRect(left, y - 9f, virtualWidth - 6f, y + 2f, rowSelected)
            val outName = r.output?.cleanName ?: "?"
            val inN = r.inputs.size
            val line = "[${i.toString().padStart(2)}]  in=$inN  → $outName"
            canvas.drawText(line, left + 4f, y, UiKit.body)
        }

        // detail panel
        val r = recipes.getOrNull(cursor)
        if (r != null) {
            val panelTop = virtualHeight - 56f
            UiKit.drawBox(canvas, 4f, panelTop, virtualWidth - 8f, 38f)
            val outName = r.output?.cleanName ?: "?"
            canvas.drawText("→ $outName", 10f, panelTop + 14f, titlePaint)
            val inputs = r.inputs.joinToString(" + ") { it.cleanName }
            canvas.drawText(
                if (isEn) "inputs: $inputs" else "재료: $inputs",
                10f, panelTop + 28f, UiKit.muted)
        }

        // message
        if (message.isNotEmpty()) {
            canvas.drawText(message, 10f, virtualHeight - 12f,
                if (messageIsError) errPaint else msgPaint)
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            if (isEn) "^v select  OK forge  R back" else "^v 선택  OK 제작  R 뒤로")
    }
}
