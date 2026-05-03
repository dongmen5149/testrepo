package com.hero3.remake.engine

/**
 * 스킬 데이터 — 클래스 별 1~2 개. SP 소모.
 *
 * 데미지 계산: effectiveAtk * powerMul + flatBonus.
 * heal=true 면 자기 회복 (powerMul × intl + flat).
 */
data class Skill(
    val id: String,
    val nameKo: String,
    val nameEn: String,
    val spCost: Int,
    val powerMul: Float = 1f,
    val flatBonus: Int = 0,
    val heal: Boolean = false,
    val descKo: String = "",
    val descEn: String = "",
    val requiredLevel: Int = 1,
)

object SkillRegistry {
    private val byClass: Map<String, List<Skill>> = mapOf(
        "ritz_assault"    to listOf(
            skill("ritz_strike",   "강타",       "Power Strike",   sp = 6,  mul = 1.5f),
            skill("ritz_megacrush","메가 크러쉬", "Mega Crush",     sp = 14, mul = 2.4f, lvl = 5),
        ),
        "ritz_disrupt"    to listOf(skill("ritz_disrupt",  "디스럽트",   "Disrupt",        sp = 8,  mul = 1.4f, flat = 4)),
        "ritz_gunslinger" to listOf(
            skill("ritz_aimshot",  "정조준",     "Aimed Shot",     sp = 8,  mul = 1.7f),
            skill("ritz_rapidfire","연사",       "Rapid Fire",     sp = 16, mul = 2.6f, lvl = 6),
        ),
        "ritz_templar"    to listOf(
            skill("ritz_holyheal", "성스런치유", "Holy Heal",      sp = 10, mul = 0.0f, flat = 60, heal = true),
            skill("ritz_holystorm","성스런 폭풍","Holy Storm",     sp = 18, mul = 2.0f, flat = 20, lvl = 7),
        ),
        "ritz_crazy"      to listOf(skill("ritz_madslash", "광기의 일격","Mad Slash",     sp = 6,  mul = 2.0f)),

        "kei_berserker"   to listOf(
            skill("kei_rage",      "광폭난도",   "Rampage",        sp = 8,  mul = 1.8f),
            skill("kei_warcry",    "전투의 외침","War Cry",        sp = 4,  mul = 1.2f, flat = 6),
            skill("kei_bloodfury", "피의 격노",  "Blood Fury",     sp = 16, mul = 3.0f, lvl = 8),
        ),
        "kei_deathknight" to listOf(
            skill("kei_deathblow", "죽음의 일격","Death Blow",     sp = 12, mul = 2.2f),
            skill("kei_doomwave",  "파멸의 파도","Doom Wave",      sp = 22, mul = 3.0f, flat = 20, lvl = 8),
        ),
        "kei_shadow"      to listOf(
            skill("kei_shadowcut", "그림자 베기","Shadow Cut",     sp = 6,  mul = 1.6f),
            skill("kei_phantom",   "환영 베기",  "Phantom Cut",    sp = 14, mul = 2.6f, lvl = 6),
        ),
        "kei_guardian"    to listOf(skill("kei_shieldbash","쉴드배쉬",   "Shield Bash",    sp = 8,  mul = 1.5f, flat = 8)),
        "kei_soulmaster"  to listOf(
            skill("kei_soulburst", "영혼 폭발",  "Soul Burst",     sp = 10, mul = 0.5f, flat = 30),
            skill("kei_soulheal",  "영혼 치유",  "Soul Heal",      sp = 8,  mul = 0.0f, flat = 50, heal = true),
            skill("kei_soulnova",  "영혼 노바",  "Soul Nova",      sp = 20, mul = 1.5f, flat = 80, lvl = 7),
        ),
    )

    /** 캐릭터 레벨로 필터된 스킬 목록. */
    fun forClass(classId: String, level: Int = 99): List<Skill> =
        byClass[classId]?.filter { it.requiredLevel <= level } ?: emptyList()

    private fun skill(id: String, ko: String, en: String, sp: Int, mul: Float = 1f,
                      flat: Int = 0, heal: Boolean = false,
                      descKo: String = "", descEn: String = "", lvl: Int = 1): Skill =
        Skill(id, ko, en, sp, mul, flat, heal, descKo, descEn, requiredLevel = lvl)
}
