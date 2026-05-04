package com.hero3.remake.scene

import android.content.res.AssetManager
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import org.json.JSONArray
import org.json.JSONObject

/**
 * 맵 갤러리 + 미리보기 씬.
 *
 * assets/maps/ 의 각 _mp.json 맵을 색상-해시 heatmap 으로 렌더하여 구조 시각 확인.
 * 정식 타일 렌더링은 `map/obj_0_bm` 분석 후 추가 예정.
 *
 * 입력:
 *   ◀▶  : 맵 변경
 *   ▲▼  : Layer 0 (terrain) ↔ Layer 1 (collision) 토글
 *   OK  : 셀 크기 토글
 */
class MapScene(private val assets: AssetManager, private val input: InputController) : Scene {

    private data class MapData(
        val name: String,
        val w: Int,
        val h: Int,
        val palette: List<Int>,
        val layer0: List<Int>,
        val layer1: List<Int>,
    )

    private val mapList: List<String> = (assets.list("maps") ?: emptyArray())
        .filter { it.endsWith("_mp.json") }
        .sortedBy { extractMapNumber(it) }

    private fun extractMapNumber(name: String): Int {
        val m = Regex("map(\\d+)_mp\\.json").find(name) ?: return 9999
        return m.groupValues[1].toInt()
    }

    private var mapIndex = 0
    private var layerIndex = 0
    private var cellSize = 4
    private var current: MapData? = null

    private val backgroundPaint = Paint().apply { color = Color.rgb(15, 15, 20) }
    private val labelPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.WHITE
        textSize = 10f
        isFakeBoldText = true
    }
    private val hintPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        color = Color.rgb(180, 180, 200)
        textSize = 8f
    }
    private val cellPaint = Paint()

    init {
        if (mapList.isNotEmpty()) loadCurrent()
    }

    override fun update(deltaMs: Long) {
        if (mapList.isEmpty()) return
        var changed = false
        if (input.pressedOnce(InputController.K_LEFT))  { mapIndex--; changed = true }
        if (input.pressedOnce(InputController.K_RIGHT)) { mapIndex++; changed = true }
        if (input.pressedOnce(InputController.K_UP))    { layerIndex = (layerIndex + 1) % 2 }
        if (input.pressedOnce(InputController.K_DOWN))  { layerIndex = (layerIndex + 1) % 2 }
        if (input.pressedOnce(InputController.K_OK))    { cellSize = if (cellSize >= 8) 2 else cellSize + 2 }
        if (changed) {
            mapIndex = ((mapIndex % mapList.size) + mapList.size) % mapList.size
            loadCurrent()
        }
    }

    private fun loadCurrent() {
        val fileName = mapList[mapIndex]
        runCatching {
            val text = assets.open("maps/$fileName").bufferedReader().use { it.readText() }
            val json = JSONObject(text)
            current = MapData(
                name = json.optString("name", fileName),
                w = json.optInt("width"),
                h = json.optInt("height"),
                palette = json.optJSONArray("palette").toIntList(),
                layer0 = json.optJSONArray("layer_0").toIntList(),
                layer1 = json.optJSONArray("layer_1").toIntList(),
            )
        }.onFailure { current = null }
    }

    private fun JSONArray?.toIntList(): List<Int> {
        if (this == null) return emptyList()
        return List(length()) { getInt(it) }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), backgroundPaint)
        canvas.drawText("맵 갤러리 / Map Gallery", 4f, 12f, labelPaint)

        if (mapList.isEmpty()) {
            canvas.drawText("No maps found", 4f, 28f, labelPaint)
            return
        }

        val map = current ?: run {
            canvas.drawText("Failed to load ${mapList[mapIndex]}", 4f, 28f, labelPaint)
            return
        }

        canvas.drawText("${mapIndex + 1}/${mapList.size}  ${map.name}  ${map.w}×${map.h}", 4f, 24f, labelPaint)
        canvas.drawText("Layer ${layerIndex} ${if (layerIndex == 0) "(terrain)" else "(objects)"}", 4f, 36f, hintPaint)
        canvas.drawText("palette: ${map.palette.size} tiles", 4f, 46f, hintPaint)

        // 그리드 렌더 영역 (가운데 정렬)
        val layer = if (layerIndex == 0) map.layer0 else map.layer1
        val gridW = map.w * cellSize
        val gridH = map.h * cellSize
        val originX = (virtualWidth - gridW) / 2
        val originY = 56

        for (ty in 0 until map.h) {
            for (tx in 0 until map.w) {
                val i = ty * map.w + tx
                if (i >= layer.size) continue
                val tileId = layer[i]
                cellPaint.color = colorForTile(tileId, layerIndex)
                val left = originX + tx * cellSize
                val top = originY + ty * cellSize
                canvas.drawRect(left.toFloat(), top.toFloat(),
                                (left + cellSize).toFloat(), (top + cellSize).toFloat(), cellPaint)
            }
        }

        canvas.drawText("◀▶ map  ▲▼ layer  OK cell-size", 4f, virtualHeight - 4f, hintPaint)
    }

    private fun colorForTile(tileId: Int, layer: Int): Int {
        if (tileId == 0) return Color.rgb(20, 20, 30)
        // 안정적 RGB 해시
        val h = (tileId * 2654435761L).toInt()
        var r = (h shr 16) and 0xff
        var g = (h shr 8) and 0xff
        var b = h and 0xff
        if (layer == 1) {
            // collision layer는 단순 색상 팔레트
            return when (tileId % 8) {
                0 -> Color.rgb(40, 40, 50)
                1 -> Color.rgb(180, 80, 80)
                2 -> Color.rgb(80, 180, 80)
                3 -> Color.rgb(80, 80, 180)
                4 -> Color.rgb(200, 200, 80)
                5 -> Color.rgb(200, 80, 200)
                6 -> Color.rgb(80, 200, 200)
                else -> Color.rgb(200, 140, 80)
            }
        }
        if (r < 40) r = 40; if (g < 40) g = 40; if (b < 40) b = 40
        return Color.rgb(r, g, b)
    }
}
