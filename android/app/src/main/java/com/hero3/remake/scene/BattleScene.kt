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
import com.hero3.remake.engine.Status
import com.hero3.remake.engine.StatusEffect
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

    /** R91: catalog SkillIndex 1회 빌드 (catalog 미설치 시 null — 보정 0). */
    private val catalogSkillIndex: com.hero3.remake.catalog.Hero3CatalogSkillIndex? =
        com.hero3.remake.catalog.Hero3CatalogProvider.get()
            ?.let { com.hero3.remake.catalog.Hero3CatalogSkillIndex.build(it) }

    /** R91: imbalance 방지 clamp 폭 (catalog primarySigned 값이 크게 튈 수 있어서). */
    private val catalogBonusClamp = 25

    private fun catalogBonusFor(nameKo: String, heal: Boolean): Int {
        val idx = catalogSkillIndex ?: return 0
        val kind = if (heal) com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.HEAL
                   else      com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.OFFENSE
        val raw = idx.primaryModifierForEngineName(nameKo, kind)
        return raw.coerceIn(-catalogBonusClamp, catalogBonusClamp)
    }

    /**
     * R96 — 파티 멤버별 buff/debuff status. battle-scoped (저장 안 됨).
     * key = party index, value = active StatusEffect 리스트.
     */
    private val partyStatuses: MutableMap<Int, MutableList<StatusEffect>> = mutableMapOf()

    private fun statusesOf(memberIdx: Int): MutableList<StatusEffect> =
        partyStatuses.getOrPut(memberIdx) { mutableListOf() }

    /** R96 — 특정 status 의 perTick 합 (해당 member 의 모든 매칭 buff). */
    private fun buffPercent(memberIdx: Int, st: Status): Int =
        partyStatuses[memberIdx]?.filter { it.status == st }?.sumOf { it.perTick } ?: 0

    /**
     * R102 — actor 의 SP_COST_REDUCE_BUFF 합 (0..clamp) 을 적용한 실 SP 비용.
     * 결과는 항상 ≥ 1 (skill 이 spCost > 0 일 때).
     */
    private fun effectiveSpCost(memberIdx: Int, baseCost: Int): Int {
        if (baseCost <= 0) return baseCost
        val reducePct = buffPercent(memberIdx, Status.SP_COST_REDUCE_BUFF).coerceIn(0, 90)
        if (reducePct <= 0) return baseCost
        return (baseCost * (100 - reducePct) / 100).coerceAtLeast(1)
    }

    /** R94: engine skill 의 catalog effectV2.nDebuffs (0 이면 부여 없음). */
    private fun catalogDebuffCountFor(nameKo: String): Int {
        val idx = catalogSkillIndex ?: return 0
        return idx.debuffCountForEngineName(nameKo)
    }

    /** R93: engine skill 의 CRI_RATE slot 보정값 (단위 = percent). clamp ±25. */
    private fun catalogCritBonusFor(nameKo: String): Int {
        val idx = catalogSkillIndex ?: return 0
        val raw = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.CRIT_RATE)
        return raw.coerceIn(-catalogBonusClamp, catalogBonusClamp)
    }

    /**
     * R96 — engine skill 의 CRIT_DEF / DEFENSE slot 값을 actor 자기 buff status 로 N턴 등록.
     * 두 종 모두 ±25 clamp, 3턴 유지. 같은 status 가 있으면 turnsLeft refresh + percent 갱신.
     */
    private fun registerSelfBuffsFromSkill(actorMemberIdx: Int, nameKo: String) {
        val idx = catalogSkillIndex ?: return
        val critDef = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.CRIT_DEF)
            .coerceIn(0, catalogBonusClamp)
        val defense = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.DEFENSE)
            .coerceIn(0, catalogBonusClamp)
        val list = statusesOf(actorMemberIdx)
        val accuracy = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.ACCURACY)
            .coerceIn(0, catalogBonusClamp)
        val dodge = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.DODGE)
            .coerceIn(0, catalogBonusClamp)
        val hpRegen = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.HP_REGEN)
            .coerceIn(0, catalogBonusClamp)
        val spRegen = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.SP_REGEN)
            .coerceIn(0, catalogBonusClamp)
        val taunt = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.TAUNT)
        val block = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.BLOCK)
            .coerceIn(0, catalogBonusClamp)
        val spCostReduce = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.SP_COST_REDUCE)
            .coerceIn(0, catalogBonusClamp)
        if (critDef > 0) {
            val ex = list.firstOrNull { it.status == Status.CRIT_DEF_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.CRIT_DEF_BUFF, turnsLeft = 3, perTick = critDef)
        }
        if (defense > 0) {
            val ex = list.firstOrNull { it.status == Status.DEFENSE_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.DEFENSE_BUFF, turnsLeft = 3, perTick = defense)
        }
        if (accuracy > 0) {
            val ex = list.firstOrNull { it.status == Status.ACCURACY_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.ACCURACY_BUFF, turnsLeft = 3, perTick = accuracy)
        }
        if (dodge > 0) {
            val ex = list.firstOrNull { it.status == Status.DODGE_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.DODGE_BUFF, turnsLeft = 3, perTick = dodge)
        }
        if (hpRegen > 0) {
            val ex = list.firstOrNull { it.status == Status.HP_REGEN_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.HP_REGEN_BUFF, turnsLeft = 3, perTick = hpRegen)
        }
        if (spRegen > 0) {
            val ex = list.firstOrNull { it.status == Status.SP_REGEN_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.SP_REGEN_BUFF, turnsLeft = 3, perTick = spRegen)
        }
        if (taunt > 0) {
            val ex = list.firstOrNull { it.status == Status.TAUNT_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.TAUNT_BUFF, turnsLeft = 3, perTick = taunt)
        }
        if (block > 0) {
            val ex = list.firstOrNull { it.status == Status.BLOCK_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.BLOCK_BUFF, turnsLeft = 3, perTick = block)
        }
        if (spCostReduce > 0) {
            val ex = list.firstOrNull { it.status == Status.SP_COST_REDUCE_BUFF }
            if (ex != null) { ex.turnsLeft = 3 }
            else list += StatusEffect(Status.SP_COST_REDUCE_BUFF, turnsLeft = 3, perTick = spCostReduce)
        }
        if (critDef > 0 || defense > 0 || accuracy > 0 || dodge > 0 || hpRegen > 0 || spRegen > 0 || taunt > 0 || block > 0 || spCostReduce > 0) {
            val parts = listOfNotNull(
                if (critDef > 0) "${if (isEn) "CDF" else "크감"}+$critDef%" else null,
                if (defense > 0) "${if (isEn) "DEF" else "방어"}+$defense%" else null,
                if (accuracy > 0) "${if (isEn) "ACC" else "명중"}+$accuracy%" else null,
                if (dodge > 0) "${if (isEn) "DOD" else "회피"}+$dodge%" else null,
                if (hpRegen > 0) "${if (isEn) "HPR" else "HP재생"}+$hpRegen/턴" else null,
                if (spRegen > 0) "${if (isEn) "SPR" else "SP재생"}+$spRegen/턴" else null,
                if (taunt > 0) "${if (isEn) "TNT" else "도발"}" else null,
                if (block > 0) "${if (isEn) "BLK" else "블록"}+$block%" else null,
                if (spCostReduce > 0) "${if (isEn) "SPC" else "SP비"}-$spCostReduce%" else null,
            ).joinToString(" ")
            pushLog(lang("자기 버프: $parts (3턴)", "Self buff: $parts (3 turns)"))
        }
    }

    /**
     * R101 — catalog REVIVE slot 이 있으면 KO 된 party member 한 명을 perTick% HP 로 부활.
     * 매칭이 없거나 KO 된 member 가 없으면 no-op. 우선 lowest index (먼저 죽은 멤버).
     */
    private fun tryReviveFromSkill(nameKo: String) {
        val idx = catalogSkillIndex ?: return
        val revivePct = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.REVIVE)
            .coerceIn(0, 100)
        if (revivePct <= 0) return
        val koIdx = party.indexOfFirst { it.hp <= 0 }
        if (koIdx < 0) return
        val target = party[koIdx]
        target.hp = (target.hpMax * revivePct / 100).coerceAtLeast(1)
        popups += Popup("+${target.hp}", onEnemy = false, targetIdx = koIdx, ttl = 1200L, color = Color.rgb(255, 240, 120))
        pushLog(lang("부활: ${displayName(target, isEn)} → ${target.hp} HP",
                     "Revived: ${displayName(target, isEn)} → ${target.hp} HP"))
    }

    /**
     * R99 — 입힌 데미지의 catalog HP_DRAIN% 만큼 actor HP 회복 (cap hpMax). 0 이면 no-op.
     */
    private fun tryHpDrainFromSkill(actor: Character, nameKo: String, dmgDealt: Int) {
        val idx = catalogSkillIndex ?: return
        val drainPct = idx.primaryModifierForEngineName(
            nameKo, com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.HP_DRAIN)
            .coerceIn(0, catalogBonusClamp)
        if (drainPct <= 0 || dmgDealt <= 0) return
        val heal = (dmgDealt * drainPct / 100).coerceAtLeast(1)
            .coerceAtMost(actor.hpMax - actor.hp)
        if (heal <= 0) return
        actor.hp += heal
        popups += Popup("+$heal", onEnemy = false, targetIdx = actorIdx, ttl = 900L, color = Color.rgb(220, 120, 220))
        pushLog(lang("흡혈: +$heal HP", "Drain: +$heal HP"))
    }

    /**
     * R97 — hit-roll. base 90% + attackerAccPct - targetDodgePct, clamp [30, 100].
     * 결과 = 명중 여부 (true = 적중, false = 빗나감/회피).
     */
    private fun rollHit(attackerAccPct: Int, targetDodgePct: Int): Boolean {
        val chance = (90 + attackerAccPct - targetDodgePct).coerceIn(30, 100)
        return Random.nextInt(100) < chance
    }

    /**
     * R96/R98 — 1턴 경과 처리.
     * R98: HP_REGEN_BUFF / SP_REGEN_BUFF 가 있으면 해당 member 에 HP/SP 회복 적용 (살아있는 member 만).
     * 이후 모든 buff turnsLeft -= 1, 만료 제거.
     */
    private fun tickPartyStatuses() {
        for ((idx, list) in partyStatuses) {
            val c = party.getOrNull(idx) ?: continue
            if (c.hp > 0) {
                var hpHealed = 0
                var spGained = 0
                for (e in list) {
                    when (e.status) {
                        Status.HP_REGEN_BUFF -> {
                            val heal = (c.hpMax - c.hp).coerceAtMost(e.perTick).coerceAtLeast(0)
                            c.hp += heal
                            hpHealed += heal
                        }
                        Status.SP_REGEN_BUFF -> {
                            val gain = (c.spMax - c.sp).coerceAtMost(e.perTick).coerceAtLeast(0)
                            c.sp += gain
                            spGained += gain
                        }
                        else -> {}
                    }
                }
                if (hpHealed > 0) {
                    popups += Popup("+$hpHealed", onEnemy = false, targetIdx = idx, ttl = 900L, color = Color.rgb(120, 240, 120))
                    pushLog(lang("재생: ${displayName(c, isEn)} +${hpHealed} HP", "Regen: ${displayName(c, isEn)} +$hpHealed HP"))
                }
                if (spGained > 0) {
                    pushLog(lang("재생: ${displayName(c, isEn)} +${spGained} SP", "Regen: ${displayName(c, isEn)} +$spGained SP"))
                }
            }
            val it = list.iterator()
            while (it.hasNext()) {
                val e = it.next()
                e.turnsLeft -= 1
                if (e.turnsLeft <= 0) it.remove()
            }
        }
    }

    private val enemy: EnemyInstance = run {
        // R80: forcedEnemyId 가 "h3_n_NNN" / "h3_h_NNN" 패턴이면 Hero3Catalog 의 161 enemies 사용.
        // 그 외는 기존 EnemyRegistry (placeholder 13 entries).
        val def = forcedEnemyId?.let { id ->
            catalogEnemy(id) ?: EnemyRegistry.get(id)
        } ?: EnemyRegistry.random(party.first().level)
        EnemyInstance(def, def.hpMax)
    }

    private fun catalogEnemy(id: String): com.hero3.remake.engine.EnemyDef? {
        if (!id.startsWith("h3_n_") && !id.startsWith("h3_h_")) return null
        val catalog = com.hero3.remake.catalog.Hero3CatalogProvider.get() ?: return null
        val hard = id.startsWith("h3_h_")
        val list = com.hero3.remake.catalog.Hero3CatalogBridge.enemiesFromCatalog(catalog, hard)
        return list.firstOrNull { it.id == id }
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
            val cost = effectiveSpCost(actorIdx, s.spCost)
            if (actor.sp < cost) {
                pushLog(lang("SP 부족.", "Not enough SP."))
                return
            }
            useSkill(s)
        }
    }

    private fun useSkill(s: Skill) {
        val actor = currentActor()
        actor.sp -= effectiveSpCost(actorIdx, s.spCost)
        val name = lang(s.nameKo, s.nameEn)
        // R91: catalog effect_v2 보정 — fuzzy 매칭 hit 의 ATT*/HP_HEAL* slot primarySigned 합.
        val catalogBonus = catalogBonusFor(s.nameKo, heal = s.heal)
        if (s.heal) {
            val targetIdx = lowestHpAliveAlly()
            val target = party[targetIdx]
            val intl = CharacterRegistry.effectiveIntl(actor)
            val healedRaw = (intl * s.powerMul).toInt() + s.flatBonus + catalogBonus
            val healed = healedRaw.coerceAtLeast(0).coerceAtMost(target.hpMax - target.hp)
            target.hp += healed
            popups += Popup("+$healed", onEnemy = false, targetIdx = targetIdx, ttl = 900L, color = Color.rgb(120, 240, 120))
            pushLog("$name → ${displayName(target, isEn)} +${healed} HP")
            if (catalogBonus != 0) pushLog(lang("(카탈로그 +$catalogBonus)", "(catalog +$catalogBonus)"))
            // R101: heal skill 이 REVIVE slot 가지면 KO 된 member 부활.
            tryReviveFromSkill(s.nameKo)
            registerSelfBuffsFromSkill(actorIdx, s.nameKo)
            phase = Phase.ANIMATE; animTtl = 500L
            return
        }
        val atk = (CharacterRegistry.effectiveAttack(actor) * s.powerMul).toInt() + s.flatBonus + catalogBonus
        val critBonus = catalogCritBonusFor(s.nameKo)
        // R97: 명중 판정. 액터 ACC buff, 적은 DODGE 0 (enemy 측 buff 미존재 — 향후 enemy.statuses 확장 시 추가).
        val accPct = buffPercent(actorIdx, Status.ACCURACY_BUFF)
        if (!rollHit(accPct, targetDodgePct = 0)) {
            pushLog(lang("$name → 빗나감.", "$name → missed."))
            phase = Phase.ANIMATE; animTtl = 500L
            return
        }
        // R102: catalog SHIELD_PIERCE → 적 방어력 perTick% 무시.
        val piercePct = catalogSkillIndex
            ?.primaryModifierForEngineName(s.nameKo,
                com.hero3.remake.catalog.Hero3CatalogSkillIndex.ModifierKind.SHIELD_PIERCE)
            ?.coerceIn(0, 100) ?: 0
        val effectiveEnemyDef = if (piercePct > 0)
            (enemy.def.def * (100 - piercePct) / 100).coerceAtLeast(0)
        else enemy.def.def
        val dmg = damage(atk, effectiveEnemyDef, extraCritPercent = critBonus)
        if (piercePct > 0) pushLog(lang("(방어 관통 -$piercePct%)", "(pierce -$piercePct%)"))
        enemy.hp -= dmg
        hitFlashMs = 220L
        heroLungeMs = 280L
        popups += Popup("-$dmg", onEnemy = true, targetIdx = -1, ttl = 900L, color = Color.rgb(255, 200, 100))
        pushLog("$name → $dmg")
        if (catalogBonus != 0) pushLog(lang("(카탈로그 +$catalogBonus)", "(catalog +$catalogBonus)"))
        // R94: catalog effectV2.nDebuffs > 0 인 skill 은 처치되지 않은 적에게 POISON 부여 (3턴).
        if (enemy.hp > 0) tryApplyPoisonFromSkill(s.nameKo, dmg)
        // R96: catalog CRIT_DEF / DEFENSE slot 값을 actor 자기 buff status 로 등록 (3턴).
        registerSelfBuffsFromSkill(actorIdx, s.nameKo)
        // R99: catalog HP_DRAIN slot → 입힌 데미지 × N% 를 actor HP 로 흡혈.
        tryHpDrainFromSkill(actor, s.nameKo, dmg)
        // R101: 공격 skill 도 REVIVE slot 가지면 KO 된 member 부활 (드물지만 가능).
        tryReviveFromSkill(s.nameKo)
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
            // R94: 적의 상태 이상 tick (poison/burn dot). 적이 죽으면 곧장 승리.
            tickEnemyStatuses()
            if (enemy.hp <= 0) { beginVictory(); return }
            // R95: SLOW/STUN 이면 적 행동 skip.
            if (!enemyShouldSkipAttack()) doEnemyAttack()
            if (aliveCount() == 0) {
                beginDefeat()
            } else {
                // R96: 한 라운드 (party 행동 → enemy 행동) 종료 → 파티 buff turnsLeft 감소.
                tickPartyStatuses()
                actorIdx = firstAliveFrom(0)
                menuIdx = 0; skillPickIdx = 0; itemPickIdx = 0
                phase = Phase.COMMAND
            }
        }
    }

    /**
     * R94/R95 — catalog 매칭 hit 의 `effectV2.nDebuffs > 0` 이면 N 종의 상태 이상을 부여.
     * nDebuffs 1=POISON, 2=POISON+BURN, 3=POISON+BURN+SLOW, ≥4=POISON+BURN+SLOW+STUN. 3턴 유지.
     * 같은 status 가 있으면 turnsLeft 갱신 (refresh).
     */
    private fun tryApplyPoisonFromSkill(nameKo: String, lastHitDmg: Int) {
        val nDebuffs = catalogDebuffCountFor(nameKo)
        if (nDebuffs <= 0) return
        val perTick = maxOf(2, lastHitDmg / 5)
        val order = listOf(Status.POISON, Status.BURN, Status.SLOW, Status.STUN)
        val applied = order.take(nDebuffs.coerceAtMost(order.size))
        for (st in applied) {
            val existing = enemy.statuses.firstOrNull { it.status == st }
            if (existing != null) {
                existing.turnsLeft = 3
            } else {
                enemy.statuses += StatusEffect(st, turnsLeft = 3, perTick = perTick)
            }
        }
        val label = applied.joinToString("/") { statusLabel(it, isEn) }
        pushLog(lang("적에게 [$label] 부여 (3턴, dot -${perTick}/턴).",
                     "Enemy debuffed [$label] (3 turns, dot -$perTick/turn)."))
    }

    /** R94/R95 — 적의 모든 상태 이상 1턴 효과 적용 + turnsLeft 감소 후 만료 제거. */
    private fun tickEnemyStatuses() {
        if (enemy.statuses.isEmpty() || enemy.hp <= 0) return
        val it = enemy.statuses.iterator()
        var totalDmg = 0
        while (it.hasNext()) {
            val e = it.next()
            when (e.status) {
                Status.POISON, Status.BURN -> {
                    val dmg = e.perTick
                    enemy.hp = (enemy.hp - dmg).coerceAtLeast(0)
                    totalDmg += dmg
                }
                Status.SLOW, Status.STUN -> { /* tick 시점 효과 없음 — doEnemyAttack 에서 처리 */ }
                Status.CRIT_DEF_BUFF, Status.DEFENSE_BUFF,
                Status.ACCURACY_BUFF, Status.DODGE_BUFF,
                Status.HP_REGEN_BUFF, Status.SP_REGEN_BUFF,
                Status.TAUNT_BUFF, Status.BLOCK_BUFF,
                Status.SP_COST_REDUCE_BUFF -> { /* party buff — enemy 에 부여 안 됨 */ }
            }
            e.turnsLeft -= 1
            if (e.turnsLeft <= 0) it.remove()
        }
        if (totalDmg > 0) {
            popups += Popup("-$totalDmg", onEnemy = true, targetIdx = -1,
                ttl = 900L, color = Color.rgb(120, 220, 120))
            pushLog(lang("도트: -$totalDmg HP", "DoT: -$totalDmg HP"))
        }
    }

    /** R95 — 적이 SLOW/STUN 상태이면 행동 skip 여부 판정. true = skip. */
    private fun enemyShouldSkipAttack(): Boolean {
        if (enemy.statuses.any { it.status == Status.STUN }) {
            pushLog(lang("적이 기절 상태 — 행동 불가.", "Enemy stunned — cannot act."))
            return true
        }
        if (enemy.statuses.any { it.status == Status.SLOW } && Random.nextFloat() < 0.5f) {
            pushLog(lang("적이 둔화 — 행동 누락.", "Enemy slowed — misses turn."))
            return true
        }
        return false
    }

    private fun statusLabel(st: Status, isEn: Boolean): String = when (st) {
        Status.POISON -> if (isEn) "POI" else "독"
        Status.BURN   -> if (isEn) "BRN" else "화상"
        Status.SLOW   -> if (isEn) "SLW" else "둔화"
        Status.STUN   -> if (isEn) "STN" else "기절"
        Status.CRIT_DEF_BUFF -> if (isEn) "CDF" else "크감"
        Status.DEFENSE_BUFF  -> if (isEn) "DEF" else "방어"
        Status.ACCURACY_BUFF -> if (isEn) "ACC" else "명중"
        Status.DODGE_BUFF    -> if (isEn) "DOD" else "회피"
        Status.HP_REGEN_BUFF -> if (isEn) "HPR" else "HP재"
        Status.SP_REGEN_BUFF -> if (isEn) "SPR" else "SP재"
        Status.TAUNT_BUFF    -> if (isEn) "TNT" else "도발"
        Status.BLOCK_BUFF    -> if (isEn) "BLK" else "블록"
        Status.SP_COST_REDUCE_BUFF -> if (isEn) "SPC" else "SP비"
    }

    private fun partyBuffLabel(st: Status, isEn: Boolean): String = statusLabel(st, isEn)

    private fun doEnemyAttack() {
        val alive = party.withIndex().filter { it.value.hp > 0 }
        if (alive.isEmpty()) return
        // R100: TAUNT_BUFF 가진 살아있는 member 가 있으면 우선 대상.
        val taunters = alive.filter { iv ->
            partyStatuses[iv.index]?.any { it.status == Status.TAUNT_BUFF } == true
        }
        val pool = if (taunters.isNotEmpty()) taunters else alive
        val pick = pool[Random.nextInt(pool.size)]
        val target = pick.value
        // R96: target 의 CRIT_DEF / DEFENSE buff 합산 → damage() / 최종 데미지에 반영.
        val critDefPct = buffPercent(pick.index, Status.CRIT_DEF_BUFF)
        val defPct     = buffPercent(pick.index, Status.DEFENSE_BUFF)
        // R97: target 의 DODGE buff 로 적의 hit-roll 감산. 적 ACC = 0 (catalog 측 enemy 없음).
        val dodgePct = buffPercent(pick.index, Status.DODGE_BUFF)
        if (!rollHit(attackerAccPct = 0, targetDodgePct = dodgePct)) {
            val name = lang(enemy.def.nameKo, enemy.def.nameEn)
            pushLog(lang("$name → ${displayName(target, isEn)} 회피!",
                         "$name → ${displayName(target, isEn)} dodged!"))
            return
        }
        // R101: target 의 BLOCK_BUFF — perTick% 확률로 무효화.
        val blockPct = buffPercent(pick.index, Status.BLOCK_BUFF)
        if (blockPct > 0 && Random.nextInt(100) < blockPct) {
            val name = lang(enemy.def.nameKo, enemy.def.nameEn)
            pushLog(lang("$name → ${displayName(target, isEn)} 막아냄!",
                         "$name → ${displayName(target, isEn)} blocked!"))
            return
        }
        val rawDmg = damage(enemy.def.atk, CharacterRegistry.effectiveDefense(target),
            extraCritDefPercent = critDefPct)
        val dmg = if (defPct > 0) maxOf(1, rawDmg * (100 - defPct) / 100) else rawDmg
        target.hp = (target.hp - dmg).coerceAtLeast(0)
        popups += Popup("-$dmg", onEnemy = false, targetIdx = pick.index, ttl = 900L, color = Color.rgb(255, 80, 80))
        val name = lang(enemy.def.nameKo, enemy.def.nameEn)
        pushLog("$name → ${displayName(target, isEn)} $dmg.")
        if (critDefPct > 0 || defPct > 0) {
            pushLog(lang("(버프 흡수: 크감 $critDefPct% / 방어 $defPct%)",
                         "(buffs: critDef $critDefPct% / def $defPct%)"))
        }
    }

    /** R83/R93/R96: damage = max(1, atk - def/2) × variance(0.8..1.2), with crit.
     *  base crit chance 8% + [extraCritPercent] (catalog CRI_RATE slot, R93). clamp [0, 50%].
     *  crit multiplier 1.7 - [extraCritDefPercent]/100 (R96, target 측 CRIT_DEF_BUFF). clamp [1.0, 1.7].
     *  catalog-fed enemy (forcedEnemyId h3_*) 은 추후 R63 stat enum / element 적용 (R84+).
     */
    private fun damage(atk: Int, def: Int, extraCritPercent: Int = 0, extraCritDefPercent: Int = 0): Int {
        val raw = max(1, atk - def / 2)
        val critChance = (0.08f + extraCritPercent / 100f).coerceIn(0f, 0.5f)
        val isCrit = Random.nextFloat() < critChance
        val variance = (raw * (0.8f + Random.nextFloat() * 0.4f)).toInt()
        val critMul = (1.7f - extraCritDefPercent / 100f).coerceIn(1.0f, 1.7f)
        val final = if (isCrit) (variance * critMul).toInt() else variance
        if (isCrit) pushLog(lang("크리티컬!", "Critical!"))
        return max(1, final)
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
        // R94/R95: 상태 이상 인디케이터 (적 HP 바 우측).
        if (enemy.statuses.isNotEmpty()) {
            val statusText = enemy.statuses.joinToString(" ") { e ->
                "${statusLabel(e.status, isEn)}(${e.turnsLeft})"
            }
            val statusPaint = Paint(UiKit.muted).apply { color = Color.rgb(150, 230, 150) }
            canvas.drawText(statusText, barX + barW - 90f, barY - 2f, statusPaint)
        }

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
            } else {
                // R96: party buff 인디케이터 (행 우측, 좌상 작은 텍스트).
                val buffs = partyStatuses[i]
                if (!buffs.isNullOrEmpty()) {
                    val txt = buffs.joinToString(" ") { e -> partyBuffLabel(e.status, isEn) + "(${e.turnsLeft})" }
                    canvas.drawText(txt, virtualWidth - 90f, y + 5f,
                        Paint(UiKit.muted).apply { color = Color.rgb(130, 200, 255); textSize = 8f })
                }
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
