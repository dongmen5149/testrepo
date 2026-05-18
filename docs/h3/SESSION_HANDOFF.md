# Hero3 인수인계 노트 (Round 64 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~94-96%**. 게임 데이터 평문 파싱 ~98% 완료. **`work/h3/game_balance.json` (537KB) = Android 리메이크용 single source of truth 출력 완료** (R64). value scale (flat/ratio/signed-debuff) 매핑 + ultimate skill diff + 0x14/0x19 미사용 확인. DES 8 파일만 사용자 환경 (NDK runner) 필요.

마지막 commit: `285449c8 feat:영웅서기3 Round 63 — master stat enum 100% 매핑 (i16 enchant desc 가 Rosetta Stone) / R61 가설 5건 정정`

**Round 64 산출물 = uncommitted** (다음 commit 시 일괄 포함):
- 신규 doc 1: [`ghidra-round64-balance-export-value-scale-2026-05-19.md`](ghidra-round64-balance-export-value-scale-2026-05-19.md)
- 신규 recon 스크립트 4: `export_game_balance.py` / `analyze_value_scale.py` / `analyze_unused_stat_codes.py` / `decode_ultimate_skills.py`
- 신규 산출물 (work/h3/, gitignored): `game_balance.json` (537KB) + `recon/{value_scale,unused_codes,ultimate_skills}.{json,log}`
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ equip trailer 177 case 의 0x14/0x19 분포 재집계 (R65 핵심)

R62 발견: 346 equip 중 177 (51%) 가 trailer 4B 에 (bonus_type, value) × 2 보유.
R64 발견: 0x14/0x19 가 i*_dat stat enum 에서는 부재하지만 equip trailer 에는 출현.

가설: 0x14/0x19 가 **boss-only stat code** (boss drop equip 의 trailer 에 집중 출현).

스크립트: `tools/recon/analyze_trailer_bonus.py` (신규)

### 1.2 ⭐⭐⭐ Ultimate `+0x14..+0x1c` 9B effect mask 디코드

R64 발견: 4 ultimate (난무 / 난사 / 연쇄 / 나락) 의 `+0x14..+0x1c` 9-byte 영역이 거의 모두 0,
normal active skill 은 0xff/0xfe/0xfd 다수.

가설: 이 영역이 **multi-hit pattern** 또는 **chain effect 인코딩** — ultimate 은 hard-coded effect 사용해서 무의미, normal 은 표 lookup index.

스크립트: `tools/recon/decode_skill_effect_mask.py` (신규)

### 1.3 ⭐⭐ Signed debuff value 검증

R64 발견: i13 의 적 대상 디버프 (드래곤피어 / 사막의폭염 등) value 가 65506/65486 = signed int16 음수.

추가 검증: 다른 dat 파일 (enemy/boss/i12 ring) 의 value 가 모두 signed unsigned 인지 통일 검증.

### 1.4 ⭐⭐ i15_dat 8번째 DES 파일 복호 (사용자 환경 필요)

R63 까지와 동일.

### 1.5 ⭐⭐ FUN_4f358 본문 ARM disassembly

R63/R64 보류. 0x14/0x19 binary literal 의 switch table 의미 확인.

### 1.6 ⭐ boss_dat trailer 6B 가변 영역 디코드

boss = enemy 의 superset (6B 가변 trailer). 이 6B 가 boss-specific stat (예: special skill ID, drop pool, AI flag) 가능.

## 2. 사용자 환경 필요 작업 (보류)

§1.4 DES 8 파일, SMAF→OGG (33 파일), 9,741 unique 대사 LLM 번역 — R63 와 동일.

## 3. Round 64 핵심 산출물 — `game_balance.json` (★★★★★)

```
work/h3/game_balance.json (537KB, schema v1.0)
├── meta:        round 64, schema 1.0
├── stat_enum:   24 codes (R63 master)
├── rarity:      6 prefix classes (R62)
├── items:       529 items × 18 categories (with rarity enrichment)
├── skills:      105 skills × 7 weapon classes (with rank_info)
├── enemies:     161 normal + 161 hard (19B stat decoded)
├── bosses:      15 normal + 15 hard
├── quests:      4 files (with R62 item xref, 20/21)
├── char_classes: 10 playable classes
└── des_status:  8 pending files + algorithm + key
```

이 JSON 이 **Android 리메이크 코드가 직접 import 할 master 데이터**. 모든 R56-R63 발견의 통합.

## 4. R64 신규 매핑 (4 영역)

### 4.1 value scale (★★★★)

| source | scale |
|---|---|
| i12 ring / i16 enchant / equip trailer | **flat** (모두) |
| i13 HP·SP heal (high 0x01, 0x04) | **flat (HP/SP delta)** |
| i13 stat buff (high 0x05-0x12) | **ratio %** (40 = +40%) |
| i13 적 대상 디버프 | **signed int16 음수** (65506 = -30) |
| i18 HP heal | **flat (4 tier)** |
| i18 SP heal | **ratio×10** (200 = 20%) |
| i18 special | **boolean** (value=0) |

### 4.2 effect_type low byte = target enum (★★★)

```
0x02 = self_temp     0x03 = target_inst    0x04 = party_temp
0x12-15 = HP heal t1-4    0x16-18 = SP heal t1-3
0x19 = revive    0x1a = town return    0x1b = town warp    0x1c = special
```

### 4.3 0x14 / 0x19 검색 결과 (★★)

| source | 0x14 | 0x19 |
|---|---:|---:|
| i13 (passive scroll) | 0 | 0 |
| i16 (enchant) | 0 | 0 |
| i17 (quest item) | 0 | 0 |
| equip trailer | 출현 | 출현 |
| binary literal pool (4-aligned) | 11 | 5 |

→ 0x14/0x19 = **equip trailer 전용** (boss drop equip 의 trailer 4B 의 bonus pair 후보) 또는 boss-specific stat.

### 4.4 Ultimate skill diff (★★)

`+0x1d` (R63 rank class): 난무 15, 난사 10, 연쇄/나락 5 — power class 재확인.
`+0x14..+0x1c` 9B 영역: ultimate 모두 0, normal active 는 0xff/0xfe 다수 — **multi-hit / chain effect mask 후보**.

## 5. Hero3 게임 시스템 (R56-R64 누적, 변경 없음)

| 영역 | 파일 / entries | 디코드 상태 |
|---|---|---|
| **전투 데이터** | enemy_dat (161) + enemyh_dat (161) — R56 | ✓ 19B stat block 완전 매핑 (R60) |
| **보스 데이터** | boss_dat (15) + bossh_dat (15) — R58 | ✓ HP +0x0a..+0x0b BE16 (R60) |
| **캐릭터/NPC** | char_dat (10 classes) + npcg_dat (78 NPCs) — R59 | ✓ class layout (R59) |
| **스킬** | s4~s10 = 7 × 15 = 105 skills — R60 | ✓ 4-cat + rank + ultimate sentinel (R64) |
| **아이템** | i0~i14, i16~i18 = 17 파일 480+ items — R60 | ✓ 5 layout + bonus + rarity + value scale (R64) |
| **퀘스트** | quest_*_dat (44+) — R58 | ✓ i17 20/21 (R62) |
| **UI/메뉴** | dat/InGame_txt (196) + menu/*.txt (50) — R60 | ✓ string table format |
| **DES** | dat/des_dat + key `"0EP@KO91"` — R57 | — (NDK runner 보류) |
| **★ Master stat enum** | 0x00~0x1c (24 codes) — R63 | ✓ 100% 매핑 |
| **★ Value scale** | flat / ratio / signed debuff / boolean — R64 | ✓ source 별 분류 |

## 6. 작업 순서 권장 (Round 65)

1. `git status` + `git log --oneline -5` — 현재 상태 확인
2. `git add` + `git commit` Round 64 산출물
3. **equip trailer 177 case 의 0x14/0x19 분포** (`tools/recon/analyze_trailer_bonus.py` 신규)
4. **ultimate `+0x14..+0x1c` 9B mask 디코드** (`tools/recon/decode_skill_effect_mask.py` 신규)
5. **boss_dat trailer 6B 가변 영역** 디코드 (신규)
6. **signed value 통일 검증** (모든 dat 파일 value range scan)
7. **i15_dat NDK runner 처리** (사용자 환경)
8. Round 65 doc 작성 + PROGRESS.md 갱신 + commit

목표 진행률 (Round 65 종료): **~96-98%** (trailer bonus +1%p, ultimate mask +1%p, boss trailer +1%p).

## 7. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (Round 17~64)
- [Round 64 상세](ghidra-round64-balance-export-value-scale-2026-05-19.md) — ★ 이번 라운드 (game_balance.json + value scale + ultimate diff)
- [Round 63](ghidra-round63-stat-enum-final-2026-05-18.md) — master stat enum 완전
- [Round 62](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) — trailer bonus / rarity / quest xref
- [Round 61](ghidra-round61-item-skill-body-decode-2026-05-18.md) — item body / i13·i14 / skill body
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill 일괄 / boss HP / string / item 카탈로그
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4 dat
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES variants
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
