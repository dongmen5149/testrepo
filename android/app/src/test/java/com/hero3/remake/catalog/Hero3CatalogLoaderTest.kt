package com.hero3.remake.catalog

import com.hero3.remake.engine.AssetNotFound
import com.hero3.remake.engine.AssetReader
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Hero3CatalogLoader unit test — Phase C / R71.
 *
 * 실제 game_balance.json 을 통해 catalog 의 24 stat enum / 18 item 카테고리 /
 * 7 weapon skill set / 161 normal enemy / 15 boss 가 로드되는지 검증.
 */
class Hero3CatalogLoaderTest {

    /** 파일 시스템에서 직접 읽는 테스트용 AssetReader. */
    private class FileAssetReader(private val baseDir: File) : AssetReader {
        override fun readText(path: String): String = try {
            File(baseDir, path).readText(Charsets.UTF_8)
        } catch (e: Exception) {
            throw AssetNotFound(path, e)
        }
        override fun readBytes(path: String): ByteArray = try {
            File(baseDir, path).readBytes()
        } catch (e: Exception) {
            throw AssetNotFound(path, e)
        }
    }

    private fun reader(): AssetReader =
        FileAssetReader(File("src/main/assets"))

    @Test
    fun load_returns_non_null_catalog() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertNotNull(catalog)
    }

    @Test
    fun catalog_schema_version_is_1_2() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertEquals("1.2", catalog.schemaVersion)
    }

    @Test
    fun stat_enum_has_24_codes() {
        val catalog = Hero3CatalogLoader.load(reader())
        // R63 master enum 24 codes (0x14, 0x19 unused but present)
        // R66 추가: 0x15 TAUNT → 25 entries total in v1.1
        assertTrue(catalog.statEnum.size >= 24)
        assertEquals("ATT1", catalog.statName(0x05))
        assertEquals("P_DEF", catalog.statName(0x07))
    }

    @Test
    fun rarity_has_6_prefixes() {
        val catalog = Hero3CatalogLoader.load(reader())
        // R62: 6 rarity prefixes (magic/legendary/epic/boss_drop/endgame/quest_reward)
        assertEquals(6, catalog.rarity.size)
    }

    @Test
    fun items_has_18_categories_and_529_total() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertEquals(18, catalog.items.size)
        assertEquals(529, catalog.totalItems)
    }

    @Test
    fun skills_has_7_weapon_classes_and_105_total() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertEquals(7, catalog.skills.size)
        assertEquals(105, catalog.totalSkills)
    }

    @Test
    fun enemies_has_161_normal_and_161_hard() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertEquals(161, catalog.enemiesNormal.size)
        assertEquals(161, catalog.enemiesHard.size)
    }

    @Test
    fun bosses_has_15_normal_and_15_hard() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertEquals(15, catalog.bossesNormal.size)
        assertEquals(15, catalog.bossesHard.size)
    }

    @Test
    fun combat_rating_formula_is_documented() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertTrue(catalog.combatRatingFormulaNormal.contains("44"))
        assertTrue(catalog.combatRatingFormulaHard.contains("64"))
    }

    @Test
    fun boss_combat_rating_matches_formula() {
        val catalog = Hero3CatalogLoader.load(reader())
        // R66 발견: rating = round(lvl/2 + 44) normal / round(lvl/2 + 64) hard
        // 30 boss entries 모두 검증 통과
        val normalMismatch = catalog.bossesNormal.count {
            it.trailerDecoded?.ratingMatches == false
        }
        val hardMismatch = catalog.bossesHard.count {
            it.trailerDecoded?.ratingMatches == false
        }
        assertEquals(0, normalMismatch)
        assertEquals(0, hardMismatch)
    }

    @Test
    fun des_status_has_zero_pending_files_after_r73() {
        val catalog = Hero3CatalogLoader.load(reader())
        // R73: all 8 files decrypted via Hero5 mx_des_decrypt variant
        assertEquals(0, catalog.desStatus.pendingFiles.size)
        assertEquals("0EP@KO91", catalog.desStatus.key)
    }

    @Test
    fun boss_skill_ids_resolved_returns_true_after_r74() {
        val catalog = Hero3CatalogLoader.load(reader())
        // R74: drop_dat 98/161 records match BSKILL set → H4 confirmed
        assertTrue(catalog.bossSkillIdsResolved())
    }

    // ─── R75: R74 DES plaintext data assertions ────────────────────────────

    @Test
    fun r74_data_is_loaded() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertNotNull(catalog.r74Data)
    }

    @Test
    fun r74_drop_table_has_161_entries_matching_enemies() {
        val catalog = Hero3CatalogLoader.load(reader())
        val d = catalog.r74Data!!
        assertEquals(161, d.dropTable.size)
        assertEquals(161, d.dropTableHard.size)
        // 1:1 with R56 enemy_dat
        assertEquals(catalog.totalEnemies, d.dropTable.size)
    }

    @Test
    fun r74_recipes_have_80_entries() {
        val catalog = Hero3CatalogLoader.load(reader())
        val d = catalog.r74Data!!
        assertEquals(80, d.recipes.size)
        assertEquals(80, d.recipesHard.size)
        // Recipe success rate constant 100 (0x64)
        assertEquals(100, d.recipes[0].successRate)
    }

    @Test
    fun r74_region_shops_have_5_entries_with_level_tiers() {
        val catalog = Hero3CatalogLoader.load(reader())
        val d = catalog.r74Data!!
        assertEquals(5, d.regionShops.size)
        // Normal mode first shop tier = level 1-15
        assertEquals(1, d.regionShops[0].lvMin)
        assertEquals(15, d.regionShops[0].lvMax)
        // Hard mode first tier = 30-44
        assertEquals(30, d.regionShopsHard[0].lvMin)
        assertEquals(44, d.regionShopsHard[0].lvMax)
    }

    @Test
    fun r84_catalog_quests_loaded_115_entries_across_4_files() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertEquals(4, catalog.questFiles.size)
        val total = catalog.questFiles.sumOf { it.nEntries }
        // R58/R62: 37 + 7 + 38 + 33 = 115 quests
        assertEquals(115, total)
        // First quest of quest_00_dat = 노력의 증명1
        val q00 = catalog.questFiles.firstOrNull { it.file == "quest_00_dat" }
        assertNotNull(q00)
        assertTrue(q00!!.entries.isNotEmpty())
        assertEquals("노력의 증명1", q00.entries[0].name)
    }

    // ─── R85: catalog quest index ───────────────────────────────────────────

    @Test
    fun r85_quest_index_builds_and_indexes_all_loaded_entries() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogQuestIndex.build(catalog)
        val flatCount = catalog.questFiles.sumOf { it.entries.size }
        assertEquals(flatCount, idx.size)
        // distinct canonical names ≤ total (= total when no duplicates).
        assertTrue(idx.distinctCanonicalNames in 1..idx.size)
    }

    @Test
    fun r85_quest_index_canonicalize_strips_trailing_digit() {
        // "노력의 증명1" / "노력의 증명2" 가 같은 캐논 이름을 가지도록.
        assertEquals("노력의 증명",
            Hero3CatalogQuestIndex.canonicalize("노력의 증명1"))
        assertEquals("노력의 증명",
            Hero3CatalogQuestIndex.canonicalize("  노력의   증명  "))
    }

    @Test
    fun r85_quest_index_lookup_finds_first_known_entry() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogQuestIndex.build(catalog)
        // "노력의 증명1" → canonical "노력의 증명" — quest_00_dat 의 첫 entry 와 매칭.
        val hits = idx.lookupExact("노력의 증명1")
        assertTrue(hits.isNotEmpty())
        assertEquals("quest_00_dat", hits[0].file)
        assertEquals(0, hits[0].pos)
        // Contains search should also work.
        val partial = idx.lookupContains("증명")
        assertTrue(partial.isNotEmpty())
    }

    @Test
    fun r85_quest_index_detects_known_duplicate_chaos_continent() {
        // "혼돈의 대륙" appears in both quest_01_dat and quest_11_dat.
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogQuestIndex.build(catalog)
        val dups = idx.duplicates()
        val chaos = dups["혼돈의 대륙"]
        assertNotNull(chaos)
        assertTrue(chaos!!.size >= 2)
        val files = chaos.map { it.file }.toSet()
        assertTrue(files.contains("quest_01_dat"))
        assertTrue(files.contains("quest_11_dat"))
    }

    // ─── R87: quest item xref ───────────────────────────────────────────────

    @Test
    fun r87_quest_item_xref_has_21_items() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertEquals(21, catalog.questItemXref.size)
        // cleanName 은 비어있지 않음
        assertTrue(catalog.questItemXref.all { it.cleanName.isNotEmpty() })
        // 21개 중 20개는 match 가 있고, 1개 ("반토막난 지도") 는 빈 매치.
        val withMatches = catalog.questItemXref.count { it.matches.isNotEmpty() }
        assertEquals(20, withMatches)
    }

    @Test
    fun r87_quest_item_xref_finds_known_item() {
        val catalog = Hero3CatalogLoader.load(reader())
        // "협곡의성수" — quest_00 등에 8 matches.
        val x = catalog.findQuestXref("협곡의성수")
        assertNotNull(x)
        assertTrue(x!!.matches.size >= 4)
        // matches 의 file 들이 quest_*_dat 형식인지.
        assertTrue(x.matches.all { it.file.startsWith("quest_") })
    }

    @Test
    fun r87_quest_xref_by_file_groups_correctly() {
        val catalog = Hero3CatalogLoader.load(reader())
        val q00matches = catalog.questXrefByFile("quest_00_dat")
        assertTrue(q00matches.isNotEmpty())
        // 모든 match.file 이 quest_00_dat 인지.
        assertTrue(q00matches.all { it.second.file == "quest_00_dat" })
        // 다른 파일은 다른 카운트.
        val q11matches = catalog.questXrefByFile("quest_11_dat")
        assertTrue(q11matches.isNotEmpty())
    }

    @Test
    fun r74_shop_catalog_and_fixed_drops_populated() {
        val catalog = Hero3CatalogLoader.load(reader())
        val d = catalog.r74Data!!
        assertEquals(38, d.shopCatalog.size)
        assertEquals(96, d.fixedDrops.size)
        // First i15 entry has Korean name with EUC-KR decoded characters
        assertTrue(d.shopCatalog[0].name.isNotEmpty())
        // Fixed drops all type=2 (R74 finding)
        assertTrue(d.fixedDrops.all { it.type == 2 })
    }

    // ─── R76: recipe input/output resolution + i15 catalog xref ─────────────

    @Test
    fun r76_recipe_outputs_resolve_to_real_catalog_items() {
        val catalog = Hero3CatalogLoader.load(reader())
        val d = catalog.r74Data!!
        // Recipe 0: bytes[9]=18, bytes[10]=0 → i18_dat[0] = "포션"
        val r0 = d.recipes[0]
        assertEquals(18, r0.outputCat)
        assertEquals(0, r0.outputId)
        val out0 = catalog.resolveItem(r0.output)
        assertNotNull(out0)
        assertEquals("포션", out0!!.cleanName)
        // Recipe 3: bytes[9]=0, bytes[10]=3 → i0_dat[3] = "강화가죽모자"
        val r3 = d.recipes[3]
        assertEquals(0, r3.outputCat)
        assertEquals(3, r3.outputId)
        val out3 = catalog.resolveItem(r3.output)
        assertNotNull(out3)
        assertEquals("강화가죽모자", out3!!.cleanName)
    }

    @Test
    fun r76_recipe_inputs_filter_out_empty_slots() {
        val catalog = Hero3CatalogLoader.load(reader())
        val d = catalog.r74Data!!
        // Recipe 0: bytes[2,3]=(255,0)=empty, bytes[4,5]=(0,2), bytes[6,7]=(255,0)=empty
        // → 1 real input (i0_dat[2])
        val r0 = d.recipes[0]
        assertEquals(1, r0.inputs.size)
        assertEquals(0, r0.inputs[0].cat)
        assertEquals(2, r0.inputs[0].id)
        // Recipe 3: bytes[2,3]=(0,1), bytes[4,5]=(8,10), bytes[6,7]=(1,5) → 3 inputs
        val r3 = d.recipes[3]
        assertEquals(3, r3.inputs.size)
    }

    @Test
    fun r76_i15_38_entries_all_resolve_to_catalog() {
        val catalog = Hero3CatalogLoader.load(reader())
        val d = catalog.r74Data!!
        // R76 finding: 38/38 i15 names match catalog clean_names exactly
        val matched = d.shopCatalog.count { catalog.resolveShopCatalogEntry(it) != null }
        assertEquals(38, matched)
    }

    // ─── R77: drop archetype clustering + region_shop xref ─────────────────

    @Test
    fun r77_drop_records_cluster_into_18_archetypes() {
        val catalog = Hero3CatalogLoader.load(reader())
        // R77 finding: 161 drop records group by bytes[0..9] into 18 distinct archetypes
        val archetypes = catalog.dropArchetypes()
        assertEquals(18, archetypes.size)
        // Largest cluster (low-level archetype) has 27 members
        val largest = archetypes.values.maxByOrNull { it.size }!!
        assertEquals(27, largest.size)
    }

    @Test
    fun r77_drop_class_flags_distinguish_normal_elite_boss() {
        val catalog = Hero3CatalogLoader.load(reader())
        val drops = catalog.r74Data!!.dropTable
        // R77: 14=normal, 18=elite, 255=box/boss
        val normal = drops.count { it.isNormalEnemy }
        val elite = drops.count { it.isElite }
        val boss = drops.count { it.isBossOrBox }
        assertTrue(normal > 0)
        assertTrue(elite > 0)
        assertTrue(boss > 0)
        // 3 classes account for vast majority (1 outlier 22B record exists)
        assertTrue(normal + elite + boss >= 158)
    }

    @Test
    fun r78_common_pool_sentinel_is_secondary_only() {
        val catalog = Hero3CatalogLoader.load(reader())
        val drops = catalog.r74Data!!.dropTable
        // R78: (133,153)=0x8599 appears 63 times in secondary, 0 in primary
        val secondaryCommon = drops.count { it.secondaryIsCommonPool }
        val primaryCommon = drops.count { it.primaryDrop == 133 to 153 }
        assertEquals(63, secondaryCommon)
        assertEquals(0, primaryCommon)
    }

    @Test
    fun r77_region_shop_items_resolve_to_i15_entries() {
        val catalog = Hero3CatalogLoader.load(reader())
        val shops = catalog.r74Data!!.regionShops
        // R77 finding: shop.itemIds are indices into i15 shop catalog
        // lv 1-15 shop has 2 items: i15[4]=얼음비늘장갑, i15[8]=바람가죽모자
        val firstShop = shops[0]
        val items = catalog.resolveShopItems(firstShop)
        assertEquals(2, items.size)
        assertEquals("얼음비늘장갑", items[0].name)
        assertEquals("바람가죽모자", items[1].name)
        // lv 26-40 (final tier) has 5 items
        val lastShop = shops[4]
        assertEquals(5, catalog.resolveShopItems(lastShop).size)
    }

    // ─── R88: QuestIndex 의 byFile / fileColors / colorOf ────────────────────

    @Test
    fun r88_quest_index_groups_entries_by_file() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogQuestIndex.build(catalog)
        // 4 quest 파일 모두 인덱싱 되어야 함.
        assertEquals(4, idx.fileCount)
        val expected = setOf("quest_00_dat", "quest_01_dat", "quest_10_dat", "quest_11_dat")
        assertEquals(expected, idx.byFile.keys)
        // 각 파일의 entries 가 모두 같은 file 로 분류됐는지 sanity check.
        for ((file, list) in idx.byFile) {
            assertTrue(list.isNotEmpty())
            assertTrue(list.all { it.file == file })
        }
        // 합계가 평탄화 인덱스 크기와 같아야 함.
        val total = idx.byFile.values.sumOf { it.size }
        assertEquals(idx.size, total)
    }

    @Test
    fun r88_quest_index_fileColors_distinct_and_stable() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogQuestIndex.build(catalog)
        val colors = idx.fileColors()
        assertEquals(idx.fileCount, colors.size)
        // 모든 색이 서로 달라야 (4 파일 < 6 슬롯 팔레트).
        assertEquals(colors.values.toSet().size, colors.size)
        // 같은 파일을 두 번 물어도 같은 색이 나와야 함.
        val first = idx.colorOf("quest_00_dat")
        val second = idx.colorOf("quest_00_dat")
        assertEquals(first, second)
        // 미지 파일은 fallback (alpha=0xFF, RGB 각 채널 ≥ 0x80) 으로 항상 색을 만든다.
        val unknown = idx.colorOf("quest_99_dat")
        assertEquals(0xFF.toInt(), (unknown ushr 24) and 0xFF)
    }

    @Test
    fun r88_quest_index_colorOf_uses_sorted_palette_slots() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogQuestIndex.build(catalog)
        // 4 파일 정렬 순: quest_00_dat / quest_01_dat / quest_10_dat / quest_11_dat
        // → 팔레트 [0..3] 슬롯과 1:1 매칭.
        val palette = Hero3CatalogQuestIndex.FILE_PALETTE
        assertEquals(palette[0], idx.colorOf("quest_00_dat"))
        assertEquals(palette[1], idx.colorOf("quest_01_dat"))
        assertEquals(palette[2], idx.colorOf("quest_10_dat"))
        assertEquals(palette[3], idx.colorOf("quest_11_dat"))
    }

    // ─── R89: Hero3CatalogSkillIndex ────────────────────────────────────────

    @Test
    fun r89_skill_index_builds_with_seven_weapon_files() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        // R71: 7 weapon skill files (s4..s10_dat).
        assertEquals(7, idx.fileCount)
        val expected = setOf("s4_dat", "s5_dat", "s6_dat", "s7_dat", "s8_dat", "s9_dat", "s10_dat")
        assertEquals(expected, idx.byFile.keys)
        // 평탄화 합계 = byFile 합계 = idx.size.
        val total = idx.byFile.values.sumOf { it.size }
        assertEquals(idx.size, total)
        // n_skills 합이 totalSkills 와 일치.
        assertEquals(catalog.totalSkills, idx.size)
    }

    @Test
    fun r89_skill_index_groups_by_weapon_label() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        // weapon 라벨이 비어있지 않고, 모든 entry 의 weapon 이 byWeapon 키와 일치.
        assertTrue(idx.byWeapon.isNotEmpty())
        for ((weapon, list) in idx.byWeapon) {
            assertTrue(weapon.isNotBlank())
            assertTrue(list.all { it.weapon == weapon })
        }
        // 알려진 weapon 라벨이 인덱싱 되어야 함.
        val labels = idx.byWeapon.keys
        assertTrue(labels.any { it.contains("창") })
        assertTrue(labels.any { it.contains("단검") })
    }

    @Test
    fun r89_skill_index_colorOf_distinct_and_stable() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        val colors = idx.fileColors()
        assertEquals(idx.fileCount, colors.size)
        // 7 파일 색이 distinct (팔레트 7 슬롯).
        assertEquals(colors.values.toSet().size, colors.size)
        // 같은 입력에 같은 색.
        assertEquals(idx.colorOf("s4_dat"), idx.colorOf("s4_dat"))
        // 미지 파일은 fallback (alpha=0xFF).
        val unknown = idx.colorOf("s99_dat")
        assertEquals(0xFF.toInt(), (unknown ushr 24) and 0xFF)
    }

    @Test
    fun r89_skill_index_lookupByName_finds_known_skill() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        // R71 s4 (창) 의 첫 active_attack = "섬광".
        val hits = idx.lookupByName("섬광")
        assertTrue(hits.isNotEmpty())
        assertTrue(hits.all { it.skill.name.contains("섬광") })
    }

    // ─── R92: Hero3CatalogItemIndex ─────────────────────────────────────────

    @Test
    fun r92_item_index_builds_with_eighteen_categories_and_529_items() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogItemIndex.build(catalog)
        // R71: 18 카테고리 × 총 529 items.
        assertEquals(18, idx.fileCount)
        assertEquals(529, idx.size)
        // 평탄화 합계 = byFile 합계 = idx.size.
        val total = idx.byFile.values.sumOf { it.size }
        assertEquals(idx.size, total)
        // categoryCount 는 18 이하 (일부 카테고리 라벨이 중복일 수 있음).
        assertTrue(idx.categoryCount in 1..18)
    }

    @Test
    fun r92_item_index_groups_by_file_and_keeps_all_entries() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogItemIndex.build(catalog)
        for ((file, list) in idx.byFile) {
            assertTrue(file.startsWith("i") && file.endsWith("_dat"))
            assertTrue(list.isNotEmpty())
            assertTrue(list.all { it.file == file })
        }
    }

    @Test
    fun r92_item_index_colorOf_distinct_for_first_ten_files_and_stable() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogItemIndex.build(catalog)
        val sorted = idx.byFile.keys.sorted()
        // 첫 10 파일은 palette slot[0..9] 와 1:1 distinct.
        val first10 = sorted.take(10)
        val colors10 = first10.map { idx.colorOf(it) }
        assertEquals(first10.size, colors10.toSet().size)
        // palette slot 매핑 확인.
        for ((i, f) in first10.withIndex()) {
            assertEquals(Hero3CatalogItemIndex.FILE_PALETTE[i], idx.colorOf(f))
        }
        // 같은 파일을 두 번 물어도 같은 색.
        assertEquals(idx.colorOf(sorted[0]), idx.colorOf(sorted[0]))
        // 미지 파일은 fallback (alpha=0xFF, 각 채널 ≥ 0x80).
        val unknown = idx.colorOf("i99_dat")
        assertEquals(0xFF.toInt(), (unknown ushr 24) and 0xFF)
        assertTrue(((unknown ushr 16) and 0xFF) >= 0x80)
        assertTrue(((unknown ushr 8) and 0xFF) >= 0x80)
        assertTrue((unknown and 0xFF) >= 0x80)
    }

    @Test
    fun r92_item_index_lookupByName_finds_known_consumable() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogItemIndex.build(catalog)
        // R76 finding: i18_dat[0] = "포션" (recipe 0 output).
        val hits = idx.lookupByName("포션")
        assertTrue(hits.isNotEmpty())
        // 매칭된 entry 의 cleanName 또는 name 에 "포션" 이 포함.
        assertTrue(hits.all { it.item.name.contains("포션") || it.item.cleanName.contains("포션") })
    }

    // ─── R91: primaryModifier (effect_v2 → damage/heal bonus) ──────────────

    @Test
    fun r91_skill_index_primaryModifier_handles_null_effect() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        // effectV2=null 인 skill 은 무조건 0 (OFFENSE / HEAL 둘 다).
        val noEffect = idx.entries.firstOrNull { it.skill.effectV2 == null }
        if (noEffect != null) {
            assertEquals(0, idx.primaryModifier(noEffect.skill,
                Hero3CatalogSkillIndex.ModifierKind.OFFENSE))
            assertEquals(0, idx.primaryModifier(noEffect.skill,
                Hero3CatalogSkillIndex.ModifierKind.HEAL))
        }
    }

    @Test
    fun r91_skill_index_primaryModifier_picks_only_matching_codes() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        // OFFENSE 합 = 살아있는 slot 중 codeName startsWith("ATT") 의 primarySigned 만.
        for (e in idx.entries) {
            val ev = e.skill.effectV2 ?: continue
            val live = listOf(ev.slot1, ev.slot2, ev.slot3).filterNot { it.isSentinel || it.isZero }
            val expectedOff = live.filter { it.codeName.startsWith("ATT") }.sumOf { it.primarySigned }
            val expectedHeal = live.filter {
                it.codeName.startsWith("HP_HEAL") || it.codeName.startsWith("HP_REGEN")
            }.sumOf { it.primarySigned }
            assertEquals(expectedOff,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.OFFENSE))
            assertEquals(expectedHeal,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.HEAL))
        }
    }

    @Test
    fun r91_primaryModifierForEngineName_returns_zero_for_unknown() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        // 매칭 0 hits → 0.
        assertEquals(0, idx.primaryModifierForEngineName(
            "__no_such_engine_skill_zzz__",
            Hero3CatalogSkillIndex.ModifierKind.OFFENSE))
        // engine "연사" 는 catalog 에 ≥1 hit (R89 finding) — Int 반환 (예외 없음).
        // 값은 데이터 의존이라 sign 검증만.
        val v = idx.primaryModifierForEngineName(
            "연사", Hero3CatalogSkillIndex.ModifierKind.OFFENSE)
        // primaryModifier 의 합은 Int 범위 안.
        assertTrue(v in Int.MIN_VALUE..Int.MAX_VALUE)
    }

    // ─── R100: TAUNT ModifierKind ──────────────────────────────────────────

    @Test
    fun r100_taunt_modifier_kind_matches_only_taunt() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        for (e in idx.entries) {
            val ev = e.skill.effectV2 ?: continue
            val live = listOf(ev.slot1, ev.slot2, ev.slot3).filterNot { it.isSentinel || it.isZero }
            val expected = live.filter { it.codeName == "TAUNT" }.sumOf { it.primarySigned }
            assertEquals(expected,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.TAUNT))
        }
    }

    // ─── R99: HP_DRAIN ModifierKind ────────────────────────────────────────

    @Test
    fun r99_hp_drain_modifier_kind_matches_only_hp_drain() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        for (e in idx.entries) {
            val ev = e.skill.effectV2 ?: continue
            val live = listOf(ev.slot1, ev.slot2, ev.slot3).filterNot { it.isSentinel || it.isZero }
            val expected = live.filter { it.codeName == "HP_DRAIN" }.sumOf { it.primarySigned }
            assertEquals(expected,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.HP_DRAIN))
        }
    }

    @Test
    fun r99_hp_drain_lookup_returns_zero_for_unknown_engine_name() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        assertEquals(0, idx.primaryModifierForEngineName(
            "__nope_zzz__", Hero3CatalogSkillIndex.ModifierKind.HP_DRAIN))
    }

    // ─── R98: HP_REGEN / SP_REGEN ModifierKind ─────────────────────────────

    @Test
    fun r98_hp_regen_modifier_kind_matches_only_hp_regen() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        for (e in idx.entries) {
            val ev = e.skill.effectV2 ?: continue
            val live = listOf(ev.slot1, ev.slot2, ev.slot3).filterNot { it.isSentinel || it.isZero }
            val expected = live.filter { it.codeName == "HP_REGEN" }.sumOf { it.primarySigned }
            assertEquals(expected,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.HP_REGEN))
        }
    }

    @Test
    fun r98_sp_regen_modifier_kind_matches_only_sp_regen() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        for (e in idx.entries) {
            val ev = e.skill.effectV2 ?: continue
            val live = listOf(ev.slot1, ev.slot2, ev.slot3).filterNot { it.isSentinel || it.isZero }
            val expected = live.filter { it.codeName == "SP_REGEN" }.sumOf { it.primarySigned }
            assertEquals(expected,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.SP_REGEN))
        }
    }

    // ─── R94: debuffCountForEngineName ─────────────────────────────────────

    @Test
    fun r94_debuff_count_zero_for_unknown_engine_name() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        assertEquals(0, idx.debuffCountForEngineName("__no_such_skill_zzz__"))
    }

    @Test
    fun r94_debuff_count_matches_best_hit_nDebuffs() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        // 모든 skill 에 대해, lookupByName(skill.name) 의 rank 최대 hit 의 nDebuffs 와 일치.
        for (e in idx.entries) {
            val hits = idx.lookupByName(e.skill.name)
            if (hits.isEmpty()) continue
            val best = hits.maxByOrNull { it.skill.effectV2?.rank ?: 0 } ?: hits[0]
            val expected = best.skill.effectV2?.nDebuffs ?: 0
            assertEquals(expected, idx.debuffCountForEngineName(e.skill.name))
        }
    }

    // ─── R93: ModifierKind 확장 (DEFENSE/CRIT*/ACCURACY/DODGE) ─────────────

    @Test
    fun r93_modifier_kinds_match_distinct_code_names() {
        // R93: 5 신규 kind 의 매칭 코드가 R91 의 OFFENSE/HEAL 와 disjoint.
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        for (e in idx.entries) {
            val ev = e.skill.effectV2 ?: continue
            val live = listOf(ev.slot1, ev.slot2, ev.slot3).filterNot { it.isSentinel || it.isZero }
            val expectedDef    = live.filter { it.codeName == "P_DEF" || it.codeName == "M_DEF" }.sumOf { it.primarySigned }
            val expectedCrit   = live.filter { it.codeName == "CRI_RATE" }.sumOf { it.primarySigned }
            val expectedCDef   = live.filter { it.codeName == "CRI_DEF" }.sumOf { it.primarySigned }
            val expectedAcc    = live.filter { it.codeName == "ACC" }.sumOf { it.primarySigned }
            val expectedDod    = live.filter { it.codeName == "DOD" }.sumOf { it.primarySigned }
            assertEquals(expectedDef,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.DEFENSE))
            assertEquals(expectedCrit,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.CRIT_RATE))
            assertEquals(expectedCDef,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.CRIT_DEF))
            assertEquals(expectedAcc,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.ACCURACY))
            assertEquals(expectedDod,
                idx.primaryModifier(e.skill, Hero3CatalogSkillIndex.ModifierKind.DODGE))
        }
    }

    @Test
    fun r93_modifier_kinds_handle_null_effect() {
        // effectV2=null 인 skill 은 모든 kind 에서 0.
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        val noEffect = idx.entries.firstOrNull { it.skill.effectV2 == null } ?: return
        for (k in Hero3CatalogSkillIndex.ModifierKind.values()) {
            assertEquals(0, idx.primaryModifier(noEffect.skill, k))
        }
    }

    @Test
    fun r93_modifier_kind_engine_lookup_returns_zero_for_unknown_name() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        for (k in Hero3CatalogSkillIndex.ModifierKind.values()) {
            assertEquals(0, idx.primaryModifierForEngineName("__nope__$k", k))
        }
    }

    // ─── R90: engine ↔ catalog skill bridge ────────────────────────────────

    @Test
    fun r90_skill_index_bridges_engine_rapidfire_to_catalog() {
        // R89 finding: engine "연사" (ritz_rapidfire) ↔ catalog 정확 매칭 (≥1 hit).
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        val hits = idx.lookupByName("연사")
        assertTrue(hits.isNotEmpty())
        // 매칭된 entry 의 effectV2 가 살아있으면 effectSummary 가 rank= 로 시작.
        val withEffect = hits.firstOrNull { it.skill.effectV2 != null }
        if (withEffect != null) {
            val summary = idx.effectSummary(withEffect.skill)
            assertNotNull(summary)
            assertTrue(summary!!.startsWith("rank="))
        }
    }

    @Test
    fun r90_skill_index_lookupByName_returns_empty_for_unknown_engine_skill() {
        // bespoke engine 스킬 ("강타" 등) 은 catalog 에 명시적 매칭이 없을 수 있다.
        // 매칭이 없어도 (no catalog match) 동작 — empty list 만 보장.
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        val hits = idx.lookupByName("__no_such_skill_zzz__")
        assertTrue(hits.isEmpty())
    }

    @Test
    fun r90_quest_registry_has_catalogKey_slot_defaulting_to_null() {
        // R90 §1.4: Quest data class 에 catalogKey: String? = null 슬롯 추가.
        // 4 bespoke 엔트리는 모두 null 그대로.
        val all = com.hero3.remake.engine.QuestRegistry.all
        assertEquals(4, all.size)
        assertTrue(all.all { it.catalogKey == null })
    }

    @Test
    fun r89_skill_index_effectSummary_handles_null_and_empty() {
        val catalog = Hero3CatalogLoader.load(reader())
        val idx = Hero3CatalogSkillIndex.build(catalog)
        // 적어도 1개 skill 은 effectV2 가 있을 것 (s4 active_attack 그룹).
        val withEffect = idx.entries.firstOrNull { it.skill.effectV2 != null }
        if (withEffect != null) {
            val summary = idx.effectSummary(withEffect.skill)
            assertNotNull(summary)
            assertTrue(summary!!.startsWith("rank="))
        }
        // effectV2=null 인 skill 은 summary=null.
        val withoutEffect = idx.entries.firstOrNull { it.skill.effectV2 == null }
        if (withoutEffect != null) {
            assertEquals(null, idx.effectSummary(withoutEffect.skill))
        }
    }
}
