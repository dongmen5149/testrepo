package com.hero3.remake.catalog

import com.hero3.remake.engine.AssetReader
import org.json.JSONArray
import org.json.JSONObject

/**
 * Hero3 게임 데이터 catalog — R64-R70 산출물 `game_balance.json` (582KB v1.1) 로더.
 *
 * 입력: `assets/game_balance.json` (R66 export_game_balance.py 산출)
 * 출력: stat_enum / rarity / items / skills / enemies / bosses / quests / char_classes / des_status
 *
 * R70 MASTER_SPEC §13 의 "Android 리메이크 권장 구현 순서" 2번 (data loader) 구현.
 * Hero4Catalog (R69 Phase C Step 5) 와 동일 패턴.
 */

data class Hero3StatEnumEntry(
    val codeHex: String,
    val name: String,
    val desc: String,
    val from: String,
)

data class Hero3Rarity(
    val prefix: String,
    val name: String,
    val color: String,
    val modifierArmor: Double,
    val modifierWeapon: Double,
)

data class Hero3Item(
    val pos: Int,
    val name: String,
    val cleanName: String,
    val rarity: String,
    val layout: String,
    val price: Int,
    val tier: Int,
    val variant: Int,
    val reqLevel: Int,
    val statPrimary: Int,
    val statSecondary: Int,
    val trailer: String,
)

data class Hero3ItemCategory(
    val file: String,
    val category: String,
    val nItems: Int,
    val items: List<Hero3Item>,
)

data class Hero3SkillEffectSlot(
    val codeHex: String,
    val codeName: String,
    val isSentinel: Boolean,
    val isZero: Boolean,
    val primarySigned: Int,
    val secondarySigned: Int,
)

data class Hero3SkillEffectV2(
    val rank: Int,
    val nDebuffs: Int,
    val slot1: Hero3SkillEffectSlot,
    val slot2: Hero3SkillEffectSlot,
    val slot3: Hero3SkillEffectSlot,
)

data class Hero3Skill(
    val pos: Int,
    val name: String,
    val category: Int,
    val categoryName: String,
    val desc: String,
    val tailHex: String,
    val rankOrLevel: Int,
    val effectV2: Hero3SkillEffectV2?,
)

data class Hero3WeaponSkillSet(
    val file: String,
    val weapon: String,
    val nSkills: Int,
    val skills: List<Hero3Skill>,
)

data class Hero3EnemyStats(
    val lvl: Int,
    val hpMax: Int,
    val expGold: Int,
    val atk: Int,
    val agi: Int,
)

data class Hero3Enemy(
    val pos: Int,
    val name: String,
    val stats: Hero3EnemyStats,
    val statBlockHex: String,
    val trailerHex: String,
)

data class Hero3BossTrailerDecoded(
    val combatRating: Int,
    val spriteIdx: Int,
    val skillSlots: List<Int>,
    val isMiscBoss: Boolean,
    val expectedRating: Int,
    val ratingMatches: Boolean,
)

data class Hero3Boss(
    val pos: Int,
    val name: String,
    val stats: Hero3EnemyStats,
    val trailerHex: String,
    val trailerDecoded: Hero3BossTrailerDecoded?,
)

data class Hero3DesPendingFile(
    val path: String,
    val role: String,
)

data class Hero3DesStatus(
    val algorithm: String,
    val key: String,
    val pendingFiles: List<Hero3DesPendingFile>,
    val blocker: String,
)

data class Hero3Catalog(
    val schemaVersion: String,
    val round: Int,
    val statEnum: Map<String, Hero3StatEnumEntry>,
    val rarity: List<Hero3Rarity>,
    val items: List<Hero3ItemCategory>,
    val skills: List<Hero3WeaponSkillSet>,
    val enemiesNormal: List<Hero3Enemy>,
    val enemiesHard: List<Hero3Enemy>,
    val bossesNormal: List<Hero3Boss>,
    val bossesHard: List<Hero3Boss>,
    val combatRatingFormulaNormal: String,
    val combatRatingFormulaHard: String,
    val desStatus: Hero3DesStatus,
) {
    val totalItems: Int get() = items.sumOf { it.nItems }
    val totalSkills: Int get() = skills.sumOf { it.nSkills }
    val totalEnemies: Int get() = enemiesNormal.size
    val totalBosses: Int get() = bossesNormal.size

    /** 특정 stat code 의 master enum 이름 lookup (예: 0x05 → "ATT1"). */
    fun statName(code: Int): String? =
        statEnum["0x${code.toString(16).padStart(2, '0')}"]?.name

    /** 보스 ID 매핑 미해결 — DES 복호화 후 R71+ 에서 확정 가능 (R67 H4 가설). */
    fun bossSkillIdsResolved(): Boolean = false
}

object Hero3CatalogLoader {

    /** [reader] 를 통해 `game_balance.json` 을 파싱하여 Hero3Catalog 반환. */
    fun load(reader: AssetReader): Hero3Catalog {
        val raw = reader.readText("game_balance.json")
        val root = JSONObject(raw)

        val meta = root.optJSONObject("meta") ?: JSONObject()
        val schemaVersion = meta.optString("schema_version", "1.1")
        val round = meta.optInt("round", 0)

        // stat_enum
        val statEnumMap = mutableMapOf<String, Hero3StatEnumEntry>()
        root.optJSONObject("stat_enum")?.let { obj ->
            val keys = obj.keys()
            while (keys.hasNext()) {
                val k = keys.next()
                val o = obj.optJSONObject(k) ?: continue
                statEnumMap[k] = Hero3StatEnumEntry(
                    codeHex = k,
                    name = o.optString("name"),
                    desc = o.optString("desc"),
                    from = o.optString("from"),
                )
            }
        }

        // rarity
        val rarityList = mutableListOf<Hero3Rarity>()
        root.optJSONObject("rarity")?.let { obj ->
            val keys = obj.keys()
            while (keys.hasNext()) {
                val p = keys.next()
                val o = obj.optJSONObject(p) ?: continue
                rarityList += Hero3Rarity(
                    prefix = p,
                    name = o.optString("name"),
                    color = o.optString("color"),
                    modifierArmor = o.optDouble("modifier_armor", 1.0),
                    modifierWeapon = o.optDouble("modifier_weapon", 1.0),
                )
            }
        }

        // items (18 categories)
        val items = mutableListOf<Hero3ItemCategory>()
        root.optJSONObject("items")?.let { obj ->
            val keys = obj.keys()
            while (keys.hasNext()) {
                val fn = keys.next()
                val cat = obj.optJSONObject(fn) ?: continue
                val itemArr = cat.optJSONArray("items") ?: JSONArray()
                val parsedItems = mutableListOf<Hero3Item>()
                for (i in 0 until itemArr.length()) {
                    val it = itemArr.optJSONObject(i) ?: continue
                    parsedItems += Hero3Item(
                        pos = it.optInt("pos"),
                        name = it.optString("name"),
                        cleanName = it.optString("clean_name", it.optString("name")),
                        rarity = it.optString("rarity", "normal"),
                        layout = it.optString("layout", "?"),
                        price = it.optInt("price", 0),
                        tier = it.optInt("tier", 0),
                        variant = it.optInt("variant", 0xff),
                        reqLevel = it.optInt("req_level", 0),
                        statPrimary = it.optInt("stat_primary", 0),
                        statSecondary = it.optInt("stat_secondary", 0),
                        trailer = it.optString("trailer", ""),
                    )
                }
                items += Hero3ItemCategory(
                    file = fn,
                    category = cat.optString("category", "?"),
                    nItems = cat.optInt("n_items", parsedItems.size),
                    items = parsedItems,
                )
            }
        }

        // skills (7 weapon classes)
        val skills = mutableListOf<Hero3WeaponSkillSet>()
        root.optJSONObject("skills")?.let { obj ->
            val keys = obj.keys()
            while (keys.hasNext()) {
                val fn = keys.next()
                val ws = obj.optJSONObject(fn) ?: continue
                val skillArr = ws.optJSONArray("skills") ?: JSONArray()
                val parsedSkills = mutableListOf<Hero3Skill>()
                for (i in 0 until skillArr.length()) {
                    val s = skillArr.optJSONObject(i) ?: continue
                    val effectV2 = s.optJSONObject("effect_v2")?.let { e ->
                        Hero3SkillEffectV2(
                            rank = e.optInt("rank"),
                            nDebuffs = e.optInt("n_debuffs"),
                            slot1 = parseSlot(e.optJSONObject("slot1")),
                            slot2 = parseSlot(e.optJSONObject("slot2")),
                            slot3 = parseSlot(e.optJSONObject("slot3")),
                        )
                    }
                    parsedSkills += Hero3Skill(
                        pos = s.optInt("pos"),
                        name = s.optString("name"),
                        category = s.optInt("category", -1),
                        categoryName = s.optString("category_name", "?"),
                        desc = s.optString("desc"),
                        tailHex = s.optString("tail_hex", ""),
                        rankOrLevel = s.optInt("rank_or_level", 0),
                        effectV2 = effectV2,
                    )
                }
                skills += Hero3WeaponSkillSet(
                    file = fn,
                    weapon = ws.optString("weapon", "?"),
                    nSkills = ws.optInt("n_skills", parsedSkills.size),
                    skills = parsedSkills,
                )
            }
        }

        // enemies / bosses
        val enemiesObj = root.optJSONObject("enemies") ?: JSONObject()
        val enemiesNormal = parseEnemyList(enemiesObj.optJSONArray("normal"))
        val enemiesHard = parseEnemyList(enemiesObj.optJSONArray("hard"))
        val bossesObj = root.optJSONObject("bosses") ?: JSONObject()
        val bossesNormal = parseBossList(bossesObj.optJSONArray("normal"))
        val bossesHard = parseBossList(bossesObj.optJSONArray("hard"))
        val formula = bossesObj.optJSONObject("combat_rating_formula")
        val crfNormal = formula?.optString("normal") ?: "round(lvl/2 + 44)"
        val crfHard = formula?.optString("hard") ?: "round(lvl/2 + 64)"

        // des_status
        val desObj = root.optJSONObject("des_status") ?: JSONObject()
        val pendingFiles = mutableListOf<Hero3DesPendingFile>()
        desObj.optJSONArray("pending_files")?.let { arr ->
            for (i in 0 until arr.length()) {
                val o = arr.optJSONObject(i) ?: continue
                pendingFiles += Hero3DesPendingFile(
                    path = o.optString("path"),
                    role = o.optString("role"),
                )
            }
        }
        val desStatus = Hero3DesStatus(
            algorithm = desObj.optString("algorithm"),
            key = desObj.optString("key"),
            pendingFiles = pendingFiles,
            blocker = desObj.optString("blocker"),
        )

        return Hero3Catalog(
            schemaVersion = schemaVersion,
            round = round,
            statEnum = statEnumMap,
            rarity = rarityList,
            items = items,
            skills = skills,
            enemiesNormal = enemiesNormal,
            enemiesHard = enemiesHard,
            bossesNormal = bossesNormal,
            bossesHard = bossesHard,
            combatRatingFormulaNormal = crfNormal,
            combatRatingFormulaHard = crfHard,
            desStatus = desStatus,
        )
    }

    private fun parseSlot(o: JSONObject?): Hero3SkillEffectSlot {
        if (o == null) return Hero3SkillEffectSlot("0x7f", "(sentinel)", true, false, 0, 0)
        return Hero3SkillEffectSlot(
            codeHex = o.optString("code_hex", "0x7f"),
            codeName = o.optString("code_name", "?"),
            isSentinel = o.optBoolean("is_sentinel", true),
            isZero = o.optBoolean("is_zero", false),
            primarySigned = o.optInt("primary_signed", 0),
            secondarySigned = o.optInt("secondary_signed", 0),
        )
    }

    private fun parseEnemyList(arr: JSONArray?): List<Hero3Enemy> {
        val out = mutableListOf<Hero3Enemy>()
        if (arr == null) return out
        for (i in 0 until arr.length()) {
            val e = arr.optJSONObject(i) ?: continue
            val s = e.optJSONObject("stats") ?: JSONObject()
            out += Hero3Enemy(
                pos = e.optInt("pos"),
                name = e.optString("name"),
                stats = Hero3EnemyStats(
                    lvl = s.optInt("lvl"),
                    hpMax = s.optInt("hp_max"),
                    expGold = s.optInt("exp_gold"),
                    atk = s.optInt("f16"),
                    agi = s.optInt("agi_or"),
                ),
                statBlockHex = e.optString("stat_block_hex"),
                trailerHex = e.optString("trailer_hex"),
            )
        }
        return out
    }

    private fun parseBossList(arr: JSONArray?): List<Hero3Boss> {
        val out = mutableListOf<Hero3Boss>()
        if (arr == null) return out
        for (i in 0 until arr.length()) {
            val b = arr.optJSONObject(i) ?: continue
            val s = b.optJSONObject("stats") ?: JSONObject()
            val tdObj = b.optJSONObject("trailer_decoded")
            val td = tdObj?.let {
                val slotArr = it.optJSONArray("skill_slots") ?: JSONArray()
                Hero3BossTrailerDecoded(
                    combatRating = it.optInt("combat_rating"),
                    spriteIdx = it.optInt("sprite_idx"),
                    skillSlots = (0 until slotArr.length()).map { i -> slotArr.optInt(i) },
                    isMiscBoss = it.optBoolean("is_misc_boss"),
                    expectedRating = it.optInt("expected_rating"),
                    ratingMatches = it.optBoolean("rating_matches"),
                )
            }
            out += Hero3Boss(
                pos = b.optInt("pos"),
                name = b.optString("name"),
                stats = Hero3EnemyStats(
                    lvl = s.optInt("lvl"),
                    hpMax = s.optInt("hp_max"),
                    expGold = s.optInt("exp_gold"),
                    atk = s.optInt("f16"),
                    agi = s.optInt("agi_or"),
                ),
                trailerHex = b.optString("trailer_hex"),
                trailerDecoded = td,
            )
        }
        return out
    }
}
