# Round 18 (2026-05-10 PM-8) — sub-handler 2개 본문 + GOT slot wide-scan 확장

## 요약

PM-7 의 type-tag reader 매핑 후속. 가장 많이 호출되는 두 sub-handler `FUN_000439a0` (37 callers) / `FUN_00047a14` (17 callers) 본문 capstone 디스어셈블 + 추가 GOT 슬롯 4개 + 본문 분석에서 발견된 신규 5개 슬롯 = **총 9개 슬롯 대상 writer 추적**. 모두 **direct write 0건** 으로 GVM 외부 주입 패턴이 시스템 전반에 걸친 표준임을 확정.

신규 발견:
1. **FUN_000439a0 = 7-entry JT dispatcher** — 0x38 stride record array, type field@(record+0x1d) - 4 → 7 cases (4..10)
2. **FUN_00047a14 = state transition function** — task_struct[0] gate → 0xf 를 다른 task slot 에 write
3. **신규 GOT 슬롯 5개 발견**: 0x128 / 0x16c / 0x29e / 0x9bb4 / 0x9cbc — 모두 0 direct write
4. **0x16c slot 가 가장 광범위한 task_struct ptr** (147+ readers, 0x444 와 동급)

---

## 1. FUN_000439a0 본문 분석 (188B, 90 instr, 37 callers)

### 디스어셈블 핵심 흐름

```asm
0x000439a0  push  {r4-r7,lr}; mov r7,sl; mov r6,r8; push {r6,r7}    ; 8 reg save
0x000439aa  sub   sp, #0x48                                          ; 72B stack frame
                                                                       ; → 7 args 가능 (4 reg + 3 stack)
0x000439ae  store r3 byte → [sp+0x3c]   ; param4 byte 보관
0x000439b0  ldr   r3, [sp+0x64] ; → [sp+0x38]  ; param5 byte
0x000439b8  ldr   r3, [sp+0x68] ; → [sp+0x34]  ; param6 byte
0x000439c2  ldr   r3, [sp+0x6c] ; → [sp+0x30]  ; param7 byte

0x000439be  ldr   r4, [pc, #0x33c]   ; r4 = 0x6f26e (GOT base offset)
0x000439c4  mov   sl, r4
0x000439ce  add   sl, pc             ; sl = 0xb2c40 (GOT base, PIC)

0x000439d0  adds  r4, r0, #0         ; r4 = param1 (ctx ptr arg)
0x000439d8  bl    #0x4ad10           ; context_getter() → r0 = global_ctx_ptr
0x000439dc  ldr   r3, [r4]; adds r3, #8   ; r3 = (*param1) + 8        — record_base
0x000439e2  str   r3, [sp+0x1c]      ; save record_base[A]
0x000439e4  adds  r1, r0, #0xb4      ; r1 = ctx + 0xb4
0x000439e6  ldr   r3, [pc, #0x318]   ; r3 = 0x29e (slot offset)
0x000439ee  adds  r4, r0, r3         ; r4 = ctx + 0x29e

0x000439f0  ldrsb r3, [r4, #0]       ; r3 = signed byte at ctx+0x29e (gate)
0x000439f4  cmp   r3, #0
0x000439f6  bgt   #0x439fc           ; if (gate > 0) skip helper
0x000439f8  bl    #0x44280            ; FUN_00044280 — gate-guard helper

0x000439fc  ldr   r1, [pc, #0x304]   ; r1 = 0x9bb4 (slot offset)
0x000439fe  adds  r1, r0, r1         ; r1 = ctx + 0x9bb4
0x00043a02  bl    #0x4ad10           ; context_getter() → r0 = ctx2 (different/same?)
0x00043a06  ldr   r2, [pc, #0x300]   ; r2 = 0x9cbc (slot offset)
0x00043a08  adds  r0, r0, r2         ; r0 = ctx2 + 0x9cbc
0x00043a0a  ldr   r3, [r0]; ldr r3, [r3]   ; double indirection
                                          ; (ctx2+0x9cbc) → ptr → ptr → record_base[B]
0x00043a10  adds  r3, #8              ; record_base[B] + 8
0x00043a12  str   r3, [sp+0x20]      ; save

0x00043a16  movs  r3, #0x38; muls r3, r2_byte, r3 ; offset = byte * 0x38
0x00043a1e  adds  r3, r3, [sp+0x1c]  ; record_addr = record_base[A] + byte * 0x38
0x00043a20  adds  r3, #0x26          ; +0x26
0x00043a22  ldrb  r3, [r3]            ; r3 = byte at record[+0x26]
0x00043a28  cmp   r3, #0
0x00043a2a  bne   #0x43a30
0x00043a2c  bl    #0x44260            ; FUN_00044260 — record-active guard

0x00043a30  ldrb  r1, [r4]             ; r1 = byte at ctx+0x29e (refresh)
                ; (이후 r5/r6 byte param 처리 + 두 번째 record array 인덱싱)
0x00043a3a  adds  r4 = (param-byte) + record_base[A]
0x00043a40  ldrb  r3, [r4 + 0x1d]      ; r3 = byte at record[+0x1d]   ⭐⭐ TYPE FIELD
0x00043a46  subs  r1, r3, #4           ; r1 = type - 4

0x00043a48  cmp   r1, #6               ; ⭐⭐ if type > 10 → bail out
0x00043a4a  bhi   #0x43a6e             ; → FUN_00043a6e (catch-all branch)

;; 7-entry jump table (type 4..10)
0x00043a4c  ldr   r3, [pc, #0x2bc]     ; r3 = 0xffff5730 (signed offset)
0x00043a4e  mov   r6, sl
0x00043a50  adds  r2, r6, r3            ; r2 = sl + 0xffff5730 = 0xb2c40 - 0xaa8d0 = 0x8370
                                        ; ⭐ JT base @ 0x8370 (in code section)
0x00043a52  lsls  r1, r1, #2            ; r1 = (type - 4) * 4
0x00043a54  ldr   r3, [r1, r2]          ; r3 = JT[type-4]
0x00043a56  adds  r3, r3, r2            ; r3 = JT_entry + JT_base = absolute target
0x00043a58  mov   pc, r3                ; JUMP

0x00043a5a  movs  r4, #1                ; (one of the JT branches dest)
```

### 정체 추정

| 측면 | 발견 |
|---|---|
| **함수 종류** | 7-entry switch dispatcher (type field 4~10) + 2 가드 helper 호출 |
| **인자** | 7개 (r0~r3 + 3 stack arg, byte 모두 sign-extend) |
| **데이터 구조** | record stride **0x38 bytes**, type field at +0x1d, active flag at +0x26 |
| **사용 슬롯** | 3개 PIC GOT slot: 0x29e (gate flag), 0x9bb4 (offset), 0x9cbc (record array base) |
| **JT 위치** | binary 내부 0x8370 (code 영역). `mov pc, r3` indirect jump |
| **호출 helper** | `FUN_00044280` (gate guard), `FUN_00044260` (active guard), `FUN_00043a6e` (type > 10 catch-all) |
| **caller 수** | 37 (top stub #7) — 광범위 재사용 = 공통 sub-system |

### 가설

**0x38 stride** + **byte type field** + **JT 7-entry** 패턴은 NPC handler (0x3c4 stride) 와 다른 별도 시스템. 후보:
- ⭐ **status effect / buff handler** (party member 마다 status entry, type 4~10 = 효과 종류)
- entity update mini-loop (per-character animation/movement state)
- inventory item action handler

cmp #6 distribution 에서 가장 인기 = type 6 가 자주 발생하는 효과. 다음 추적 거리:
1. **JT @ 0x8370 디코드** — 7 entries 의 실제 target 함수 식별
2. **FUN_00044260 / FUN_00044280** 본문 분석 (가드 helper 들)
3. **slot 0x9cbc 의 record_base[B] 사용처** — 이건 어떤 array 인지

---

## 2. FUN_00047a14 본문 분석 (96B, 46 instr, 17+ callers)

### 디스어셈블 핵심 흐름

```asm
0x00047a14  push  {r4-r6,lr}; mov r6,sl; push {r6}        ; 5 reg save
0x00047a1a  ldr   r3, [pc, #0x48]    ; r3 = 0x6b21c (GOT offset literal)
0x00047a1c  mov   sl, r3
0x00047a1e  ldr   r3, [pc, #0x48]    ; r3 = 0x16c (slot offset)
0x00047a20  add   sl, pc              ; sl = 0xb2c40 (GOT base)
0x00047a22  add   r3, sl              ; r3 = 0xb2dac (= GOT base + 0x16c)
0x00047a24  ldr   r3, [r3]            ; r3 = *(0xb2dac) = struct ptr  ⭐ SINGLE indirection
0x00047a26  ldrb  r3, [r3]            ; r3 = first byte of struct      ⭐ task_state byte

0x00047a30  adds  r6, r0, #0          ; r6 = param1
0x00047a32  lsrs  r5, r1, #0x18       ; r5 = param2 byte
0x00047a34  lsrs  r4, r2, #0x18       ; r4 = param3 byte

0x00047a36  cmp   r3, #0              ; ⭐ first_byte == 0?
0x00047a38  bne   #0x47a40            ; nonzero → state transition

;; FALL-THROUGH: zero → no-op return
0x00047a3a  pop   {r3}; mov sl, r3
0x00047a3e  pop   {r4, r5, r6, pc}     ; RETURN

;; STATE TRANSITION (first_byte != 0)
0x00047a40  ldr   r3, [pc, #0x28]      ; r3 = 0x128 (DIFFERENT slot)
0x00047a42  add   r3, sl                ; r3 = 0xb2d68 (= GOT + 0x128)
0x00047a44  ldr   r2, [r3]              ; r2 = *(0xb2d68) = OTHER task ptr
0x00047a46  movs  r3, #0xf
0x00047a48  str   r3, [r2]              ; ⭐⭐ *task_ptr_2 = 0x0f  STATE WRITE

0x00047a4a  bl    #0x4ad10              ; context_getter()
0x00047a4e  ldr   r3, [pc, #0x20]       ; r3 = 0x9e78 (slot offset)
0x00047a52  adds  r0, r0, r3            ; r0 = ctx + 0x9e78
0x00047a54  movs  r3, #1
0x00047a56  strb  r3, [r0]              ; ctx[+0x9e78] = 1 (flag set)

0x00047a5a  adds  r0, r6, #0            ; restore param1 to r0
0x00047a5c  adds  r1, r5, #0            ; param2 byte to r1
0x00047a5e  bl    #0x98244              ; ⭐ FUN_00098244 (key downstream helper)
0x00047a62  b     #0x47a3a              ; jump to common epilogue
```

### 정체 추정

| 측면 | 발견 |
|---|---|
| **함수 종류** | conditional state transition + downstream call |
| **gate** | task_struct[0] (slot 0x16c → ptr → byte[0]) — single indirection (다른 task ptr) |
| **transition** | task_2[0] (slot 0x128 → ptr → byte[0]) ← **0x0f** state write |
| **side effect** | ctx[+0x9e78] = 1 (signaling flag) |
| **downstream** | `FUN_00098244` 호출 (param1, param2 전달) |
| **caller 수** | 17+ (cmp #6 6x, cmp #1 3x, cmp #7 2x, etc.) |

### 가설

**0x0f = 15** 라는 매직 넘버 + 다른 task ptr 에 쓰기 + `FUN_00098244` 호출 = **subsystem-internal state machine 트리거**.

후보:
- ⭐ **SFX/animation trigger** (state 0xf = "play effect")
- save journal entry write
- queue producer for some subsystem

다음 추적 거리:
1. **FUN_00098244 본문 분석** (downstream helper)
2. **slot 0x128 의 다른 readers** — `0x47a14` 외에 `0x479c8 / 0x982f0 / 0x983e8 / 0x94788 / 0x23cd4 / 0x2ae44` (총 9 readers)
3. **state value 0xf 의 consumer** — 어디서 task_2 의 byte[0]==0xf 를 읽고 분기하는지

---

## 3. GOT 슬롯 wide-scan 확장 (9 슬롯)

### 결과 종합

| Slot offset | Slot abs addr | Direct writes | PC-rel reads | 주요 readers | 정체 가설 |
|---|---|---|---|---|---|
| **0x444** ⭐⭐ | 0xb3084 | **0** (PM-7) | 60+ | task_ptr_getter cluster | primary task_ptr_ptr |
| **0x16c** ⭐⭐ | 0xb2dac | **0** | **147** | FUN_00043508 (3x), FUN_00043a6e, FUN_00044280, FUN_00046de0, FUN_00047a14, FUN_00048ac8, ... | alternate task_struct ptr (single indir) |
| **0x9bb4** | 0xb67f4 | **0** | 80+ | FUN_00026a80 (4x+) | router-specific state |
| **0x9cbc** | 0xb68fc | **0** | 30+ | FUN_0001c1a8 (4x), FUN_000439a0 | record array base ptr |
| **0x9c70** ⭐ | 0xb68b0 | 0 (PM-7) | 112 | FUN_0003a028 cluster | widespread task data |
| **0x9c71** | 0xb68b1 | 0 (PM-7) | 0 | (movw absent) | (literal not used directly) |
| **0x9c84** | 0xb68c4 | 0 (PM-7) | 0 | (movw absent) | (literal not used directly) |
| **0xac78** | 0xbd8b8 | 0 (PM-7) | 0 | (movw absent) | (literal not used directly) |
| **0x128** | 0xb2d68 | **0** | 9 | FUN_00023cd4, FUN_0002ae44 (2x), FUN_000479c8, FUN_00047a14, FUN_00094788, FUN_000982f0, FUN_000983e8 (2x) | secondary state ptr (write 0xf target) |
| **0x29e** | 0xb2ede | **0** | 5 | FUN_0001f1e4, FUN_00042be8, FUN_00042fbc, FUN_000439a0, FUN_000442e4 | small flag |
| **0x9e78** | 0xb6ab8 | (참고) | (참고) | FUN_00047a14 ctx flag write | per-context flag |

### ⭐⭐ 핵심 결론

**system-wide 0 direct write** = GVM 펌웨어 외부 주입 표준 패턴 확인. 게임 코드는 슬롯 자체에 절대 쓰지 않고, 슬롯이 가리키는 struct 의 필드만 *(ptr) = value 형태로 수정.

이는 PM-7 의 0x444 단일 슬롯 가설을 9 슬롯으로 일반화. 게임의 모든 글로벌 state 가 GVM 외부 주입 패턴을 따름.

### 슬롯 0x16c vs 0x444 비교

PM-7 의 0x444 (= 0xb3084) 가 "primary task_ptr_ptr" (double indirection: `[r3] [r3]`).
이번에 발견한 0x16c (= 0xb2dac) 는 single indirection: `[r3]` 한 번만. 다른 종류의 task struct.

가설: 게임이 multiple task pointer 를 사용 (각 subsystem 별):
- 0x444 = 메인 게임 task (event/dispatcher)
- 0x16c = secondary task (animation/SFX/UI?)
- 0x128 = tertiary task (state 0xf 가 쓰여지는 곳, downstream subsystem)
- 0x9bb4 = router-internal task
- 0x9cbc = record array base (게임 entity 들)
- 0x9c70 = widespread (가장 많이 읽힘)

각 슬롯의 task struct 정체는 caller 수가 많은 reader 함수들 본문 분석으로 추가 풀이 가능.

---

## 4. 신규 발견 함수 + onward 후보

### 4.1 핵심 sub-handler 확정

| 함수 | 크기 | callers | 정체 | 다음 단계 |
|---|---|---|---|---|
| **FUN_000439a0** ⭐⭐ | 188B | 37 | 7-entry JT dispatcher (type 4..10), 0x38 stride record | JT @ 0x8370 디코드 |
| **FUN_00047a14** ⭐⭐ | 96B | 17+ | state transition (0xf write) + FUN_00098244 호출 | FUN_00098244 본문 |
| **FUN_00043a6e** ⭐ | ? | (FUN_000439a0 catch-all) | type > 10 default case | 본문 분석 |
| **FUN_00044260** | ? | (FUN_000439a0 helper) | record-active guard | 본문 분석 (소형) |
| **FUN_00044280** | 392B | 11 | gate guard + 0x16c reader | 본문 분석 |

### 4.2 onward helper 후보

| 함수 | 컨텍스트 | 우선순위 |
|---|---|---|
| **FUN_00098244** | FUN_00047a14 의 downstream — state 0xf transition 후 호출. param1/param2 전달 | ⭐⭐ 다음 차례 |
| **FUN_00043508** (1176B) | slot 0x16c 의 가장 큰 reader (3x reads). top-level task processor 후보 | ⭐⭐ |
| **FUN_00098328 / FUN_000983e8** | slot 0x128 readers — 0xf state value 의 consumer 후보 | ⭐ |
| **FUN_0003a028 cluster** | slot 0x9c70 (~20+ reads) consumer. 광범위 재사용 | 중 |
| **FUN_00026a80** (8.4KB) | slot 0x9bb4 의 4+ reader. PM-7 router 가설 + 0x9bb4 = router state | 중 |

---

## 5. 다음 세션 권장 다음 단계 (Round 19 후보)

| # | 작업 | 명령 | 산출물 |
|---|---|---|---|
| ⭐⭐ 2AA | FUN_00098244 본문 (FUN_00047a14 downstream) | `disasm_subsystem_func.py 0x98244 <end>` | state-0xf consumer 정체 |
| ⭐⭐ 2AB | FUN_000439a0 의 JT @ 0x8370 디코드 (7 entries) | 신규 helper or capstone walk | 7 type handler 식별 |
| ⭐ 2AC | FUN_00043508 (1176B, slot 0x16c reader 3x) | `disasm_subsystem_func.py 0x43508 0x439a0` | secondary task processor |
| 2AD | slot 0x16c 의 task_struct 필드 매핑 | 0x16c reader top-5 함수의 `+offset` 패턴 분석 | task_struct layout |
| 2AE | slot 0x128 readers 검증 (state 0xf consumer) | FUN_000982f0/983e8 본문 | state-0xf 의 의미 |

---

## 6. 신규 도구

이번 라운드는 **기존 도구 (disasm_subsystem_func.py + find_global_slot_writers.py) 만 재사용** — 신규 도구 추가 불필요. 두 도구 모두 다음 세션에도 같은 역할로 직접 호출 가능.

---

## 7. 주요 산출물

```
work/h3/popular_helper_439a0_disasm.json     ; 2W
work/h3/sub_handler_47a14_disasm.json        ; 2X
work/h3/global_slot_0x9c70_writers.json      ; 2Y (PM-7 follow-up)
work/h3/global_slot_0x9c71_writers.json
work/h3/global_slot_0x9c84_writers.json
work/h3/global_slot_0xac78_writers.json
work/h3/global_slot_0x128_writers.json       ; 신규 슬롯
work/h3/global_slot_0x16c_writers.json       ; 신규 슬롯 (가장 광범위)
work/h3/global_slot_0x29e_writers.json
work/h3/global_slot_0x9bb4_writers.json
work/h3/global_slot_0x9cbc_writers.json
```

JSON 통계: 9 슬롯 × {direct_writes/reads, writers_by_func, readers_by_func} 데이터 + 모든 reader site 목록.

---

## 8. Round 18 핵심 takeaway

1. **GVM 외부 주입은 9 슬롯 모두에 적용** — 단일 0x444 슬롯이 아닌 시스템 표준 패턴.
2. **0x16c 가 0x444 와 동급의 핵심 task ptr** — 147 readers, single indirection (다른 종류).
3. **FUN_000439a0 = 7-entry JT type dispatcher** — 0x38 stride record array, type field 4..10.
4. **FUN_00047a14 = state transition (0xf)** — task_struct gate + 다른 task ptr 에 0xf 쓰기 + FUN_00098244 호출. 다음 진척의 결정적 onward 포인터.
5. **JT @ 0x8370** (binary 내부) — 첫 발견된 internal jump table. 7 entries 디코드가 type 4..10 의 의미를 풀어냄.
