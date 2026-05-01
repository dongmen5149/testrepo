package com.hero3.remake.scene

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import com.hero3.remake.MainActivity
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.NpcRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * 단일 NPC 와의 대화 씬.
 *
 * NpcRegistry 에서 npcId 로 조회한 후 dialogues 라인을 순서대로 재생.
 * 모든 라인 재생 후 OK → 이전 씬으로 pop.
 */
class NpcDialogueScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val npcId: String,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val npc = NpcRegistry.forMap(0).firstOrNull { it.id == npcId }
        ?: NpcRegistry.forMap(1).firstOrNull { it.id == npcId }   // 추후 다른 맵 지원

    private val portrait: Bitmap? = npc?.let { n ->
        runCatching {
            val dir = "${settings.spritesDir()}/${n.spriteDir}"
            val files = context.assets.list(dir)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
            if (files.isEmpty()) null
            else context.assets.open("$dir/${files.first()}").use { BitmapFactory.decodeStream(it) }
        }.getOrNull()
    }

    private var lineIdx = 0
    private var revealedChars = 0
    private var elapsedMs = 0L
    private val charsPerSec = 30f

    private val bg = Paint().apply { color = Color.rgb(20, 25, 40) }

    private fun lines(): List<String> {
        val n = npc ?: return emptyList()
        return if (settings.language == "en") n.dialoguesEn else n.dialoguesKo
    }

    override fun update(deltaMs: Long) {
        elapsedMs += deltaMs
        val ls = lines()
        val cur = ls.getOrNull(lineIdx)
        if (cur != null) {
            revealedChars = minOf(cur.length, ((elapsedMs * charsPerSec) / 1000f).toInt())
        }
        if (input.pressedOnce(InputController.K_OK)) {
            val full = cur?.length ?: 0
            if (revealedChars < full) {
                elapsedMs = (full / charsPerSec * 1000f).toLong() + 1L
            } else {
                lineIdx++
                elapsedMs = 0L
                revealedChars = 0
                if (lineIdx >= ls.size) {
                    onRequest(MainActivity.SceneRequest.Pop)
                }
            }
        }
        if (input.pressedOnce(InputController.K_SOFT2)) {
            onRequest(MainActivity.SceneRequest.Pop)
        }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)

        val n = npc
        if (n == null) {
            canvas.drawText("[Unknown NPC: $npcId]", 8f, 30f, UiKit.body)
            return
        }

        // 포트레이트 (왼쪽 상단, 4× 업스케일)
        portrait?.let { bmp ->
            val scale = 4
            val dw = bmp.width * scale
            val dh = bmp.height * scale
            canvas.drawBitmap(bmp,
                Rect(0, 0, bmp.width, bmp.height),
                Rect(20, 40, 20 + dw, 40 + dh), null)
        }

        val ls = lines()
        val cur = ls.getOrNull(lineIdx)
        val name = if (settings.language == "en") n.nameEn else n.nameKo

        if (cur == null) {
            UiKit.drawDialogueBox(canvas, virtualWidth, virtualHeight, name,
                listOf(if (settings.language == "en") "..." else "..."))
        } else {
            val shown = cur.substring(0, minOf(revealedChars, cur.length))
            val wrapped = wrap(shown, 30)
            UiKit.drawDialogueBox(canvas, virtualWidth, virtualHeight,
                speaker = name,
                lines = wrapped + if (revealedChars >= cur.length) listOf("▼") else emptyList())
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight, "OK ▶  R back")
    }

    private fun wrap(s: String, maxCharsPerLine: Int): List<String> {
        if (s.length <= maxCharsPerLine) return listOf(s)
        val out = mutableListOf<String>()
        var i = 0
        while (i < s.length) {
            out += s.substring(i, minOf(i + maxCharsPerLine, s.length))
            i += maxCharsPerLine
        }
        return out
    }
}
