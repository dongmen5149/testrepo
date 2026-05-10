# Hero3 Ghidra — Round 32 / PM-22 (2026-05-10)
## FUN_00042758 본문 (state initializer) + ObjectB read 패턴 정정 + 0x9b00 cluster 발견

> Round 31 의 0x24300 5-events 공통 helper (FUN_00042758) 본문 분석 + Round 31 의 "ObjectB address store" 가설을 raw disasm 으로 정정. 결과: FUN_00042758 = entity state initializer (cluster #1 처리), 17 ObjectB-related 사이트는 store 가 아니라 read 패턴.

## TL;DR (3줄)

1. ⭐⭐⭐ **FUN_00042758 = entity state initializer** (1.1KB, 21 cmp arms, 2 ctx_getter early + 1 memset_like). **task_struct[0x9afc~0x9b3c] cluster (Round 25 신규 cluster #1) 의 dominant reader** — 0x9afc/0x9b06/0x9b14/0x9b1c/0x9b3c 모두 사용. 0x019b/0x189/0x191/0x193/0x1ad/0x173 (0x18x-cluster medium_int) 5+5+1+1+1+1 = 14x 사용. memset_like at 0x42b6e = state buffer init. 5 events (35/48/49/51/57) = entity creation/reset.
2. ⭐⭐⭐ **Round 31 의 "ObjectB address store" 가설 부분 정정** — 0xac94 + 0x18 17 사이트 raw disasm 에서 실제 패턴은 **ObjectB read** (`ldr r3, [pc] (=0x18); add r3, sl; ldr r3, [r3]` = ObjectB instance ptr 읽기). 즉 17 사이트는 **task_struct[0xac94] 의 address 를 register 와 함께 ObjectB instance 도 read** — 결합 사용 패턴. ObjectB GOT slot 의 진짜 dynamic update 는 별도 사이트에 있을 가능성 (Round 27 의 first_sites 가 다른 패턴이었음).
3. ⭐⭐ **17 사이트 enclosing function 분포**: FUN_00030018 (7x), FUN_0008beba (7x), FUN_0008e89e (3x). FUN_000818f0 은 0xac94 read 만 하고 ObjectB 결합 안 함 (entity handler 자체는 ObjectB 추상화 사용 안 함). 3 funcs 가 ObjectB API + entity record 결합 사용 = entity ↔ system bridge.

부수 발견:
- ⭐⭐ **FUN_00042758 caller chain — single direct BL** (0x24302 in FUN_000241dc, literal pool 0건). 즉 dedicated initializer for 5 system events.
- ⭐ **task_struct[0x9b00 cluster] dominant reader 확정** — Round 25 의 신규 cluster #1 (0x9afc/0x9b01/0x9b14/0x9b1c) 이 FUN_00042758 의 **메인 working data**. cluster size 추정 ~64 byte (0x9afc~0x9b3c).
- ⭐ FUN_00042758 의 0x18x medium_int cluster (0x019b 5x, 0x189 2x, 0x191/0x193/0x1ad/0x173 1x) = 0x18x range 의 medium_int 들이 GOT slot 후보 (실제로 ctx field 인지 검증 필요).

## 1. FUN_00042758 (entity state initializer)

### 1.1 Boundary 와 prologue

| 측면 | 값 |
|---|---|
| 시작 | 0x42758 |
| 끝 | 0x42be8 (다음 push prologue) |
| size | 1168 byte (1.1KB) |
| instr | 551 |
| cmp arms | 21 |
| context_getter calls | **2** (early at 0x4276a, 0x42770 — 두 번 호출!) |
| memset_like calls | 1 (at 0x42b6e) |

```asm
0x42758: push {r4-r7, lr}              ; PIC standard prologue
0x4275a: mov r7, sl
0x4275c: mov r6, r8
0x4275e: push {r6, r7}
0x42760: ldr r1, [pc, #0x338]           ; GOT base setup
0x42762: mov sl, r1
0x42764: sub sp, #0x34                  ; 52 byte stack frame
0x42766: add sl, pc
0x42768: adds r4, r0, #0                ; r4 = caller_arg saved
0x4276a: bl 0x4ad10                      ; <-- 1st context_getter
0x4276e: str r0, [sp, #0x18]            ; task_ptr saved at sp+0x18
0x42770: bl 0x4ad10                      ; <-- 2nd context_getter (재호출)
0x42774: mov r2, sp
0x42776: adds r2, #0x33
0x42778: movs r3, #1
0x4277a: strb r3, [r2]                  ; *(sp+0x33) = 1  (local flag init)
0x4277c: adds r6, r0, #0                ; r6 = task_ptr
0x4277e: str r2, [sp, #0x14]            ; saved local addr
```

→ **state init pattern**:
- caller_arg 받기 (r4)
- task_ptr 두 번 fetch (r0, r6)
- local stack flag (offset +0x33) = 1
- local stack pointer (offset +0x14) = address of flag

### 1.2 PC-rel literal 분포

| value | count | 추정 |
|---|---|---|
| 0x019b | 5x | medium_int (0x18x cluster) |
| 0x189 | 2x | medium_int |
| 0x9b3c, 0x9b14, 0x9b06, 0x9b1c, 0x9afc, 0x9cc0 | 각 1x | task_struct fields (Round 25 cluster #1) |
| 0x191, 0x193, 0x1ad, 0x173 | 각 1x | medium_int (0x18x cluster) |
| 0x32c, 0x33c, 0x340, 0x344, 0x263 | 각 1x | small offsets |
| 0x704d6, 0xffffffff | 각 1x | binary_addr / -1 |

**핵심**: task_struct[0x9b00 cluster] 의 dominant reader 확정. Round 25 의 신규 cluster (FUN_00041c14 에서 발견) 가 이 함수의 메인 메모리.

### 1.3 cmp 분포

| imm | count |
|---|---|
| 0 | 9x |
| 3, 6, 0xd, 1 | 각 2x |
| 2, 4, 0x11, 8 | 각 1x |

→ spread state-by-state. 21 arms 중 most popular = `cmp #0`. Range 0..0x11 = 18 distinct states.

### 1.4 memset_like at 0x42b6e

함수 끝 부근 (0x42b6e) 의 memset_like (FUN_0009fb78) 호출. r0 = 어떤 buffer, r1 = byte value, r2 = length 추정. 함수가 종료 직전 buffer 초기화 = state reset.

### 1.5 정체 가설 — entity state initializer

조합 패턴:
- caller_arg (5 events 35/48/49/51/57 = lifecycle events)
- task_ptr 두 번 fetch (single-deref + 추가 fetch?)
- local stack flag init (state setup)
- task_struct[0x9b00 cluster] read (Round 25 cluster #1, FUN_00041c14 와 공유)
- 0x18x medium_int cluster (state IDs 또는 GOT slots)
- final memset_like (state buffer init)

→ **entity state initializer / lifecycle setup function**. 5 system events 의 응답으로 호출되어 entity state 를 fresh state 로 초기화.

caller chain:
- direct BL 단 1건 (0x24302 in FUN_000241dc 의 0x24300)
- literal pool 0건 = isolated dedicated initializer

## 2. ObjectB read 패턴 정정 (Round 31 부분 정정)

### 2.1 17 사이트 raw disasm 검증

Round 31 가설: 17 사이트 = **address store** (`*(sl + 0x18) = (task_ptr + 0xac94)`).

Round 32 raw 검증 — sample sites:

```asm
; FUN_00030018 의 사이트 0x31600
0x31600: ldr r4, [pc, #0x210]    ; r4 = 0xac94
0x31602: adds r2, r3, r4         ; r2 = task_ptr + 0xac94
0x31604: ldr r3, [pc, #0x218]    ; r3 = 0x18
0x31606: add r3, sl               ; r3 = sl + 0x18 = ObjectB GOT slot addr
0x31608: ldr r3, [r3]             ; r3 = *(GOT[0x18]) = ObjectB instance ptr  ← READ
0x3160a: ldr r1, [r3]             ; r1 = *ObjectB = vtable ptr (또는 first field)
0x3160c: adds r0, r7, #0
0x3160e: subs r0, #0x9c           ; r0 = r7 - 0x9c
```

**즉 store 가 아니라 ObjectB read + vtable read 패턴**. Round 31 의 가설 부분 정정.

### 2.2 정체 정정

| 측면 | Round 31 가설 | Round 32 정정 |
|---|---|---|
| 17 사이트 정체 | ObjectB GOT slot 에 task_struct[0xac94] address store | **ObjectB instance 와 task_struct[0xac94] 를 함께 read** |
| ObjectB slot dynamic update | 17 사이트가 update 시점 | 17 사이트는 update 가 **아님** (read 만), 진짜 dynamic update 는 별도 사이트 |
| 의미 | entity 활성화 시 ObjectB 갱신 | entity 처리 함수가 ObjectB 와 entity record 를 결합 사용 |

**진짜 ObjectB writer 사이트**는 추가 분석 필요 (Round 27 의 first_sites 의 store 패턴이 어디서 발생했는지 재검증).

### 2.3 17 사이트 enclosing function 분포

| 함수 | count |
|---|---|
| FUN_00030018 | 7x |
| FUN_0008beba | 7x |
| FUN_0008e89e | 3x |

**FUN_000818f0 은 이 결합 패턴 사용 안 함** = entity handler 자체는 ObjectB 추상화를 거치지 않고 task_struct 에서 직접 처리.

3 funcs (FUN_00030018/8beba/8e89e) 의 정체:
- FUN_00030018: 0xac94 14x reader (Round 27)
- FUN_0008beba: 0xac94 14x + 0xac98 22x reader, NPC dispatcher 영역 (Round 30 PROGRESS 표시)
- FUN_0008e89e: 0xac94 9x, SCN dispatcher main entry (PROGRESS 의 알려진 함수)

→ **3 funcs = entity ↔ system bridge** (entity record 와 ObjectB API 결합). 즉 entity 가 ObjectB 추상화를 통해 system service 받음.

### 2.4 ObjectB 의 진짜 정체 (Round 31~32 종합)

```
ObjectB GOT slot (0x18) — fixed system slot
  └─ ObjectB instance ptr (heap or fixed memory)
      └─ vtable (240 readers / 240 funcs system-wide):
           ├─ vtable[0]: first method (가장 자주 호출)
           ├─ vtable[+0x10]: another method
           └─ ... (9 known offsets: 0/0x10/0x20/0x44/0x54/0x58/0x68/0x7c/0x80)

Usage pattern (3 entity-bridge funcs):
  task_ptr+0xac94 + ObjectB instance + ObjectB.vtable[some_method]
  → entity record 를 ObjectB API 의 인자로 전달
  → ObjectB API 가 entity 에 system service 제공 (예: memory mgmt, sound, etc.)
```

ObjectB 가 **system service interface** (RTOS-like 인터페이스), entity 가 그 service 의 client.

## 3. 갱신된 entity 처리 모델

```
Active entity:
  ├─ task_struct[0xac78~0xac9d] 38B state record
  │     +0x1c (0xac94) = entity 의 substructure base address
  │
  ├─ FUN_000818f0 (5.6KB single-entity handler) — entity state 직접 처리
  │     - task_struct field 직접 access (200+)
  │     - ObjectB 추상화 사용 안 함
  │
  ├─ FUN_00030018, FUN_0008beba, FUN_0008e89e — entity ↔ system bridge
  │     - task_struct[0xac94] (entity self-address) + ObjectB API 결합
  │     - 17 사이트에서 ObjectB.vtable 호출
  │
  └─ FUN_00042758 — entity state initializer (lifecycle)
        - 5 system events (35/48/49/51/57) 응답으로 호출
        - task_struct[0x9b00 cluster] 처리 (Round 25 cluster #1)
        - memset_like 로 state buffer init
```

## 4. Round 33 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2CW | **ObjectB GOT slot 의 진짜 writer 사이트 추적** (Round 27 의 first_sites store 패턴이 어디?) | 도구 추가 lenient 화 또는 inline disasm |
| ⭐⭐ 2CX | FUN_00040cec 본문 (0x242c0 = 4-events 공통 helper) | `disasm_subsystem_func.py 0x40cec` |
| ⭐⭐ 2CY | task_struct[0x9b00 cluster] system-wide reader (Round 25 cluster #1 의 전체 사용) | KNOWN_FIELDS 0x9b00~0x9b40 추가 + 재실행 |
| ⭐⭐ 2CZ | 0x18x medium_int cluster (0x173/0x189/0x191/0x193/0x19b/0x1ad) 정체 — GOT slot vs ctx field | usage pattern 검증 |
| ⭐ 2DA | FUN_00030018 본문 (entity-bridge func) | `disasm_subsystem_func.py 0x30018` |
| ⭐ 2DB | FUN_0008beba/0x8e89e 본문 (다른 entity-bridge funcs) | `disasm_subsystem_func.py` |
| ⭐ 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 92% miss) | 도구 추가 확장 |

## 산출물

- `work/h3/most_popular_42758_disasm.json` — FUN_00042758 (1.1KB) 본문 분석
