# Hero3 Ghidra — Round 25 / PM-15 (2026-05-10)
## FUN_0009a008 (= FUN_0009b252 의 진짜 super-function) + 0x9bb4 bit-field 정정 + 0x9c70 cluster 검증

> Round 24 의 `find_task_struct_field_readers.py` 통계가 보여준 **0x9bb4 dominant (69 sites, 15 funcs, FUN_0009b252 46x)** 발견을 raw disasm 으로 검증한 결과, 가설 (= "type-tag dispatch key") 이 부정확했고 실제 의미는 **bit flag field** 임을 확정. 또 PM-7 의 "FUN_0009b252 (4KB) = type-tag reader" 자체가 더 큰 super-function 의 sub-label 임도 확인.

## TL;DR (3줄)

1. ⭐⭐⭐ **FUN_0009b252 는 함수 entry 가 아니라 FUN_0009a008 (8.6KB / 0x9a008~0x9c27e) 의 sub-label**. 진짜 함수는 2-stage JT dispatch (1st: `caller_arg2[caller_arg3]` byte ∈ [4..10] → 7 entries; 2nd: r6 ∈ [0..0xd] → 14 entries).
2. ⭐⭐⭐ **task_struct[0x9bb4] = bit flag field** (NOT type tag dispatch key). 모든 6 access 사이트가 `task_ptr + 0x9bb4` 를 helper FUN_0007d31c 로 전달, r1 = mask (4/8/0x10/0x20/0x40, 또는 negate 로 clear). 다른 14 readers (FUN_00041c6e/00041c14/0009ada4 등) 도 동일 bit-field 패턴.
3. ⭐⭐ **0x9c70/0x9c71/0x9c84/0x9c85 = 인접 byte fields** (각 100+/100+/39/37 sites). Round 24 의 "byte array base" 가설은 **정정** — 이들은 단순 byte fields (`ctx + offset` 으로 `ldrb` / `strb` 단순 read-write). Array indexing 패턴 없음.

부수 발견:
- ⭐ FUN_00041c14 (FUN_00041c6e 의 진짜 시작, 2.8KB / 0x41c14~0x42758) — 17-entry JT dispatcher. **신규 task_struct field cluster** 0x9afc/0x9b01/0x9b14/0x9b1c (총 21+ refs in 1 func) 발견.
- ⭐ FUN_00044a38 (388B) / FUN_000482c8 (492B) — **거의 identical sibling dispatchers** (둘 다 cmp #0x1c bhi default + 13~14 context_getter call + 0x9cb8 4x reference). Template-instantiated 또는 source-copy 가능성.
- ⭐ **신규 GOT slot 0xd1c** 발견 (FUN_0009a008 사이트 0x9a278/0x9a326 에서 `ldr r3, [pc, #N]; add r3, sl` 패턴). Round 23 의 8 GOT slots 에 추가 → 누적 **9 GOT slots**.

## 1. FUN_0009a008 (8.6KB) — 진짜 함수 boundary

PM-7/Round 24 의 FUN_0009b252 (4KB) 분석은 이 함수의 **sub-label** 을 본 것. 진짜 함수 시작 = 0x9a008.

### 1.1 Function boundary 확정

```
0x9a008: push {r4, r5, r6, r7, lr}
0x9a00a: mov r7, sl
0x9a00c: mov r6, r8
0x9a00e: push {r6, r7}             ; PIC standard prologue (sl, r8 spill)
0x9a010: sub sp, #0x44              ; 0x44 byte stack frame
...
0x9c27e: (이전 instr)
0x9c280: push {r4, r5, lr}          ; <-- 다음 함수 시작 (FUN_0009c280)
```

함수 size = 0x9c280 - 0x9a008 = **0x2278 = 8824 bytes (~8.6KB)**. 1881 instructions.

### 1.2 Caller convention

prologue 가 caller args 5개 받음:
- r0 (= caller arg 1) → `str r0, [sp, #0x38]` (saved)
- r1 (= caller arg 2) → `str r1, [sp, #0x34]` (record array pointer 추정)
- r2 (= caller arg 3) → `lsls r2, r2, #0x18; lsrs r4, r2, #0x18` (unsigned byte, record index 추정)
- r3 (= caller arg 4) → `lsls r3, r3, #0x18; lsrs r6, r3, #0x18` (unsigned byte, second-stage type tag)
- [sp, #0x60] (= caller arg 5) → `lsrs r7, r3, #0x18` (unsigned byte)

### 1.3 First-stage JT dispatch (0x9a04a)

```asm
0x9a02a: bl 0x4ad10                 ; context_getter, r0 = task_ptr
0x9a030: adds r0, #0xb4              ; r0 = task_ptr + 0xb4 (NOT used here, saved to r8)
0x9a036: mov r8, r0
0x9a03a: ldr r1, [sp, #0x34]        ; r1 = caller_arg2 (record array ptr)
0x9a03e: asrs r3, r0, #0x18         ; r3 = signed byte (caller_arg4 saved)
0x9a040: ldrsb r3, [r1, r3]         ; r3 = signed byte at [caller_arg2 + caller_arg4]
0x9a042: subs r1, r3, #4
0x9a044: cmp r1, #6                 ; range check: r1 ∈ [0..6] (= byte ∈ [4..10])
0x9a046: bhi 0x9a07e                 ; default error
0x9a048: ldr r3, [pc, #0x2f8]        ; JT base offset (negative_signed)
0x9a04a: mov r0, sl                  ; r0 = GOT base
0x9a04c: adds r2, r0, r3             ; r2 = JT base
0x9a04e: lsls r1, r1, #2             ; r1 = idx * 4
0x9a050: ldr r3, [r1, r2]
0x9a052: adds r3, r3, r2
0x9a054: mov pc, r3                   ; <-- JT jump (7 entries)
```

**1st-stage key = `caller_arg2[caller_arg4]` byte** (record array indexed by some offset). 즉 caller 가 record array + index 를 줘서 그 자리의 byte 가 dispatch key.

### 1.4 Second-stage JT dispatch (0x9b286, sub-label "FUN_0009b252")

```asm
0x9b252: movs r2, #0xb               ; (이건 sub-label 안의 명령, 함수 entry 아님)
0x9b254: bl 0x9a7f0
...
0x9b27e: cmp r1, #0xd
0x9b280: bls 0x9b286
0x9b282: bl 0x9a07e                  ; default error
0x9b286: ldr r3, [pc, #0x310]        ; JT base = 0xffffa318 (negative offset)
0x9b288: mov r0, sl
0x9b28a: adds r2, r0, r3
0x9b28c: lsls r1, r1, #2
0x9b28e: ldr r3, [r1, r2]
0x9b290: adds r3, r3, r2
0x9b292: mov pc, r3                  ; <-- JT jump (14 entries: 0..0xd)
```

**2nd-stage key = r6** (caller arg 4 byte, 즉 caller 가 직접 second-stage type tag 를 전달). r1 = 8-bit signed of r6.

JT base value = 0xffffa318 (signed). 실제 binary 위치 = `(GOT base) + 0xffffa318 = (GOT base) - 0x5ce8`. GOT base = 0xb2c40 (Round 23 확정) 이라면 JT @ 0xacf58.

## 2. task_struct[0x9bb4] = bit flag field

### 2.1 Round 24 의 가설 vs 실측

| 측면 | Round 24 가설 | Round 25 실측 |
|---|---|---|
| 정체 | type tag dispatch key (state machine state) | bit flag field (다중 boolean state) |
| FUN_0009b252 의 46x access | dispatch 의 키로 자주 read | 각각의 bit 를 test/set/clear |
| Helper 함수 | 직접 cmp arm (??) | **FUN_0007d31c (bit op helper)** 로 전달 |

### 2.2 모든 6 access 패턴이 동일

FUN_0009a008 안의 모든 0x9bb4 LDR 사이트:

```asm
bl 0x4ad10                ; context_getter, r0 = task_ptr
ldr r4, [pc, #N]          ; r4 = 0x9bb4
movs r1, #M                ; r1 = bitmask (예: 0x10, 4, 8, 0x20)
adds r0, r0, r4           ; r0 = task_ptr + 0x9bb4
add r2, sp, #0x3c         ; r2 = stack output buffer
bl 0x7d31c                ; bit op helper (test? set? clear via r1 sign?)
```

`rsbs r1, r1, #0` (negate) 가 한 사이트에 있음 → r1 < 0 = clear bit, r1 > 0 = set/test bit.

### 2.3 다른 14 readers 도 같은 패턴

`find_task_struct_field_readers.py` 의 first_sites 의 post_pattern 분석 결과:
- FUN_0003fbec @ 0x3fbfa: `movs r3, #0x10` (= 1<<4 mask)
- FUN_00041c6e @ 0x424f6: `movs r1, #4` (= 1<<2 mask)
- FUN_00041c6e @ 0x4256a: `movs r3, #0x14` (= 0b10100, 두 비트 set)
- FUN_00041c6e @ 0x425aa: `rsbs r1, r1, #0` (negate, clear bit)

**즉 task_struct[0x9bb4] = 다중 boolean flag 가 packed 된 byte/word**. 각 bit 가 별개의 state.

### 2.4 인접 fields cluster (FUN_00041c14 분석에서)

| field | sites | 추정 의미 |
|---|---|---|
| 0x9bb4 | 5x | bit flag field (위 분석) |
| 0x9bb6 | 1x | adjacent (signed short, +2 offset within bitmap) |
| 0x9bb7 | 1x | adjacent byte |
| 0x9bc8 | 1x | small offset cluster |

→ **task_struct[0x9bb4..0x9bc8] = bit flag substructure** (16 byte 정도의 flags 영역).

## 3. task_struct[0x9bd0] = ptr-to-object slot (vtable invoker)

FUN_0009a008 안의 3 사이트가 동일 패턴:

```asm
bl 0x4ad10               ; context_getter, r0 = task_ptr
ldr r5, [pc, #N]         ; r5 = 0x9bd0
adds r0, r0, r5          ; r0 = task_ptr + 0x9bd0
ldr r3, [r0]             ; r3 = *(task_ptr + 0x9bd0) = object pointer
ldr r0, [r3]             ; r0 = *r3 = vtable pointer
adds r0, #8              ; r0 = vtable + 8
bl 0x7cd58               ; method invoker (vtable[2] 호출?)
```

**즉 task_struct[0x9bd0] = ptr-to-object** (with vtable). 매번 같은 vtable[8] method 호출.

세 사이트 모두 동일 패턴 = 같은 object 의 같은 method 를 다른 path 에서 invoke.

## 4. FUN_00041c14 (FUN_00041c6e 의 진짜 시작)

### 4.1 Boundary

- 시작: 0x41c14 (`push {r4-r7, lr}; mov r7, sl; mov r6, r8; push {r6, r7}; ldr r0, [pc, #0x324]; mov sl, r0; sub sp, #0x44; add sl, pc`)
- 끝: 0x42758 (다음 push prologue)
- size: **0xb44 = 2884 bytes (~2.8KB)**, 1315 instructions
- JT dispatch range: 0..0x10 (= 17 entries) at 0x41c72

### 4.2 신규 task_struct field cluster 발견

literal value 빈도 (top 10):
| value | count | 추정 |
|---|---|---|
| 0x9b14 | 10x | byte field cluster #1 |
| 0x9b01 | 6x | byte field cluster #1 (1-byte offset) |
| 0x9bb4 | 5x | bit flag field (Round 24 dominant) |
| 0x019b | 4x | medium_int (record stride? GOT slot?) |
| 0x019d | 4x | medium_int |
| 0x9b1c | 4x | byte field cluster #1 |
| 0x9cb8 | 4x | record array adjacent (= 0x9cbc - 4) |
| 0x9cbc | 2x | record array slot |

**신규 cluster 0x9afc~0x9b1c** = task_struct 의 별도 substructure (총 21+ refs in 단일 func).

### 4.3 첫 cmp arm 이 곧장 sub-label 진입

```asm
0x41c66: cmp r3, #0x00 → beq 0x41c6e   ; <-- 0x41c6e (PM-7 의 sub-label) 가 cmp r3 == 0 path
```

즉 0x41c6e = "초기 상태" path 의 entry.

## 5. FUN_00044a38 + FUN_000482c8 — sibling dispatchers

두 함수가 거의 identical:

| 측면 | FUN_00044a38 | FUN_000482c8 |
|---|---|---|
| 시작 | 0x44a38 | 0x482c8 |
| 크기 | 388 bytes | 492 bytes |
| Prologue | `push {r4-r7,lr}; mov r7,sl; push {r7}` | 동일 |
| 1st cmp | `cmp r1, #0x1c → bhi default` | `cmp r4, #0x1c → bhi default` |
| 2nd cmp | `cmp r3, #0x00 → ble` | 동일 |
| context_getter calls | 13 | 14 |
| 0x9cb8 ref | 4x (literal pool 같은 위치) | 4x (literal pool 같은 위치) |

→ **template-instantiated** 또는 source-copy 가능성. record array dispatcher 의 두 변형 (다른 record stride/type 처리).

## 6. 0x9c70/0x9c71/0x9c84/0x9c85 = 인접 byte fields (Round 24 정정)

### 6.1 Wide-scan 결과

| field | sites | 사용 패턴 |
|---|---|---|
| 0x9c70 | 112 | byte read (`ldrb r3, [r3]`) + byte write (`strb r3, [r2]`) |
| 0x9c71 | 115 | byte read + byte write |
| 0x9c84 | 39 | byte read + byte write |
| 0x9c85 | 37 | byte read + byte write |

### 6.2 모든 사이트가 단순 byte field 패턴

```asm
bl 0x4ad10              ; context_getter, r0 = task_ptr
adds r3, r0, #0          ; r3 = task_ptr
ldr r1, [pc, #N]         ; r1 = field_offset (0x9c70 등)
adds r2, r3, r1          ; r2 = task_ptr + offset
movs r3, #M              ; r3 = immediate value (0/2/8 등)
strb r3, [r2]            ; *task_struct[offset] = M
```

또는 read 측:

```asm
ldr r1, [pc, #N]
adds r3, r3, r1
ldrb r3, [r3]            ; r3 = *task_struct[offset]
cmp r3, #0
beq ...                  ; boolean branch
```

### 6.3 Round 24 가설 정정

| 측면 | Round 24 가설 | Round 25 실측 |
|---|---|---|
| 정체 | byte array base offset (record_idx 기반 access) | 4개 인접 byte fields (단순 read/write) |
| 사용 | `task_ptr + record_idx_byte + 0x9c70 + 2` (multi-level) | `task_ptr + 0x9c70` (단순) |
| field count | 1 array | 4 byte fields (0x9c70/71/84/85) |

Round 24 의 "byte array base" 는 한 사이트의 복합 계산을 일반화한 것. 실측은 단순 byte fields.

## 7. 신규 GOT slot — 0xd1c

FUN_0009a008 의 사이트 0x9a278/0x9a326 에서:

```asm
ldr r3, [pc, #N]          ; r3 = 0xd1c
add r3, sl                ; r3 = sl + 0xd1c (GOT slot access)
ldr r0, [r3]              ; r0 = *(GOT[0xd1c])
```

`add r3, sl` 패턴 → 진짜 GOT slot. Round 23 의 8 GOT slots 에 추가:

| slot | 의미 |
|---|---|
| 0x18 | ObjectB (240 readers) |
| 0x16c | alternate task struct ptr (147 readers) |
| 0x29e | small flag |
| 0x128 | secondary state ptr |
| 0x444 | task_ptr (= context_getter 가 read) |
| 0x44c | ObjectA (resource manager) |
| 0xd00 | StorageCell |
| 0xd04 | ObjectA helper data ptr #1 |
| 0xd08 | ObjectA helper data ptr #2 |
| **0xd1c** ⭐ | **신규** — ObjectA helper cluster 인접 (0xd00 + 0x1c) |

누적 **9 GOT slots** (모두 0 direct write 확인됨).

## 8. 갱신된 게임 시스템 모델

### 8.1 task_struct 의 의미 있는 fields (Round 25 시점)

| offset | 정체 (Round 25 검증 후) |
|---|---|
| 0x6 | signed byte (0x16c-deref 에서 자주 read — small enum field) |
| 0x29e | small flag |
| 0xb4 | byte (record array byte offset 후보 — FUN_0009a008 의 saved register r8) |
| 0x9afc~0x9b1c | byte field cluster #1 (FUN_00041c14 에서 활발) |
| **0x9bb4~0x9bc8** ⭐ | **bit flag substructure** (다중 boolean state, 0x7d31c helper) |
| 0x9bd0 | ptr-to-object (vtable invoker via 0x7cd58) |
| **0x9c70/71/84/85** ⭐ | **4개 인접 byte fields** (각 100+/100+/39/37 sites) |
| 0x9cb8/9cbc/9cc0/9cfe | record array slots |
| 0x9e28 | sound state #1 |
| 0x9e78 | per-context flag |
| 0xa220/a244/a245/a254 | sound state cluster |
| 0xac78 | FUN_000241dc 전용 |

### 8.2 Helper functions 매핑

| addr | 정체 |
|---|---|
| 0x4ad10 | context_getter (single deref `*GOT[0x444]`) |
| 0x7d31c | **bit test/set/clear helper** ⭐ (r0 = ptr, r1 = mask, r2 = output) |
| 0x7cd58 | **vtable method invoker** ⭐ (r0 = vtable+offset) |
| 0x99764 | sound_trigger (r0=ctx, r1=sound_id) |
| 0x9fd64 | sound paired helper |

## 9. Round 26 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2BJ | FUN_0007d31c (bit helper) 본문 분석 | `disasm_subsystem_func.py 0x7d31c <next_push>` |
| ⭐⭐ 2BK | FUN_0007cd58 (vtable invoker) 본문 분석 | `disasm_subsystem_func.py 0x7cd58 <next_push>` |
| ⭐⭐ 2BL | task_struct[0x9afc~0x9b1c] cluster wide-scan (FUN_00041c14 외 다른 readers) | `find_task_struct_field_readers.py --field 0x9b14` |
| ⭐ 2BM | FUN_0009a008 의 1st-stage JT @ 0xacf58 디코드 (7 entries) | binary 직접 read |
| ⭐ 2BN | FUN_0009a008 의 2nd-stage JT (sub-label "FUN_0009b252") 디코드 (14 entries) | binary 직접 read |

## 산출물

- `work/h3/type_tag_dispatcher_v2_disasm.json` — FUN_0009a008 (0x9a008~0x9c280) 본문 분석
- `work/h3/record_disp_41c14_disasm.json` — FUN_00041c14 (0x41c14~0x42758) 본문 분석
- `work/h3/record_disp_44a38_disasm.json` — FUN_00044a38 (388B)
- `work/h3/record_disp_482c8_disasm.json` — FUN_000482c8 (492B)
- `work/h3/task_struct_field_readers.json` — Round 24 의 누적 reader 통계 (재사용)
