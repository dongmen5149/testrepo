package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.R
import com.hero3.remake.engine.Character
import com.hero3.remake.engine.CharacterRegistry
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * 상태 화면 — GameState 의 파티 + CharacterRegistry 의 base stats 를 표시.
 * LEFT/RIGHT 로 파티 멤버 전환.
 */
class StatusScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private val party: MutableList<Character> = gameState.loadParty().toMutableList()
    private var idx: Int = 0

    private val bg = Paint().apply { color = Color.rgb(15, 18, 30) }
    private val heroSprite: android.graphics.Bitmap? = runCatching {
        val root = "${settings.spritesDir()}/hero/h00000_bm"
        val files = context.assets.list(root)?.filter { it.endsWith(".png") }?.sorted() ?: emptyList()
        if (files.isEmpty()) null
        else context.assets.open("$root/${files.first()}").use {
            android.graphics.BitmapFactory.decodeStream(it)
        }
    }.getOrNull()

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2) ||
            input.pressedOnce(InputController.K_OK)) {
            onRequest(MainActivity.SceneRequest.Pop)
        }
        if (party.size > 1) {
            if (input.pressedOnce(InputController.K_LEFT))
                idx = (idx - 1 + party.size) % party.size
            if (input.pressedOnce(InputController.K_RIGHT))
                idx = (idx + 1) % party.size
        }
        // L 키 = 같은 영웅 내 클래스 cycle
        if (input.pressedOnce(InputController.K_SOFT1)) cycleClass()
    }

    private fun cycleClass() {
        val ch = party.getOrNull(idx) ?: return
        val prefix = when (ch.id) { "kei" -> "kei_"; "ritz" -> "ritz_"; else -> return }
        val candidates = CharacterRegistry.classes.filter { it.id.startsWith(prefix) }
        if (candidates.isEmpty()) return
        val curIdx = candidates.indexOfFirst { it.id == ch.classId }
        val nextIdx = (curIdx + 1) % candidates.size
        val newClassId = candidates[nextIdx].id
        // 새 클래스의 base 로 HP/SP 재계산. 비율 보존.
        val hpRatio = ch.hp.toFloat() / ch.hpMax.coerceAtLeast(1)
        val spRatio = ch.sp.toFloat() / ch.spMax.coerceAtLeast(1)
        val newCh = CharacterRegistry.newCharacter(ch.id, newClassId, ch.level).copy(
            exp = ch.exp,
            equipWeapon = ch.equipWeapon,
            equipArmor = ch.equipArmor,
            equipAccessory = ch.equipAccessory,
        )
        newCh.hp = (newCh.hpMax * hpRatio).toInt().coerceAtLeast(1)
        newCh.sp = (newCh.spMax * spRatio).toInt().coerceAtLeast(0)
        party[idx] = newCh
        gameState.saveParty(party)
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        UiKit.drawHeader(canvas, virtualWidth, context.getString(R.string.txt_001))  // STATUS

        val ch = party.getOrNull(idx)
        val cls = ch?.let { CharacterRegistry.classOf(it.classId) }
        val charName = when (ch?.id) {
            "kei"  -> settings.lang("케이", "Kei")
            "ritz" -> settings.lang("리츠", "Ritz")
            else   -> ch?.id ?: "-"
        }
        val className = cls?.let { settings.lang(it.nameKo, it.nameEn) } ?: "-"

        // 캐릭터 정보 박스
        UiKit.drawBox(canvas, 8f, 32f, virtualWidth - 16f, 80f)
        // 영웅 포트레이트 (3× scale, 우측 상단)
        heroSprite?.let { bmp ->
            val s = 3
            val dx = virtualWidth - bmp.width * s - 12
            val dy = 36
            canvas.drawBitmap(bmp, android.graphics.Rect(0, 0, bmp.width, bmp.height),
                android.graphics.Rect(dx, dy, dx + bmp.width * s, dy + bmp.height * s), null)
        }
        canvas.drawText(context.getString(R.string.txt_017) + ": $charName", 16f, 50f, UiKit.body)
        canvas.drawText("CLASS: $className", 16f, 64f, UiKit.body)
        canvas.drawText(context.getString(R.string.txt_048) + " ${ch?.level ?: 1}",          16f, 78f, UiKit.body)
        canvas.drawText(context.getString(R.string.txt_049) + ": ${ch?.hp}/${ch?.hpMax}",   16f, 92f, UiKit.body)
        canvas.drawText(context.getString(R.string.txt_050) + ": ${ch?.sp}/${ch?.spMax}",   120f, 92f, UiKit.body)
        // HP / SP 바
        if (ch != null) {
            val bgP  = android.graphics.Paint().apply { color = android.graphics.Color.argb(120, 60, 60, 80) }
            val hpP  = android.graphics.Paint().apply { color = android.graphics.Color.rgb(220, 80, 80) }
            val spP  = android.graphics.Paint().apply { color = android.graphics.Color.rgb(80, 140, 220) }
            val barH = 3f
            // HP
            canvas.drawRect(60f, 88f, 60f + 50f, 88f + barH, bgP)
            canvas.drawRect(60f, 88f, 60f + 50f * (ch.hp.toFloat() / ch.hpMax.coerceAtLeast(1)), 88f + barH, hpP)
            // SP
            canvas.drawRect(160f, 88f, 160f + 50f, 88f + barH, bgP)
            canvas.drawRect(160f, 88f, 160f + 50f * (ch.sp.toFloat() / ch.spMax.coerceAtLeast(1)), 88f + barH, spP)
        }
        val expNeed = ch?.expToNext() ?: 1
        val expCur  = ch?.exp ?: 0
        canvas.drawText(context.getString(R.string.txt_051) + ": $expCur / $expNeed",
            16f, 106f, UiKit.muted)
        // EXP 바
        val barX = 16f; val barY = 108f; val barW = 100f; val barH = 4f
        val ratio = (expCur.toFloat() / expNeed.coerceAtLeast(1)).coerceIn(0f, 1f)
        canvas.drawRect(barX, barY, barX + barW, barY + barH,
            android.graphics.Paint().apply { color = android.graphics.Color.argb(120, 60, 60, 80) })
        canvas.drawRect(barX, barY, barX + barW * ratio, barY + barH,
            android.graphics.Paint().apply { color = android.graphics.Color.rgb(120, 200, 120) })
        canvas.drawText("${gameState.gold} G", virtualWidth - 60f, 106f, UiKit.body)

        // 스탯 박스
        UiKit.drawBox(canvas, 8f, 120f, virtualWidth - 16f, 130f)
        val s = cls?.base
        val statRows = listOf(
            R.string.txt_052 to (s?.str?.toString()  ?: "-"),
            R.string.txt_053 to (s?.dex?.toString()  ?: "-"),
            R.string.txt_054 to (s?.vit?.toString()  ?: "-"),
            R.string.txt_055 to (s?.intl?.toString() ?: "-"),
            R.string.txt_056 to (s?.att1?.toString() ?: "-"),
            R.string.txt_057 to (s?.att2?.toString() ?: "-"),
            R.string.txt_058 to (s?.pdef?.toString() ?: "-"),
            R.string.txt_059 to (s?.mdef?.toString() ?: "-"),
            R.string.txt_060 to (s?.let { "${it.cri}%" } ?: "-"),
            R.string.txt_061 to (s?.let { "${it.res}%" } ?: "-"),
            R.string.txt_062 to (s?.acc?.toString() ?: "-"),
            R.string.txt_063 to (s?.dod?.toString() ?: "-"),
        )
        for ((i, row) in statRows.withIndex()) {
            val col = i % 2
            val r = i / 2
            val x = 16f + col * 110f
            val y = 138f + r * 16f
            canvas.drawText(context.getString(row.first), x, y, UiKit.muted)
            canvas.drawText(row.second, x + 50f, y, UiKit.body)
        }

        // 장비 + Effective ATK/DEF
        if (ch != null) {
            UiKit.drawBox(canvas, 8f, 254f, virtualWidth - 16f, 60f)
            fun itemName(id: String?): String {
                val it = id?.let { ItemRegistry.get(it) } ?: return settings.lang("(없음)", "(none)")
                return settings.lang(it.nameKo, it.nameEn)
            }
            canvas.drawText(settings.lang("무기: ", "Weapon: ") + itemName(ch.equipWeapon),    16f, 268f, UiKit.body)
            canvas.drawText(settings.lang("방어: ", "Armor:  ") + itemName(ch.equipArmor),     16f, 282f, UiKit.body)
            canvas.drawText(settings.lang("장신: ", "Accy:   ") + itemName(ch.equipAccessory), 16f, 296f, UiKit.body)
            val ea = CharacterRegistry.effectiveAttack(ch)
            val ed = CharacterRegistry.effectiveDefense(ch)
            canvas.drawText("ATK $ea  DEF $ed", virtualWidth - 100f, 296f, UiKit.body)
        }

        val nav = if (party.size > 1) "◀▶ ${idx + 1}/${party.size}  " else ""
        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            nav + settings.lang("L 직업  ", "L class  ") + context.getString(R.string.hint_back_cancel))
    }
}
