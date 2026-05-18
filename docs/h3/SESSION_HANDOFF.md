# Hero3 인수인계 노트 (Round 70 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~99.5%**. **자동 분석 완전 종결**. `docs/h3/MASTER_SPEC.md` (4,700+ lines) = Android 리메이크 single reference 작성. exp_gold 4 그룹 implicit enemy tier 발견. enemyg sprite coincidence 정정. **Round 71+ 는 모두 사용자 환경 필수** (DES 8 파일 / LLM 번역 / SMAF audio).

마지막 commit: `615cfe5d feat:영웅서기3 Round 69 — i14 ammo 정정 + enemy stat scaling + dialogue translation queue (자동 분석 종료)`

**Round 70 산출물 = uncommitted**:
- ★★★★★ 신규 doc: [`MASTER_SPEC.md`](MASTER_SPEC.md) — Android 리메이크 single reference (15 sections, 4,700+ lines)
- 신규 round doc: [`ghidra-round70-master-spec-exp-groups-2026-05-19.md`](ghidra-round70-master-spec-exp-groups-2026-05-19.md)
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 자동 분석 완전 종결 — 모든 작업 사용자 환경 필수

### 1.1 ⭐⭐⭐ DES 8 파일 복호화 (최우선)

- **i15_dat** (7400B, master item table 추정)
- drop_dat / droph_dat (3080B, enemy 드롭)
- getitem_dat (400B, fixed drops)
- smith_dat / smithh_dat (896B, smith 레시피)
- shop_dat / shoph_dat (상점)

방법: Hero5 NDK runner (key `"0EP@KO91"` + `dat/des_dat` tables, R57 확정).

### 1.2 ⭐⭐⭐ boss skill ID 매핑 최종 확정

R67/R68/R70: H4 (별도 boss skill table) confirmed but unresolved. DES 복호화된 파일 안에 boss AI table 발견 가능.

### 1.3 ⭐⭐ i14 smith 레시피 매핑

smith_dat 복호화 후 i14 (조합 재료) → i0~i12 (결과물) 정확 매핑. R69 의 7 카테고리 + crafting map 기준.

### 1.4 ⭐⭐ Dialogue LLM 번역

9,740 entries, **$4.09 추정 비용** (Claude Sonnet 4.6). 한국어 → 영어 i18n.

### 1.5 ⭐ SMAF→OGG audio 변환

33 파일. Android audio asset 준비.

## 2. Round 70 핵심 발견

### 2.1 MASTER_SPEC.md 통합 문서 (★★★★★)

15 section reference:
1. 게임 시스템 한눈 요약
2. Master Stat Enum (24 codes)
3. Rarity Prefix System
4. Item Catalog (18 카테고리, 529 items)
5. Skill System (105 skills)
6. Enemy System (4 exp tier)
7. Boss System (combat_rating formula)
8. Crafting System (i14 7 카테고리)
9. Quest System (44+)
10. Asset Catalog
11. DES System
12. Region Map (8 regions)
13. Hero3 핵심 게임 디자인 통찰
14. Android 리메이크 권장 구현 순서
15. R56-R70 round-by-round 요약

### 2.2 exp_gold 4 그룹 = implicit enemy tier (★★★★)

| group | n | scaling | 카테고리 |
|---|---:|---|---|
| **9.7x** | 41 | normal 800 → hard 7,700 | 일반 전투 |
| **1.8x** | 22 | normal 6,400 → hard 11,500 | 정찰/고급 |
| **stable** | 16 | normal ≈ hard ≈ 2,600 | 보스/특별 (`{` prefix 4개) |
| **other** | 82 | 다양 | gunners/skeletons/creatures |

→ Android 리메이크 enemy spawn 균형 + drop rate 조정에 활용.

### 2.3 enemyg_dat 케이 패턴 정정 (★★★)

R68 의 (2,2,1,1) 3 hits 가 22 byte sprite entry 의 animation frame data 임이 확정. boss skill mapping 과 무관. → boss skill ID 매핑은 DES 복호화 후만 가능.

## 3. Android 리메이크 권장 구현 순서 (MASTER_SPEC §13)

1. **engine-core** (Phase C Step 1-5 완료): pure Kotlin engine
2. **data loader**: `work/h3/game_balance.json` (582KB) 또는 dat 파일 직접 파싱
3. **stat system**: 24-code enum + value scale 규칙
4. **item system**: 18 카테고리 + rarity prefix + equip trailer bonus pair
5. **skill system**: 30-byte tail layout + effect chain (slot1/2/3) + ultimate sentinel
6. **enemy/boss system**: 19B stat block + 6B boss trailer + combat_rating formula
7. **i18n**: 246 UI strings + 9,740 dialogue (LLM 번역 후)
8. **DES decryption** (사용자 환경 의존): drop/smith/shop 테이블
9. **audio**: SMAF→OGG 33 files

## 4. 작업 순서 권장 (Round 71+)

1. `git status` + `git log --oneline -5`
2. `git add` + `git commit` Round 70 산출물 (MASTER_SPEC + round doc)
3. **사용자 환경 진행 필수**:
   - DES 8 파일 복호화 (Hero5 NDK runner)
   - Dialogue LLM 번역 (9,740 entries, $4.09)
   - SMAF→OGG audio 변환

목표 진행률 (Round 71+, 사용자 환경 후): **~99.8%+**.

## 5. 참고 문서

- ★★★★★ [MASTER_SPEC.md](MASTER_SPEC.md) — Hero3 single reference (R70 신규)
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 70](ghidra-round70-master-spec-exp-groups-2026-05-19.md) — ★ 이번 라운드 (master spec + exp groups)
- [Round 69](ghidra-round69-ammo-enemy-stat-dialogue-2026-05-19.md) — ammo 정정 + stat scaling + dialogue
- [Round 68](ghidra-round68-boss-skill-search-gun-marker-fun4f358-2026-05-19.md) — boss skill 검색 + gun marker
- [Round 67](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md) — skill header + enemy trailer
- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + combat_rating + v1.1
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum
- (R56-R62) — see MASTER_SPEC §14
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
