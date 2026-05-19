# 영웅서기3 Round 77 — Drop Archetype (18 클러스터) + Region Shop ↔ i15 Xref + i15 Trailer 일부

**Date**: 2026-05-19
**Status**: ✅ drop_dat 17B = 10B archetype template + 7B per-enemy overrides 구조 확정. region_shops itemIds = i15 indices 검증. **23/23 tests pass**. 진행률 ~99.995%.

## 한 줄

drop_dat 161 records 가 **bytes[0..9] 기준 18 distinct archetype 클러스터**로 그룹화 (low-level 27 → boss 8). bytes[13] **{14=normal, 18=elite, 255=box/boss}** class flag 확정. region_shops 의 itemIds 가 **i15 (shop catalog) 의 index**임을 검증 (lv 1-15 shop = i15[4,8]: 얼음비늘장갑/바람가죽모자).

## 1. 신규 산출물

| 파일 | 변경 |
|---|---|
| `Hero3Catalog.kt` | `Hero3DropRecord` 에 7 accessor (archetypeTemplate/subTier/primaryDrop/classFlag/variant/secondaryDrop/isNormalEnemy/isElite/isBossOrBox) + `Hero3Catalog.dropArchetypes()` + `resolveShopItems()` |
| `Hero3CatalogLoaderTest.kt` | 20 → **23 tests, 23/23 PASS** (3 신규 R77) |

## 2. drop_dat 17B Field Map 최종

```
record[17B] := [0..9]   10B archetype loot template  (18 distinct)
               [10]     sub-tier rank (0..7)
               [11..12] primary drop pair (or common-pool sentinel (133,153)=0x8599)
               [13]     class flag: 14=normal, 18=elite, 255=box/boss
               [14]     per-enemy variant
               [15..16] secondary drop pair (또는 bytes[11..12] 중복)
```

### 2.1 18 Archetype Clusters

| 크기 | level range | hp range | 대표 enemies |
|---|---|---|---|
| 27 | 6-18 | 32-94 | 아스크란가드, 와일드쿠퍼, 스컬워커 |
| 24 | 29-34 | 50-63 | 코르버스워리어, 솔티안워리어, 솔티안위자드 |
| 22 | 19-28 | 40-127 | 솔티안로그, 도적, 코르버스로그 |
| 22 | 35-37 | 53-150 | 아스크란체이서, 아스크란엑셀, 데드솔저 |
| 19 | 39-43 | 58-175 | 아스크란템플러, 솔티안워락, 얼티밋쿠퍼 |
| 11 | 1-5 | 27-36 | 포레스트쿠퍼, 먼지, 벌, 야생쥐 (튜토리얼) |
| 8 | 65-67 | 338-360 | {카이저골렘, {시바, {와일드스쿠툼 (보스) |
| 8 | 2-37 | 27-54 | '박스 8개 (treasure boxes) |
| 6 | 11-30 | 43-57 | 중대장 시리즈 (모두 zero template) |
| 3 | 32-34 | 49-50 | '쥐 '벌 '유령 (special items) |
| 6 × 1 | 단일 entries | — | (각자 고유 archetype) |

### 2.2 byte[13] 분류 분포

| flag | 의미 | 출현 |
|---|---|---|
| 14 (0x0e) | 일반 적 | 다수 (low-level archetypes 100%) |
| 18 (0x12) | 엘리트 / 고급 | mid-high (lvl 39+ archetypes 우세) |
| 255 (0xff) | 보스 / 보물상자 | 8 (`{카이저...` archetype 전체) |

## 3. Region Shop ↔ i15 Xref 검증

shop.bytes[5..9] 의 각 byte (≠ 0xff) = i15 catalog 의 index:

| shop | level | itemIds | i15 entries |
|---|---|---|---|
| 0 | 1-15  | [4, 8] | 얼음비늘장갑, 바람가죽모자 |
| 1 | 8-22  | [1, 4, 8] | 오웬스피어, 얼음비늘장갑, 바람가죽모자 |
| 2 | 16-30 | [1, 4, 5, 8] | + 소울퀘이드 |
| 3 | 21-35 | [1, 4, 5, 8] | (동일) |
| 4 | 26-40 | [1, 2, 4, 5, 8] | + 워락 |

→ shop = NPC 가 파는 고급 카탈로그. 고레벨 지역에서 점점 더 많은 아이템 unlock.

## 4. i15 5B trailer 부분 정밀 (18/37)

```
trailer = [stat1] [stat2] 0x0f [stat3 or 0xff] [class_flag 5 or 0]
```

- byte[2] = `0x0f` (uniq=1) **확정 marker**
- byte[0,1] = small ints 0-12 = stat 값 (ATK1/ATK2?)
- byte[4] = `5` for 15/18 entries (class restriction code 5 = all-class 추정)

entries 18+: trailer marker `0x14` (= 0x0e?) 로 변경 가능 — i15 후반부 (level 30+ 아이템) 구조 차이. R78 정밀화 권장.

## 5. 신규 Kotlin API

```kotlin
// Hero3DropRecord
val archetypeTemplate: List<Int>       // bytes[0..9]
val subTier: Int                       // bytes[10]
val primaryDrop: Pair<Int, Int>        // (bytes[11], bytes[12])
val classFlag: Int                     // bytes[13]
val variant: Int                       // bytes[14]
val secondaryDrop: Pair<Int, Int>      // (bytes[15], bytes[16])
val isNormalEnemy: Boolean             // classFlag == 14
val isElite: Boolean                   // classFlag == 18
val isBossOrBox: Boolean               // classFlag == 255

// Hero3Catalog
fun dropArchetypes(): Map<List<Int>, List<Hero3DropRecord>>
fun resolveShopItems(shop: Hero3RegionShop): List<Hero3ShopCatalogEntry>
```

## 6. R78 후속

1. **i15 trailer 정밀** (entries 18-37 의 0x14 marker 구조)
2. **getitem_dat 96 entries 분류** (cat 15/17/18 → quest vs dungeon drop)
3. **drop archetype ↔ enemy file map** (bytes[0..9] template 의 의미: gold/exp BE u16?)
4. **bytes[11..12] / [15..16] item ref 디코딩** (0x8599 sentinel 의 의미)
5. (정책 승인 시) SMAF Phase B

## 7. 진행률

- R76 종료: ~99.99%
- R77 종료: **~99.995%** (drop_dat structural decode + shop xref + i15 partial trailer)
