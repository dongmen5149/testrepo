# 영웅서기3 Round 79 — Catalog Bridge: 데이터→게임 통합 시작

**Date**: 2026-05-19
**Status**: ✅ **29/29 tests pass** (24 Loader + 5 Bridge). R78 audit 후 첫 통합 작업.

## 1. 한 줄

R78에서 식별한 "분석 데이터가 게임 코드에 통합되지 않은 격차"를 메우기 위해 **Hero3CatalogBridge** 신규 모듈 추가. 161×2 enemies / 5 region shops / 80 recipes 를 engine-core 타입(EnemyDef / Item / 등)으로 변환하는 layer.

## 2. 신규 산출물

### 2.1 `Hero3CatalogBridge.kt` (app 모듈)

3 핵심 API:
```kotlin
object Hero3CatalogBridge {
    fun enemiesFromCatalog(c: Hero3Catalog, hardMode: Boolean = false): List<EnemyDef>
    fun shopStockFromCatalog(c: Hero3Catalog, shopIdx: Int, hardMode: Boolean = false): List<Item>
    fun forgeRecipesFromCatalog(c: Hero3Catalog, hardMode: Boolean = false): List<ResolvedRecipe>
}
```

설계 원칙:
- **engine-core 비파괴**: 기존 `EnemyRegistry`/`ShopRegistry` 보존, 새 API 병행
- **opt-in 통합**: scene 들이 점진적으로 catalog-fed 데이터로 전환 가능
- **R74 데이터 없으면 빈 list 반환**: 호출자가 fallback 결정

### 2.2 변환 디테일

**enemy 변환** (R56 19B stat → EnemyDef):
- name, hpMax, atk = catalog stats 직접 사용
- def: R56에서 미해독 → `hpMax/8 + lvl/4` 추정
- expReward/goldReward: R56 `exp_gold` BE u16 → high byte / low byte split (R69 가설)
- spriteDir: `enemy/eXXXX_bm` (idx + 0x100 hex)
- dropTable: R74 drop_dat primary/secondary, common-pool sentinel (133,153) skip

**shop 변환** (R74 region_shop + i15 catalog):
- shop.itemIds = i15 indices (R77 확인) → i15 entry name 으로 ItemRegistry 매칭
- ItemRegistry 미등록은 placeholder Item 생성 (price=100, MATERIAL kind)

**recipe 변환** (R74 smith + R76 resolveItem):
- ResolvedRecipe = (recipe, inputs: List<Hero3Item>, output: Hero3Item?)
- 0xff cat slot 자동 필터 (R76)

## 3. Tests (5/5 신규)

```
Hero3CatalogBridgeTest:
  bridge_converts_161_normal_enemies               ✓
  bridge_converts_161_hard_enemies                 ✓
  bridge_shop_stock_resolves_for_5_region_shops    ✓
  bridge_forge_recipes_resolve_to_real_items       ✓
  bridge_drop_table_excludes_common_pool_sentinel  ✓  (259 drop entries)
```

총 tests: 24 (Loader) + 5 (Bridge) = **29/29 PASS**.

## 4. 진행률 영향 (R78 audit 대비)

| 영역 | R78 | R79 |
|---|---|---|
| Catalog/Data layer | 88% | **92%** (Bridge 추가 +4%p) |
| **데이터-Scene 통합** | **15%** | **30%** (Bridge layer 완성, scene 미연결) |
| 종합 | ~65-70% | **~70-72%** |

데이터 변환 layer 가 완성됐으므로 R80~ 에서 scene 들을 BridgeAPI 로 전환하면 진행률이 빠르게 올라감.

## 5. R80 권장 (다음 라운드 — Scene 통합)

1. **BattleScene** → 시작 시 Hero3Catalog 1회 로드 + `enemiesFromCatalog` 사용
   - 기존 `EnemyRegistry.random()` 을 wrap: catalog 가 있으면 161 enemies 풀, 없으면 fallback
2. **ShopScene** → `npcId` 가 `"region_shop_N"` 패턴이면 `shopStockFromCatalog(catalog, N)` 사용
3. **InventoryScene** → "단조" 메뉴 추가, `forgeRecipesFromCatalog` 표시
4. **CatalogViewerScene** → R74 recipes/shops/drops 섹션 surface
5. **Hero3CatalogProvider** singleton (app-level) — Activity-scoped 1회 로드 캐시

## 6. 알려진 한계 (R80+ 작업)

- `inferDef()` 는 휴리스틱 — R63 24-stat-enum 의 P_DEF (0x07) 직접 사용 가능 시 정밀해짐
- exp/gold split 가설 (R69 4그룹) 검증 필요
- dropTable 의 itemId 명 (`h3_drop_p_NNN_MMM`) 은 placeholder — R80+ 에서 byte → 실 itemId 매핑
- Hard mode `enemiesHard` 가 R56 데이터로 161 entries 확정인지 검증 필요
