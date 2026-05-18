# Hero3 인수인계 노트 (Round 62 종료 시점, 2026-05-18)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~88-91%**. 게임 데이터 평문 파싱 ~98% 완료 (모든 body + trailer 디코드 완료). 게임 시스템 모델링 84% (item/skill/effect/rarity/quest 매핑 완전). DES 8 파일만 사용자 환경 (NDK runner) 필요.

마지막 commit: `b8da2617 feat:영웅서기3 Round 61 — item body 정밀 디코드 / i13·i14 카테고리 식별 / skill body 디코드 (105 skills + 480+ items)`

**Round 62 산출물 = uncommitted** (다음 commit 시 일괄 포함):
- 신규 doc 1: [`ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md`](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md)
- 신규 recon 스크립트 3: `analyze_item_variants.py` / `decode_skill_rank.py` / `cross_ref_quest_item.py`
- 신규 dump (work/ 폴더, gitignored): `item_variants.{json,log}` / `skill_rank_decoded.{json,log}` / `quest_item_xref.{json,log}`
- PROGRESS.md 갱신 (Round 62 entry + 다음 세션 가이드)
- 이 SESSION_HANDOFF.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ 새 bonus_type code 의미 매핑

R62 에서 trailer 51% 가 (bonus_type, value) × 2 쌍을 보유함을 발견. 식별된 미분류 type code 8개:

| code | 가설 |
|---:|---|
| 0x01 | ? (드물게 등장 2회) |
| 0x03 | ? ($세라핌핸드 EVA+15, $썬샤인스톤 HP+15 와 동반) |
| 0x04 | ? ($메테오스톤+20, $썬샤인스톤+15) |
| 0x08 | **MATK?** (defenders 에 자주, 마법사용 아이템) |
| 0x09 | **MDEF 추가?** 또는 정신력 |
| 0x0b | **마법 회피?** (배리어자켓, 나이트건틀릿) |
| 0x10 | **카오스류?** (카오스후드/슈트/건틀릿) |
| 0x11 | **사격류?** (라이오넬/제비우스/데스리미터 = 라이플 전용) |

스크립트: `tools/recon/decode_effect_handler.py` (신규) — binary 의 FUN_4f358 또는 stat_modify 함수 literal pool grep 으로 type → string 매핑 추출.

### 1.2 ⭐⭐⭐ enchant (i16) tail vs equip trailer 비교

i16 의 4B tail 이 equip trailer (R62 발견) 와 동일 포맷인지 검증. 같다면 enchant = "movable trailer" = base item 의 trailer slot 을 사용자가 자유 부여하는 시스템.

입력: `work/h3/recon/item_decoded.json` 의 i16 layout 과 i0~i11 trailer 비교.

### 1.3 ⭐⭐ rank progression vs req_level 매핑

skill 의 `+0x1d` rank tier (1/2/3) 와 equip 의 req_level (5tier 간격) 의 연결.

가설:
- rank 1 skill ↔ equip req_level 10
- rank 2 skill ↔ equip req_level 25
- rank 3 skill ↔ equip req_level 40

스크립트: `tools/recon/correlate_rank_req_level.py` (신규).

### 1.4 ⭐⭐ rarity prefix → 가격 modifier 분석

R62 의 7-tier rarity (normal / magic / legendary / epic / boss_drop / endgame / quest_reward) 의 price 분포 비교. 가설: magic = base ×1, legendary = ×1.5, epic = ×2, boss_drop = ×3.

### 1.5 ⭐ i15_dat = 8번째 DES 파일 복호 (사용자 환경 필요)

R60/R61 와 동일. 8 DES 파일 일괄 처리 필요.

### 1.6 ⭐ FUN_4f358 본문 정밀 (Ghidra)

R55/R59/R61 보류. **R62 의 bonus_type 매핑 작업과 직접 연결**. R63 1.1 의 prerequisite.

## 2. 사용자 환경 필요 작업 (보류)

§1.5 DES 8 파일, SMAF→OGG (33 파일), 9,741 unique 대사 LLM 번역 (~$0.66) — R61 과 동일.

## 3. 이미 발견한 Hero3 게임 시스템 (Round 56-62 누적)

### 3.1 평문 파싱 완료 + body 디코드 (Round 62 시점)

| 영역 | 파일 / entries | body 디코드 상태 |
|---|---|---|
| **전투 데이터** | enemy_dat (161) + enemyh_dat (161) — R56 | ✓ 19B stat block 완전 매핑 (R60) |
| **보스 데이터** | boss_dat (15) + bossh_dat (15) — R58 | ✓ HP 위치 +0a..+0b BE16 확정 (R60) |
| **캐릭터/NPC** | char_dat (10 classes) + npcg_dat (78 NPCs) — R59 | ✓ class layout (R59) |
| **스킬** | s4~s10_dat = 7 파일 × 15 = 105 skills — R60 | ✓ 4-category (R61) + rank tier @ +0x1d (R62) |
| **아이템** | i0~i14, i16~i18 = 17 파일 480+ items — R60 | ✓ 5 layout (R61) + **trailer = bonus 쌍** (R62) + rarity prefix (R62) |
| **퀘스트** | quest_00/01/10/11_dat (44+ quests) — R58 | ✓ **i17 21 items ↔ quest text 20/21 매칭** (R62) |
| **UI/메뉴** | dat/InGame_txt (196) + menu/*.txt (50) — R60 | ✓ string table format |
| **DES 시스템** | dat/des_dat (824B) + key `"0EP@KO91"` — R57 | — |

### 3.2 DES 암호화 (미해결, 8 파일)

§1.5 참고.

### 3.3 boss/enemy stat block 정밀 layout (R60 확정)

19B stat block: (R61 SESSION_HANDOFF 와 동일)

### 3.4 item 20B equip body layout (R62 갱신)

| Offset | Width | Meaning |
|---|---|---|
| +0..1 | LE16 | **price** (Gold) |
| +2..3 | 2B | pad |
| +4 | byte | **tier index** (0~16, sprite/icon) |
| +5 | byte | **variant** (sprite override; 0xff=default tier sprite) |
| +6..7 | 2B | pad |
| +8 | byte | **req_level** (단조 +5 per tier) |
| +9..11 | 3B | pad |
| +12..13 | LE16 | **stat_primary** (ATK 무기, DEF 방어구) |
| +14..15 | LE16 | **stat_secondary** (무기 sub-damage) |
| **+16..17** | **2B** | **bonus pair 1** (type + value) — R62 신규 |
| **+18..19** | **2B** | **bonus pair 2** (type + value) — R62 신규 |

bonus_type 매핑 (R61 ring + R62 trailer):
- 0x02 HP, 0x05 STR, 0x06 INT, 0x07 VIT, 0x0a AGI
- 0x0c DEF?, 0x0d MDEF?, 0x0e HIT, 0x0f EVA, 0x12 ATK
- 신규 미식별 8개 (§1.1)

### 3.5 item name prefix = rarity class (R62 신규)

| prefix | class | trailer 보너스 패턴 |
|---|---|---|
| (none) | normal | 0 0 0 0 |
| `\|` | magic | 1 쌍 |
| `'` | legendary | 1~2 쌍 |
| `$` | epic | 2 쌍 |
| `{` | boss_drop | 2 쌍 (높은 stat) |
| `@` | endgame | 2 쌍 (tier≥14, 가격 매우 낮음) |
| `}` | quest_reward | 0 (보상용) |

### 3.6 skill body 4-category + rank (R62 갱신)

| cat | 의미 | 클래스당 갯수 | rank @ +0x1d |
|---:|---|---:|---|
| 0 | weapon mastery (passive) | 7 | 1/2/3 (tier-up) |
| 1 | active attack | 3 | 1/2/3 |
| 2 | active buff | 2 | 보통 1 |
| 3 | passive bonus | 3 | 보통 1 |

SP cost 7-tier: 100/200/300/400/500/600/800.

weapon mastery base damage @ +0x09/+0x0a:
| weapon | base | scaling marker @ +0x02 |
|---|---:|---:|
| 창 | 3 | 2 |
| 대검 | 42 | 20 (+0x0b=40 양손 bonus) |
| 단검 | 41 | 2 |
| 건 | 45 | 2 (+0x0c=20 burst) |
| 라이플 | 45 | 20 (+0x0f/+0x11 range) |
| 다크석 | 64 | 2 |
| 홀리석 | 64 | 30 (max scale) |

### 3.7 i17 quest item → quest 매핑 (R62 신규, 20/21)

| quest 파일 | i17 items |
|---|---|
| quest_00_dat | 협곡의성수, 의문의보석, 토레즈시민증, 시크릿카드, 영혼석, 토레즈의서신, 레아의수련목록, 굴베이그의완드 |
| quest_01_dat | 협곡의성수, 토레즈시민증, 토레즈의서신, 오래된보석함, 로얄윈터하츠, 유리엽서, 유리방패, 테너의유물, 영혼석 |
| quest_10_dat | 협곡의성수, 토레즈시민증, 시크릿카드, 토레즈의서신, 오래된보석함, 일레느의노트 |
| quest_11_dat | 시그널펜던트A/B, 협곡의성수, 토레즈시민증, 토레즈의서신, 유리엽서, 유리방패, 운디네의부적, 평화의문장, 총기부속, 영혼사슬 |
| (unmatched) | 반토막난 지도 — 튜토리얼 추정 |

## 4. Hero3 게임 세계 (변경 없음, R61 과 동일)

- 8 main regions: 네메시스숲 / 네오솔티아 / 협곡 / 아스크라 / 엔자크사막 / 토레즈 / 로우엔 평원 / 리파이너의유적
- 2 주인공 (리츠/케이) × 5 클래스 × 7 weapon skill tree
- 14 item categories (8 weapon × 25 + 4 armor + ring/scroll/material/enchant/quest/consumable) = 480+ items
- 15 bosses (R60 HP 확정)

## 5. 작업 순서 권장 (Round 63)

1. `git status` + `git log --oneline -5` — 현재 상태 확인
2. `git add` + `git commit` Round 62 산출물
3. **새 bonus_type code 매핑** (`tools/recon/decode_effect_handler.py` 신규 + binary literal grep)
4. **enchant vs trailer 비교** (`tools/recon/compare_enchant_trailer.py` 신규)
5. **rank ↔ req_level correlation** (`tools/recon/correlate_rank_req_level.py` 신규)
6. **rarity → price modifier 분석**
7. **i15_dat NDK runner 처리** (사용자 환경)
8. 시간 여유 시 FUN_4f358 / FUN_3a028 (Ghidra 보류)
9. Round 63 doc 작성 + PROGRESS.md 갱신 + commit

목표 진행률 (Round 63 종료 시): **~91-94%** (bonus type 매핑 +2%p, enchant 통합 +1%p, rank/req correlation +0.5%p, i15_dat 평문 시 +3%p).

## 6. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (Round 17~62)
- [Round 62 상세](ghidra-round62-item-skill-rank-quest-xref-2026-05-18.md) — ★ 이번 라운드 상세
- [Round 61](ghidra-round61-item-skill-body-decode-2026-05-18.md) — item body / i13·i14 / skill body
- [Round 60](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — skill 일괄 / boss HP / string table / item 카탈로그
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4 dat
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES variants
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-8].md`
- 모든 recon scripts: `tools/recon/`
