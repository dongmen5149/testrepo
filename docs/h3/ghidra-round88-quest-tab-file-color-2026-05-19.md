# Hero3 Round 88 — Quests 탭 file-색상 + QuestIndex byFile API (2026-05-19)

## 0. 한 줄 요약

R85/R87 의 `Hero3CatalogQuestIndex` 에 `byFile` / `fileColors()` / `colorOf(file)` API + 4-슬롯 ARGB 팔레트를 추가하고, `CatalogViewerScene` 의 Quests 탭이 `quest_00_dat / quest_01_dat / quest_10_dat / quest_11_dat` 4 파일을 amber / teal / lavender / soft-red 로 구분 렌더링. `rowsForTab` 을 `List<Row>` 구조로 작은 리팩터 — 다른 탭은 그대로 default body paint. 81/81 tests + APK BUILD SUCCESSFUL.

## 1. 동기 / 배경

R87 종료 시점 권장 작업 5종:
1. QuestRegistry catalogKey  
2. Skills detail panel  
3. R66 effect_v2 BattleScene  
4. ForgeScene gold cost  
5. **Quests tab file-색상** ← 본 라운드

R85 에서 quest index 의 `duplicates()` (★ 표기) 로 4 파일 교차 중복을 잡았지만, CatalogViewer 의 Quests 탭은 115 entries 가 흐름상 4 파일 헤더로만 구분되어 “지금 보고 있는 행이 어느 파일이냐” 가 한눈에 안 들어왔다. quest_00 (메인) / quest_01 (서브) / quest_10 (하드 메인) / quest_11 (하드 서브) 의 4 분할을 색으로 즉시 식별하게 만드는 것이 목표.

또한 `quest_item_xref` (R87) 와 향후 R66 effect_v2 BattleScene 통합 작업에서도 같은 파일 색을 재사용할 수 있게, 색상 정의를 Scene 코드가 아니라 `Hero3CatalogQuestIndex` 에 두어 공용 hint 로 노출.

## 2. 산출물

### 2.1 `Hero3CatalogQuestIndex` API 확장

- `val byFile: Map<String, List<Hero3CatalogQuestEntry>>` — 파일별 그룹.
- `val fileCount: Int` — 파일 수.
- `fun colorOf(file: String): Int` — 정렬된 파일명을 팔레트 슬롯에 매핑, 미지 파일은 hash fallback (각 채널 ≥ 0x80 → 어두운 배경에서도 가독).
- `fun fileColors(): Map<String, Int>` — UI 가 한번에 캐싱하기 좋은 형태.
- `companion val FILE_PALETTE: IntArray` — amber / teal / lavender / soft-red + 예비 green / pink.

### 2.2 `CatalogViewerScene` 리팩터

- `rowsForTab(Tab): List<String>` → `rowsForTab(Tab): List<Row>` 로 변경. `Row(text, paint?)`.
- 기존 12 탭은 `Row(it)` 한 줄 변환만으로 동일 렌더링.
- Quests 탭만 `questRows()` 로 분리, 파일 헤더 + entries 양쪽에 같은 file color paint 주입.
- `questPaintCache` 로 Paint 인스턴스를 ARGB 별 1개로 캐싱 (frame 마다 alloc 회피).
- 헤더 텍스트에 `files=<n>` 카운트 추가.

### 2.3 단위 테스트 (Hero3CatalogLoaderTest)

3종 추가:
- `r88_quest_index_groups_entries_by_file`: byFile 의 4 키 ({quest_00,_01,_10,_11}_dat), 각 group 의 file 일치, 합계 = idx.size.
- `r88_quest_index_fileColors_distinct_and_stable`: 4 색이 distinct, 같은 입력 같은 출력, 미지 파일도 alpha=0xFF 보장.
- `r88_quest_index_colorOf_uses_sorted_palette_slots`: 정렬 순(00→01→10→11) ↔ palette[0..3] 1:1.

총: 32 → 35 (catalog) / 78 → **81** 전체.

## 3. 검증

```
:app:testDebugUnitTest      → 35/35 (catalog) + 12/12 (extras) = 47/47, 0 failures
:engine-core:testDebugUnitTest → 7+6+2+15+4 = 34/34, 0 failures
:app:assembleDebug          → BUILD SUCCESSFUL, 14M APK
```

## 4. 영향 / 후속

- Quests 탭 가독성 향상; quest_*_dat 4 파일 흐름이 시각적으로 즉시 분리.
- 다른 Scene/UI 가 동일 파일 색을 재사용 가능 (`Hero3CatalogQuestIndex.colorOf(...)`).
- Row 모델은 CatalogViewerScene 안의 private 구조 — 외부 호환성 변화 없음.

## 5. 다음 라운드 (R89) 후보

| 후보 | 가치 | 비고 |
|---|---|---|
| QuestRegistry catalogKey | 중 | engine-core 4 quest 는 catalog 와 narrative 분리 — 단순 binding 만이라도 슬롯 추가. |
| Skills detail panel (Hero3Skill effectV2) | 중상 | SkillRegistry ↔ Hero3WeaponSkillSet 매핑 + slot1/slot2/slot3 표시. |
| R66 effect_v2 BattleScene | 상 | 데미지 공식에 effectV2 slot debuff 반영. |
| ForgeScene gold cost | 하 | 11-byte recipe 의 bytes[0..1] 이 cost 인지 확정 후 진행. |
| QuestScene에 quest catalog 색 적용 | 중 | R88 의 file color 를 in-game UI 까지 확장. |

## 6. 산출물 위치

- `android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogQuestIndex.kt` (R88 API 추가)
- `android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt` (Row 모델 + questRows)
- `android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt` (R88 tests 3종)
