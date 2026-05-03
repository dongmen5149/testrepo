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
import com.hero3.remake.engine.EnemyDef
import com.hero3.remake.engine.EnemyInstance
import com.hero3.remake.engine.EnemyRegistry
import com.hero3.remake.engine.GameState
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Inventory
import com.hero3.remake.engine.ItemKind
import com.hero3.remake.engine.ItemRegistry
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit
import kotlin.math.max
import kotlin.random.Random

/**
 * 단순 턴제 전투 — 영웅(파티 리더) vs 적 1마리.
 *
 * 메뉴: ATTACK / ITEM(소비 아이템) / RUN.
 * 명중률은 단순 rng. 데미지 = max(1, atk + str/2 - def/2 ± 20%).
 */
class BattleScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val gameState: GameState,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
    private val forcedEnemyId: String? = null,
) : Scene {

    private enum class Phase { COMMAND, ITEM_PICK, SKILL_PICK, ANIMATE, DEATH, RESULT }

    private val party: MutableList<Character> = gameState.loadParty().toMutableList()
    private val hero: Character = party.firstOrNull() ?: CharacterRegistry.newCharacter("kei", "kei_berserker")
    private val heroClass = CharacterRegistry.classOf(hero.classId)!!
    private val inventory: Inventory = gameState.loadInventory()

    private val enemy: EnemyInstance = run {
        val def = forcedEnemyId?.let { EnemyRegistry.get(it) } ?: EnemyRegistry.random(hero.level)
        EnemyInstance(def, def.hpMax)
    }

    private var phase: Phase = Phase.COMMAND
    private var menuIdx = 0
    private var itemPickIdx = 0
    private var skillPickIdx = 0
    private val skills = com.hero3.remake.engine.SkillRegistry.forClass(hero.classId, hero.level)
    private val log = ArrayDeque<String>()
    private var animTtl = 0L
    private var deathTtl = 0L
    private val deathDuration = 700L
    private var renderClockMs = 0L
    private var hitFlashMs = 0L
    private var heroLungeMs = 0L
    private var screenFlashMs = 0L
    private var introMs = if (forcedEnemyId?.startsWith("boss_") == true) 1800L else 0L

    private data class Popup(var text: String, val onEnemy: Boolean, var ttl: Long, val color: Int)
    private val popups = mutableListOf<Popup>()
    private var resultGold = 0
    private var resultExp = 0
    private var resultLevels = 0
    private var resultDrops: MutableList<String> = mutableListOf()
    private var completedQuestIds: List<String> = emptyList()
    private var victory = false

    private val bg = Paint().apply { color = Color.rgb(15, 12, 25) }

    init {
        val bgm = if (forcedEnemyId?.startsWith("boss_") == true)
            com.hero3.remake.engine.SfxBus.Bgm.BOSS
        else com.hero3.remake.engine.SfxBus.Bgm.BATTLE
        com.hero3.remake.engine.SfxBus.playMusic(bgm)
        if (forcedEnemyId?.startsWith("boss_") == true)
            com.hero3.remake.engine.SfxBus.play(com.hero3.remake.engine.SfxBus.Sfx.BOSS_INTRO)
    }
    private val hpBar = Paint().apply { color = Color.rgb(220, 80, 80) }
    private val spBar = Paint().apply { color = Color.rgb(80, 140, 220) }
    private val hpBarBg = Paint().apply { color = Color.argb(120, 60, 60, 80) }
    private val enemySprite: Bitmap? = loadEnemySprite()
    private val heroSprite: Bitmap? = loadHeroSprite()

    private fun loadHeroSprite(): Bitmap? = runCatching {
        val root = "${settings.spritesDir()}/hero/h00000_bm"
        val files = context.assets.list(root)?.filter { it.endsWith(".png") }?.sorted() ?: return@runCatching null
        if (files.isEmpty()) return@runCatching null
        context.assets.open("$root/${files.first()}").use { BitmapFactory.decodeStream(it) }
    }.getOrNull()

    private fun loadEnemySprite(): Bitmap? = runCatching {
        val root = "${settings.spritesDir()}/${enemy.def.spriteDir}"
        val files = context.assets.list(root)?.filter { it.endsWith(".png") }?.sorted() ?: return@runCatching null
        if (files.isEmpty()) return@runCatching null
        context.assets.open("$root/${files.first()}").use { BitmapFactory.decodeStream(it) }
    }.getOrNull()

    override fun update(deltaMs: Long) {
        renderClockMs += deltaMs
        if (hitFlashMs > 0) hitFlashMs -= deltaMs
        if (heroLungeMs > 0) heroLungeMs -= deltaMs
        if (screenFlashMs > 0) screenFlashMs -= deltaMs
        if (introMs > 0) { introMs -= deltaMs; return }
        // popup ttl
        val it = popups.iterator()
        while (it.hasNext()) {
            val p = it.next(); p.ttl -= deltaMs; if (p.ttl <= 0) it.remove()
        }
        when (phase) {
            Phase.COMMAND      -> updateCommand()
            Phase.ITEM_PICK    -> updateItemPick()
            Phase.SKILL_PICK   -> updateSkillPick()
            Phase.ANIMATE      -> updateAnimate(deltaMs)
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
                0 -> doHeroAttack()
                1 -> { phase = Phase.SKILL_PICK; skillPickIdx = 0 }
                2 -> { phase = Phase.ITEM_PICK; itemPickIdx = 0 }
                3 -> tryRun()
            }
        }
    }

    private fun updateSkillPick() {
        if (input.pressedOnce(InputController.K_SOFT2)) { phase = Phase.COMMAND; return }
        if (skills.isEmpty()) {
            pushLog(if (settings.language == "en") "No skills." else "스킬 없음.")
            phase = Phase.COMMAND; return
        }
        if (input.pressedOnce(InputController.K_UP))   skillPickIdx = (skillPickIdx - 1 + skills.size) % skills.size
        if (input.pressedOnce(InputController.K_DOWN)) skillPickIdx = (skillPickIdx + 1) % skills.size
        if (input.pressedOnce(InputController.K_OK)) {
            val s = skills[skillPickIdx]
            if (hero.sp < s.spCost) {
                pushLog(if (settings.language == "en") "Not enough SP." else "SP 부족.")
                return
            }
            useSkill(s)
        }
    }

    private fun useSkill(s: com.hero3.remake.engine.Skill) {
        hero.sp -= s.spCost
        val isEn = settings.language == "en"
        val name = if (isEn) s.nameEn else s.nameKo
        if (s.heal) {
            val intl = CharacterRegistry.effectiveIntl(hero)
            val healed = ((intl * s.powerMul).toInt() + s.flatBonus).coerceAtMost(hero.hpMax - hero.hp)
            hero.hp += healed
            popups += Popup("+$healed", onEnemy = false, ttl = 900L, color = Color.rgb(120, 240, 120))
            pushLog(if (isEn) "$name +${healed} HP" else "$name +${healed} HP")
            beginEnemyTurn()
            return
        }
        val atk = (CharacterRegistry.effectiveAttack(hero) * s.powerMul).toInt() + s.flatBonus
        val dmg = damage(atk, enemy.def.def)
        enemy.hp -= dmg
        hitFlashMs = 220L
        heroLungeMs = 280L
        popups += Popup("-$dmg", onEnemy = true, ttl = 900L, color = Color.rgb(255, 200, 100))
        pushLog(if (isEn) "$name → ${dmg}" else "$name → ${dmg}")
        if (enemy.hp <= 0) { enemy.hp = 0; beginVictory() } else beginEnemyTurn()
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
            pushLog(if (settings.language == "en") "No items." else "아이템 없음.")
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
        when (item.id) {
            "potion_s", "potion_m" -> {
                val healed = (hero.hpMax - hero.hp).coerceAtMost(item.power)
                hero.hp += healed
                pushLog(if (settings.language == "en") "${(if(settings.language=="en")item.nameEn else item.nameKo)} +${healed} HP"
                        else "${item.nameKo} +${healed} HP")
            }
            "ether_s" -> {
                val gained = (hero.spMax - hero.sp).coerceAtMost(item.power)
                hero.sp += gained
                pushLog("${if(settings.language=="en") item.nameEn else item.nameKo} +${gained} SP")
            }
            else -> {
                pushLog(if (settings.language == "en") "Cannot use." else "사용 불가.")
                phase = Phase.COMMAND
                return
            }
        }
        inventory.remove(invIdx, 1)
        gameState.saveInventory(inventory)
        beginEnemyTurn()
    }

    private fun doHeroAttack() {
        val base = CharacterRegistry.effectiveAttack(hero)
        val dmg = damage(base, enemy.def.def)
        enemy.hp -= dmg
        hitFlashMs = 220L
        heroLungeMs = 220L
        com.hero3.remake.engine.SfxBus.play(com.hero3.remake.engine.SfxBus.Sfx.HIT)
        popups += Popup("-$dmg", onEnemy = true, ttl = 900L, color = Color.rgb(255, 220, 90))
        pushLog(if (settings.language == "en") "Hero hits for ${dmg}." else "영웅 공격 ${dmg}.")
        if (enemy.hp <= 0) {
            enemy.hp = 0
            beginVictory()
        } else {
            beginEnemyTurn()
        }
    }

    private fun tryRun() {
        if (Random.nextFloat() < 0.6f) {
            pushLog(if (settings.language == "en") "Escaped!" else "도망쳤다!")
            persistAndExit(victory = false, ranAway = true)
        } else {
            pushLog(if (settings.language == "en") "Cannot escape!" else "도망칠 수 없다!")
            beginEnemyTurn()
        }
    }

    private fun beginEnemyTurn() {
        phase = Phase.ANIMATE
        animTtl = 600L
    }

    private fun updateAnimate(deltaMs: Long) {
        animTtl -= deltaMs
        if (animTtl <= 0) {
            if (enemy.hp > 0) doEnemyAttack()
            phase = if (hero.hp <= 0 || enemy.hp <= 0) Phase.RESULT else Phase.COMMAND
            if (hero.hp <= 0) beginDefeat()
            else if (enemy.hp <= 0) beginVictory()
        }
    }

    private fun doEnemyAttack() {
        val dmg = damage(enemy.def.atk, CharacterRegistry.effectiveDefense(hero))
        hero.hp = (hero.hp - dmg).coerceAtLeast(0)
        popups += Popup("-$dmg", onEnemy = false, ttl = 900L, color = Color.rgb(255, 80, 80))
        val name = if (settings.language == "en") enemy.def.nameEn else enemy.def.nameKo
        pushLog(if (settings.language == "en") "${name} hits for ${dmg}." else "${name} 공격 ${dmg}.")
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
        resultLevels = hero.gainExp(resultExp)
        gameState.gold += resultGold
        // 드롭 굴림
        for ((itemId, prob) in enemy.def.dropTable) {
            if (Random.nextFloat() < prob) {
                if (inventory.add(itemId, 1)) {
                    resultDrops += itemId
                    val item = com.hero3.remake.engine.ItemRegistry.get(itemId)
                    val nm = (if (settings.language == "en") item?.nameEn else item?.nameKo) ?: itemId
                    com.hero3.remake.engine.EventBus.push(
                        if (settings.language == "en") "Got: $nm" else "획득: $nm")
                } else {
                    com.hero3.remake.engine.EventBus.push(
                        if (settings.language == "en") "Bag full, item lost." else "가방 가득, 아이템 잃음.")
                }
            }
        }
        gameState.saveInventory(inventory)
        gameState.markEnemyDefeated(enemy.def.id)
        if (enemy.def.id.startsWith("boss_")) {
            gameState.markBossDefeated(enemy.def.id)
            screenFlashMs = 600L
            com.hero3.remake.engine.SfxBus.play(com.hero3.remake.engine.SfxBus.Sfx.BOSS_DEFEAT)
            com.hero3.remake.engine.EventBus.push(
                if (settings.language == "en") "Boss defeated: ${enemy.def.nameEn}"
                else "보스 처치: ${enemy.def.nameKo}")
        }
        if (resultLevels > 0) {
            screenFlashMs = maxOf(screenFlashMs, 350L)
            com.hero3.remake.engine.SfxBus.play(com.hero3.remake.engine.SfxBus.Sfx.LEVEL_UP)
            popups += Popup("LEVEL UP!", onEnemy = false, ttl = 1500L, color = Color.rgb(120, 240, 120))
            com.hero3.remake.engine.EventBus.push(
                if (settings.language == "en") "LEVEL UP! Lv${hero.level}"
                else "레벨업! Lv${hero.level}")
        }
        // 자동 퀘스트 완료 (보스 처치 후)
        completedQuestIds = com.hero3.remake.engine.QuestLog(gameState).tickAutoComplete(inventory)
        for (qid in completedQuestIds) {
            val q = com.hero3.remake.engine.QuestRegistry.get(qid)
            val title = q?.let { if (settings.language == "en") it.titleEn else it.titleKo } ?: qid
            com.hero3.remake.engine.EventBus.push(
                if (settings.language == "en") "Quest done: $title"
                else "퀘스트 완료: $title")
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
        if (party.isNotEmpty()) party[0] = hero
        // 최종 보스 처치 시 엔딩
        if (victory && enemy.def.id == "boss_sealed") {
            gameState.saveParty(party)
            onRequest(MainActivity.SceneRequest.Ending)
            return
        }
        if (!victory && !ranAway) {
            // 패배 → 솔티아로 부활 (HP/SP 25%)
            for (c in party) {
                c.hp = (c.hpMax * 0.25f).toInt().coerceAtLeast(1)
                c.sp = (c.spMax * 0.25f).toInt().coerceAtLeast(0)
            }
            gameState.resetPosition(0, 17, 12)
            com.hero3.remake.engine.EventBus.push(
                if (settings.language == "en") "Knocked out... revived in Soltia."
                else "쓰러졌다... 솔티아에서 부활.")
        }
        gameState.saveParty(party)
        onRequest(MainActivity.SceneRequest.Pop)
    }

    private fun pushLog(s: String) {
        log.addLast(s)
        while (log.size > 4) log.removeFirst()
    }

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val isEn = settings.language == "en"

        val eName = if (isEn) enemy.def.nameEn else enemy.def.nameKo
        UiKit.drawHeader(canvas, virtualWidth, eName)

        // 적 sprite (중앙 상단) — 부유 + 피격 흔들림 + 사망 페이드
        enemySprite?.let { bmp ->
            val scale = 4
            val dw = bmp.width * scale
            val dh = bmp.height * scale
            val cx = virtualWidth / 2 - dw / 2
            val bob = (kotlin.math.sin(renderClockMs / 280.0) * 3.0).toInt()
            val shake = if (hitFlashMs > 0) ((kotlin.math.sin(renderClockMs / 30.0) * 4.0).toInt()) else 0
            val deathAlpha = if (phase == Phase.DEATH)
                (deathTtl.toFloat() / deathDuration * 255f).toInt().coerceIn(0, 255)
            else 255
            val paint = if (deathAlpha < 255) Paint().apply { alpha = deathAlpha } else null
            canvas.drawBitmap(bmp, Rect(0, 0, bmp.width, bmp.height),
                Rect(cx + shake, 30 + bob, cx + dw + shake, 30 + dh + bob), paint)
        }

        // 데미지/힐 팝업
        for (p in popups) {
            val frac = (p.ttl / 900f).coerceIn(0f, 1f)
            val rise = ((1f - frac) * 24f).toInt()
            val alpha = (frac * 255).toInt().coerceIn(0, 255)
            val pp = Paint(UiKit.body).apply { color = p.color; this.alpha = alpha; textSize = 14f; isFakeBoldText = true }
            val (px, py) = if (p.onEnemy) (virtualWidth / 2 - 8) to (90 - rise)
                           else (virtualWidth - 50) to (148 - rise)
            canvas.drawText(p.text, px.toFloat(), py.toFloat(), pp)
        }

        // 적 HP 바
        val barX = 30f; val barY = 110f; val barW = virtualWidth - 60f; val barH = 6f
        canvas.drawRect(barX, barY, barX + barW, barY + barH, hpBarBg)
        val ratio = enemy.hp.toFloat() / enemy.def.hpMax.coerceAtLeast(1)
        canvas.drawRect(barX, barY, barX + barW * ratio, barY + barH, hpBar)
        canvas.drawText("HP ${enemy.hp}/${enemy.def.hpMax}", barX, barY - 2f, UiKit.muted)

        // 영웅 sprite (좌측, 3× scale, 공격 시 lunge)
        heroSprite?.let { bmp ->
            val scale = 3
            val dw = bmp.width * scale
            val dh = bmp.height * scale
            val lunge = if (heroLungeMs > 0) {
                val frac = heroLungeMs / 280f
                ((1f - kotlin.math.abs(frac - 0.5f) * 2f) * 16f).toInt()
            } else 0
            canvas.drawBitmap(bmp, Rect(0, 0, bmp.width, bmp.height),
                Rect(8 + lunge, 80, 8 + dw + lunge, 80 + dh), null)
        }

        // 영웅 정보
        UiKit.drawBox(canvas, 8f, 130f, virtualWidth - 16f, 36f)
        val heroName = when (hero.id) {
            "kei"  -> if (isEn) "Kei"  else "케이"
            "ritz" -> if (isEn) "Ritz" else "리츠"
            else   -> hero.id
        }
        canvas.drawText("$heroName  Lv${hero.level}", 14f, 144f, UiKit.body)
        canvas.drawText("HP ${hero.hp}/${hero.hpMax}  SP ${hero.sp}/${hero.spMax}", 14f, 158f, UiKit.body)
        val hbW = 90f; val hbH = 4f
        canvas.drawRect(120f, 140f, 120f + hbW, 140f + hbH, hpBarBg)
        canvas.drawRect(120f, 140f, 120f + hbW * (hero.hp.toFloat() / hero.hpMax.coerceAtLeast(1)), 140f + hbH, hpBar)
        canvas.drawRect(120f, 154f, 120f + hbW, 154f + hbH, hpBarBg)
        canvas.drawRect(120f, 154f, 120f + hbW * (hero.sp.toFloat() / hero.spMax.coerceAtLeast(1)), 154f + hbH, spBar)

        // 메뉴 / 로그
        when (phase) {
            Phase.COMMAND -> renderCommand(canvas, isEn)
            Phase.ITEM_PICK -> renderItemPick(canvas, isEn)
            Phase.SKILL_PICK -> renderSkillPick(canvas, isEn)
            Phase.ANIMATE -> renderLog(canvas)
            Phase.DEATH   -> renderLog(canvas)
            Phase.RESULT -> renderResult(canvas, isEn)
        }

        // 보스 인트로 오버레이
        if (introMs > 0) {
            val frac = (introMs / 1800f).coerceIn(0f, 1f)
            // 페이드 인/아웃 — 0~0.3 페이드인, 0.7~1.0 페이드아웃 형태
            val a = (240f * if (frac > 0.7f) (1f - frac) / 0.3f else if (frac < 0.3f) frac / 0.3f else 1f)
                .toInt().coerceIn(0, 240)
            canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(),
                Paint().apply { color = Color.argb(a, 0, 0, 0) })
            val title = (if (isEn) "BOSS: " else "보스: ") + (if (isEn) enemy.def.nameEn else enemy.def.nameKo)
            val tp = Paint(UiKit.body).apply {
                color = Color.rgb(255, 220, 90); textSize = 22f; isFakeBoldText = true
                alpha = a
            }
            val w = tp.measureText(title)
            canvas.drawText(title, (virtualWidth - w) / 2f, virtualHeight / 2f, tp)
        }

        // 보스 처치 시 화면 플래시 (가장 위 레이어)
        if (screenFlashMs > 0) {
            val a = (screenFlashMs / 600f * 220f).toInt().coerceIn(0, 220)
            canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(),
                Paint().apply { color = Color.argb(a, 255, 255, 255) })
        }

        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            when (phase) {
                Phase.COMMAND   -> if (isEn) "▲▼ select  OK confirm" else "▲▼ 선택  OK 확정"
                Phase.ITEM_PICK -> if (isEn) "▲▼ pick  OK use  R back" else "▲▼ 선택  OK 사용  R 뒤로"
                Phase.SKILL_PICK -> if (isEn) "▲▼ pick  OK cast  R back" else "▲▼ 선택  OK 시전  R 뒤로"
                Phase.ANIMATE   -> "..."
                Phase.DEATH     -> "..."
                Phase.RESULT    -> if (isEn) "OK continue" else "OK 계속"
            })
    }

    private fun renderCommand(canvas: Canvas, isEn: Boolean) {
        val labels = if (isEn) listOf("ATTACK", "SKILL", "ITEM", "RUN")
                     else      listOf("공격",   "스킬",  "아이템","도망")
        UiKit.drawBox(canvas, 8f, 175f, virtualWidth - 16f, 70f)
        for ((i, label) in labels.withIndex()) {
            UiKit.drawMenuItem(canvas, 16f, 180f + i * 16f, virtualWidth - 32f, 14f, label, i == menuIdx)
        }
    }

    private fun renderSkillPick(canvas: Canvas, isEn: Boolean) {
        UiKit.drawBox(canvas, 8f, 175f, virtualWidth - 16f, 70f)
        if (skills.isEmpty()) {
            canvas.drawText(if (isEn) "(no skills)" else "(스킬 없음)", 16f, 195f, UiKit.muted)
            return
        }
        val visible = 4
        val scrollStart = (skillPickIdx - visible + 1).coerceAtLeast(0)
        val end = minOf(skills.size, scrollStart + visible)
        for (i in scrollStart until end) {
            val s = skills[i]
            val name = if (isEn) s.nameEn else s.nameKo
            UiKit.drawMenuItem(canvas, 16f, 180f + (i - scrollStart) * 16f, virtualWidth - 32f, 14f,
                "$name  SP ${s.spCost}", i == skillPickIdx)
        }
        if (skills.size > visible) {
            canvas.drawText("${skillPickIdx + 1}/${skills.size}",
                virtualWidth - 36f, 244f, UiKit.muted)
        }
    }

    private fun renderItemPick(canvas: Canvas, isEn: Boolean) {
        UiKit.drawBox(canvas, 8f, 175f, virtualWidth - 16f, 70f)
        val list = consumables()
        if (list.isEmpty()) {
            canvas.drawText(if (isEn) "(no consumables)" else "(소비 아이템 없음)", 16f, 195f, UiKit.muted)
            return
        }
        val visible = 4
        val scrollStart = (itemPickIdx - visible + 1).coerceAtLeast(0)
        val end = minOf(list.size, scrollStart + visible)
        for (i in scrollStart until end) {
            val invIdx = list[i]
            val slot = inventory.get(invIdx)!!
            val item = ItemRegistry.get(slot.itemId)
            val name = (if (isEn) item?.nameEn else item?.nameKo) ?: slot.itemId
            UiKit.drawMenuItem(canvas, 16f, 183f + (i - scrollStart) * 16f, virtualWidth - 32f, 14f,
                "$name ×${slot.count}", i == itemPickIdx)
        }
        if (list.size > visible) {
            canvas.drawText("${itemPickIdx + 1}/${list.size}",
                virtualWidth - 36f, 244f, UiKit.muted)
        }
    }

    private fun renderLog(canvas: Canvas) {
        UiKit.drawBox(canvas, 8f, 175f, virtualWidth - 16f, 70f)
        for ((i, line) in log.withIndex()) {
            canvas.drawText(line, 16f, 188f + i * 14f, UiKit.body)
        }
    }

    private fun renderResult(canvas: Canvas, isEn: Boolean) {
        UiKit.drawBox(canvas, 8f, 175f, virtualWidth - 16f, 70f)
        if (victory) {
            canvas.drawText(if (isEn) "VICTORY!" else "승리!", 16f, 192f, UiKit.body)
            canvas.drawText(if (isEn) "EXP +${resultExp}" else "경험치 +${resultExp}", 16f, 210f, UiKit.body)
            canvas.drawText("GOLD +${resultGold}", 16f, 226f, UiKit.body)
            if (resultLevels > 0) {
                canvas.drawText(if (isEn) "LEVEL UP! Lv${hero.level}" else "레벨업! Lv${hero.level}",
                    140f, 210f, UiKit.body)
            }
            if (completedQuestIds.isNotEmpty()) {
                val q = com.hero3.remake.engine.QuestRegistry.get(completedQuestIds.first())
                val title = if (q == null) completedQuestIds.first()
                            else if (isEn) q.titleEn else q.titleKo
                canvas.drawText((if (isEn) "QUEST DONE: " else "퀘스트 완료: ") + title,
                    16f, 240f, UiKit.body)
            }
            if (resultDrops.isNotEmpty()) {
                val dropNames = resultDrops.mapNotNull {
                    val it_ = com.hero3.remake.engine.ItemRegistry.get(it)
                    if (isEn) it_?.nameEn else it_?.nameKo
                }
                canvas.drawText((if (isEn) "DROP: " else "드롭: ") + dropNames.joinToString(", "),
                    16f, 226f, UiKit.muted)
            }
        } else {
            canvas.drawText(if (isEn) "DEFEATED..." else "패배...", 16f, 192f, UiKit.body)
            canvas.drawText(if (isEn) "Returning to title." else "타이틀로 돌아갑니다.", 16f, 210f, UiKit.muted)
        }
    }
}
