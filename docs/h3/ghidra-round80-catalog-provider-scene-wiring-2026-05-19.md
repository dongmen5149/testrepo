# 영웅서기3 Round 80 — Hero3CatalogProvider + Scene 점진적 통합

**Date**: 2026-05-19
**Status**: ✅ **33/33 tests + APK BUILD SUCCESSFUL**. Catalog 데이터가 처음으로 실제 scene 코드 경로에 통합됨.

## 1. 한 줄

R79 의 Hero3CatalogBridge 위에 **Hero3CatalogProvider** singleton 추가. MainActivity 가 `catalog` lazy 로드 시 자동 install. **BattleScene / ShopScene / CatalogViewerScene** 3개를 catalog-fed 모드로 전환 (기존 동작 보존, opt-in 패턴).

## 2. 신규 산출물

### 2.1 `Hero3CatalogProvider.kt` (catalog 모듈)

```kotlin
object Hero3CatalogProvider {
    fun install(loader: () -> Hero3Catalog)  // MainActivity lazy 진입점
    fun installCatalog(catalog: Hero3Catalog)  // 테스트/직접 주입
    fun get(): Hero3Catalog?                  // null-safe 접근
    fun require(): Hero3Catalog               // 필수 경로
    fun reset()                               // 테스트 정리
}
```

double-checked locking 으로 thread-safe init.

### 2.2 MainActivity wiring (1 줄 추가)

`catalog` lazy property 가 로드 후 자동 `Hero3CatalogProvider.installCatalog(it)` 호출.

### 2.3 BattleScene → catalog-fed enemy (opt-in by ID pattern)

```kotlin
val def = forcedEnemyId?.let { id ->
    catalogEnemy(id) ?: EnemyRegistry.get(id)   // ← R80: catalog 우선
} ?: EnemyRegistry.random(party.first().level)
```

- `forcedEnemyId == "h3_n_NNN"` → R56 normal enemy 161개 중 매칭
- `forcedEnemyId == "h3_h_NNN"` → R56 hard enemy
- 그 외 → 기존 EnemyRegistry (placeholder 13)

### 2.4 ShopScene → region_shop pattern

```kotlin
private val stock: List<Item> =
    regionShopStock(npcId) ?: ShopRegistry.stock(npcId, gameState)
```

- `npcId == "region_shop_N"` → R74 의 5 catalog shops 사용 (lv 1-15 ~ 26-40 tiers)
- 그 외 → 기존 ShopRegistry (merchant_bo / merchant_jin)

### 2.5 CatalogViewerScene — 3 신규 tab + overview 갱신

탭 7 → 10:
1. ✨ **Shop Catalog** (i15 38 entries with EUC-KR descriptions)
2. ✨ **Forge Recipes** (80 entries with resolved input count + output name)
3. ✨ **Region Shops** (5 shops × level tier × resolved item names)
4. ✅ DES 탭은 "pending=0" 시 R73 success 메시지 표시

Overview 에 R74 카운트 (shop catalog/recipes/region shops/drop tables) 4 줄 추가.

## 3. Tests + Build

| Suite | Tests |
|---|---|
| Hero3CatalogLoaderTest | 24 |
| Hero3CatalogBridgeTest | 5 |
| **Hero3CatalogProviderTest (신규)** | **4** |
| **합계** | **33/33 PASS** |

```
get_returns_null_before_install
require_throws_before_install
install_runs_loader_once_then_caches   (double-init 무시)
installCatalog_replaces_instance
```

`:app:assembleDebug` **BUILD SUCCESSFUL 11s** — APK 생성까지 통과.

## 4. 진행률 변화

| 영역 | R79 | R80 |
|---|---|---|
| Catalog/Data layer | 92% | **94%** |
| **데이터-Scene 통합** | **30%** | **50%** (BattleScene/ShopScene/CatalogViewer 직접 사용) |
| Playable Remake | 50% | **55%** |
| **종합 remake** | **70-72%** | **74-76%** |

## 5. 통합 진행 trace

R74 (8 DES 평문 파싱)
  → R75 (Hero3Catalog data class)
  → R76-R78 (정밀화 + audit)
  → R79 (Hero3CatalogBridge — engine-core 타입 변환)
  → **R80 (Hero3CatalogProvider + scene wiring)** ← 여기

scene 들이 처음으로 R56-R78 데이터를 실제 게임 경로에서 사용.

## 6. R81 권장 (계속)

1. ⭐⭐⭐⭐⭐ **InventoryScene 단조 메뉴** — `forgeRecipesFromCatalog` 활용한 craft UI
2. ⭐⭐⭐⭐ **BattleScene combat formula** — 24-stat enum 적용, skill effect_v2 통합
3. ⭐⭐⭐⭐ **EncounterTable** → drop archetype 기반 (region+lvl → 161 enemy 풀)
4. ⭐⭐⭐ **QuestRegistry** catalog-fed (44+ quests)
5. ⭐⭐⭐ **MapWalkScene** → encounter trigger 가 catalog enemies 사용
6. ⭐⭐ NpcRegistry 에 "region_shop_N" NPCs 추가
7. ⭐⭐ SMAF Phase B / LLM 번역 (정책)

## 7. 변경 파일 목록

```
M  android/app/src/main/java/com/hero3/remake/MainActivity.kt
M  android/app/src/main/java/com/hero3/remake/scene/BattleScene.kt
M  android/app/src/main/java/com/hero3/remake/scene/ShopScene.kt
M  android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt
A  android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogProvider.kt
A  android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogProviderTest.kt
```
