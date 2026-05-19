# Hero3 Round 86 — Quest export truncation fix (2026-05-19)

## 0. 한 줄 요약

R84 의 `export_game_balance.py` quest section 에 있던 `entries[:20]` 슬라이스 제거 → catalog quest entries **67 → 115 완전 복구**. game_balance.json 패치 (832KB → 837KB). R85 의 quest index 가 즉시 더 많은 중복 탐지: **8 → 11 duplicates** (cross-file 10 + intra-file "협곡 탐사" quest_10 내 2회). 모든 75 tests 그대로 통과 + APK BUILD SUCCESSFUL.

## 1. 신규 산출물

### 1.1 코드/데이터

- `tools/recon/export_game_balance.py` — quest entries 슬라이스 제거 (line 393: `entries[:20]` → `entries`)
- `android/app/src/main/assets/game_balance.json` — quests.files 전체 재기록
  - quest_00_dat: 20 → 37 entries
  - quest_01_dat: 7 → 7 (변경 없음)
  - quest_10_dat: 20 → 38 entries
  - quest_11_dat: 20 → 33 entries
  - 총: 67 → **115 entries**

### 1.2 테스트

추가 코드 없음. R85 의 4 quest_index 테스트 + R84 의 `r84_catalog_quests_loaded_115_entries_across_4_files` 모두 그대로 통과 — index 통계 (loaded=115) 와 duplicates 셋이 자동 업데이트됨.

## 2. 신규 데이터 발견 — duplicates 8 → 11

| canonical name | 출현 파일 | 비고 |
|---|---|---|
| 엔자크의 영광 | quest_01 + quest_11 | R85 confirmed |
| 영혼의 시 | quest_01 + quest_11 | R85 confirmed |
| 로우엔의 치안 | quest_01 + quest_11 | R85 confirmed |
| 남쪽의 마물 | quest_01 + quest_11 | R85 confirmed |
| 마지막 증거 | quest_01 + quest_11 | R85 confirmed |
| 혼돈의 대륙 | quest_01 + quest_11 | R85 confirmed |
| 고대의 마법장비 | quest_01 + quest_11 | R85 confirmed |
| 전장으로 | quest_00 + quest_10 | R85 confirmed |
| **반전세력 엘지스** | quest_00 + quest_10 | R86 신규 (이전 truncated) |
| **등대를 향해** | quest_00 + quest_10 | R86 신규 (이전 truncated) |
| **협곡 탐사** | quest_10 only × 2 | R86 신규 — intra-file 중복 |

**해석 강화**:

- quest_01_dat (7 entries) = quest_11_dat (33 entries) 의 normal/hard 쌍이 아니라, quest_01 ⊂ quest_11. quest_11 가 풀버전, quest_01 은 7 entries 만 발췌.
- quest_00 ↔ quest_10 도 3 cross-file 매칭 (전장으로 / 반전세력 엘지스 / 등대를 향해) → 일부 quest 가 두 chapter 에 공통 등장.
- quest_10_dat 내 "협곡 탐사" 가 pos=4753 + pos=상이 2회 — 게임 내 동일 quest 가 2가지 boss/reward 변형 가능성.

## 3. 진행률

이전: ~99.96% (R85)
이번: ~99.97% (+0.01%p, 데이터 정합성 — Catalog Quest 의 완전성)

## 4. R87 권장 후속 작업

1. **CatalogViewer Quests tab — file 별 색상 / 정렬 옵션** (115 entries 화면 가독성)
2. **QuestRegistry catalogKey 필드** — engine-core `Quest` 에 옵셔널 필드 추가, 4 hardcoded 의 매칭 가능성 재검토 (115 entries 기준)
3. **R66 effect_v2 BattleScene 통합**
4. **CatalogViewer Skills detail panel**
5. **R62 item_xref 21 매핑**
6. **ForgeScene gold cost**
