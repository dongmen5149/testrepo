# Hero3 Ghidra — Round 31 / PM-21 (2026-05-10)
## FUN_000241dc 7 handlers 본문 + 0xac94 = ObjectB instance 발견 + task_struct GVM-injected 확정

> Round 30 의 74-entry JT 디코드 결과 (12 진짜 events → 7 destinations) 후속. 7 destination handlers 본문 분석 + 0xac94 의 외부 array 정체 추적 = **GOT slot 0x18 (ObjectB) 발견**. 즉 entity state record (0xac78) 의 +0x1c 가 ObjectB instance 자체.

## TL;DR (3줄)

1. ⭐⭐⭐ **0xac94 = ObjectB instance 의 base** — 60 LDR 사이트의 second LDR 분포: **0x18 (17x dominant)** = **GOT slot 0x18 (ObjectB ptr) offset**. 즉 `*(sl + 0x18) = (task_ptr + 0xac94)` = **ObjectB GOT slot 에 entity substructure 의 self-address 등록**. Round 21 의 ObjectB master GVM interface (240 readers) 가 사실 **task_struct[0xac94] 안의 entity-per instance**. entity 활성화 시 ObjectB slot 을 dynamic update.
2. ⭐⭐⭐ **task_struct allocator 검증 = GVM-injected 확정** — GOT slot 0x444 (task_ptr) write 사이트 **0건**, read 사이트 7건. 즉 게임 binary 안에 task_struct allocator 부재 = **GVM firmware 가 외부에서 task_struct maintain** (Round 23 가설 최종 확정).
3. ⭐⭐ **FUN_000241dc 7 handlers 본문 분석** — 7 destinations 의 의미 매핑:
   - **0x24300 (most popular, 5 events)**: 단순 wrapper `bl FUN_00042758(caller_arg)`
   - **0x242c0 (4 events)**: `bl FUN_00040cec(caller_arg)`
   - **0x2427a (event -16)**: complex toggle + bl 0x3fbd4 + bl 0x48bf8(r0=5)
   - **0x24308~ 영역**: ObjectA destructor (0x98364, Round 20 일치) + state reset = **cleanup handler**

부수 발견:
- ⭐⭐ **2 substructure 의 통일된 +0x1c 패턴**: substructure A (0x9bb4) 의 +0x1c = 0x9bd0-Object instance ptr / substructure B (0xac78) 의 +0x1c = 0xac94 = **ObjectB instance**. **task_struct = multiple substructure collection** 가설 최종 확정 (각 substructure 가 +0x1c 위치에 instance pointer).
- ⭐ FUN_000241dc 의 신규 helper 함수 매핑: 0x42758 (5-events 공통) / 0x40cec (4-events 공통) / 0x3fbd4 / 0x252c8 / 0x99cbc / 0x98364 (ObjectA destructor) / 0x947f4 / 0x48bf8 / 0x2c6a4
- ⭐ context_getter (FUN_0004ad10) 가 GOT[0x444] 의 **유일한 reader cluster** (7 reads 모두 context_getter 안). 다른 함수들은 context_getter 호출로 우회.

## 1. FUN_000241dc 7 destination handlers 본문

### 1.1 handler 매핑

| dest | events | 본문 요약 | helper 호출 |
|---|---|---|---|
| 0x24246 | 62 (84%) | `add sp, #4; pop ...; pop {r4-r6, pc}` (epilogue, no-op) | - |
| **0x24300** | **5** (35/48/49/51/57) | `r0=caller_arg; bl 0x42758; b epilogue` | **FUN_00042758** ⭐ |
| 0x242c0 | 4 (-4..-1) | `r0=caller_arg; bl 0x40cec; b epilogue` | FUN_00040cec |
| 0x242d0 | 3 (-5/53/55) | check chain → fall-through to 0x24308 area | 0x252c8/0x527fc |
| 0x24264 | 1 (-10) | task[+0xf2] short check → bl 0x2c6a4(r0=0xe) | 0x2c6a4 |
| 0x2427a | 1 (-16) | task field toggle + bl 0x3fbd4 + bl 0x48bf8(r0=5) | 0x3fbd4, 0x48bf8 |
| 0x242c8 | 1 (42) | bl 0x3fbd4 + r0=8 + fall-through to 0x24274 | 0x3fbd4, 0x2c6a4 |

### 1.2 0x24300 (most popular, 5 events) — minimal wrapper

```asm
0x24300: adds r0, r5, #0     ; r0 = caller arg (saved as r5)
0x24302: bl 0x42758           ; <-- FUN_00042758(caller_arg)
0x24306: b 0x24246             ; return
```

→ 5 unrelated events 가 **단일 helper FUN_00042758 호출**. caller_arg 그대로 전달.

**FUN_00042758** = Round 25 의 boundary 검색에서 발견된 함수 (FUN_00041c14 다음). 다음 라운드의 핵심 추적 대상.

### 1.3 0x24308~0x2435e cleanup/state-reset 영역

이 영역은 7 destinations 표 에 없지만 0x242d0/0x24300 의 fall-through path 에서 도달:

```asm
0x24308: ldr r3, [pc]; add r3, sl; ldr r0, [r3]
         bl 0x99cbc                    ; <-- helper
0x24314: r0=0; r1=caller_arg; bl 0x2b5c4
0x2431e: ctx_getter; check field; bne 0x2432e
0x2432e: bl 0x98364                    ; <-- ObjectA destructor (Round 20 일치!)
         bl 0x947f4                    ; state reset helper
         r0=3; bl 0x48bf8               ; mode-3 helper
         ; ... task_struct field 0/1 write (state reset)
0x24364: r0=r5; bl 0x818f0              ; <-- single-entity handler!
```

→ **cleanup + state reset path**. ObjectA destructor (0x98364) + state reset → BL 0x818f0 (single-entity handler). 즉 entity destruction → re-spawn pattern.

## 2. 0xac94 의 외부 array = ObjectB GOT slot

### 2.1 second LDR pcrel value 분포 (60 sites)

| value | count | 의미 |
|---|---|---|
| **0x18** | **17x** ⭐ | **GOT slot 0x18 (ObjectB ptr)** |
| 0xfffffec8~0xfffffef8 | 11x (1~2 each) | negative offsets (= JT-like data 또는 binary 영역 ref) |
| 0xac7a | 1x | task_struct[0xac7a] (entity record 의 다른 field) |
| 외 | 9x spread | 다양한 GOT/data offsets |

**0x18 dominant** = Round 23 의 8 GOT slots 중 ObjectB.

### 2.2 Address store 패턴 결합 분석

```asm
adds r4, r3, r4         ; r4 = task_ptr+0xac94
ldr r5, [pc, #N]         ; r5 = 0x18 (ObjectB GOT slot offset)
adds r5, r5, r7          ; r5 = 0x18 + r7 (where r7 saved sl?)
str r4, [r5]             ; *(sl + 0x18) = task_ptr+0xac94
```

→ **ObjectB GOT slot 의 ptr 을 (task_ptr+0xac94) 로 update**.

### 2.3 Round 21 의 ObjectB 정체 정정

Round 21 의 가설:
- ObjectB (slot 0x18) = **master GVM interface object** (240 readers / 240 funcs)

Round 31 정정:
- ObjectB slot 의 ptr 자체는 **dynamic** — 게임 코드가 entity 활성화 시 그 entity 의 substructure (task_struct[0xac94] 위치) 를 가리키게 update
- 즉 ObjectB = **현재 active entity 의 +0x1c position** = entity 의 sub-record/sub-pointer
- 240 readers 가 사용하는 ObjectB vtable methods 는 사실 **현재 active entity 의 method**

**더 큰 의미**: ObjectB 는 fixed object 가 아니라 **current-active-entity proxy** = 게임의 current 처리 entity 를 system-wide reference 가능하게 함.

이는 다음 라운드에서 검증:
- 17 address-store 사이트가 어떤 events / 어떤 entity 활성화 시 호출되는가
- ObjectB vtable methods 가 entity-별 다른 행동인지, 단일 vtable shared 인지

### 2.4 negative offsets (-0x108~-0x138)

11 사이트가 negative offset 사용 = **JT-like relative offsets**. binary 안의 코드 영역 references. 이 패턴이 무엇을 가리키는지는 다음 라운드 추적.

## 3. task_struct allocator 검증 — GVM-injected 확정

### 3.1 GOT slot 0x444 (task_ptr) writer 검색

```
=== GOT slot 0x444 ===
  total LDR pcrel sites: 7
  read sites (ldr r, [r+sl]): 7
  ⭐ WRITE sites (str r, [r+sl]): 0
```

**7 reads, 0 writes**. 즉 task_struct ptr 자체가 게임 binary 에서 한 번도 set 되지 않음.

### 3.2 GVM injection 확정

게임 binary 가 task_struct ptr 을 set 하지 않음 = **GVM firmware 가 외부에서 set**. 동일 패턴이 Round 23 의 다른 8 GOT slots:
- slot 0x18 (ObjectB), 0x16c, 0x29e, 0x128, 0x444, 0x44c (ObjectA), 0xd00, 0xd04, 0xd08, 0xd1c

**모두 0 direct writes** = GVM firmware 가 binary load 시점에 모든 system slot 을 inject.

### 3.3 context_getter 의 7 reads

7 read 사이트 모두 FUN_0004ad10 (context_getter) 안. 즉 게임의 다른 코드는 context_getter 를 통해서만 task_ptr 접근. context_getter 가 GVM firmware 와 게임 사이의 정확한 boundary.

## 4. 갱신된 task_struct 모델

### 4.1 substructure 통일 패턴 (+0x1c = instance ptr)

```
task_struct (44KB+, GVM firmware-maintained)
  ├─ +0x9bb4..0x9bd0  substructure A (32B):
  │    ├─ +0x00 (0x9bb4) bit flags
  │    └─ +0x1c (0x9bd0) ptr → 0x9bd0-Object instance (≥84B, GVM-injected)
  │                       └─ vtable[+0x08] = FUN_0007cd58 (60% dominant)
  │
  └─ +0xac78..0xac9d  substructure B (38B, entity state record):
       ├─ +0x00 (0xac78) entity base/type
       └─ +0x1c (0xac94) ⭐ ObjectB instance base
                         (게임 코드가 ObjectB GOT slot 0x18 에 register)
                         → vtable: 0/0x10/0x20/0x44/0x54/0x58/0x68/0x7c/0x80
```

→ **task_struct = multiple substructure 의 collection**. 각 substructure +0x1c 에 instance pointer.

### 4.2 ObjectB 정체 정정

| 측면 | Round 21 가설 | Round 31 정정 |
|---|---|---|
| ObjectB slot (0x18) | static master GVM interface | **dynamic — current-active-entity proxy** |
| 240 readers | master object 의 vtable methods | **현재 active entity 의 method calls** |
| ObjectB instance 위치 | 외부 fixed location | **task_struct[0xac94] = entity record 의 +0x1c** |

### 4.3 indirect entry hierarchy 갱신

```
GVM Firmware
  ├─ FUN_0006619c (paint/tick callback)
  ├─ FUN_00070f34 (key handler)
  ├─ FUN_0008b2e8 (sister entry, record 0x3c4)
  ├─ FUN_0008dcd8 (main entry, record 0x3c4)
  └─ FUN_000241dc (system event dispatcher, 74-entry JT)
       ├─ 0x24300 → FUN_00042758(arg) — 5 events most popular
       ├─ 0x242c0 → FUN_00040cec(arg) — 4 consecutive events
       ├─ 0x2427a → toggle + 0x3fbd4 + 0x48bf8(r0=5) — event -16
       ├─ 0x24264 → 0x2c6a4(r0=0xe) — event -10
       └─ cleanup path (0x24308~):
              ObjectA destructor (0x98364) → state reset → BL 0x818f0 (single-entity)
```

## 5. Round 32 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2CQ | **FUN_00042758 본문 분석** (0x24300 = 5 events 공통 helper, lifecycle 후보) | `disasm_subsystem_func.py 0x42758 <next_push>` |
| ⭐⭐ 2CR | 0x42758 의 caller chain (FUN_000241dc 외 다른 callers) | BL 0x42758 검색 |
| ⭐⭐ 2CS | ObjectB slot 0x18 의 17 address-store sites — 어떤 events/entry 에서 update? | inline disasm + caller mapping |
| ⭐⭐ 2CT | substructure A (0x9bb4) 의 +0x1c (= 0x9bd0) 도 같은 GOT[0x44c] (ObjectA) update 패턴인지 검증 | 도구 검색 |
| ⭐ 2CU | FUN_00040cec 본문 (0x242c0 = 4-events 공통 helper) | `disasm_subsystem_func.py 0x40cec` |
| ⭐ 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 92% miss) | 도구 추가 확장 |
| ⭐ 2CV | negative offsets (-0x108..-0x138) 의 11 사이트 정체 (JT-like data?) | binary 영역 분석 |

## 산출물

- (메모리 내 분석)
- 갱신된 PROGRESS.md / 메모리 / 신규 문서
