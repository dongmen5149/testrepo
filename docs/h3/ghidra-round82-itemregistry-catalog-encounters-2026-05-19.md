# 영웅서기3 Round 82 — ItemRegistry catalog 확장 + MapWalk encounter catalog-fed

**Date**: 2026-05-19
**Status**: ✅ **69/69 tests pass** + APK BUILD SUCCESSFUL. MapWalk encounter 가 처음으로 161 catalog enemies 풀 사용.

## 1. 한 줄

R81 의 ForgeScene 단조 매칭 범위를 ItemRegistry 15 → **500+ catalog items** 로 확장 (registerExtra API). MapWalkScene 의 random encounter 가 R56 의 **161 catalog enemies 의 level-band ±5** 풀에서 추출. BattleScene 의 R80 `h3_n_NNN` pattern 이 실제로 자동 발화됨.

## 2. 신규 / 변경

### 2.1 ItemRegistry (engine-core) — extensible 확장

```kotlin
private val extras: MutableMap<String, Item> = mutableMapOf()

fun get(id: String): Item? = byId[id] ?: extras[id]
fun registerExtra(items: List<Item>)
fun allWithExtras(): List<Item> = all + extras.values
```

base list 보존 + 외부 추가 등록 가능. 동일 id 는 마지막 등록 우선.

### 2.2 Hero3CatalogBridge 신규 helper 2개

```kotlin
// catalog 의 18 categories × first N entries → engine-core Item
fun catalogItemPool(catalog, maxPerCategory = 30): List<Item>

// 161 enemies 중 player level ±5 범위 random pick
fun randomCatalogEnemyId(catalog, playerLevel, hardMode = false): String?
```

- `catalogItemPool`: id `h3_item_<file>_<pos>`, kind 는 file 카테고리 기반 추론 (i0-i3 ARMOR, i4-i10 WEAPON, i12-i13 ACCESSORY, i14 MATERIAL, i17 ACCESSORY, i18 CONSUMABLE)
- `randomCatalogEnemyId`: level-band 우선, 비어 있으면 전체 random fallback. ID = `h3_n_NNN` / `h3_h_NNN` (R80 패턴)

### 2.3 MainActivity — eager catalog load + ItemRegistry sync

```kotlin
val catalog: Hero3Catalog by lazy {
    Hero3CatalogLoader.load(AndroidAssetReader(this)).also {
        Hero3CatalogProvider.installCatalog(it)
        ItemRegistry.registerExtra(Hero3CatalogBridge.catalogItemPool(it))  // R82
    }
}

// onCreate: catalog 강제 트리거 → provider + extras 자동 등록
try { catalog } catch (_: Throwable) { }
```

### 2.4 MapWalkScene encounter → catalog 우선

```kotlin
val catalog = Hero3CatalogProvider.get()
val leaderLvl = gameState.loadParty().firstOrNull()?.level ?: 1
val enemyId = catalog
    ?.let { Hero3CatalogBridge.randomCatalogEnemyId(it, leaderLvl) }
    ?: EncounterTable.rollEnemy(m.id)?.id
```

catalog 설치 시 161 enemies 풀, 미설치 시 기존 EncounterTable.

### 2.5 ForgeScene matching 확장

`ItemRegistry.all` → `ItemRegistry.allWithExtras()`. 카탈로그 등록 item 도 input/output 매칭에 포함되어 80 recipes 의 매칭 성공률 대폭 향상.

## 3. Tests

| Suite | Before | After |
|---|---|---|
| Hero3CatalogLoaderTest | 24 | 24 |
| **Hero3CatalogBridgeTest** | 5 | **7** (+2 R82) |
| Hero3CatalogProviderTest | 4 | 4 |
| **app subtotal** | 33 | **35** |
| engine-core (5 suites) | 34 | 34 |
| **TOTAL** | 67 | **69 / 69 PASS** |

`:app:assembleDebug` BUILD SUCCESSFUL 5s.

### 3.1 신규 Bridge tests

- `r82_catalog_item_pool_extends_inventory_registry` — 50+ unique items, all `h3_item_` prefix
- `r82_random_catalog_enemy_id_matches_h3_n_pattern` — level 10 input → "h3_n_..." 반환

## 4. 진행률 변화

| 영역 | R81 | R82 |
|---|---|---|
| Catalog/Data layer | 95% | **96%** |
| **데이터-Scene 통합** | **60%** | **75%** (ItemRegistry + MapWalk + Forge 모두 catalog-fed) |
| Playable Remake | 60% | **70%** (random battle 이 catalog 161 enemies 사용) |
| **종합 remake** | **77-79%** | **82-84%** |

## 5. 게임 플레이 흐름 (R82 통합 후)

1. App start → catalog lazy 로드 → ItemRegistry 에 catalog items 등록 + provider install
2. MainMenu → MapWalk → 이동 중 random encounter
   - **161 catalog enemies 풀**에서 player lvl ±5 random pick
   - `SceneRequest.BattleEnemy("h3_n_NNN")` → BattleScene catalog-fed enemy
3. MainMenu → 단조 → 80 recipes 중 craft 가능한 것은 표시 즉시 craft
   - ItemRegistry 가 catalog items 포함하므로 매칭 성공률 대폭 향상
4. NPC 인접 시 `region_shop_N` → R74 5 region shops (R81)

→ R56-R78 분석 데이터의 ~75% 가 실제 게임 플레이 경로에서 사용.

## 6. R83 권장

1. ⭐⭐⭐⭐⭐ **BattleScene combat formula** — R63 24 stat enum + skill effect_v2 + element advantage
2. ⭐⭐⭐⭐ **QuestRegistry catalog-fed** (44+ quests)
3. ⭐⭐⭐⭐ **BattleScene drop integration** — enemy 처치 시 R74 drop_dat record 의 primary/secondary 사용
4. ⭐⭐⭐ **MapWalkScene region_shop NPC 좌표** map 데이터와 동기화
5. ⭐⭐⭐ **ForgeScene gold cost / multi-qty** (recipe byte 정밀화)
6. ⭐⭐ SMAF Phase B / LLM 번역 (정책)

## 7. 변경 파일

```
M android/app/src/main/java/com/hero3/remake/MainActivity.kt
M android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogBridge.kt
M android/app/src/main/java/com/hero3/remake/scene/ForgeScene.kt
M android/app/src/main/java/com/hero3/remake/scene/MapWalkScene.kt
M android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogBridgeTest.kt
M engine-core/src/commonMain/kotlin/com/hero3/remake/engine/Item.kt
A docs/h3/ghidra-round82-itemregistry-catalog-encounters-2026-05-19.md
```
