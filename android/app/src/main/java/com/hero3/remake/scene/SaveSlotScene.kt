package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.UiKit

/**
 * 세이브 슬롯 화면 — 3 슬롯, 선택해 저장 / 불러오기.
 *
 * 현재 게임 상태(`gameState`, slotId 0)를 선택한 슬롯으로 복사하거나
 * 슬롯 데이터를 현재 활성 슬롯으로 불러옴.
 */
class SaveSlotScene(
    private val context: Context,
    private val input: InputController,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val slotCount = 3
    private val slots: List<GameState> = (1..slotCount).map { GameState(context, slotId = it) }
    private var selected = 0
    private var mode: Mode = Mode.SAVE

    private enum class Mode { SAVE, LOAD }

    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_UP))    { selected = (selected - 1 + slotCount) % slotCount }
        if (input.pressedOnce(InputController.K_DOWN))  { selected = (selected + 1) % slotCount }
        if (input.pressedOnce(InputController.K_LEFT) || input.pressedOnce(InputController.K_RIGHT)) {
            mode = if (mode == Mode.SAVE) Mode.LOAD else Mode.SAVE
        }
        if (input.pressedOnce(InputController.K_OK)) {
            val slot = slots[selected]
            if (mode == Mode.SAVE) {
                slot.copyFrom(gameState)
            } else if (!slot.isEmpty()) {
                gameState.copyFrom(slot)
                onRequest(MainActivity.SceneRequest.MapWalk)
                return
            }
        }
        if (input.pressedOnce(InputController.K_SOFT2)) onRequest(MainActivity.SceneRequest.Pop)
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val title = when (mode) {
            Mode.SAVE -> if (currentLanguageIsKorean()) "저장 슬롯" else "Save Slot"
            Mode.LOAD -> if (currentLanguageIsKorean()) "불러오기 슬롯" else "Load Slot"
        }
        UiKit.drawHeader(canvas, virtualWidth, title, "◀▶ to switch SAVE/LOAD")

        var y = 60f
        for (i in 0 until slotCount) {
            val slot = slots[i]
            val label = if (slot.isEmpty()) {
                if (currentLanguageIsKorean()) "슬롯 ${i + 1}: 비어있음"
                else "Slot ${i + 1}: empty"
            } else {
                "Slot ${i + 1}: map ${slot.currentMapId} (${slot.heroX},${slot.heroY})"
            }
            UiKit.drawMenuItem(canvas, 12f, y, virtualWidth - 24f, 28f, label, i == selected)
            y += 34f
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "▲▼  ◀▶ mode  OK ${if (mode == Mode.SAVE) "save" else "load"}  R back")
    }

    private fun currentLanguageIsKorean(): Boolean {
        return context.resources.configuration.locales.get(0).language == "ko"
    }
}
