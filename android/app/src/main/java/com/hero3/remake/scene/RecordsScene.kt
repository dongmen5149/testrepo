package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.engine.ChestRegistry
import com.hero3.remake.engine.EnemyRegistry
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.QuestRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/** 진척률·통계 요약. */
class RecordsScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2) ||
            input.pressedOnce(InputController.K_OK)) {
            onRequest(MainActivity.SceneRequest.Pop)
        }
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val isEn = settings.language == "en"
        UiKit.drawHeader(canvas, virtualWidth, if (isEn) "RECORDS" else "기록")

        val totalEnemies = EnemyRegistry.all.size
        val seenEnemies  = gameState.defeatedEnemyIds.size
        val totalBosses  = EnemyRegistry.all.count { it.id.startsWith("boss_") }
        val seenBosses   = gameState.defeatedEnemyIds.count { it.startsWith("boss_") }
        val totalChests  = ChestRegistry.all.size
        val openedChests = gameState.openedChestIds.size
        val totalQuests  = QuestRegistry.all.size
        val doneQuests   = gameState.doneQuestIds.size

        UiKit.drawBox(canvas, 8f, 32f, virtualWidth - 16f, 200f)
        var y = 52f
        fun row(label: String, value: String) {
            canvas.drawText(label, 16f, y, UiKit.muted)
            canvas.drawText(value, virtualWidth - 90f, y, UiKit.body)
            y += 18f
        }
        row(if (isEn) "Play time"  else "플레이 시간",  GameState.formatPlayTime(gameState.playTimeMs))
        row(if (isEn) "Gold"       else "소지금",       "${gameState.gold} G")
        row(if (isEn) "Bestiary"   else "도감",         "$seenEnemies / $totalEnemies")
        row(if (isEn) "Bosses"     else "보스",         "$seenBosses / $totalBosses")
        row(if (isEn) "Chests"     else "보물상자",     "$openedChests / $totalChests")
        row(if (isEn) "Quests"     else "퀘스트",       "$doneQuests / $totalQuests")
        row(if (isEn) "Cleared"    else "클리어",
            if (gameState.gameCleared) "★" else "—")

        UiKit.drawHints(canvas, virtualWidth, virtualHeight, "OK / R back")
    }
}
