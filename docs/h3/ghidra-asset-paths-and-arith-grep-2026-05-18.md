# Hero3 Ghidra — paired storage 가설 폐기 + arith-heavy leaf grep + NPC 테이블 indexing 패턴 (Round 55)

> **세션**: 2026-05-18, Round 55
> **이전 Round**: [ghidra-mode4-jt-and-battle-search-2026-05-18.md](ghidra-mode4-jt-and-battle-search-2026-05-18.md) (Round 54)
> **재현 도구**: `tools/recon/scan_got_d28_d38_paired.py` / `dump_ac25c_ac26c_data.py` / `dump_ac1xx_string_table.py` / `find_arith_heavy_leaves.py` / `disasm_battle_top_candidates.py` / `dump_mul_context_95408.py` / `dump_mul_context_4f358_26130.py`

## 한 줄 요약

Round 54 의 "GOT[+0xd28/+0xd38] = player vs enemy 버퍼" 가설을 **완전히 폐기**. 두 슬롯은 binary 내부의 **asset path string table 의 인접 entries** ("/menu/chatacterheader_txt" + "/menu/chatacterbody_txt"). arith-heavy leaf grep 으로 **6개 후보 함수 발견** (FUN_95408 34 muls + FUN_95a64 26 muls + FUN_4de34/26130/4f358/47814) — **그러나 모든 muls 는 Round 14 의 NPC table grid indexing 패턴 (`* 0x3c4 row + * 0x3c col`)** 으로 확인. 산술 후보가 모두 NPC table accessor. **전투 시스템 발견 실패 — 그러나 새로운 강력한 가설**: 적 stats 가 NPC 테이블 (0x3c4-stride) 에 임베디드되어 있음.

## 1. GOT[+0xd28/+0xd38] paired storage 가설 폐기 (2VA)

`tools/recon/scan_got_d28_d38_paired.py` 으로 전체 binary 스캔:

### 1.1 GOT slot raw values

```
GOT[+0xd28] @ 0xb3968 = 0x000ac25c  (binary internal)
GOT[+0xd38] @ 0xb3978 = 0x000ac26c  (binary internal, 16B gap)
```

→ 둘 다 **binary 내부 정적 데이터 영역** (0xac25c, 0xac26c). GOT[+0x18/+0x444/+0x16c] 처럼 GVM-injected runtime ptr 가 아님.

### 1.2 사용처 wide-scan

```
GOT[+0xd28] sites: 7   (0x9a4a6, 0x9a53e, 0x9b7ba, 0x9bb1e, 0x9bb9c, 0x9bf78, 0x9c258)
GOT[+0xd38] sites: 4   (0x9aaa6, 0x9b1c0, 0x9bb58, 0x9c230)
```

**모든 11 reference 가 FUN_9a008 (0x9a008..0x9c280) 내부**. 함수 외부 호출 없음 → FUN_9a008 의 내부 전용 슬롯.

### 1.3 0xac25c/0xac26c 데이터 영역 정체

`tools/recon/dump_ac1xx_string_table.py` byte dump 결과 (0xac150..0xac280):

```
0xac1d0: 02 02 02 0b 0e 00 00 00 00 2f 6c 6f 67 6f 2f 6c   ← /logo/lo
0xac1e0: 6f 67 6f 5f 62 6d 00 00 00 2f 6d 65 6e 75 2f 74   ← /menu/t (continuation)
0xac1f0: 74 6c 65 5f 74 78 74 00 2f 6d 65 6e 75 2f 68 65   ← tle_txt./menu/he
0xac200: 6c 70 68 61 64 65 72 5f 74 78 74 00 2f 6d 65 6e   ← lphader_txt./men
0xac210: 75 2f 68 65 6c 70 62 6f 64 79 5f 74 78 74 00 00   ← u/helpbody_txt
0xac220: 2f 6d 65 6e 75 2f 63 6f 75 6e 74 72 79 68 65 61   ← /menu/countryhea
0xac230: 64 65 72 5f 74 78 74 00 2f 6d 65 6e 75 2f 63 6f   ← der_txt./menu/co
0xac240: 75 6e 74 72 79 62 6f 64 79 5f 74 78 74 00 00 00   ← untrybody_txt
0xac250: 2f 6d 65 6e 75 2f 63 68 61 74 61 63 74 65 72 68   ← /menu/chatacterh
0xac260: 61 64 65 72 5f 74 78 74 00 00 00 00 2f 6d 65 6e   ← ader_txt..../men   ← GOT[+0xd38] @ 0xac26c starts here
0xac270: 75 2f 63 68 61 74 61 63 74 65 72 62 6f 64 79 5f   ← u/chatacterbody_
```

**핵심**: 0xac25c 은 string `/menu/chatacterheader_txt\0` 의 **mid-pointer** (start = 0xac250, offset +0xc = "terhader_txt" 의 시작). 0xac26c 은 **다음 string `/menu/chatacterbody_txt\0` 의 정확한 시작** (32B 정렬 padding 이후).

**의미**: FUN_9a008 의 mode 4 가 이 두 path string 을 직접 reference 하여 **asset 파일 로딩** 수행. 추정 path:
- "header_txt" → 캐릭터 헤더 정보 (이름, 레벨, 직업 등)
- "body_txt" → 캐릭터 본문 정보 (스탯, 인벤토리, 스킬?)

→ FUN_9a008 mode 4 = **character data 화면 로딩/표시 모드**. **paired player/enemy storage 아님**.

**기타 asset path strings** 발견 (Round 55 부수 산출):
- `/logo/logo_bm` (logo image)
- `/menu/title_txt` (title screen)
- `/menu/helphader_txt` + `/menu/helpbody_txt` (help screen) — typo `helphader`
- `/menu/countryheader_txt` + `/menu/countrybody_txt` (country selection)
- `/menu/chatacterheader_txt` + `/menu/chatacterbody_txt` (character info) — typo `chatacter`
- `/menu/menu_b`, `/menu/alp_bm`, `/menu/title_cif`, `/menu/menu_cfi`, `/comm/item_bm`, `/menu/rits_bm`, `/menu/kei_bm`, `/menu/title_bm`, `/menu/menu_txt`, `/comm/shadow_bm`, `/comm/attmsg_bm`, `/comm/number_bm`, `/comm/ui_bm`, `/hero/co...`

원작에 **"chatacter"/"helphader" 등 영어 typo 가 다수** 존재 — 한국 개발사의 J2ME 시기 영문 변수명.

## 2. arith-heavy leaf 함수 grep (2VD)

`tools/recon/find_arith_heavy_leaves.py`: 1,433 함수 entries 중 size 80B~1500B + BL ≤ 4 + arith_score ≥ 20 필터로 30 후보. **mul count 가 강력한 battle indicator** 가설로 정렬.

### 2.1 Top 6 후보 통계

| Func | size | BL | mul | asrs | subs | ldrb | cmp | score |
|---|---|---|---|---|---|---|---|---|
| **FUN_95408** | 1208B | 4 | **34** | 8 | 96 | 12 | 4 | 508 ★ TOP |
| **FUN_95a64** | 988B | 2 | 26 | 4 | 80 | 9 | 4 | 400 ★ 인접 |
| FUN_4de34 | 632B | 2 | 21 | 10 | 44 | 6 | 3 | 292 |
| FUN_8004c | 1064B | 3 | 15 | 32 | 87 | 11 | 8 | 413 |
| FUN_aeec | 1020B | 3 | 15 | 29 | 50 | 4 | 7 | 312 |
| FUN_26130 | 784B | 1 | 14 | 31 | 55 | 5 | 12 | 320 |
| FUN_47814 | 436B | 2 | 13 | 11 | 0 | 8 | 14 | 153 |
| FUN_4f358 | 896B | 1 | 10 | 34 | 64 | 5 | 12 | 323 |

### 2.2 muls context 분석 — battle 가설 폐기

`tools/recon/dump_mul_context_95408.py` + `dump_mul_context_4f358_26130.py` 으로 mul 직전/직후 4 inst 패턴 확인:

**모든 mul 의 직전 패턴**:
```asm
movs r3, #0xf1
lsls r3, r3, #2          ; r3 = 0xf1 << 2 = 0x3c4 = 964
muls r2, r3, r2          ; r2 = 0x3c4 * r2 (row idx)
movs r3, #0x3c           ; r3 = 0x3c = 60
muls r3, r1, r3          ; r3 = 0x3c * r1 (col idx)
adds r3, r2, r3          ; r3 = 0x3c4*row + 0x3c*col
adds r3, r3, r0          ; r3 = table_base + 0x3c4*row + 0x3c*col
```

**핵심**: 이건 **Round 14 의 NPC table grid indexing 패턴 (0x3c4 row stride / 0x3c col stride)**. 모든 후보가 단일 정형 패턴 = **NPC table accessor**.

**가설 정정**: arith-heavy = damage calculator → arith-heavy = **NPC table 다중 lookup 함수** (one function reads multiple entities by row*col index).

### 2.3 FUN_4f358 의 asrs 패턴 — **새 가설: NPC table 의 int16 stat 필드 추출**

asrs 가 34회로 가장 높은 FUN_4f358 의 context:

```asm
ldrh r3, [r3]            ; load 16-bit half-word from entity record
lsls r3, r3, #0x10
asrs r3, r3, #0x10       ; sign-extend i16 → i32
cmp r3, #0xc             ; max 12?
ble ...
```

`ldrh + sign-extend + cmp #0xc` 패턴이 반복 → **entity record 의 int16 필드를 읽어 12 이하 범위 검사**. JRPG 캐릭터 레벨 (1-12, 1-30 등) 또는 stat (atk/def 1-12) 의 전형.

**새 가설**: NPC table (0x3c4-byte stride row + 0x3c-byte stride col) 의 entry 안에 **enemy stats (HP/atk/def/lvl) 가 int16 필드로 임베디드**. FUN_4f358 / FUN_26130 / FUN_8004c 등은 NPC table 에서 stat 을 읽어 화면 표시 또는 전투 계산.

## 3. 전투 시스템 위치 — 가설 갱신

### Round 47-55 분석 요약

| 후보 | 라운드 | 결론 |
|---|---|---|
| FUN_818f0 (input dispatcher) | R50-R52 | input handler, NOT battle |
| FUN_9a008 (7-mode interpreter) | R52-R55 | script bytecode VM (asset 로딩), NOT battle |
| FUN_8e89e (16.3KB SCN interpreter) | R35 | 대화/cutscene bytecode VM |
| FUN_77c78 (save record reader) | R51-R53 | MD5-verified save reader |
| FUN_3a028 / 630e8 / 88a30 (party readers) | R54 | menu/UI/state dispatchers |
| FUN_95408 / 95a64 / 4de34 / 26130 / 4f358 (arith-heavy) | R55 | **NPC table multi-lookup** |

### 새 가설 1: 전투 = NPC table accessor + script opcode 조합

JRPG 모바일 게임 패턴:
- enemy stats (HP/atk/def/lvl/exp/gold) 가 **NPC table row** 에 저장
- 각 0x3c4-byte row 가 **하나의 entity definition** (player class + party + enemies + NPCs 통합)
- 0x3c-byte col 은 **multi-instance slot** (같은 enemy 의 여러 instance, 또는 stat 카테고리 분리)
- 전투 진행 = SCN bytecode (`FUN_8e89e` 또는 `FUN_9a008`) 의 specific opcode 가 `NPC_table[enemy_id][stat_field] -= damage` 호출

### 새 가설 2: NPC table = enemy database

Round 14 의 "0x3c4 grid + +0x3b3 flag" + Round 40 의 NPC dialog/quest 시스템 확정 → NPC table 이 **모든 entity (NPC + monster) 의 통합 DB**.

검증 방법:
- NPC table 의 한 row 의 첫 0x3c byte (= col 0) 를 dump → enemy stat 구조 식별
- "HP" 후보 필드 (16-bit, 1-9999 범위) 와 "atk/def" 필드 (8-bit, 1-99 범위) 의 offset 식별

## 4. 분석 진행률 갱신

### Known facts (Round 55 시점)

- **Hero3 binary structure**: 735,760B, 1,433 decompiled functions, ~141 분석 완료 (~10%)
- **GOT slots**: known 27 (R54 의 +0xd28/+0xd38 = asset path string ptr 추가 확인)
- **task_struct fields**: ~30 known (entity_state 38B record + 9 sub-field 매핑 완료)
- **ObjectB methods**: 14 known (+0x7c/+0x80 = JVM RecordStore 추정)
- **Algorithms identified**: MD5 (FUN_5610c), AES 가능성 (별도 검색 필요), 0x3c4-stride NPC table indexing
- **Major interpreter functions**:
  - FUN_8e89e (16.3KB SCN bytecode interpreter, 19 opcodes)
  - FUN_9a008 (8.8KB 7-mode script VM, 122 sub-opcodes)
  - FUN_818f0 (input event dispatcher, 30 leaf handlers)

### Battle system 미발견 — 확정된 negative result

R47-R55 의 12개 분석 함수 + 30+ arith-heavy 검색 후보 모두 **NPC table accessor / menu dispatcher / asset loader**. 명확한 damage formula (atk-def, mul by lvl, HP-=dmg) 없음.

→ **전투가 NPC table data + SCN opcode 조합으로 분산** 추정. 별도의 "battle.c" 같은 모듈 없음.

## 5. 다음 라운드 (Round 56) 권장 작업

### 5.1 우선 1순위: NPC table row 0 의 raw structure dump

`task[+0x9e28]` (R27 cluster storage base) → first row (0x3c4 bytes) 의 모든 field 분석. 어떤 offset 이 HP/atk/def/lvl 인지 식별. enemy 데이터 첫 entry 직접 검증.

### 5.2 우선 2순위: FUN_4f358 본문 정밀

asrs+ldrh+cmp #0xc 패턴이 반복되는 FUN_4f358 (896B) — int16 stat extraction 함수. 이를 caller chain 으로 추적하여 **상위 호출자 (= battle screen?) 식별**.

### 5.3 우선 3순위: SCN bytecode opcode 0x12 본문 정밀 (R37)

R37 의 발견: "opcode 0x12 = 11.4KB Korean dialogue sub-interpreter (47 arms)". 그 중 일부 arm 이 **damage 계산 opcode** 가능성. 47 arm 의 모든 dispatch target 매핑.

### 5.4 보류된 작업 (Round 53/54/55 누적)

- FUN_9a008 mode 4 state 4-5 의 9-entry sub-sub-JT 디코드
- FUN_3a028 16-JT + FUN_88a30 16-JT 디코드
- arg=+55/+57 menu hotkey 분기 본문
- FUN_439a0 의 12 BL callees (44280/44260/47a14 등)
- FUN_561dc (MD5_Final) + FUN_56164 (MD5_Update) 본문 검증

## 부록 — 산출 스크립트 + raw output

| 스크립트 | 역할 |
|---|---|
| `scan_got_d28_d38_paired.py` | GOT[+0xd28/+0xd38] paired wide-scan (FUN_9a008 내부 11 references) |
| `dump_ac25c_ac26c_data.py` | 0xac25c/+10 raw data → asset path string 확인 |
| `dump_ac1xx_string_table.py` | string table 전체 영역 byte dump |
| `find_arith_heavy_leaves.py` | 1,433 함수 중 arith-heavy 후보 30개 선별 |
| `disasm_battle_top_candidates.py` | top 6 후보 prologue + literal 분석 |
| `dump_mul_context_95408.py` | FUN_95408 의 34 mul context (NPC grid indexing 확인) |
| `dump_mul_context_4f358_26130.py` | FUN_4f358 의 34 asrs context (int16 stat 가설) |

raw output: `work/h3/round55_got_d28_d38.txt`, `work/h3/round55_arith_heavy.txt`, `work/h3/round55_battle_top.txt`, `work/h3/round55_mul_95408.txt`, `work/h3/round55_mul_4f358_26130.txt`.
