package com.hero3.remake.scene

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.SfxBus
import com.hero3.remake.engine.UiKit

/**
 * 타이틀 화면 — 로고 비트맵 + 타이틀/서브타이틀 + 메뉴 (새 게임 / 이어하기 / 설정).
 *
 * 입력:
 *   ▲▼  : 메뉴 항목 변경
 *   OK  : 선택
 */
class TitleScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private data class Item(val labelResId: Int, val request: MainActivity.SceneRequest)

    private val items = listOf(
        Item(R.string.menu_new_game, MainActivity.SceneRequest.NewGame),
        Item(R.string.menu_continue, MainActivity.SceneRequest.SaveSlots),
        Item(R.string.menu_settings, MainActivity.SceneRequest.SettingsScene),
        Item(R.string.menu_gallery, MainActivity.SceneRequest.SpriteGallery),
    )
    private var selected = 0

    private val bgPaint = Paint().apply { color = Color.BLACK }
    private val pulsePaint = Paint().apply {
        color = Color.WHITE
        textSize = 12f
        isFakeBoldText = true
        textAlign = Paint.Align.CENTER
    }
    private val versionPaint = Paint().apply {
        color = Color.rgb(120, 120, 140)
        textSize = 8f
        textAlign = Paint.Align.RIGHT
    }
    private val titlePaint = Paint().apply {
        color = Color.rgb(255, 230, 130)
        textSize = 28f
        isFakeBoldText = true
        textAlign = Paint.Align.CENTER
    }
    private val subtitlePaint = Paint().apply {
        color = Color.rgb(200, 200, 220)
        textSize = 14f
        textAlign = Paint.Align.CENTER
    }

    private val logo: Bitmap? = runCatching {
        // logo/logo_bm/frame_00_*.png 중 첫 PNG
        val dir = "${settings.spritesDir()}/logo/logo_bm"
        val files = context.assets.list(dir)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
        if (files.isEmpty()) return@runCatching null
        context.assets.open("$dir/${files.first()}").use { BitmapFactory.decodeStream(it) }
    }.getOrNull()

    private val cleared: Boolean = GameState.anySlotCleared(context)
    private var elapsedMs = 0L

    init { SfxBus.playMusic(SfxBus.Bgm.TITLE) }

    override fun update(deltaMs: Long) {
        elapsedMs += deltaMs
        if (input.pressedOnce(InputController.K_UP))   { selected = (selected - 1 + items.size) % items.size }
        if (input.pressedOnce(InputController.K_DOWN)) { selected = (selected + 1) % items.size }
        if (input.pressedOnce(InputController.K_OK))   { onRequest(items[selected].request) }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bgPaint)

        // 타이틀
        canvas.drawText(context.getString(R.string.main_title), virtualWidth / 2f, 60f, titlePaint)
        canvas.drawText(context.getString(R.string.main_subtitle), virtualWidth / 2f, 84f, subtitlePaint)

        // 로고 (있으면 중앙)
        logo?.let { bmp ->
            val scale = 4
            val dw = bmp.width * scale
            val dh = bmp.height * scale
            val left = (virtualWidth - dw) / 2
            val top = 110
            canvas.drawBitmap(bmp,
                Rect(0, 0, bmp.width, bmp.height),
                Rect(left, top, left + dw, top + dh), null)
        }

        // 메뉴 항목 (4개)
        val itemH = 18f
        val totalH = items.size * itemH
        val startY = virtualHeight - totalH - 24f
        for ((i, item) in items.withIndex()) {
            val y = startY + i * itemH
            val label = context.getString(item.labelResId)
            UiKit.drawMenuItem(canvas, 50f, y, virtualWidth - 100f, itemH - 2f, label, i == selected)
        }

        // 버전
        canvas.drawText("v0.1.0", virtualWidth - 4f, virtualHeight - 4f, versionPaint)
        // 클리어 ★
        if (cleared) {
            val starPaint = Paint().apply {
                color = Color.rgb(255, 220, 80); textSize = 11f; isFakeBoldText = true
                textAlign = Paint.Align.LEFT
            }
            canvas.drawText("★ CLEAR", 4f, virtualHeight - 4f, starPaint)
        }
    }
}
