package com.hero3.remake.scene

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import com.hero3.remake.MainActivity
import com.hero3.remake.catalog.Hero3Catalog
import com.hero3.remake.engine.InputController
import com.hero3.remake.engine.Scene
import com.hero3.remake.engine.Settings
import com.hero3.remake.engine.UiKit

/**
 * R72 신규 — Hero3 game_balance.json (R71 catalog) 의 raw 데이터 brower.
 *
 * 4-7 키 (또는 ▲▼) 로 카테고리 전환 / OK 로 entry 선택:
 *   1. Overview         — 총 개수 요약
 *   2. Stat Enum        — 24/25 codes
 *   3. Rarity           — 6 prefix
 *   4. Item Categories  — 18 카테고리 (i0~i18)
 *   5. Skill Sets       — 7 weapon (s4~s10)
 *   6. Boss Roster      — 15 normal + 15 hard
 *   7. DES Status       — 8 pending files
 *
 * 디버그 / 자료 검증용 scene. 실제 게임 플레이 화면 아님.
 */
class CatalogViewerScene(
    private val context: Context,
    private val input: InputController,
    private val settings: Settings,
    private val catalog: Hero3Catalog,
    private val onRequest: (MainActivity.SceneRequest) -> Unit,
) : Scene {

    private enum class Tab(val labelKo: String, val labelEn: String) {
        OVERVIEW("개요", "Overview"),
        STAT_ENUM("스탯 enum", "Stat Enum"),
        RARITY("등급", "Rarity"),
        ITEMS("아이템 카테고리", "Item Categories"),
        SKILLS("스킬셋", "Skill Sets"),
        BOSSES("보스 명단", "Boss Roster"),
        SHOP_CATALOG("상점 카탈로그", "Shop Catalog"),  // R80: R74 i15 38 entries
        RECIPES("단조 레시피", "Forge Recipes"),       // R80: R74 smith 80 entries
        REGION_SHOPS("지역 상점", "Region Shops"),     // R80: R74 5 region shops
        QUESTS("퀘스트 목록", "Quests"),                // R84: catalog 115 quests
        QUEST_ITEM_XREF("아이템-퀘스트 xref", "Item-Quest Xref"),  // R87: 21 items
        DES("DES 상태", "DES Status"),
    }

    private var tabIdx = 0
    private var rowIdx = 0
    private val bg = Paint().apply { color = Color.rgb(10, 14, 28) }

    override fun update(deltaMs: Long) {
        if (input.pressedOnce(InputController.K_SOFT2) ||
            input.pressedOnce(InputController.K_OK)) {
            onRequest(MainActivity.SceneRequest.Pop); return
        }
        if (input.pressedOnce(InputController.K_LEFT)) {
            tabIdx = (tabIdx - 1 + Tab.values().size) % Tab.values().size
            rowIdx = 0
        }
        if (input.pressedOnce(InputController.K_RIGHT)) {
            tabIdx = (tabIdx + 1) % Tab.values().size
            rowIdx = 0
        }
        val rows = rowsForTab(Tab.values()[tabIdx])
        if (input.pressedOnce(InputController.K_UP)) rowIdx = (rowIdx - 1 + rows.size).coerceAtLeast(0) % rows.size.coerceAtLeast(1)
        if (input.pressedOnce(InputController.K_DOWN)) rowIdx = (rowIdx + 1) % rows.size.coerceAtLeast(1)
    }

    private fun rowsForTab(tab: Tab): List<String> {
        val isEn = settings.isEn
        return when (tab) {
            Tab.OVERVIEW -> overviewRows(isEn)
            Tab.STAT_ENUM -> catalog.statEnum.entries.map { (k, v) -> "$k  ${v.name.padEnd(20)}  ${v.desc.take(40)}" }
            Tab.RARITY -> catalog.rarity.map { r ->
                "${r.prefix.ifBlank { "(none)" }}  ${r.name.padEnd(14)}  arm×${r.modifierArmor}  wep×${r.modifierWeapon}"
            }
            Tab.ITEMS -> catalog.items.map { c ->
                "${c.file.padEnd(8)}  ${c.category.padEnd(10)}  n=${c.nItems}"
            }
            Tab.SKILLS -> catalog.skills.map { ws ->
                "${ws.file.padEnd(8)}  ${ws.weapon.padEnd(20)}  n=${ws.nSkills}"
            }
            Tab.BOSSES -> catalog.bossesNormal.map { b ->
                val td = b.trailerDecoded
                val rating = td?.combatRating ?: 0
                val slots = td?.skillSlots?.joinToString(",") ?: "?"
                "${b.name.padEnd(10)}  lvl=${b.stats.lvl}  HP=${b.stats.hpMax}  rating=$rating  slots=[$slots]"
            }
            Tab.SHOP_CATALOG -> catalog.r74Data?.shopCatalog?.map { e ->
                "[${e.nlen.toString().padStart(2)}] ${e.name.padEnd(10)}  ${e.body.take(50)}"
            } ?: listOf("(R74 data not loaded)")
            Tab.RECIPES -> catalog.r74Data?.recipes?.mapIndexed { i, r ->
                val out = catalog.resolveItem(r.output)?.cleanName ?: "?"
                val inN = r.inputs.size
                "[${i.toString().padStart(2)}] in=$inN → out=i${r.outputCat}[${r.outputId}] = $out"
            } ?: listOf("(R74 data not loaded)")
            Tab.REGION_SHOPS -> catalog.r74Data?.regionShops?.mapIndexed { i, s ->
                val items = catalog.resolveShopItems(s).joinToString(", ") { it.name }
                "shop[$i]  lv ${s.lvMin}-${s.lvMax}  items=[$items]"
            } ?: listOf("(R74 data not loaded)")
            Tab.QUESTS -> {
                // R85 — quest index 기반 중복 표시 및 통계 헤더.
                val index = com.hero3.remake.catalog.Hero3CatalogQuestIndex.build(catalog)
                val dupNames = index.duplicates().keys
                val header = listOf(
                    "loaded=${index.size}  distinct=${index.distinctCanonicalNames}  duplicates=${dupNames.size}"
                )
                val body = catalog.questFiles.flatMap { qf ->
                    listOf("=== ${qf.file} (n_entries=${qf.nEntries}, loaded=${qf.entries.size}, ${qf.sizeBytes}B) ===") +
                    qf.entries.map { e ->
                        val canon = com.hero3.remake.catalog.Hero3CatalogQuestIndex.canonicalize(e.name)
                        val mark = if (canon in dupNames) "★" else " "
                        "$mark pos=${e.pos.toString().padStart(4)}  ${e.name}"
                    }
                }
                if (catalog.questFiles.isEmpty()) listOf("(no catalog quests parsed)") else header + body
            }
            Tab.QUEST_ITEM_XREF -> {
                // R87 — 21 items × N matches. item 별로 group 후 첫 3 match 표시.
                if (catalog.questItemXref.isEmpty()) listOf("(no quest_item_xref data)")
                else {
                    val totalMatches = catalog.questItemXref.sumOf { it.matches.size }
                    listOf("items=${catalog.questItemXref.size}  total_matches=$totalMatches") +
                    catalog.questItemXref.flatMap { xref ->
                        listOf("─ ${xref.cleanName}  (${xref.matches.size} matches)") +
                        xref.matches.take(3).map { m ->
                            "    ${m.file}@${m.offset.toString().padStart(4)}  \"${m.text}\""
                        } +
                        if (xref.matches.size > 3) listOf("    … +${xref.matches.size - 3} more") else emptyList()
                    }
                }
            }
            Tab.DES -> catalog.desStatus.pendingFiles.map { f ->
                "${f.path.padEnd(20)}  ${f.role}"
            }.ifEmpty { listOf("✓ All ${catalog.desStatus.algorithm} files decrypted (R73)") }
        }
    }

    private fun overviewRows(isEn: Boolean): List<String> = listOf(
        "schema_version = ${catalog.schemaVersion}",
        "round_at_export = ${catalog.round}",
        "total items: ${catalog.totalItems}",
        "total skills: ${catalog.totalSkills}",
        "total enemies (normal): ${catalog.totalEnemies}",
        "total bosses (normal): ${catalog.totalBosses}",
        "stat_enum codes: ${catalog.statEnum.size}",
        "rarity classes: ${catalog.rarity.size}",
        "combat rating (normal): ${catalog.combatRatingFormulaNormal}",
        "combat rating (hard): ${catalog.combatRatingFormulaHard}",
        "DES pending: ${catalog.desStatus.pendingFiles.size} files (key: ${catalog.desStatus.key})",
        "boss skill IDs resolved: ${catalog.bossSkillIdsResolved()}",
        // R80: R74 data 통합 현황
        "R74 shop catalog: ${catalog.r74Data?.shopCatalog?.size ?: 0} entries",
        "R74 recipes: ${catalog.r74Data?.recipes?.size ?: 0} entries",
        "R74 region shops: ${catalog.r74Data?.regionShops?.size ?: 0} entries",
        "R74 drop tables: ${catalog.r74Data?.dropTable?.size ?: 0} records",
        "R84 catalog quests: ${catalog.questFiles.sumOf { it.nEntries }} entries across ${catalog.questFiles.size} files",
        if (isEn) "" else "",
        if (isEn) "R71-R80 — Android remake data layer + bridge." else "R71-R80 — Android 리메이크 데이터 계층 + bridge.",
    )

    override fun render(canvas: Canvas) {
        canvas.drawRect(0f, 0f, virtualWidth.toFloat(), virtualHeight.toFloat(), bg)
        val isEn = settings.isEn
        val tab = Tab.values()[tabIdx]
        UiKit.drawHeader(canvas, virtualWidth,
            if (isEn) "CATALOG / ${tab.labelEn}" else "자료집 / ${tab.labelKo}",
            "v${catalog.schemaVersion}  (${tabIdx + 1}/${Tab.values().size})")

        // tab row indicator
        val tabRowY = 24f
        var x = 6f
        for ((i, t) in Tab.values().withIndex()) {
            val label = if (isEn) t.labelEn else t.labelKo
            val w = label.length * 7f + 8f
            if (i == tabIdx) canvas.drawRect(x, tabRowY - 9f, x + w, tabRowY + 2f,
                Paint().apply { color = Color.argb(120, 255, 220, 90) })
            canvas.drawText(label, x + 4f, tabRowY, if (i == tabIdx) UiKit.body else UiKit.muted)
            x += w + 2f
            if (x > virtualWidth - 40f) { x = 6f; }
        }

        // row list
        val rows = rowsForTab(tab)
        val rowH = 11f
        val maxVisible = ((virtualHeight - 60f) / rowH).toInt()
        val scrollStart = (rowIdx - maxVisible + 2).coerceAtLeast(0).coerceAtMost(maxOf(0, rows.size - maxVisible))
        UiKit.drawBox(canvas, 4f, 36f, virtualWidth - 8f, virtualHeight - 56f)
        for (j in 0 until maxVisible.coerceAtMost(rows.size)) {
            val i = scrollStart + j
            if (i >= rows.size) break
            val y = 48f + j * rowH
            if (i == rowIdx) canvas.drawRect(6f, y - 8f, virtualWidth - 6f, y + 2f,
                Paint().apply { color = Color.argb(80, 200, 200, 255) })
            canvas.drawText(rows[i], 8f, y, UiKit.body)
        }

        // footer
        UiKit.drawHints(canvas, virtualWidth, virtualHeight,
            if (isEn) "<> tab  ^v row  R back" else "<> 탭  ^v 행  R 뒤로")
    }
}
