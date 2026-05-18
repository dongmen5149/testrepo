# Hero3 인수인계 노트 (Round 60 종료 시점, 2026-05-18)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~82-85%**. 게임 데이터 평문 파싱 ~95% 완료 (4 영역: enemy/boss/skill/item/string). DES 8 파일 (R57+R60)만 사용자 환경 (NDK runner) 필요.

마지막 commit: `4c0dad22 feat:영웅서기3 Round 59 — char/npcg/s4 dat 평문 파싱 (10 classes + 78 NPCs + 15 skills) + 리츠/케이 PLAYER 캐릭터 확정`

**Round 60 산출물 = uncommitted** (다음 commit 시 일괄 포함):
- 신규 doc 1: [`ghidra-round60-skill-item-strings-bosshp-2026-05-18.md`](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md)
- 신규 recon 스크립트 4: `parse_all_skill_dat.py` / `verify_boss_hp_hypothesis.py` / `parse_string_table.py` / `parse_i_dat.py`
- 신규 dump 4: `work/h3/recon/skill_dat_all.{json,log}` / `string_tables.json` / `i_dat_all.{json,log}`
- PROGRESS.md 갱신 (Round 60 entry + 다음 세션 가이드)
- 이 SESSION_HANDOFF.md 갱신

## 1. 즉시 진행 가능한 작업 (자동, 사용자 입력 불필요)

### 1.1 ⭐⭐⭐ item dat body 정밀 필드 매핑

R60에서 17 파일 (480+ items) 평문 파싱 완료. body 19~20B stat block 정밀 디코드 필요.

입력: [`work/h3/recon/i_dat_all.json`](../../work/h3/recon/i_dat_all.json) — 모든 item 의 name + body hex preview.

추정 필드 (가설):
- bytes 0..1 (LE16): 가격 / cost
- bytes 4..5 (BE16): 요구레벨 또는 메인 스탯
- bytes 10..11 (BE16): tier-related (5-tier scaling pattern 0x01/0x07/0x0c/0x11/0x16 관찰됨)
- bytes 12..13 (BE16): 데미지 / 방어력
- bytes 14..15 (BE16): 보조 스탯
- bytes 16..19: flag / 가변 (예: 무기는 +0x14 까지 데미지 + 16~17 element/type)

검증: 같은 카테고리의 5-tier 아이템 (예: 가죽모자→강화가죽모자→...) 의 단조증가 필드를 hunt — `verify_boss_hp_hypothesis.py` 와 같은 brute force 방식.

스크립트 작성: `tools/recon/decode_item_body.py` (parse_s4_dat 재사용 + BE16/LE16 monotonic hunt).

### 1.2 ⭐⭐⭐ i15_dat = 8번째 DES 파일 + 기존 7 DES 일괄 NDK 처리

8 DES 후보 (R57+R60):
| 파일 | 크기 | entropy |
|---|---|---|
| `dat/drop_dat` | 3080B | 7.90 |
| `dat/droph_dat` | 3080B | 7.79 |
| `dat/getitem_dat` | 400B | 7.40 |
| `dat/smith_dat` | 896B | 7.76 |
| `dat/smithh_dat` | 896B | 7.68 |
| `dat/shop_dat` | 72B | 5.92 |
| `dat/shoph_dat` | 72B | 5.89 |
| **`dat/i15_dat`** ★ NEW | **7400B** | **7.97** |

i15_dat = 가장 큰 암호화 파일 → 핵심 master table / shop inventory / weapon stats master 추정. 평문 시 진행률 +5%p.

**Hero5 NDK runner 활용**: `tools/ndk_des_runner/des_runner` (armv7 ELF) + key `"0EP@KO91"` + `dat/des_dat` tables. Android AVD armeabi-v7a 또는 qemu-arm. 자세한 절차: [`tools/ndk_des_runner/README.md`](../../tools/ndk_des_runner/README.md), `docs/h5/SESSION_HANDOFF.md` §진입점 A.

→ [[reference_h5_des_blocker]] 정보 그대로 적용.

### 1.3 ⭐⭐ i13_dat / i14_dat 카테고리 식별

- i13_dat (35 entries, 첫: `자비의손길`) — 스킬북? 마법서? 특수 아이템?
- i14_dat (46 entries, 첫: `붉은용액`) — 희귀 소비? 이벤트 아이템?

body 패턴 분석 + 게임 컨텍스트 (npcg/quest 텍스트와 cross-reference) 로 식별.

### 1.4 ⭐⭐ skill_dat body 정밀 디코드

7 파일 × 15 skills × 30-70B body. 데미지 계수 / 쿨다운 / SP cost / element 필드 식별.

입력: [`work/h3/recon/skill_dat_all.json`](../../work/h3/recon/skill_dat_all.json).

각 클래스의 passive 1~7 (size 38B) 와 active 8 (size 60-80B) 의 body 차이 분석. R59 의 발견 (각 skill 에 한국어 설명 + 30-70B stat block) 확장.

### 1.5 ⭐ FUN_4f358 본문 정밀 (R55/R59 보류)

R55 발견: FUN_4f358 (896B) = int16 sign-extension + cmp #0xc 패턴. **enemy stat reader 가설**.

```bash
python tools/recon/disasm_battle_top_candidates.py
```

R60 의 enemy/boss HP 위치 (+0x0a..+0x0b BE16) 와 일치하는지 확인.

### 1.6 ⭐ FUN_3a028 16-JT 디코드 (R54 보류)

party stats menu dispatcher. 16 entry 매핑 → 어떤 스탯/스킬 화면인지 식별. Round 51 의 decode 패턴 재사용.

## 2. 사용자 환경 필요 작업 (보류)

### 2.1 DES 8 파일 복호화 (R57+R60)

→ §1.2 참고. **i15_dat 신규 추가**.

복호 성공 시 예상 평문:
- `drop_dat`: 적별 drop item 테이블
- `getitem_dat`: 이벤트 item 획득
- `smith_dat`: 대장간 업그레이드 레시피
- `shop_dat`: 상점 inventory (72B = 작음, 단일 list)
- `i15_dat`: master table or master shop list (7400B = 가장 큼)

### 2.2 SMAF→OGG 변환

H3 의 SMAF 음악 파일 33개, paired OGG 없음. `smaf2midi` 등 외부 도구 필요.

### 2.3 9,741 unique 대사 LLM 번역 (~$0.66)

비용 승인 필요. R39 의 scn_v2 26,415 줄 분석 결과 기반.

## 3. 이미 발견한 Hero3 게임 시스템 (Round 56-60 결과)

### 3.1 평문 파싱 완료 (Round 60 시점: 36 파일)

| 영역 | 파일 / entries |
|---|---|
| **전투 데이터** | enemy_dat (161) + enemyh_dat (161) — R56 |
| **보스 데이터** | boss_dat (15) + bossh_dat (15) — R58 |
| **캐릭터/NPC** | char_dat (10 classes) + npcg_dat (78 NPCs) — R59 |
| **스킬** | s4~s10_dat = **7 파일 × 15 skills = 105 skills** — R60 |
| **아이템** | i0~i14, i16~i18 = **17 파일 480+ items** — R60 |
| **퀘스트** | quest_00/01/10/11_dat (44+ quests) — R58 |
| **UI/메뉴** | dat/InGame_txt (196 strings), menu/*.txt (50 strings) — R60 |
| **DES 시스템** | dat/des_dat (824B = FIPS DES tables) + key `"0EP@KO91"` — R57 |

### 3.2 DES 암호화 (미해결, **8 파일** — R57 7개 + R60 1개)

§1.2 표 참고. 모두 같은 key + tables 로 NDK runner 일괄 처리.

DES 정보:
- **Key**: `"0EP@KO91"` (binary 0xac594, 8 bytes ASCII)
- **Algorithm tables**: `dat/des_dat` (824B = 표준 FIPS DES IP/IP⁻¹/E/P/S1-S8/PC1/PC2)
- **변형 시도** (R58): ECB / CBC+zero-IV / CBC+key-IV / parity-adjusted / bit-reversed key 모두 실패
- **유일 해결**: Hero5 NDK runner (armv7 dlsym + MX_desDecrypt)

### 3.3 boss/enemy stat block 정밀 layout (R60 확정)

19B stat block:
| Offset | Width | Meaning |
|---|---|---|
| +0x00 | byte | **level** |
| +0x01..+0x03 | 3B | padding 0 |
| +0x04..+0x05 | BE16 | f4_5 (가설: AI script ID / 무기 ID) |
| +0x06..+0x07 | BE16 | f6_7 (가설: graphics ID / sprite ref) |
| +0x08..+0x09 | BE16 | f8_9 (가설: SP / MP) |
| **+0x0a..+0x0b** | **BE16** | **MaxHP ✓ 확정** |
| **+0x0c..+0x0d** | **BE16** | **CurrentHP** (= MaxHP 초기) |
| **+0x0e..+0x0f** | **BE16** | **EXP / Gold reward ✓** |
| +0x10 | byte | f16 (가설: AGI) |
| +0x11 | byte | f17 (가설: flag) |
| +0x12 | byte | f18 (보통 0) |

trailer:
- enemy: `01 1e` (2B 고정)
- boss: **6B 가변** (R58 발견, 보스별 다름)

### 3.4 Ghidra 분석 진척

(R59 와 동일, 새 분석 없음 — R60 는 데이터 위주)

## 4. Hero3 게임 세계 (퀘스트 메타데이터로 식별)

### 4.1 8 main regions

1. **네메시스숲** — 시작 지역 (블랙헨지, 빛의신당, 주둔지)
2. **네오솔티아** — 솔티안 왕국 수도 (케이 출신지)
3. **협곡** — 분기 지점 (성수 조합, 독기 면역)
4. **아스크라** — 적국 (리츠 출신지, 국경 돌파 후)
5. **엔자크사막** — 동남쪽 사막 (역사학자 NPC)
6. **토레즈** — 광산도시 (소녀 NPC, 유리엽서, 시민증)
7. **로우엔 평원** — 동쪽 평원 (도적, 데몬)
8. **리파이너의유적** — 던전

### 4.2 2 주인공 + 10 클래스 + 7 무기 skill tree

| 주인공 | 5 클래스 | 무기1 | 무기2 | skill files |
|---|---|---|---|---|
| **리츠** (아스크라) | 어썰트워리어 | 창 (i4) | 방패 (i11) | s4 |
| | 디스럽터 | 양손검 (i5) | 건 (i7) | s5+s7 |
| | 건슬링어 | 단검 (i6) | 건 (i7) | s6+s7 |
| | 나이트템플러 | 양손검 (i5) | 홀리마법 (i10) | s5+s10 |
| | 크레이지암즈 | 라이플 (i8) | 건 (i7) | s7+s8 |
| **케이** (네오솔티아) | 버서커 | 양손검 (i5) | 단검 (i6) | s5+s6 |
| | 데스나이트 | 양손검 (i5) | 다크마법 (i9) | s5+s9 |
| | 섀도우워커 | 단검 (i6) | 다크마법 (i9) | s6+s9 |
| | 가디언나이트 | (방패+홀리?) | | s10 |
| | 소울마스터 | 홀리마스터 | | s10 |

### 4.3 적 라인업 (군단 시스템)

- 아스크란 군단 (적국, 가드/워리어/템플러/체이서/엑셀/워락/건너/슈터)
- 코르버스 군단 (워리어/로그/어쌔신/건너)
- 솔티안 군단 (왕국군, 워리어/로그/매지션/위자드/워락)
- 포레스트/와일드 쿠퍼 (야생 동물)
- 일반 (도적 등)

### 4.4 15 bosses (HP 확정 — R60)

- **리츠/케이** (paired, tier 1-3, normal lvl 14/24/32 HP 14080/16896/19456)
- **멜페토/큐** (paired, tier 4, lvl 44 HP 22784)
- 벨루스, 시즈타이탄(×2), 아르보르, 오르도(×2)
- **홀리가디언** (lvl 46/67, final boss 추정)

hard mode HP scaling 2.1~2.5x (boss 별 다름, manually-balanced).

## 5. 작업 순서 권장 (Round 61)

1. `git status` + `git log --oneline -5` — 현재 상태 확인
2. **item body 정밀 디코드 스크립트 작성** (`tools/recon/decode_item_body.py`)
   - input: `work/h3/recon/i_dat_all.json`
   - method: 같은 카테고리 5-tier 단조증가 hunt
3. **i13_dat / i14_dat 카테고리 식별** (다른 카테고리 body 와 패턴 비교)
4. **i15_dat NDK runner 처리** (사용자 환경 필요)
5. **skill body 디코드** (각 skill 의 데미지/SP/cool/element)
6. 시간 여유 시 FUN_4f358 / FUN_3a028 (Ghidra 보류 작업)
7. Round 61 doc 작성 + PROGRESS.md 갱신 + commit

목표 진행률 (Round 61 종료 시): **~85-88%** (item body decode +2%p, i13/i14 식별 +1%p, i15_dat 평문 시 +5%p).

## 6. 참고 문서

- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (Round 17~60)
- [Round 60 상세](ghidra-round60-skill-item-strings-bosshp-2026-05-18.md) — ★ 이번 라운드 상세
- [Round 59](ghidra-char-npcg-skill-parsing-2026-05-18.md) — char/npcg/s4 dat
- [Round 58](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) — boss/quest + DES variants
- [Round 57](ghidra-des-system-and-dat-paths-2026-05-18.md) — DES 시스템 식별
- [reference_h5_des_blocker](../../C:/Users/Ryu/.claude/projects/d--testrepo/memory/reference_h5_des_blocker.md) — H5 NDK runner 정보 (H3 도 동일 적용)
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-8].md`
- 모든 recon scripts: `tools/recon/`
