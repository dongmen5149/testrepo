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
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit
import org.json.JSONObject

/**
 * 대화 데모 — `dialogue_corpus.json` 에서 한 이벤트의 연속 대사를 재생.
 * RPG 스타일 dialogue box + 화자 이름 + 글자 흘러나옴 효과.
 *
 * 입력:
 *   OK   : 다음 대사
 *   ▲▼  : 이벤트 변경 (e0000, e0001, ...)
 *   R    : 뒤로
 */
class DialogueDemoScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private data class Line(val event: String, val offset: Int, val text: String)

    private val allLines: List<Line>
    private val byEvent: Map<String, List<Line>>
    private val eventNames: List<String>
    private val translations: Map<String, String>     // ko → en (없으면 원본 사용)

    private var eventIdx = 0
    private var lineIdx = 0
    private var revealedChars = 0
    private var elapsedMs = 0L
    private val charsPerSec = 30f

    private val bg = Paint().apply { color = Color.rgb(20, 25, 40) }
    private val portraitPaint = Paint()

    private val portrait: Bitmap?

    init {
        // dialogue_corpus.json 파싱
        val text = runCatching {
            context.assets.open("dialogue_corpus.json").bufferedReader().use { it.readText() }
        }.getOrDefault("{}")
        val json = runCatching { JSONObject(text) }.getOrDefault(JSONObject())
        val arr = json.optJSONArray("lines")
        val tmp = mutableListOf<Line>()
        if (arr != null) {
            // 너무 많으면 첫 5,000 만 (메모리 절약)
            val limit = minOf(arr.length(), 5000)
            for (i in 0 until limit) {
                val o = arr.optJSONObject(i) ?: continue
                tmp += Line(
                    event = o.optString("event"),
                    offset = o.optInt("offset"),
                    text = o.optString("text"),
                )
            }
        }
        allLines = tmp
        byEvent = allLines.groupBy { it.event }
        eventNames = byEvent.keys.sorted()

        // 번역본 (영어 모드에서 사용). 없으면 빈 map → 원본 사용.
        translations = runCatching {
            val transText = context.assets.open("dialogue_translations_en.json")
                .bufferedReader().use { it.readText() }
            val obj = JSONObject(transText)
            val out = mutableMapOf<String, String>()
            for (key in obj.keys()) out[key] = obj.optString(key)
            out.toMap()
        }.getOrDefault(emptyMap())

        // 첫 영웅 스프라이트를 portrait 으로 사용
        portrait = runCatching {
            val dir = "${settings.spritesDir()}/hero/h00000_bm"
            val files = context.assets.list(dir)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
            if (files.isEmpty()) null
            else context.assets.open("$dir/${files.first()}").use { BitmapFactory.decodeStream(it) }
        }.getOrNull()
    }

    private fun currentLines(): List<Line> = byEvent[eventNames.getOrNull(eventIdx)] ?: emptyList()

    override fun update(deltaMs: Long) {
        elapsedMs += deltaMs
        val lines = currentLines()
        val cur = lines.getOrNull(lineIdx)
        if (cur != null) {
            val target = displayText(cur).length
            revealedChars = minOf(target, ((elapsedMs * charsPerSec) / 1000f).toInt())
        }

        if (input.pressedOnce(InputController.K_OK)) {
            val full = cur?.let { displayText(it).length } ?: 0
            if (revealedChars < full) {
                // 즉시 완성
                elapsedMs = (full / charsPerSec * 1000f).toLong() + 1L
            } else {
                // 다음 라인
                lineIdx++
                if (lineIdx >= lines.size) lineIdx = 0
                elapsedMs = 0L
                revealedChars = 0
            }
        }
        if (input.pressedOnce(InputController.K_UP)) {
            eventIdx = (eventIdx - 1 + eventNames.size.coerceAtLeast(1)) % eventNames.size.coerceAtLeast(1)
            lineIdx = 0; elapsedMs = 0L; revealedChars = 0
        }
        if (input.pressedOnce(InputController.K_DOWN)) {
            eventIdx = (eventIdx + 1) % eventNames.size.coerceAtLeast(1)
            lineIdx = 0; elapsedMs = 0L; revealedChars = 0
        }
        if (input.pressedOnce(InputController.K_SOFT2)) onRequest(MainActivity.SceneRequest.Pop)
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)

        UiKit.drawHeader(canvas, virtualWidth,
            context.getString(R.string.scene_dialogue_demo),
            "${eventIdx + 1}/${eventNames.size}  ${eventNames.getOrNull(eventIdx) ?: "-"}")

        // 포트레이트 (왼쪽 상단)
        portrait?.let { bmp ->
            val scale = 4
            val dw = bmp.width * scale
            val dh = bmp.height * scale
            canvas.drawBitmap(bmp,
                Rect(0, 0, bmp.width, bmp.height),
                Rect(20, 60, 20 + dw, 60 + dh), portraitPaint)
        }

        val lines = currentLines()
        val cur = lines.getOrNull(lineIdx)
        if (cur == null) {
            UiKit.drawDialogueBox(canvas, virtualWidth, virtualHeight, "—",
                listOf("(no dialogue available)"))
        } else {
            val full = displayText(cur)
            val shown = full.substring(0, minOf(revealedChars, full.length))
            // 줄바꿈: 화면 폭에 맞게 단순 분할
            val wrapped = wrap(shown, maxCharsPerLine = 30)
            UiKit.drawDialogueBox(canvas, virtualWidth, virtualHeight,
                speaker = "[${cur.event}]",
                lines = wrapped + if (revealedChars >= full.length) listOf("▼") else emptyList())
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "OK ▶  ▲▼ event  R back")
    }

    /** 현재 언어 설정에 맞는 표시 텍스트 (영어 모드 + 번역 있으면 번역, 아니면 원본 한국어). */
    private fun displayText(line: Line): String {
        return if (settings.language == "en") {
            translations[line.text] ?: line.text
        } else {
            line.text
        }
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
