# Round 71 — Hero3Catalog data classes + CatalogLoader + unit tests (2026-05-19)

> 이번 라운드 목표: R70 의 MASTER_SPEC 의 "Android 리메이크 권장 구현 순서" §13 의 **2번 data loader 구현**. R64-R70 의 game_balance.json (582KB v1.1) 을 Kotlin data class 로 노출.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐⭐ **Hero3Catalog data classes 19개 + CatalogLoader** 구현 — game_balance.json v1.1 (582KB) 을 typed Kotlin object 로 노출. Hero4Catalog (R69 Phase C Step 5) 와 동일 패턴
- ⭐⭐⭐⭐ **android/app/src/main/assets/game_balance.json 복사** — Hero3 app 이 직접 import 가능. 582,116 bytes
- ⭐⭐⭐⭐ **AndroidAssetReader 구현** — Hero4 와 동일 platform-agnostic 추상화. engine-core 의 AssetReader interface 구현
- ⭐⭐⭐ **Hero3CatalogLoaderTest 12 unit tests 모두 통과** — 24 stat enum / 18 item / 7 skill set / 161 enemy / 15 boss / 6 rarity / 8 DES pending / combat_rating formula 검증

## 1. Hero3Catalog 데이터 모델 (★★★★★)

### 1.1 19 data classes (top-down)

```kotlin
data class Hero3Catalog(
    val schemaVersion: String,           // "1.1"
    val round: Int,                      // 66 (game_balance.json 생성 시)
    val statEnum: Map<String, Hero3StatEnumEntry>,
    val rarity: List<Hero3Rarity>,
    val items: List<Hero3ItemCategory>,
    val skills: List<Hero3WeaponSkillSet>,
    val enemiesNormal: List<Hero3Enemy>,
    val enemiesHard: List<Hero3Enemy>,
    val bossesNormal: List<Hero3Boss>,
    val bossesHard: List<Hero3Boss>,
    val combatRatingFormulaNormal: String,  // "round(lvl/2 + 44)"
    val combatRatingFormulaHard: String,    // "round(lvl/2 + 64)"
    val desStatus: Hero3DesStatus,
)

data class Hero3StatEnumEntry(...)        // 24 codes (R63)
data class Hero3Rarity(...)               // 6 prefixes (R62)
data class Hero3Item(...)                 // equip20 fields + clean_name + rarity
data class Hero3ItemCategory(...)         // i0~i18 grouping
data class Hero3SkillEffectSlot(...)      // R66 effect chain v2 slot
data class Hero3SkillEffectV2(...)        // 3-slot right-justified chain
data class Hero3Skill(...)                // skill body + effect_v2
data class Hero3WeaponSkillSet(...)       // s4~s10 grouping
data class Hero3EnemyStats(...)           // lvl/hpMax/expGold/atk/agi
data class Hero3Enemy(...)
data class Hero3BossTrailerDecoded(...)   // R65 6B trailer parsed
data class Hero3Boss(...)
data class Hero3DesPendingFile(...)
data class Hero3DesStatus(...)
```

### 1.2 helper methods

```kotlin
val totalItems: Int get() = items.sumOf { it.nItems }     // 529
val totalSkills: Int get() = skills.sumOf { it.nSkills }  // 105
val totalEnemies: Int get() = enemiesNormal.size          // 161
val totalBosses: Int get() = bossesNormal.size            // 15

fun statName(code: Int): String?
  // 0x05 → "ATT1", 0x07 → "P_DEF", ...

fun bossSkillIdsResolved(): Boolean = false
  // R67/R68/R70: H4 confirm but DES 복호화 후만 가능
```

## 2. Hero3CatalogLoader (★★★★★)

### 2.1 API

```kotlin
object Hero3CatalogLoader {
    fun load(reader: AssetReader): Hero3Catalog
}
```

### 2.2 사용 예 (Hero3 MainActivity / Scene)

```kotlin
val assetReader = AndroidAssetReader(this)
val catalog = Hero3CatalogLoader.load(assetReader)
println("Hero3: ${catalog.totalItems} items, ${catalog.totalSkills} skills")
println("Stat ATT1: ${catalog.statName(0x05)}")  // "ATT1"

// 보스 정보 활용
val 리츠Boss = catalog.bossesNormal.first { it.name == "리츠" }
println("리츠 combat_rating: ${리츠Boss.trailerDecoded?.combatRating}")  // 51
println("리츠 skills: ${리츠Boss.trailerDecoded?.skillSlots}")  // [3, 2, 1, 2]
```

### 2.3 platform-agnostic 의존

- engine-core 의 `AssetReader` interface (R69 Phase C Step 4c) 사용
- Android: `AndroidAssetReader(context)` → `context.assets.open()`
- 향후 iOS: `BundleAssetReader` 동일 패턴

## 3. AndroidAssetReader (Hero3 app, ★★★★)

`android/app/src/main/java/com/hero3/remake/platform/AndroidAssetReader.kt`:

```kotlin
class AndroidAssetReader(private val context: Context) : AssetReader {
    override fun readText(path: String): String = ...
    override fun readBytes(path: String): ByteArray = ...
}
```

Hero4 의 동일 클래스와 1:1 동일 (engine-core 의 platform-agnostic AssetReader 구현).

## 4. assets 배포

```
android/app/src/main/assets/game_balance.json (582,116 bytes)
  ← work/h3/game_balance.json (R66 export_game_balance.py 산출)
```

## 5. unit tests — 12개 모두 통과 ★★★

`android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt`:

```
✓ load_returns_non_null_catalog
✓ catalog_schema_version_is_1_1
✓ stat_enum_has_24_codes
✓ rarity_has_6_prefixes
✓ items_has_18_categories_and_529_total
✓ skills_has_7_weapon_classes_and_105_total
✓ enemies_has_161_normal_and_161_hard
✓ bosses_has_15_normal_and_15_hard
✓ combat_rating_formula_is_documented
✓ boss_combat_rating_matches_formula
✓ des_status_has_8_pending_files
✓ boss_skill_ids_resolved_returns_false
```

### 5.1 build config 변경

`android/app/build.gradle.kts`:
```kotlin
testImplementation("org.json:json:20240303")  // R71 신규
// Android stub 의 JSONObject 가 null 반환 (isReturnDefaultValues=true)
// → 실제 org.json 라이브러리 필요
```

### 5.2 핵심 검증

- **boss combat_rating formula** — 30 boss entries 모두 `round(lvl/2 + 44|64)` 통과
  - normal: lvl 14 → 51, lvl 32 → 60, lvl 46 → 67
  - hard: lvl 51 → 90, lvl 67 → 98
- **stat_enum lookup**: 0x05 → "ATT1", 0x07 → "P_DEF" 정확
- **boss skill ID resolution**: `false` (R67/R68 H4 가설, DES 복호화 후만 가능)

## 6. R71 산출물

### 6.1 신규 코드 (3개)

- `android/app/src/main/java/com/hero3/remake/catalog/Hero3Catalog.kt` (data classes 19 + loader)
- `android/app/src/main/java/com/hero3/remake/platform/AndroidAssetReader.kt` (AssetReader impl)
- `android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt` (12 tests)

### 6.2 신규 asset

- `android/app/src/main/assets/game_balance.json` (582,116 bytes, work/h3 → assets 복사)

### 6.3 빌드 config 변경

- `android/app/build.gradle.kts` — testImplementation org.json:json:20240303 추가

### 6.4 진행률 갱신

- **R70 종료 ~99.5%** → **R71 종료 ~99.7%** (+0.2%p)
- 게임 시스템 모델링: 99.9% (이미 거의 100%)
- **Android 리메이크 통합도**: data loader 완성 = MASTER_SPEC §13 step 2 완료
- 자동 분석 가능 영역: ~100% (DES 복호화 + LLM 번역 + audio 만 남음)

## 7. Hero3 Android 리메이크 다음 단계 (R72+)

### 7.1 자동 가능 (engine-core 통합)

1. ⭐⭐⭐ **Hero3 scene 코드에서 Hero3Catalog 사용** — InventoryScene/BattleScene 등이 catalog 의 items/enemies 직접 사용
2. ⭐⭐⭐ **stat enum lookup helper** — combat 계산 시 catalog.statName(code) 활용
3. ⭐⭐ **rarity prefix 처리** — InventoryScene 가 rarity color 표시
4. ⭐⭐ **boss combat_rating 표시** — 보스 mob UI 에 "권장 lvl: 51" 표시
5. ⭐ **i14 crafting recipe loader** — DES 복호화 후 smith_dat 매핑 시 활용

### 7.2 사용자 환경 필수 (Hero3 자체 분석)

R70 와 동일:
- DES 8 파일 복호화
- Dialogue LLM 번역 ($4.09)
- SMAF→OGG audio
- boss skill ID 매핑 (DES 후속)

## 8. 참고

- [MASTER_SPEC.md](MASTER_SPEC.md) §13 — Android 리메이크 권장 구현 순서 (이 라운드 = step 2)
- [Round 70](ghidra-round70-master-spec-exp-groups-2026-05-19.md) — Master Spec 작성
- [Hero4 R69](../h4/round69-skill-catalog-and-batch-decrypt.md) — Hero4Catalog 패턴 (이 라운드의 reference)
- [Phase C Step 4c](../../C:/Users/viewe/.claude/projects/c--gameRemake-testrepo/memory/project_phase_c.md) — AssetReader interface 도입
- `engine-core/src/commonMain/kotlin/com/hero3/remake/engine/AssetReader.kt` — platform-agnostic 인터페이스
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
