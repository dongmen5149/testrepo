package com.hero3.remake.catalog

import com.hero3.remake.engine.AssetNotFound
import com.hero3.remake.engine.AssetReader
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File

/**
 * Hero3CatalogBridge unit test — R79 "데이터→게임 통합" 검증.
 *
 * 161×2 enemies / 5 region shops / 80 recipes 가 engine-core 타입으로 정상 변환되는지.
 */
class Hero3CatalogBridgeTest {

    private class FileAssetReader(private val baseDir: File) : AssetReader {
        override fun readText(path: String): String = try {
            File(baseDir, path).readText(Charsets.UTF_8)
        } catch (e: Exception) { throw AssetNotFound(path, e) }
        override fun readBytes(path: String): ByteArray = try {
            File(baseDir, path).readBytes()
        } catch (e: Exception) { throw AssetNotFound(path, e) }
    }

    private fun catalog(): Hero3Catalog =
        Hero3CatalogLoader.load(FileAssetReader(File("src/main/assets")))

    @Test
    fun bridge_converts_161_normal_enemies() {
        val c = catalog()
        val enemies = Hero3CatalogBridge.enemiesFromCatalog(c, hardMode = false)
        assertEquals(161, enemies.size)
        val first = enemies[0]
        // R56: enemy[0] = 아스크란가드 lvl 15 hp 41
        assertEquals("아스크란가드", first.nameKo)
        assertTrue(first.hpMax >= 1)
        assertTrue(first.atk >= 1)
        assertTrue(first.spriteDir.startsWith("enemy/e"))
    }

    @Test
    fun bridge_converts_161_hard_enemies() {
        val c = catalog()
        val enemies = Hero3CatalogBridge.enemiesFromCatalog(c, hardMode = true)
        assertEquals(161, enemies.size)
    }

    @Test
    fun bridge_shop_stock_resolves_for_5_region_shops() {
        val c = catalog()
        // R74: 5 region shops × i15 catalog
        // shop[0] (lv 1-15) has 2 items: 얼음비늘장갑, 바람가죽모자
        val shop0 = Hero3CatalogBridge.shopStockFromCatalog(c, 0)
        assertEquals(2, shop0.size)
        assertEquals("얼음비늘장갑", shop0[0].nameKo)
        // shop[4] (lv 26-40) has 5 items
        val shop4 = Hero3CatalogBridge.shopStockFromCatalog(c, 4)
        assertEquals(5, shop4.size)
    }

    @Test
    fun bridge_forge_recipes_resolve_to_real_items() {
        val c = catalog()
        val recipes = Hero3CatalogBridge.forgeRecipesFromCatalog(c)
        assertEquals(80, recipes.size)
        // Recipe 0: output → i18[0] = 포션
        val r0 = recipes[0]
        assertNotNull(r0.output)
        assertEquals("포션", r0.output!!.cleanName)
        // Recipe 0 has 1 valid input (others are 0xff empty)
        assertEquals(1, r0.inputs.size)
        // Recipe 3 has 3 inputs all real
        val r3 = recipes[3]
        assertEquals(3, r3.inputs.size)
    }

    @Test
    fun r82_catalog_item_pool_extends_inventory_registry() {
        val c = catalog()
        val pool = Hero3CatalogBridge.catalogItemPool(c)
        // 18 categories × min 1 entry → at least 50 items
        assertTrue(pool.size >= 50)
        // 모든 entry 가 unique id
        assertEquals(pool.size, pool.map { it.id }.toSet().size)
        // id prefix
        assertTrue(pool.all { it.id.startsWith("h3_item_") })
    }

    @Test
    fun r110f_catalog_item_pool_default_loads_all_529_items() {
        val c = catalog()
        val pool = Hero3CatalogBridge.catalogItemPool(c)
        // R110f: maxPerCategory 기본값 50 으로 상향. 18 file × max 46 entry = 529 catalog items 모두 적재.
        // (정확히 529 가 아닌 ≥ 529 인 이유: 18 file 외 변동 가능성 대비.)
        assertTrue("expected all 529 catalog items, got ${pool.size}", pool.size >= 529)
    }

    @Test
    fun r110f_catalog_item_pool_max_per_category_30_truncates() {
        val c = catalog()
        val capped = Hero3CatalogBridge.catalogItemPool(c, maxPerCategory = 30)
        val full = Hero3CatalogBridge.catalogItemPool(c)  // default 50
        // 30 cap 시 7 file 이 truncate 되어 60 items 누락.
        assertTrue("expected cap=30 to truncate, ${capped.size} vs ${full.size}", capped.size < full.size)
        assertEquals(60, full.size - capped.size)
    }

    @Test
    fun r83_drop_table_resolves_some_to_catalog_item_ids() {
        val c = catalog()
        val enemies = Hero3CatalogBridge.enemiesFromCatalog(c)
        // R83: drop_dat primary/secondary 가 (cat, id) 로 해석 시도, catalog 매칭 시 h3_item_ prefix
        val allDropIds = enemies.flatMap { e -> e.dropTable.map { it.first } }
        val resolvedCount = allDropIds.count { it.startsWith("h3_item_") }
        val placeholderCount = allDropIds.count { it.startsWith("h3_drop_") }
        // 해석된 것 + placeholder 합계 = 259 (R79 카운트 변경 없음)
        assertEquals(259, resolvedCount + placeholderCount)
        // 적어도 일부는 resolve 되었어야 함 (catalog 의 item 수가 많으므로)
        assertTrue("expected some drops to resolve, got $resolvedCount", resolvedCount > 0)
    }

    @Test
    fun r82_random_catalog_enemy_id_matches_h3_n_pattern() {
        val c = catalog()
        val id = Hero3CatalogBridge.randomCatalogEnemyId(c, playerLevel = 10)
        assertNotNull(id)
        assertTrue(id!!.startsWith("h3_n_"))
        // level-band 가 비어 있으면 fallback random 이라 ID 자체는 항상 valid
    }

    @Test
    fun bridge_drop_table_excludes_common_pool_sentinel() {
        val c = catalog()
        val enemies = Hero3CatalogBridge.enemiesFromCatalog(c)
        // 63 records have common-pool secondary — those should NOT add a secondary drop
        val totalDropEntries = enemies.sumOf { it.dropTable.size }
        // Expected: 161 primary minus those that are also (133,153)=0 primary (R78: 0)
        //         + 161 secondary minus 63 common-pool = 98 secondary
        // total = 161 + 98 = 259
        assertEquals(259, totalDropEntries)
    }
}
