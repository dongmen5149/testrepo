package com.hero3.remake.catalog

/**
 * R89 — Catalog skill 인덱스.
 *
 * [Hero3Catalog.skills] 의 7 weapon sets (s4..s10_dat) 와 그 안의 ~100+ skills 를
 * 빠르게 평탄화/그룹화/색상 hint 와 함께 조회할 수 있게 한다.
 *
 * R85 [Hero3CatalogQuestIndex] 의 자매 API. 같은 패턴 (entries / byKey / colorOf / fileColors / FILE_PALETTE):
 *  - entries        : 평탄화된 (skill, owning set) pairs
 *  - byWeapon       : weapon label 기준 group
 *  - byFile         : s4_dat .. s10_dat 기준 group
 *  - colorOf(file)  : weapon set 파일별 안정적 ARGB 색
 *  - fileColors()   : 일괄 매핑 (UI 캐싱용)
 *
 * 용도:
 *  - CatalogViewerScene Skills tab 의 weapon-별 색 구분 + per-skill drill-down.
 *  - 추후 BattleScene 에서 weapon-skill ↔ engine SkillRegistry 의 fuzzy 매칭 (name contains 등).
 *  - 추후 effectV2 slot 정보 표시.
 *
 * 7 weapon files (R71 분석):
 *    s4_dat = 창 (스피어), s5_dat = 검 (대검), s6_dat = 단검,
 *    s7_dat = 건 (피스톨), s8_dat = 라이플, s9_dat = 홀리석 (백마법), s10_dat = 다크석 (흑마법)
 */
class Hero3CatalogSkillIndex(
    val entries: List<Entry>,
    val byWeapon: Map<String, List<Entry>>,
    val byFile: Map<String, List<Entry>>,
) {
    /** 한 행을 표시하기 좋게 weapon set + skill 을 묶은 view. */
    data class Entry(
        val file: String,
        val weapon: String,
        val skill: Hero3Skill,
    )

    val size: Int get() = entries.size
    val fileCount: Int get() = byFile.size
    val weaponCount: Int get() = byWeapon.size

    /** weapon 라벨이 [fragment] 를 포함하는 skill 들. */
    fun lookupByWeapon(fragment: String): List<Entry> {
        val needle = fragment.trim()
        if (needle.isEmpty()) return emptyList()
        return entries.filter { it.weapon.contains(needle) }
    }

    /** skill 이름이 [fragment] 를 포함하는 entries. engine ↔ catalog 미래 fuzzy bridge 용. */
    fun lookupByName(fragment: String): List<Entry> {
        val needle = fragment.trim()
        if (needle.isEmpty()) return emptyList()
        return entries.filter { it.skill.name.contains(needle) }
    }

    /**
     * R88 [Hero3CatalogQuestIndex.colorOf] 와 같은 규칙 — 정렬된 파일명을 [FILE_PALETTE] 슬롯에 매핑.
     * 미지 파일은 hash fallback (각 채널 ≥ 0x80 보장 — 어두운 배경 가독).
     */
    fun colorOf(file: String): Int {
        val sortedFiles = byFile.keys.sorted()
        val idx = sortedFiles.indexOf(file)
        return if (idx >= 0) FILE_PALETTE[idx % FILE_PALETTE.size]
        else fallbackHashColor(file)
    }

    /** 파일명 → 색상 (UI 캐싱용 일괄 매핑). */
    fun fileColors(): Map<String, Int> =
        byFile.keys.sorted().withIndex().associate { (i, f) ->
            f to FILE_PALETTE[i % FILE_PALETTE.size]
        }

    /**
     * R91/R93: catalog effectV2 의 어떤 stat code 를 어느 식에 더할지 지정.
     *
     *  - OFFENSE   = ATT*               (R91: BattleScene.useSkill 데미지 +)
     *  - HEAL      = HP_HEAL* / HP_REGEN* (R91: BattleScene.useSkill 회복 +)
     *  - DEFENSE   = P_DEF / M_DEF      (R93: 미래 wiring — 받는 데미지 reduction)
     *  - CRIT_RATE = CRI_RATE           (R93: BattleScene.damage crit % 가산)
     *  - CRIT_DEF  = CRI_DEF            (R93: 미래 wiring — 받는 crit 감쇄)
     *  - ACCURACY  = ACC                (R93: 미래 wiring — miss 시스템 도입 후)
     *  - DODGE     = DOD                (R93: 미래 wiring — 회피 시스템 도입 후)
     */
    enum class ModifierKind {
        OFFENSE, HEAL, DEFENSE, CRIT_RATE, CRIT_DEF, ACCURACY, DODGE,
        /** R98 — HP_REGEN slot 한정 (ongoing tick). HEAL kind 와 겹쳐 즉시-시전 + 지속 효과 모두 가능. */
        HP_REGEN,
        /** R98 — SP_REGEN slot 한정 (ongoing tick). */
        SP_REGEN,
        /** R99 — HP_DRAIN slot. 시전 시 입힌 데미지의 perTick% 를 actor HP 로 회복 (life steal). */
        HP_DRAIN,
        /** R100 — TAUNT slot. 시전 시 actor 를 적 target picker 우선순위로 N턴 등록. */
        TAUNT,
        /** R101 — REVIVE slot. 시전 시 KO 된 party member 한 명을 perTick% HP 로 부활. */
        REVIVE,
        /** R101 — BLOCK slot. 시전 시 actor 자기 BLOCK buff (perTick% 받는 공격 무효) 등록. */
        BLOCK,
    }

    /**
     * R91 — engine 데미지/회복 식에 가산할 catalog 보정값.
     *
     * 살아있는 effectV2 slot 만 검사하고, [kind] 에 맞는 codeName 을 가진 slot 의
     * `primarySigned` 를 합산한다. 매칭이 없거나 effectV2=null 이면 0.
     *
     *  - [ModifierKind.OFFENSE] → codeName 이 "ATT" 로 시작 (ATT1 / ATT1_BASE / ATT2)
     *  - [ModifierKind.HEAL]    → codeName 이 "HP_HEAL" / "HP_REGEN" 으로 시작
     *
     * BattleScene.useSkill 가 호출. 결과는 clamp 등 후처리 없이 raw 합을 돌려준다 —
     * 호출측에서 imbalance 방지 clamp 적용.
     */
    fun primaryModifier(skill: Hero3Skill, kind: ModifierKind): Int {
        val ev = skill.effectV2 ?: return 0
        val live = listOf(ev.slot1, ev.slot2, ev.slot3).filterNot { it.isSentinel || it.isZero }
        var sum = 0
        for (s in live) {
            val keep = when (kind) {
                ModifierKind.OFFENSE   -> s.codeName.startsWith("ATT")
                ModifierKind.HEAL      -> s.codeName.startsWith("HP_HEAL") || s.codeName.startsWith("HP_REGEN")
                ModifierKind.DEFENSE   -> s.codeName == "P_DEF" || s.codeName == "M_DEF"
                ModifierKind.CRIT_RATE -> s.codeName == "CRI_RATE"
                ModifierKind.CRIT_DEF  -> s.codeName == "CRI_DEF"
                ModifierKind.ACCURACY  -> s.codeName == "ACC"
                ModifierKind.DODGE     -> s.codeName == "DOD"
                ModifierKind.HP_REGEN  -> s.codeName == "HP_REGEN"
                ModifierKind.SP_REGEN  -> s.codeName == "SP_REGEN"
                ModifierKind.HP_DRAIN  -> s.codeName == "HP_DRAIN"
                ModifierKind.TAUNT     -> s.codeName == "TAUNT"
                ModifierKind.REVIVE    -> s.codeName == "REVIVE"
                ModifierKind.BLOCK     -> s.codeName == "BLOCK"
            }
            if (keep) sum += s.primarySigned
        }
        return sum
    }

    /**
     * R91 — engine skill 한국어 이름으로 catalog 를 fuzzy 매칭한 뒤 [primaryModifier] 결과를 돌려준다.
     * 매칭 hits 가 여러 개면 rank 가 가장 높은 1개 사용 (SkillScene 의 catalogLine 과 동일 규칙).
     * 매칭 없음 / catalog 미설치 등은 0.
     */
    fun primaryModifierForEngineName(nameKo: String, kind: ModifierKind): Int {
        val hits = lookupByName(nameKo)
        if (hits.isEmpty()) return 0
        val best = hits.maxByOrNull { it.skill.effectV2?.rank ?: 0 } ?: hits[0]
        return primaryModifier(best.skill, kind)
    }

    /**
     * R94 — engine skill 의 한국어 이름으로 catalog 를 fuzzy 매칭한 뒤, 가장 rank 높은 hit 의
     * `effectV2.nDebuffs` 를 반환. 매칭 없음 / effectV2=null = 0. BattleScene 이 0 초과 시
     * 적에게 [com.hero3.remake.engine.Status] 를 부여하는 신호로 사용.
     */
    fun debuffCountForEngineName(nameKo: String): Int {
        val hits = lookupByName(nameKo)
        if (hits.isEmpty()) return 0
        val best = hits.maxByOrNull { it.skill.effectV2?.rank ?: 0 } ?: hits[0]
        return best.skill.effectV2?.nDebuffs ?: 0
    }

    /** [Hero3Skill] 의 effectV2 가 있고 첫 슬롯이 sentinel/zero 가 아니면 한 줄 요약 — 디버그/UI 용. */
    fun effectSummary(skill: Hero3Skill): String? {
        val ev = skill.effectV2 ?: return null
        val live = listOfNotNull(ev.slot1, ev.slot2, ev.slot3)
            .filterNot { it.isSentinel || it.isZero }
        if (live.isEmpty()) return "rank=${ev.rank} (no live slot)"
        val parts = live.joinToString(" | ") { s ->
            val sign = if (s.primarySigned >= 0) "+" else ""
            "${s.codeName}${sign}${s.primarySigned}/${s.secondarySigned}"
        }
        val deb = if (ev.nDebuffs > 0) "  deb=${ev.nDebuffs}" else ""
        return "rank=${ev.rank}$deb  $parts"
    }

    companion object {
        /** [Hero3Catalog.skills] 의 모든 weapon set × skills 를 평탄화해서 인덱스 빌드. */
        fun build(catalog: Hero3Catalog): Hero3CatalogSkillIndex {
            val flat = catalog.skills.flatMap { ws ->
                ws.skills.map { sk -> Entry(ws.file, ws.weapon, sk) }
            }
            val byWeapon = flat.groupBy { it.weapon }
            val byFile = flat.groupBy { it.file }
            return Hero3CatalogSkillIndex(flat, byWeapon, byFile)
        }

        /**
         * R89 — sX_dat 7종을 정렬 순서대로 매핑할 ARGB 팔레트.
         * R88 quest 팔레트와 색상 충돌 없는 hue spread.
         *   s4 창   = sky blue
         *   s5 검   = warm orange
         *   s6 단검 = mint
         *   s7 건   = magenta
         *   s8 라이플 = gold
         *   s9 홀리석 = ivory
         *   s10 다크석 = violet
         */
        val FILE_PALETTE: IntArray = intArrayOf(
            0xFF89C7FF.toInt(),  // sky blue
            0xFFFFB068.toInt(),  // warm orange
            0xFF7CE0B0.toInt(),  // mint
            0xFFFF8FD8.toInt(),  // magenta
            0xFFFFE066.toInt(),  // gold
            0xFFEFE5C2.toInt(),  // ivory
            0xFFB89CFF.toInt(),  // violet
        )

        private fun fallbackHashColor(file: String): Int {
            var h = 0
            for (c in file) h = (h * 31 + c.code) and 0x00FFFFFF
            val r = 0x80 or (h shr 16 and 0x7F)
            val g = 0x80 or (h shr 8 and 0x7F)
            val b = 0x80 or (h and 0x7F)
            return (0xFF shl 24) or (r shl 16) or (g shl 8) or b
        }
    }
}
