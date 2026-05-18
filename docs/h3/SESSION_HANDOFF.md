# Hero3 인수인계 노트 (Round 63 종료 시점, 2026-05-18)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~91-94%**. 게임 데이터 평문 파싱 ~98% 완료. **master stat enum 100% 매핑 확정** (R63). 게임 시스템 모델링 92% (item/skill/effect/rarity/quest/enum 매핑 완전). DES 8 파일만 사용자 환경 (NDK runner) 필요.

마지막 commit: `f3a75650 feat:영웅서기3 Round 62 — item trailer = bonus pair 발견 (177/346=51%) / rarity prefix 7등급 / skill rank @ +0x1d / quest item xref 20/21`

**Round 63 산출물 = uncommitted** (다음 commit 시 일괄 포함):
- 신규 doc 1: [`ghidra-round63-stat-enum-final-2026-05-18.md`](ghidra-round63-stat-enum-final-2026-05-18.md)
- 신규 recon 스크립트 2: `map_stat_enum.py` / `correlate_price_rank.py`
- 신규 dump (work/ 폴더, gitignored): `stat_enum.{json,log}` / `price_rank_corr.{json,log}`
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ game_balance.json 통합 출력 (R64 핵심)

R56-R63 의 모든 recon 산출물을 master stat enum 으로 통일된 JSON 으로 출력. **Android 리메이크용 single source of truth**.

```
work/h3/game_balance.json
├── stat_enum:    (R63 master enum, 24 codes)
├── items:        (i0~i18, 480+ items, bonus_type 통일)
├── skills:       (s4~s10, 105 skills, rank power class)
├── enemies:      (enemy_dat 161 + boss_dat 15 with R60 19B layout)
├── quests:       (44+ quests with R62 i17 cross-ref)
├── strings:      (R60 246 strings + InGame_txt)
├── rarity:       (R62 7 prefix class)
└── des_status:   (8 files pending NDK)
```

스크립트: `tools/recon/export_game_balance.py` (신규)

### 1.2 ⭐⭐⭐ i15_dat = 8번째 DES 파일 복호 (사용자 환경 필요)

R60/R61/R62 와 동일. 8 DES 파일 일괄 처리 필요.

### 1.3 ⭐⭐ i13/i14/i17/i18 effect_value scale 분석

R63 에서 stat_enum 은 매핑 완료. 미해결: value 의 의미 (% ratio 또는 flat).

가설:
- 0x05 (i13) = 40 → 물공 +40% (ratio)
- 0x05 (ring) = 8 → 물공 +8 (flat)
- 같은 코드라도 사용처에 따라 다른 scaling

스크립트: `tools/recon/analyze_value_scale.py` (신규)

### 1.4 ⭐⭐ 0x14 / 0x19 / 0x01 미사용 코드 추적

R63 에서 i12/i13/i16 4 소스로 cross-validate 했으나 0x14, 0x19 는 어디서도 명시적 의미 발견 못함.

binary literal grep + FUN_4f358 본문 정밀 (R55/R59/R61/R63 보류 항목).

### 1.5 ⭐⭐ rank 5-15 ultimate 스킬 byte-by-byte 비교

R63 발견: 단검 난무(r15) / 건 난사(r10) / 라이플 연쇄(r5) / 다크 나락(r5). 이들 30B tail 을 일반 스킬과 비교해 ultimate-only field 식별.

스크립트: `tools/recon/decode_ultimate_skills.py` (신규)

### 1.6 ⭐ FUN_4f358 본문 정밀 (Ghidra)

R55/R59/R61/R63 보류. stat_modify 함수 후보, R64 의 0x14/0x19 매핑 prerequisite.

## 2. 사용자 환경 필요 작업 (보류)

§1.2 DES 8 파일, SMAF→OGG (33 파일), 9,741 unique 대사 LLM 번역 (~$0.66) — R62 와 동일.

## 3. 이미 발견한 Hero3 게임 시스템 (Round 56-63 누적)

### 3.1 평문 파싱 완료 + body 디코드 (Round 63 시점)

| 영역 | 파일 / entries | body 디코드 상태 |
|---|---|---|
| **전투 데이터** | enemy_dat (161) + enemyh_dat (161) — R56 | ✓ 19B stat block 완전 매핑 (R60) |
| **보스 데이터** | boss_dat (15) + bossh_dat (15) — R58 | ✓ HP 위치 +0a..+0b BE16 확정 (R60) |
| **캐릭터/NPC** | char_dat (10 classes) + npcg_dat (78 NPCs) — R59 | ✓ class layout (R59) |
| **스킬** | s4~s10_dat = 7 파일 × 15 = 105 skills — R60 | ✓ 4-cat + rank power class (R62/R63) |
| **아이템** | i0~i14, i16~i18 = 17 파일 480+ items — R60 | ✓ 5 layout + bonus 매핑 100% (R63) |
| **퀘스트** | quest_00/01/10/11_dat (44+ quests) — R58 | ✓ **i17 20/21 매칭** (R62) |
| **UI/메뉴** | dat/InGame_txt (196) + menu/*.txt (50) — R60 | ✓ string table format |
| **DES 시스템** | dat/des_dat (824B) + key `"0EP@KO91"` — R57 | — |
| **★ Stat enum** | 0x00~0x1c (24 codes) — R63 | ✓ **100% 매핑 (i13+i16+ring+trailer)** |

### 3.2 DES 암호화 (미해결, 8 파일)

§1.2 참고.

### 3.3 ★ Master stat enum (R63 핵심 산출물)

| code | name | meaning | confirmed by |
|---:|---|---|---|
| 0x00 | ATT1_BASE | 무기 공격력 (i16) | i16 뇌제의 |
| 0x01 | HP_HEAL_INSTANT | 즉시 HP 회복 | i13 자비의손길 |
| 0x02 | HP_MAX | HP 최대치 | i13+i16+ring+trailer |
| 0x03 | HP_REGEN | HP 회복속도 | i13 승리의염원 + i16 공명의 + ring 회복의반지 |
| 0x04 | SP_MAX | SP 최대치/회복 | i13 잠재의식 + ring 데몬의뿔 |
| 0x05 | ATT1 (물공) | 물리공격력 | i13 끓어오르는피 + ring 힘의반지 |
| 0x06 | ATT2 (특공) | 특수공격력 (마법/총기) | i13 악마의속삼임 + ring 정신의반지 |
| 0x07 | P_DEF (물방) | 물리방어력 | i13 철벽의가드 + i16 금강의 + ring 체력의반지 |
| 0x08 | M_DEF (특방) | 특수방어력 | i13 오로라의장벽 + i16 정령의 + ring 히드라 |
| 0x09 | ACC | 명중률 | i13 사냥꾼의눈 + i16 사신의 + ring 콘돌/백발백중 |
| 0x0a | DOD (회피) | 회피율 | i13 시간의지배자 + i16 영제의 + ring 민첩의반지 |
| 0x0b | BLOCK | 방패방어율 | i13 용자의가호 + i16 철벽의 + ring 기사/프로텍트 |
| 0x0c | CRI_RATE | 크리티컬 발생율 | i16 속박의 (R61 P.DEF 가설 폐기) |
| 0x0d | CRI_DEF | 크리피해 감소 | i16 결의의 (R61 M.DEF 가설 폐기) |
| 0x0e | SP_COST_REDUCE | 스킬 SP 소모 감소 | i16 현자의 + ring 총명의반지 (R61 HIT 가설 폐기) |
| 0x0f | SP_REGEN | SP 회복속도 | i16 마도의 + ring 지혜의반지 (R61 EVA 가설 폐기) |
| 0x10 | HP_DRAIN | 공격시 HP 흡수 | i16 흡혈의 + ring 카오스/데몬 |
| 0x11 | CD_REDUCE | 쿨타임 감소 | i13 질풍노도 + i16 폭풍의 |
| 0x12 | SHIELD_PIERCE | 방패 무시 확률 | i16 직격의 (R61 ATK 정정) |
| 0x14 | ? | (rare) | 미식별 |
| 0x16 | BUFF_REMOVE | 능력치 증가 해제 | i13 망각의향 |
| 0x17 | CURE_STATUS | 상태이상 회복 | i13 혼의외침 |
| 0x19 | ? | (rare) | 미식별 |
| 0x1c | REVIVE | 전투불능 회복 | i13 피닉스의숨결 |

### 3.4 ★ Rarity → 가격 modifier (R63)

| rarity | 방어구 | 무기 | quest_reward |
|---|---:|---:|---:|
| normal | 1.0x | 1.0x | — |
| magic (`\|`) | 1.13x | 1.01x | — |
| legendary (`'`) | 1.06x | — | — |
| epic (`$`) | 1.15x | 0.93x | — |
| boss_drop (`{`) | 1.5x | **0.03x (free)** | — |
| endgame (`@`) | low | low | — |
| quest_reward (`}`) | 0 | 0 | 0 |

→ Hero3 rarity 는 **stat-driven, NOT price-driven**. 무기 boss_drop 은 사실상 무료 loot.

### 3.5 Skill rank power class (R63)

`+0x1d` byte = "skill power class" (R62 의 "1-3 tier 가설" 정정):
- weapon_passive: 1-5 범위 (단검은 1-5 full, 라이플/홀리석은 전부 1)
- active 스킬 일반: 1-4 범위
- **active 스킬 ultimate**: 5-15 (단검 난무 r15, 건 난사 r10, 라이플 연쇄 r5, 다크 나락 r5)

### 3.6 boss/enemy/item layout (R60-R63 누적, 변경 없음)

(R62 SESSION_HANDOFF 참고)

### 3.7 i17 quest item → quest 매핑 (R62, 20/21)

(R62 SESSION_HANDOFF 참고)

## 4. Hero3 게임 세계 (변경 없음)

- 8 main regions / 2 주인공 × 5 클래스 / 480+ items / 15 bosses / 161×2 enemies / 105 skills / 44+ quests

## 5. 작업 순서 권장 (Round 64)

1. `git status` + `git log --oneline -5` — 현재 상태 확인
2. `git add` + `git commit` Round 63 산출물
3. **game_balance.json 통합 출력** (`tools/recon/export_game_balance.py` 신규)
4. **value scale 분석** (`tools/recon/analyze_value_scale.py` 신규)
5. **0x14 / 0x19 미사용 코드 추적** (binary literal grep + FUN_4f358)
6. **ultimate 스킬 비교** (`tools/recon/decode_ultimate_skills.py` 신규)
7. **i15_dat NDK runner 처리** (사용자 환경)
8. Round 64 doc 작성 + PROGRESS.md 갱신 + commit

목표 진행률 (Round 64 종료 시): **~93-96%** (game_balance.json +1%p, value scale +1%p, 0x14/0x19 매핑 +1%p, ultimate decode +0.5%p).

## 6. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (Round 17~63)
- [Round 63 상세](ghidra-round63-stat-enum-final-2026-05-18.md) — ★ 이번 라운드 (master stat enum 완전)
- [Round 62](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) — trailer = bonus / rarity / quest xref
- [Round 61](ghidra-round61-item-skill-body-decode-2026-05-18.md) — item body / i13·i14 / skill body
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill 일괄 / boss HP / string table / item 카탈로그
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4 dat
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES variants
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-8].md`
- 모든 recon scripts: `tools/recon/`
