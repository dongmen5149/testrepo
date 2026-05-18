package com.hero3.remake.engine

/**
 * 캐릭터 + 직업 데이터 모델.
 *
 * 원본 char_dat 에는 리츠/케이 각 5개 클래스(총 10) 의 이름만 추출되어 있고
 * 실제 스탯 수치는 미해독 상태이므로 직업별 base stats 는 휴리스틱 placeholder.
 * Ghidra 결과로 실제 수치 디코드되면 이 곳만 교체하면 된다.
 */
data class Stats(
    val str: Int,    // 힘
    val dex: Int,    // 민첩
    val vit: Int,    // 체력
    val intl: Int,   // 정신
    val att1: Int,
    val att2: Int,
    val pdef: Int,
    val mdef: Int,
    val cri: Int,    // %
    val res: Int,    // %
    val acc: Int,
    val dod: Int,
)

data class CharacterClass(
    val id: String,
    val nameKo: String,
    val nameEn: String,
    val base: Stats,
)

/**
 * 캐릭터 인스턴스 — Registry 의 base 위에 레벨/HP/SP/EXP 등 가변 상태를 얹은 것.
 * GameState 가 직렬화해 저장.
 */
data class Character(
    val id: String,
    val classId: String,
    var level: Int,
    var hp: Int,
    var hpMax: Int,
    var sp: Int,
    var spMax: Int,
    var exp: Int,
    /** 장착 슬롯 — 비어있으면 null. */
    var equipWeapon: String? = null,
    var equipArmor: String? = null,
    var equipAccessory: String? = null,
) {
    /** Lv N → Lv N+1 에 필요한 누적 EXP. 단순 quadratic. */
    fun expToNext(): Int = level * level * 20

    fun gainExp(amount: Int): Int {
        exp += amount
        var levelsGained = 0
        while (exp >= expToNext()) {
            exp -= expToNext()
            level++
            // 레벨업 보너스 — VIT/INT 비율 약간 반영, full heal
            val hpInc = 8 + level
            val spInc = 4 + level / 2
            hpMax += hpInc; sp = spMax; hp = hpMax
            spMax += spInc; sp = spMax
            levelsGained++
        }
        return levelsGained
    }
}

object CharacterRegistry {

    /** char_dat.json 의 한국어 이름과 1:1 매핑 + 영어 표기. */
    val classes: List<CharacterClass> = listOf(
        CharacterClass("ritz_assault",   "어썰트워리어",   "Assault Warrior",
            Stats(12, 10, 11, 6, 22, 0, 14, 5, 8,  0, 88,  10)),
        CharacterClass("ritz_disrupt",   "디스럽터",       "Disruptor",
            Stats(10, 14, 9,  8, 18, 4, 12, 8, 12, 5, 92,  14)),
        CharacterClass("ritz_gunslinger","건슬링어",       "Gunslinger",
            Stats(8,  16, 8,  9, 20, 6, 10, 7, 14, 5, 95,  16)),
        CharacterClass("ritz_templar",   "나이트템플러",   "Knight Templar",
            Stats(13, 8,  13, 7, 20, 4, 18, 10, 6, 8, 85,  8)),
        CharacterClass("ritz_crazy",     "크레이지암즈",   "Crazy Arms",
            Stats(15, 12, 10, 5, 26, 2, 12, 4, 10, 0, 86,  12)),

        CharacterClass("kei_berserker", "버서커",         "Berserker",
            Stats(15, 10, 13, 4, 28, 0, 14, 4, 9,  0, 84,  9)),
        CharacterClass("kei_deathknight","데스나이트",     "Death Knight",
            Stats(13, 9,  14, 8, 24, 6, 18, 12, 6, 10, 82, 7)),
        CharacterClass("kei_shadow",    "섀도우워커",     "Shadow Walker",
            Stats(11, 16, 10, 7, 22, 4, 12, 8, 18, 6, 94, 18)),
        CharacterClass("kei_guardian",  "가디언나이트",   "Guardian Knight",
            Stats(14, 8,  15, 8, 22, 4, 20, 12, 5, 10, 83, 7)),
        CharacterClass("kei_soulmaster","소울마스터",     "Soul Master",
            Stats(9,  11, 10, 16, 14, 22, 10, 18, 7, 14, 88, 11)),
    )

    private val byId: Map<String, CharacterClass> = classes.associateBy { it.id }

    fun classOf(id: String): CharacterClass? = byId[id]

    /** 새 캐릭터 생성 — base stats 의 vit/intl 로 HP/SP 결정. */
    fun newCharacter(id: String, classId: String, level: Int = 1): Character {
        val c = byId[classId] ?: classes.first()
        val hpMax = 80 + c.base.vit * 4 + (level - 1) * 8
        val spMax = 30 + c.base.intl * 3 + (level - 1) * 4
        return Character(
            id = id, classId = classId, level = level,
            hp = hpMax, hpMax = hpMax,
            sp = spMax, spMax = spMax,
            exp = 0,
        )
    }

    /** 기본 파티 — 케이(버서커) + 리츠(어썰트워리어). */
    fun defaultParty(): List<Character> = listOf(
        newCharacter("kei",  "kei_berserker"),
        newCharacter("ritz", "ritz_assault"),
    )

    /** 장비 보너스를 합친 effective ATK. */
    fun effectiveAttack(ch: Character): Int {
        val cls = classOf(ch.classId) ?: return 1
        val w = ch.equipWeapon?.let { ItemRegistry.get(it) }
        val r = ch.equipAccessory?.let { ItemRegistry.get(it) }
        val weaponPower = if (w?.kind == ItemKind.WEAPON) w.power else 0
        // ring_pwr / ring_dest 가 STR 보너스, 나머지 액세서리는 ATK 무관
        val accStr = when (r?.id) {
            "ring_pwr", "ring_dest" -> r.power
            else -> 0
        }
        return cls.base.att1 + cls.base.str / 2 + weaponPower + accStr
    }

    /** 장비 보너스를 합친 effective DEF. */
    fun effectiveDefense(ch: Character): Int {
        val cls = classOf(ch.classId) ?: return 1
        val a = ch.equipArmor?.let { ItemRegistry.get(it) }
        val armorPower = if (a?.kind == ItemKind.ARMOR) a.power else 0
        return cls.base.pdef + cls.base.vit / 2 + armorPower
    }

    /** ring_mana 가 INT +N 으로 효력을 발휘. heal 스킬에 영향. */
    fun effectiveIntl(ch: Character): Int {
        val cls = classOf(ch.classId) ?: return 0
        val r = ch.equipAccessory?.let { ItemRegistry.get(it) }
        val intBonus = if (r?.id == "ring_mana") r.power else 0
        return cls.base.intl + intBonus
    }
}
