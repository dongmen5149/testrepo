# Hero3 Ghidra — Round 30 / PM-20 (2026-05-10)
## FUN_000241dc 74-entry JT 디코드 + 0xac94 정체 정정 + 0x9bd0 instance allocator 추적

> Round 29 의 5번째 indirect entry (FUN_000241dc) 의 74-entry JT 를 GOT base 정확히 계산해서 디코드. 결과: **74 entries → 단 7 destinations**, 62/74 (84%) 가 epilogue (no-op). 또 0xac94 정체가 entity metadata 가 아니라 **pointer field** 임을 본문 분석으로 정정.

## TL;DR (3줄)

1. ⭐⭐⭐ **FUN_000241dc 74-entry JT 디코드 성공** — GOT base = 0x000b2c40 (Round 23 추정 일치), JT base = 0x000a6710. **74 entries → 단 7 distinct destinations**, **62 cases (84%) 가 epilogue 0x24246** (no-op, default return). 진짜 처리되는 events = **12개** (caller_arg = -16 / -10 / -5..-1 / 35 / 42 / 48 / 49 / 51 / 53 / 55 / 57). sparse event handler.
2. ⭐⭐⭐ **0xac94 정체 정정 — pointer field, NOT entity metadata** — 4 readers 본문 분석. FUN_00030018/0x8beba/0x8e89e (모두 14/14/9x): **address store 패턴** (`str r4, [r5]` where r4 = `task_ptr+0xac94` 의 address) = task_struct[0xac94] 의 위치를 외부 array 에 등록. FUN_000818f0 (20x): **read 패턴** (`ldr r3, [r3]; cmp r3, #0; bne` = pointer + null check) = pointer field 처리. Round 28~29 의 "entity metadata" 가설 정정.
3. ⭐⭐ **0x9bd0 의 21 LDR 사이트 모두 read 패턴** (vtable+8 추출 + 외부 store), 진짜 writer 미발견. → **0x9bd0 instance ptr 도 GVM firmware 외부 주입 가능성** (8 GOT slots 와 같은 패턴).

부수 발견:
- ⭐⭐ **FUN_000241dc 의 12 진짜 events** dispatcher destinations: 0x2427a / 0x24264 / 0x242c0 (4 인접 events) / 0x242c8 / 0x242d0 (3 events) / 0x24300 (5 events). **0x24300 이 가장 popular handler** (5 events 공통 처리).
- ⭐ FUN_000241dc 의 caller_arg=-10 → 0x24264 처리: `bl 0x4ad10; adds r0, #0xf2; ldrsh r3, [r0]; cmp r3, #0; ble 0x24246; movs r0, #0xe; bl 0x2c6a4` = task_struct[0xf2] short read + helper call.
- ⭐ FUN_000241dc 의 BL 0x818f0 (single-entity handler) 호출 = caller_arg=49/51/57 중 하나의 case 안에서 발생 (0x24300 → ... → 0x24364 fall-through).

## 1. FUN_000241dc 74-entry JT 디코드

### 1.1 GOT base + JT base 정확 계산

Prologue 분석으로 PIC GOT base 추출:
```asm
0x241e2: ldr r0, [pc, #0x318]    ; PC = (0x241e2+4)&~3 = 0x241e4
                                  ; lit_addr = 0x241e4 + 0x318 = 0x244fc
                                  ; lit value = 0x0008ea54
0x241e8: add sl, pc               ; sl = 0x8ea54 + (0x241e8+4) = 0x000b2c40
```

→ **GOT base = 0x000b2c40** (Round 23 의 추정과 일치).

Dispatch 위치:
```asm
0x24256: ldr r3, [pc, #0x2bc]    ; PC = (0x24256+4)&~3 = 0x24258
                                  ; lit_addr = 0x24258 + 0x2bc = 0x24514
                                  ; lit value = -50480 (signed)
0x24258: mov r0, sl               ; r0 = GOT base = 0x000b2c40
0x2425a: adds r2, r0, r3          ; r2 = JT base = 0x000b2c40 - 50480 = 0x000a6710
```

→ **JT base = 0x000a6710** (binary 안의 JT 영역).

### 1.2 74 entries 디코드 결과

각 entry = 4 byte signed offset (from JT base). 74 cases (caller_arg = idx - 0x10):

| caller_arg | dest | 의미 |
|---|---|---|
| -16 | 0x2427a | unique handler #1 |
| -15..-12 | 0x24246 | epilogue (no-op) |
| -11 | 0x24246 | epilogue |
| -10 | 0x24264 | task[+0xf2] short → 0x2c6a4 helper |
| -9..-6 | 0x24246 | epilogue |
| -5 | 0x242d0 | shared handler #1 |
| -4..-1 | 0x242c0 | shared handler #2 (4 events 공통) |
| 0..34 | 0x24246 | epilogue (35 cases!) |
| 35 | 0x24300 | shared handler #3 |
| 36..41 | 0x24246 | epilogue |
| 42 | 0x242c8 | unique handler #2 |
| 43..47 | 0x24246 | epilogue |
| 48..49 | 0x24300 | shared handler #3 |
| 50 | 0x24246 | epilogue |
| 51 | 0x24300 | shared handler #3 |
| 52 | 0x24246 | epilogue |
| 53 | 0x242d0 | shared handler #1 |
| 54 | 0x24246 | epilogue |
| 55 | 0x242d0 | shared handler #1 |
| 56 | 0x24246 | epilogue |
| 57 | 0x24300 | shared handler #3 |

**Summary**: **74 → 7 distinct destinations, 12 진짜 events**, 62 epilogue (84%).

### 1.3 7 destinations + 호출 분포

| dest | event count | hits |
|---|---|---|
| **0x24246** (epilogue) | 62 | default no-op |
| **0x24300** | 5 | events 35/48/49/51/57 |
| **0x242c0** | 4 | events -4..-1 (consecutive) |
| **0x242d0** | 3 | events -5/53/55 |
| 0x24264 | 1 | event -10 |
| 0x242c8 | 1 | event 42 |
| 0x2427a | 1 | event -16 |

→ **0x24300 = most popular handler** (5 unrelated events → 같은 처리).

### 1.4 Sparse dispatcher 의 의미

74-entry JT 가 sparse 한 이유:
- **caller arg + 0x10 shift** = signed range [-0x10..0x39] 를 0..0x49 로 매핑
- 84% events 가 no-op = GVM firmware 가 매우 다양한 event code 를 보내지만 게임은 12개에만 반응
- consecutive events (-5..-1, -4..-1) 가 같은 handler 공유 = signed near-zero events 의 **default behavior**
- 35/48/49/51/57 (spread) 가 같은 handler = unrelated event 들이 같은 응답 (예: focus/idle/blur 같은 lifecycle events)

→ **FUN_000241dc = GVM firmware system event dispatcher** (lifecycle/state events, NOT game logic).

## 2. 0xac94 정체 정정 — pointer field

### 2.1 4 readers 본문 분석

| reader | hits | 패턴 |
|---|---|---|
| FUN_00030018 | 14x | **address store**: `str r4, [r5]` where r4 = task_ptr+0xac94 의 address |
| FUN_0008beba | 14x | 동일 address store 패턴 |
| FUN_0008e89e | 9x | 동일 address store 패턴 |
| FUN_000818f0 | 20x | **read + null check**: `ldr r3, [r3]; cmp r3, #0; bne` |

### 2.2 Address store 패턴 (FUN_00030018 등 3 readers)

```asm
adds r3, r0, #0          ; r3 = task_ptr (saved)
ldr r4, [pc, #N]         ; r4 = 0xac94 (field offset)
adds r4, r3, r4          ; r4 = task_ptr + 0xac94 (= 자체 address)
ldr r5, [pc, #N]         ; r5 = ANOTHER GOT slot offset
adds r5, r5, r7          ; r5 = some external array + r7 (entity index?)
str r4, [r5]             ; *(external_array[r7]) = (task_ptr + 0xac94)
```

→ **task_struct[0xac94] 의 address 자체를 외부 array 에 저장**. 즉 0xac94 가 **substructure base** 역할 (외부 코드가 substructure 를 참조하기 위한 pointer).

### 2.3 Read 패턴 (FUN_000818f0)

```asm
adds r3, r0, #0
ldr r0, [pc, #N]         ; r0 = 0xac94
adds r3, r3, r0          ; r3 = task_ptr + 0xac94
ldr r3, [r3]             ; r3 = *(task_ptr + 0xac94) = pointer/word
cmp r3, #0
bne 0x81e2a              ; null check → branch on non-null
```

→ **pointer field 의 null check + 분기**. 0xac94 자체가 pointer field (또는 first word of substructure 가 sub-pointer).

### 2.4 Round 28~29 가설 정정

| 측면 | Round 28~29 가설 | Round 30 본문 정정 |
|---|---|---|
| 정체 | entity metadata (type code 또는 status flag) | **pointer field** (또는 substructure base address) |
| 사용 | 4 readers 가 검사하는 main key | 3 readers 가 address 를 외부 array 에 등록, 1 reader 가 pointer null check |
| 38B record 안 | +0x1c (entity 식별자) | +0x1c = **substructure 안의 sub-pointer** 또는 substructure 가 외부 array 의 한 element 임을 확정 |

### 2.5 entity state record 38B 모델 갱신

```
task_struct[0xac78] = 38B entity state record  
                       (substructure A — like the 0x9bb4 substructure but for entity state)
  +0x00 (0xac78) base/type field (43 sites, system-wide-ish)
  +0x01 (0xac79) byte (FUN_818f0 only)
  ...
  +0x1c (0xac94) ⭐ pointer/substructure base (57 sites, 4 funcs)
                  - 3 funcs 가 address 를 외부 array 에 register
                  - 1 func 가 pointer 로 사용 (null check + deref)
  +0x20 (0xac98) word (22, FUN_818f0 only)
  +0x25 (0xac9d) byte (6, FUN_818f0 only)
```

이는 **substructure A (0x9bb4~0x9bd0) 와 유사 패턴**:
- 0x9bb4 substructure: +0 bit flags + +0x1c ptr-to-Object
- 0xac78 substructure: +0 entity field + **+0x1c pointer** (sub-substructure 또는 external entry)

→ **task_struct 가 multiple substructure 들의 array** 일 가능성 (각 substructure ≥ 28~38 byte).

## 3. 0x9bd0 instance allocator 추적

### 3.1 21 LDR pcrel 사이트 모두 read 패턴

```asm
ldr r0, [pc, #N]         ; r0 = 0x9bd0
adds r3, r3, r0          ; r3 = task_ptr + 0x9bd0
ldr r3, [r3]             ; r3 = *(task_ptr + 0x9bd0) = instance ptr (NOT NULL)
ldr r3, [r3]             ; r3 = *instance = vtable ptr
adds r3, #8              ; r3 = vtable + 8
str r3, [r4]             ; *r4 = vtable + 8 (saved to stack/external)
```

모든 21 사이트가 동일 — vtable+8 method ptr 추출 + 외부 저장. 진짜 instance write (allocator) 사이트 미발견.

### 3.2 추정 — GVM firmware 외부 주입

PIC 환경의 진짜 writer 패턴 부재 = Round 23 의 8 GOT slots 와 같은 **GVM firmware 동적 주입**. 즉:
- task_struct[0x9bd0] 의 instance pointer 는 **외부에서 set**
- 게임 코드는 read 만 (vtable+8 method invocation)

이 가설은 다음 확인 필요:
- task_struct allocate 위치 추적 (전체 task_struct 의 lifetime)
- 또는 GVM firmware 의 dynamic injection 패턴 (정적 분석 한계)

## 4. 갱신된 모델

### 4.1 task_struct substructure pattern

```
task_struct (44KB+, GVM-injected)
  ├─ +0x9bb4..0x9bd0  substructure A (32B):
  │    ├─ +0x00 (0x9bb4) bit flags (FUN_0007d31c bit-scan)
  │    └─ +0x1c (0x9bd0) ptr-to-0x9bd0-Object (≥84B, heap-alloc)
  │         ⚠ instance allocator 미식별 → GVM firmware 주입 추정
  │
  └─ +0xac78..0xac9d  substructure B (38B, entity state record):
       ├─ +0x00 (0xac78) entity base/type (system-wide-ish)
       ├─ +0x1c (0xac94) ⭐ pointer field (3 funcs register address, 1 reads)
       │    → 외부 array 에 substructure 의 self-address 등록
       └─ +0x20 (0xac98) word (FUN_818f0 only)

→ task_struct = multiple substructure 의 collection (~32~38B blocks)
```

### 4.2 indirect entry hierarchy

```
GVM Firmware
  ├─ FUN_0006619c (paint/tick callback)
  ├─ FUN_00070f34 (key handler)
  ├─ FUN_0008b2e8 (sister entry, record 0x3c4)
  ├─ FUN_0008dcd8 (main entry, record 0x3c4)
  └─ FUN_000241dc (system event dispatcher, 74-entry JT)
       ├─ 62 events (84%) → no-op
       └─ 12 events → 7 handlers (대부분 small handlers, BL 0x818f0 single-entity 포함)
```

## 5. Round 31 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2CM | FUN_000241dc 의 7 destination handlers 본문 분석 (0x24264 / 0x2427a / 0x242c0 / 0x242c8 / 0x242d0 / 0x24300) | inline disasm |
| ⭐⭐ 2CN | 0xac94 의 외부 array (3 funcs 가 register 하는 destination) 정체 | str dest 의 GOT slot 추적 |
| ⭐⭐ 2CO | task_struct allocator 추적 (instance pointer 의 진짜 set 위치) | 더 정교한 wide-scan |
| ⭐ 2CP | 0x24300 (FUN_000241dc 의 5 events 공통 handler) 가 어떤 event 응답인지 | 본문 + cmp 패턴 |
| ⭐ 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 92% miss) | 도구 추가 확장 |

## 산출물

- (메모리 내 분석, JT decode 스크립트는 inline)
- 갱신된 PROGRESS.md / 메모리 / 신규 문서
