# Hero3 Ghidra — Round 33 / PM-23 (2026-05-10)
## ObjectB GOT slot writer 0건 확정 (Round 31 가설 완전 폐기) + FUN_00040cec event registrar + 0x9b00 cluster 도구 limitation

> Round 32 의 "ObjectB read 패턴 정정" 후속 — ObjectB GOT slot (0x18) 의 진짜 writer 사이트를 wide-scan 으로 찾기. 결과: **0 writes, 876 reads** → **ObjectB 도 GVM firmware 외부 주입** (slot 0x444, 8 GOT slots 와 같은 패턴). Round 31 의 "current-active-entity proxy" 가설 완전 폐기, **Round 21 의 원래 master interface 가설로 회귀**.

## TL;DR (3줄)

1. ⭐⭐⭐ **ObjectB GOT slot writer 0건 확정** — 909 LDR pcrel sites (value=0x18), 876 sites = 진짜 GOT[0x18] access (add+sl 패턴), 그 중 **read = 876, WRITE = 0**. 즉 게임 binary 가 ObjectB slot 을 한 번도 update 하지 않음 → **ObjectB 도 GVM firmware 외부 주입** (Round 23 의 8 GOT slots 패턴, task_ptr slot 0x444 와 동일). **Round 21 의 원래 master interface 가설 confirmed** (Round 31 의 dynamic proxy 가설 완전 폐기).
2. ⭐⭐⭐ **17 ObjectB-read 사이트의 진짜 의미** — Round 31~32 의 가설들 (address store / instance + record 결합 read) 정정. 실제 패턴: `r2 = task_ptr+0xac94 (entity record address); r3 = ObjectB instance; ObjectB.method(r2)` = **entity record 를 ObjectB API 의 인자로 전달**. 즉 ObjectB = static system service interface, 3 entity-bridge funcs 가 entity record 를 인자로 ObjectB method 호출.
3. ⭐⭐ **FUN_00040cec = simple event code register** (240 byte). 첫 액션: `*task_struct[0x274] = caller_arg` (4 events -4..-1 의 event code 등록), 6 cmp arms (state 0/2/3/5), 1 ctx_getter early. **0x274 = task_struct field 0x274** (= 0x9d * 4) 신규 발견.

부수 발견:
- ⭐⭐ **0x9b00 cluster (Round 25 신규 cluster #1) 가 도구 lenient 화 후에도 거의 0 hits** = 다른 lenient 한 패턴 사용 (stack save/load 또는 multi-hop register propagation). FUN_00042758 본문에서 5x 봤지만 도구는 못 잡음. 다음 라운드 추가 도구 강화 필요.
- ⭐ **task_struct[0x274] = event code field** (FUN_00040cec 가 4-events caller_arg 저장 위치) — 신규 task_struct field offset 발견 (KNOWN_FIELDS 추가).
- ⭐ FUN_00040cec 도 isolated (아직 caller chain 검증 안 함, 그러나 Round 30 표 통해 caller = FUN_000241dc 의 0x242c0 호출만으로 보임).

## 1. ObjectB GOT slot (0x18) writer 추적

### 1.1 Wide-scan 결과

```
total LDR pcrel sites with value=0x18: 909
of which add+sl followed (real GOT[0x18] access): 876
  read (after add+sl, then ldr): 876 (100%)
  ⭐ WRITE (after add+sl, then str): 0
```

**909 - 876 = 33 사이트는 add+sl 안 따름** = 0x18 이 다른 의미 (예: byte counter, immediate constant) 로 사용. 진짜 GOT slot access 는 876 사이트.

**876 read / 0 write** = ObjectB slot 의 game-side 갱신 사이트가 정확히 0건.

### 1.2 의미 — GVM firmware 외부 주입

PIC 환경에서 GOT slot 의 game-side write 부재 = GVM firmware 가 binary load 시점에 inject. 이는 Round 23 의 8 GOT slots 와 같은 패턴:
- slot 0x18 (ObjectB) — **0 writes 확정 (Round 33)**
- slot 0x16c (alternate task struct) — Round 23 0 writes
- slot 0x29e (small flag) — Round 23 0 writes
- slot 0x128 (state ptr) — Round 23 0 writes
- slot 0x444 (task_ptr) — Round 31 0 writes 확정
- slot 0x44c (ObjectA) — Round 23 0 writes
- slot 0xd00, 0xd04, 0xd08, 0xd1c — Round 23~25 0 writes

→ **모든 9 GOT slots 가 GVM firmware 외부 주입 확정**. 게임 binary 는 read 만.

### 1.3 Round 21~32 의 ObjectB 가설 진화

| Round | 가설 | 상태 |
|---|---|---|
| 21 (PM-11) | ObjectB = master GVM interface (240 readers, static) | **✅ 최종 confirmed** |
| 23 (PM-13) | ObjectB 는 단순 task_ptr_holder | partial — ObjectB 는 system-wide service interface |
| 31 (PM-21) | ObjectB = current-active-entity proxy (dynamic update) | ❌ **완전 폐기** (Round 33) |
| 32 (PM-22) | 17 사이트 = ObjectB instance + entity record 결합 read | ✅ 패턴은 맞음, 의미는 정정 |
| **33 (PM-23)** | **ObjectB = static GVM-injected master interface, 17 사이트 = ObjectB.method(entity_record) 호출** | **✅ 최종 모델** |

### 1.4 17 사이트의 진짜 의미

```asm
ldr r4, [pc] (=0xac94); adds r2, r3, r4    ; r2 = task_ptr + 0xac94 (= entity record self-address)
ldr r3, [pc] (=0x18); add r3, sl            ; r3 = sl + 0x18 = GOT slot 주소
ldr r3, [r3]                                 ; r3 = ObjectB instance ptr (READ)
ldr r1, [r3]                                 ; r1 = ObjectB.vtable[0] (또는 first field)
adds r0, r7, #0; subs r0, #0x9c              ; r0 = r7 - 0x9c (다른 인자)
; ... ObjectB.method(r0, r1, r2, ...) 호출
```

**결론**: r2 = entity record self-address 가 **ObjectB API 의 r2 인자** 로 전달. 즉 `ObjectB.method(arg0=r0, arg1=r1, entity_ptr=r2)`. ObjectB 가 entity 처리를 위해 entity record 를 인자로 받음.

3 entity-bridge funcs (FUN_00030018/0x8beba/0x8e89e) 의 정체:
- entity 의 task_struct[0xac94] address 를 r2 로 전달
- ObjectB instance 와 vtable read
- ObjectB API 호출 (entity-specific service)

## 2. FUN_00040cec — simple event code register

### 2.1 Boundary 와 prologue

| 측면 | 값 |
|---|---|
| 시작 | 0x40cec |
| 끝 | 0x40ddc (다음 push prologue) |
| size | 240 byte (0.24KB) |
| instr | 109 |
| cmp arms | 6 |
| context_getter | 1 (early) |

```asm
0x40cec: push {r4, r5, r6, lr}    ; smaller PIC prologue (no r8)
0x40cee: mov r6, sl
0x40cf0: push {r6}
0x40cf2: ldr r1, [pc, #0xd0]       ; GOT base
0x40cf4: mov sl, r1
0x40cf6: add sl, pc
0x40cf8: adds r5, r0, #0           ; r5 = caller_arg saved
0x40cfa: bl 0x4ad10                 ; context_getter, r0 = task_ptr
0x40cfe: movs r2, #0x9d
0x40d00: lsls r2, r2, #2           ; r2 = 0x9d << 2 = 0x274
0x40d02: adds r3, r0, r2           ; r3 = task_ptr + 0x274
0x40d04: str r5, [r3]              ; ⭐ *(task_ptr + 0x274) = caller_arg
```

→ **첫 액션이 task_struct[0x274] 에 caller_arg store**.

### 2.2 caller_arg 의 의미

FUN_000241dc 의 0x242c0 case 는 4 events (-4..-1) 를 처리:
```asm
0x242c0: adds r0, r5, #0    ; r0 = caller_arg (= -4 ~ -1)
0x242c2: bl 0x40cec
```

→ **task_struct[0x274] = signed event code (-4..-1)**. 이는 game system event 의 lifecycle 단계 추적 가능 (4 인접 events 가 같은 함수 사용 = 동일 시리즈 event).

### 2.3 신규 task_struct field — 0x274

KNOWN_FIELDS 에 0x274 추가. 의미: **event code register / state ID** (4 events -4..-1 가 자기 code 를 저장).

### 2.4 6 cmp arms (state-by-state)

```
0x40d22: cmp r0, #0x02 → beq 0x40d2e
0x40d26: cmp r0, #0x02 → bgt 0x40db8
0x40d2a: cmp r0, #0x00 → beq 0x40d34
0x40d3a: cmp r0, #0x00 → beq 0x40d4a
0x40db8: cmp r0, #0x03 → beq 0x40d34
0x40dbc: cmp r0, #0x05 → bne 0x40d2e
```

→ **task_struct 의 다른 field (r0) 의 값 0/2/3/5 검사**. 즉 event code register 후 다른 state 검사로 분기.

## 3. 0x9b00 cluster 도구 limitation

### 3.1 Wide-scan 결과 (도구 KNOWN_FIELDS 38 fields)

```
field 0x9afc (39676): 0 verified ctx+field sites in 0 unique funcs
field 0x9b01 (39681): 0 verified ctx+field sites in 0 unique funcs
field 0x9b06 (39686): 0 verified ctx+field sites in 0 unique funcs
field 0x9b14 (39700): 0 verified ctx+field sites in 0 unique funcs
field 0x9b1c (39708): 1 verified ctx+field sites in 1 unique funcs
field 0x9b3c (39740): 0 verified ctx+field sites in 0 unique funcs
```

→ **0x9b00 cluster auto-detect 거의 실패**.

### 3.2 모순 — Round 32 본문 분석에서는 발견됨

FUN_00042758 본문 (Round 32) 에서 task_struct[0x9afc/0x9b06/0x9b14/0x9b1c/0x9b3c] 5x access 발견. 그러나 도구는 못 잡음.

**원인 추정**: FUN_00042758 의 task_ptr 사용 패턴이 도구의 R0-propagation 패턴과 다름:
```asm
bl 0x4ad10
str r0, [sp, #0x18]       ; ← stack save (도구 미커버)
bl 0x4ad10
adds r6, r0, #0            ; ← r6 saved (도구 커버하지만 r6 가 함수 전체 used)
; ... 100+ instr 후
ldr r0, [sp, #0x18]        ; ← stack reload (도구 미커버)
ldr rX, [pc, #N]            ; field offset
adds rY, r0, rX
```

도구가 stack save/reload 패턴을 추적 못해서 R0_equiv 추적 끊김.

### 3.3 다음 라운드 도구 강화 필요

- stack save/reload 추적: `str r0, [sp, #N]` ↔ `ldr rX, [sp, #N]` 매칭
- 함수 전체 R0_equiv 추적 (현재는 16-instr window)
- 또는 cluster 별 직접 wide-scan (R0 propagation 무시, ctx + offset 패턴만 검색)

## 4. 갱신된 시스템 모델

### 4.1 GVM firmware 외부 주입 9 GOT slots (모두 0 writes 확정)

```
GVM Firmware (binary load 시점에 inject)
  ├─ slot 0x18  → ObjectB (master GVM interface) ⭐ Round 33 0 writes 확정
  ├─ slot 0x16c → alternate task struct
  ├─ slot 0x29e → small flag
  ├─ slot 0x128 → state ptr
  ├─ slot 0x444 → task_ptr (context_getter) ⭐ Round 31 0 writes 확정
  ├─ slot 0x44c → ObjectA (resource manager)
  ├─ slot 0xd00 → StorageCell
  ├─ slot 0xd04, 0xd08 → ObjectA helper data ptrs
  └─ slot 0xd1c → ObjectA helper cluster 인접
```

### 4.2 Object 사용 패턴 모델 (Round 33 결정판)

```
ObjectB (GOT[0x18]) — static system service interface
  ├─ 240 readers / 240 funcs
  ├─ vtable 9 known method offsets (0/0x10/0x20/0x44/0x54/0x58/0x68/0x7c/0x80)
  └─ Usage:
       - Direct ObjectB.method() 호출 (system service request)
       - 17 사이트: ObjectB.method(entity_record_ptr) — entity-specific service
                   (3 entity-bridge funcs: FUN_00030018, FUN_0008beba, FUN_0008e89e)

ObjectA (GOT[0x44c]) — resource manager
  ├─ 8 readers, vtable 12 method offsets
  └─ acquire-use-release lifecycle (POSIX-like errors)

0x9bd0-Object (task_struct[0x9bb4]'s +0x1c instance ptr)
  ├─ 21 unique reader funcs (system-wide)
  ├─ vtable[+0x08] = function ptr to FUN_0007cd58 (60% dominant)
  └─ vtable[+0x18] = halfword metadata (sprite tile coord 후보)
```

### 4.3 task_struct field 통계 (Round 33 추가)

신규 추가:
- **0x274** ⭐ — FUN_00040cec store target (event code, signed)

확장된 KNOWN_FIELDS = **39 fields** (0x9b06 추가).

## 5. Round 34 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2DC | **find_task_struct_field_readers.py 추가 lenient 화** — stack save/reload 추적 | 도구 코드 수정 |
| ⭐⭐ 2DD | task_struct[0x274] (event code) 의 다른 reader 매핑 — 누가 읽는지 | wide-scan |
| ⭐⭐ 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 92% miss, 같은 한계) | 도구 추가 확장 |
| ⭐⭐ 2DA | FUN_00030018 본문 (entity-bridge func 의 정체) | `disasm_subsystem_func.py 0x30018` |
| ⭐ 2DB | FUN_0008beba/0x8e89e 본문 (다른 entity-bridge funcs) | `disasm_subsystem_func.py` |
| ⭐ 2DE | 0x9b00 cluster 직접 wide-scan (R0 propagation 무시) | tool 추가 작성 |
| 2BM | FUN_0009a008 의 1st-stage JT @ 0xacf58 디코드 (7 entries) | binary 직접 read |
| 2BN | FUN_0009a008 의 2nd-stage JT (sub-label "FUN_0009b252") 디코드 (14 entries) | binary 직접 read |

## 산출물

- `tools/recon/find_task_struct_field_readers.py` — KNOWN_FIELDS 38 → 39 fields (0x274 + 0x9b06 추가)
- `work/h3/fun_40cec_disasm.json` — FUN_00040cec (240B) 본문
