# Hero3 Round 92 — Hero3CatalogItemIndex + ITEMS 탭 drill-down (2026-05-19)

## 0. 한 줄 요약

R85/R89 의 catalog 인덱스 패턴 3번째 적용 — **`Hero3CatalogItemIndex`** 신설 (entries / byCategory / byFile / colorOf / fileColors / FILE_PALETTE 10색 + lookupByName / lookupByCategory). `CatalogViewerScene` 의 ITEMS 탭이 기존 18-줄 카테고리 요약 → ~547 줄 per-item drill-down 으로 확장 (pos / cleanName / raw name). 10 슬롯 팔레트 + 8 hash fallback (18 카테고리). 96/96 tests (catalog 46→50, +4) + APK BUILD SUCCESSFUL.

## 1. 동기

R85 Quest 인덱스 / R89 Skill 인덱스 / R92 Item 인덱스 — catalog 의 세 메인 데이터 축이 모두 같은 API 패턴 (`byFile` + `colorOf` + `fileColors` + `lookupByName`) 으로 통일. ITEMS 탭은 18 카테고리 × 평균 ~29 items 라는 가장 큰 데이터 셋이라 drill-down 가치가 가장 높음. R71 catalog 가 모든 데이터를 이미 적재해놨기 때문에 인덱스/UI 만 붙이면 됨.

## 2. 산출물

### 2.1 `Hero3CatalogItemIndex` (신규)

`android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogItemIndex.kt`

- `data class Entry(file, category, item)` — category + item 평탄화 view.
- `val entries: List<Entry>` (catalog 의 총 529 items 와 동일).
- `val byCategory: Map<String, List<Entry>>` — 카테고리 라벨별 그룹.
- `val byFile: Map<String, List<Entry>>` — i0..i18_dat 그룹 (18개, gap 포함).
- `fun colorOf(file)` / `fun fileColors()` — R88/R89 인덱스와 동일한 사용성. 10 슬롯 palette → 11번째부터 hash fallback.
- `fun lookupByName(fragment)` / `fun lookupByCategory(fragment)` — fuzzy 검색. lookupByName 은 `item.name` + `item.cleanName` 둘 다 검사.
- `companion val FILE_PALETTE: IntArray` — 10색 (coral / amber / yellow / lime / aqua / cyan / periwinkle / orchid / rose / sand). R88 quest (4 색) / R89 skill (7 색) 과 hue 충돌 회피.

### 2.2 `CatalogViewerScene` ITEMS 탭 확장

`android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt`

- 신규 `itemRows()` 함수 — Quest/Skill 와 동일한 패턴.
- 헤더: `loaded=N  categories=M  files=K`.
- category 헤더: `=== iN_dat  <category>  (n=N) ===` (파일 색).
- item 행: ` pos=NNN  <cleanName>  [<raw name>]`.
- 기존 `Row(text, paint?)` 모델 재사용 — alloc 추가 없음, paint cache 공유.

### 2.3 unit tests (catalog 46→50, +4)

`android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt`

- `r92_item_index_builds_with_eighteen_categories_and_529_items` — 18 files / 529 items / byFile 합 == idx.size.
- `r92_item_index_groups_by_file_and_keeps_all_entries` — 모든 byFile key 가 `iN_dat` 형식.
- `r92_item_index_colorOf_distinct_for_first_ten_files_and_stable` — 첫 10 files = palette slot[0..9] 1:1 distinct + 미지 파일 hash fallback (alpha=0xFF, 각 채널 ≥ 0x80).
- `r92_item_index_lookupByName_finds_known_consumable` — "포션" (i18_dat[0]) 매칭 확인.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 34/34 pass
:app:testDebugUnitTest          → 62/62 pass  (catalog 46→50, +4, bridge 8, provider 4)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 96/96, 0 failures
```

## 4. R93 권장 작업

- ⭐⭐ §1.2 확장 — `P_DEF / M_DEF` slot 매핑 추가 (BattleScene.doEnemyAttack 의 받는 데미지 modifier).
- ⭐⭐ §1.2 확장 — `CRI_RATE / ACC / DOD` 매핑 (현 8% 크리에 가산).
- ⭐⭐ 디버프 (`nDebuffs > 0`) → engine `Status` enum 도입 + BattleScene tick.
- ⭐⭐ §1.5 ForgeScene recipe bytes[0..1] = gold cost 가설 검증.
- ⭐ Phase C: Dialogue LLM 번역 ($4.09, 사용자 API key 필요).

R88-R92 의 catalog 인덱스 3종 패턴이 정착 → R93 부터는 "각 인덱스 위에 build 된 데이터를 game logic 에 연결" 이 자연스러운 다음 단계.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~88-89% → ~89% (catalog item 인덱스로 18 카테고리 529 items 가 UI 에서 drill-down 가능, 게임 logic 통합 준비 완료).
