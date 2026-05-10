# Hero3 Ghidra — Round 27 / PM-17 (2026-05-10)
## `find_task_struct_field_readers.py` lenient 화 + system-wide 통계 대거 정정 + 0x9bd0-object vtable layout

> Round 26 의 도구 undercount 발견을 후속 — R0-propagation 추적을 추가해서 lenient 매칭으로 system-wide 통계 정정. 결과는 다수 field 의 hits 가 5~10배 증가 (가장 큰 변화: 0x9e28 = 16 → **101 sites, 83 funcs**, 0xac78 = 5 → **43 sites**).

## TL;DR (3줄)

1. ⭐⭐⭐ **도구 lenient 화 후 통계 대거 정정** — 도구가 `bl 0x4ad10` 후 R0 가 다른 register 로 saved (`adds rZ, r0, #0`, `mov rZ, r0`) 되어도 추적. 결과: 0x9e28 = 16→**101 sites (83 unique funcs)**, 0xac78 = 5→**43 sites**, 0x9c71 = 0→**97 sites**, 0x9bd0 = 19→**25 sites (21 unique funcs)**.
2. ⭐⭐⭐ **0x9bd0-object vtable layout 매핑** — 42 raw pcrel 사이트 분석 결과 **vtable[+0x08] = dominant** (30/42 = 71%). 부수 methods: +0x39, +0x54, +0x5a, +0x8c, +0x94, +0xb4, +0xb9. ObjectA vtable (0/0xc/0x10/0x1c/0x20/0x2c/0x44/0x54/0x58/0x68/0x7c/0x80) 와 다른 layout = **별개 객체 타입 확정**.
3. ⭐⭐⭐ **FUN_000818f0 = main entity update loop 강력 뒷받침** — Round 27 lenient 통계가 0xac78 dominant reader (34/43 = 79%) + 0x9c71 (13x) + 0x9e28 (5x) + 0xa220 (0x9c70 등) 다중 dominant. PM-3 의 "5.4KB, 287 BLs, 212x context_getter" 가설 강화. PIC standard prologue + 0x6c byte stack frame.

부수 발견:
- ⭐⭐ **FUN_0008d87c 신규 핵심 함수** — 0x9c71 (9x) + 0x9e28 (4x) 등 dominant. NPC/entity dispatcher 후보 (record 0x3c4 의 sister entry, PROGRESS.md 의 game update flow 와 일치).
- ⭐ **0x9c70 cluster 일부 미캐치** — wide-scan 112 vs lenient 9 = 여전히 92% miss. 추가 패턴 (stack-load 후 reuse) 필요. 단, 0x9c71/84/85 는 80%+ caught.
- ⭐ **0xac78 readers 정정** — Round 24 의 "FUN_000241dc 전용" 가설 폐기. **FUN_000818f0 가 34x dominant**, FUN_000241dc 는 5x.

## 1. 도구 lenient 화 — 패턴 확장

### 1.1 기존 (narrow) vs 신규 (lenient)

```python
# 기존 (Round 24~26): R0 직접 사용만 검사
bl 0x4ad10                  # r0 = task_ptr
ldr Rx, [pc, #imm]           # Rx = field_offset
adds Ry, R0, Rx              # <-- 여기서 R0 가 직접 매칭되어야

# 신규 (Round 27): R0 propagation 추적
bl 0x4ad10                   # r0 = task_ptr
adds rZ, r0, #0              # <-- 신규: r0 saved to rZ (r0_equiv 추가)
ldr Rx, [pc, #imm]           # Rx = field_offset
adds Ry, rZ, Rx              # <-- rZ 도 r0_equiv 로 매칭 OK
```

### 1.2 R0-propagation 추적 알고리즘

```python
r0_equiv = {"r0"}  # initial: r0 holds task_ptr

for each instr in 16-window after bl 0x4ad10:
    # Stop on branch
    if mnem.startswith("b"): break

    # Detect r0 save:
    #   adds rZ, r0, #0
    #   mov rZ, r0
    #   movs rZ, r0
    if save pattern: r0_equiv.add(rZ)

    # Detect field LDR:
    if ldr Rx, [pc, #imm] and *imm in fields:
        ldr_target = (Rx, lit_value)

    # Detect field add:
    if adds Ry, <r0_equiv>, ldr_target.Rx:
        record hit(field_offset)
```

핵심 변경:
- 16-instr lookahead (기존 12)
- branch instruction 만나면 break (false hit 방지)
- 다중 register propagation (rZ, rZ', ... 모두 r0_equiv)
- `r0_via` 메타데이터 (direct vs saved:rZ) 기록

### 1.3 Before/After 통계

| field | 이전 (auto narrow) | Round 27 lenient | 변화 |
|---|---|---|---|
| 0x29e | 3 | 4 | +33% |
| 0x9bb4 | 68 | 69 (20 funcs ↑) | unique funcs +5 |
| 0x9bb6 | 5 | 7 | +40% |
| 0x9bc8 | 0 | 4 | NEW |
| 0x9bd0 | 19 | **25 (21 funcs)** | +50% sites, +50% funcs |
| 0x9c70 | 0 | 9 | NEW (but wide-scan 112) |
| 0x9c71 | 0 | **97 (37 funcs)** | NEW (wide-scan 115, 84% caught) |
| 0x9c84 | 0 | **34 (18 funcs)** | NEW |
| 0x9c85 | 0 | **31 (11 funcs)** | NEW |
| 0x9cb8 | 11 | 8 (slight drop?) | -27% (re-classified) |
| 0x9cbc | 17 | 28 | +65% |
| 0x9cc0 | 9 | 11 | +22% |
| 0x9cfe | 3 | 5 | +67% |
| **0x9e28** | 16 | **101 (83 funcs)** | ⭐⭐⭐ +500% |
| 0x9e78 | 5 | 11 | +120% |
| 0xa220 | 1 | 12 | +1100% |
| 0xa244 | 1 | 5 | +400% |
| 0xa245 | 0 | 4 | NEW |
| 0xa254 | 1 | 6 | +500% |
| **0xac78** | 5 | **43 (4 funcs)** | ⭐⭐⭐ +760% |

가장 큰 정정: **0x9e28 (sound state #1) 가 system-wide 가장 활발한 task_struct field**.

## 2. 0x9bd0-object vtable layout 매핑

### 2.1 raw pcrel 42 sites + forward-window method offset 분포

| offset | hits | 비율 |
|---|---|---|
| **+0x08** | 30x | **71% dominant** |
| +0xb4 | 3x | 7% |
| +0x39 | 2x | 5% |
| +0x09 | 1x | (= +0x08 변형) |
| +0x27, +0x28, +0x30, +0x31 | 각 1x | small offsets |
| +0x54, +0x5a | 각 1x | (ObjectA vtable 와 겹침) |
| +0x8c, +0x94 | 각 1x | medium offsets |
| +0xb4, +0xb9 | 각 1x | high offsets |

### 2.2 ObjectA vtable 와 비교

| Object | vtable methods (offsets) |
|---|---|
| ObjectA (slot 0x44c) | 0/0xc/0x10/0x1c/0x20/0x2c/0x44/0x54/0x58/0x68/0x7c/0x80 |
| ObjectB (slot 0x18) | 0/0x10/0x20/0x44/0x54/0x58/0x68/0x7c/0x80 |
| **0x9bd0-object** ⭐ | **0x08** (dominant) + 0x39/0x54/0x5a/0x8c/0x94/0xb4/0xb9 |

**0x9bd0-object 의 vtable layout 이 ObjectA/B 와 다름**:
- ObjectA/B: 0x10/0x20/0x44 cluster
- 0x9bd0-object: **0x08 dominant + spread offsets** (0x39/0x54/0x5a/0x8c/0x94/0xb4/0xb9)

→ **0x9bd0-object = 별개 객체 타입 확정**.

ObjectA = audio/asset resource manager (POSIX errors, acquire-use-release).  
ObjectB = master GVM interface object.  
**0x9bd0-object = ???** (다음 라운드에 vtable[+0x08] sub-call 의 정체 추적 필요).

### 2.3 Reader 분포 (21 unique funcs)

| reader | count | 노트 |
|---|---|---|
| FUN_0009b252 | 3x | (= FUN_0009a008 sub-label) |
| FUN_0009ada4 | 2x | FUN_0009a008 의 또 다른 sub-label 후보 |
| FUN_000487ec | 2x | FUN_000482c8 sibling 의 sub-label 후보 |
| FUN_000052b0 | 1x | early-binary func |
| FUN_0000a970 | 1x | early-binary func |
| FUN_0001e134 | 1x | task ptr indirect chain |
| FUN_00040fb0 | 1x | (+0x8c offset access) |
| 외 14 funcs | 각 1x | wide-spread usage |

→ **0x9bd0-object 가 system-wide 핵심 객체** (game state 의 21+ 함수가 access).

## 3. FUN_000818f0 = main entity update loop 강력 뒷받침

### 3.1 Round 27 통계의 dominant reader 분포

| field | FUN_000818f0 hits | 전체 hits |
|---|---|---|
| 0xac78 | **34x** | 43 (79% dominant) |
| 0x9c71 | 13x | 97 (13% dominant) |
| 0x9e28 | 5x | 101 (5% dominant) |
| 0x29e (?) | 1x | - |

### 3.2 Prologue 분석

```asm
0x818f0: push {r4-r7, lr}            ; PIC standard prologue
0x818f2: mov r7, sl
0x818f4: mov r6, r8
0x818f6: push {r6, r7}
0x818f8: mov r7, sp                  ; frame pointer
0x818fa: sub sp, #0x6c               ; large stack frame (108 byte)
0x818fc: ldr r1, [pc, #0x3b0]        ; GOT base setup
0x818fe: mov sl, r1
0x81900: add sl, pc
0x81902: subs r3, r7, #4
0x81904: str r0, [r3]                ; caller arg saved
0x81906: adds r2, r7, #0
0x81908: subs r2, #8
0x8190a: movs r3, #0
0x8190c: str r3, [r2]                ; local var = 0
0x8190e: adds r4, r7, #0
0x81910: subs r4, #9
0x81912: bl 0x4ad10                   ; <-- first context_getter (of 212+)
```

특징:
- **0x6c byte stack frame** = 큰 local state (= frame buffer/iteration state)
- frame pointer setup (r7 = sp)
- PIC standard prologue
- 첫 명령부터 context_getter 호출 = task_struct 핵심 처리

### 3.3 PM-3 가설 vs Round 27 검증

| 측면 | PM-3 가설 | Round 27 검증 |
|---|---|---|
| size | 5.4KB | (변동 없음) |
| BL count | 287 | (변동 없음) |
| context_getter | 212x | (변동 없음) |
| 정체 | per-entity update loop | **0xac78/0x9c71/0x9e28 dominant reader** = 강력 뒷받침 |
| 핵심 field | 0x18 (ObjectB) | **0xac78 (34x 단일 함수)** + 0x9e28 (sound state #1) + 0x9c71 (byte field) |

**FUN_000818f0 가 entity update loop 라면 0xac78 = entity-per 데이터 (예: entity flag/state)**, 0x9c71 = entity-per byte field, 0x9e28 = sound trigger.

## 4. 신규 핵심 함수 — FUN_0008d87c

Round 27 통계에서 새로 부각된 함수:

| field | FUN_0008d87c hits |
|---|---|
| 0x9c71 | **9x** (37 unique funcs 중 2위) |
| 0x9e28 | 4x (83 funcs 중 4위) |
| 외 | (분석 필요) |

PROGRESS.md 의 game update flow:
```
FUN_0008b2e8 (sister entry, record 0x3c4)
   inline @ 0x8c19c → FUN_0008d5e4 (jt 0xabaa8)
FUN_0008dcd8 (main entry, record 0x3c4)
   inline @ 0x8eb80 → FUN_0008ff18 (jt 0xabc68)
```

**FUN_0008d87c 는 0x8b2e8 (sister entry) 와 0x8dcd8 (main entry) 사이** = NPC/entity dispatcher 의 한 inline 영역. record 0x3c4 stride 처리 함수의 후보.

## 5. 0x9c70 cluster 부분 미캐치

| field | wide-scan raw | lenient verified | 캐치율 |
|---|---|---|---|
| 0x9c70 | 112 | 9 | **8%** (여전히 92% miss) |
| 0x9c71 | 115 | 97 | 84% |
| 0x9c84 | 39 | 34 | 87% |
| 0x9c85 | 37 | 31 | 84% |

0x9c70 의 압도적 미캐치: 이 field 의 사용 패턴이 다른 cluster member 와 다름. 추정:
- **stack-load 후 reuse** 패턴 (e.g. `subs r3, r7, #4; ldr r3, [r3]; ldr r1, [pc, #N]; adds r2, r3, r1`)
- 직접 context_getter 호출 없이 stack 에서 task_ptr 가져온 케이스
- Round 28 에서 추가 lenient 화 가능 (stack-load tracking 필요)

## 6. 갱신된 게임 시스템 모델

### 6.1 task_struct field 통계 (Round 27)

```
task_struct (44KB+, 핵심 fields)
  ├─ 0x29e   small flag (4 sites, 4 funcs)
  ├─ 0x9afc~0x9b1c byte field cluster #1 (1+ sites, FUN_00041c14)
  ├─ 0x9bb4~0x9bd0 substructure A (32B):
  │    ├─ +0x00 (0x9bb4) bit flags (69 sites, 20 funcs, FUN_0009b252 39x)
  │    ├─ +0x02 (0x9bb6) byte field (7 sites)
  │    ├─ +0x03 (0x9bb7) byte field (1)
  │    ├─ +0x14 (0x9bc8) field (4)
  │    └─ +0x1c (0x9bd0) ptr-to-object (25 sites, 21 unique funcs)  ⭐ system-wide
  ├─ 0x9c70  byte field (9+ caught, 112 raw — under-caught)
  ├─ 0x9c71  byte field ⭐ (97 sites, 37 funcs, top: FUN_000818f0 13x)
  ├─ 0x9c84  byte field (34 sites, 18 funcs, top: FUN_0003be34 5x)
  ├─ 0x9c85  byte field (31 sites, 11 funcs, top: FUN_0003be34 6x)
  ├─ 0x9cb8/9cbc/9cc0/9cfe  record array slots (8/28/11/5)
  ├─ 0x9e28  ⭐⭐ sound state #1 (101 sites, 83 unique funcs — system-wide)
  ├─ 0x9e78  per-context flag (11 sites, 7 funcs)
  ├─ 0xa220/a244/a245/a254  sound state cluster (12/5/4/6)
  └─ 0xac78  ⭐⭐ FUN_000818f0 dominant (34/43, 79%)
```

### 6.2 Object hierarchy (Round 27)

```
GVM Firmware (외부 주입)
  └─ 9 GOT slots:
       ├─ slot 0x18  → ObjectB ptr (240 readers, master GVM interface)
       ├─ slot 0x444 → task_ptr (context_getter)
       ├─ slot 0x44c → ObjectA ptr (resource manager)
       └─ ...

task_struct (huge struct via *(slot 0x444))
  ├─ +0x9bb4..0x9bd0 substructure A
  │    └─ +0x1c (0x9bd0) → ptr-to-object [신규 객체 type, vtable[+0x08] dominant]
  └─ 외 다수 fields

Object types:
  ObjectA  : vtable 0/0xc/0x10/0x1c/0x20/0x2c/0x44/0x54/0x58/0x68/0x7c/0x80
  ObjectB  : vtable 0/0x10/0x20/0x44/0x54/0x58/0x68/0x7c/0x80
  0x9bd0-Object ⭐ : vtable +0x08 dominant + 0x39/0x54/0x5a/0x8c/0x94/0xb4/0xb9
```

## 7. Round 28 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2BT | **FUN_000818f0 본문 분석** (5.4KB, entity update loop 후보) | `disasm_subsystem_func.py 0x818f0 <next_push>` |
| ⭐⭐ 2BU | 0x9bd0-Object vtable[+0x08] sub-call 정체 (30x dominant method) | indirect call 추적 |
| ⭐⭐ 2BV | FUN_0008d87c 본문 (신규 핵심 함수) | `disasm_subsystem_func.py 0x8d87c <next_push>` |
| ⭐⭐ 2BW | **0x9c70 stack-load 패턴 추가 lenient 화** | 도구 추가 확장 |
| ⭐ 2BX | 0xac78 의 FUN_000818f0 34x reader 패턴 (entity slot offset) | inline disasm |
| ⭐ 2BY | 0x9e28 의 83 unique funcs distribution + sound trigger graph | reader chain 분석 |

## 산출물

- `tools/recon/find_task_struct_field_readers.py` — lenient 패턴 추가 (R0 propagation tracking, 16-instr window, branch break)
- `work/h3/task_struct_field_readers.json` — 정정된 system-wide 통계 (26 fields)
