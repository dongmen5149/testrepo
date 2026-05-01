package com.hero3.remake.scene

import android.content.res.AssetManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings

/**
 * 스프라이트 갤러리 + 애니메이션 플레이어.
 *
 * `assets/sprites/<category>/<bmName>/frame_NN_*.png` 구조에서
 * 같은 디렉토리 안의 frame PNG 들을 5fps 로 순환 재생.
 *
 * 입력:
 *   ◀▶  : 스프라이트 (디렉토리) 변경
 *   ▲▼  : 카테고리 변경
 *   OK  : 4× 줌 토글
 *   L   : 한국어/영어 라벨
 *   R   : 일시정지/재개
 */
class SpriteGalleryScene(
    private val assets: AssetManager,
    private val input: InputController,
    private val settings: Settings? = null,
) : Scene {

    private val categories = listOf("boss", "enemy", "hero", "npc", "menu", "comm", "logo", "skill", "fgi", "map")
    private val spritesRoot: String = settings?.spritesDir() ?: "sprites"

    /** sprite "이름" = 디렉토리 (멀티프레임 BM) 또는 단일 PNG (구버전 자산) */
    private data class SpriteEntry(val displayName: String, val frames: List<String>)

    private val perCategory: Map<String, List<SpriteEntry>> = categories.associateWith { cat ->
        runCatching { listSprites(cat) }.getOrDefault(emptyList())
    }
    private val nonEmpty = categories.filter { perCategory[it]?.isNotEmpty() == true }

    private fun listSprites(cat: String): List<SpriteEntry> {
        val entries = mutableListOf<SpriteEntry>()
        val items = assets.list("$spritesRoot/$cat") ?: return entries
        for (name in items.sorted()) {
            val sub = "$spritesRoot/$cat/$name"
            val children = runCatching { assets.list(sub) }.getOrNull()
            if (!children.isNullOrEmpty() && children.any { it.endsWith(".png") }) {
                entries += SpriteEntry(name, children.filter { it.endsWith(".png") }.sorted().map { "$sub/$it" })
            } else if (name.endsWith(".png")) {
                entries += SpriteEntry(name, listOf(sub))
            }
        }
        return entries
    }

    private var catIndex = 0
    private var spriteIndex = 0
    private var frameIndex = 0
    private var elapsedMs = 0L
    private val frameMsPerCycle = 200L  // 5fps

    private val frameCache = mutableMapOf<String, Bitmap>()
    private var zoomedIn = true
    private var koreanLabels = true
    private var paused = false

    private val backgroundPaint = Paint().apply { color = Color.rgb(20, 20, 30) }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 10f
        isFakeBoldText = true
    }
    private val hintPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.rgb(180, 180, 200)
        textSize = 8f
    }

    override fun update(deltaMs: Long) {
        if (nonEmpty.isEmpty()) return

        var changed = false
        if (input.pressedOnce(InputController.K_LEFT))  { spriteIndex--; frameIndex = 0; changed = true }
        if (input.pressedOnce(InputController.K_RIGHT)) { spriteIndex++; frameIndex = 0; changed = true }
        if (input.pressedOnce(InputController.K_UP))    { catIndex--; spriteIndex = 0; frameIndex = 0; changed = true }
        if (input.pressedOnce(InputController.K_DOWN))  { catIndex++; spriteIndex = 0; frameIndex = 0; changed = true }
        if (input.pressedOnce(InputController.K_OK))    { zoomedIn = !zoomedIn }
        if (input.pressedOnce(InputController.K_SOFT1)) { koreanLabels = !koreanLabels }
        if (input.pressedOnce(InputController.K_SOFT2)) { paused = !paused }

        if (changed) {
            catIndex = ((catIndex % nonEmpty.size) + nonEmpty.size) % nonEmpty.size
            val list = perCategory.getValue(nonEmpty[catIndex])
            spriteIndex = ((spriteIndex % list.size) + list.size) % list.size
            elapsedMs = 0
        }

        if (!paused) {
            elapsedMs += deltaMs
            val curFrameCount = currentSprite()?.frames?.size ?: 1
            if (curFrameCount > 1) {
                frameIndex = ((elapsedMs / frameMsPerCycle) % curFrameCount.toLong()).toInt()
            } else {
                frameIndex = 0
            }
        }
    }

    private fun currentSprite(): SpriteEntry? {
        if (nonEmpty.isEmpty()) return null
        val list = perCategory.getValue(nonEmpty[catIndex])
        return if (list.isNotEmpty()) list[spriteIndex.coerceIn(0, list.size - 1)] else null
    }

    private fun loadFrame(path: String): Bitmap? {
        frameCache[path]?.let { return it }
        return runCatching {
            assets.open(path).use { BitmapFactory.decodeStream(it) }
        }.getOrNull()?.also { frameCache[path] = it }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), backgroundPaint)

        val title = if (koreanLabels) "스프라이트 갤러리" else "SPRITE GALLERY"
        canvas.drawText(title, 4f, 12f, labelPaint)

        if (nonEmpty.isEmpty()) {
            canvas.drawText(if (koreanLabels) "자산이 없습니다" else "No assets bundled", 4f, 30f, labelPaint)
            renderHints(canvas)
            return
        }

        val cat = nonEmpty[catIndex]
        val list = perCategory.getValue(cat)
        canvas.drawText("$cat  ${spriteIndex + 1} / ${list.size}", 4f, 24f, labelPaint)

        val sprite = currentSprite() ?: run { renderHints(canvas); return }
        canvas.drawText(sprite.displayName, 4f, 36f, hintPaint)

        val totalFrames = sprite.frames.size
        if (totalFrames > 0) {
            val curFrame = frameIndex.coerceIn(0, totalFrames - 1)
            canvas.drawText("frame ${curFrame + 1}/${totalFrames}${if (paused) " [PAUSED]" else ""}", 4f, 48f, hintPaint)
            loadFrame(sprite.frames[curFrame])?.let { bmp ->
                val scale = if (zoomedIn) 4 else 1
                val dw = bmp.width * scale
                val dh = bmp.height * scale
                val left = (virtualWidth - dw) / 2
                val top = (virtualHeight - dh) / 2
                val src = Rect(0, 0, bmp.width, bmp.height)
                val dst = Rect(left, top, left + dw, top + dh)
                canvas.drawBitmap(bmp, src, dst, null)
            }
        }
        renderHints(canvas)
    }

    private fun renderHints(canvas: Canvas) {
        val hint = if (koreanLabels)
            "◀▶ 스프라이트  ▲▼ 카테고리  OK 줌  L 언어  R 일시정지"
        else
            "<> sprite  ^v category  OK zoom  L lang  R pause"
        canvas.drawText(hint, 4f, virtualHeight - 4f, hintPaint)
    }
}
