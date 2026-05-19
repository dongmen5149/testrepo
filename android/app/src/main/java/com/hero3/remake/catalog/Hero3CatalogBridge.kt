package com.hero3.remake.catalog

import com.hero3.remake.engine.EnemyDef
import com.hero3.remake.engine.Item
import com.hero3.remake.engine.ItemKind
import com.hero3.remake.engine.ItemRegistry

/**
 * Hero3 R56-R78 분석 데이터를 engine-core 타입(EnemyDef / Item / 등)으로 변환하는 bridge.
 *
 * 목적 (R79 audit 후속): R74까지의 풍부한 데이터를 게임 코드에 통합할 수 있게 함.
 * scene/registries 는 직접 Hero3Catalog 를 보지 않고 이 bridge 의 결과만 사용.
 *
 * 핵심 API:
 *   - [enemiesFromCatalog]    : 161×2 enemy stats → List<EnemyDef> (normal/hard)
 *   - [shopStockFromCatalog]  : 5 region_shops × i15 catalog → List<Item> per shop
 *   - [forgeRecipesFromCatalog]: 80 recipes → resolved input/output [Hero3Item]
 *
 * R74 데이터가 없으면 (catalog.r74Data == null) 빈 list 반환 → 호출자가 fallback 결정.
 */
object Hero3CatalogBridge {

    /** Hero3Catalog 의 enemiesNormal (또는 Hard) 161 entries → EnemyDef list.
     *
     *  Sprite 경로는 `enemy/eXXXX_bm` 패턴 — pos 인덱스 + 0x100 base offset 기반.
     *  drop_table 은 R74 drop_dat 의 primary/secondary drop 을 사용 (가능 시).
     */
    fun enemiesFromCatalog(catalog: Hero3Catalog, hardMode: Boolean = false): List<EnemyDef> {
        val list = if (hardMode) catalog.enemiesHard else catalog.enemiesNormal
        val drops = catalog.r74Data?.let { if (hardMode) it.dropTableHard else it.dropTable }
        return list.mapIndexed { idx, e ->
            val stats = e.stats
            val drop = drops?.getOrNull(idx)
            EnemyDef(
                id          = catalogEnemyId(e.name, idx, hardMode),
                nameKo      = e.name,
                nameEn      = e.name,  // 영문 미디코드 — 한글 이름 사용
                hpMax       = stats.hpMax.coerceAtLeast(1),
                atk         = stats.atk.coerceAtLeast(1),
                def         = inferDef(stats.hpMax, stats.lvl),
                expReward   = expFromBE(stats.expGold),
                goldReward  = goldFromBE(stats.expGold),
                spriteDir   = "enemy/e${(0x100 + idx).toString(16).padStart(4, '0')}_bm",
                dropTable   = drop?.let { buildDropTable(it, catalog) } ?: emptyList(),
            )
        }
    }

    /** 5 region_shops × i15 shop catalog → List<Item>.
     *
     *  shop.itemIds 가 i15 catalog index 인 점을 이용해 entry name 으로 ItemRegistry 조회.
     *  ItemRegistry 에 미등록 entries 는 임시 Item placeholder 로 생성.
     */
    fun shopStockFromCatalog(catalog: Hero3Catalog, shopIdx: Int, hardMode: Boolean = false): List<Item> {
        val r74 = catalog.r74Data ?: return emptyList()
        val shops = if (hardMode) r74.regionShopsHard else r74.regionShops
        val shop = shops.getOrNull(shopIdx) ?: return emptyList()
        return shop.itemIds.mapNotNull { id ->
            val entry = r74.shopCatalog.getOrNull(id) ?: return@mapNotNull null
            // ItemRegistry 먼저 시도 → 없으면 한글 이름 기반 placeholder Item
            findItemByKoName(entry.name) ?: placeholderItem(entry, id)
        }
    }

    /** 80 recipes → resolved (inputs, output) Hero3Item lists. */
    data class ResolvedRecipe(
        val recipe: Hero3Recipe,
        val inputs: List<Hero3Item>,
        val output: Hero3Item?,
    )

    fun forgeRecipesFromCatalog(catalog: Hero3Catalog, hardMode: Boolean = false): List<ResolvedRecipe> {
        val r74 = catalog.r74Data ?: return emptyList()
        val list = if (hardMode) r74.recipesHard else r74.recipes
        return list.map { r ->
            ResolvedRecipe(
                recipe = r,
                inputs = r.inputs.mapNotNull { catalog.resolveItem(it) },
                output = catalog.resolveItem(r.output),
            )
        }
    }

    // ─── helpers ──────────────────────────────────────────────────────────

    private fun catalogEnemyId(name: String, idx: Int, hardMode: Boolean): String {
        val mode = if (hardMode) "h" else "n"
        return "h3_${mode}_${idx.toString().padStart(3, '0')}"
    }

    /** R56 enemy_dat의 stat[10..11]=hp_max BE u16, stat[14..15]=exp_gold combined.
     *  exp/gold split은 R69에서 4 그룹화 가설; 단순화: high byte=exp tier, low=gold base.
     */
    private fun expFromBE(combined: Int): Int = (combined ushr 8).coerceAtLeast(1)
    private fun goldFromBE(combined: Int): Int = (combined and 0xff).coerceAtLeast(1)

    /** DEF 는 enemy_dat 19B 안에 명시되지 않음 (R56). hp/lvl 기반 추정. */
    private fun inferDef(hpMax: Int, lvl: Int): Int =
        ((hpMax / 8) + (lvl / 4)).coerceAtLeast(1)

    private fun buildDropTable(d: Hero3DropRecord, catalog: Hero3Catalog): List<Pair<String, Float>> {
        val table = mutableListOf<Pair<String, Float>>()
        // primary drop (if not common-pool sentinel)
        val (p1, p2) = d.primaryDrop
        if (p1 != 133 || p2 != 153) {
            // best-effort: byte[11] as 카테고리 hint (실제 의미 R79+ 확정)
            table.add("h3_drop_p_${p1}_${p2}" to 0.30f)
        }
        // secondary drop (only if not common-pool)
        if (!d.secondaryIsCommonPool) {
            val (s1, s2) = d.secondaryDrop
            table.add("h3_drop_s_${s1}_${s2}" to 0.15f)
        }
        return table
    }

    private fun findItemByKoName(name: String): Item? =
        ItemRegistry.all.firstOrNull { it.nameKo == name }

    private fun placeholderItem(entry: Hero3ShopCatalogEntry, idx: Int): Item =
        Item(
            id = "h3_shop_${idx.toString().padStart(2, '0')}",
            nameKo = entry.name,
            nameEn = entry.name,
            kind = ItemKind.MATERIAL,
            price = 100,
            power = 0,
            descKo = entry.body.take(80),
            descEn = "",
        )
}
