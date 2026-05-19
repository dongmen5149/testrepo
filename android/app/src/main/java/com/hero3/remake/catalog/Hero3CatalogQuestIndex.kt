package com.hero3.remake.catalog

/**
 * R85 — Catalog quest 인덱스.
 *
 * R84 에서 [Hero3Catalog.questFiles] 로 노출된 catalog quest entries
 * (quest_00/01/10/11_dat) 를 한국어 이름 기준으로 빠르게 찾을 수 있게 한다.
 *
 * 용도:
 *  - QuestRegistry 의 캐논 한국어 이름 매칭 (engine-core 의 4 quest → catalog 의 67+ entries).
 *  - CatalogViewerScene Quests tab 에서 중복/매칭 표시.
 *  - 향후 NPC dialogue 의 한국어 키워드 → quest entry 역인덱스.
 *
 * 정규화 규칙:
 *  - 트림 + 내부 공백 1개로 압축
 *  - 끝에 붙은 1자리 숫자 ("증명1") 는 캐논 키에서 제거 (시퀀스 표기 흡수)
 *  - 그 외 한글/한자/숫자/영문은 모두 보존
 */
class Hero3CatalogQuestIndex(
    val entries: List<Hero3CatalogQuestEntry>,
    val byCanonicalName: Map<String, List<Hero3CatalogQuestEntry>>,
    val byFile: Map<String, List<Hero3CatalogQuestEntry>>,
) {
    val size: Int get() = entries.size
    val distinctCanonicalNames: Int get() = byCanonicalName.size
    val fileCount: Int get() = byFile.size

    /** 이름이 정확히 일치하는 entry (없으면 빈 리스트). */
    fun lookupExact(rawName: String): List<Hero3CatalogQuestEntry> =
        byCanonicalName[canonicalize(rawName)].orEmpty()

    /** 부분 일치 검색 (한국어 token 포함). */
    fun lookupContains(fragment: String): List<Hero3CatalogQuestEntry> {
        val needle = fragment.trim()
        if (needle.isEmpty()) return emptyList()
        return entries.filter { it.name.contains(needle) }
    }

    /** [Hero3CatalogQuestEntry] 가 이 인덱스에 속하는지 확인. */
    operator fun contains(entry: Hero3CatalogQuestEntry): Boolean =
        entries.any { it.file == entry.file && it.pos == entry.pos }

    /** 동일 캐논 이름이 2회 이상 나타난 케이스 (예: "혼돈의 대륙" quest_01/quest_11 양쪽). */
    fun duplicates(): Map<String, List<Hero3CatalogQuestEntry>> =
        byCanonicalName.filterValues { it.size > 1 }

    /**
     * R88 — quest_*_dat 파일별 안정적인 ARGB 색상 hint.
     *
     * `quest_00_dat / quest_01_dat / quest_10_dat / quest_11_dat` 처럼
     * 일정 패턴의 파일명을 등장 순서대로 [FILE_PALETTE] 의 색상에 매핑한다.
     * 미지의 파일명은 이름 hash 로 fallback 한다.
     *
     * 반환값은 android `Color.argb(...)` 와 같은 32-bit ARGB. Scene 코드는
     * `Paint().apply { color = ... }` 에 그대로 쓸 수 있다.
     */
    fun colorOf(file: String): Int {
        val sortedFiles = byFile.keys.sorted()
        val idx = sortedFiles.indexOf(file)
        return if (idx >= 0) FILE_PALETTE[idx % FILE_PALETTE.size]
        else fallbackHashColor(file)
    }

    /** 파일명 → 색상 일괄 매핑 (UI 가 한번에 캐싱하기 좋은 형태). */
    fun fileColors(): Map<String, Int> =
        byFile.keys.sorted().withIndex().associate { (i, f) ->
            f to FILE_PALETTE[i % FILE_PALETTE.size]
        }

    companion object {
        /** [Hero3Catalog.questFiles] 의 모든 entries 를 평탄화해서 인덱스 빌드. */
        fun build(catalog: Hero3Catalog): Hero3CatalogQuestIndex {
            val flat = catalog.questFiles.flatMap { it.entries }
            val byName = flat.groupBy { canonicalize(it.name) }
            val byFile = flat.groupBy { it.file }
            return Hero3CatalogQuestIndex(flat, byName, byFile)
        }

        /**
         * 캐논 이름 — 정규화. trim + 공백 압축 + 꼬리 1자리 숫자 제거.
         *
         * Public — 같은 규칙으로 외부에서도 매칭 키를 만들 수 있게 노출.
         */
        fun canonicalize(name: String): String {
            val collapsed = name.trim().replace(Regex("\\s+"), " ")
            return collapsed.replace(Regex("\\d$"), "")
        }

        /**
         * R88 — quest_*_dat 4종에 대응하는 ARGB 색상 팔레트.
         * 어둠 배경 (CatalogViewerScene bg ≈ rgb(10,14,28)) 위에서 읽힐 정도로
         * 채도/명도를 충분히 높게 잡았다.
         *  - quest_00_dat = warm amber (메인 라인)
         *  - quest_01_dat = teal (서브 라인)
         *  - quest_10_dat = lavender (하드 메인)
         *  - quest_11_dat = soft red (하드 서브)
         */
        val FILE_PALETTE: IntArray = intArrayOf(
            0xFFFFD062.toInt(),  // amber
            0xFF8DE4D7.toInt(),  // teal
            0xFFC8B6FF.toInt(),  // lavender
            0xFFFF9E9E.toInt(),  // soft red
            0xFF9FE08F.toInt(),  // green (예비)
            0xFFFFB4F0.toInt(),  // pink  (예비)
        )

        private fun fallbackHashColor(file: String): Int {
            var h = 0
            for (c in file) h = (h * 31 + c.code) and 0x00FFFFFF
            // 명도 보정: 모든 채널 0x80 이상 유지
            val r = 0x80 or (h shr 16 and 0x7F)
            val g = 0x80 or (h shr 8 and 0x7F)
            val b = 0x80 or (h and 0x7F)
            return (0xFF shl 24) or (r shl 16) or (g shl 8) or b
        }
    }
}
