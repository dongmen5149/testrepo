package com.hero3.remake.catalog

import com.hero3.remake.engine.AssetNotFound
import com.hero3.remake.engine.AssetReader
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
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
    fun catalog_schema_version_is_1_1() {
        val catalog = Hero3CatalogLoader.load(reader())
        assertEquals("1.1", catalog.schemaVersion)
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
    fun des_status_has_8_pending_files() {
        val catalog = Hero3CatalogLoader.load(reader())
        // R57/R60: 8 DES pending (i15/drop/droph/getitem/smith/smithh/shop/shoph)
        assertEquals(8, catalog.desStatus.pendingFiles.size)
        assertEquals("0EP@KO91", catalog.desStatus.key)
    }

    @Test
    fun boss_skill_ids_resolved_returns_false() {
        val catalog = Hero3CatalogLoader.load(reader())
        // R67/R68/R70 confirm: H4 (별도 boss skill table) but unresolved
        assertFalse(catalog.bossSkillIdsResolved())
    }
}
