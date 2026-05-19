# 영웅서기3 Round 84 — Catalog 115 Quests 통합 + Viewer Quests tab

**Date**: 2026-05-19
**Status**: ✅ **71/71 tests** + APK BUILD SUCCESSFUL. R58/R62 의 4 quest 파일 (총 115 entries) 가 Hero3Catalog 에 정식 로딩 + CatalogViewer 에서 surface.

## 1. 한 줄

R58/R62 가 디코드한 **quest_00/01/10/11_dat 4 파일 × 115 entries** (노력의 증명1, 수상한 동굴, 엔자크의 영광 등) 를 Hero3Catalog 의 `questFiles` 로 통합. CatalogViewer 에 신규 **Quests** tab 추가.

## 2. 신규 / 변경

### 2.1 Hero3Catalog data class 확장

```kotlin
data class Hero3CatalogQuestEntry(file: String, pos: Int, name: String)
data class Hero3CatalogQuestFile(file: String, sizeBytes: Int, nEntries: Int, entries: List<Hero3CatalogQuestEntry>)

data class Hero3Catalog(
    ...,
    val questFiles: List<Hero3CatalogQuestFile> = emptyList(),  // R84 신규
)
```

### 2.2 Loader.parseQuestFiles(obj)

game_balance.json 의 `quests.files.<filename>.entries` 배열을 파싱하여 4 파일 × N entries 구조로 변환. `quests.item_xref` (R62, 21 items) 는 별도 처리 (R85+).

### 2.3 CatalogViewer 변경

- Tab 10 → **11** (신규 QUESTS 탭)
- Quests tab: 4 파일 헤더 + 각 entry "pos=NNNN  name" 형식 (115 줄)
- Overview 에 quest 카운트 추가: "R84 catalog quests: 115 entries across 4 files"

## 3. 데이터 분포 (R58/R62 재확인)

| file | nEntries | 대표 entries |
|---|---|---|
| quest_00_dat | 37 | 노력의 증명1, 수상한 동굴, 길잃은 소녀 |
| quest_01_dat | 7 | 엔자크의 영광, 영혼의 시, 로우엔의 치안 |
| quest_10_dat | 38 | 수상한 보석, 낯익은 여자, 옛 친구의 부탁 |
| quest_11_dat | 33 | 집결의 도구, 하찮은 임무, 연금협회의 의뢰 |
| **합계** | **115** | |

## 4. Tests

LoaderTest 24 → **25** (`r84_catalog_quests_loaded_115_entries_across_4_files`):
- 4 files / 115 total entries 확인
- quest_00_dat 의 첫 entry = "노력의 증명1"

| Suite | Tests |
|---|---|
| **Hero3CatalogLoaderTest** | **25** (+1) |
| Hero3CatalogBridgeTest | 8 |
| Hero3CatalogProviderTest | 4 |
| **app subtotal** | **37** |
| engine-core (5 suites) | 34 |
| **TOTAL** | **71 / 71 PASS** |

`:app:assembleDebug` BUILD SUCCESSFUL 5s.

## 5. 진행률 변화

| 영역 | R83 | R84 |
|---|---|---|
| Catalog/Data layer | 97% | **98%** |
| **데이터-Scene 통합** | **80%** | **82%** (Quests viewer) |
| Playable Remake | 74% | 74% (UI surface 만, 게임 logic 미연결) |
| **종합 remake** | **84-86%** | **85-87%** |

## 6. 한계 + R85 권장

### 6.1 알려진 한계 (R84 범위 밖)

- catalog Quest entry 는 `pos + name` 만 — desc / reward / 종료조건 정보 없음 (원본 데이터에 거의 없음)
- 4 quest 파일 중 어느 게 메인/사이드인지 메타 미분류
- QuestRegistry (4 hardcoded) ↔ catalog 115 entries 연결 미구현 — name 매칭 시도하면 일부는 mappable

### 6.2 R85 권장

1. ⭐⭐⭐⭐⭐ **QuestRegistry catalog-fed 본격** — 115 entries 중 hardcoded 4 와 동일 한국어 이름 매칭 (`guardian_hunt` ↔ `고대 가디언 토벌` 등)
2. ⭐⭐⭐⭐ **R66 skill effect_v2 BattleScene 통합** — 25/105 skills 의 element/debuff 데이터 사용
3. ⭐⭐⭐⭐ **CatalogViewerScene Skills tab** — effect_v2 detail panel (rank/n_debuffs/slot1-3 codeName)
4. ⭐⭐⭐ R62 item_xref 21 quest-item 매핑 surface
5. ⭐⭐⭐ ForgeScene gold cost (R74 byte 정밀화)
6. ⭐⭐ SMAF Phase B / LLM 번역 (정책)

## 7. 변경 파일

```
M android/app/src/main/java/com/hero3/remake/catalog/Hero3Catalog.kt
M android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt
M android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt
A docs/h3/ghidra-round84-quest-catalog-viewer-2026-05-19.md
```
