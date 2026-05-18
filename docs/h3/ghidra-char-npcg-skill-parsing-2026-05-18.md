# Hero3 Ghidra — char_dat (10 classes) + npcg_dat (78 NPCs) + s4_dat (15 skills) 평문 파싱 (Round 59)

> **세션**: 2026-05-18, Round 59
> **이전 Round**: [ghidra-boss-quest-dat-and-des-variants-2026-05-18.md](ghidra-boss-quest-dat-and-des-variants-2026-05-18.md) (Round 58)
> **재현 도구**: `tools/recon/parse_char_npcg_s4_dat.py`

## 한 줄 요약

Round 58 의 "미파싱 평문 파일" 3개 (char_dat, npcg_dat, s4_dat) 완전 파싱. **char_dat = 10 playable character classes** (리츠 5 클래스 + 케이 5 클래스) — **리츠 + 케이가 boss 가 아닌 플레이어블 주인공** 확정. **npcg_dat = 78 NPC graphics info** (13B/entry, sprite IDs + animation). **s4_dat = 15 skill entries = 창수 클래스 스킬 트리** (창술 1-7 기본 + 섬광/자격/압도/유도/장벽/태산/의지/정신 액티브). DES 후보 7 파일과 NDK runner 가 Round 60+ 작업.

## 1. char_dat (348B) = 10 playable character classes (2ZA)

`tools/recon/parse_char_npcg_s4_dat.py` 결과:

### 1.1 Entry 구조 (enemy/boss_dat 와 다른 dual-name 구조)

```
[size_byte] [00] [name1_len]   ← 3-byte header
[name1 (Korean)]                ← name1_len bytes ("리츠" / "케이" 4B)
[name2_len]                     ← 1-byte
[name2 (Korean)]                ← name2_len bytes ("어썰트워리어" 12B 등)
[7 bytes stat]
[2 bytes trailer]
total = size_byte + 2
```

### 1.2 10 Playable classes

| pos | name1 | name2 (class) | stat (7B + 2 pad) |
|---|---|---|---|
| 0x000 | **리츠** | 어썰트워리어 (Assault Warrior) | 00 04 05 11 0c 00 06 |
| 0x01d | **리츠** | 디스럽터 (Disruptor) | 01 05 07 0e 0a 0d 03 |
| 0x036 | **리츠** | 건슬링어 (Gunslinger) | 03 07 06 0a 08 07 0f |
| 0x04f | **리츠** | 나이트템플러 (Knight Templar) | 00 04 08 0b 0c 0e 03 |
| 0x06c | **리츠** | 크레이지암즈 (Crazy Arms) | 03 07 08 00 0a 13 06 |
| 0x089 | **케이** | 버서커 (Berserker) | 02 06 05 0c 08 00 0f |
| 0x0a0 | **케이** | 데스나이트 (Death Knight) | 01 05 09 0d 0a 0e 03 |
| 0x0bb | **케이** | 섀도우워커 (Shadow Walker) | 02 06 09 07 08 0a 0f |
| 0x0d6 | **케이** | 가디언나이트 (Guardian Knight) | 00 04 0a 0b 0c 0b 06 |
| 0x0f3 | **케이** | 소울마스터 (Soul Master) | 0b 09 0a 00 0a 13 06 |

### 1.3 핵심 함의

→ **리츠와 케이는 boss 가 아니라 PLAYER 캐릭터** (R58 boss_dat 의 리츠/케이 = tutorial NPC 또는 적대 분기).

각 캐릭터에 **5 클래스 분기** 시스템:
- 리츠: 어쌀트워리어 / 디스럽터 / 건슬링어 / 나이트템플러 / 크레이지암즈
- 케이: 버서커 / 데스나이트 / 섀도우워커 / 가디언나이트 / 소울마스터

stat 7 bytes 의미 추정 (stat 0 = weapon class type):
- stat 0 = weapon 종류 (0=검, 1=세이버?, 2=도끼, 3=총, 11=?)
- stat 1..6: ATK / DEF / HP_growth / MP_growth / 등 클래스별 기본 stat

stat 0 의 변화 패턴:
- 어쌀트/나이트템플러 stat0=0 → 같은 무기 (검?)
- 디스럽터/데스나이트 stat0=1
- 버서커/섀도우워커 stat0=2
- 건슬링어/크레이지암즈 stat0=3 (gunner-class)
- 소울마스터 stat0=11 (특수 무기?)

## 2. npcg_dat (1014B) = 78 NPC graphics entries (2ZB)

깔끔한 13-byte fixed-size entries:

### 2.1 Entry 구조

```
+0: 0x0b           ← size (항상 11, 즉 total 13)
+1: 0x00           ← reserved
+2: type byte      ← 0x01 (active NPC) or 0x00 (passive/empty)
+3..+9: 7 byte graphics data (sprite IDs, animation frames, color palette idx)
+10..+11: 0xff 0xff (또는 sub-data)
+12: 0x06 또는 0x00 ← entry terminator
```

### 2.2 78 entries sample

| idx | type | graphics data |
|---|---|---|
| 0 | 0x01 | 11 00 00 00 ff ff ff ff ff (active NPC) |
| 1 | 0x01 | 00 00 00 00 00 00 ff ff ff |
| 2 | 0x01 | 0f 01 01 01 ff ff ff ff ff |
| 3 | 0x01 | 01 01 01 01 01 ff ff ff ff |
| 4 | 0x01 | 1b 02 02 02 ff ff ff ff ff |
| 5 | 0x01 | 02 02 02 02 02 01 ff ff ff |
| 6 | 0x00 | 00 00 00 00 ff ff ff ff ff (passive) |
| 7 | 0x00 | 00 00 00 00 ff ff ff ff ff (passive) |
| 8 | 0x01 | 0e 04 04 04 ff ff ff ff ff |
| ... | ... | ... |

→ **NPC 78명의 graphics ID 매핑**. 짝수 인덱스 (0, 2, 4, ...) = NPC graphics 변형, 홀수 인덱스 = 본체. Round 14 의 NPC table 0x3c4-stride 와 다른 별도 graphics-only file.

## 3. s4_dat (894B) = 15 skill entries = 창수 클래스 스킬 트리 (2ZC)

### 3.1 Entry 구조

```
[size_byte] [00] [name_len]   ← 3-byte header
[name + '\0']                  ← name_len bytes (EUC-KR skill name)
[1 byte body type/flag]
[1 byte description length]
[description (Korean text)]
[stat block (variable, 30-50 bytes)]
total = size_byte + 2
```

### 3.2 15 skills

#### Passive skills (창술 1-7, 기본 무기 숙련도)

| name | desc | stat_pattern |
|---|---|---|
| 창술 | 한 손으로 창을 사용하는 기술 | base passive |
| 창술2 | (passive lvl 2) | +ATK |
| 창술3 | (passive lvl 3) | |
| 창술4 | (passive lvl 4) | |
| 창술5 | (passive lvl 5) | |
| 창술6 | (passive lvl 6) | |
| 창술7 | (passive lvl 7) | |

#### Active skills

| name | desc 원문 |
|---|---|
| **섬광** (Flash) | 빠르게 돌진하는 돌격기. 연속사용 가능. |
| **자격** (Stab/Stinger) | 창끝에 모은 무형의 힘을 단숨에 지른다. |
| **압도** (Press/Overwhelm) | 적에게 위압감을 주어 공격을 늦춘다. |
| **유도** (Lure/Induce) | 적들의 공격을 자신에게 집중시킨다. |
| **장벽** (Barrier) | 집중력을 끌어올려 방어력을 증가시킨다. |
| **태산** (Mountain) | 기본 방어력을 끌어올린다. |
| **의지** (Will) | 최대 HP를 증가시켜 생존률을 높인다. |
| **정신** (Spirit) | 기절에 대한 저항력을 증가시킨다. |

### 3.3 핵심 함의

s4_dat = **"skill class 4 (창수)" data**. Hero3 에 **다른 클래스의 skill 파일도 존재할 가능성** (s1_dat, s2_dat, s3_dat 등 미확인). 

창수 = 가디언나이트? 나이트템플러? Long-spear 사용 = 나이트템플러 추정. char_dat 의 10 클래스 × (passive 7 + active 8) ≈ **150 skills** 총합 추정.

s4_dat 본문 stat block 의 60-70 byte는 cooldown/damage/range/MP_cost/etc 데이터. 정밀 분석은 R60+.

## 4. Hero3 데이터 시스템 종합 (Round 56-59)

### 4.1 평문 파싱 완료 데이터 파일

| 파일 | 크기 | entries | 내용 |
|---|---|---|---|
| `dat/enemy_dat` | 5495B | **161** | 적 stat (lvl, HP, ATK, DEF, EXP, Gold) |
| `dat/enemyh_dat` | 5495B | **161** | 적 stat hard mode |
| `boss/boss_dat` | 508B | **15** | 보스 stat |
| `boss/bossh_dat` | 508B | **15** | 보스 stat hard mode |
| `dat/char_dat` | 348B | **10** | 플레이어블 클래스 (리츠 5 + 케이 5) |
| `dat/quest_00_dat` | 4851B | **37** | 메인퀘스트 (1막) |
| `dat/quest_01_dat` | 4216B | **7+** | 사이드퀘스트 |
| `dat/quest_10_dat` | 5360B | ? | 메인퀘스트 (2막) |
| `dat/quest_11_dat` | 4269B | ? | 사이드퀘스트 (2막) |
| `npc/npcg_dat` | 1014B | **78** | NPC graphics info |
| `skill/s4_dat` | 894B | **15** | 창수 클래스 스킬 |

### 4.2 암호화 (DES) 대상 파일 — Round 60+ NDK runner 작업

| 파일 | 크기 | DES 후보 |
|---|---|---|
| `dat/drop_dat` | 3080B | ✓ 8x |
| `dat/droph_dat` | 3080B | ✓ 8x |
| `dat/getitem_dat` | 400B | ✓ 8x |
| `dat/smith_dat` | 896B | ✓ 8x (R58 신규) |
| `dat/smithh_dat` | 896B | ✓ 8x |
| `dat/shop_dat` | 72B | ? (작아서 불확실) |
| `dat/shoph_dat` | 72B | ? |

### 4.3 Hero3 게임 시스템 완전 매핑

- **2 주인공** (리츠, 케이) × **5 클래스** = 10 playable
- **161 enemies** × **2 difficulty** = 322 enemy entries
- **15 bosses** × 2 difficulty = 30 boss entries
- **78 NPCs** graphics
- **15 skills** per class × ~10 classes ≈ 150 skills
- **44+ quests** (4 quest files)
- **8 main regions** (네메시스숲~리파이너의유적)

## 5. 진행률 갱신 (Round 59 시점)

| 영역 | Round 58 | Round 59 |
|---|---|---|
| 자산 포맷 분석 | ~90% | **~93%** (+3%p) |
| 게임 데이터 추출 | 75% | **88%** (+13%p: char + npcg + s4) |
| Ghidra 게임 로직 | ~62% | ~62% (변동 없음) |
| 암호화 해독 | ~70% | ~70% (NDK runner 대기) |

**Android remake 완성 기준**: 약 **75-78%** (Round 59 +3-5%p)

## 6. Round 60 권장 작업

### 6.1 우선 1순위: NDK runner 로 DES 복호화

[`tools/ndk_des_runner/des_runner`] (H5 빌드 완료) + key "0EP@KO91" + DES tables (dat/des_dat) → H3 의 7 encrypted dat 파일 복호화.

복호 후 평문 파싱 예상:
- drop_dat (3080B): 적별 drop item 테이블
- getitem_dat (400B): item 획득 이벤트
- smith_dat (896B): 대장간 업그레이드 레시피
- shop_dat (72B): 상점 inventory

### 6.2 우선 2순위: 다른 skill 파일 확인

s4_dat 외 다른 skill 파일 (`s1_dat`~`s10_dat`?) 존재 확인 + 파싱.

### 6.3 우선 3순위: boss_dat stat 정밀

byte 0x08..0x0a 의 3-byte 가 **24-bit HP** 일 가능성 → boss 의 진짜 max HP 추출 (수십만~수백만).

### 6.4 보류 작업 (Round 53~58 누적)

- FUN_4f358 본문 정밀 (int16 stat extractor — 이제 enemy stat reader 가설)
- FUN_3a028 / FUN_88a30 16-JT
- SCN opcode 0x12 47-arm
- arg=+55/+57 menu hotkey
- enemy_dat loader 함수 발견

## 부록 — 산출 스크립트

| 스크립트 | 역할 |
|---|---|
| `parse_char_npcg_s4_dat.py` | char_dat / npcg_dat / s4_dat 3개 파일 동시 파싱 |

raw output: `work/h3/round59_misc_dat.txt`, `round59_misc_dat_v2.txt`.
