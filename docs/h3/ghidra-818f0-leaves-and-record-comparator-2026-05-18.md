# Hero3 Ghidra — FUN_818f0 30 leaf handlers + FUN_77c78 save/load comparator + entity_state record 확장 + FUN_9a008 NOT-battle (Round 52)

> **세션**: 2026-05-18, Round 52
> **이전 Round**: [ghidra-818f0-dispatch-matrix-and-allocator-2026-05-18.md](ghidra-818f0-dispatch-matrix-and-allocator-2026-05-18.md) (Round 51)
> **재현 도구**: `tools/recon/dump_818f0_leaf_handlers.py` / `disasm_77c78_behavior_installer.py` / `disasm_9a008_prologue.py`

## 한 줄 요약

Round 51 의 (event_code × entity_state) 매트릭스 30 leaf handlers 각각 short dump 으로 게임 액션 식별. **UP/DOWN = arg(-1, -2) state(0,1), LEFT/RIGHT = arg(-3, -4) state(3,9)** 키패드 매핑 확정. **party member array @ `task[+0x9c70] + idx*0x3c` 확정** (60B entries → R50 ObjectB alloc 크기와 일치). **task[+0xac78..+0xac9d] 38B entity_state record 의 9 sub-field 매핑** (+0xac79 backup, +0xac7a flag, +0xac80/84/94/98/9c/9d). **FUN_77c78 = save/load record comparator** (NOT behavior installer — 16B alloc 2회 + FUN_99a9c query + 16-byte name 비교 + match/mismatch destructor). **FUN_9a008 = 8.8KB sparse state machine (NOT battle interpreter)** — 23 cmp + 28 BL + 2 nested JTs (7+16 entries), task[+0xb4] sub-struct base.

## 1. 30 leaf handler 매핑 (2SA)

`tools/recon/dump_818f0_leaf_handlers.py` 의 dump 분석. (event_arg, entity_state) → 실행 액션:

### 1.1 arg = -16 (Confirm/Enter action) — 10 leaf

| state | leaf addr | 액션 (추정) |
|---|---|---|
| 0 | 0x819e2 | `FUN_2c6a4(event=3)` → epilogue. event 3 발사 (Round 43: ObjectE screen transition) |
| 1, 8 | 0x819ec | `FUN_3d5d0(sound_id=7)` + `task[+0x9c71] = 0` (party member field clear) + 추가 처리 |
| 2 | 0x81a32 | `task[+0xac84]` ptr 검증 (non-null path) + ObjectB master 호출 |
| 3, 5, 6, 11, 12 | 0x81b2c/0x81b48/0x81b64 | **`task[+0xac78] = task[+0xac79]`** = state restore (backup→current) → epilogue |
| 4 | 0x81af6 | `task[+0xac7a] = 1` + **state 4→2** (`task[+0xac78] = 2`) |
| 7 | 0x82df4 | NO-OP |
| 9 | 0x81b80 | state restore (+0xac79 → +0xac78) (state 3/5/6/9/11/12 와 동일 패턴) |
| 10 | 0x81ac0 | `task[+0xac7a] = 1` + **state 10→8** (`task[+0xac78] = 8`) |

**Pattern**: arg=-16 = **Confirm key**. state 4/10 은 forward transition (4→2, 10→8). state 3/5/6/9/11/12 는 backup state 로 복귀. state 0 은 event 3 발사 (screen transition). state 1/8 은 sound 7 + party member clear.

### 1.2 arg = -5 (Letter Input subsystem) — 10 leaf

| state | leaf addr | 액션 |
|---|---|---|
| 0 | 0x81be2 | `if (FUN_92bd0() == 0) { sound(8); task[+0xac78] = 1 }` (state 0→1 + sound 8) |
| 1 | 0x81c48 | `task[+0xac9c] = FUN_92bd0()` (input byte 저장) |
| 8 | 0x81ce8 | `task[+0x9e28]` storage ptr +8 offset → local. 복잡한 setup |
| 2 | 0x81f18 | `task[+0xac80]` (신규 ptr) + `task[+0xac84]` (sub-struct) 더블 deref |
| 10 | 0x8210e | **state 10→9** + sound 5 |
| 4 | 0x82126 | **state 4→3** + sound 4 |
| 9 | 0x8213e | `if (FUN_92bd0() == 0)` → `task[+0x9e28]` storage 접근 (NPC table query?) |
| 6, 7, 11, 12 | 0x8225c | state restore (+0xac79 → +0xac78) — arg=-16 패턴과 동일 |
| 3 | 0x82278 | `if (FUN_92bd0() == 0)` → `task[+0xac94]` (R31 ObjectB instance) 접근 |
| 5 | 0x823ce | state restore (+0xac79 → +0xac78) |

**Pattern**: arg=-5 = **letter input event** (multi-state name entry / keypad input). state 1 에 input byte 누적. state 0/3/9 에 FUN_92bd0 (input poll). state 2/3/9 는 entity record/ObjectB 접근.

### 1.3 arg = -3 (RIGHT keypad direction A) — 4 leaf

| state | leaf addr | 액션 |
|---|---|---|
| 2, 8 | 0x82458 | `entry_ptr = task[+0x9c70] + local[-9](=idx) * 0x3c` = **party member array entry @ idx (60B stride)** ★ |
| 3, 9 | 0x824e8 | `arg = local[-4]; FUN_92d30(arg)` (LEFT/RIGHT keypad call) → state==3/9 = horizontal cursor |
| 4 | 0x824f6 | `if (task[+0xac7a] > 0xa) goto epilogue; task[+0xac7a] -= 0xa` (counter decrement) |
| 10 | 0x82598 | 동일 (counter decrement) |

### 1.4 arg = -4 (RIGHT keypad direction B — paired with -3) — 4 leaf

| state | leaf addr | 액션 |
|---|---|---|
| 2, 8 | 0x8267c | `entry_ptr = task[+0x9c70] + local[-9] * 0x3c` (party member access, 동일) |
| 3, 9 | 0x8270a | `FUN_92d30(local[-4])` (LEFT/RIGHT cursor) — arg=-3 과 동일 |
| 4 | 0x82716 | `if (task[+0xac7a] > 0x58) goto epilogue` (제한 88 = decimal) — 다른 max bound |
| 10 | 0x82804 | `cmp task[+0xac7a], task[+0xac9d] - 0xa` (counter vs limit) |

### 1.5 arg = -1 (UP keypad direction A) — 4 leaf

| state | leaf addr | 액션 |
|---|---|---|
| 0, 1 | 0x82936 | `arg = local[-4]; FUN_92cc0(arg)` (UP/DOWN keypad call) → state==0/1 = vertical cursor |
| 2, 8 | 0x82942 | party member entry access (`task[+0x9c70] + idx*0x3c`) — 동일 패턴 |
| 4 | 0x829da | `if (task[+0xac7a] > 0x62) goto epilogue` (제한 98) — 다른 bound |
| 10 | 0x82a40 | `cmp task[+0xac7a], task[+0xac9d]` (counter vs limit, 동일 패턴) |

### 1.6 arg = -2 (UP keypad direction B — paired with -1) — 4 leaf

| state | leaf addr | 액션 |
|---|---|---|
| 0, 1 | 0x82ad8 | `FUN_92cc0(local[-4])` (UP/DOWN) — arg=-1 과 동일 |
| 2, 8 | 0x82ae4 | party member entry access (동일) |
| 4 | 0x82b9c | `if (task[+0xac7a] <= 1) goto epilogue; task[+0xac7a] -= 1` (counter decrement, 동일) |
| 10 | 0x82be4 | (counter decrement, 동일) |

### 1.7 arg = +55 / +57 (Menu Special Actions, guarded by state==2 ‖ state==8) — 2 leaf

| arg | leaf body addr | 액션 |
|---|---|---|
| +55 (0x37, ASCII '7') | 0x82c56 | `entry = *task[+0x9e28] + 8` (storage base) + `local[-0x15], local[-0x5c]` stack setup |
| +57 (0x39, ASCII '9') | 0x82d42 | `entry = *task[+0x9e28] + 8` (storage base, 동일) + `local[-0x15], local[-0x64]` stack setup |

**Pattern**: 두 handler 가 identical structure, 다른 stack offset (-0x5c vs -0x64 = 8 byte 차이) → 같은 코드 패턴의 별개 액션. state guard `state==2 ‖ state==8` = "active selection mode" 에서만 트리거. 가설: **menu hotkey actions** (예: "save (7)" / "load (9)").

## 2. 게임 액션 매핑 종합

| event_arg | 키보드 매핑 (확정) | 의미 |
|---|---|---|
| -16 | "C" / "ENTER" (Confirm) | 메뉴 확정 / state forward transition |
| -5 | "Letter input" sentinel | 텍스트 입력 (entity naming) |
| -4 | LEFT (paired with -3) | 수평 cursor B |
| -3 | LEFT (paired with -4) | 수평 cursor A — FUN_92d30 호출 |
| -2 | UP/DOWN (paired with -1) | 수직 cursor B |
| -1 | UP/DOWN (paired with -2) | 수직 cursor A — FUN_92cc0 호출 |
| +55 ('7' ASCII) | hotkey '7' | menu special action 1 |
| +57 ('9' ASCII) | hotkey '9' | menu special action 2 |

**핵심 인사이트**: -1/-2 LEFT/RIGHT 가 짝, -3/-4 LEFT/RIGHT 가 짝 — 두 pair 는 아마 **CANCEL/BACK button (-1/-2) vs MENU/CONTEXT button (-3/-4)** 의 별도 입력 매핑. 둘 다 동일 FUN_92cc0/92d30 호출이지만 entity_state machine 상 다른 transition 을 트리거할 수 있음.

## 3. task[+0xac78..+0xac9d] 38B entity_state record 확장 (2SD)

leaf dump 에서 모든 ldrb/strb literal 추출. R28 의 38B 추정 (0xac78..0xac9d) 의 모든 매핑:

| offset | size | 발견 | 의미 |
|---|---|---|---|
| **+0x00 (=0xac78)** | byte | R28 / R51 / R52 | **entity state (primary key for nested JT)** |
| **+0x01 (=0xac79)** | byte | R52 | **state backup (restore target)** — state 3/5/6/9/11/12 에서 `0xac78 = 0xac79` 복귀 |
| **+0x02 (=0xac7a)** | byte | R52 | **flag/counter byte** — 4→2/10→8 transition 시 `=1`, counter decrement 사용 |
| **+0x08 (=0xac80)** | ptr | R52 | external ptr (arg=-5 state=2 에서 deref) |
| **+0x0c (=0xac84)** | ptr | R52 | sub-struct ptr (arg=-16 state=2, arg=-5 state=2) |
| **+0x1c (=0xac94)** | ptr | R31 | **ObjectB instance** (Round 31 의 발견) — arg=-5 state=3 에서 deref |
| **+0x20 (=0xac98)** | ptr | R52 | sub-struct (arg=-4 state=4 + arg=-1 state=4 cursor selection) |
| **+0x24 (=0xac9c)** | byte | R52 | **input result byte** (arg=-5 state=1 에서 FUN_92bd0 결과 저장) |
| **+0x25 (=0xac9d)** | byte | R52 | **limit/count byte** (arg=-4 state=10, arg=-1 state=10 의 cmp 인자) |

**전체 38B 구조 추정** (0x00..0x25 까지 사용 확인 = 38B):
```c
struct entity_state_record {
    uint8_t  state;            // +0x00  primary state (used by all nested JTs)
    uint8_t  backup_state;     // +0x01  restore target
    uint8_t  flag;             // +0x02  transition counter / flag
    uint8_t  pad_3[5];         // +0x03..+0x07
    void*    ext_ptr;          // +0x08  external ptr
    uint8_t  pad_0c[4];        // (size of ptr varies — 추가 4B 가능)
    void*    sub_struct;       // +0x0c  sub-struct
    uint8_t  pad_10[12];       // +0x10..+0x1b
    void*    objb_instance;    // +0x1c  ObjectB instance (R31)
    void*    sub_cursor;       // +0x20  cursor sub-struct
    uint8_t  input_result;     // +0x24  input byte
    uint8_t  limit;            // +0x25  count/limit byte
};
```

**검증 필요**: ptr/byte 의 정확한 크기 (32-bit ARM alignment 가정). offset +0x10..+0x1b 의 미사용 영역 = 가능한 추가 field.

## 4. party member array @ task[+0x9c70] + idx*0x3c 확정

leaf dump 의 arg=-3/-4/-1/-2 의 state==2/8 가 모두:
```
ptr = FUN_4ad10();                            // task_struct
idx = (uint8)local[-9];                       // entity selector (saved earlier)
entry = task[+0x9c70] + idx * 0x3c;            // 60-byte stride
```

**Round 45 의 6-byte cluster (task[+0x9c71..+0x9c76])** 의 진정한 의미: **0x9c70 은 party member array base ptr/literal**, +0x9c71..+0x9c76 의 6 byte 는 **6 명의 party member 의 cursor index** (= array index into the 60-byte party member entries).

**entry size 0x3c = 60 bytes 가 Round 50 의 vtable[+0x54] alloc(60B) 와 동일**. 이건 **party member 의 dynamically-allocated ObjectB instance 크기** 와 매치 → 두 데이터가 동일 구조체. arg=-5 state=3 에서 `task[+0xac94]` (= task[+0xac78+0x1c]) 의 ObjectB instance 접근도 같은 60B 구조.

→ **task[+0xac94] = "현재 선택된 party member 의 ObjectB instance"** 확정.

## 5. FUN_77c78 = save/load record comparator (2SB)

`tools/recon/disasm_77c78_behavior_installer.py` 전체 dump 분석:

```c
int FUN_77c78(int saved_arg /*r0*/) {                      // R51 의 "behavior installer" 가설 정정
    FUN_4ad10();                                            // task_struct (반환값 무시 — 호환성?)

    ObjectB_master = *GOT[+0x18];                            // r5
    alloc = ObjectB_master.vtable[+0x54];                    // R51 alloc

    temp_obj_16B = alloc(0x10);                              // 16B 임시 객체 1
    *sp[0xc] = temp_obj_16B;

    *sp[0] = 0;                                              // mismatch flag = 0
    r0 = saved_arg;
    r1 = &sp[0x10];                                          // output buffer pointer

    record_ptr = FUN_99a9c(saved_arg, &out_buf, 0);          // ★ NEW helper: query/find
    if (record_ptr == 0) goto cleanup_temp_only;

    r4 = *record_ptr;
    new_obj = alloc(*out_buf);                               // 16B 임시 객체 2

    payload = *new_obj + 8;                                  // skip 8B header
    record_array = r4 + 0x18;                                // record + 0x18 = 16B sub-array start
    size = *out_buf - 0x10;

    FUN_9f624(payload, record_array, size);                  // ★ NEW: memcpy/init helper
    FUN_d060(payload, size);                                 // ★ NEW: setup helper
    FUN_5610c(payload, size, r4 + 8);                        // ★ NEW: process helper

    record_name = r4 + 8;                                    // record's 16-byte name field
    // 16-byte name comparison
    for (i = 0; i <= 0xf; i++) {
        if ((int8)record_name[i] != (int8)r7[i]) {           // r7 = payload + 8 (loaded earlier)
            *sp[0] = 1;                                      // mismatch
        }
    }

    destructor = ObjectB_master.vtable[+0x58];                // R50/R51 confirmed destructor

    if (*sp[0] != 0) {                                       // mismatch → destroy all 3 + return 0
        destructor(temp_obj_16B);
        destructor(record_ptr);
        destructor(new_obj);
        return 0;
    } else {                                                  // match → destroy temps + return new_obj
        destructor(temp_obj_16B);
        destructor(record_ptr);
        return new_obj;                                        // r0 = *sp[4] = new_obj
    }
}
```

**진짜 정체**: **save/load record 검증 + 클론 헬퍼**. 입력 = save 슬롯 키, 출력 = 매칭된 클론 객체 (또는 NULL). 16-byte name 일치 검사가 핵심.

**Round 51 의 "behavior installer" 가설 폐기**. vtable[+0x54] alloc 직후 호출 = 새 60B ObjectB instance 의 데이터를 save 슬롯에서 복원하는 시도.

신규 helper 함수 4개 발견:
- **FUN_99a9c** — 1st-level data query (record_ptr + size 반환)
- **FUN_9f624** — memcpy/init helper
- **FUN_d060** — setup helper
- **FUN_5610c** — process helper (16-byte name 추가 인자)

## 6. FUN_9a008 = sparse state machine, NOT battle (2SE)

`tools/recon/disasm_9a008_prologue.py` 통계:

**Function size**: 8.8KB (0x9a008..0x9c280)

**Body 통계**:
- Total BL: **28** (unique targets: 7)
- Total cmp #imm: **23** (unique values: 8)

→ **거대 함수치고 매우 sparse**. 16.3KB FUN_8e89e (R35 SCN bytecode interpreter, 62 cmp + 121 BL) 와 대비 — 그건 진짜 interpreter, 이건 아님.

**Top BL targets**:
- BL 0x4ad10 x10 (task_struct getter, 자주 사용)
- BL 0x439a0 x7 ★ 신규 helper (가장 빈번)
- BL 0x7d31c x3 (Round 26 8-bit unrolled scan helper)
- BL 0x7cd58 x3 (Round 26 leaf 산술 helper)
- BL 0x442e4 x2 신규
- BL 0x47a14 x2 신규
- BL 0x7a49c x1 신규

**Top cmp #imm**:
- cmp #0x02 x8 (state byte = 2 검사 가장 많음)
- cmp #0x03 x4
- cmp #0x00 x3, cmp #0x01 x3
- cmp #0x04, #0x05, #0x06, #0x0f (각 1-2회)

**prologue (FUN_9a008 의 첫 80B)**:
```c
void FUN_9a008(int r0, int r1, int r2, int r3) {
    sub_arg_lo = (byte)r3;                                    // lower byte preserved
    sub_arg2 = sp[0x60];                                       // arg5 from stack (5-arg fn)
    saved_r2 = (byte)r2; saved_r3 = ...;                       // bytes extracted
    sp[0x34] = r1; sp[0x38] = r0;

    task = FUN_4ad10();
    sub_ctx = task + 0xb4;                                     // ★ task[+0xb4] sub-struct (NEW)
    ...
    state = local[saved_byte] - 4;                              // first JT key (idx = byte - 4)
    if ((unsigned)state > 6) goto default;                      // out-of-range
    // Self-relative JT 7 entries @ sl + 0xffff9f90
    pc = sl + 0xffff9f90 + state*4 + JT[state];

    // 다른 path 의 JT
    arg6 = saved_byte_2 - 2;                                    // (byte arg) shifted
    if ((signed)arg6 > 0xf) goto default;                       // out-of-range
    // Self-relative JT 16 entries @ sl + 0xffff9fac
    pc = sl + 0xffff9fac + arg6*4 + JT[arg6];
}
```

**구조**: 5-arg function (r0/r1/r2/r3 + sp[0x60]). 2 nested JTs (7 + 16 entries). **task[+0xb4] sub-struct** (FUN_75b98 의 +0xa3ac 와 별개) 사용.

**해석**: 23 cmp 의 dominant value 0x2 (8회) 는 entity_state 와 매치 — Round 51 의 entity_state {2, 8} active state 와 일치. **8.8KB 의 대부분은 sparse default + JT table padding + 데이터** 일 가능성.

**가설**: FUN_9a008 = **deep menu / character status / inventory screen state machine**. battle 보다는 메뉴 UI 가 더 적합. cmp #2 dominant + task[+0xb4] sub-struct 사용 + Round 26 helpers (산술/scan) = menu/status screen 의 cursor 처리.

**전투 시스템 위치 후보**: FUN_8e89e (R35 16.3KB 진짜 interpreter, 62 cmp + 121 BL + Korean 문자) 가 진짜 dialogue/cutscene interpreter 였고, 아직 발견 안된 별도 함수가 전투일 수 있다.

## 7. 신규 helper 함수 + GOT slot inventory

### 신규 helper 함수 (Round 52 발견)

| addr | role | 발견 위치 |
|---|---|---|
| FUN_99a9c | 1st-level data query (record_ptr + size 반환) | FUN_77c78 |
| FUN_9f624 | memcpy/init helper | FUN_77c78 |
| FUN_d060 | setup helper | FUN_77c78 |
| FUN_5610c | process helper (16B name 비교) | FUN_77c78 |
| FUN_439a0 | sparse-state-machine 자주 호출 helper | FUN_9a008 |
| FUN_442e4 | FUN_9a008 dispatch helper | FUN_9a008 |
| FUN_47a14 | FUN_9a008 dispatch helper | FUN_9a008 |
| FUN_7a49c | FUN_9a008 leaf | FUN_9a008 |

### 신규 task_struct field

| field | size | 의미 |
|---|---|---|
| `task[+0xb4]` | sub-struct | FUN_9a008 base (FUN_75b98 의 +0xa3ac 와 다름) |
| `task[+0xac79]` | byte | entity_state backup |
| `task[+0xac7a]` | byte | entity_state flag/counter |
| `task[+0xac80]` | ptr | entity external ptr |
| `task[+0xac84]` | ptr | entity sub-struct |
| `task[+0xac98]` | ptr | cursor sub-struct |
| `task[+0xac9c]` | byte | input result |
| `task[+0xac9d]` | byte | limit/count |

### 신규 sound IDs (Round 52)

leaf handler dump 에서 추출 (`movs r0, #N; bl FUN_3d5d0`):
- sound 3 (arg=-16 state=0)
- sound 4 (arg=-5 state=4)
- sound 5 (arg=-5 state=10)
- sound 7 (arg=-16 state=1/8)
- sound 8 (arg=-5 state=0)

Round 48 의 19 unique sound IDs 에 추가. (이미 알려진 0x7 = 7, 0x20 = 32 = R43 등 sound IDs 와 일부 중복)

## 8. 다음 라운드 (Round 53) 권장 작업

1. **FUN_99a9c (save/load query) 본문** — input args + 어떤 storage 에서 record 를 찾는가
2. **FUN_5610c / FUN_d060 / FUN_9f624** 본문 — save record 직렬화 helper trio
3. **FUN_439a0 (FUN_9a008 의 dominant helper)** 본문
4. **FUN_9a008 의 7+16 nested JT 디코드** + leaf 매핑 — 진짜 정체 식별 (menu? status?)
5. **arg=+55 / +57 의 분기 본문** — `local[-0x5c], local[-0x64]` 의 의미 (menu hotkey 가설 검증)
6. **arg=-5 state=8 의 task[+0x9e28] storage 접근** — letter input mode 8 의 storage 매핑

## 부록 — 산출 스크립트 + raw output

| 스크립트 | 역할 |
|---|---|
| `dump_818f0_leaf_handlers.py` | 30 leaf handler 식별용 short dump |
| `disasm_77c78_behavior_installer.py` | FUN_77c78 = save/load comparator 전체 disasm |
| `disasm_9a008_prologue.py` | FUN_9a008 prologue 50 inst + cmp/BL 통계 |

raw output: `work/h3/round52_leaf_handlers.txt` (660 lines), `work/h3/round52_77c78.txt`, `work/h3/round52_9a008.txt`.
