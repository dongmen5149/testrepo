# Hero3 Ghidra — FUN_9a008 mode 4 sub-JT 디코드 + task field wide-scan + 전투 시스템 검색 (Round 54)

> **세션**: 2026-05-18, Round 54
> **이전 Round**: [ghidra-9a008-interpreter-and-md5-saveload-2026-05-18.md](ghidra-9a008-interpreter-and-md5-saveload-2026-05-18.md) (Round 53)
> **재현 도구**: `tools/recon/decode_9a008_mode4_sub_jt.py` / `disasm_9ada4_status_engine.py` / `disasm_battle_candidates.py` / `find_task_struct_field_readers.py --field 0x9bb4 / 0x9c70`

## 한 줄 요약

Round 53 의 "FUN_9a008 mode 4 dominant (31 entries)" 가설 검증. **mode 4 의 31 entries → 단 8 distinct leaf** (22 epilogue, 7 active states 2/3/4-5/6/7/9/10/30 만 dispatched). task[+0x9bb4] (R24 bit flag) wide-scan 으로 **19 readers** 식별 — top reader FUN_0009ada4 는 사실 FUN_9a008 mode 2 내부 sub-leaf (independent function 아님). task[+0x9c70] (party member array) wide-scan 으로 **27 readers** 식별 — 신규 dispatcher 함수 3개 발견 (**FUN_3a028 16-JT party stats dispatcher / FUN_630e8 render-related driver / FUN_88a30 task[+0xa848] sub-dispatcher**). **전투 시스템 후보 없음 — 모두 menu/UI/state dispatcher**. 가설: **전투가 SCN bytecode opcode 내부에 임베디드** (FUN_8e89e 또는 FUN_9a008 의 leaf 어딘가).

## 1. FUN_9a008 mode 4 (JT_1[4]) 의 31-entry sub-JT (2UA)

JT_1[4] @ 0x9b7e6 의 sub-JT 디코드:
- sub-JT base = sl + 0xffffa3ec = **0xad02c** (self-relative)
- count = 31 entries (cmp #0x1e = 30 max)

**결과: 31 entries → 8 distinct targets** (22 entries = epilogue 0x9a07e):

| state idx | target | 비고 |
|---|---|---|
| 0, 1 | 0x9a07e | epilogue (NO-OP) |
| **2** | 0x9b81a | `cmp r7, #1; beq do_work` — sub-input flag = 1 가드 |
| **3, 30** | 0x9bbbc | `cmp r5, #1 / #2` sub-dispatch ★ paired |
| **4, 5** | 0x9b8d2 | `cmp r1, #9; bhi epilogue` + 9-entry sub-sub-JT @ 0xffffa468 |
| **6** | 0x9bacc | `cmp r3, #7 → 0x9bb10` + `cmp r3, #8 → 0x9bb06` (2-way sub-dispatch) |
| **7** | 0x9bb16 | `cmp r7, #0; beq do_work` + GOT[+0xd28] + GOT[+0x16c] 사용 |
| **8** | 0x9a07e | epilogue |
| **9** | 0x9bb4c | `cmp r4, #1; beq` + GOT[+0xd38] + GOT[+0x16c] (state 7 과 GOT slot 다름!) |
| **10** | 0x9bb94 | `cmp r7, #1; beq` + GOT[+0xd28] + GOT[+0x16c] (state 7 과 동일 GOT slot) |
| 11..29 | 0x9a07e | epilogue (NO-OP) |

### 핵심 인사이트

- **mode 4 의 active state = 7개** (states 2/3/4-5/6/7/9/10/30 합집합). 31-entry capacity 의 **23% 만 활용**.
- state 3 과 state 30 paired = state 30 가 reload/wrap 상태 (마지막 idx) — script bytecode 의 sentinel?
- **state 7 과 state 10 이 동일한 GOT[+0xd28] 접근** = 같은 buffer/object 처리. state 9 는 다른 GOT[+0xd38] = **paired storage system** (player buffer vs enemy buffer 후보!) ★
- state 4/5 의 9-entry sub-sub-JT (cmp #9) → **3중 nested JT** = 더 깊은 sub-opcode dispatch

### 가설: mode 4 = 양측 storage 처리 mode

GOT[+0xd28] + GOT[+0xd38] = **두 인접 GOT slot (16B 간격)**. 이건 전투 시스템의 "player party slot" vs "enemy slot" pair 와 일치. 다만 명확한 HP/damage 산술은 prologue 에서 보이지 않음.

## 2. task[+0x9bb4] (R24 dominant bit flag field) wide-scan (2UC)

`find_task_struct_field_readers.py --field 0x9bb4` 결과:

- **71 verified ctx+field sites in 19 unique funcs** (전체 binary)
- Top readers:
  - **FUN_0009ada4 (41 reads)** ★
  - FUN_00041c6e (5x) — R36 cluster #1 SM child
  - FUN_0009a14e (4x) — FUN_9a008 sub-region
  - FUN_00026a80 (3x) — R43 subsystem router
  - FUN_00009a50 (2x), FUN_00031dc (2x)

### FUN_9ada4 정체 검증

`tools/recon/disasm_9ada4_status_engine.py` 으로 prologue dump → **"FUN_9ada4 는 함수가 아님"** 확인:

```
0x9ada4: ldr  r4, [sp, #0xc]      ; ★ NO push prologue!
0x9ada6: asrs r3, r4, #0x15
0x9ada8: adds r3, r3, r2
0x9adaa: ldr  r3, [r3, #0x10]
0x9adac: ldr  r3, [r3]
...
```

→ **0x9ada4 는 FUN_9a008 (0x9a008..0x9c280) 내부의 mode 2 sub-leaf branch target**. Ghidra 가 별도 function entry 로 잘못 분류. **41 reads of task[+0x9bb4] 는 FUN_9a008 mode 2 의 dispatch 후 leaf 들에 걸쳐 분포**.

**의미**: FUN_9a008 mode 2 = "task[+0x9bb4] bit flag 검사/조작 mode" = **status condition tester/setter** 가설. JRPG status effect (poison/sleep/paralysis) 처리에 적합한 패턴.

## 3. task[+0x9c70] (party member array base) wide-scan (2UC continued)

`find_task_struct_field_readers.py --field 0x9c70` 결과:

- **44 verified ctx+field sites in 27 unique funcs**
- Top readers:
  - **FUN_0003a028 (8 reads)** ★ — 신규
  - FUN_000818f0 (5x) — R50 input dispatcher (이미 known)
  - **FUN_000630e8 (4 reads)** ★ — 신규
  - FUN_00057394 (2x) — R48 render byte_append
  - **FUN_00088a30 (2 reads)** ★ — 신규

3개 신규 dispatcher 함수 본문 분석 (`disasm_battle_candidates.py`):

### 3.1 FUN_3a028 (500B) — **party member 16-JT dispatcher**

```c
void FUN_3a028(int r0_arg) {                              // 1-arg dispatcher
    local[-4] = r0_arg;
    local[-0x14] = r0_arg + 0x10;                          // skip 16B header
    if (local[-0x14] > 0xf) goto epilogue_3a200;           // 16 idx limit
    // Self-relative JT 16 entries @ sl + 0xffff4788
    pc = sl + 0xffff4788 + idx*4 + JT[idx];
}
```

**통계**: 15 BL (13x FUN_4ad10!) + 9 cmp (7x cmp #0) + **12 PC-rel literals 가 모두 0x9c70** = task[+0x9c70] 의 12회 명시적 lookup.

**의미**: 매 dispatch 마다 task[+0x9c70] (= party member array base) 를 다시 fetch + null check (cmp #0). **party member 16-entry JT 가 idx 별로 다른 stat 표시?** Equipment / Status / Skill / Item 메뉴 후보. **NOT 전투** (산술 없음).

### 3.2 FUN_630e8 (3936B) — **render-driven dispatcher**

```c
void FUN_630e8(int r0, int r1) {
    task = FUN_4ad10();
    local[-0x10] = task + 0xa3ac;                          // ★ R51 render sub-struct base
    local[-0x14] = r1 + 5;
    if (cmp local[-0x14], #4) {
        // sub-dispatch
    }
    ...
    BL FUN_75b98 (R50/R51 render flush)
}
```

**통계**: 14 BL (9x FUN_4ad10, 1x FUN_75b98) + 6 cmp + dominant literals 미확인.

**의미**: task[+0x9c70] (party member) + task[+0xa3ac] (render sub-struct) 결합 = **party member rendering** = HUD 또는 character status panel renderer. BL FUN_75b98 = render flush 호출 확인. **NOT 전투**.

### 3.3 FUN_88a30 (1152B) — **task[+0xa848] sub-struct dispatcher**

```c
void FUN_88a30(int r0_arg) {
    local[-4] = r0_arg;
    local[-8] = FUN_8578c();                               // R46 task[+0xa848] getter
    local[-0x30] = local[-4] + 0x10;                        // skip 16B header
    if (local[-0x30] > 0xf) goto epilogue_88e92;            // 16-idx limit
    // Self-relative JT 16 entries @ sl + 0xffff8d24
    pc = sl + 0xffff8d24 + idx*4 + JT[idx];
}
```

**통계**: 13 BL (6x **FUN_861a8** 신규 dominant helper) + 6 cmp + LIT 0x415 x7 (constant — entity record offset?).

**의미**: task[+0xa848] (central screen state, R47-R50) 의 16-entry sub-handler. **save/load menu navigation 후보**. **신규 helper FUN_861a8 (1.6KB+ 잠재)**.

## 4. 전투 시스템 검색 — 종합 결과

R47-R54 의 11개 분석 함수 중 **명확한 전투 시스템 패턴 (HP/MP/damage 산술 + 공격력/방어력 stat lookup) 보이는 함수 없음**.

분석된 후보별 정체:
- FUN_8e89e (16.3KB, R35) — SCN bytecode interpreter (대화/cutscene)
- FUN_9a008 (8.8KB, R52-R54) — 7-mode bytecode interpreter (script)
- FUN_3a028 (500B, R54) — party member 16-JT (stats/equipment menu)
- FUN_630e8 (3.9KB, R54) — render-related driver (HUD)
- FUN_88a30 (1.2KB, R54) — task[+0xa848] sub-dispatcher (save/load)
- FUN_77c78 (R51-R53) — MD5-verified save record reader
- FUN_818f0 (R50-R52) — input dispatcher (keypad)

### 새 가설: 전투 = SCN bytecode opcode 내부

JRPG 모바일 게임 패턴에서 **combat logic 이 stage scripts 의 bytecode opcode 로 임베디드** 되는 경우가 흔함. 특히:
- FUN_8e89e (R35) 의 19 opcodes 또는 11.4KB Korean dialogue sub-interpreter (R37 opcode 0x12)
- FUN_9a008 의 mode 4 state 4-5 (9-entry sub-sub-JT) — 3중 nested dispatch = damage formula 후보
- FUN_9a008 의 mode 2 (task[+0x9bb4] bit flag intensive) = status effect application

**Round 55 작업**: SCN interpreter (FUN_8e89e) 의 opcode 본문 정밀 + FUN_9a008 mode 4 state 4-5 의 9-entry sub-sub-JT 디코드 + **arith-heavy leaf 함수 grep** (mul/subs/asrs 빈도 높은 함수).

## 5. 신규 발견 함수 + 정정 사항

### 신규 함수 (Round 54)

| addr | size | 역할 |
|---|---|---|
| FUN_3a028 | 500B | party member 16-JT dispatcher (equipment/stats menu 후보) |
| FUN_630e8 | 3936B | task[+0x9c70] + task[+0xa3ac] render driver |
| FUN_88a30 | 1152B | task[+0xa848] 16-JT sub-dispatcher (save/load menu 후보) |
| FUN_45f78 | ? | FUN_3a028 의 callee |
| FUN_46890 | ? | FUN_3a028 의 callee |
| FUN_64018 | ? | FUN_630e8 의 callee |
| FUN_4fc7c | ? | FUN_630e8 의 callee |
| FUN_5512c | ? | FUN_630e8 의 callee |
| FUN_5727c | ? | FUN_630e8 의 callee |
| FUN_861a8 | ? | FUN_88a30 의 dominant helper (6 calls) |
| FUN_54648 | ? | FUN_88a30 의 callee |

**known function 총합 추정**: R52 까지 ~120 + R53 추가 ~10 + R54 추가 ~11 = **약 141 known**. Hero3 binary 의 1,433 decompiled entries 중 약 10%.

### 정정 사항

| 가설 | 라운드 | 결과 |
|---|---|---|
| FUN_9ada4 = 독립 함수 (status effect engine) | R54 초반 | **폐기** → FUN_9a008 mode 2 의 sub-leaf branch target (Ghidra 오분류) |
| FUN_9a008 mode 4 = 31-state dense | R53 | **정정** → 31 capacity 중 7 active states 만 사용 (NO-OP 22 entries) |
| FUN_9a008 mode 4 dominant | R53 | 부분 정정 — entry capacity 만 큼, 실제 active state 는 다른 mode 와 비슷 |

## 6. 두 paired GOT slot 발견: +0xd28 vs +0xd38

mode 4 state 7/10 = GOT[+0xd28], state 9 = GOT[+0xd38]. **16B 간격으로 인접한 두 GOT slot** 이 별개 storage object 를 가리킴.

가설: **player party 버퍼 vs enemy 버퍼** 의 paired ptr. 전투 시스템 후보 강력. Round 55 에서 두 GOT slot 의 binary 내 값 + 사용처 wide-scan 필요.

**known GOT slots**: R53 의 25 → R54 추가 (+0xd28, +0xd38) → **27**

## 7. 다음 라운드 (Round 55) 권장 작업

1. **GOT[+0xd28] + GOT[+0xd38] 사용처 wide-scan** — paired storage system 검증 + 전투 후보 강화
2. **FUN_9a008 mode 4 state 4-5 의 9-entry sub-sub-JT @ 0xffffa468 디코드** — 3중 nested JT 최종 leaf 확인 (damage formula 후보)
3. **FUN_8e89e (R35 SCN interpreter) 19 opcode leaves 본문 정밀** — combat opcode 후보 확인
4. **FUN_3a028 의 16-JT @ 0xffff4788 디코드** — 16 party stats menu entries
5. **FUN_88a30 의 16-JT @ 0xffff8d24 디코드** + FUN_861a8 (dominant helper) 본문
6. **arg=+55/+57 menu hotkey 분기 본문** (Round 53/54 이월)
7. **arith-heavy leaf 함수 grep** — `mul/asrs/lsls/subs` 빈도 높은 작은 함수 검색 (damage 계산 후보)

## 부록 — 산출 스크립트

| 스크립트 | 역할 |
|---|---|
| `decode_9a008_mode4_sub_jt.py` | mode 4 의 31-entry sub-JT @ 0xad02c 디코드 + 8 distinct leaf 첫 8 inst dump |
| `disasm_9ada4_status_engine.py` | FUN_9ada4 prologue dump (function 정체 검증) |
| `disasm_battle_candidates.py` | FUN_3a028/630e8/88a30 prologue + stats dump |

raw output: `work/h3/round54_mode4_jt.txt`, `work/h3/round54_9ada4.txt`, `work/h3/round54_battle_candidates.txt`, `work/h3/round54_field_9bb4.txt`, `work/h3/round54_field_9c70.txt`.
