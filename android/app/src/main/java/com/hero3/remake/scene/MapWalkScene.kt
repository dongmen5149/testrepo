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
import com.hero3.remake.engine.Character
import com.hero3.remake.engine.Chest
import com.hero3.remake.engine.ChestRegistry
import com.hero3.remake.engine.EncounterTable
import com.hero3.remake.engine.EnemyRegistry
import com.hero3.remake.engine.EventBus
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.MapGraph
import com.hero3.remake.engine.Npc
import com.hero3.remake.engine.NpcRegistry
import com.hero3.remake.engine.QuestRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.SfxBus
import com.hero3.remake.engine.UiKit
import kotlin.math.abs
import kotlin.math.sin
import kotlin.random.Random
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

    private data class DecoMarker(val tx: Int, val ty: Int, val id: Int, val type: Int)

    private data class MapData(
        val id: Int,
        val name: String,
        val w: Int,
        val h: Int,
        val palette: List<Int>,
        val layer0: List<Int>,
        val layer1: List<Int>,
        val decorations: List<DecoMarker> = emptyList(),
        /** R109: meta_header_hex 의 첫 byte = theme sheet ID. theme_{themeId}_bm 로 layer_0 렌더. */
        val themeId: Int = -1,
        /** R109: layer_0 raw 값을 `>> themeShift` 하여 sheet 의 row index 얻는다. */
        val themeShift: Int = 0,
    )

    private val tilePx = 16
    private val moveCooldownMs = 130L

    private var toastText: String = ""
    private var toastTtl: Long = 0L

    /** 전투 직후 인카운터 억제. MapWalk 진입 시점부터 3s. */
    private var encounterGraceMs: Long = 3000L
    private var playtimeAccumMs: Long = 0L
    private var stepsSinceSave: Int = 0
    private var tutorialMs: Long = if (!gameState.tutorialShown) 6000L else 0L
    private var leaderCache: Character? = null
    private var leaderCacheStamp: Long = -1L
    private fun cachedLeader(): Character? {
        if (leaderCacheStamp != elapsedMs / 250L) {
            leaderCache = gameState.loadParty().firstOrNull()
            leaderCacheStamp = elapsedMs / 250L
        }
        return leaderCache
    }

    private val isEn: Boolean get() = settings.isEn
    private fun lang(ko: String, en: String): String = settings.lang(ko, en)

    private var moveTimer = 0L
    private var animFrame = 0
    private var animTimer = 0L
    private val animFrameMs = 200L
    private var elapsedMs = 0L

    private val bg = Paint().apply { color = Color.rgb(8, 10, 18) }
    private val tilePaint = Paint()
    private val gridPaint = Paint().apply {
        color = Color.argb(60, 200, 200, 220); style = Paint.Style.STROKE; strokeWidth = 1f
    }

    private var map: MapData? = null
    private val heroWalk: List<List<Bitmap>>  // [dir 0..3][anim 0..7]
    private val npcSprites: MutableMap<String, Bitmap> = mutableMapOf()
    /** R109: theme sheet ID → 16x16 tile bitmap 리스트. lazy load. */
    private val themeTileCache: MutableMap<Int, List<Bitmap>> = mutableMapOf()
    /** R110a: obj sheet ID → frame_idx → 가변 크기 sprite bitmap. lazy load. */
    private val objFrameCache: MutableMap<Int, Map<Int, Bitmap>> = mutableMapOf()

    init {
        loadMap(gameState.currentMapId)
        // 첫 진입 시 hero 좌표 미설정이면 맵 중앙에 배치
        if (gameState.heroX < 0 || gameState.heroY < 0) {
            map?.let { gameState.resetPosition(it.id, it.w / 2, it.h / 2) }
        }
        heroWalk = loadHeroWalk()
        SfxBus.playMusic(SfxBus.Bgm.FIELD)
    }

    private fun loadMap(id: Int) {
        val fileName = "map${id}_mp.json"
        runCatching {
            val text = context.assets.open("maps/$fileName").bufferedReader().use { it.readText() }
            val o = JSONObject(text)
            val w = o.optInt("width")
            val h = o.optInt("height")
            val decoArr = o.optJSONArray("extras_records")
            val decos = if (decoArr == null) emptyList() else List(decoArr.length()) { i ->
                val r = decoArr.getJSONObject(i)
                val tile = r.getJSONArray("tile")
                DecoMarker(tile.getInt(0), tile.getInt(1), r.getInt("id"), r.getInt("type"))
            }
            val l0 = jsonIntArray(o.optJSONArray("layer_0"))
            val themeId = parseFirstHexByte(o.optString("meta_header_hex", ""))
            val themeRows = themeId.takeIf { it >= 0 }?.let { loadThemeTiles(it)?.size ?: 0 } ?: 0
            val themeShift = if (themeRows > 0 && l0.isNotEmpty()) {
                val maxL0 = l0.max()
                var s = 0
                while (s < 8 && (maxL0 shr s) >= themeRows) s++
                if (s < 8) s else 0
            } else 0
            map = MapData(
                id = id,
                name = o.optString("name", "?"),
                w = w, h = h,
                palette = jsonIntArray(o.optJSONArray("palette")),
                layer0 = l0,
                layer1 = jsonIntArray(o.optJSONArray("layer_1")),
                decorations = decos,
                themeId = themeId,
                themeShift = themeShift,
            )
            gameState.markVisited(id)
        }
    }

    /** "06070141" → 0x06 = 6. 비어 있거나 parse 실패 시 -1. */
    private fun parseFirstHexByte(s: String): Int {
        val t = s.trim().replace(" ", "")
        if (t.length < 2) return -1
        return runCatching { t.substring(0, 2).toInt(16) }.getOrDefault(-1)
    }

    /**
     * R109: theme_{id}_bm/frame_00*.png 을 열어 16×16 tile bitmap 리스트로 split.
     * 동일 themeId 재진입 시 cache 사용.
     */
    private fun loadThemeTiles(themeId: Int): List<Bitmap>? {
        if (themeId < 0) return null
        themeTileCache[themeId]?.let { return it }
        val dir = "${settings.spritesDir()}/map/theme_${themeId}_bm"
        return runCatching {
            val files = context.assets.list(dir)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
            if (files.isEmpty()) return@runCatching null
            val sheet = context.assets.open("$dir/${files.first()}").use { BitmapFactory.decodeStream(it) }
            val px = sheet.width  // 보통 16. HD/SD 동일.
            val rows = sheet.height / px
            (0 until rows).map { row -> Bitmap.createBitmap(sheet, 0, row * px, px, px) }
        }.getOrNull()?.also { themeTileCache[themeId] = it }
    }

    /**
     * R110a: obj_{id}_bm/frame_NN_*.png 을 열어 frame_idx → Bitmap map 으로 적재.
     * obj sheet 의 frame 은 가변 크기 sprite (16×16 wall, 24×32 building, 10×42 lamp 등).
     * layer_1[i] >> 6 으로 frame_idx 선택.
     */
    private fun loadObjFrames(objId: Int): Map<Int, Bitmap>? {
        if (objId < 0) return null
        objFrameCache[objId]?.let { return it }
        val dir = "${settings.spritesDir()}/map/obj_${objId}_bm"
        return runCatching {
            val files = context.assets.list(dir)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
            if (files.isEmpty()) return@runCatching null
            val framePat = Regex("frame_(\\d+)_")
            val map = mutableMapOf<Int, Bitmap>()
            for (f in files) {
                val m = framePat.find(f) ?: continue
                val idx = m.groupValues[1].toInt()
                map[idx] = context.assets.open("$dir/$f").use { BitmapFactory.decodeStream(it) }
            }
            map.toMap()
        }.getOrNull()?.also { objFrameCache[objId] = it }
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

    private fun loadHeroWalk(): List<List<Bitmap>> {
        // h0_cif 베이크 결과: dir0..3 × anim 0..7 (32 PNG) + dir_mapping.json (FACING->cif dir 매핑).
        // dir_mapping.json 은 픽셀 symmetry 로 자동 검출 — hero 마다 다름.
        val dir = "${settings.spritesDir()}/hero/h0_walk"
        val dirOrder = loadDirMapping(dir) ?: intArrayOf(0, 1, 2, 3)
        return (0..3).map { facing ->
            val cifDir = dirOrder[facing]
            (0..7).mapNotNull { f ->
                runCatching {
                    context.assets.open("$dir/dir${cifDir}_${f}.png").use { BitmapFactory.decodeStream(it) }
                }.getOrNull()
            }
        }
    }

    private fun loadDirMapping(dir: String): IntArray? = runCatching {
        val text = context.assets.open("$dir/dir_mapping.json").bufferedReader().use { it.readText() }
        // 단순 정규식 파싱 — kotlinx.serialization 의존성 추가 회피.
        val m = Regex("\"facing_to_dir\"\\s*:\\s*\\[\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)\\s*]").find(text)
        m?.let { intArrayOf(it.groupValues[1].toInt(), it.groupValues[2].toInt(), it.groupValues[3].toInt(), it.groupValues[4].toInt()) }
    }.getOrNull()

    private fun isWalkable(x: Int, y: Int): Boolean {
        val m = map ?: return false
        if (x < 0 || y < 0 || x >= m.w || y >= m.h) return false
        // NPC 가 있는 칸은 통행 불가 (patrol 반영)
        if (NpcRegistry.forMap(m.id).any {
                val p = NpcRegistry.effectivePos(it, elapsedMs); p.first == x && p.second == y
            }) return false
        if (m.layer1.isEmpty()) return true
        val idx = y * m.w + x
        if (idx >= m.layer1.size) return true
        return m.layer1[idx] == 0
    }

    private fun tryMove(dx: Int, dy: Int, facing: Int) {
        gameState.heroFacing = facing
        val newX = gameState.heroX + dx
        val newY = gameState.heroY + dy
        val m = map ?: return

        // 맵 경계를 넘어갈 때 → MapGraph 에서 이웃 맵 검색
        if (newX < 0 || newY < 0 || newX >= m.w || newY >= m.h) {
            val side = MapGraph.sideOf(dx, dy) ?: return
            val nextId = MapGraph.neighborOf(m.id, side) ?: return
            transitionTo(nextId, side, gameState.heroX, gameState.heroY)
            return
        }
        if (isWalkable(newX, newY)) {
            gameState.heroX = newX
            gameState.heroY = newY
            // 한 걸음마다 작은 자연 회복 + 5걸음마다 일괄 저장
            stepsSinceSave++
            if (stepsSinceSave >= 5) {
                val party = gameState.loadParty().toMutableList()
                var changed = false
                for (c in party) {
                    if (c.hp < c.hpMax) { c.hp = (c.hp + 2).coerceAtMost(c.hpMax); changed = true }
                    if (c.sp < c.spMax) { c.sp = (c.sp + 1).coerceAtMost(c.spMax); changed = true }
                }
                if (changed) gameState.saveParty(party)
                stepsSinceSave = 0
            }
            // 보물상자 픽업
            val chest = ChestRegistry.at(m.id, newX, newY)
            if (chest != null && chest.id !in gameState.openedChestIds) {
                openChest(chest)
            }
            // 보스 트리거 타일 우선 검사 (인카운터보다 우선)
            val bossId = bossTriggerAt(m.id, newX, newY)
            if (bossId != null && !gameState.isBossDefeated(bossId)) {
                onRequest(MainActivity.SceneRequest.BattleEnemy(bossId))
                return
            }
            if (encounterGraceMs <= 0 && settings.encounterMultiplier > 0f &&
                EncounterTable.shouldEncounter(m.id, Random.nextFloat() / settings.encounterMultiplier)) {
                // R82: catalog 설치되어 있고 party leader 가 있으면 catalog 161 enemies 풀 사용.
                // fallback: EncounterTable (placeholder 13).
                val catalog = com.hero3.remake.catalog.Hero3CatalogProvider.get()
                val leaderLvl = gameState.loadParty().firstOrNull()?.level ?: 1
                val enemyId = catalog
                    ?.let { com.hero3.remake.catalog.Hero3CatalogBridge.randomCatalogEnemyId(it, leaderLvl) }
                    ?: EncounterTable.rollEnemy(m.id)?.id
                if (enemyId != null) {
                    encounterGraceMs = 3000L
                    onRequest(MainActivity.SceneRequest.BattleEnemy(enemyId))
                }
            }
        }
    }

    private fun openChest(chest: Chest) {
        SfxBus.play(SfxBus.Sfx.CHEST)
        val inv = gameState.loadInventory()
        val ok = if (chest.itemId.isNotEmpty()) inv.add(chest.itemId, chest.count) else true
        if (ok) {
            gameState.saveInventory(inv)
            gameState.openedChestIds = gameState.openedChestIds + chest.id
            if (chest.gold > 0) gameState.gold += chest.gold
            val item = ItemRegistry.get(chest.itemId)
            val nm = item?.let { lang(it.nameKo, it.nameEn) } ?: chest.itemId
            val goldStr = if (chest.gold > 0) " +${chest.gold}G" else ""
            EventBus.push(lang("보물상자: $nm ×${chest.count}$goldStr",
                              "Chest: $nm ×${chest.count}$goldStr"))
        } else {
            EventBus.push(lang("가방 가득 — 상자 패스.", "Bag full — chest skipped."))
        }
    }

    private fun bossTriggerAt(mapId: Int, x: Int, y: Int): String? =
        bossTriggersFor(mapId).firstOrNull { it.x == x && it.y == y }?.bossId

    private data class BossTrigger(val x: Int, val y: Int, val bossId: String)

    private fun bossTriggersFor(mapId: Int): List<BossTrigger> = when (mapId) {
        10 -> listOf(BossTrigger(8, 4, "boss_guardian"))
        11 -> listOf(BossTrigger(6, 6, "boss_chaos"))
        12 -> listOf(BossTrigger(10, 6, "boss_sealed"))
        else -> emptyList()
    }

    private fun transitionTo(nextId: Int, fromSide: MapGraph.Side, fromX: Int, fromY: Int) {
        loadMap(nextId)
        val nm = map ?: return
        val (nx, ny) = MapGraph.entryPoint(fromSide, fromX, fromY, nm.w, nm.h)
        gameState.resetPosition(nm.id, nx, ny, gameState.heroFacing)
        moveTimer = 250L   // 전환 직후 잠깐 대기
        encounterGraceMs = 3000L
    }

    override fun update(deltaMs: Long) {
        // gameState 의 맵 ID 가 외부에서 바뀌었으면(예: 패배 부활) 재로딩
        if (map?.id != gameState.currentMapId) loadMap(gameState.currentMapId)
        // 토스트 큐 폴링
        if (toastTtl > 0) toastTtl -= deltaMs
        if (toastTtl <= 0) {
            val next = EventBus.pop()
            if (next != null) { toastText = next; toastTtl = 2500L }
            else { toastText = "" }
        }
        elapsedMs += deltaMs
        if (encounterGraceMs > 0) encounterGraceMs -= deltaMs
        if (tutorialMs > 0) {
            tutorialMs -= deltaMs
            if (tutorialMs <= 0 || input.pressedOnce(InputController.K_OK)) {
                tutorialMs = 0; gameState.tutorialShown = true
            }
        }
        // 플레이 시간 누적 (1초마다 일괄 저장)
        playtimeAccumMs += deltaMs
        if (playtimeAccumMs >= 1000L) {
            gameState.addPlayTime(playtimeAccumMs)
            playtimeAccumMs = 0L
        }
        animTimer += deltaMs
        if (animTimer >= animFrameMs) {
            animTimer = 0L
            animFrame = (animFrame + 1) % 8
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
                val p = NpcRegistry.effectivePos(it, elapsedMs)
                p.first == gameState.heroX + face.first && p.second == gameState.heroY + face.second
            } ?: NpcRegistry.adjacent(gameState.currentMapId, gameState.heroX, gameState.heroY, elapsedMs)
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

        // Layer 0 (terrain) 렌더 — R109: theme_{themeId}_bm 의 row tile bitmap 사용.
        // cache 없으면 색상 grid 로 graceful fallback.
        val themeTiles = if (m.themeId >= 0) loadThemeTiles(m.themeId) else null
        val dst = Rect()
        for (ty in ty0 until ty1) {
            for (tx in tx0 until tx1) {
                val i = ty * m.w + tx
                if (i >= m.layer0.size) continue
                val tileId = m.layer0[i]
                val px = tx * tilePx - camX
                val py = ty * tilePx - camY + hudOffsetY
                val bmp = themeTiles?.getOrNull(tileId shr m.themeShift)
                if (bmp != null) {
                    dst.set(px, py, px + tilePx, py + tilePx)
                    canvas.drawBitmap(bmp, null, dst, null)
                } else {
                    tilePaint.color = colorForTile(tileId, layer = 0)
                    canvas.drawRect(px.toFloat(), py.toFloat(),
                        (px + tilePx).toFloat(), (py + tilePx).toFloat(), tilePaint)
                }
            }
        }
        // Layer 1 (collision/objects) 렌더 — R110a: obj_{themeId}_bm 의 가변 크기 sprite 사용.
        // layer_1[i] >> 6 = frame_idx (NEOSOLTIA 134-map 통계: 99%+ 가 frame_idx<<6 패턴).
        // bottom-center anchor — tile 의 (px, py+tilePx) 에 sprite 바닥 정렬.
        // top-down 순서로 그려 perspective overlap (남쪽 sprite 가 북쪽 위에) 자동.
        val objFrames = if (m.themeId >= 0) loadObjFrames(m.themeId) else null
        for (ty in ty0 until ty1) {
            for (tx in tx0 until tx1) {
                val i = ty * m.w + tx
                if (i >= m.layer1.size) continue
                val tileId = m.layer1[i]
                if (tileId == 0) continue
                val px = tx * tilePx - camX
                val py = ty * tilePx - camY + hudOffsetY
                val sprite = objFrames?.get(tileId shr 6)
                if (sprite != null) {
                    val sx = px + (tilePx - sprite.width) / 2
                    val sy = py + (tilePx - sprite.height)
                    canvas.drawBitmap(sprite, sx.toFloat(), sy.toFloat(), null)
                } else {
                    tilePaint.color = colorForTile(tileId, layer = 1)
                    canvas.drawRect(px.toFloat(), py.toFloat(),
                        (px + tilePx).toFloat(), (py + tilePx).toFloat(), tilePaint)
                }
            }
        }

        // 데코레이션 마커 (_mp extras 해독, 2026-05-07) — id 별 색상으로 작은 점 표시.
        // §4.1 sprite 디코딩 풀리면 진짜 그림으로 교체.
        for (d in m.decorations) {
            if (d.tx !in tx0..tx1 || d.ty !in ty0..ty1) continue
            tilePaint.color = colorForDecoId(d.id)
            val cx = d.tx * tilePx - camX + tilePx / 2
            val cy = d.ty * tilePx - camY + hudOffsetY + tilePx / 2
            canvas.drawCircle(cx.toFloat(), cy.toFloat(), 2.5f, tilePaint)
        }

        // 보물상자 (안 열린 것만)
        for (chest in ChestRegistry.forMap(m.id)) {
            if (chest.id in gameState.openedChestIds) continue
            if (chest.x !in tx0..tx1 || chest.y !in ty0..ty1) continue
            val cx = chest.x * tilePx - camX + 2
            val cy = chest.y * tilePx - camY + hudOffsetY + 2
            tilePaint.color = Color.rgb(180, 130, 40)
            canvas.drawRect(cx.toFloat(), cy.toFloat(),
                (cx + tilePx - 4).toFloat(), (cy + tilePx - 4).toFloat(), tilePaint)
            tilePaint.color = Color.rgb(255, 220, 90)
            canvas.drawRect((cx + 4).toFloat(), (cy + 5).toFloat(),
                (cx + tilePx - 8).toFloat(), (cy + 8).toFloat(), tilePaint)
        }

        // NPC 그리기 (patrol 반영)
        for (npc in NpcRegistry.forMap(gameState.currentMapId)) {
            val (px, py) = NpcRegistry.effectivePos(npc, elapsedMs)
            if (px !in tx0..tx1 || py !in ty0..ty1) continue
            val sprite = loadNpcSprite(npc)
            val nx = px * tilePx - camX + (tilePx - (sprite?.width ?: tilePx)) / 2
            val ny = py * tilePx - camY + (tilePx - (sprite?.height ?: tilePx)) + hudOffsetY
            if (sprite != null) {
                canvas.drawBitmap(sprite, nx.toFloat(), ny.toFloat(), null)
            } else {
                tilePaint.color = Color.rgb(220, 200, 100)
                canvas.drawCircle((px * tilePx - camX + tilePx / 2).toFloat(),
                    (py * tilePx - camY + tilePx / 2 + hudOffsetY).toFloat(),
                    4f, tilePaint)
            }
            // 퀘스트 마커 (! = 새 퀘스트 / ? = 진행 중인데 이 NPC 가 발급자)
            val q = npc.startsQuestId
            if (q != null) {
                val active = gameState.activeQuestIds.contains(q)
                val done   = gameState.doneQuestIds.contains(q)
                val mark = when { !active && !done -> "!"; active && !done -> "?"; else -> null }
                if (mark != null) {
                    val bob = (sin(elapsedMs / 220.0) * 2.0).toFloat()
                    val mp = Paint().apply {
                        color = if (mark == "!") Color.rgb(255, 220, 80) else Color.rgb(120, 200, 255)
                        textSize = 12f; isFakeBoldText = true; textAlign = Paint.Align.CENTER
                    }
                    canvas.drawText(mark,
                        (px * tilePx - camX + tilePx / 2).toFloat(),
                        (py * tilePx - camY + hudOffsetY - 2 + bob),
                        mp)
                }
            }
        }

        // 영웅 그리기 — 방향별 8 frame walk-cycle
        val facing = gameState.heroFacing.coerceIn(0, 3)
        val dirFrames = heroWalk.getOrNull(facing).orEmpty()
        val frame = dirFrames.getOrNull(animFrame % dirFrames.size.coerceAtLeast(1))
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

        // 미니맵 (우측 하단, 60×60) — Settings 토글
        if (settings.minimapVisible) run {
            val miniSize = 60
            val cell = (miniSize.toFloat() / maxOf(m.w, m.h)).coerceAtMost(2f)
            val mapPxMiniW = (m.w * cell).toInt()
            val mapPxMiniH = (m.h * cell).toInt()
            val mx = virtualWidth - mapPxMiniW - 4
            val my = virtualHeight - mapPxMiniH - 14
            // 배경
            tilePaint.color = Color.argb(180, 0, 0, 0)
            canvas.drawRect(mx.toFloat() - 1, my.toFloat() - 1,
                (mx + mapPxMiniW + 1).toFloat(), (my + mapPxMiniH + 1).toFloat(), tilePaint)
            // 충돌
            for (ty in 0 until m.h) {
                for (tx in 0 until m.w) {
                    val i = ty * m.w + tx
                    val blocked = (i < m.layer1.size && m.layer1[i] != 0)
                    tilePaint.color = if (blocked) Color.rgb(80, 80, 100) else Color.rgb(40, 80, 50)
                    canvas.drawRect(mx + tx * cell, my + ty * cell,
                        mx + (tx + 1) * cell, my + (ty + 1) * cell, tilePaint)
                }
            }
            // 보스 트리거 (미처치만, 보라)
            tilePaint.color = Color.rgb(220, 80, 220)
            for ((bx, by, bossId) in bossTriggersFor(m.id)) {
                if (gameState.isBossDefeated(bossId)) continue
                canvas.drawRect(mx + bx * cell, my + by * cell,
                    mx + (bx + 1) * cell, my + (by + 1) * cell, tilePaint)
            }
            // 닫힌 상자 (황금)
            tilePaint.color = Color.rgb(255, 200, 60)
            for (chest in ChestRegistry.forMap(m.id)) {
                if (chest.id in gameState.openedChestIds) continue
                canvas.drawRect(mx + chest.x * cell, my + chest.y * cell,
                    mx + (chest.x + 1) * cell, my + (chest.y + 1) * cell, tilePaint)
            }
            // NPC dots (patrol 반영)
            tilePaint.color = Color.rgb(120, 200, 255)
            for (npc in NpcRegistry.forMap(m.id)) {
                val (px, py) = NpcRegistry.effectivePos(npc, elapsedMs)
                canvas.drawRect(mx + px * cell, my + py * cell,
                    mx + (px + 1) * cell, my + (py + 1) * cell, tilePaint)
            }
            // hero (방향 표시)
            tilePaint.color = Color.rgb(255, 60, 60)
            val hx = mx + gameState.heroX * cell
            val hy = my + gameState.heroY * cell
            canvas.drawRect(hx, hy, hx + cell, hy + cell, tilePaint)
            // 방향 화살표 (작은 사각형으로 가리키는 방향 강조)
            tilePaint.color = Color.WHITE
            val s = (cell / 2f).coerceAtLeast(1f)
            when (gameState.heroFacing) {
                GameState.FACING_UP    -> canvas.drawRect(hx + s/2, hy,           hx + cell - s/2, hy + s/2,        tilePaint)
                GameState.FACING_DOWN  -> canvas.drawRect(hx + s/2, hy + cell - s/2, hx + cell - s/2, hy + cell,    tilePaint)
                GameState.FACING_LEFT  -> canvas.drawRect(hx,       hy + s/2,     hx + s/2,        hy + cell - s/2, tilePaint)
                GameState.FACING_RIGHT -> canvas.drawRect(hx + cell - s/2, hy + s/2, hx + cell,    hy + cell - s/2, tilePaint)
            }
        }

        // HUD (상단 24px)
        UiKit.drawBox(canvas, 0f, 0f, virtualWidth.toFloat(), 24f, radius = 0f)
        canvas.drawText("📍 ${m.name}  (${gameState.heroX},${gameState.heroY})",
            4f, 16f, UiKit.body)
        val leader = cachedLeader()
        if (leader != null) {
            val hudText = "Lv${leader.level} ${leader.exp}/${leader.expToNext()}  HP ${leader.hp}/${leader.hpMax}  SP ${leader.sp}/${leader.spMax}  ${gameState.gold}G"
            canvas.drawText(hudText, virtualWidth - 200f, 16f, UiKit.body)
        }
        // 활성 퀘스트 한 줄 (최상단 active quest)
        val activeId = gameState.activeQuestIds.firstOrNull()
        if (activeId != null) {
            val q = QuestRegistry.get(activeId)
            val title = q?.let { lang(it.titleKo, it.titleEn) } ?: activeId
            val tp = Paint(UiKit.muted).apply { color = Color.rgb(255, 220, 130); textSize = 9f }
            canvas.drawText("◆ $title", 4f, 23f, tp)
        }

        // 인접 NPC 가 있으면 OK 힌트 표시 (patrol 반영)
        val nearbyNpc = NpcRegistry.adjacent(gameState.currentMapId,
            gameState.heroX, gameState.heroY, elapsedMs)
        // 보스 근접 경고 (3타일 이내 + 미처치)
        val bossWarn: String? = run {
            val nearest = bossTriggersFor(m.id).firstOrNull { bt ->
                !gameState.isBossDefeated(bt.bossId) &&
                abs(bt.x - gameState.heroX) + abs(bt.y - gameState.heroY) <= 3
            } ?: return@run null
            val def = EnemyRegistry.get(nearest.bossId)
            val name = def?.let { lang(it.nameKo, it.nameEn) } ?: nearest.bossId
            lang("⚠ 보스 근처: $name", "⚠ Boss nearby: $name")
        }
        val edgeHint: String? = run {
            val sides = mutableListOf<String>()
            if (gameState.heroX == 0          && MapGraph.neighborOf(m.id, MapGraph.Side.W) != null) sides += "◀"
            if (gameState.heroX == m.w - 1    && MapGraph.neighborOf(m.id, MapGraph.Side.E) != null) sides += "▶"
            if (gameState.heroY == 0          && MapGraph.neighborOf(m.id, MapGraph.Side.N) != null) sides += "▲"
            if (gameState.heroY == m.h - 1    && MapGraph.neighborOf(m.id, MapGraph.Side.S) != null) sides += "▼"
            if (sides.isEmpty()) null
            else lang("출구: ${sides.joinToString(" ")}", "Exit: ${sides.joinToString(" ")}")
        }
        val hint = when {
            nearbyNpc != null -> {
                val name = lang(nearbyNpc.nameKo, nearbyNpc.nameEn)
                lang("OK ▶ $name 와(과) 대화", "OK ▶ Talk to $name")
            }
            bossWarn != null -> bossWarn
            edgeHint != null -> edgeHint
            else -> "${context.getString(R.string.hint_dpad_navigate)}  L menu  R title"
        }
        UiKit.drawHints(canvas, virtualWidth, virtualHeight, hint)

        // 튜토리얼 오버레이 (첫 진입)
        if (tutorialMs > 0) {
            val a = (tutorialMs.coerceAtMost(1000L) / 1000f * 220f).toInt().coerceIn(0, 220)
            canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(),
                Paint().apply { color = Color.argb(a, 0, 0, 0) })
            val tp = Paint(UiKit.body).apply { color = Color.rgb(255, 235, 200); textSize = 11f }
            val lines = if (isEn) listOf(
                "Welcome to Hero3 Remake.",
                "",
                "◀▶▲▼  Move",
                "OK     Talk / Interact",
                "L      Main Menu",
                "R      Title",
                "#      (debug screens)",
                "",
                "OK to dismiss.",
            ) else listOf(
                "영웅서기3 리메이크에 오신 것을 환영합니다.",
                "",
                "◀▶▲▼  이동",
                "OK     대화 / 상호작용",
                "L      메인 메뉴",
                "R      타이틀",
                "#      (디버그 화면)",
                "",
                "OK 키로 닫기.",
            )
            var ty = 90f
            for (line in lines) {
                val w = tp.measureText(line)
                canvas.drawText(line, (virtualWidth - w) / 2f, ty, tp)
                ty += 16f
            }
        }

        // 토스트 (중앙 상단)
        if (toastTtl > 0 && toastText.isNotEmpty()) {
            val pad = 8f
            val textW = UiKit.body.measureText(toastText)
            val boxW = textW + pad * 2
            val boxX = (virtualWidth - boxW) / 2f
            val boxY = 30f
            UiKit.drawBox(canvas, boxX, boxY, boxW, 22f)
            canvas.drawText(toastText, boxX + pad, boxY + 14f, UiKit.body)
        }
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

    /** id 별 데코 마커 색상 — 0x3e/0x3f(풀) 녹색, 0x40~0x42 갈색, 그 외 hash 기반. */
    private fun colorForDecoId(id: Int): Int = when (id) {
        0x02 -> Color.rgb(255, 120, 120)        // 특수 마커 (드물게 등장)
        0x3e, 0x3f -> Color.rgb(120, 200, 120)  // 풀/덤불 (가장 흔함)
        0x40, 0x41, 0x42 -> Color.rgb(180, 140, 90)  // 가구류
        0x6f, 0x7a, 0x7b, 0x7c -> Color.rgb(180, 180, 90)
        0x95, 0x96 -> Color.rgb(150, 150, 200)
        0x99, 0x9a, 0x9b -> Color.rgb(200, 150, 200)
        0xaa -> Color.rgb(220, 200, 100)
        0xc6, 0xc7 -> Color.rgb(100, 200, 200)
        0xd1, 0xd2, 0xd3, 0xd4 -> Color.rgb(200, 100, 200)
        else -> {
            val h = (id * 2654435761L).toInt()
            Color.rgb(((h shr 16) and 0xff).coerceIn(80, 255),
                      ((h shr 8) and 0xff).coerceIn(80, 255),
                      (h and 0xff).coerceIn(80, 255))
        }
    }
}
