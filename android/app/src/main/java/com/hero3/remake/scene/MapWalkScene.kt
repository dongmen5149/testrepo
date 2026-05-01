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
import com.hero3.remake.engine.Npc
import com.hero3.remake.engine.NpcRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit
import org.json.JSONObject

/**
 * 게임 본체 — 영웅이 맵 위를 걷는 씬.
 *
 * 현재 (Pre-Ghidra 단계):
 *   - 타일은 색상 그리드로 임시 렌더 (theme/obj BM 의 type 0x0c 미해독)
 *   - Layer 1 (collision) 은 0 = 통행, !=0 = 차단
 *   - 영웅은 hero/h00000_bm 의 멀티프레임을 단순 cycle 로 걷기 애니메이션
 *   - 카메라는 영웅 중심으로 viewport 스크롤
 *
 * Ghidra 후 추가:
 *   - theme/obj BM 실제 그래픽
 *   - NPC sprite 배치 (extras 영역 파싱)
 *   - 출구/이벤트 트리거
 *
 * 입력:
 *   ◀▶▲▼  : 영웅 이동
 *   OK    : 인터랙트 (placeholder)
 *   L     : 메인 메뉴 (씬 push)
 *   R     : 타이틀로
 */
class MapWalkScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private data class MapData(
        val id: Int,
        val name: String,
        val w: Int,
        val h: Int,
        val palette: List<Int>,
        val layer0: List<Int>,
        val layer1: List<Int>,
    )

    private val tilePx = 16
    private val moveCooldownMs = 130L

    private var moveTimer = 0L
    private var animFrame = 0
    private var animTimer = 0L
    private val animFrameMs = 200L

    private val bg = Paint().apply { color = Color.rgb(8, 10, 18) }
    private val tilePaint = Paint()
    private val gridPaint = Paint().apply {
        color = Color.argb(60, 200, 200, 220); style = Paint.Style.STROKE; strokeWidth = 1f
    }

    private var map: MapData? = null
    private val heroFrames: List<Bitmap>
    private val npcSprites: MutableMap<String, Bitmap> = mutableMapOf()

    init {
        loadMap(gameState.currentMapId)
        // 첫 진입 시 hero 좌표 미설정이면 맵 중앙에 배치
        if (gameState.heroX < 0 || gameState.heroY < 0) {
            map?.let { gameState.resetPosition(it.id, it.w / 2, it.h / 2) }
        }
        heroFrames = loadHeroFrames()
    }

    private fun loadMap(id: Int) {
        val fileName = "map${id}_mp.json"
        runCatching {
            val text = context.assets.open("maps/$fileName").bufferedReader().use { it.readText() }
            val o = JSONObject(text)
            val w = o.optInt("width")
            val h = o.optInt("height")
            map = MapData(
                id = id,
                name = o.optString("name", "?"),
                w = w, h = h,
                palette = jsonIntArray(o.optJSONArray("palette")),
                layer0 = jsonIntArray(o.optJSONArray("layer_0")),
                layer1 = jsonIntArray(o.optJSONArray("layer_1")),
            )
        }
    }

    private fun jsonIntArray(arr: org.json.JSONArray?): List<Int> {
        if (arr == null) return emptyList()
        return List(arr.length()) { arr.getInt(it) }
    }

    private fun facingTile(facing: Int): Pair<Int, Int> = when (facing) {
        GameState.FACING_UP -> 0 to -1
        GameState.FACING_DOWN -> 0 to 1
        GameState.FACING_LEFT -> -1 to 0
        GameState.FACING_RIGHT -> 1 to 0
        else -> 0 to 1
    }

    private fun loadNpcSprite(npc: Npc): Bitmap? {
        npcSprites[npc.id]?.let { return it }
        val dir = "${settings.spritesDir()}/${npc.spriteDir}"
        return runCatching {
            val files = context.assets.list(dir)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
            if (files.isEmpty()) return null
            context.assets.open("$dir/${files.first()}").use { BitmapFactory.decodeStream(it) }
        }.getOrNull()?.also { npcSprites[npc.id] = it }
    }

    private fun loadHeroFrames(): List<Bitmap> {
        val dir = "${settings.spritesDir()}/hero/h00000_bm"
        val files = runCatching {
            context.assets.list(dir)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
        }.getOrDefault(emptyList())
        return files.mapNotNull { name ->
            runCatching {
                context.assets.open("$dir/$name").use { BitmapFactory.decodeStream(it) }
            }.getOrNull()
        }
    }

    private fun isWalkable(x: Int, y: Int): Boolean {
        val m = map ?: return false
        if (x < 0 || y < 0 || x >= m.w || y >= m.h) return false
        // NPC 가 있는 칸은 통행 불가
        if (NpcRegistry.forMap(m.id).any { it.x == x && it.y == y }) return false
        if (m.layer1.isEmpty()) return true
        val idx = y * m.w + x
        if (idx >= m.layer1.size) return true
        return m.layer1[idx] == 0
    }

    private fun tryMove(dx: Int, dy: Int, facing: Int) {
        gameState.heroFacing = facing
        val newX = gameState.heroX + dx
        val newY = gameState.heroY + dy
        if (isWalkable(newX, newY)) {
            gameState.heroX = newX
            gameState.heroY = newY
        }
    }

    override fun update(deltaMs: Long) {
        animTimer += deltaMs
        if (animTimer >= animFrameMs) {
            animTimer = 0L
            animFrame = (animFrame + 1) % heroFrames.size.coerceAtLeast(1)
        }

        moveTimer -= deltaMs
        if (moveTimer <= 0L) {
            var moved = false
            when {
                input.isPressed(InputController.K_LEFT) -> { tryMove(-1, 0, GameState.FACING_LEFT); moved = true }
                input.isPressed(InputController.K_RIGHT) -> { tryMove(1, 0, GameState.FACING_RIGHT); moved = true }
                input.isPressed(InputController.K_UP) -> { tryMove(0, -1, GameState.FACING_UP); moved = true }
                input.isPressed(InputController.K_DOWN) -> { tryMove(0, 1, GameState.FACING_DOWN); moved = true }
            }
            if (moved) moveTimer = moveCooldownMs
        }

        if (input.pressedOnce(InputController.K_OK)) {
            // 영웅이 바라보는 칸의 NPC 와 대화 (없으면 인접 NPC 검색)
            val face = facingTile(gameState.heroFacing)
            val targetNpc = NpcRegistry.forMap(gameState.currentMapId).firstOrNull {
                it.x == gameState.heroX + face.first && it.y == gameState.heroY + face.second
            } ?: NpcRegistry.adjacent(gameState.currentMapId, gameState.heroX, gameState.heroY)
            if (targetNpc != null) {
                onRequest(MainActivity.SceneRequest.NpcDialogue(targetNpc.id))
            }
        }
        if (input.pressedOnce(InputController.K_SOFT1)) {
            onRequest(MainActivity.SceneRequest.MainMenu)
        }
        if (input.pressedOnce(InputController.K_SOFT2)) {
            onRequest(MainActivity.SceneRequest.Title)
        }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val m = map ?: run {
            canvas.drawText("Map not loaded", 8f, 20f, UiKit.body)
            return
        }

        // 카메라: 영웅을 중심에 두되, 맵 경계를 넘지 않도록 clamp
        val viewportW = virtualWidth
        val viewportH = virtualHeight - 24       // 위 24px = HUD
        val mapPxW = m.w * tilePx
        val mapPxH = m.h * tilePx
        var camX = gameState.heroX * tilePx + tilePx / 2 - viewportW / 2
        var camY = gameState.heroY * tilePx + tilePx / 2 - viewportH / 2
        camX = camX.coerceIn(0, maxOf(0, mapPxW - viewportW))
        camY = camY.coerceIn(0, maxOf(0, mapPxH - viewportH))

        // viewport 영역 결정
        val tx0 = (camX / tilePx).coerceAtLeast(0)
        val ty0 = (camY / tilePx).coerceAtLeast(0)
        val tx1 = ((camX + viewportW) / tilePx + 1).coerceAtMost(m.w)
        val ty1 = ((camY + viewportH) / tilePx + 1).coerceAtMost(m.h)
        val hudOffsetY = 24

        // Layer 0 (terrain) 렌더 — 색상 그리드로 임시
        for (ty in ty0 until ty1) {
            for (tx in tx0 until tx1) {
                val i = ty * m.w + tx
                if (i >= m.layer0.size) continue
                val tileId = m.layer0[i]
                tilePaint.color = colorForTile(tileId, layer = 0)
                val px = tx * tilePx - camX
                val py = ty * tilePx - camY + hudOffsetY
                canvas.drawRect(px.toFloat(), py.toFloat(),
                    (px + tilePx).toFloat(), (py + tilePx).toFloat(), tilePaint)
            }
        }
        // Layer 1 (collision/objects) 렌더 — 비-0 만 색상 패널 (반투명)
        for (ty in ty0 until ty1) {
            for (tx in tx0 until tx1) {
                val i = ty * m.w + tx
                if (i >= m.layer1.size) continue
                val tileId = m.layer1[i]
                if (tileId == 0) continue
                tilePaint.color = colorForTile(tileId, layer = 1)
                val px = tx * tilePx - camX
                val py = ty * tilePx - camY + hudOffsetY
                canvas.drawRect(px.toFloat(), py.toFloat(),
                    (px + tilePx).toFloat(), (py + tilePx).toFloat(), tilePaint)
            }
        }

        // NPC 그리기
        for (npc in NpcRegistry.forMap(gameState.currentMapId)) {
            if (npc.x !in tx0..tx1 || npc.y !in ty0..ty1) continue
            val sprite = loadNpcSprite(npc)
            val nx = npc.x * tilePx - camX + (tilePx - (sprite?.width ?: tilePx)) / 2
            val ny = npc.y * tilePx - camY + (tilePx - (sprite?.height ?: tilePx)) + hudOffsetY
            if (sprite != null) {
                canvas.drawBitmap(sprite, nx.toFloat(), ny.toFloat(), null)
            } else {
                tilePaint.color = Color.rgb(220, 200, 100)
                canvas.drawCircle((npc.x * tilePx - camX + tilePx / 2).toFloat(),
                    (npc.y * tilePx - camY + tilePx / 2 + hudOffsetY).toFloat(),
                    4f, tilePaint)
            }
        }

        // 영웅 그리기 (현재 frame)
        val frame = heroFrames.getOrNull(animFrame.coerceAtMost(heroFrames.size - 1))
        if (frame != null) {
            val hx = gameState.heroX * tilePx - camX + (tilePx - frame.width) / 2
            val hy = gameState.heroY * tilePx - camY + (tilePx - frame.height) + hudOffsetY
            canvas.drawBitmap(frame, hx.toFloat(), hy.toFloat(), null)
        } else {
            // sprite 없으면 화살표
            val hx = (gameState.heroX * tilePx - camX + tilePx / 2).toFloat()
            val hy = (gameState.heroY * tilePx - camY + tilePx / 2 + hudOffsetY).toFloat()
            tilePaint.color = Color.YELLOW
            canvas.drawCircle(hx, hy, 4f, tilePaint)
        }

        // HUD (상단 24px)
        UiKit.drawBox(canvas, 0f, 0f, virtualWidth.toFloat(), 24f, radius = 0f)
        canvas.drawText("📍 ${m.name}  (${gameState.heroX},${gameState.heroY})",
            4f, 16f, UiKit.body)

        // 인접 NPC 가 있으면 OK 힌트 표시
        val nearbyNpc = NpcRegistry.forMap(gameState.currentMapId).firstOrNull { npc ->
            val dx = kotlin.math.abs(npc.x - gameState.heroX)
            val dy = kotlin.math.abs(npc.y - gameState.heroY)
            (dx + dy) == 1
        }
        val hint = if (nearbyNpc != null) {
            val name = if (settings.language == "en") nearbyNpc.nameEn else nearbyNpc.nameKo
            if (settings.language == "en") "OK ▶ Talk to $name" else "OK ▶ ${name} 와(과) 대화"
        } else {
            "${context.getString(R.string.hint_dpad_navigate)}  L menu  R title"
        }
        UiKit.drawHints(canvas, virtualWidth, virtualHeight, hint)
    }

    private fun colorForTile(tileId: Int, layer: Int): Int {
        if (tileId == 0) return if (layer == 0) Color.rgb(40, 80, 50) else Color.TRANSPARENT
        // 안정적 hash → RGB
        val h = (tileId * 2654435761L).toInt()
        var r = (h shr 16) and 0xff
        var g = (h shr 8) and 0xff
        var b = h and 0xff
        if (layer == 1) {
            // 충돌 layer는 회색조로 어둡게
            val v = ((r + g + b) / 3).coerceIn(60, 200)
            return Color.rgb(v, v - 20, v - 30)
        }
        if (r < 50) r = 50; if (g < 50) g = 50; if (b < 50) b = 50
        return Color.rgb(r, g, b)
    }
}
