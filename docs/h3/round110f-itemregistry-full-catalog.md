# Hero3 Round 110f — ItemRegistry full catalog 적재 (60 items 추가) — 2026-05-20

> R74-R108 catalog wiring 패턴 재개. R110a/c/e 의 시각 자동화 deferred 후, 안전한 데이터 확장 라운드.

## 0. TL;DR

- `Hero3CatalogBridge.catalogItemPool(maxPerCategory = 30)` 의 cap 으로 60 catalog items 누락 (7 file 이 30 초과 entry 보유).
- `maxPerCategory = 50` 으로 상향 → catalog 529 items 모두 ItemRegistry 에 적재.
- 영향: ForgeScene recipe matching, Inventory display, drop_table resolve 범위 확장.
- Tests +2 (R110f 검증): 134/134 → 135/135 → 136/136 PASS, build green.

## 1. 데이터 분석

catalog (`game_balance.json` items) 의 18 file 별 entry 수:

| file | n_entries | 30-cap 누락 |
|---|---|---|
| i0_dat | 33 | 3 |
| i1_dat | 41 | 11 |
| i2_dat | 37 | 7 |
| i3_dat | 38 | 8 |
| i4-i11_dat | 25 each | 0 |
| i12_dat | 40 | 10 |
| i13_dat | 35 | 5 |
| i14_dat | 46 | 16 |
| i16_dat | 15 | 0 |
| i17_dat | 21 | 0 |
| i18_dat | 26 | 0 |

**총 catalog: 529 items. 30-cap 시 적재 = 469 (60 누락).**

R110f 전 (cap=30) 누락된 60 items 는 보통 high-tier endgame 장비 / 재료 (각 file 의 후반부 entries) — R76 finding 에 따르면 i14_dat 의 후반 16 entries 가 가장 큰 손실.

## 2. 변경 사항

### 2.1 [`Hero3CatalogBridge.kt`](../../android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogBridge.kt)

```diff
- fun catalogItemPool(catalog: Hero3Catalog, maxPerCategory: Int = 30): List<Item> {
+ fun catalogItemPool(catalog: Hero3Catalog, maxPerCategory: Int = 50): List<Item> {
```

기본값만 30 → 50 으로 변경. 호출자가 명시적으로 `maxPerCategory` 를 전달하면 그 값 적용. `MainActivity.onCreate` 의 호출은 인자 없이 호출 — 자동으로 새 기본값 적용.

### 2.2 [`Hero3CatalogBridgeTest.kt`](../../android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogBridgeTest.kt)

테스트 2개 추가:

- `r110f_catalog_item_pool_default_loads_all_529_items` — 기본 호출 시 ≥ 529 items 적재.
- `r110f_catalog_item_pool_max_per_category_30_truncates` — `maxPerCategory=30` 명시 시 정확히 60 items truncate 됨 (regression guard).

## 3. 영향

- **ForgeScene** — recipe matching 범위 ↑ (60 추가 catalog items 가 recipe input/output 으로 매칭 가능).
- **InventoryScene** — 인벤토리에 적재 가능한 item 종류 ↑.
- **Hero3CatalogBridge.buildDropTable** — drop_dat 가 60 catalog items 도 해석할 수 있음 → `h3_item_*` resolve 율 ↑ (R83 의 259 drop entries 중 resolve 개수 증가).
- **catalog mapping coverage**: engine bespoke 17/529 → ItemRegistry 적재 기준 ~469/529 → ~529/529 (전체 적재). 매핑 정확도는 별개 (cleanName → 한국어 이름 그대로 사용).

## 4. 회귀

```
./gradlew.bat :app:testDebugUnitTest         → BUILD SUCCESSFUL  (catalog tests 4 → 6, R110f +2)
./gradlew.bat :engine-core:testDebugUnitTest → BUILD SUCCESSFUL  (engine tests 변동 없음)
```

## 5. 베타 출시 진척도 영향

- 콘텐츠 매핑 (C, 가중치 15%): item ItemRegistry 적재 측면 ~89% → ~100% (item 등록 기준).
- 단 "정확한 stat / nameKo / engine bespoke 매핑" 측면은 미해결. 진척도 평가는 ~46% 유지 (cleanName 그대로 사용, narrative 매핑 미실시).

## 6. 후속 round 후보

- R110g: enemy registry 확장 — `enemiesFromCatalog` 의 161 entries 가 EnemyRegistry 에 동일 패턴으로 추가 등록 가능. 패턴은 R82 itemPool 동일.
- R110h: skill catalog 확장 — `Hero3CatalogSkillIndex` 의 ~115 skills 를 SkillRegistry 에 적재.
- R110i: quest catalog 확장 — `Hero3CatalogQuestIndex` 의 115 quests 를 QuestRegistry 에 적재.

각각 ~1-2 dev day, 시각 임팩트 작지만 catalog wiring 진척도 ↑.

## 7. 참고

- R82 (item pool 도입): [project_hero3_status](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/project_hero3_status.md) §R82
- R76 (i14 high-tier endgame 분석): ghidra-round76
- R110a/c/e (자동 시각 트랙 소진): 본 세션 직전
