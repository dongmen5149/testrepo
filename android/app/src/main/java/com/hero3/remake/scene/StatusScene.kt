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
 * 상태 화면 — 캐릭터 스탯 mockup.
 * 실제 데이터는 캐릭터 시스템 구현 후 연결. 현재는 placeholder.
 */
class StatusScene(
    private val context: Context,
    private val input: InputController,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2) ||
            input.pressedOnce(InputController.K_OK)) {
            onRequest(MainActivity.SceneRequest.Pop)
        }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth, context.getString(R.string.txt_001))  // STATUS

        // 캐릭터 정보 박스
        UiKit.drawBox(canvas, 8f, 32f, virtualWidth - 16f, 80f)
        canvas.drawText(context.getString(R.string.txt_017) + ": 케이 / Kei", 16f, 50f, UiKit.body)
        canvas.drawText("CLASS: Soltian Warrior", 16f, 64f, UiKit.body)
        canvas.drawText(context.getString(R.string.txt_048) + " 1", 16f, 78f, UiKit.body)         // LV
        canvas.drawText(context.getString(R.string.txt_049) + ": 100/100", 16f, 92f, UiKit.body)  // HP
        canvas.drawText(context.getString(R.string.txt_050) + ": 50/50", 110f, 92f, UiKit.body)   // SP
        canvas.drawText(context.getString(R.string.txt_051) + ": 0", 16f, 106f, UiKit.muted)      // EXP

        // 스탯 박스
        UiKit.drawBox(canvas, 8f, 120f, virtualWidth - 16f, 130f)
        val statRows = listOf(
            R.string.txt_052 to "10",  // 힘 / STR
            R.string.txt_053 to "8",   // 민첩 / DEX
            R.string.txt_054 to "12",  // 체력 / VIT
            R.string.txt_055 to "5",   // 정신 / INT
            R.string.txt_056 to "20",  // ATT1
            R.string.txt_057 to "0",   // ATT2
            R.string.txt_058 to "15",  // P.DEF
            R.string.txt_059 to "5",   // M.DEF
            R.string.txt_060 to "5%",  // CRI
            R.string.txt_061 to "0%",  // RES
            R.string.txt_062 to "85",  // ACC
            R.string.txt_063 to "10",  // DOD
        )
        for ((i, row) in statRows.withIndex()) {
            val col = i % 2
            val r = i / 2
            val x = 16f + col * 110f
            val y = 138f + r * 16f
            canvas.drawText(context.getString(row.first), x, y, UiKit.muted)
            canvas.drawText(row.second, x + 50f, y, UiKit.body)
        }

        // 힌트
        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            context.getString(R.string.hint_back_cancel))
    }
}
