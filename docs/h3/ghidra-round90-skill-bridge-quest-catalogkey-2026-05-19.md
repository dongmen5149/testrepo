# Hero3 Round 90 — SkillScene engine↔catalog bridge + Quest.catalogKey 슬롯 (2026-05-19)

## 0. 한 줄 요약

R89 의 `Hero3CatalogSkillIndex.lookupByName` + `effectSummary` 를 **실제 사용 지점에 처음 연결**. `SkillScene` 의 하단 detail panel 에 engine 스킬 한국어 이름 → catalog skill fuzzy 매칭 → effectV2 한 줄 요약을 추가 (40→54 픽셀 박스). 매칭 없음 / catalog 미설치는 muted color 로 graceful fallback. 함께 §1.4 의 `Quest.catalogKey: String? = null` 슬롯도 도입 (4 bespoke entries 그대로 null). 89/89 tests (catalog 40→43, +3) + APK BUILD SUCCESSFUL.

## 1. 동기

R88-R89 가 catalog API 두 인덱스 (`Hero3CatalogQuestIndex`, `Hero3CatalogSkillIndex`) 를 정착시키고 `CatalogViewerScene` 안에서만 노출됐다. SESSION_HANDOFF §1.1 의 권장은 "lookup API 를 본 게임 scene 에서 실제로 쓰는 첫 통합 라운드". R90 의 두 작업은 **소비측 통합** 1건 + **데이터 모델 슬롯** 1건의 작은 묶음.

## 2. 산출물

### 2.1 `SkillScene` — catalog effectSummary 표시

`android/app/src/main/java/com/hero3/remake/scene/SkillScene.kt`

- `Hero3CatalogProvider.get()?.let { Hero3CatalogSkillIndex.build(it) }` 로 lazy 인덱스 1회 빌드 (catalog 미설치 시 null).
- 신규 `catalogLine(nameKo)` — engine skill 의 `nameKo` 를 `lookupByName` 으로 fuzzy 검색. 매칭이 여러 개면 `effectV2.rank` 최대값. effectV2=null 이면 "(no effectV2)".
- 하단 detail box 높이 40 → 54, 3번째 줄에 `<weapon>: rank=N (deb=M)  CODE+x/y | …` 표시. 매칭 있음 = sky-blue muted (140/220/255), 없음 = grey (110/110/130), catalog 미설치 = "(catalog n/a)".
- finding (R89 와 일관): engine "연사" (`ritz_rapidfire`) → catalog s7/s8 의 "연사" 정확 매칭 (≥1 hit). engine `강타 / 메가 크러쉬 / 정조준 / 영혼 노바` 등은 catalog 의 weapon-technique 명 (`섬광 / 창술1..7`) 과 단어 형태가 달라 lookupByName(contains) 로 매칭 안 되는 정상 케이스 — "(no catalog match)" 줄로 표시되며 게임 진행에 영향 없음.

### 2.2 `Quest.catalogKey` 슬롯

`engine-core/src/commonMain/kotlin/com/hero3/remake/engine/Quest.kt`

- `data class Quest(...)` 끝에 `val catalogKey: String? = null` 추가.
- 4 bespoke entries (`guardian_hunt / chaos_lord / sealed_god / herb_gather`) 모두 `null` 그대로 — 추후 narrative 정의 시 `Hero3CatalogQuestIndex.canonicalize` 결과를 넣어 catalog 의 115 quests 와 매핑.

### 2.3 unit tests (catalog 40→43, +3)

`android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt`

- `r90_skill_index_bridges_engine_rapidfire_to_catalog` — engine "연사" → catalog ≥1 hit, effectV2 있으면 summary "rank=" 시작.
- `r90_skill_index_lookupByName_returns_empty_for_unknown_engine_skill` — sentinel 입력으로 empty list 반환.
- `r90_quest_registry_has_catalogKey_slot_defaulting_to_null` — 4 bespoke entries 모두 `catalogKey == null`.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 34/34 pass
:app:testDebugUnitTest          → 55/55 pass  (catalog 40→43, bridge 8, provider 4)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 89/89 (+3 from R89), 0 failures
```

## 4. R91 권장 작업

R90 으로 §1.1 (SkillScene) + §1.4 (Quest.catalogKey) 두 항목이 닫혔다. R91 후보:

- ⭐⭐⭐⭐ §1.2 R66 effect_v2 를 BattleScene 데미지 공식에 반영. catalog 매칭 hit 의 slot1.codeName (ATT1 / DEF / HP_HEAL_INSTANT) 을 modifier 로. 작업량 중급.
- ⭐⭐⭐ §1.3 `Hero3CatalogItemIndex` 신설 (R88-R89 패턴 3번째). 18 카테고리 × N items + ITEMS 탭 drill-down.
- ⭐⭐ §1.5 ForgeScene recipe bytes[0..1] gold cost 가설 검증.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~87-88% → ~88% (lookup API 첫 소비 + 데이터 모델 슬롯, +0.5%p 수준 — UI 가독성 + 미래 bridge 기반).
