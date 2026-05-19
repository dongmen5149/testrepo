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
) {
    val size: Int get() = entries.size
    val distinctCanonicalNames: Int get() = byCanonicalName.size

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

    companion object {
        /** [Hero3Catalog.questFiles] 의 모든 entries 를 평탄화해서 인덱스 빌드. */
        fun build(catalog: Hero3Catalog): Hero3CatalogQuestIndex {
            val flat = catalog.questFiles.flatMap { it.entries }
            val by = flat.groupBy { canonicalize(it.name) }
            return Hero3CatalogQuestIndex(flat, by)
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
    }
}
