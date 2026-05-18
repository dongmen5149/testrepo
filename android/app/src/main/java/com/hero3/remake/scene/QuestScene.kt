package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.QuestRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * 퀘스트 목록 — 활성/완료 분리 표시.
 * UP/DOWN 으로 선택, 우측에 desc 표시.
 */
class QuestScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val active = gameState.activeQuestIds.toList().sorted()
    private val done   = gameState.doneQuestIds.toList().sorted()
    private val combined = active.map { it to true } + done.map { it to false }

    private var idx = 0
    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }
    private val activeColor = Paint(UiKit.body).apply { color = Color.rgb(255, 220, 90) }
    private val doneColor   = Paint(UiKit.body).apply { color = Color.rgb(140, 200, 140) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2) ||
            input.pressedOnce(InputController.K_OK)) {
            onRequest(MainActivity.SceneRequest.Pop); return
        }
        if (combined.isEmpty()) return
        if (input.pressedOnce(InputController.K_UP))   idx = (idx - 1 + combined.size) % combined.size
        if (input.pressedOnce(InputController.K_DOWN)) idx = (idx + 1) % combined.size
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth, context.getString(R.string.txt_011))   // QUEST
        val isEn = settings.isEn
        canvas.drawText("${gameState.gold} G", virtualWidth - 60f, 20f,
            Paint(UiKit.body).apply { color = Color.rgb(255, 220, 90) })

        if (combined.isEmpty()) {
            canvas.drawText(if (isEn) "(no quests)" else "(퀘스트 없음)", 16f, 60f, UiKit.muted)
            UiKit.drawHints(canvas, virtualWidth, virtualHeight, context.getString(R.string.hint_back_cancel))
            return
        }

        UiKit.drawBox(canvas, 8f, 32f, virtualWidth - 16f, 14f * combined.size + 12f)
        for ((i, item) in combined.withIndex()) {
            val (qid, isActive) = item
            val q = QuestRegistry.get(qid)
            val title = q?.let { if (isEn) it.titleEn else it.titleKo } ?: qid
            val tag = if (isActive) "●" else "✓"
            val paint = if (isActive) activeColor else doneColor
            val y = 50f + i * 14f
            if (i == idx) {
                canvas.drawRect(10f, y - 11f, virtualWidth - 18f, y + 2f,
                    Paint().apply { color = Color.argb(120, 255, 220, 90) })
            }
            canvas.drawText("$tag $title", 16f, y, paint)
        }

        // 선택된 퀘스트 상세
        val sel = combined.getOrNull(idx)
        if (sel != null) {
            val (qid, isActive) = sel
            val q = QuestRegistry.get(qid)
            UiKit.drawBox(canvas, 8f, virtualHeight - 90f, virtualWidth - 16f, 60f)
            val desc = q?.let { if (isEn) it.descEn else it.descKo } ?: ""
            canvas.drawText(desc, 14f, virtualHeight - 72f, UiKit.body)
            // 진행도
            if (q != null && isActive) {
                val requiredItemId = q.requiredItemId
                val defeatBossId = q.defeatBossId
                val progress = when {
                    requiredItemId != null -> {
                        val owned = gameState.loadInventory().all()
                            .filter { it.itemId == requiredItemId }.sumOf { it.count }
                        val nm = ItemRegistry.get(requiredItemId)?.let {
                            if (isEn) it.nameEn else it.nameKo
                        } ?: requiredItemId
                        "$nm: $owned/${q.requiredItemCount}"
                    }
                    defeatBossId != null -> {
                        val done = gameState.isBossDefeated(defeatBossId)
                        if (isEn) (if (done) "Boss: defeated" else "Boss: alive")
                        else      (if (done) "보스: 처치" else "보스: 미처치")
                    }
                    else -> ""
                }
                if (progress.isNotEmpty()) {
                    canvas.drawText(progress, 14f, virtualHeight - 56f, UiKit.body)
                }
            }
            if (q != null && (q.rewardGold > 0 || q.rewardItemId != null)) {
                val r = buildString {
                    append(if (isEn) "Reward: " else "보상: ")
                    if (q.rewardGold > 0) append("${q.rewardGold}G ")
                    q.rewardItemId?.let { append(it) }
                }
                canvas.drawText(r, 14f, virtualHeight - 40f, UiKit.muted)
            }
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            "${context.getString(R.string.hint_dpad_navigate)}  ${context.getString(R.string.hint_back_cancel)}")
    }
}
