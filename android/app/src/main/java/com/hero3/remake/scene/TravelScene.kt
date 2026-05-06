package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.engine.EventBus
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit
import org.json.JSONObject

/** 방문한 맵으로 빠른 이동. 각 맵의 안전한 진입점에 영웅을 배치. */
class TravelScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private data class Entry(val mapId: Int, val name: String, val safeX: Int, val safeY: Int)

    private val entries: List<Entry> = gameState.visitedMapIds.sorted().map { mid ->
        val nm = runCatching {
            val text = context.assets.open("maps/map${mid}_mp.json").bufferedReader().use { it.readText() }
            JSONObject(text).optString("name", "?")
        }.getOrDefault("?")
        val (sx, sy) = safeSpot(mid)
        Entry(mid, nm, sx, sy)
    }

    private var idx = 0
    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2)) { onRequest(MainActivity.SceneRequest.Pop); return }
        if (entries.isEmpty()) return
        if (input.pressedOnce(InputController.K_UP))   idx = (idx - 1 + entries.size) % entries.size
        if (input.pressedOnce(InputController.K_DOWN)) idx = (idx + 1) % entries.size
        if (input.pressedOnce(InputController.K_OK)) {
            val e = entries[idx]
            // 같은 맵이면 비용 0, 다른 맵 = 50G
            val cost = if (e.mapId == gameState.currentMapId) 0 else 50
            if (gameState.gold < cost) {
                EventBus.push(settings.lang("골드 부족 (50G).", "Not enough gold (50G)."))
                return
            }
            gameState.gold -= cost
            gameState.resetPosition(e.mapId, e.safeX, e.safeY)
            onRequest(MainActivity.SceneRequest.Pop)
            onRequest(MainActivity.SceneRequest.MapWalk)
        }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth, settings.lang("빠른 이동", "FAST TRAVEL"))

        if (entries.isEmpty()) {
            canvas.drawText(settings.lang("(방문한 맵 없음)", "(no visited maps)"),
                16f, 60f, UiKit.muted)
        } else {
            UiKit.drawBox(canvas, 8f, 32f, virtualWidth - 16f, 18f * entries.size + 12f)
            for ((i, e) in entries.withIndex()) {
                val y = 50f + i * 18f
                if (i == idx) {
                    canvas.drawRect(10f, y - 12f, virtualWidth - 18f, y + 4f,
                        Paint().apply { color = Color.argb(120, 255, 220, 90) })
                }
                canvas.drawText("map${e.mapId}  ${e.name}", 16f, y, UiKit.body)
            }
        }
        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            settings.lang("▲▼  OK 이동 (50G)  R 뒤로", "▲▼  OK travel (50G)  R back"))
    }

    private fun safeSpot(mapId: Int): Pair<Int, Int> = when (mapId) {
        0 -> 17 to 12
        1 -> 5 to 5
        10 -> 6 to 6
        11 -> 4 to 8
        12 -> 5 to 5
        else -> 1 to 1
    }
}

