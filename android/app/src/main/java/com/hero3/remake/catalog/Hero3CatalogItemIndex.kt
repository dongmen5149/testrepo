package com.hero3.remake.catalog

/**
 * R92 — Catalog item 인덱스 (Quest/Skill 인덱스 패턴 3번째 적용).
 *
 * [Hero3Catalog.items] 의 18 categories (i0..i18_dat, gap 있음) 와 그 안의 ~529 items 를
 * 평탄화 / 파일·카테고리 그룹화 / 색상 hint 와 함께 조회할 수 있게 한다.
 *
 * R85 [Hero3CatalogQuestIndex] / R89 [Hero3CatalogSkillIndex] 의 자매 API. 같은 패턴:
 *  - entries        : 평탄화된 (item, owning category) pairs
 *  - byCategory     : category 라벨 기준 group
 *  - byFile         : iN_dat 기준 group
 *  - colorOf(file)  : 파일별 안정적 ARGB 색
 *  - fileColors()   : 일괄 매핑 (UI 캐싱용)
 *
 * 18 카테고리는 10-슬롯 팔레트 + hash fallback 으로 매핑 — 정렬 슬롯 0..9 는 distinct,
 * 10번째부터는 fallback 색 (각 채널 ≥ 0x80 보장, 어두운 배경에서 가독성 OK).
 *
 * R71 의 18 item categories (참고):
 *    i0..i3 = ARMOR (모자/상의/하의/장갑), i4..i10 = WEAPON (창/검/단검/권총/라이플/홀리/다크),
 *    i12..i13 = ACCESSORY (반지/귀걸이/목걸이), i14 = MATERIAL, i15 = high-tier catalog (R76),
 *    i17 = ACCESSORY (브로치/스톤), i18 = CONSUMABLE.
 */
class Hero3CatalogItemIndex(
    val entries: List<Entry>,
    val byCategory: Map<String, List<Entry>>,
    val byFile: Map<String, List<Entry>>,
) {
    /** category + item 을 묶은 view. */
    data class Entry(
        val file: String,
        val category: String,
        val item: Hero3Item,
    )

    val size: Int get() = entries.size
    val fileCount: Int get() = byFile.size
    val categoryCount: Int get() = byCategory.size

    /** category 라벨이 [fragment] 를 포함하는 entries. */
    fun lookupByCategory(fragment: String): List<Entry> {
        val needle = fragment.trim()
        if (needle.isEmpty()) return emptyList()
        return entries.filter { it.category.contains(needle) }
    }

    /** item 의 `name` 또는 `cleanName` 이 [fragment] 를 포함하는 entries. */
    fun lookupByName(fragment: String): List<Entry> {
        val needle = fragment.trim()
        if (needle.isEmpty()) return emptyList()
        return entries.filter { it.item.name.contains(needle) || it.item.cleanName.contains(needle) }
    }

    /**
     * R88 [Hero3CatalogQuestIndex.colorOf] / R89 [Hero3CatalogSkillIndex.colorOf] 와 같은 규칙.
     * 정렬된 파일명 → palette slot[0..9]. 10번째부터는 hash fallback (각 채널 ≥ 0x80).
     */
    fun colorOf(file: String): Int {
        val sortedFiles = byFile.keys.sorted()
        val idx = sortedFiles.indexOf(file)
        return if (idx in 0 until FILE_PALETTE.size) FILE_PALETTE[idx]
        else fallbackHashColor(file)
    }

    /** 파일명 → 색상 (UI 캐싱용 일괄 매핑). 슬롯 부족 분은 hash fallback 사용. */
    fun fileColors(): Map<String, Int> =
        byFile.keys.sorted().withIndex().associate { (i, f) ->
            f to (if (i in 0 until FILE_PALETTE.size) FILE_PALETTE[i] else fallbackHashColor(f))
        }

    companion object {
        /** [Hero3Catalog.items] 의 모든 category × items 를 평탄화해서 인덱스 빌드. */
        fun build(catalog: Hero3Catalog): Hero3CatalogItemIndex {
            val flat = catalog.items.flatMap { c ->
                c.items.map { it -> Entry(c.file, c.category, it) }
            }
            val byCategory = flat.groupBy { it.category }
            val byFile = flat.groupBy { it.file }
            return Hero3CatalogItemIndex(flat, byCategory, byFile)
        }

        /**
         * R92 — 10-슬롯 ARGB 팔레트. R88 quest (4 색) / R89 skill (7 색) 과 hue 충돌 없는 분포.
         * 18 카테고리이지만 10 슬롯만 distinct, 11번째부터 hash fallback (각 채널 ≥ 0x80) 사용.
         *   slot[0] coral / [1] amber / [2] yellow / [3] lime / [4] aqua / [5] cyan
         *   slot[6] periwinkle / [7] orchid / [8] rose / [9] sand
         */
        val FILE_PALETTE: IntArray = intArrayOf(
            0xFFFF8A80.toInt(),  // coral
            0xFFFFB74D.toInt(),  // amber
            0xFFFFE082.toInt(),  // yellow
            0xFFC0CA33.toInt(),  // lime
            0xFF80DEEA.toInt(),  // aqua
            0xFF4DD0E1.toInt(),  // cyan
            0xFFA7B5FF.toInt(),  // periwinkle
            0xFFE091F8.toInt(),  // orchid
            0xFFFF94B2.toInt(),  // rose
            0xFFE6C99B.toInt(),  // sand
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
