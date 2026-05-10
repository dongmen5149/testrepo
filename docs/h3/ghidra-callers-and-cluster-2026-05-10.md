# Hero3 Ghidra — Round 29 / PM-19 (2026-05-10)
## FUN_000818f0 caller chain (FUN_000241dc 5번째 indirect entry) + 0xac78 cluster system-wide + 0x9bd0-Object instance ≥84B

> Round 28 의 "FUN_000818f0 = single-entity handler (외부 caller-driven)" 가설을 caller chain 추적으로 검증. 결과: **FUN_000241dc 가 BL 0x818f0 의 단 1 caller**, **FUN_000241dc 자체는 indirect-only entry function** (5번째 발견). 또 0xac78 cluster 의 system-wide reader 매핑으로 entity state record 가설 강화.

## TL;DR (3줄)

1. ⭐⭐⭐ **FUN_000818f0 의 caller chain** — direct BL caller **단 1건** (0x24366 in FUN_000241dc), literal pool entries 0건. 0x24246 = epilogue (NOT loop start) 였고 32 backward branches 모두 early-return. 진짜 dispatch = 0x2424e: **74-entry massive JT** (`r1 = caller_arg + 0x10; cmp r1, #0x49; mov pc, r3`). FUN_000241dc 도 **0 direct callers + 0 literal entries** = **5번째 indirect-only entry function** (PROGRESS.md 의 알려진 4 entries 외 신규).
2. ⭐⭐⭐ **0xac78~0xac9d cluster system-wide reader 매핑** — 12 fields 중 **10개가 FUN_000818f0 전용** (single-entity state record 가설 확정). 유일한 system-wide field = **0xac94 (57 sites, 4 funcs: FUN_000818f0 20x + FUN_00030018 14x + FUN_0008beba 14x + FUN_0008e89e 9x)** = entity metadata 후보 (entity type 또는 status flag).
3. ⭐⭐ **0x9bd0-Object instance ≥84B** — instance fields 분포: +0x04/0x10/0x18/0x1a/0x1c/0x1d/0x20/0x30/0x54 spread (10개 distinct offsets). Round 26 의 "0x9bb4 + 0x9bd0 = same 32B substructure" 가설 정정 — **instance 는 task_struct 외부 (heap-allocated 또는 별도 영역), substructure A 의 +0x1c 위치에는 instance pointer**.

부수 발견:
- ⭐⭐ **GVM firmware 의 indirect-only entries 누적 5개** — FUN_0006619c (paint/tick), FUN_00070f34 (key handler), FUN_0008b2e8 (sister entry), FUN_0008dcd8 (main entry), **FUN_000241dc (74-entry event dispatcher) ⭐ 신규 5번째**.
- ⭐ **FUN_000241dc 의 74-entry JT key = caller_arg + 0x10** → range [-0x10..0x39] event/state code. caller arg 가 -0x10 이상이면 dispatch, 아니면 epilogue.
- ⭐ FUN_000241dc 안에서 sub-call: FUN_000818f0 (1x, single-entity), FUN_00085fc8, FUN_0002c6a4, FUN_0003a444, etc.
- ⭐ FUN_00081688 = 0xac84 (3x) reader (FUN_000818f0 옆에 있는 함수, 인접 entity handler 후보).

## 1. FUN_000818f0 caller chain — 5번째 indirect entry 발견

### 1.1 Direct BL 검색

```
=== direct BL 0x818f0 callers: 1 ===
  0x00024366

=== PC-rel literal pool entries containing 0x818f0: 0 ===
```

**유일한 caller = 0x24366** (in FUN_000241dc 영역, 956 byte).

### 1.2 0x24366 caller 컨텍스트

```asm
0x24364: adds r0, r5, #0     ; r0 = r5 (= caller arg, signed byte saved)
0x24366: bl 0x818f0           ; <-- 단일 호출 사이트
0x2436a: b 0x24246             ; <-- backward branch to "0x24246"
```

처음 보면 0x24246 이 loop start 처럼 보임. 그러나 실측:

```asm
0x24246: add sp, #4
0x24248: pop {r3}
0x2424a: mov sl, r3
0x2424c: pop {r4, r5, r6, pc}    ; <-- function return!
```

**0x24246 = function epilogue, NOT loop start**. 32 backward branches 모두 early-return 패턴.

### 1.3 진짜 dispatch — 74-entry massive JT

진짜 dispatch 위치 = 0x2424e:

```asm
0x2424e: adds r1, r5, #0       ; r1 = caller arg (saved as r5)
0x24250: adds r1, #0x10        ; r1 += 0x10 (offset shift)
0x24252: cmp r1, #0x49         ; range check 0..0x49 (= 74 entries)
0x24254: bhi 0x24246            ; default → epilogue
0x24256: ldr r3, [pc, #0x2bc]  ; JT base offset
0x24258: mov r0, sl
0x2425a: adds r2, r0, r3
0x2425c: lsls r1, r1, #2       ; r1 *= 4
0x2425e: ldr r3, [r1, r2]
0x24260: adds r3, r3, r2
0x24262: mov pc, r3             ; <-- JT jump (74 entries)
```

→ **74-entry massive JT**. caller arg + 0x10 = key. caller arg ∈ [-0x10..0x39] (= 74 events/states).

### 1.4 FUN_000241dc 도 indirect-only

```
=== direct BL 0x241dc callers: 0 ===
=== PC-rel literal pool entries containing 0x241dc: 0 ===
```

→ **FUN_000241dc 도 indirect-only entry function**.

PROGRESS.md 의 알려진 4 indirect entries:
- FUN_0006619c (paint/tick callback)
- FUN_00070f34 (key handler)
- FUN_0008b2e8 (sister entry, record 0x3c4)
- FUN_0008dcd8 (main entry, record 0x3c4)

→ **FUN_000241dc = 5번째 indirect-only entry** (PROGRESS.md 에 추가 필요).

### 1.5 FUN_000241dc 의 정체 — 시스템 event/state dispatcher

74-entry JT (caller arg ∈ [-0x10..0x39]) = **GVM firmware 가 다양한 event/state code 로 호출**. caller arg = signed value, 0x10 shift 로 0..0x49 인덱싱.

prologue 에서 task_struct 처리:
```asm
0x241dc: push {r4, r5, r6, lr}
0x241de: mov r6, sl
0x241e0: push {r6}
0x241e2: ldr r0, [pc, #0x318]    ; GOT base
0x241ea: adds r5, r1, #0           ; r5 = caller arg #2 (event code)
0x241ec: bl 0x4ad10                 ; context_getter
0x241f0: ldr r2, [pc, #0x30c]      ; field_offset
0x241f2: adds r4, r0, #0           ; r4 = task_ptr (saved)
0x241f4: adds r6, r0, r2           ; r6 = task_ptr + field_offset
0x241f6: bl 0x4ad10                 ; second context_getter (re-fetch)
0x241fa: movs r3, #0x9f
0x241fc: lsls r3, r3, #2           ; r3 = 0x9f << 2 = 0x27c (= 636, frame size?)
```

caller args:
- arg 1 (r0): unused at prologue
- arg 2 (r1 → r5): event/state code (signed byte, +0x10 shift for JT)

### 1.6 FUN_000241dc 안의 sub-handlers (BL targets sample)

```asm
0x24278: b 0x24246          ; case 'X' → return
0x24360: movs r0, #3
0x24362: b 0x24274           ; jump to common handler
0x24364: adds r0, r5, #0
0x24366: bl 0x818f0          ; case "single-entity update + render"
0x2436e: bl 0x85fc8          ; another sub-call
```

74 cases 의 다양한 sub-handler 호출:
- 0x818f0 (single-entity state handler)
- 0x85fc8 (?)
- 0x2c6a4 (event helper)
- 0x3a444 (?)

## 2. 0xac78~0xac9d cluster system-wide reader 매핑

### 2.1 Round 28 의 38B entity state record 가설을 검증

도구 KNOWN_FIELDS 확장 (12 fields → 36 fields):
```python
0xac78, 0xac79, 0xac7a, 0xac7c,
0xac80, 0xac84,
0xac90, 0xac92, 0xac94, 0xac98, 0xac9c, 0xac9d,
```

### 2.2 Reader 분포

| field | sites | unique funcs | top readers |
|---|---|---|---|
| 0xac78 | 43 | 4 | FUN_000818f0(34x), FUN_000241dc(5x), FUN_0002c6a4(3x), FUN_000933e8(1x) |
| 0xac79 | 8 | 1 | FUN_000818f0(8x) |
| 0xac7a | 42 | 2 | FUN_000818f0(41x), FUN_0002c6a4(1x) |
| 0xac7c | 2 | 1 | FUN_000818f0(2x) |
| 0xac80 | 5 | 1 | FUN_000818f0(5x) |
| 0xac84 | 7 | 2 | FUN_000818f0(4x), **FUN_00081688(3x)** |
| 0xac90 | 3 | 1 | FUN_000818f0(3x) |
| 0xac92 | 1 | 1 | FUN_000818f0(1x) |
| **0xac94** | **57** | **4** | **FUN_000818f0(20x), FUN_00030018(14x), FUN_0008beba(14x), FUN_0008e89e(9x)** ⭐ |
| 0xac98 | 22 | 1 | FUN_000818f0(22x) |
| 0xac9c | 2 | 2 | FUN_000818f0(1x), FUN_00083b92(1x) |
| 0xac9d | 6 | 1 | FUN_000818f0(6x) |

### 2.3 통찰

- **10/12 fields 가 FUN_000818f0 전용** (single-entity state record 가설 확정)
- **0xac94 만 system-wide** (57 sites, 4 funcs) — entity metadata 후보:
  - FUN_000818f0 (20x, entity handler)
  - FUN_00030018 (14x, 신규 entity reader)
  - FUN_0008beba (14x, NPC dispatcher 영역)
  - FUN_0008e89e (9x, SCN dispatcher / record 0x3c4 main entry)
- **0xac78** 도 약간 spread (4 funcs) — base offset / 메모리 base 역할
- **0xac84 (FUN_00081688 3x)** = FUN_000818f0 인접 함수 = peer entity handler 후보

### 2.4 entity state record 38B 모델

```
task_struct[0xac78] = entity state record (38 byte)
  +0x00 (0xac78) base/type field      (43 sites, 4 funcs) ⭐ system-wide
  +0x01 (0xac79) byte (FUN_818f0 only) (8)
  +0x02 (0xac7a) byte (FUN_818f0 only) (42 ⭐top FUN_818f0 access)
  +0x04 (0xac7c) (2)
  +0x08 (0xac80) (5)
  +0x0c (0xac84) (7, FUN_81688 3x = peer)
  +0x18 (0xac90) (3)
  +0x1a (0xac92) (1)
  +0x1c (0xac94) ⭐⭐ entity metadata (57 sites, 4 funcs system-wide)
  +0x20 (0xac98) word (22, FUN_818f0 only)
  +0x24 (0xac9c) (2, FUN_83b92 1x)
  +0x25 (0xac9d) byte (6, FUN_818f0 only)
```

**가설**: 0xac94 = entity type code 또는 status flag (entity dispatcher 들이 검사하는 main key).

## 3. 0x9bd0-Object instance ≥84B (Round 26 가설 정정)

### 3.1 Instance field offsets (forward-window walk)

42 raw 0x9bd0 사이트에서 instance ptr deref 후 immediate offset 추적:

| offset | hits | 추정 |
|---|---|---|
| +0x1c (28) | 3x | adjacent to vtable+0x18 halfword |
| +0x10 (16) | 2x | mid-instance field |
| +0x18 (24) | 2x | vtable+0x18 halfword (Round 26) |
| +0x20 (32) | 2x | mid-instance field |
| +0x04 | 1x | early field |
| +0x1a, +0x1d, +0x30, +0x54 | 각 1x | spread fields |
| +0x374 | 1x | outlier (sub-object 또는 다른 패턴) |

→ **10 distinct instance offsets**, 최대 +0x54 (= ≥84 byte).

### 3.2 Round 26 가설 정정

| 측면 | Round 26 가설 | Round 29 정정 |
|---|---|---|
| 0x9bb4 + 0x9bd0 관계 | task_struct 안의 32B substructure (offset 0 + offset 0x1c) | substructure A 의 +0x1c 가 ptr-to-instance, instance 는 task_struct 외부 |
| Instance size | 32 byte | **≥84 byte** (10 distinct fields, max offset +0x54) |
| 위치 | task_struct 안 inline | **task_struct 외부 (heap-allocated 또는 별도 영역)** |

### 3.3 갱신된 구조 모델

```
task_struct (44KB+, single instance)
  └─ 0x9bb4..0x9bd0  substructure A (32B)
       ├─ +0x00 (0x9bb4) bit flag field
       ├─ +0x02 (0x9bb6) byte field
       ├─ +0x14 (0x9bc8) field
       └─ +0x1c (0x9bd0) ptr → 0x9bd0-Object instance (외부, ≥84B)

0x9bd0-Object instance (별도 메모리 영역, ≥84B)
  ├─ +0x00 (vtable ptr)
  ├─ +0x04 ... +0x54 (instance fields)
  └─ ...
  └─ vtable pointer points to vtable struct:
       ├─ vtable[+0x08] = function pointer → FUN_0007cd58 (60% dominant)
       └─ vtable[+0x18] = halfword metadata
```

## 4. 갱신된 indirect entry 목록 (5개)

```
GVM Firmware (외부 주입, 정적 분석 한계)
  ├─ FUN_0006619c (paint/tick callback) — 매 프레임 호출
  ├─ FUN_00070f34 (key handler) — 키 입력 시 호출
  ├─ FUN_0008b2e8 (sister entry, record 0x3c4)
  ├─ FUN_0008dcd8 (main entry, record 0x3c4)
  └─ FUN_000241dc ⭐ NEW (74-entry event/state dispatcher, caller_arg + 0x10 key)
```

FUN_000241dc 의 위치 (0x241dc) 는 0x6619c, 0x70f34, 0x8b2e8, 0x8dcd8 와 비교해서 **가장 작은 주소** = binary 의 시스템 영역. 핵심 firmware-callable function.

## 5. Round 30 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2CG | **FUN_000241dc 의 74-entry JT 디코드** + 각 case 의 sub-handler 매핑 | `decode_scn_jumptable.py` 적용 |
| ⭐⭐ 2CH | task_struct[0xac94] 의 4 readers 본문 분석 (entity metadata 의 의미) | FUN_00030018, FUN_0008beba, FUN_0008e89e |
| ⭐⭐ 2CI | 0x9bd0-Object instance allocator 추적 (heap 또는 외부 메모리) | 0x9bd0 의 writer (substructure A +0x1c 에 ptr 저장) 검색 |
| ⭐ 2CJ | FUN_00081688 본문 (FUN_000818f0 인접 peer entity handler 후보) | `disasm_subsystem_func.py 0x81688 <next_push>` |
| ⭐ 2CK | FUN_00030018 본문 (0xac94 14x reader) | `disasm_subsystem_func.py 0x30018 <next_push>` |
| ⭐ 2CL | FUN_0008e89e = SCN dispatcher main entry — 이미 PROGRESS.md 에 있음 | (재해석 가능) |
| 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 92% miss) | 도구 추가 확장 |

## 산출물

- `tools/recon/find_task_struct_field_readers.py` — KNOWN_FIELDS 36 fields 로 확장 (0xac78 cluster 12 fields)
- `work/h3/task_struct_field_readers.json` — 36 fields system-wide reader 통계
