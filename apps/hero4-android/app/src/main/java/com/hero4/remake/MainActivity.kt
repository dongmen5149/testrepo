package com.hero4.remake

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView
import com.hero3.remake.engine.ItemRegistry
import com.hero4.remake.catalog.Hero4CatalogLoader
import com.hero4.remake.platform.AndroidAssetReader

/**
 * Hero4 Android 진입점 — Phase C Step 5 에서 engine-core (KMM) 의존 추가 (2026-05-19).
 *
 * 현재 상태:
 *   - engine-core (commonMain, Hero3 와 공유) 의 NpcRegistry / ItemRegistry / SkillRegistry 등 직접 사용 가능
 *   - Hero4 게임 콘텐츠 (Hero4 자산을 읽는 Scene 들) wiring 은 Step 4 (Compose MP) + Step 5 후속에서
 *   - h4_catalog.json (R69) 을 Hero4 전용 NpcRegistry 등으로 변환하는 loader 는 Hero4CatalogLoader.kt 참조
 *
 * 자산은 이미 src/main/assets/ 에 prepare_android_assets.py 로 배포되어 있음.
 */
class MainActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setBackgroundColor(Color.BLACK)
        }
        // Phase C Step 5 — engine-core 의존 검증 + Hero4 catalog 로드 (proof-of-concept)
        val sb = StringBuilder("영웅서기4 - 환영의검\nRemake (Hero4)\n\n")
        try {
            val catalog = Hero4CatalogLoader.load(AndroidAssetReader(this))
            sb.append("✓ engine-core (KMM): item registry size = ${ItemRegistry.all.size}\n")
            sb.append("✓ Hero4 catalog (R69):\n")
            sb.append("    heroes=${catalog.heroes.size} (${catalog.heroes.joinToString { it.name }})\n")
            sb.append("    skill sets=${catalog.skillSets.size}, total skills=${catalog.totalSkills}\n")
            sb.append("    items=${catalog.items.size} files, ${catalog.totalItemKorean} Korean entries\n")
            sb.append("    NPC scripts=${catalog.npc.size}, ${catalog.totalNpcKorean} Korean entries\n")
            sb.append("    quests=${catalog.quests.size} (${catalog.mainStoryQuests} 메인스토리)\n")
            sb.append("    hero stat blocks=${catalog.heroStats.size}\n\n")
            if (catalog.quests.isNotEmpty()) {
                sb.append("First quest: ${catalog.quests[0].name}\n")
                sb.append("  → ${catalog.quests[0].description.take(40)}\n\n")
            }
            sb.append("Phase 3 (engine wiring) — 자산 + 데이터 준비 완료")
        } catch (e: Exception) {
            sb.append("Catalog load failed: ${e.message}")
        }
        layout.addView(TextView(this).apply {
            text = sb.toString()
            setTextColor(Color.WHITE)
            textSize = 14f
            gravity = Gravity.CENTER
        })
        setContentView(layout)
    }
}
