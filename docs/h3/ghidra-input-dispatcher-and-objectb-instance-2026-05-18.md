# Hero3 Ghidra — FUN_818f0 입력 디스패처 + FUN_3a86c 메뉴 nav + ObjectB instance @ +0x08 (Round 50)

> **세션**: 2026-05-18, Round 50
> **이전 Round**: [ghidra-a848-deferred-fields-and-letter-input-jt-2026-05-18.md](ghidra-a848-deferred-fields-and-letter-input-jt-2026-05-18.md) (Round 49)
> **재현 도구**: `tools/recon/decode_3a86c_jt.py` / `disasm_3a86c_handlers.py` / `disasm_92d30_full.py` / `disasm_82df4_full.py` / `disasm_75b98_full.py` / `trace_a848_08_context.py` / `disasm_818f0_prologue.py`

## 한 줄 요약

Round 49의 FUN_3a86c 16-JT dispatcher 발견을 확장. Round 50에서 **JT 16 entries → 단 4개 distinct handlers 디코드** (-1/-2/-3/-4 = 메뉴 nav, -5 = letter input, -16 = clear) + **FUN_92d30 = '4'/'6' LEFT/RIGHT keypad nav (FUN_92cc0의 짝꿍)** + **task[0xa848]+0x08 = 동적 할당된 ObjectB 인스턴스 포인터** (vtable[+0x54] = alloc, **vtable[+0x58] = destructor 확정!**) + **FUN_818f0 정정 = 74-entry JT 입력 디스패처** (NOT iteration loop).

## 1. FUN_3a86c JT 16 entries — 4 distinct handlers

### 1.1 Self-relative JT 디코드 (2QA)

Round 49의 disasm 패턴 `pc = sl + JT[idx*4]` 에서 LITERAL1 = LITERAL2 = 0xffff481c (동일 literal pool slot @0x3a9d8). 즉 **self-relative JT pattern**:
- JT_base = sl + LITERAL1 = 0xb2c40 + 0xffff481c = **0xa745c** (binary 내!)
- 각 entry는 JT_base 기준 self-relative offset → target = JT_base + JT[idx]

### 1.2 16 entries → 4 distinct handlers

`tools/recon/decode_3a86c_jt.py` 결과:

| entity_arg | idx | JT[idx] (signed) | Handler | 의미 |
|---|---|---|---|---|
| **-16 (0xf0)** | 0 | -445342 | **0x3a8be** | (Round 49 path: strb -1 = sentinel clear) |
| -15..-6 (10 entries) | 1..10 | -445074 | **0x3a9ca** | **NO-OP / EPILOGUE** (그냥 return) |
| **-5 (0xfb)** | 11 | -445342 | **0x3a8be** | (Round 49 path: BL FUN_3c920 letter input) |
| **-4 (0xfc)** | 12 | -445136 | **0x3a98c** | **INCREMENT-AND-CLAMP** (cursor DOWN) |
| **-3 (0xfd)** | 13 | -445194 | **0x3a952** | **DECREMENT-AND-WRAP** (cursor UP) |
| **-2 (0xfe)** | 14 | -445136 | **0x3a98c** | (same as -4: DOWN) |
| **-1 (0xff)** | 15 | -445194 | **0x3a952** | (same as -3: UP) |

### 1.3 handler 0x3a98c — INCREMENT-AND-CLAMP (Cursor DOWN)

```c
// pseudo-code
{
    ctx = context_getter();
    counter_addr = ctx + lit1;
    byte_a = (*counter_addr) + 1;             // cursor++
    *(ctx + lit2) = byte_a;                    // store new cursor
    byte_b = (*(ctx + lit3)) - 1;              // max - 1
    if (byte_a > byte_b)                       // overflow
        *(ctx + lit4) = 0;                     // wrap to 0
}
```

**메뉴 cursor DOWN** (or NEXT) 동작 — 카운터 1 증가, max 초과 시 0 으로 wrap.

### 1.4 handler 0x3a952 — DECREMENT-AND-WRAP (Cursor UP)

```c
// pseudo-code
{
    ctx = context_getter();
    byte_a = (*counter_addr) - 1;              // cursor--
    *(ctx + lit2) = byte_a;
    if (byte_a < 0) {                          // underflow
        byte_max = (*(ctx + lit3)) - 1;
        *(ctx + lit4) = byte_max;              // wrap to max-1
    }
}
```

**메뉴 cursor UP** (or PREV) 동작 — 카운터 1 감소, 음수 시 max-1 으로 wrap.

### 1.5 handler 0x3a9ca — EPILOGUE

```
mov sp, r7; pop {r3}; mov sl, r3; pop {r4, r7, pc}
```

entity_arg -15..-6 인 10가지 경우 모두 NO-OP 으로 분기. 함수 단순 return.

### 1.6 FUN_3a86c 종합

```c
int FUN_3a86c(int sub_mode /*r0*/, int entity_arg /*r1, signed [-0x10..-1]*/) {
    if (entity_arg + 0x10 > 0xf) return;                    // range guard
    switch (entity_arg) {
        case -16: ctx_byte = -1; break;                      // CLEAR sentinel
        case -5:  FUN_3c920(sub_mode, ctx_byte); break;     // letter input
        case -4: case -2: cursor_inc_and_clamp(); break;     // DOWN/NEXT
        case -3: case -1: cursor_dec_and_wrap(); break;      // UP/PREV
        default: /* -15..-6 */ break;                        // NO-OP
    }
}
```

**FUN_3a86c = "menu cursor navigation + letter input" subsystem entry**. sub_mode=#2 (from FUN_818f0 call) = keypad mode for FUN_3c920 letter input.

## 2. FUN_92d30 — 수평 keypad 네비게이션 (2QB)

```c
int FUN_92d30(int arg) {  // r0 = input code
    if (arg == '4' || arg == -3) { FUN_92bf8(3); return 1; }   // LEFT
    if (arg == '6' || arg == -4) { FUN_92bf8(4); return 1; }   // RIGHT
    return 0;
}
```

ASCII 키패드 코드 + 음수 sentinel 양쪽 지원. Round 46 의 FUN_92cc0 ('2'/'8' UP/DOWN) 와 짝꿍.

### 2.1 완전한 4방향 phone keypad 체계

| Function | 방향 | ASCII | Sentinel | FUN_92bf8 mode |
|---|---|---|---|---|
| FUN_92cc0 (R46) | UP | '2' (0x32) | -1 | 1? |
| FUN_92cc0 (R46) | DOWN | '8' (0x38) | -2 | 2? |
| **FUN_92d30 (R50)** | **LEFT** | '4' (0x34) | -3 | **3** |
| **FUN_92d30 (R50)** | **RIGHT** | '6' (0x36) | -4 | **4** |

**FUN_92bf8 (sub-helper)** 가 mode 1/2/3/4 로 호출됨 → mode 별 직접 분기 가능성.

**참고**: FUN_3a86c 의 -1/-2 (UP/DOWN) 와 -3/-4 (cursor inc/dec) 의 의미가 FUN_92cc0/92d30 의 -1/-2 (UP/DOWN) 와 -3/-4 (LEFT/RIGHT) 와 다름. 즉 **음수 sentinel은 호출 컨텍스트마다 다르게 해석됨** — 통일된 의미 체계가 아니라 호출 함수 별 local convention.

## 3. task[0xa848]+0x08 = 동적 할당된 ObjectB 인스턴스 포인터 (2QD)

Round 49의 +0x08 finding (7 reads + 3 writes, DOMINANT new field) 의 컨텍스트 추적
(`tools/recon/trace_a848_08_context.py`):

### 3.1 FUN_85e88 (84B, 가장 단순) — 순수 free 패턴

```c
void FUN_85e88(void) {
    ptr = FUN_85578c();                       // ptr = &task[0xa848]
    handle = ptr->[+8];                        // (R) handle = +0x08 (지금 할당된 객체 포인터)
    if (handle != 0) {                          // 비제로면
        global = *(sl + lit);                    // ObjectB GOT slot dereference
        method = global->[0]->[+0x58];           // vtable[+0x58]
        method(handle);                           // bl 0xa429c (indirect call) — DESTRUCTOR
        ptr->[+8] = 0;                            // (W) clear pointer
    }
}
```

### 3.2 FUN_85b18 (880B) — free-then-alloc 패턴

```c
void FUN_85b18(/* args */) {
    ptr = &task[0xa848];
    handle = ptr->[+8];                        // (R)
    if (handle != 0) {
        ptr->[+8] = vtable[+0x58](handle);      // DESTRUCT (via vtable[+0x58])
        ptr->[+8] = 0;                           // (W) clear
    }
    new_handle = vtable[+0x54](0x3c);          // ALLOC 60 byte object
    ptr->[+8] = new_handle;                     // (W) store new pointer
    // ... use new_handle ...
}
```

### 3.3 FUN_85b18 의 새 instance 사용 (0x85c1a)

```c
// 0x85c1a-1e:
handle = ptr->[+8];                            // (R)
content = *handle;                              // deref → 객체 내용 시작
content += 8;                                   // offset 8 within instance
local[-0x28] = content;                          // save to local
// ... 이후 content[+...] field access
```

객체 dereference 후 +8 offset 사용 → ObjectB instance 의 field +0x08 사용.

### 3.4 종합 — ObjectB lifecycle

```c
struct ObjectB_instance {  // 60 bytes (0x3c)
    /* +0x00 */ void* vtable;        // (assumed)
    /* +0x04 */ ...                  // (unknown)
    /* +0x08 */ ...                  // 사용됨 (FUN_85c1a)
    /* +0x58 */ ...                  // method 0x58 (destructor) 호출됨
    /*  ...   */
};

// vtable layout (partial, 9 methods 확정 Round 47):
ObjectB_vtable = {
    /* +0x00 */ ...,
    /* +0x08 */ method08,
    /*  ...   */
    /* +0x54 */ allocator,           // ★ Round 50 신규: 객체 생성 (new(size))
    /* +0x58 */ destructor,          // ★ Round 50 신규: 객체 소멸 (delete or finalize)
    /* +0x60 */ method0x60,          // Round 47 finding
};
```

**vtable[+0x58] = ObjectB destructor 확정** (Round 47 의 method0x58 정체가 destructor 임). 또한 **vtable[+0x54] = allocator** 신규 식별 (Round 47 의 9 methods + 0x54 = 10 known methods).

**task[0xa848]+0x08 의미**: **현재 활성 ObjectB instance 의 포인터** (예: 현재 메뉴/screen state object). State 변경 시 free-then-alloc 패턴.

## 4. FUN_75b98 render flush 본문 (2QE)

```c
void FUN_75b98(void* r0 /* &task[0xa848]+0x10 */, int r1 /* mode=7 */, int r2 /* 1 */, int r3 /* 1 */) {
    // Save args to locals
    local[-4]  = r0;
    local[-8]  = r1;
    local[-0x10] = r3;
    local[-9]  = (byte)r2;                    // mode byte

    ctx = context_getter();                    // ctx = context base
    local[-0x14] = ctx;
    buffer = ctx + literal;                    // buffer ptr (some sub-context table)
    local[-0x18] = buffer;

    if (buffer[+0xa0] != 0) {                   // dirty flag at +0xa0
        memset_like(buffer + 0xa0, 0, 256);     // CLEAR 256 byte sub-buffer
    }

    global1 = *(sl + lit1);                    // GOT table 1
    table = *global1;
    method = table[+0]                          // first table entry
    global2 = *(sl + lit2);                    // another GOT
    arg_buf = buffer + 0xa0;
    indirect_call(global2[+1], arg_buf, r0);   // via veneer 0xa42a4
    // ... more processing ...
}
```

핵심: **FUN_75b98 은 256-byte sub-buffer 의 dirty flag 검사 + memset(0) clear + render dispatch** 패턴. mode=7 / opt=1/1 인자는 후속 분기에 사용 가능성.

## 5. FUN_82df4 — 공유 epilogue (2QF)

```
0x82df4: mov sp, r7
0x82df6: pop {r3, r4}
0x82df8: mov r8, r3
0x82dfa: mov sl, r4
0x82dfc: pop {r4, r5, r6, r7, pc}
```

12 byte 짜리 **표준 ARM Thumb function epilogue**. 의미적 함수가 아닌 **다중 함수가 코드 재사용으로 공유하는 epilogue trampoline**. FUN_818f0 의 early-return (`bl FUN_82df4`) 시 호출.

## 6. FUN_818f0 정정 — 74-entry 입력 디스패처 (2QC)

Round 48 에서 "74-entity iteration loop" 로 잘못 해석. Round 50 에서 prologue 정밀
분석 후 정정:

### 6.1 Prologue 분석

```
0x818f0: push {r4-r7, lr} + r8/sl saves
0x818fa: sub sp, #0x6c                       ; 108 byte local frame
0x81902: str r0, [r7-4]                       ; ★ local[-4] = r0 = ARGUMENT (NOT entity_ptr!)
0x8190a: str #0, [r7-8]                       ; local[-8] = 0
0x81912: bl context_getter
0x8191e: strb (byte at ctx+lit), [r7-9]      ; local[-9] = init byte from context
0x81924-3e: 추가 context+lit indexing + signed byte → local[-0xa]
```

**핵심 정정**: local[-4] = **함수 인자 r0** (NOT entity_ptr). 함수가 받는 입력은
1개의 event/state code.

### 6.2 cmp #0x49 분석

```
0x81968: r3 = local[-4] + 0x10                ; r3 = arg + 0x10
0x81970: stack[-0x6c] = r3                     ; save normalized idx
0x81978: r1 = stack[-0x6c] = arg + 0x10
0x8197a: cmp r1, #0x49
0x8197c: bls 0x81982                           ; if (arg+0x10) <= 0x49 unsigned, proceed
0x8197e: bl FUN_82df4                          ; else early return (shared epilogue)

; 0x81982-9a: JT dispatch
0x8198a: lsls r2, r3, #2                      ; r2 = idx * 4
0x8198c-90: r3 = sl + lit + idx*4              ; JT base + idx*4
0x81992: ldr r2, [r3]
0x81994-8: 또 다른 sl + lit (target base)
0x8199a: mov pc, r3                            ; INDIRECT JT JUMP
```

**핵심**: `(arg + 0x10) ≤ 0x49 unsigned` 검사 → 통과 시 **74-entry JT 디스패치**.

### 6.3 유효 입력 범위

`(arg + 0x10) ≤ 0x49 unsigned` 만족하는 signed arg:
- **arg ∈ [-0x10..-1]** (16 entries, signed negative — sentinel codes)
- **arg ∈ [0..0x39]** (58 entries, positive ASCII/numeric codes)
- 합계: **74 distinct event codes** ← Round 48 의 "74" 의 진짜 정체!

### 6.4 FUN_818f0 정체 — 입력 이벤트 디스패처

```c
int FUN_818f0(int event_code /*r0*/) {        // 74 입력값을 받아 분기
    save_args();
    init_context_byte();                       // local[-9] = ctx byte
    init_event_index();                         // local[-0xa] = indexed event ID

    // First: check if event flag set → fire FUN_3a86c (letter input)
    if (context_flag_byte != 0) {
        FUN_3a86c(/*r0=*/2, /*r1=*/event_code);
        FUN_82df4();                              // early return
    }

    // Else: dispatch via 74-entry JT
    idx = event_code + 0x10;
    if (idx > 0x49) return;                      // out of range
    JT[idx]();                                    // pc = JT_base + JT[idx]
    // JT targets include FUN_92d30 (LEFT/RIGHT), FUN_92cc0 (UP/DOWN), etc.
}
```

**Round 48 의 "74-entity iteration loop" 가설 완전 정정**: 실제로는 **74-entry input event dispatcher**. FUN_818f0 의 6 reload sites 는 동일 인자를 여러 sub-handler 에 pass-through 하는 다중 JT entry 의 패턴.

## 7. 갱신된 시스템 모델

```c
struct SessionContext {  // task[0xa848], ≥0x5c bytes
    /* +0x00 */ u32 primary_state;
    /* +0x01 */ u8  sub_state_idx_1;             // FP table 1 dispatch idx
    /* +0x02 */ u8  sub_state_idx_2;             // FP table 2 dispatch idx
    /* +0x03 */ u8  entity_dispatch_state;       // FUN_86058 only
    /* +0x04 */ void* secondary_ptr;
    /* +0x08 */ ObjectB* active_instance;        // ★ 동적 할당된 객체 (60B, lifecycle: alloc/free via vtable)
    /* +0x0c */ u32 render_dirty_flag;            // 0=clean, 1=dirty
    /* +0x10 */ render_subrec_t subrec;          // FUN_75b98 의 r0 인자
    /* +0x58 */ u32 sub_struct_member;
    /* +0x5c.. */ ...
};

struct ObjectB_vtable {
    /* +0x00 */ ...
    /* +0x08 */ method08,
    /* +0x10 */ method0x10 (Round 44),
    /* +0x54 */ allocator (Round 50 NEW),
    /* +0x58 */ destructor (Round 50 NEW),
    /* +0x60 */ method0x60 (Round 47),
    /* (others) */
};
// 10 known methods 확정 (Round 47의 9 + Round 50의 +0x54)

// 입력 디스패치 chain
FUN_818f0(event_code)       // 74-entry JT → sub-handler 선택
  → FUN_3a86c(2, ea_code)   // 16-entry JT → 4 handlers
       case -5:  FUN_3c920(mode, char)    // letter input core (Round 46)
       case -4/-2: cursor_inc()           // DOWN
       case -3/-1: cursor_dec()           // UP
       case -16:  ctx_byte = -1           // CLEAR
       (-15..-6): NO-OP
  → FUN_92d30(arg)          // '4'/'6' or -3/-4 → FUN_92bf8(3/4) LEFT/RIGHT
  → FUN_92cc0(arg)          // '2'/'8' or -1/-2 → FUN_92bf8(?/?) UP/DOWN (Round 46)
  → ... (other handlers in 74-entry JT)

// Render path
FUN_57394_render
  → check task[0xa848]+0x0c (dirty flag)
  → if dirty: FUN_75b98(&task[0xa848]+0x10, 7, 1, 1) → memset clear + redraw
       buffer[+0xa0..+0x1a0] cleared (256 bytes) if its own dirty
       indirect render call via veneer 0xa42a4
```

## 8. 다음 라운드 (Round 51) 후속 작업

1. **FUN_818f0 의 74-entry JT 전체 디코드** — JT @ 0x8198c 의 sl-rel literal 추출, 74 target 함수 매핑 (2RA)
2. **FUN_92bf8 본문 분석** — mode 1/2/3/4 (UP/DOWN/LEFT/RIGHT) 별 처리 (2RB)
3. **FUN_3c920 본문 정밀** — 33-arm cmp 'd'/'f'/'g'/'h'/'i' phone keypad letter mapping (2RC)
4. **vtable[+0x54] allocator + 새 할당 객체 lifecycle 추적** — Round 47 task[0x9c71]+memset 1060B 와의 연관 (2RD)
5. **FUN_75b98 의 mode=7 분기** — 본 라운드에서 partial, mode 별 분기 분석 (2RE)
6. **전투 시스템 발견** — FUN_0009a008 8.6KB super function (계속 미분석)

## 부록 — 사용한 도구

- **`tools/recon/decode_3a86c_jt.py`** (Round 50 ★ JT 16 entries)
- **`tools/recon/disasm_3a86c_handlers.py`** (Round 50 ★ 4 handlers 분석)
- **`tools/recon/disasm_92d30_full.py`** (Round 50 ★ keypad nav)
- **`tools/recon/disasm_82df4_full.py`** (Round 50)
- **`tools/recon/disasm_75b98_full.py`** (Round 50 ★ render flush)
- **`tools/recon/trace_a848_08_context.py`** (Round 50 ★ ObjectB instance)
- **`tools/recon/disasm_818f0_prologue.py`** (Round 50 ★ FUN_818f0 정정)
- 기존: `tools/recon/disasm_subsystem_func.py`, `find_next_function.py` 등
