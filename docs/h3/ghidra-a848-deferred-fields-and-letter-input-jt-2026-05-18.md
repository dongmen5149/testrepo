# Hero3 Ghidra — task[0xa848] deferred sub-fields + 0x0c dirty flag + FUN_3a86c JT dispatch (Round 49)

> **세션**: 2026-05-18, Round 49
> **이전 Round**: [ghidra-a848-substruct-and-fp-tables-2026-05-18.md](ghidra-a848-substruct-and-fp-tables-2026-05-18.md) (Round 48)
> **재현 도구**: `tools/recon/analyze_a848_stack_reload_v3.py` / `trace_a848_0c_to_gfx.py` / `analyze_818f0_entity_v2.py` / `disasm_3a86c_with_r0_trace.py`

## 한 줄 요약

Round 48 에서 task[0xa848] sub-struct ≥0x5c bytes + 4 GVM FP tables 식별. Round 49 에서 **task[0xa848] 추가 sub-field +0x03 (byte) + +0x08 (word)** 발견 (stack-cached pointer reload tracking) + **+0x0c = "render dirty flag"** 의미 정정 (NOT render target value) + **+0x10 = render sub-struct pointer** (FUN_75b98 의 r0 인자) + **FUN_3a86c = 16-entry JT dispatcher on signed entity_arg** (NOT a pointer-based call).

## 1. task[0xa848] sub-struct field map 갱신

### 1.1 Round 49 신규 발견 — deferred stack-cached reload tracking

Round 48 에서 18 callers 가 `str r2, [r7-N]` 으로 &task[0xa848] 포인터를 로컬에
stash 한 후 함수 내내 deferred multi-field access 했다고 보고. Round 49 의
`analyze_a848_stack_reload_v3.py` 는 forward register propagation 으로 stack
slot reload 패턴 (`subs Rx, r7, #N; ldr Ry, [Rx]; ldr/str Rz, [Ry, #M]`) 을
정확히 추적하여 누락된 sub-field 발견:

| Offset | Type | R | W | 사이트 (function bound) | 의미 추정 |
|---|---|---|---|---|---|
| +0x00 | word | 1 | _ | 0x579b8 (FUN_57394) | primary state |
| **+0x01** | u8 | 2 | **11** | 0x85f5c, 0x86016, 0x86142/5e/7a (FUN_86058), 0x88a8e (FUN_88a30), 0x89bb4 (FUN_89b18), 0x857ba (FUN_857a4), ... | **sub-state byte idx #1 + state setter** (11 STRB) |
| +0x02 | u8 | 2 | 3 | 0x85f88, 0x85fea, 0x8623c (FUN_861a8), 0x862f4 (FUN_862d4), 0x85894 (FUN_857a4) | sub-state byte idx #2 |
| **+0x03** | u8 | 3 | 1 | 0x860d4 (W), 0x86130/4c/68 (R) — **FUN_86058 only** | **NEW byte field — entity dispatch state?** |
| +0x04 | word | _ | 1 | 0x8625a (FUN_861a8) | secondary pointer |
| **+0x08** | word | **7** | 3 | 0x85b8e/a2/b4/cc/c1a (FUN_85b18), 0x85ea6/b8/c8 (FUN_85e88), 0x890fa (FUN_88eb0), 0x89c02 (FUN_89b18) | **NEW word field — DOMINANT (10 acc)** |
| **+0x0c** | word | 2 | 4 | 0x57040, 0x57084 (FUN_56f3c save/load), 0x575fc/57602/579a8/57bcc (FUN_57394 render) | **render dirty flag** (R/W = 1) |
| +0x10..+0x57 | (sub-struct) | _ | _ | FUN_75b98 arg 로 흐름 — Round 49/2PB 참고 | render sub-struct |
| +0x58 | word | 1 | _ | 0x85eba | sub-struct member |

**Struct 크기**: ≥0x5c bytes 확정 (Round 48 그대로).

**핵심 신규 sub-field**:
- **+0x03 (byte)** — FUN_86058 (7th indirect entry, 336B) 내부에서만 access. 0x860d4 strb (state set) → 0x86130/4c/68 ldrb (3 reads) = entity dispatch state byte. Round 47 의 task[0x9c71..0x9c76] 6-byte cluster 와 별개의 sub-state.
- **+0x08 (word)** — 4개 함수 (FUN_85b18, FUN_85e88, FUN_88eb0, FUN_89b18) 에 분산. 7 reads + 3 writes = 10 access 로 dominant. **task[0xa848]+0x08 = "current selection / active entity index"** 후보 (state machine state value).

### 1.2 +0x01 의 11 writes — state transition setter pattern

Round 48 에서 +0x01 은 2 reads 만 보였으나, Round 49 의 reload tracking 으로
**11 STRB writes** 발견:
- FUN_86058 (7th indirect entry) 내부에서 3 sites (0x86142/5e/7a) — 7th entry 가 state 를 set
- FUN_88a30 (1152B) — 0x88a8e
- FUN_89b18 (1336B) — 0x89bb4
- FUN_857a4 (772B) — 0x857ba 부근
- 추가 4 sites in 다른 functions

**해석**: +0x01 은 "**current sub-state index #1**" 이고, 다양한 함수에서 state transition 시 새 값을 write. FUN_85edc/85fc8 의 dispatch 시 read (Round 48 finding) 의 setter 측.

## 2. task[0xa848]+0x0c — render dirty flag 정정

Round 48 에서 task[0xa848]+0x0c 를 "save+render 공유 sub-state" 로 보고. Round 49 의
`trace_a848_0c_to_gfx.py` 로 FUN_57394 의 4 사이트 컨텍스트 추적 후 의미 정정:

### 2.1 두 사이트 0x575fc 와 0x57bcc — 동일 패턴 (dirty check)

```
; FUN_57394 at 0x575f6:
0x575f6: bl FUN_85578c           ; r0 = &task[0xa848]
0x575fc: ldr r3, [r3, #0xc]      ; r3 = task[0xa848]+0x0c (READ)
0x575fe: cmp r3, #0               ; dirty?
0x57600: beq 0x57624              ; clean → SKIP rendering

; If dirty (+0x0c != 0):
0x57602: bl FUN_85578c            ; reload pointer
0x57608: movs r3, #0
0x5760a: str r3, [r2, #0xc]      ; **CLEAR dirty flag (+0x0c = 0)**

0x5760c: bl FUN_85578c
0x57610: adds r3, r0, #0
0x57612: adds r3, #0x10           ; r3 = &task[0xa848] + 0x10
0x57614: adds r0, r3, #0           ; r0 = arg = &task[0xa848]+0x10
0x57616: movs r1, #7
0x57618: movs r2, #1
0x5761a: movs r3, #1
0x5761c: bl FUN_75b98             ; **call FUN_75b98(&task[0xa848]+0x10, 7, 1, 1)**
```

### 2.2 두 사이트 0x57602 / 0x579a8 — write 패턴

- **0x57602 의 다음 store at 0x5760a** = `movs r3, #0; str r3, [r2, #0xc]` = **CLEAR (ACK)**
- **0x579a8** = `movs r3, #1; str r3, [r2, #0xc]` = **SET (DIRTY)**

### 2.3 결론 — +0x0c 의 의미

**task[0xa848]+0x0c 는 "render dirty flag" (boolean 0/1)**, NOT a render target value:

| 시점 | +0x0c 값 | 의미 |
|---|---|---|
| 상태 변경 후 (0x579a8) | 1 | "render pending — buffer 갱신 필요" |
| render 검사 (0x575fc, 0x57bcc) | 1 이면 process | "dirty 면 flush" |
| flush 완료 후 (0x5760a) | 0 | "clean — acknowledged" |

이는 일반적인 **lazy/dirty rendering 패턴**. 즉:
- Game state 변경 시 +0x0c = 1 mark
- 매 frame 의 render 단계에서 +0x0c == 1 검사
- Dirty 면 FUN_75b98(&task[0xa848]+0x10, 7, 1, 1) 호출하여 갱신 + +0x0c = 0
- Clean 이면 skip (성능 최적화)

### 2.4 +0x10 = render sub-struct pointer

dirty 시 호출되는 FUN_75b98 의 r0 인자 = `&task[0xa848] + 0x10`. 따라서
**task[0xa848]+0x10 부터 시작하는 sub-struct (≥0x48 bytes 까지) 가 render 가능한
"deferred render record"**. FUN_75b98(r0=&record, r1=7, r2=1, r3=1) 시그니처로 호출.

FUN_56f3c (save/load) 가 +0x0c 를 read/write 하는 의미는: **save 시 dirty flag 의
상태를 보존, restore 시 복원** — 그래야 save load 후에도 정상적인 dirty/render 사이클이
유지된다.

## 3. FUN_3a86c letter input — 16-entry JT dispatcher (NOT pointer-based)

Round 47/48 에서 FUN_3a86c (388B / 177 instr) 를 "letter input subsystem 진입점" 으로
식별. Round 49 의 `disasm_3a86c_with_r0_trace.py` 로 본문 정밀 분석:

### 3.1 Prologue + JT 디스패치

```
0x3a86c: push prologue + sp -= 0xc
0x3a87e: str r0, [r7-4]               ; local[-4] = sub-mode arg (e.g., #2)
0x3a884: str r1, [r7-8]               ; local[-8] = entity_arg
0x3a88a: ldr r3, [r7-8]               ; r3 = entity_arg
0x3a88c: adds r3, #0x10                ; r3 = entity_arg + 0x10
0x3a894: str r3, [r7-0xc]              ; local[-0xc] = entity_arg + 0x10

0x3a89c: ldr r2, [r7-0xc]              ; r2 = entity_arg + 0x10
0x3a89e: cmp r2, #0xf
0x3a8a0: bls 0x3a8a4                   ; (entity_arg+0x10) <= 0xf → JT dispatch
0x3a8a2: b 0x3a9ca                     ; else: escape

; JT dispatch (16 entries)
0x3a8aa: ldr r3, [r7-0xc]              ; r3 = entity_arg + 0x10 (= idx, 0..0xf)
0x3a8ac: lsls r2, r3, #2                ; r2 = idx * 4
0x3a8ae: ldr r3, [pc, #0x128]
0x3a8b0: add r3, sl                     ; r3 = sl + literal (JT base GOT slot)
0x3a8b2: adds r3, r2, r3                 ; r3 = JT_base + idx*4
0x3a8b4: ldr r2, [r3]                    ; r2 = JT[idx] (offset)
0x3a8b6: ldr r3, [pc, #0x120]
0x3a8b8: add r3, sl                     ; r3 = sl + another literal (target base)
0x3a8ba: adds r3, r2, r3                 ; r3 = target_base + JT[idx]
0x3a8bc: mov pc, r3                      ; ★ INDIRECT JT JUMP
```

**핵심**: FUN_3a86c 는 **16-entry indirect JT** 로 entity_arg+0x10 idx 에 따라 dispatch.

### 3.2 entity_arg 의 정체 — signed integer in [-0x10..-1]

cmp #0xf range guard 가 통과하려면 (entity_arg + 0x10) 가 [0..0xf]. 즉:
- entity_arg ∈ [-0x10..-1] (signed)
- Valid 범위 16 가지 entity 'event code' (-16..-1)

이는 entity_arg 가 **pointer 가 아니라 small signed integer (entity event/state code)** 임을 의미. Round 48 의 "FUN_818f0 의 BL 호출 시 r1 = current entity ptr" 가설 정정 필요 — 사실 r1 = **현재 entity 의 state 코드 (-1..-16)**.

### 3.3 entity_arg == -5 case (JT entry 0xb = idx 0x10+(-5)=0xb)

```
0x3a8be: ldr r3, [r7-8]                ; r3 = entity_arg
0x3a8c4: movs r2, #5
0x3a8c6: rsbs r2, r2, #0                ; r2 = -5
0x3a8c8: cmp r3, r2
0x3a8ca: bne 0x3a90c                    ; if entity_arg != -5, branch

; entity_arg == -5 path
0x3a8cc: bl context_getter              ; r0 = ctx
0x3a8d2-d8: ctx + literal → ldrb (byte from context table)
0x3a8da: asrs r2, r3, #0x18              ; sign-extend (now r2 = signed byte)
0x3a8dc: ldr r3, [r7-4]                ; r3 = sub-mode (e.g., #2)
0x3a8e0: adds r0, r3, #0                ; r0 = sub-mode
0x3a8e2: adds r1, r2, #0                ; r1 = signed byte from context
0x3a8e4: bl FUN_3c920                   ; ★ FUN_3c920(sub_mode, signed_byte) — letter input core (Round 46)
```

**r0 = #2 sub-mode** 의 정체: **FUN_3c920 (letter input core, 33-arm cmp 'd'/'f'/'g'/'h'/'i'
phone keypad) 의 첫 인자** = **keypad mode selector**. 가능한 값:
- 0 = letter (기본)
- 2 = digit / numeric
- 다른 모드 (대문자/한글/symbol)

### 3.4 entity_arg != -5 case (0x3a90c-0x3a92a)

```
0x3a90c-22: 2x context_getter + ctx+literal → strb -1 (set sentinel byte)
0x3a92a: bl FUN_2d77c
```

다른 entity event code 처리. **strb -1 = sentinel write** = "cleared" 상태로 set.

### 3.5 Common epilogue (0x3a92e-0x3a9ca)

13 context_getter calls + cmp #0 분기 + FUN_2d77c 호출. State 마무리 처리.

## 4. FUN_000818f0 entity loop 정정

Round 48 finding: "FUN_818f0 = 74-entity iteration loop (stride 0x10)". Round 49 의
재검토로 정정:

### 4.1 6 entity_ptr reload sites — 모두 BL pass-through

`analyze_818f0_entity_v2.py` 결과: FUN_818f0 내 6개 `subs Rx, r7, #4; ldr Rd, [Rx]`
reload 사이트가 있으나, 각 reload 직후 **entity_ptr 가 다른 함수의 인자로 즉시 전달**:

| Reload @ | 직후 패턴 | 호출되는 함수 |
|---|---|---|
| 0x81956 | `r0=#2; r1=r3; bl FUN_3a86c` | FUN_3a86c (letter input) |
| 0x81966 | `r3 += 0x10; str r3, [stack-0x6c]` | (loop advance, no call) |
| 0x824ea | `r0 = r3; bl FUN_92d30` | FUN_92d30 (sub-handler) |
| 0x8270c | `r0 = r3; bl FUN_92d30` | FUN_92d30 |
| 0x82938 | `r0 = r3; bl FUN_92cc0` | FUN_92cc0 (Round 46 '2'/'8' dispatcher) |
| 0x82ada | `r0 = r3; bl FUN_92cc0` | FUN_92cc0 |

**결론**: FUN_818f0 자체는 entity record 필드를 **직접 access 하지 않음**. 항상
entity_arg 를 sub-handler 의 인자로 전달. 따라서 entity record structure 는
sub-handler 측 (FUN_3a86c, FUN_92d30, FUN_92cc0) 에서 분석 필요.

### 4.2 entity_arg 가 pointer 아님 (FUN_3a86c 검증 후)

§3.2 의 FUN_3a86c 분석으로 entity_arg 가 **signed integer [-0x10..-1]** 임이 확인됨.
따라서 Round 48 의 "FUN_818f0 = 74-entity iteration loop with pointer arithmetic"
해석은 정정 필요:

**정정된 가설**:
- FUN_818f0 의 local[-4] = **현재 처리 중인 entity 의 event code** (signed int, 가능 -1..-16 + 정상값)
- `adds r3, #0x10` 의 의미는 단순한 entity offset advance 가 아닐 수 있음 (state machine state advance 가능성)
- cmp #0x49 (= 73 decimal) 는 다른 의미 (entity 개수 상한이 아닐 가능성)

이는 FUN_818f0 의 전체 구조 재분석 필요 (Round 50 후속).

## 5. 4 GVM FP tables (Round 48 finding) — entry size 추정 한계

`task[0xa848]+0x01` 의 11 strb writes 중 immediate value 가 있는 사이트들의 max
값 추적 시도. 대부분 writes 는 r3 = (어떤 register 의 값) 이거나 sign-extended
context byte 이므로 정적 상한 추정 불가. **GVM 런타임 디버깅 또는 emulator
inspection 필요**. Round 49 에서는 deferred 처리.

## 6. 갱신된 task[0xa848] struct 모델

```c
struct SessionContext {  // task[0xa848], size ≥ 0x5c bytes
    /* +0x00 */ u32 primary_state;          // 1 read (sister entry)
    /* +0x01 */ u8  sub_state_idx_1;         // 11 writes (state transitions) + 4 reads (FP dispatch)
    /* +0x02 */ u8  sub_state_idx_2;         // 5 writes + 3 reads (FP dispatch)
    /* +0x03 */ u8  entity_dispatch_state;   // NEW: 1 write + 3 reads (FUN_86058 only)
    /* +0x04 */ void* secondary_ptr;         // 1 write + 1 read
    /* +0x08 */ u32 active_selection;        // NEW: 7 reads + 3 writes (DOMINANT new field)
    /* +0x0c */ u32 render_dirty_flag;       // 0=clean, 1=dirty (save 시 보존)
    /* +0x10 */ render_subrecord_t subrec;   // render sub-struct passed to FUN_75b98
    /*  ...   */
    /* +0x58 */ u32 sub_struct_member;       // 1 read at 0x85eba
    /* +0x5c.. */ ...
};

void FUN_85578c(void) { return &task[0xa848]; }                 // pure getter
void FUN_85edc(arg0, arg1) {                                     // 2-단 sequential dispatch
    rect_draw(...);
    FP_table_1[ctx.sub_state_idx_1](arg0, arg1);
    FP_table_2[ctx.sub_state_idx_2](arg0, arg1);
}
void FUN_85fc8(arg0) {                                           // 조건부 dispatch
    int r = FP_table_2'[ctx.sub_state_idx_2](arg0);
    if (r == 0) FP_table_1'[ctx.sub_state_idx_1](arg0);
}
void FUN_57394_render(void) {                                    // render with dirty check
    // ...
    if (ctx.render_dirty_flag != 0) {
        ctx.render_dirty_flag = 0;                                // ACK
        FUN_75b98(&ctx.subrec, 7, 1, 1);                          // flush
    }
}
void FUN_3a86c(int sub_mode, int entity_arg /* signed [-0x10..-1] */) {
    if (entity_arg + 0x10 > 0xf) return;                          // range guard
    int idx = entity_arg + 0x10;                                  // 0..0xf
    JT[idx]();  // 16-entry dispatch
    // case -5: FUN_3c920(sub_mode, ctx_byte);  // letter input core
    // ...
}
```

## 7. 다음 라운드 (Round 50) 후속 작업

1. **FUN_3a86c 의 16 JT entries 전체 디코드** — task[GOT+literal] 의 위치 식별, 각 entry 의 target 함수 파악 (2QA)
2. **FUN_92d30 / FUN_82df4 본문 분석** — FUN_818f0 의 sub-handlers 두 정체 (2QB)
3. **FUN_818f0 전체 구조 재분석** — entity_arg 가 signed int 라는 finding 기반, 실제 loop 구조 파악 (2QC)
4. **task[0xa848]+0x08 의 정확한 의미** — 4 함수에 분산된 7R+3W 의 read/write 컨텍스트 추적 (2QD)
5. **FUN_75b98 본문 분석** — render sub-struct flush 함수, (mode=7, 1, 1) 인자 의미 (2QE)
6. **전투 시스템 발견** — FUN_0009a008 8.6KB super function (계속 미분석)

## 부록 — 사용한 도구

- `tools/recon/analyze_a848_substruct.py` (Round 48)
- `tools/recon/analyze_a848_proper_writes.py` (Round 48)
- `tools/recon/analyze_a848_stack_reload.py` (Round 49, v1 incomplete)
- **`tools/recon/analyze_a848_stack_reload_v3.py`** (Round 49 ★ 정정본)
- **`tools/recon/trace_a848_0c_to_gfx.py`** (Round 49)
- **`tools/recon/analyze_818f0_entity_v2.py`** (Round 49)
- **`tools/recon/disasm_3a86c_with_r0_trace.py`** (Round 49)
- 기존: `tools/recon/disasm_subsystem_func.py`, `tools/recon/find_function_containing.py`,
  `tools/recon/find_next_function.py`
