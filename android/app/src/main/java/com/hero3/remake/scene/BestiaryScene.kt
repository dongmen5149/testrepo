package com.hero3.remake.scene

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import com.hero3.remake.MainActivity
import com.hero3.remake.catalog.Hero3Boss
import com.hero3.remake.engine.EnemyRegistry
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * 적 도감 — 한 번이라도 처치한 적의 스탯/sprite 노출. 미처치는 "???".
 */
class BestiaryScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val list = EnemyRegistry.all
    private var idx = 0
    private val bg = Paint().apply { color = Color.rgb(15, 12, 25) }
    private val spriteCache: MutableMap<String, Bitmap?> = mutableMapOf()

    /** R72: Hero3Catalog 의 보스 목록 — 선택된 enemy 가 보스이면 combat_rating 표시.
     *  MainActivity 의 lazy catalog 가 로드되지 않은 경우 null 반환 (graceful degrade). */
    private val catalogBosses: List<Hero3Boss>? by lazy {
        runCatching {
            (context as? MainActivity)?.catalog?.bossesNormal
        }.getOrNull()
    }

    private fun bossInfoFor(enemyName: String): Hero3Boss? {
        val bosses = catalogBosses ?: return null
        // EnemyRegistry 의 nameKo 와 Hero3Catalog 의 name (EUC-KR 디코드) 매칭
        return bosses.firstOrNull { it.name == enemyName }
    }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2) ||
            input.pressedOnce(InputController.K_OK)) {
            onRequest(MainActivity.SceneRequest.Pop); return
        }
        if (input.pressedOnce(InputController.K_UP))   idx = (idx - 1 + list.size) % list.size
        if (input.pressedOnce(InputController.K_DOWN)) idx = (idx + 1) % list.size
    }

    private fun spriteOf(spriteDir: String): Bitmap? = spriteCache.getOrPut(spriteDir) {
        runCatching {
            val root = "${settings.spritesDir()}/$spriteDir"
            val files = context.assets.list(root)?.filter { it.endsWith(".png") }?.sorted() ?: return@runCatching null
            if (files.isEmpty()) return@runCatching null
            context.assets.open("$root/${files.first()}").use { BitmapFactory.decodeStream(it) }
        }.getOrNull()
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val isEn = settings.isEn
        UiKit.drawHeader(canvas, virtualWidth, if (isEn) "BESTIARY" else "도감")

        val unlocked = gameState.defeatedEnemyIds
        // 좌측 목록
        val rowH = 12f
        UiKit.drawBox(canvas, 4f, 32f, 130f, rowH * list.size + 8f)
        for ((i, e) in list.withIndex()) {
            val y = 44f + i * rowH
            if (i == idx) canvas.drawRect(6f, y - 9f, 132f, y + 1f,
                Paint().apply { color = Color.argb(120, 255, 220, 90) })
            val seen = e.id in unlocked
            val nm = if (seen) (if (isEn) e.nameEn else e.nameKo) else "???"
            canvas.drawText("${i + 1}. $nm", 8f, y, if (seen) UiKit.body else UiKit.muted)
        }

        // 우측 상세
        val sel = list[idx]
        val seen = sel.id in unlocked
        UiKit.drawBox(canvas, 138f, 32f, 98f, virtualHeight - 60f)
        if (seen) {
            spriteOf(sel.spriteDir)?.let { bmp ->
                val scale = 3
                canvas.drawBitmap(bmp, Rect(0, 0, bmp.width, bmp.height),
                    Rect(150, 40, 150 + bmp.width * scale, 40 + bmp.height * scale), null)
            }
            val statsTop = 110f
            canvas.drawText("HP ${sel.hpMax}", 142f, statsTop,        UiKit.body)
            canvas.drawText("ATK ${sel.atk}",  142f, statsTop + 14f,  UiKit.body)
            canvas.drawText("DEF ${sel.def}",  142f, statsTop + 28f,  UiKit.body)
            canvas.drawText("EXP ${sel.expReward}", 142f, statsTop + 42f, UiKit.muted)
            canvas.drawText("${sel.goldReward}G",   142f, statsTop + 56f, UiKit.muted)
            // R72: 보스이면 catalog 의 combat_rating + sprite_idx 추가 표시
            val boss = bossInfoFor(sel.nameKo)
            if (boss?.trailerDecoded != null) {
                val td = boss.trailerDecoded
                canvas.drawText(
                    if (isEn) "★ Boss rating: ${td.combatRating} (recommended lvl)" else "★ 보스 권장 lvl: ${td.combatRating}",
                    142f, statsTop + 70f, UiKit.body,
                )
                canvas.drawText(
                    "sprite #${td.spriteIdx}  ${if (td.isMiscBoss) "misc" else "story"}",
                    142f, statsTop + 84f, UiKit.muted,
                )
            }
            // 드롭 목록
            if (sel.dropTable.isNotEmpty()) {
                val dropY = if (bossInfoFor(sel.nameKo)?.trailerDecoded != null) statsTop + 100f else statsTop + 76f
                canvas.drawText(if (isEn) "Drops:" else "드롭:", 142f, dropY, UiKit.muted)
                var dy = dropY + 12f
                for ((id, p) in sel.dropTable) {
                    val nm = ItemRegistry.get(id)?.let {
                        if (isEn) it.nameEn else it.nameKo
                    } ?: id
                    canvas.drawText("- $nm  ${(p * 100).toInt()}%", 142f, dy, UiKit.muted)
                    dy += 11f
                }
            }
        } else {
            canvas.drawText("???", 170f, 100f, UiKit.muted)
            canvas.drawText(if (isEn) "Defeat to unlock." else "처치 시 해금.",
                146f, 130f, UiKit.muted)
        }

        canvas.drawText("${unlocked.size}/${list.size}", virtualWidth - 40f, virtualHeight - 10f, UiKit.muted)
        UiKit.drawHints(canvas, virtualWidth, virtualHeight, "▲▼  R back")
    }
}
