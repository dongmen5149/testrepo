package com.hero4.remake.catalog

import com.hero3.remake.engine.AssetReader
import org.json.JSONArray
import org.json.JSONObject

/**
 * Hero4 게임 데이터 catalog (R69 산출물 `h4_catalog.json` 로더).
 *
 * 입력: `assets/h4_catalog.json` (28KB, R69 build_h4_catalog.py 산출)
 * 출력: heroes / skill_sets / items / npc 4 도메인 객체
 *
 * Phase C Step 5 의 proof-of-concept — engine-core 의 NpcRegistry/SkillRegistry 와 동일
 * 패턴이지만 Hero4 전용 데이터. 향후 engine-core 의 추상화 inteface 로 통합.
 */
data class Hero4Hero(
    val name: String,
    val classSuggested: String,
    val skillSet: String,
    val note: String,
)

data class Hero4Skill(
    val name: String,
    val offsetHex: String,
)

data class Hero4SkillSet(
    val file: String,
    val skillCount: Int,
    val skills: List<Hero4Skill>,
)

data class Hero4ItemFile(
    val file: String,
    val size: Int,
    val koreanCount: Int,
    val uniqueNames: List<String>,
)

data class Hero4NpcFile(
    val file: String,
    val size: Int,
    val koreanCount: Int,
    val samples: List<String>,
)

data class Hero4Quest(
    val sourceFile: String,
    val name: String,
    val description: String,
    val category: String,
)

data class Hero4Catalog(
    val meta: Map<String, Any>,
    val heroes: List<Hero4Hero>,
    val skillSets: List<Hero4SkillSet>,
    val items: List<Hero4ItemFile>,
    val npc: List<Hero4NpcFile>,
    val quests: List<Hero4Quest>,
) {
    val totalSkills: Int get() = skillSets.sumOf { it.skillCount }
    val totalItemKorean: Int get() = items.sumOf { it.koreanCount }
    val totalNpcKorean: Int get() = npc.sumOf { it.koreanCount }
    val mainStoryQuests: Int get() = quests.count { it.category == "메인퀘스트" }
}

object Hero4CatalogLoader {

    /** [reader] 를 통해 `h4_catalog.json` 을 파싱하여 Hero4Catalog 반환.
     *  Phase C Step 4c (2026-05-19) — Context 직접 의존을 platform-agnostic AssetReader 로 전환. */
    fun load(reader: AssetReader): Hero4Catalog {
        val raw = reader.readText("h4_catalog.json")
        val root = JSONObject(raw)

        // meta
        val meta = root.optJSONObject("meta")?.toStringMap() ?: emptyMap()

        // heroes
        val heroes = mutableListOf<Hero4Hero>()
        root.optJSONObject("heroes")?.optJSONArray("list")?.let { arr ->
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                heroes += Hero4Hero(
                    name = o.optString("name"),
                    classSuggested = o.optString("class_suggested"),
                    skillSet = o.optString("skill_set"),
                    note = o.optString("note"),
                )
            }
        }

        // skill_sets
        val skillSets = mutableListOf<Hero4SkillSet>()
        root.optJSONArray("skill_sets")?.let { arr ->
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                val skills = mutableListOf<Hero4Skill>()
                o.optJSONArray("skills")?.let { sArr ->
                    for (j in 0 until sArr.length()) {
                        val s = sArr.getJSONObject(j)
                        skills += Hero4Skill(
                            name = s.optString("name"),
                            offsetHex = s.optString("offset"),
                        )
                    }
                }
                skillSets += Hero4SkillSet(
                    file = o.optString("file"),
                    skillCount = o.optInt("skill_count"),
                    skills = skills,
                )
            }
        }

        // items
        val items = mutableListOf<Hero4ItemFile>()
        root.optJSONArray("items")?.let { arr ->
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                items += Hero4ItemFile(
                    file = o.optString("file"),
                    size = o.optInt("size"),
                    koreanCount = o.optInt("korean_count"),
                    uniqueNames = o.optJSONArray("unique_names")?.toStringList() ?: emptyList(),
                )
            }
        }

        // npc
        val npc = mutableListOf<Hero4NpcFile>()
        root.optJSONArray("npc")?.let { arr ->
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                npc += Hero4NpcFile(
                    file = o.optString("file"),
                    size = o.optInt("size"),
                    koreanCount = o.optInt("korean_count"),
                    samples = o.optJSONArray("samples")?.toStringList() ?: emptyList(),
                )
            }
        }

        // quests (R70)
        val quests = mutableListOf<Hero4Quest>()
        root.optJSONArray("quests")?.let { arr ->
            for (i in 0 until arr.length()) {
                val o = arr.getJSONObject(i)
                quests += Hero4Quest(
                    sourceFile = o.optString("source_file"),
                    name = o.optString("name"),
                    description = o.optString("description"),
                    category = o.optString("category"),
                )
            }
        }

        return Hero4Catalog(meta, heroes, skillSets, items, npc, quests)
    }

    private fun JSONObject.toStringMap(): Map<String, Any> {
        val out = mutableMapOf<String, Any>()
        val keys = keys()
        while (keys.hasNext()) {
            val k = keys.next()
            out[k] = get(k)
        }
        return out
    }

    private fun JSONArray.toStringList(): List<String> =
        (0 until length()).map { optString(it) }
}
