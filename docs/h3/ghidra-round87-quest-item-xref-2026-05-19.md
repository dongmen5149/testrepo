# Hero3 Round 87 — Quest Item Xref 통합 (2026-05-19)

## 0. 한 줄 요약

R62 의 `quest_item_xref` (21 items, JSON 에는 있었지만 catalog 가 무시) 을 `Hero3Catalog.questItemXref` 로 통합. 신규 CatalogViewer 탭 (Item-Quest Xref) — 각 item 의 quest 출현 위치/오프셋/컨텍스트. lookup API 2종 (`findQuestXref` / `questXrefByFile`). 78/78 tests + APK BUILD SUCCESSFUL.

**신규 finding**: 21 items 중 1 ("반토막난 지도") 만 match 0 — 다른 20개는 quest_*_dat 안에서 평균 ~10 match 위치. "토레즈시민증" 35 matches, "토레즈의서신" 38 matches (가장 빈번).

## 1. 신규 산출물

### 1.1 코드

- `Hero3Catalog.kt`:
  - 신규 data class: `Hero3QuestItemMatch` (file, offset, text, context) + `Hero3QuestItemXref` (cleanName, matches)
  - `Hero3Catalog.questItemXref: List<Hero3QuestItemXref>`
  - `Hero3CatalogLoader.parseQuestItemXref(obj)` — `quests.item_xref` dict → List 변환
  - `findQuestXref(name)` / `questXrefByFile(file)` API
- `CatalogViewerScene.kt`:
  - 신규 Tab `QUEST_ITEM_XREF` ("아이템-퀘스트 xref" / "Item-Quest Xref")
  - 각 item 별 첫 3 match 표시 + "… +N more" 줄임표

### 1.2 테스트 (3 신규, 78/78 pass)

- `r87_quest_item_xref_has_21_items` — 21 items, 1만 빈 match (반토막난 지도)
- `r87_quest_item_xref_finds_known_item` — "협곡의성수" 매칭 + quest_ 파일 확인
- `r87_quest_xref_by_file_groups_correctly` — file 별 group filter 검증

## 2. R88 권장 후속 작업

1. **QuestRegistry catalogKey 필드** — engine-core `Quest` 에 옵셔널 catalog 이름
2. **CatalogViewer Skills detail panel** — 스킬 effect block 단일 entry 상세
3. **R66 effect_v2 BattleScene 통합** — 11 debuff codes 적용
4. **ForgeScene gold cost** — recipe 별 비용 부과
5. **Quests tab file-색상** — 115 entries 가독성 (file 별 prefix 색상)
