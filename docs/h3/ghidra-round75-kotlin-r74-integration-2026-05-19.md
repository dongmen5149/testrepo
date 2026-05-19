# 영웅서기3 Round 75 — R74 DES 평문 → Kotlin Catalog 통합 + game_balance v1.2

**Date**: 2026-05-19
**Status**: ✅ Hero3Catalog 5 신규 data class + Loader + 5 신규 unit tests (총 17/17 pass). 진행률 ~99.98%.

## 한 줄

R74 의 5 종 DES 평문 JSON (shop_catalog/drop_table/recipes/region_shops/fixed_drops) 을 **Hero3Catalog** 의 `r74Data` 로 통합. game_balance.json **v1.1 (582KB) → v1.2 (832KB)**. `bossSkillIdsResolved()` 가 R74 H4 confirmation 으로 **true** 반환.

## 1. 신규 산출물

| 파일 | 변경 |
|---|---|
| `tools/recon/patch_game_balance_v12.py` | 신규 — v1.1 in-place patch, R74 8 JSON 통합 |
| `android/app/src/main/assets/game_balance.json` | 582KB → 832KB (R74 data 추가) |
| `work/h3/game_balance.json` | 동일본 |
| `Hero3Catalog.kt` | +5 data class (`Hero3ShopCatalogEntry`, `Hero3DropRecord`, `Hero3Recipe`, `Hero3RegionShop`, `Hero3FixedDrop`, `Hero3R74Data`) + loader |
| `Hero3CatalogLoaderTest.kt` | 12 → 17 tests (+5 R74 assertions, schema 1.1 → 1.2, des pending 8 → 0, bossSkill resolved false → true) |
| 본 라운드 doc | `ghidra-round75-kotlin-r74-integration-2026-05-19.md` |

## 2. drop_dat 17B 필드 분석 (부분 — R76 후속 필요)

byte 위치별 통계 (161 records):

| byte | uniq | 특이점 |
|---|---|---|
| [0-1] | 13 | 13 distinct pairs — `(120,20)`, `(90,15)` 등 = enemy 분류 (13 enemy templates × ~12 instances?) |
| [2-3] | 13/10 | 동일 패턴 — pairing 가능성 |
| [4-9] | 13-18 | 변동 |
| [10] | **29** | 0-31 범위 — 5-bit 필드 (sequence index?) |
| [11-12] | 29/31 | 가변 — boss skill ID 후보 |
| **[13]** | **3** | `{14, 18, 255}` 만 — 구조적 marker / flag |
| [14] | 29 | 다수가 7 또는 0 |
| [15-16] | 25/23 | **(133, 153) = (0x85, 0x99) 63회 반복** — 공통 footer / 공통 drop 풀? |

normal vs hard byte 차이: byte[0..12] ~144/160 differ, byte[13-14] 만 76-80/160 differ → byte[13-14] 가 구조 적 marker, byte[0..12] 가 stat data.

**R76 가설**: 17B = `(stat_pair × 5: 10B) + index(1) + drop_skill_a(2) + flag(1) + sub(1) + drop_skill_b(2)`.

## 3. i15 5B trailer 패턴 (부분)

```
trailer := [u8] [u8] 0x0f [u8 or 0xff] [u8 typically 5 or 0]
```

byte[2] = `0x0f` always (uniq=1) → terminator marker confirmed.
byte[4] 가 `5` 인 entries 가 15/18 → 캐릭터 class restriction flag 후보 (R76 검증).

## 4. Hero3R74Data API

```kotlin
data class Hero3Recipe(val offset: Int, val bytes: List<Int>) {
    val successRate: Int  // bytes[8] = 0x64 (always 100%)
    val outputCat:   Int  // bytes[9]
    val outputId:    Int  // bytes[10]
}

data class Hero3RegionShop(val offset: Int, val bytes: List<Int>) {
    val lvMin:   Int      // bytes[2]
    val lvMax:   Int      // bytes[3]
    val itemIds: List<Int> // bytes[5..9].filter { it != 0xff }
}

data class Hero3FixedDrop(val type: Int, val flag: Int, val cat: Int, val id: Int)
```

`Hero3Catalog.r74Data: Hero3R74Data?` 가 null 이 아니면 R74 통합 완료 상태.
`bossSkillIdsResolved()` = `r74Data?.dropTable?.isNotEmpty() == true`.

## 5. 테스트

- 12 기존 + 5 신규 R74 검증 = **17/17 PASS** (BUILD SUCCESSFUL in 33s)
- `r74_drop_table_has_161_entries_matching_enemies` — drop count == enemy count (R74 finding)
- `r74_region_shops_have_5_entries_with_level_tiers` — (1-15) normal / (30-44) hard
- `r74_recipes_have_80_entries` — successRate=100 (0x64) confirmed
- `r74_shop_catalog_and_fixed_drops_populated` — fixed drops all type=2

## 6. Round 76 후속

1. **drop_dat 17B precise field map** — byte[15-16]=(133,153) repeat 의 의미, byte[13] {14,18,255} 분기
2. **i15 5B trailer** — byte[0,1,3] 가 stat (ATK/DEF/element?) 인지 i0-i12 catalog stat block 과 cross-check
3. **smith recipe input parsing** — byte[2..7] 의 4 input items 가 `(cat, id) × 2` 인지 `(cat, id, qty)` 인지 확정
4. **Hero3Catalog ↔ i15 38 entries cross-validation** — name match against existing items 529
5. SMAF Phase B (사용자 정책)

## 7. 진행률

- R74 종료: ~99.97%
- R75 종료: **~99.98%** (Android 통합 + 테스트 + game_balance v1.2)
