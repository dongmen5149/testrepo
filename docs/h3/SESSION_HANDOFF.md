# Hero3 인수인계 노트 (Round 61 종료 시점, 2026-05-18)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~86-89%**. 게임 데이터 평문 파싱 ~98% 완료 (모든 body 필드 디코드 완료). 게임 시스템 모델링 78% (item/skill/effect 매핑 완전). DES 8 파일만 사용자 환경 (NDK runner) 필요.

마지막 commit: `7b855de2 feat:영웅서기3 Round 60 — skill 7 파일 일괄 / boss HP 위치 / string table 246 strings / item 17 파일 480+ items + i15_dat 신규 DES`

**Round 61 산출물 = uncommitted** (다음 commit 시 일괄 포함):
- 신규 doc 1: [`ghidra-round61-item-skill-body-decode-2026-05-18.md`](ghidra-round61-item-skill-body-decode-2026-05-18.md)
- 신규 recon 스크립트 2: `decode_item_body.py` / `decode_skill_body.py`
- 신규 dump (work/ 폴더, gitignored): `item_decoded.{json,log}` / `skill_decoded.{json,log}`
- PROGRESS.md 갱신 (Round 61 entry + 다음 세션 가이드)
- 이 SESSION_HANDOFF.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ item body 의 unknown byte 추가 식별

R61 에서 20B body 의 주요 필드 (price/tier/variant/lvl/stat1/stat2) 매핑 완료. 미식별:
- byte +4 (tier index 0~16) 와 game sprite/icon 매핑
- byte +5 (variant) = color/skin 변형 (0xff=default 외 0x70~0x90 범위 출현)
- 무기 stat_secondary (sub-damage) 정확한 의미 (속성? 관통? 2nd hit?)

스크립트 작성: `tools/recon/analyze_item_variants.py` — variant byte 분포 + sprite 매핑 cross-check.

### 1.2 ⭐⭐⭐ weapon mastery skill body 30B stat block 정밀 디코드

R61 에서 4-category 식별 완료 (weapon_passive 7 + active_attack 3 + active_buff 2 + passive_bonus 3). 미식별:
- weapon_passive 7-tier 각 30B 안의 byte +11/+12 = weapon damage 와 i*_dat sub-stat 비교
- skill rank 별 stat 변화 (rank 1→2→3 의 차이)
- active skill 의 cooldown / range / status_effect 필드 위치

입력: `work/h3/recon/skill_decoded.json` + `tools/recon/decode_skill_body.py` 확장.

### 1.3 ⭐⭐ i17 퀘스트 아이템 ↔ quest_*_dat cross-reference

R58 에서 quest_*_dat 44+ quest 평문 파싱 완료. R60에서 i17 21개 퀘스트 아이템 식별. 매핑:
- 시그널펜던트A/B → 특정 quest?
- 협곡의성수 → "협곡의 독소" quest
- 토레즈시민증 → 토레즈 광산도시 quest
- 등 21개 모두 사용 컨텍스트 추적

스크립트: `tools/recon/cross_ref_quest_item.py` — quest 텍스트에서 item 이름 grep + 위치 정렬.

### 1.4 ⭐⭐ i15_dat = 8번째 DES 파일 복호 (사용자 환경 필요)

7400B = master shop list 또는 master item table 추정. 다른 7 DES 와 함께 NDK runner 일괄 처리.

8 DES 후보:
| 파일 | 크기 | entropy |
|---|---|---|
| `dat/drop_dat` | 3080B | 7.90 |
| `dat/droph_dat` | 3080B | 7.79 |
| `dat/getitem_dat` | 400B | 7.40 |
| `dat/smith_dat` | 896B | 7.76 |
| `dat/smithh_dat` | 896B | 7.68 |
| `dat/shop_dat` | 72B | 5.92 |
| `dat/shoph_dat` | 72B | 5.89 |
| `dat/i15_dat` | 7400B | 7.97 |

`tools/ndk_des_runner/des_runner` (armv7 ELF) + key `"0EP@KO91"` + `dat/des_dat` tables. Android AVD armeabi-v7a 또는 qemu-arm.

### 1.5 ⭐ FUN_4f358 / FUN_3a028 본문 정밀 (Ghidra 보류 작업)

R55/R59 의 미해결. R60의 enemy/boss HP 위치 (+0x0a..+0x0b BE16) 와 일치하는지 확인.

## 2. 사용자 환경 필요 작업 (보류)

§1.4 DES 8 파일, SMAF→OGG (33 파일), 9,741 unique 대사 LLM 번역 (~$0.66) — R60 와 동일.

## 3. 이미 발견한 Hero3 게임 시스템 (Round 56-61 누적)

### 3.1 평문 파싱 완료 + body 디코드 (Round 61 시점)

| 영역 | 파일 / entries | body 디코드 상태 |
|---|---|---|
| **전투 데이터** | enemy_dat (161) + enemyh_dat (161) — R56 | ✓ 19B stat block 완전 매핑 (R60) |
| **보스 데이터** | boss_dat (15) + bossh_dat (15) — R58 | ✓ HP 위치 +0a..+0b BE16 확정 (R60) |
| **캐릭터/NPC** | char_dat (10 classes) + npcg_dat (78 NPCs) — R59 | ✓ class layout (R59) |
| **스킬** | s4~s10_dat = 7 파일 × 15 = 105 skills — R60 | ✓ 4-category 디코드 (R61) |
| **아이템** | i0~i14, i16~i18 = 17 파일 480+ items — R60 | ✓ 5 layout 디코드 (R61) |
| **퀘스트** | quest_00/01/10/11_dat (44+ quests) — R58 | — (텍스트 기반, body 분석 불필요) |
| **UI/메뉴** | dat/InGame_txt (196) + menu/*.txt (50) — R60 | ✓ string table format |
| **DES 시스템** | dat/des_dat (824B) + key `"0EP@KO91"` — R57 | — |

### 3.2 DES 암호화 (미해결, 8 파일)

§1.4 참고.

### 3.3 boss/enemy stat block 정밀 layout (R60 확정, R61 그대로)

19B stat block:
| Offset | Width | Meaning |
|---|---|---|
| +0x00 | byte | **level** |
| +0x01..+0x03 | 3B | padding |
| +0x04..+0x05 | BE16 | f4_5 (AI script ID / 무기 ID 추정) |
| +0x06..+0x07 | BE16 | f6_7 (graphics ID 추정) |
| +0x08..+0x09 | BE16 | f8_9 (SP / MP 추정) |
| **+0x0a..+0x0b** | **BE16** | **MaxHP ✓ 확정** |
| **+0x0c..+0x0d** | **BE16** | **CurrentHP** |
| **+0x0e..+0x0f** | **BE16** | **EXP / Gold reward** |
| +0x10 | byte | AGI (추정) |
| +0x11..+0x12 | 2B | flag / padding |

### 3.4 item 20B equip body layout (R61 신규 확정)

| Offset | Width | Meaning |
|---|---|---|
| +0..1 | LE16 | **price** (Gold) |
| +2..3 | 2B | pad |
| +4 | byte | **tier index** (0~16, sprite/icon) |
| +5 | byte | **variant** (color/skin; 0xff=default) |
| +6..7 | 2B | pad |
| +8 | byte | **req_level** (단조 +5 per tier) |
| +9..11 | 3B | pad |
| +12..13 | LE16 | **stat_primary** (ATK 무기, DEF 방어구) |
| +14..15 | LE16 | **stat_secondary** (무기 sub-damage) |
| +16..19 | 4B | trailing pad (zero) |

### 3.5 skill body 4-category (R61 신규)

| cat | 의미 | 클래스당 갯수 |
|---:|---|---:|
| 0 | weapon mastery (passive) | 7 |
| 1 | active attack | 3 |
| 2 | active buff | 2 |
| 3 | passive bonus | 3 |

SP cost 7-tier: 100/200/300/400/500/600/800.

### 3.6 Ghidra 분석 진척

(R59 와 동일, R60/R61 는 데이터 위주, Ghidra 신규 분석 없음. FUN_4f358/3a028 여전히 보류.)

## 4. Hero3 게임 세계

### 4.1 8 main regions

네메시스숲 / 네오솔티아 / 협곡 / 아스크라 / 엔자크사막 / 토레즈 / 로우엔 평원 / 리파이너의유적

### 4.2 2 주인공 + 10 클래스 + 7 weapon skill tree

| 주인공 | 5 클래스 | weapon (i*) | skill (s*) |
|---|---|---|---|
| **리츠** (아스크라) | 어썰트워리어 | 창(i4) + 방패(i11) | s4 |
| | 디스럽터 | 양손검(i5) + 건(i7) | s5+s7 |
| | 건슬링어 | 단검(i6) + 건(i7) | s6+s7 |
| | 나이트템플러 | 양손검(i5) + 홀리(i10) | s5+s10 |
| | 크레이지암즈 | 라이플(i8) + 건(i7) | s7+s8 |
| **케이** (네오솔티아) | 버서커 | 양손검(i5) + 단검(i6) | s5+s6 |
| | 데스나이트 | 양손검(i5) + 다크(i9) | s5+s9 |
| | 섀도우워커 | 단검(i6) + 다크(i9) | s6+s9 |
| | 가디언나이트 | 방패+홀리? | s10 |
| | 소울마스터 | 홀리마스터 | s10 |

### 4.3 14 item categories (R61 디코드)

8 weapon types (창/대검/단검/건/라이플/다크석/홀리석) × 25 entries + 4 armor slots (헬멧/갑옷/장갑/신발) + 방패 + 반지 + 패시브 스크롤 + 조합재료 + enchant + 퀘스트 + 소비. 총 480+ items.

### 4.4 15 bosses (HP 확정 R60)

§3.3 참고. 리츠/케이 paired (tier 1-3), 멜페토/큐, 벨루스, 시즈타이탄, 아르보르, 오르도, 홀리가디언 (final).

## 5. 작업 순서 권장 (Round 62)

1. `git status` + `git log --oneline -5` — 현재 상태 확인
2. `git add` + `git commit` Round 61 산출물 (이 commit 이후 다음 작업)
3. **item variant/tier 분석** (`tools/recon/analyze_item_variants.py` 신규)
4. **skill weapon_passive 30B 정밀** (decode_skill_body.py 확장)
5. **i17 quest item cross-ref** (`tools/recon/cross_ref_quest_item.py` 신규)
6. **i15_dat NDK runner 처리** (사용자 환경)
7. 시간 여유 시 FUN_4f358 / FUN_3a028 (Ghidra 보류)
8. Round 62 doc 작성 + PROGRESS.md 갱신 + commit

목표 진행률 (Round 62 종료 시): **~89-92%** (item variant +1%p, skill rank decode +2%p, quest cross-ref +1%p, i15_dat 평문 시 +5%p).

## 6. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (Round 17~61)
- [Round 61 상세](ghidra-round61-item-skill-body-decode-2026-05-18.md) — ★ 이번 라운드 상세
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill 일괄 / boss HP / string table / item 카탈로그
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4 dat
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES variants
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-8].md`
- 모든 recon scripts: `tools/recon/`
