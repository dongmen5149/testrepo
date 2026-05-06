package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.CharacterRegistry
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.SkillRegistry
import com.hero3.remake.engine.UiKit

/**
 * 스킬 목록 — 파티 멤버별 클래스 스킬 + 잠금/해금 표시.
 * LEFT/RIGHT 멤버 전환, UP/DOWN 스킬 선택.
 */
class SkillScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val party = gameState.loadParty()
    private var memberIdx = 0
    private var skillIdx = 0

    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }
    private val unlocked = Paint(UiKit.body).apply { color = Color.rgb(255, 240, 180) }
    private val locked   = Paint(UiKit.body).apply { color = Color.rgb(100, 100, 110) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2) ||
            input.pressedOnce(InputController.K_OK)) {
            onRequest(MainActivity.SceneRequest.Pop); return
        }
        if (party.size > 1) {
            if (input.pressedOnce(InputController.K_LEFT))  { memberIdx = (memberIdx - 1 + party.size) % party.size; skillIdx = 0 }
            if (input.pressedOnce(InputController.K_RIGHT)) { memberIdx = (memberIdx + 1) % party.size; skillIdx = 0 }
        }
        val all = currentAll()
        if (all.isNotEmpty()) {
            if (input.pressedOnce(InputController.K_UP))   skillIdx = (skillIdx - 1 + all.size) % all.size
            if (input.pressedOnce(InputController.K_DOWN)) skillIdx = (skillIdx + 1) % all.size
        }
    }

    private fun currentAll() = party.getOrNull(memberIdx)?.let { ch ->
        SkillRegistry.forClass(ch.classId, level = 99)
    } ?: emptyList()

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth, context.getString(R.string.txt_010))   // SKILL
        val isEn = settings.isEn
        val ch = party.getOrNull(memberIdx)
        if (ch == null) {
            canvas.drawText("(no party)", 16f, 60f, UiKit.muted); return
        }
        val cls = CharacterRegistry.classOf(ch.classId)
        val nm = when (ch.id) { "kei" -> if (isEn) "Kei" else "케이"; "ritz" -> if (isEn) "Ritz" else "리츠"; else -> ch.id }
        val cn = if (isEn) cls?.nameEn else cls?.nameKo
        canvas.drawText("$nm  Lv${ch.level}  ($cn)", 16f, 44f, UiKit.body)

        val skills = SkillRegistry.forClass(ch.classId, level = 99)
        UiKit.drawBox(canvas, 8f, 52f, virtualWidth - 16f, 14f * skills.size + 12f)
        for ((i, s) in skills.withIndex()) {
            val y = 70f + i * 14f
            val ok = ch.level >= s.requiredLevel
            val paint = if (ok) unlocked else locked
            if (i == skillIdx) {
                canvas.drawRect(10f, y - 11f, virtualWidth - 18f, y + 2f,
                    Paint().apply { color = Color.argb(120, 255, 220, 90) })
            }
            val name = if (isEn) s.nameEn else s.nameKo
            val tag = if (ok) "" else " (Lv${s.requiredLevel})"
            canvas.drawText("$name$tag", 16f, y, paint)
            canvas.drawText("SP ${s.spCost}", virtualWidth - 50f, y, paint)
        }

        val sel = skills.getOrNull(skillIdx)
        if (sel != null) {
            UiKit.drawBox(canvas, 8f, virtualHeight - 70f, virtualWidth - 16f, 40f)
            val name = if (isEn) sel.nameEn else sel.nameKo
            canvas.drawText(name, 14f, virtualHeight - 54f, UiKit.body)
            val mulText = if (sel.heal) {
                val parts = mutableListOf<String>()
                if (sel.powerMul > 0f) parts += if (isEn) "INT×${sel.powerMul}" else "INT×${sel.powerMul}"
                if (sel.flatBonus > 0) parts += "+${sel.flatBonus}"
                (if (isEn) "Heal: " else "회복: ") + parts.joinToString(" ")
            } else {
                val parts = mutableListOf<String>()
                if (sel.powerMul != 1f) parts += "ATK×${sel.powerMul}"
                if (sel.flatBonus > 0) parts += "+${sel.flatBonus}"
                "DMG: " + parts.joinToString(" ")
            }
            canvas.drawText(mulText, 14f, virtualHeight - 40f, UiKit.muted)
        }

        val nav = if (party.size > 1) "◀▶ ${memberIdx + 1}/${party.size}  " else ""
        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            nav + "${context.getString(R.string.hint_dpad_navigate)}  ${context.getString(R.string.hint_back_cancel)}")
    }
}
