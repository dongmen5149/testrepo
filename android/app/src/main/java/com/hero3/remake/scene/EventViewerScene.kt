package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.UiKit
import org.json.JSONObject

/**
 * scn_v2 의 244 이벤트 중 하나를 선택해 화자/대사 트리플을 스크롤 뷰어로 표시.
 *
 * 좌측 폴리시:
 *   ◀▶ 이벤트 인덱스 변경 (e0000 ~ e0243)
 *   ▲▼ 대사 스크롤
 *   R 뒤로
 */
class EventViewerScene(
    private val context: Context,
    private val input: InputController,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val totalEvents = 244
    private var eventIdx = 0
    private var scrollIdx = 0
    /** all / 리츠 / 케이 / 일레느 / 시엔 / 레아. SOFT1 로 cycle. */
    private val filters = listOf<String?>(null, "리츠", "케이", "일레느", "시엔", "레아")
    private var filterIdx = 0
    private var entries: List<Triple<String?, String?, String>> = emptyList()
    private var filteredEntries: List<Triple<String?, String?, String>> = emptyList()
    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }
    private val speakerPaint = Paint(UiKit.body).apply { color = Color.rgb(255, 220, 90) }
    private val modePaint    = Paint(UiKit.muted).apply { color = Color.rgb(160, 200, 255); textSize = 9f }

    init { loadEvent(0) }

    private fun loadEvent(idx: Int) {
        eventIdx = idx.coerceIn(0, totalEvents - 1)
        scrollIdx = 0
        val name = "scn_v2/e%04d_scn.json".format(eventIdx)
        entries = runCatching {
            val text = context.assets.open(name).bufferedReader().use { it.readText() }
            val obj = JSONObject(text)
            val arr = obj.optJSONArray("entries") ?: return@runCatching emptyList<Triple<String?, String?, String>>()
            (0 until arr.length()).map { i ->
                val e = arr.getJSONObject(i)
                Triple(
                    e.optString("speaker", null).takeUnless { it == "null" || it.isNullOrEmpty() },
                    e.optString("mode_byte", null).takeUnless { it == "null" || it.isNullOrEmpty() },
                    e.optString("text", ""),
                )
            }
        }.getOrDefault(emptyList())
        applyFilter()
    }

    private fun applyFilter() {
        val f = filters[filterIdx]
        filteredEntries = if (f == null) entries else entries.filter { it.first == f }
        scrollIdx = 0
    }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2) ||
            input.pressedOnce(InputController.K_OK)) {
            onRequest(MainActivity.SceneRequest.Pop); return
        }
        if (input.pressedOnce(InputController.K_LEFT))  loadEvent(eventIdx - 1)
        if (input.pressedOnce(InputController.K_RIGHT)) loadEvent(eventIdx + 1)
        if (input.pressedOnce(InputController.K_SOFT1)) {
            filterIdx = (filterIdx + 1) % filters.size
            applyFilter()
        }
        if (filteredEntries.isNotEmpty()) {
            val maxScroll = (filteredEntries.size - VISIBLE).coerceAtLeast(0)
            if (input.pressedOnce(InputController.K_UP))   scrollIdx = (scrollIdx - 1).coerceAtLeast(0)
            if (input.pressedOnce(InputController.K_DOWN)) scrollIdx = (scrollIdx + 1).coerceAtMost(maxScroll)
        }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val filterLabel = filters[filterIdx] ?: "ALL"
        UiKit.drawHeader(canvas, virtualWidth,
            "Event e%04d  [%s]  %d/%d".format(eventIdx, filterLabel, filteredEntries.size, entries.size))

        if (filteredEntries.isEmpty()) {
            canvas.drawText("(empty)", 16f, 60f, UiKit.muted)
        } else {
            UiKit.drawBox(canvas, 6f, 32f, virtualWidth - 12f, virtualHeight - 60f)
            var y = 50f
            val end = minOf(filteredEntries.size, scrollIdx + VISIBLE)
            for (i in scrollIdx until end) {
                val (spk, mode, text) = filteredEntries[i]
                val head = (spk ?: "narrator") + (mode?.let { "  $it" } ?: "")
                canvas.drawText(head, 12f, y, speakerPaint)
                y += 11f
                // wrap text
                val maxChars = 30
                var s = text
                while (s.isNotEmpty() && y < virtualHeight - 30f) {
                    val take = s.take(maxChars)
                    canvas.drawText(take, 12f, y, UiKit.body)
                    s = s.substring(take.length)
                    y += 12f
                }
                y += 4f
                if (y > virtualHeight - 30f) break
            }
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "◀▶ event  ▲▼ scroll  L filter  R back")
    }

    companion object { private const val VISIBLE = 6 }
}
