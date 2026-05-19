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
}
