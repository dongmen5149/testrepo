package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.SfxBus
import com.hero3.remake.engine.UiKit

/**
 * 봉인된 신 처치 후 자동 진입하는 엔딩 — 검정 배경 + 위로 스크롤하는 크레딧.
 * OK 또는 R 로 스킵.
 */
class EndingScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
    private val markCleared: Boolean = true,
) : Scene {

    init {
        if (markCleared) gameState.gameCleared = true
        SfxBus.playMusic(SfxBus.Bgm.ENDING)
    }

    private val isEn: Boolean get() = settings.isEn

    private val creditsKo = listOf(
        "",
        "운명의 수레바퀴는 멈추었다.",
        "솔티아에 다시 평화가 찾아왔다.",
        "",
        "영웅의 이름은",
        "별이 되어 영원히 빛나리.",
        "",
        "—",
        "",
        "원작:  영웅서기3 - 운명의수레바퀴",
        "       (한빛소프트, 2008)",
        "",
        "리메이크: Hero3 Remake (Strategy C)",
        "엔진:    Kotlin / Android Canvas",
        "자산:    HD scale4x 업스케일",
        "i18n:    한국어 / 영어",
        "",
        "감사합니다.",
        "",
        "— FIN —",
    )

    private val creditsEn = listOf(
        "",
        "The wheel of destiny has stopped.",
        "Peace returns to Soltia.",
        "",
        "The hero's name shall shine",
        "as a star, forever.",
        "",
        "—",
        "",
        "Original: Hero3 - Wheel of Destiny",
        "          (Hanbit Soft, 2008)",
        "",
        "Remake:   Hero3 Remake (Strategy C)",
        "Engine:   Kotlin / Android Canvas",
        "Assets:   HD scale4x upscale",
        "i18n:     Korean / English",
        "",
        "Thank you.",
        "",
        "— FIN —",
    )

    private fun lines() = if (isEn) creditsEn else creditsKo

    private var elapsedMs = 0L
    private val pxPerSec = 22f

    private val bg = Paint().apply { color = Color.BLACK }
    private val text = Paint(UiKit.body).apply { color = Color.rgb(255, 235, 200); textSize = 14f }

    override fun update(deltaMs: Long) {
        elapsedMs += deltaMs
        if (input.pressedOnce(InputController.K_OK) ||
            input.pressedOnce(InputController.K_SOFT2)) {
            exit()
        }
    }

    private fun exit() {
        if (markCleared) onRequest(MainActivity.SceneRequest.Title)
        else onRequest(MainActivity.SceneRequest.Pop)
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val ls = lines()
        val lineH = 18f
        val totalH = ls.size * lineH + virtualHeight
        val yOffset = virtualHeight - elapsedMs / 1000f * pxPerSec
        for ((i, line) in ls.withIndex()) {
            val w = text.measureText(line)
            val y = yOffset + i * lineH
            if (y < -lineH || y > virtualHeight + lineH) continue
            canvas.drawText(line, (virtualWidth - w) / 2f, y, text)
        }
        // 끝까지 흘러갔으면 자동 종료
        if (yOffset + ls.size * lineH < 0) exit()
        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            if (isEn) "OK skip" else "OK 스킵")
    }
}
