package com.hero3.remake.scene

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import com.hero3.remake.MainActivity
import com.hero3.remake.engine.Character
import com.hero3.remake.engine.CharacterRegistry
import com.hero3.remake.engine.EnemyInstance
import com.hero3.remake.engine.EnemyRegistry
import com.hero3.remake.engine.EventBus
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Inventory
import com.hero3.remake.engine.ItemKind
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.PartyTurnOrder
import com.hero3.remake.engine.QuestLog
import com.hero3.remake.engine.QuestRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.SfxBus
import com.hero3.remake.engine.Skill
import com.hero3.remake.engine.SkillRegistry
import com.hero3.remake.engine.UiKit
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sin
import kotlin.random.Random

/**
 * 턴제 전투 — 파티(살아있는 멤버 전원) vs 적 1마리.
 *
 * 라운드 = 살아있는 모든 파티 멤버가 순서대로 행동 → 적 1회 (랜덤 살아있는 멤버 타겟).
 * 패배 = 전 멤버 HP 0. 승리 = 적 HP 0.
 * 힐 스킬은 HP 비율 가장 낮은 살아있는 아군에게 자동 시전.
 */
class BattleScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
    private val forcedEnemyId: String? = null,
) : Scene {

    private enum class Phase { COMMAND, ITEM_PICK, SKILL_PICK, ANIMATE, ENEMY_TURN, DEATH, RESULT }

    private val party: MutableList<Character> = gameState.loadParty().toMutableList().also {
        if (it.isEmpty()) it.add(CharacterRegistry.newCharacter("kei", "kei_berserker"))
    }
    private var actorIdx: Int = firstAliveFrom(0)
    private fun currentActor(): Character = party[actorIdx]
    private fun currentSkills(): List<Skill> =
        SkillRegistry.forClass(currentActor().classId, currentActor().level)

    private val isEn: Boolean get() = settings.isEn
    private fun lang(ko: String, en: String): String = settings.lang(ko, en)
    private fun pushEvent(ko: String, en: String) = EventBus.push(settings.lang(ko, en))
    private val partyHeight: Float get() = 18f * party.size + 6f
    private val menuTop: Float get() = 130f + partyHeight + 6f

    private val inventory: Inventory = gameState.loadInventory()

    private val enemy: EnemyInstance = run {
        val def = forcedEnemyId?.let { EnemyRegistry.get(it) } ?: EnemyRegistry.random(party.first().level)
        EnemyInstance(def, def.hpMax)
    }

    private var phase: Phase = Phase.COMMAND
    private var menuIdx = 0
    private var itemPickIdx = 0
    private var skillPickIdx = 0
    private val log = ArrayDeque<String>()
    private var animTtl = 0L
    private var deathTtl = 0L
    private val deathDuration = 700L
    private var renderClockMs = 0L
    private var hitFlashMs = 0L
    private var heroLungeMs = 0L
    private var screenFlashMs = 0L
    private var introMs = if (forcedEnemyId?.startsWith("boss_") == true) 1800L else 0L

    private data class Popup(var text: String, val onEnemy: Boolean, val targetIdx: Int, var ttl: Long, val color: Int)
    private val popups = mutableListOf<Popup>()
    private var resultGold = 0
    private var resultExp = 0
    private var resultLevels = 0
    private var resultDrops: MutableList<String> = mutableListOf()
    private var completedQuestIds: List<String> = emptyList()
    private var victory = false

    private val bg = Paint().apply { color = Color.rgb(15, 12, 25) }

    init {
        val isBoss = forcedEnemyId?.startsWith("boss_") == true
        SfxBus.playMusic(if (isBoss) SfxBus.Bgm.BOSS else SfxBus.Bgm.BATTLE)
        if (isBoss) SfxBus.play(SfxBus.Sfx.BOSS_INTRO)
    }
    private val hpBar = Paint().apply { color = Color.rgb(220, 80, 80) }
    private val spBar = Paint().apply { color = Color.rgb(80, 140, 220) }
    private val hpBarBg = Paint().apply { color = Color.argb(120, 60, 60, 80) }
    private val activeMarker = Paint().apply { color = Color.rgb(255, 220, 90) }
    private val deadOverlay = Paint().apply { color = Color.argb(160, 30, 10, 10) }
    private val enemySprite: Bitmap? = loadFirstSprite(enemy.def.spriteDir)
    private val heroSprite: Bitmap? = loadFirstSprite("hero/h00000_bm")

    private fun loadFirstSprite(relPath: String): Bitmap? = runCatching {
        val root = "${settings.spritesDir()}/$relPath"
        val first = context.assets.list(root)?.filter { it.endsWith(".png") }?.sorted()?.firstOrNull()
            ?: return@runCatching null
        context.assets.open("$root/$first").use { BitmapFactory.decodeStream(it) }
    }.getOrNull()

    private fun firstAliveFrom(start: Int): Int =
        PartyTurnOrder.firstAliveFrom(party, start)

    private fun aliveCount(): Int =
        PartyTurnOrder.aliveCount(party)

    private fun lowestHpAliveAlly(): Int =
        PartyTurnOrder.lowestHpAliveAlly(party, fallback = actorIdx)

    override fun update(deltaMs: Long) {
        renderClockMs += deltaMs
        if (hitFlashMs > 0) hitFlashMs -= deltaMs
        if (heroLungeMs > 0) heroLungeMs -= deltaMs
        if (screenFlashMs > 0) screenFlashMs -= deltaMs
        if (introMs > 0) { introMs -= deltaMs; return }
        val it = popups.iterator()
        while (it.hasNext()) {
            val p = it.next(); p.ttl -= deltaMs; if (p.ttl <= 0) it.remove()
        }
        when (phase) {
            Phase.COMMAND      -> updateCommand()
            Phase.ITEM_PICK    -> updateItemPick()
            Phase.SKILL_PICK   -> updateSkillPick()
            Phase.ANIMATE      -> updateAnimate(deltaMs)
            Phase.ENEMY_TURN   -> updateEnemyTurn(deltaMs)
            Phase.DEATH        -> updateDeath(deltaMs)
            Phase.RESULT       -> updateResult()
        }
    }

    private fun updateDeath(deltaMs: Long) {
        deathTtl -= deltaMs
        if (deathTtl <= 0) phase = Phase.RESULT
    }

    private fun updateCommand() {
        val n = 4
        if (input.pressedOnce(InputController.K_UP))   menuIdx = (menuIdx - 1 + n) % n
        if (input.pressedOnce(InputController.K_DOWN)) menuIdx = (menuIdx + 1) % n
        if (input.pressedOnce(InputController.K_OK)) {
            when (menuIdx) {
                0 -> doActorAttack()
                1 -> { phase = Phase.SKILL_PICK; skillPickIdx = 0 }
                2 -> { phase = Phase.ITEM_PICK; itemPickIdx = 0 }
                3 -> tryRun()
            }
        }
    }

    private fun updateSkillPick() {
        val skills = currentSkills()
        if (input.pressedOnce(InputController.K_SOFT2)) { phase = Phase.COMMAND; return }
        if (skills.isEmpty()) {
            pushLog(lang("스킬 없음.", "No skills."))
            phase = Phase.COMMAND; return
        }
        if (input.pressedOnce(InputController.K_UP))   skillPickIdx = (skillPickIdx - 1 + skills.size) % skills.size
        if (input.pressedOnce(InputController.K_DOWN)) skillPickIdx = (skillPickIdx + 1) % skills.size
        if (input.pressedOnce(InputController.K_OK)) {
            val s = skills[skillPickIdx]
            val actor = currentActor()
            if (actor.sp < s.spCost) {
                pushLog(lang("SP 부족.", "Not enough SP."))
                return
            }
            useSkill(s)
        }
    }

    private fun useSkill(s: Skill) {
        val actor = currentActor()
        actor.sp -= s.spCost
        val name = lang(s.nameKo, s.nameEn)
        if (s.heal) {
            val targetIdx = lowestHpAliveAlly()
            val target = party[targetIdx]
            val intl = CharacterRegistry.effectiveIntl(actor)
            val healed = ((intl * s.powerMul).toInt() + s.flatBonus).coerceAtMost(target.hpMax - target.hp)
            target.hp += healed
            popups += Popup("+$healed", onEnemy = false, targetIdx = targetIdx, ttl = 900L, color = Color.rgb(120, 240, 120))
            pushLog("$name → ${displayName(target, isEn)} +${healed} HP")
            phase = Phase.ANIMATE; animTtl = 500L
            return
        }
        val atk = (CharacterRegistry.effectiveAttack(actor) * s.powerMul).toInt() + s.flatBonus
        val dmg = damage(atk, enemy.def.def)
        enemy.hp -= dmg
        hitFlashMs = 220L
        heroLungeMs = 280L
        popups += Popup("-$dmg", onEnemy = true, targetIdx = -1, ttl = 900L, color = Color.rgb(255, 200, 100))
        pushLog("$name → $dmg")
        if (enemy.hp <= 0) { enemy.hp = 0; beginVictory() } else { phase = Phase.ANIMATE; animTtl = 500L }
    }

    private fun consumables(): List<Int> {
        return inventory.all().mapIndexedNotNull { i, slot ->
            val it = ItemRegistry.get(slot.itemId)
            if (it?.kind == ItemKind.CONSUMABLE) i else null
        }
    }

    private fun updateItemPick() {
        if (input.pressedOnce(InputController.K_SOFT2)) { phase = Phase.COMMAND; return }
        val list = consumables()
        if (list.isEmpty()) {
            pushLog(lang("아이템 없음.", "No items."))
            phase = Phase.COMMAND
            return
        }
        if (input.pressedOnce(InputController.K_UP))   itemPickIdx = (itemPickIdx - 1 + list.size) % list.size
        if (input.pressedOnce(InputController.K_DOWN)) itemPickIdx = (itemPickIdx + 1) % list.size
        if (input.pressedOnce(InputController.K_OK)) {
            val invIdx = list[itemPickIdx]
            useConsumable(invIdx)
        }
    }

    private fun useConsumable(invIdx: Int) {
        val slot = inventory.get(invIdx) ?: return
        val item = ItemRegistry.get(slot.itemId) ?: return
        val itemName = lang(item.nameKo, item.nameEn)
        when (item.id) {
            "potion_s", "potion_m" -> {
                val targetIdx = lowestHpAliveAlly()
                val target = party[targetIdx]
                val healed = (target.hpMax - target.hp).coerceAtMost(item.power)
                target.hp += healed
                popups += Popup("+$healed", onEnemy = false, targetIdx = targetIdx, ttl = 900L, color = Color.rgb(120, 240, 120))
                pushLog("$itemName → ${displayName(target, isEn)} +${healed} HP")
            }
            "ether_s" -> {
                val actor = currentActor()
                val gained = (actor.spMax - actor.sp).coerceAtMost(item.power)
                actor.sp += gained
                pushLog("$itemName +${gained} SP")
            }
            else -> {
                pushLog(lang("사용 불가.", "Cannot use."))
                phase = Phase.COMMAND
                return
            }
        }
        inventory.remove(invIdx, 1)
        gameState.saveInventory(inventory)
        phase = Phase.ANIMATE; animTtl = 500L
    }

    private fun doActorAttack() {
        val actor = currentActor()
        val base = CharacterRegistry.effectiveAttack(actor)
        val dmg = damage(base, enemy.def.def)
        enemy.hp -= dmg
        hitFlashMs = 220L
        heroLungeMs = 220L
        SfxBus.play(SfxBus.Sfx.HIT)
        popups += Popup("-$dmg", onEnemy = true, targetIdx = -1, ttl = 900L, color = Color.rgb(255, 220, 90))
        pushLog(lang("${displayName(actor, false)} 공격 $dmg.", "${displayName(actor, true)} hits for $dmg."))
        if (enemy.hp <= 0) {
            enemy.hp = 0
            beginVictory()
        } else {
            phase = Phase.ANIMATE; animTtl = 500L
        }
    }

    private fun tryRun() {
        if (Random.nextFloat() < 0.6f) {
            pushLog(lang("도망쳤다!", "Escaped!"))
            persistAndExit(victory = false, ranAway = true)
        } else {
            pushLog(lang("도망칠 수 없다!", "Cannot escape!"))
            // 도망 실패 → 모든 파티 행동 스킵하고 적 턴
            phase = Phase.ENEMY_TURN; animTtl = 600L
        }
    }

    /**
     * 한 멤버 행동 후: 다음 살아있는 멤버 차례 또는 적 턴.
     */
    private fun updateAnimate(deltaMs: Long) {
        animTtl -= deltaMs
        if (animTtl <= 0) {
            if (enemy.hp <= 0) { beginVictory(); return }
            // 다음 살아있는 멤버
            val next = nextActorAfter(actorIdx)
            if (next < 0) {
                // 라운드 끝 → 적 턴
                phase = Phase.ENEMY_TURN
                animTtl = 600L
            } else {
                actorIdx = next
                skillPickIdx = 0
                itemPickIdx = 0
                menuIdx = 0
                phase = Phase.COMMAND
            }
        }
    }

    private fun nextActorAfter(cur: Int): Int =
        PartyTurnOrder.nextAliveAfter(party, cur)

    private fun updateEnemyTurn(deltaMs: Long) {
        animTtl -= deltaMs
        if (animTtl <= 0) {
            doEnemyAttack()
            if (aliveCount() == 0) {
                beginDefeat()
            } else {
                actorIdx = firstAliveFrom(0)
                menuIdx = 0; skillPickIdx = 0; itemPickIdx = 0
                phase = Phase.COMMAND
            }
        }
    }

    private fun doEnemyAttack() {
        val alive = party.withIndex().filter { it.value.hp > 0 }
        if (alive.isEmpty()) return
        val pick = alive[Random.nextInt(alive.size)]
        val target = pick.value
        val dmg = damage(enemy.def.atk, CharacterRegistry.effectiveDefense(target))
        target.hp = (target.hp - dmg).coerceAtLeast(0)
        popups += Popup("-$dmg", onEnemy = false, targetIdx = pick.index, ttl = 900L, color = Color.rgb(255, 80, 80))
        val name = lang(enemy.def.nameKo, enemy.def.nameEn)
        pushLog("$name → ${displayName(target, isEn)} $dmg.")
    }

    private fun damage(atk: Int, def: Int): Int {
        val raw = max(1, atk - def / 2)
        val variance = (raw * (0.8f + Random.nextFloat() * 0.4f)).toInt()
        return max(1, variance)
    }

    private fun beginVictory() {
        victory = true
        resultExp = enemy.def.expReward
        resultGold = enemy.def.goldReward
        // 살아있는 멤버 모두 EXP 획득. 첫 멤버의 레벨업 회수가 결과 화면에 표시됨.
        var maxLevels = 0
        for (c in party) {
            if (c.hp <= 0) continue
            val gained = c.gainExp(resultExp)
            if (gained > maxLevels) maxLevels = gained
        }
        resultLevels = maxLevels
        gameState.gold += resultGold
        for ((itemId, prob) in enemy.def.dropTable) {
            if (Random.nextFloat() < prob) {
                if (inventory.add(itemId, 1)) {
                    resultDrops += itemId
                    val item = ItemRegistry.get(itemId)
                    val nm = item?.let { lang(it.nameKo, it.nameEn) } ?: itemId
                    pushEvent("획득: $nm", "Got: $nm")
                } else {
                    pushEvent("가방 가득, 아이템 잃음.", "Bag full, item lost.")
                }
            }
        }
        gameState.saveInventory(inventory)
        gameState.markEnemyDefeated(enemy.def.id)
        if (enemy.def.id.startsWith("boss_")) {
            gameState.markBossDefeated(enemy.def.id)
            screenFlashMs = 600L
            SfxBus.play(SfxBus.Sfx.BOSS_DEFEAT)
            pushEvent("보스 처치: ${enemy.def.nameKo}", "Boss defeated: ${enemy.def.nameEn}")
            // 자동 세이브 — 활성 슬롯 flush + 마지막 사용 수동 슬롯 미러링
            gameState.saveParty(party)
            gameState.saveInventory(inventory)
            gameState.flush()
            val mirrored = gameState.mirrorToLastSavedSlot(context)
            if (mirrored > 0) pushEvent("자동 저장 → 슬롯 $mirrored", "Auto-saved → Slot $mirrored")
            else              pushEvent("자동 저장됨",            "Auto-saved")
        }
        if (resultLevels > 0) {
            screenFlashMs = maxOf(screenFlashMs, 350L)
            SfxBus.play(SfxBus.Sfx.LEVEL_UP)
            popups += Popup("LEVEL UP!", onEnemy = false, targetIdx = 0, ttl = 1500L, color = Color.rgb(120, 240, 120))
            pushEvent("레벨업!", "LEVEL UP!")
        }
        completedQuestIds = QuestLog(gameState).tickAutoComplete(inventory)
        for (qid in completedQuestIds) {
            val q = QuestRegistry.get(qid)
            val title = q?.let { lang(it.titleKo, it.titleEn) } ?: qid
            pushEvent("퀘스트 완료: $title", "Quest done: $title")
        }
        phase = Phase.DEATH
        deathTtl = deathDuration
    }

    private fun beginDefeat() {
        victory = false
        phase = Phase.RESULT
    }

    private fun updateResult() {
        if (input.pressedOnce(InputController.K_OK) || input.pressedOnce(InputController.K_SOFT2)) {
            persistAndExit(victory = victory, ranAway = false)
        }
    }

    private fun persistAndExit(victory: Boolean, ranAway: Boolean) {
        if (victory && enemy.def.id == "boss_sealed") {
            gameState.saveParty(party)
            onRequest(MainActivity.SceneRequest.Ending)
            return
        }
        if (!victory && !ranAway) {
            for (c in party) {
                c.hp = (c.hpMax * 0.25f).toInt().coerceAtLeast(1)
                c.sp = (c.spMax * 0.25f).toInt().coerceAtLeast(0)
            }
            gameState.resetPosition(0, 17, 12)
            pushEvent("쓰러졌다... 솔티아에서 부활.", "Knocked out... revived in Soltia.")
        }
        gameState.saveParty(party)
        onRequest(MainActivity.SceneRequest.Pop)
    }

    private fun pushLog(s: String) {
        log.addLast(s)
        while (log.size > 4) log.removeFirst()
    }

    private fun displayName(c: Character, isEn: Boolean): String = when (c.id) {
        "kei"  -> if (isEn) "Kei"  else "케이"
        "ritz" -> if (isEn) "Ritz" else "리츠"
        else   -> c.id
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)

        UiKit.drawHeader(canvas, virtualWidth, lang(enemy.def.nameKo, enemy.def.nameEn))

        // 적 sprite (중앙 상단) — 부유 + 피격 흔들림 + 사망 페이드
        enemySprite?.let { bmp ->
            val scale = 4
            val dw = bmp.width * scale
            val dh = bmp.height * scale
            val cx = virtualWidth / 2 - dw / 2
            val bob = (sin(renderClockMs / 280.0) * 3.0).toInt()
            val shake = if (hitFlashMs > 0) (sin(renderClockMs / 30.0) * 4.0).toInt() else 0
            val deathAlpha = if (phase == Phase.DEATH)
                (deathTtl.toFloat() / deathDuration * 255f).toInt().coerceIn(0, 255)
            else 255
            val paint = if (deathAlpha < 255) Paint().apply { alpha = deathAlpha } else null
            canvas.drawBitmap(bmp, Rect(0, 0, bmp.width, bmp.height),
                Rect(cx + shake, 30 + bob, cx + dw + shake, 30 + dh + bob), paint)
        }

        // 적 HP 바
        val barX = 30f; val barY = 110f; val barW = virtualWidth - 60f; val barH = 6f
        canvas.drawRect(barX, barY, barX + barW, barY + barH, hpBarBg)
        val ratio = enemy.hp.toFloat() / enemy.def.hpMax.coerceAtLeast(1)
        canvas.drawRect(barX, barY, barX + barW * ratio, barY + barH, hpBar)
        canvas.drawText("HP ${enemy.hp}/${enemy.def.hpMax}", barX, barY - 2f, UiKit.muted)

        // 액터(현재 차례) sprite — 좌측, lunge
        heroSprite?.let { bmp ->
            val scale = 3
            val dw = bmp.width * scale
            val dh = bmp.height * scale
            val lunge = if (heroLungeMs > 0) {
                val frac = heroLungeMs / 280f
                ((1f - abs(frac - 0.5f) * 2f) * 16f).toInt()
            } else 0
            canvas.drawBitmap(bmp, Rect(0, 0, bmp.width, bmp.height),
                Rect(8 + lunge, 80, 8 + dw + lunge, 80 + dh), null)
        }

        // 파티 패널 — 멤버별 HP/SP 박스 (130~170 영역)
        renderPartyPanel(canvas, isEn)

        // 데미지/힐 팝업
        for (p in popups) {
            val frac = (p.ttl / 900f).coerceIn(0f, 1f)
            val rise = ((1f - frac) * 24f).toInt()
            val alpha = (frac * 255).toInt().coerceIn(0, 255)
            val pp = Paint(UiKit.body).apply { color = p.color; this.alpha = alpha; textSize = 14f; isFakeBoldText = true }
            val (px, py) = if (p.onEnemy) (virtualWidth / 2 - 8) to (90 - rise)
                           else partyMemberPopupAnchor(p.targetIdx).let { (x, y) -> x to (y - rise) }
            canvas.drawText(p.text, px.toFloat(), py.toFloat(), pp)
        }

        // 메뉴 / 로그
        when (phase) {
            Phase.COMMAND      -> renderCommand(canvas, isEn)
            Phase.ITEM_PICK    -> renderItemPick(canvas, isEn)
            Phase.SKILL_PICK   -> renderSkillPick(canvas, isEn)
            Phase.ANIMATE      -> renderLog(canvas)
            Phase.ENEMY_TURN   -> renderLog(canvas)
            Phase.DEATH        -> renderLog(canvas)
            Phase.RESULT       -> renderResult(canvas, isEn)
        }

        // 보스 인트로 오버레이
        if (introMs > 0) {
            val frac = (introMs / 1800f).coerceIn(0f, 1f)
            val a = (240f * if (frac > 0.7f) (1f - frac) / 0.3f else if (frac < 0.3f) frac / 0.3f else 1f)
                .toInt().coerceIn(0, 240)
            canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(),
                Paint().apply { color = Color.argb(a, 0, 0, 0) })
            val title = lang("보스: ", "BOSS: ") + lang(enemy.def.nameKo, enemy.def.nameEn)
            val tp = Paint(UiKit.body).apply {
                color = Color.rgb(255, 220, 90); textSize = 22f; isFakeBoldText = true
                alpha = a
            }
            val w = tp.measureText(title)
            canvas.drawText(title, (virtualWidth - w) / 2f, virtualHeight / 2f, tp)
        }

        if (screenFlashMs > 0) {
            val a = (screenFlashMs / 600f * 220f).toInt().coerceIn(0, 220)
            canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(),
                Paint().apply { color = Color.argb(a, 255, 255, 255) })
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            when (phase) {
                Phase.COMMAND     -> lang("▲▼ 선택  OK 확정",        "▲▼ select  OK confirm")
                Phase.ITEM_PICK   -> lang("▲▼ 선택  OK 사용  R 뒤로", "▲▼ pick  OK use  R back")
                Phase.SKILL_PICK  -> lang("▲▼ 선택  OK 시전  R 뒤로", "▲▼ pick  OK cast  R back")
                Phase.ANIMATE     -> "..."
                Phase.ENEMY_TURN  -> "..."
                Phase.DEATH       -> "..."
                Phase.RESULT      -> lang("OK 계속", "OK continue")
            })
    }

    /** 파티 패널: 한 줄에 한 멤버. 활성 액터엔 좌측에 ▶ 표시. 죽은 멤버는 어두운 오버레이. */
    private fun renderPartyPanel(canvas: Canvas, isEn: Boolean) {
        val top = 130f
        val rowH = 18f
        UiKit.drawBox(canvas, 8f, top, virtualWidth - 16f, rowH * party.size + 6f)
        for ((i, c) in party.withIndex()) {
            val y = top + 4f + i * rowH
            // 활성 액터 마커
            if (i == actorIdx && phase == Phase.COMMAND) {
                canvas.drawText("▶", 12f, y + 11f, Paint(UiKit.body).apply { color = Color.rgb(255, 220, 90) })
            }
            val nm = displayName(c, isEn)
            canvas.drawText("$nm Lv${c.level}", 22f, y + 11f, UiKit.body)
            // HP 바
            val hbX = 100f; val hbW = 80f; val hbH = 4f
            canvas.drawRect(hbX, y + 4f, hbX + hbW, y + 4f + hbH, hpBarBg)
            canvas.drawRect(hbX, y + 4f, hbX + hbW * (c.hp.toFloat() / c.hpMax.coerceAtLeast(1)), y + 4f + hbH, hpBar)
            canvas.drawRect(hbX, y + 11f, hbX + hbW, y + 11f + hbH, hpBarBg)
            canvas.drawRect(hbX, y + 11f, hbX + hbW * (c.sp.toFloat() / c.spMax.coerceAtLeast(1)), y + 11f + hbH, spBar)
            canvas.drawText("${c.hp}/${c.hpMax}", hbX + hbW + 4f, y + 9f, UiKit.muted)
            canvas.drawText("${c.sp}/${c.spMax}", hbX + hbW + 4f, y + 16f, UiKit.muted)

            if (c.hp <= 0) {
                canvas.drawRect(10f, y - 1f, virtualWidth - 18f, y + rowH - 3f, deadOverlay)
                canvas.drawText(lang("기절", "KO"),
                    virtualWidth - 40f, y + 11f,
                    Paint(UiKit.body).apply { color = Color.rgb(255, 120, 120) })
            }
        }
    }

    private fun partyMemberPopupAnchor(idx: Int): Pair<Int, Int> {
        val safeIdx = idx.coerceIn(0, (party.size - 1).coerceAtLeast(0))
        val top = 130
        val rowH = 18
        return (virtualWidth - 70) to (top + 4 + safeIdx * rowH + 11)
    }

    private fun drawMenuFrame(canvas: Canvas) {
        UiKit.drawBox(canvas, 8f, menuTop, virtualWidth - 16f, 70f)
    }

    private fun renderCommand(canvas: Canvas, isEn: Boolean) {
        val labels = if (isEn) listOf("ATTACK", "SKILL", "ITEM", "RUN")
                     else      listOf("공격",   "스킬",  "아이템","도망")
        val nm = displayName(currentActor(), isEn)
        drawMenuFrame(canvas)
        canvas.drawText(lang("$nm 차례", "$nm's turn"), 14f, menuTop + 12f, UiKit.muted)
        for ((i, label) in labels.withIndex()) {
            UiKit.drawMenuItem(canvas, 16f, menuTop + 16f + i * 14f, virtualWidth - 32f, 12f, label, i == menuIdx)
        }
    }

    /** 페이지네이션된 픽 메뉴 공통 렌더. [empty]가 비어있으면 placeholder 출력. */
    private fun <T> renderPickList(
        canvas: Canvas,
        items: List<T>,
        selectedIdx: Int,
        emptyText: String,
        rowOffset: Float,
        label: (T) -> String,
    ) {
        drawMenuFrame(canvas)
        if (items.isEmpty()) {
            canvas.drawText(emptyText, 16f, menuTop + 20f, UiKit.muted)
            return
        }
        val visible = 4
        val scrollStart = (selectedIdx - visible + 1).coerceAtLeast(0)
        val end = minOf(items.size, scrollStart + visible)
        for (i in scrollStart until end) {
            UiKit.drawMenuItem(canvas, 16f, menuTop + rowOffset + (i - scrollStart) * 16f, virtualWidth - 32f, 14f,
                label(items[i]), i == selectedIdx)
        }
        if (items.size > visible) {
            canvas.drawText("${selectedIdx + 1}/${items.size}", virtualWidth - 36f, menuTop + 70f, UiKit.muted)
        }
    }

    private fun renderSkillPick(canvas: Canvas, isEn: Boolean) {
        renderPickList(canvas, currentSkills(), skillPickIdx,
            emptyText = lang("(스킬 없음)", "(no skills)"), rowOffset = 6f) { s ->
            "${lang(s.nameKo, s.nameEn)}  SP ${s.spCost}"
        }
    }

    private fun renderItemPick(canvas: Canvas, isEn: Boolean) {
        renderPickList(canvas, consumables(), itemPickIdx,
            emptyText = lang("(소비 아이템 없음)", "(no consumables)"), rowOffset = 8f) { invIdx ->
            val slot = inventory.get(invIdx)!!
            val item = ItemRegistry.get(slot.itemId)
            val name = item?.let { lang(it.nameKo, it.nameEn) } ?: slot.itemId
            "$name ×${slot.count}"
        }
    }

    private fun renderLog(canvas: Canvas) {
        drawMenuFrame(canvas)
        for ((i, line) in log.withIndex()) {
            canvas.drawText(line, 16f, menuTop + 14f + i * 14f, UiKit.body)
        }
    }

    private fun renderResult(canvas: Canvas, isEn: Boolean) {
        drawMenuFrame(canvas)
        if (victory) {
            canvas.drawText(lang("승리!", "VICTORY!"), 16f, menuTop + 16f, UiKit.body)
            canvas.drawText(lang("경험치 +$resultExp", "EXP +$resultExp"), 16f, menuTop + 32f, UiKit.body)
            canvas.drawText("GOLD +$resultGold", 16f, menuTop + 48f, UiKit.body)
            if (resultLevels > 0) {
                canvas.drawText(lang("레벨업!", "LEVEL UP!"), 140f, menuTop + 32f, UiKit.body)
            }
            if (completedQuestIds.isNotEmpty()) {
                val first = completedQuestIds.first()
                val q = QuestRegistry.get(first)
                val title = q?.let { lang(it.titleKo, it.titleEn) } ?: first
                canvas.drawText(lang("퀘스트 완료: ", "QUEST DONE: ") + title,
                    16f, menuTop + 64f, UiKit.body)
            }
            if (resultDrops.isNotEmpty()) {
                val dropNames = resultDrops.mapNotNull { id ->
                    ItemRegistry.get(id)?.let { lang(it.nameKo, it.nameEn) }
                }
                canvas.drawText(lang("드롭: ", "DROP: ") + dropNames.joinToString(", "),
                    16f, menuTop + 48f, UiKit.muted)
            }
        } else {
            canvas.drawText(lang("패배...", "DEFEATED..."), 16f, menuTop + 16f, UiKit.body)
            canvas.drawText(lang("타이틀로 돌아갑니다.", "Returning to title."), 16f, menuTop + 32f, UiKit.muted)
        }
    }
}
