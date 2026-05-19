# 영웅서기3 Round 76 — Smith Recipe 완전 디코드 + i15↔Catalog 38/38 + drop_dat 17B 상관분석

**Date**: 2026-05-19
**Status**: ✅ Smith recipe field map 확정, i15 38 entries 모두 catalog 매칭, drop_dat 17B 통계적 상관 식별. 진행률 ~99.99%.

## 한 줄

Smith recipe 11B = `[const 9,0] [3 input slots × (cat,id), 0xff=empty] [const 100%] [output (cat,id)]`. output_id 가 i{cat}_dat 의 N번째 entry 와 1:1 매칭 — **80 recipe → 실제 아이템 이름 100% 해결 가능**. i15 38 entries **38/38 catalog clean_names exact match**.

## 1. 신규 산출물

| 파일 | 변경 |
|---|---|
| `Hero3Catalog.kt` | +`Hero3ItemRef` data class, `Hero3Recipe.inputs/output` 확장, `Hero3Catalog.resolveItem()` / `resolveShopCatalogEntry()` |
| `Hero3CatalogLoaderTest.kt` | 17 → **20 tests** (3 신규 R76, **BUILD SUCCESSFUL 20/20 PASS**) |
| `docs/h3/SESSION_HANDOFF.md` | R76 결과 반영 |

## 2. Smith Recipe Field Map 확정

```
recipe[11B] = [0]=0x09 const  [1]=0x00 const
              [2,3]=(in1_cat, in1_id)
              [4,5]=(in2_cat, in2_id)
              [6,7]=(in3_cat, in3_id)
              [8]=0x64 (100% success rate const)
              [9]=output_cat   [10]=output_id
```

- byte[0]=9 80/80 ✓, byte[1]=0 80/80 ✓, byte[8]=100 80/80 ✓
- `cat=0xff (255)` → slot 미사용 (byte[2]: 56/80 = 0xff = 1-input recipes)
- output_id 는 i{cat}_dat 의 list index 와 1:1 매칭:
  - recipe[0] → i18_dat[0] = **"포션"**
  - recipe[1] → i18_dat[1] = **"하이포션"**
  - recipe[3] → i0_dat[3] = **"강화가죽모자"**
  - recipe[9] → i17_dat[20] = **"영혼사슬"**

output cat 분포: i18(48), i17(9), i0(4), i2/i4(3), i3/i5/i1/i11(2), i9/i6/i7/i8/i10(1) = endgame consumable + equipment crafting tree

## 3. i15 ↔ Catalog 38/38 Exact Match

R74 i15 38 EUC-KR names → catalog `clean_name` exact match 모두 성공:

| i15 name | 카탈로그 file | pos |
|---|---|---|
| 붉은머리띠 | i0_dat | 368 |
| 오웬스피어 | i4_dat | 374 |
| 워락 | i8_dat | 388 |
| 데스블러드 | i9_dat | 390 |
| 영혼사슬 | i17_dat | (smith recipe 출력 일치) |
| 데몬블레이드 | i5_dat | (final tier) |

→ i15_dat 은 **고급 아이템 카탈로그** (각 카테고리의 후반부 high-tier 아이템만 모음, 레벨 10-57)

## 4. drop_dat 17B 통계적 상관분석

161 records vs R56 enemy stats (Pearson r):

| byte | vs enemy_lvl | vs enemy_hp_max | 해석 |
|---|---|---|---|
| [8]  | **+0.642** ⭐ | +0.260 | level-scaled value |
| [10] | **+0.601** ⭐ | **+0.683** ⭐ | HP-scaled value (drop count?) |
| [12] | **-0.562** ⭐ | -0.292 | inverse level (drop rate?) |
| [13] | +0.356 | **+0.627** ⭐ | HP-scaled |
| [14] | +0.360 | **+0.627** ⭐ | HP-scaled |

drop record 1,2,3 (enemy level 30, 34, 34) bytes[0..9] **완전 동일** → bytes[0..9] = **enemy archetype 공유 template**, bytes[10..16] = **per-enemy 변동분**.

**R77 가설**: 17B = `[10B shared archetype loot pool] + [1B index] + [6B per-enemy overrides]`.

## 5. i15 5B trailer (보류)

trailer 추출 heuristic 이 body EUC-KR bytes 와 충돌 — `; ` 마커가 본문 내에도 빈번하게 출현하여 신뢰할 수 없음. R74 의 `[u8][u8][0x0f][u8][u8]` 기록 외에 정밀화 보류 (R77+).

## 6. 신규 Kotlin API

```kotlin
data class Hero3ItemRef(val cat: Int, val id: Int) {
    val isEmpty: Boolean              // cat == 0xff
    val catalogFile: String           // "i{cat}_dat"
}

val Hero3Recipe.inputs: List<Hero3ItemRef>  // non-empty slots only
val Hero3Recipe.output: Hero3ItemRef

fun Hero3Catalog.resolveItem(ref): Hero3Item?
fun Hero3Catalog.resolveShopCatalogEntry(e): Hero3Item?
```

## 7. R77 후속

1. drop_dat 17B precise field map (shared template + per-enemy overrides)
2. i15 5B trailer (정확한 boundary detection)
3. Hero3Catalog 의 region_shops itemIds 가 어떤 카테고리 ID 인지 (cat 추정 필요 — 현재 raw id 만)
4. getitem_dat 96 entries 의 cat 분포 (15/17/18) → quest 보상인지 dungeon drop 인지 분류
5. SMAF Phase B (정책 대기)

## 8. 진행률

- R75 종료: ~99.98%
- R76 종료: **~99.99%** (Recipe 완전 디코드 + catalog 통합)
