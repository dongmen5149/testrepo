package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.UiKit

/**
 * 인벤토리 mockup — 가방 / 장비 / 스킬 탭 + 슬롯 그리드.
 * 실제 아이템 데이터는 미정. txt_127 (빈슬롯) 으로 채움.
 */
class InventoryScene(
    private val context: Context,
    private val input: InputController,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val tabs = listOf(R.string.txt_008, R.string.txt_009, R.string.txt_010)  // 가방·장비·스킬
    private var tabIdx = 0
    private var slotIdx = 0
    private val cols = 5
    private val rows = 4
    private val totalSlots = cols * rows

    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }
    private val slotEmpty = Paint().apply { color = Color.argb(120, 80, 80, 100) }
    private val slotEmptyBorder = Paint().apply {
        color = Color.argb(120, 140, 140, 160); style = Paint.Style.STROKE; strokeWidth = 1f
    }
    private val slotSelected = Paint().apply {
        color = Color.rgb(255, 220, 90); style = Paint.Style.STROKE; strokeWidth = 2f
    }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2)) onRequest(MainActivity.SceneRequest.Pop)
        if (input.pressedOnce(InputController.K_SOFT1)) tabIdx = (tabIdx + 1) % tabs.size
        if (input.pressedOnce(InputController.K_LEFT))  slotIdx = (slotIdx - 1 + totalSlots) % totalSlots
        if (input.pressedOnce(InputController.K_RIGHT)) slotIdx = (slotIdx + 1) % totalSlots
        if (input.pressedOnce(InputController.K_UP))    slotIdx = (slotIdx - cols + totalSlots) % totalSlots
        if (input.pressedOnce(InputController.K_DOWN))  slotIdx = (slotIdx + cols) % totalSlots
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth, context.getString(R.string.txt_002))  // INVENTORY

        // 탭
        var x = 8f
        for ((i, t) in tabs.withIndex()) {
            UiKit.drawMenuItem(canvas, x, 28f, 70f, 18f, context.getString(t), i == tabIdx)
            x += 74f
        }

        // 슬롯 그리드 시작 (탭 아래)
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
                canvas.drawRoundRect(rect, 4f, 4f, slotEmpty)
                canvas.drawRoundRect(rect, 4f, 4f, slotEmptyBorder)
                if (r * cols + c == slotIdx) {
                    canvas.drawRoundRect(rect, 4f, 4f, slotSelected)
                }
            }
        }

        // 선택된 슬롯 정보 (mock)
        UiKit.drawBox(canvas, 8f, virtualHeight - 60f, virtualWidth - 16f, 36f)
        canvas.drawText(context.getString(R.string.txt_127), 14f, virtualHeight - 44f, UiKit.muted)  // 빈슬롯
        canvas.drawText("Slot ${slotIdx + 1}/$totalSlots", 14f, virtualHeight - 30f, UiKit.muted)

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "L tab  ${context.getString(R.string.hint_dpad_navigate)}  ${context.getString(R.string.hint_back_cancel)}")
    }
}
