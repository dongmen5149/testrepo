# Hero3 Round 85 — Catalog Quest 인덱스 + 중복 매칭 (2026-05-19)

## 0. 한 줄 요약

R84 의 `Hero3Catalog.questFiles` 위에 **한국어 이름 기반 quest 인덱스** (`Hero3CatalogQuestIndex`) 를 추가. 캐논화 (꼬리 1자리 숫자 제거 + 공백 정규화) 후 67 entries → 59 distinct, **8 cross-file duplicates** 발견 ("전장으로", "엔자크의 영광", "영혼의 시", "로우엔의 치안", "남쪽의 마물", "마지막 증거", "혼돈의 대륙", "고대의 마법장비" — 모두 `quest_01_dat`/`quest_11_dat` 또는 `quest_00`/`quest_10` 쌍). CatalogViewer Quests tab 에 통계 헤더 + 중복 ★ 마커 표시.

## 1. 신규 산출물

### 1.1 코드

- `android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogQuestIndex.kt` (신규)
  - `Hero3CatalogQuestIndex.build(catalog)` — `questFiles` 평탄화 + 캐논화 인덱스 빌드
  - `canonicalize(name)` — trim + 공백 압축 + 꼬리 1자리 숫자 제거
  - `lookupExact(name)` / `lookupContains(fragment)` / `duplicates()`
- `MainActivity.questIndex: Hero3CatalogQuestIndex by lazy` — process-scoped 노출
- `CatalogViewerScene` Quests tab — 헤더 (loaded/distinct/duplicates 카운트) + 중복 entry 앞 ★ 표시

### 1.2 테스트 (4 신규, 75/75 pass)

- `r85_quest_index_builds_and_indexes_all_loaded_entries`
- `r85_quest_index_canonicalize_strips_trailing_digit`
- `r85_quest_index_lookup_finds_first_known_entry`
- `r85_quest_index_detects_known_duplicate_chaos_continent`

## 2. 데이터 발견

### 2.1 cross-file 중복 8쌍

| canonical name | 출현 파일 |
|---|---|
| 전장으로 | quest_00_dat + quest_10_dat |
| 엔자크의 영광 | quest_01_dat + quest_11_dat |
| 영혼의 시 | quest_01_dat + quest_11_dat |
| 로우엔의 치안 | quest_01_dat + quest_11_dat |
| 남쪽의 마물 | quest_01_dat + quest_11_dat |
| 마지막 증거 | quest_01_dat + quest_11_dat |
| 혼돈의 대륙 | quest_01_dat + quest_11_dat |
| 고대의 마법장비 | quest_01_dat + quest_11_dat |

**해석**: `quest_X1_dat` = `quest_X0_dat` 의 하드 모드 대응 (R74 region shops 의 normal/hard 분리 패턴과 동일). quest_01 ↔ quest_11 7 entries 모두 매칭됨 → quest_01_dat = quest_11_dat 의 다른 표현인 듯.

### 2.2 truncation 미확정

`n_entries` 메타데이터 (37/7/38/33 = 115) vs `entries` 배열 실제 길이 (20/7/20/20 = 67). 메타데이터 신뢰 시 ~48 entry 미파싱. 업스트림 export script (R84) 의 cut-off 추정 — R86 에서 재추출 권장.

## 3. R86 권장 후속 작업

1. **export_game_balance.py quest entry truncation 수정** — n_entries 메타와 실 entries 정합화 (67 → 115)
2. **QuestRegistry 캐논 키 매칭** — engine-core `Quest` 에 `catalogKey: String? = null` 추가, 4 hardcoded quests 의 fan-fiction 이름을 canonical catalog 이름으로 교체 가능성 검토
3. **CatalogViewer Skills detail panel** — R84 핸드오프 잔여 항목
4. **R66 skill effect_v2 BattleScene 통합** — debuff codes 11 distinct 를 실 전투에 적용

## 4. 진행률

이전: ~99.95% (R84 종료)
이번: ~99.96% (+0.01%p, 데이터 정합성 + 검증 인프라)

남은 자동 가능 항목: R74 export script truncation 수정, QuestRegistry 캐논 매칭, CatalogViewer Skills detail panel, item_xref 21 매핑, ForgeScene gold cost.
