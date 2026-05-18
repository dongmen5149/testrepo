# Hero3 Ghidra — FUN_818f0 (event_code × entity_state) double-keyed dispatch matrix + vtable[+0x54] allocator (Round 51)

> **세션**: 2026-05-18, Round 51
> **이전 Round**: [ghidra-input-dispatcher-and-objectb-instance-2026-05-18.md](ghidra-input-dispatcher-and-objectb-instance-2026-05-18.md) (Round 50)
> **재현 도구**: `tools/recon/disasm_818f0_dispatch.py` / `decode_818f0_jt.py` / `disasm_818f0_jt_targets.py` / `disasm_4ad10_3d434.py` / `extract_818f0_handler_ctx_offsets.py` / `decode_818f0_nested_jts.py` / `disasm_92bf8_full.py` / `disasm_3c920_prologue_jt.py` / `trace_vtable_54_allocator.py` / `disasm_75b98_mode7.py` / `check_got_444.py`

## 한 줄 요약

Round 50 의 "FUN_818f0 = 74-entry 입력 디스패처" 발견을 5 라운드 깊이로 확장. **74 entries → 9 distinct primary handlers + 8 handlers 모두 task[+0xac78] (entity state byte) secondary key 로 nested JT dispatch** = 완전한 (event_code, entity_state) double-keyed dispatch matrix 추출. **FUN_4ad10 = task_struct getter** (= `*GOT[+0x444]`, GVM-runtime-injected ptr to 0xb6c80). **FUN_3d434 = cleanup helper** (GOT[+0x284/288/28c] + task[+0xa23c/a24c] zero-out). **FUN_92bf8 = cursor INC/DEC with wraparound** (task[0xa280] cur + task[0xa281] max). **FUN_3c920 letter input** = mode 1-4 dispatch + entity context setup via 0x3c4 multiplier (= Round 14 NPC grid). **vtable[+0x54] = generic alloc(size_t)** (60B 호출). **GOT[+0x18] = ObjectB master ptr 확정**. **FUN_75b98 mode=1 = timer arm (curr+0x7d0 = 2s), mode≠1 = clear**.

## 1. FUN_818f0 의 1st-level JT 74 entries → 9 distinct targets

`tools/recon/decode_818f0_jt.py` 실행 결과 (literal @ 0x81cc0 = `0xffff8800`, JT_base = 0xb2c40 + 0xffff8800 = **0xab440**, self-relative pattern):

| event arg | idx | handler | hits | 비고 |
|---|---|---|---|---|
| -16 (0xf0) | 0 | 0x8199c | 1 | init / clear path (FUN_818f0 fall-through) |
| -15..-6 (10 entries) | 1..10 | 0x82df4 | 10 | 공유 epilogue (NO-OP) |
| -5 (0xfb) | 11 | 0x81b9c | 1 | letter input ★ |
| -4 (0xfc) | 12 | 0x8263a | 1 | sentinel ↓ pair |
| -3 (0xfd) | 13 | 0x823ea | 1 | sentinel ↓ pair |
| -2 (0xfe) | 14 | 0x82a98 | 1 | sentinel ↑ pair (→ FUN_92cc0) |
| -1 (0xff) | 15 | 0x828f6 | 1 | sentinel ↑ pair (→ FUN_92cc0) |
| +0..+54 (55 entries) | 16..70 | 0x82df4 | 55 | 공유 epilogue (NO-OP) |
| +55 (0x37) | 71 | 0x82c2c | 1 | guard: state==2 ‖ state==8 ★ |
| +56 (0x38) | 72 | 0x82df4 | 1 | NO-OP |
| +57 (0x39) | 73 | 0x82d18 | 1 | guard: state==2 ‖ state==8 ★ |

**74 entries → 9 distinct primary handlers** (그 중 1개는 NO-OP epilogue, 1개는 fall-through init, 6개는 sentinel 이벤트, 2개는 special positive 이벤트). 유의미한 application-level handlers = **8개**.

## 2. 2nd-level dispatch: task[+0xac78] entity_state nested JT

`tools/recon/extract_818f0_handler_ctx_offsets.py` 실행 결과: **모든 8 handler 가 동일한 `task[+0xac78]` (= Round 28 의 entity_state record 첫 byte)** 를 secondary key 로 사용. 이건 (event_code, entity_state) double-keyed dispatch.

| arg | ctx offset | cmp limit | nested JT base | dispatch 양상 |
|---|---|---|---|---|
| -16 | task[+0xac78] | <=12 | 0xab568 (13 entries) | 10 distinct targets (state 0/1=8/2/3/4/5/6=11=12/7=epilogue/9/10 각각) |
| -5 | task[+0xac78] | <=12 | 0xab59c (13 entries) | 10 distinct targets (state 0/1/2/3/4/5/6=7=11=12/8/9/10 각각) |
| -3 | task[+0xac78] | <=10 | 0xab5d0 (11 entries) | 5 distinct (state 2=8 / 3=9 / 4 / 10 / 나머지=epilogue) |
| -4 | task[+0xac78] | <=10 | 0xab5fc (11 entries) | 5 distinct (state 2=8 / 3=9 / 4 / 10 / 나머지=epilogue) — **arg=-3 과 동일 그룹** |
| -1 | task[+0xac78] | <=10 | 0xab628 (11 entries) | 5 distinct (state 0=1 / 2=8 / 4 / 10 / 나머지=epilogue) |
| -2 | task[+0xac78] | <=10 | 0xab654 (11 entries) | 5 distinct (state 0=1 / 2=8 / 4 / 10 / 나머지=epilogue) — **arg=-1 과 동일 그룹** |
| +55 | task[+0xac78] | (no JT) | — | guard: `state==2 ‖ state==8 → 본문, else epilogue` |
| +57 | task[+0xac78] | (no JT) | — | guard: `state==2 ‖ state==8 → 본문, else epilogue` |

**핵심 인사이트**:
- arg=-3 과 arg=-4 가 state grouping 패턴 동일 (2=8 / 3=9 / 4 / 10 그룹) → **paired direction events**
- arg=-1 과 arg=-2 가 state grouping 패턴 동일 (0=1 / 2=8 / 4 / 10 그룹) → **paired direction events**
- arg=+55(0x37) 과 arg=+57(0x39) 가 동일 guard `state==2 ‖ state==8` → **paired action events**
- entity_state ∈ {2, 8} 가 가장 active (모든 사인 -1/-2/-3/-4/+55/+57 에서 dedicated path)
- state==0/1, 4, 10 도 frequent active state

arg=-1/-2 handler 의 state==0/1 path 가 BL FUN_92cc0 ('2'/'8' UP/DOWN keypad) 호출 → **-1/-2 = UP/DOWN sentinel, -3/-4 = LEFT/RIGHT sentinel** 추정 (Round 50 의 FUN_3a86c finding 과 정확히 동기화).

## 3. FUN_4ad10 = task_struct getter (= `*GOT[+0x444]`)

`tools/recon/disasm_4ad10_3d434.py` + `check_got_444.py`:

```
0x4ad10..0x4ad28: 18B function
  Reset PIC: sl = pc + 0x67f1e (→ 0xb2c40 GOT base)
  r3 = sl + 0x444         ; GOT slot @ sl + 0x444 (= 0xb3084)
  r0 = *r3                 ; r0 = *GOT[+0x444] = 0xb6c80 (runtime-injected)
  bx lr                    ; return ptr to task_struct
```

**GOT[+0x444] @ 0xb3084 = 0x000b6c80** (binary end = 0xb3a10) → **task_struct 가 binary 외부 GVM-allocated heap region @ 0xb6c80** 에 존재. Round 31 의 "task_struct GVM-injected 확정 (0x444 write 0건)" 가 여기서 정확히 검증됨.

**중요**: 이로써 FUN_818f0 의 모든 handler 가 호출하는 `BL 0x4ad10` 은 단순히 task_struct 포인터를 가져오는 헬퍼. 모든 후속 `[r0 + 0xac78]` 은 **`task_struct[+0xac78]` = entity_state record 첫 byte** (Round 28).

GOT 인접 슬롯 sample (0xb3044..0xb30c4):
- GOT[+0x428] @ 0xb3068 = 0x000b11cc (binary 내 코드/데이터)
- GOT[+0x440] @ 0xb3080 = 0x000a7d84
- **GOT[+0x444] @ 0xb3084 = 0x000b6c80 ★ task_struct ptr (binary 외부)**
- GOT[+0x448] @ 0xb3088 = 0x000c2380 (binary 외부, 다른 GVM struct)
- GOT[+0x44c] @ 0xb308c = 0x000c2280

## 4. FUN_3d434 = global cleanup helper

`tools/recon/disasm_4ad10_3d434.py`:

```c
void FUN_3d434(void) {                                  // arg=-16 + arg=-5 handler 의 첫 BL
    if (*GOT[+0x284] != NULL) {                           // 첫번째 sub-system slot
        ObjectB_master.vtable[+0x58]((*GOT[+0x284]));     // destructor (Round 50 vtable[+0x58])
        *GOT[+0x284] = NULL;
        task[+0xa23c] = 0;                                 // clear state byte
    }
    if (*GOT[+0x288] != NULL) {                           // 두번째 sub-system slot (parallel)
        ObjectB_master.vtable[+0x58]((*GOT[+0x288]));
        *GOT[+0x288] = NULL;
        task[+0xa24c] = 0;
    }
    if (*GOT[+0x28c] != NULL) {                           // 세번째 sub-system slot
        // 더 복잡한 처리 (loop, JT 가능)
    }
}
```

**의미**: 3개의 parallel sub-system slot (GOT[+0x284, +0x288, +0x28c]) 를 destruct + task state field (task[+0xa23c, +0xa24c]) zero-out. 신규 task field **0xa23c, 0xa24c** 발견. arg=-16 ("clear") + arg=-5 ("letter input") 의 진입점에서 호출됨 = sub-system reset.

## 5. FUN_92bf8 = cursor INC/DEC with wraparound (2RB)

200B, 1 BL, 3 cmps. Round 50 의 FUN_92cc0/92d30 (UP/DOWN/LEFT/RIGHT) 와 짝지어진 generic cursor handler.

```c
void FUN_92bf8(int8_t arg /*r0*/) {
    task_struct_t* task = FUN_4ad10();
    if (arg == 4) {                                       // INC direction (4 = "RIGHT/DOWN" sentinel)
        task->byte[0xa280] += 1;
        if ((int8)task->byte[0xa280] >= (int8)task->byte[0xa281]) {
            task->byte[0xa280] = 0;                        // wrap to 0
        }
    } else {                                              // DEC direction (default)
        task->byte[0xa280] -= 1;
        if ((int8)task->byte[0xa280] < 0) {
            task->byte[0xa280] = (int8)task->byte[0xa281] - 1;  // wrap to max-1
        }
    }
}
```

**역할 확정**: `task[0xa280]` = cursor pos, `task[0xa281]` = cursor max bound. FUN_92cc0 ('2'/'8') 과 FUN_92d30 ('4'/'6') 의 single-axis stepper. (UP/LEFT = arg≠4 = DEC, DOWN/RIGHT = arg=4 = INC.) Round 46 의 "task[0xa280] (15 callers) byte reader" 가 정확히 이 cursor field.

## 6. FUN_3c920 = letter input + entity context setup (2RC)

`tools/recon/disasm_3c920_prologue_jt.py`: 2836B, **37 cmp** (Round 46 의 33-arm cmp 확장 — 4 신규 발견), **`d`/`f`/`g`/`h`/`i` ASCII cmps 확정** = lowercase letter keypad mapping.

prologue dispatch (0x3c920..0x3c988):
```c
void FUN_3c920(int r0 /*arg*/, int r1 /*sub_mode*/) {
    local[-4] = r0;
    local[-5] = (byte)r1;
    int mode = local[-4];
    if (mode == 3) goto branch_3cfe0;                     // mode 3 dedicated path
    if (mode > 3) {
        if (mode == 4) {
            FUN_3d308();                                   // mode 4 specific
        }
        FUN_3d408();                                       // shared call
        goto epilogue;
    }
    if (mode == 2) goto branch_3c988;                     // mode 2 (main letter input)
    FUN_3d408();                                           // mode 0/1 default
    goto epilogue;

branch_3c988:                                             // main letter input setup
    local[-0xc] = *(*task_struct[+0x9e28]) + 8;            // Round 27 task[+0x9e28] cluster
    local[-0xd] = task_struct[+0x9c71];                    // Round 45 6-byte cluster (party member?)
    local[-0xe] = task_struct[+0x9c72 + offset];          // entity selector
    int idx_1 = (int8)local[-0xd];
    int idx_2 = (int8)local[-0xe];
    int row_size = 0xf1 * 4 = 0x3c4;                       // ★ Round 14 NPC grid stride
    int col_size = 0x3c;                                   // ★ NPC entry size
    base = *task_struct[+0x9e28] + idx_1 * 0x3c + idx_2 * 0x3c4 + 0xed*4;
    local[-0xf] = *(uint16*)(base + 2);                    // ?? data field
    local[-0x12] = 0x3e8 = 1000;                           // 1 second timeout
    // ... 33+ letter keypad cmps follow (cmp 'd'/'f'/'g'/'h'/'i' + numeric)
}
```

**핵심 의미**: letter input 은 **entity의 name field 편집**용 (party member 또는 save slot name). Round 14 의 0x3c4-stride NPC grid 가 여기서 동일하게 사용됨 → **letter input 이 NPC table 의 name field 를 편집** 할 가능성 (또는 그 위의 hero[N].name 영역). `task[+0x9e28]` = Round 27 cluster (storage base) + `task[+0x9c71]` Round 45 6-byte cluster = entity selector. 0x3e8(=1000ms) 은 letter timeout (multi-tap delay).

## 7. ObjectB vtable[+0x54] = generic alloc(size_t) (2RD)

`tools/recon/trace_vtable_54_allocator.py` (0x85ba0..0x85c20):

```c
// Allocation site
GOT[+0x18] = ObjectB_master_ptr_ptr;                       // ★ GOT[+0x18] 정체 확정
r3 = *(*GOT[+0x18]);                                       // r3 = ObjectB_vtable
r3 = r3[+0x54];                                            // r3 = vtable[+0x54] (function ptr)
r0 = 0x3c;                                                 // 60 bytes
bl veneer_a42a0;                                           // veneer: bx r3 → indirect call
// r0 = newly allocated 60-byte ObjectB instance ptr
*(task[+0xa848] + 8) = r0;                                 // store at task[0xa848] sub-struct +0x08
```

**signature**: `void* alloc(size_t size_in_bytes)`. **runtime-resolved** (vtable[+0x54] is GVM-injected). 

**Post-alloc 흐름** (0x85bce..0x85c1e):
```c
// Read task[+0xa32c] (신규 flag byte)
if (task[+0xa32c] != 0) {
    fp = *GOT[+0xb44];                                     // 신규 GOT slot 1
} else {
    fp = *GOT[+0xb48];                                     // 신규 GOT slot 2
}
local[-0xc] = FUN_77c78(fp);                               // 신규 helper (behavior installer?)
// ... 후속 처리
```

**신규 발견**:
- **GOT[+0x18] = ObjectB master ptr** 확정 (14 known GOT slots → 그 중 ObjectB 의 slot 식별)
- **GOT[+0xb44], GOT[+0xb48]** = 두 신규 GOT slot (behavior function pointers, 분기 선택)
- **task[+0xa32c]** = 신규 flag byte (behavior selector)
- **FUN_77c78** = 신규 helper (behavior installer 추정, 1.6KB+)
- ObjectB known vtable methods: Round 50 의 10개 + vtable[+0x54] alloc 재확인 = **11 known**

## 8. FUN_75b98 mode 분기 풀이 (2RE)

324B, 4 BL, 2 cmps (mode == 1 분기 + dirty flag check).

```c
void FUN_75b98(int r0, int r1, int r2 /*mode*/, int r3) {
    task = FUN_4ad10();
    sub_ctx = &task[+0xa3ac];                              // sub-struct @ task+0xa3ac

    if (sub_ctx[+0xa0] != 0) {                              // 256-byte buffer dirty flag
        memset(&sub_ctx[+0xa0], 0, 256);                    // FUN_9fb78 = memset (3-arg)
    }

    // ObjectB.method[r3?] indirect call (graphics flush) via veneer 0xa42a4
    // GOT[+0x18] (ObjectB) + r3 + sub_ctx[+0xa0] buffer arg
    GOT[+0x18].method?(sub_ctx + 0xa0, ..., r3_field, ...);

    sub_ctx[+0x460] = (byte)r2;                             // mode byte at +0x460
    sub_ctx[+0x9c]  = r1;                                   // r1 stored at +0x9c
    sub_ctx[+0x40]  = 0;                                    // clear at +0x40
    sub_ctx[+0x461] = (byte)r2;                             // mode byte mirror at +0x461

    if (r2 == 1) {                                          // ★ mode == 1 (timer arm)
        timer_slot = *GOT[+0x9ac];                          // 신규 GOT slot
        time_now = ObjectB.vtable[+0x70]();                  // get system time (64-bit via veneer 0xa42a0)
        // 64-bit add: result = time_now + 0x7d0 (2000ms = 2 seconds)
        *timer_slot[0] = (low + 0x7d0) ;                     // adcs for carry → 64-bit
        *timer_slot[4] = high + carry;
    } else {                                                // ★ mode != 1 (예: mode=7) → timer disarm
        timer_slot = *GOT[+0x9ac];
        *timer_slot[0] = 0;
        *timer_slot[4] = 0;
    }
}
```

**역할 확정**:
- task[+0xa3ac] = **render sub-struct base** (256B buffer @ +0xa0 + 여러 byte field)
- 신규 GOT slot **GOT[+0x9ac]** = 64-bit timer slot
- ObjectB.vtable[+0x70] = system time getter (64-bit) — **ObjectB methods → 12 known** (10 [R50] + +0x54 [R51] + +0x70 [R51])
- mode == 1 → arm 2-second timer (예: "press any key" UI prompt)
- mode != 1 (R50 의 mode=7 포함) → disarm timer
- (r0, r1, r3) = graphics flush context (256B buffer + r1 attribute + r3 ObjectB.method selector)

## 9. 신규 task_struct fields + GOT slots

| field/slot | size | 발견 위치 | 의미 |
|---|---|---|---|
| `task[+0xa23c]` | byte | FUN_3d434 cleanup | sub-system 1 active flag |
| `task[+0xa24c]` | byte | FUN_3d434 cleanup | sub-system 2 active flag |
| `task[+0xa32c]` | byte | post-alloc (0x85bce) | behavior selector flag (post-alloc) |
| `task[+0xa3ac+0xa0]` | 256B | FUN_75b98 | render flush buffer |
| `task[+0xa3ac+0x460..461]` | 2B | FUN_75b98 | mode byte mirror |
| `task[+0xa3ac+0x9c]` | word | FUN_75b98 | r1 attribute slot |
| **GOT[+0x18]** | ptr-to-ptr | alloc site | ObjectB master ptr (★ 정체 확정) |
| **GOT[+0x444]** | ptr | FUN_4ad10 | task_struct ptr (runtime-injected, 0xb6c80) |
| **GOT[+0x284]** | ptr | FUN_3d434 cleanup | sub-system slot 1 |
| **GOT[+0x288]** | ptr | FUN_3d434 cleanup | sub-system slot 2 |
| **GOT[+0x28c]** | ptr | FUN_3d434 cleanup | sub-system slot 3 |
| **GOT[+0xb44]** | fp | post-alloc | behavior function ptr 1 |
| **GOT[+0xb48]** | fp | post-alloc | behavior function ptr 2 |
| **GOT[+0x9ac]** | ptr | FUN_75b98 | 64-bit timer slot ptr |
| **GOT[+0x484]** | ? | FUN_75b98 | render call attribute |

GOT 슬롯 known 14 → **23개** 확장.

## 10. ObjectB methods 업데이트

| offset | role | 발견 round |
|---|---|---|
| +0x00 | ? | R20 |
| +0x08 | dominant reader | R28 |
| +0x0c | event handler (ObjectE 이벤트?) | R41 |
| +0x10 | graphics primitive (event 3) | R44 |
| +0x18 | ? | R20 |
| +0x44 | ? | R22 |
| +0x4c | ? | R22 |
| +0x50 | ? | R20 |
| **+0x54** | **alloc(size_t)** ★ | R51 (Round 50 hint 확정) |
| +0x58 | destructor (ptr) | R47/R50 |
| +0x60 | new method | R47 |
| **+0x70** | **system time getter (64-bit)** ★ | R51 |

ObjectB known methods: **10 → 12**.

## 11. FUN_818f0 의 진짜 정체 — 게임 입력 메인 이벤트 dispatcher

종합:

```c
void FUN_818f0(int event_code /*r0*/) {                   // 메인 입력 이벤트 처리 함수
    if (event_code == something) {
        FUN_4ad10(); ... etc                                // 일부 사전 처리
    }
    int idx = event_code + 0x10;
    if ((unsigned)idx > 0x49) goto epilogue_82df4;        // event ∉ [-0x10..0x39]

    switch (idx) {                                          // 74-entry JT @ 0xab440
      case 0:  /* event=-16 */ goto handler_8199c;        // CLEAR/INIT
      case 11: /* event=-5  */ goto handler_81b9c;        // LETTER INPUT
      case 12: /* event=-4  */ goto handler_8263a;        // RIGHT? sentinel
      case 13: /* event=-3  */ goto handler_823ea;        // RIGHT? sentinel paired with -4
      case 14: /* event=-2  */ goto handler_82a98;        // DOWN/UP sentinel (→ FUN_92cc0)
      case 15: /* event=-1  */ goto handler_828f6;        // DOWN/UP sentinel (→ FUN_92cc0)
      case 71: /* event=+55 (0x37, '7' ASCII) */ goto handler_82c2c;  // guard state==2/8
      case 73: /* event=+57 (0x39, '9' ASCII) */ goto handler_82d18;  // guard state==2/8
      default: goto epilogue_82df4;                         // 66 entries → NO-OP
    }
}

// 각 handler 본문 (간략화)
handler_X(...) {
    BL FUN_4ad10;                                           // task = task_struct
    state = task[+0xac78];                                  // ★ entity_state byte (Round 28)
    if (state > LIMIT) goto epilogue;                       // 8/11/13 maximum
    JT[state]();                                            // 2nd-level: state-specific leaf
}
```

**의미**: FUN_818f0 은 **(event_code, entity_state) 2D 매트릭스 디스패처**. 입력 이벤트 코드 ∈ [-16..+57] 의 8 유의미 코드 × entity_state ∈ {0..12} 가 약 **8×8 = 64 가지 상태별 leaf handler** 로 분기. 게임 내 캐릭터/메뉴/대화 모드를 통합 처리하는 핵심 입력 처리 함수.

## 12. 다음 라운드 (Round 52) 권장 작업

1. **30개 leaf handler 본문 매핑** — 각 (event, state) → 어떤 게임 액션? UP→state=2 → walk_north? letter→state=8 → name 한 글자 추가? 등
2. **task[+0xac78..+0xac9d] 38B entity state record 의 모든 field 매핑** — Round 28 partial 확장
3. **FUN_77c78 본문** — behavior installer (vtable[+0x54] alloc 직후 호출, GOT[+0xb44/0xb48] fp 인자)
4. **GOT[+0x284/+0x288/+0x28c]** sub-system slot 의 lifecycle 추적 — 어디서 set 되는가?
5. **GOT[+0xb44/+0xb48]** behavior fp 의 실 target 함수 식별
6. **FUN_0009a008 super function (8.8KB)** 첫 본문 — battle 시스템 후보
7. **FUN_3c920 mode 3 path (0x3cfe0)** + mode 4 path (FUN_3d308) 본문

## 부록 A — 산출 스크립트 인덱스

| 스크립트 | 역할 |
|---|---|
| `disasm_818f0_dispatch.py` | FUN_818f0 dispatch window (0x81960..0x819b0) disasm |
| `decode_818f0_jt.py` | 74-entry primary JT 디코드 (literal @ 0x81cc0) |
| `disasm_818f0_jt_targets.py` | 8 distinct handler 본문 dump (truncated 40 lines each) |
| `disasm_4ad10_3d434.py` | FUN_4ad10 task getter + FUN_3d434 cleanup 본문 |
| `check_got_444.py` | GOT[+0x444] = 0xb6c80 (binary 외부) 확인 |
| `extract_818f0_handler_ctx_offsets.py` | 8 handler 의 ctx offset = 일률 0xac78 검증 |
| `decode_818f0_nested_jts.py` | 6 nested JT 전체 디코드 (state grouping) |
| `disasm_92bf8_full.py` | FUN_92bf8 cursor INC/DEC 전체 disasm |
| `disasm_3c920_prologue_jt.py` | FUN_3c920 prologue + 37 cmp 스캔 |
| `trace_vtable_54_allocator.py` | vtable[+0x54] alloc site + veneer disasm |
| `disasm_75b98_mode7.py` | FUN_75b98 full disasm (mode==1 timer 분기 풀이) |

## 부록 B — round51_818f0_handlers.txt (8 handler raw dump)

`work/h3/round51_818f0_handlers.txt` 에 보존. 8개 distinct handler 각 첫 40 inst dump (총 ~340 lines).
