package com.hero3.remake.scene

import android.app.Activity
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * 환경설정 — 언어 / 화질 토글.
 *
 * 언어 변경 시 Activity 재생성 (Configuration override 적용).
 */
class SettingsScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private data class Item(val labelResId: Int, val type: Type)
    private enum class Type { LANGUAGE, QUALITY, BACK }

    private val items = listOf(
        Item(R.string.settings_language, Type.LANGUAGE),
        Item(R.string.settings_quality, Type.QUALITY),
        Item(R.string.txt_134, Type.BACK),  // 확인 / Confirm
    )
    private var selected = 0

    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_UP))   { selected = (selected - 1 + items.size) % items.size }
        if (input.pressedOnce(InputController.K_DOWN)) { selected = (selected + 1) % items.size }
        if (input.pressedOnce(InputController.K_LEFT) || input.pressedOnce(InputController.K_RIGHT)) {
            toggleCurrent()
        }
        if (input.pressedOnce(InputController.K_OK)) {
            when (items[selected].type) {
                Type.LANGUAGE, Type.QUALITY -> toggleCurrent()
                Type.BACK -> onRequest(MainActivity.SceneRequest.Pop)
            }
        }
        if (input.pressedOnce(InputController.K_SOFT2)) onRequest(MainActivity.SceneRequest.Pop)
    }

    private fun toggleCurrent() {
        when (items[selected].type) {
            Type.LANGUAGE -> {
                settings.language = if (settings.language == "ko") "en" else "ko"
                // Activity 재생성으로 locale 갱신
                (context as? Activity)?.recreate()
            }
            Type.QUALITY -> {
                settings.qualityHd = !settings.qualityHd
            }
            Type.BACK -> {}
        }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth, context.getString(R.string.txt_015))  // 환경설정

        var y = 50f
        for ((i, item) in items.withIndex()) {
            val name = context.getString(item.labelResId)
            val value = when (item.type) {
                Type.LANGUAGE -> if (settings.language == "ko")
                    context.getString(R.string.language_korean) else context.getString(R.string.language_english)
                Type.QUALITY -> if (settings.qualityHd)
                    context.getString(R.string.settings_quality_hd) else context.getString(R.string.settings_quality_sd)
                Type.BACK -> ""
            }
            val label = if (item.type == Type.BACK) name else "$name : ◀ $value ▶"
            UiKit.drawMenuItem(canvas, 16f, y, virtualWidth - 32f, 22f, label, i == selected)
            y += 28f
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "▲▼  ◀▶ change  OK  R back")
    }
}
