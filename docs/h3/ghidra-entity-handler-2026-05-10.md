# Hero3 Ghidra — Round 28 / PM-18 (2026-05-10)
## FUN_000818f0 본문 분석 (5.6KB) + 0x9bd0-Object vtable[+0x08] sub-call 정체 + FUN_0008d87c 본문

> Round 27 의 FUN_000818f0 entity update loop 가설을 본문 분석으로 검증. 결과: **iteration loop 아님** (0 backward branches), 실제는 **single-entity state handler**. 또 task_struct[0xac78~0xac9d] = 38 byte entity-per state record cluster 발견.

## TL;DR (3줄)

1. ⭐⭐⭐ **FUN_000818f0 = single-entity state handler** (NOT iteration loop). 5724B / 2559 instr, **212 context_getter** (PM-3 추정 일치), **0 backward branches** = 외부 caller 가 entity 마다 호출. **task_struct[0xac78~0xac9d] = 38 byte entity-per state record cluster** (51+42+34+20+12+7+5+5+4+3+2+2 = 200+ access in 단일 함수).
2. ⭐⭐⭐ **0x9bd0-Object vtable[+0x08] = function pointer to FUN_0007cd58** (60% dominant target, 6/10 caught sites). vtable[+0x08] 는 FUN_0007cd58 (Round 26 의 leaf 산술 helper) 호출 → **vtable[+0x18] halfword data 처리 패턴**. 즉 0x9bd0-Object = "halfword data + accessor function" 형식의 generic data class.
3. ⭐⭐ **FUN_0008d87c (1.1KB, 4 cmp arms) = simple sub-handler** — 0x9c70 (7x) + 0x9e28 (5x) + 0x1668 (3x) dominant. game update flow 의 sister entry 와 main entry 사이 inline 영역 = entity slot 처리 sub-handler.

부수 발견:
- ⭐⭐ **0xac78 cluster 정밀 매핑** — 0xac78 (42x) / 0xac79 (12x) / 0xac7a (51x) / 0xac7c (2x) / 0xac80 (5x) / 0xac84 (4x) / 0xac90 (5x) / 0xac92 (3x) / 0xac94 (20x) / 0xac98 (34x) / 0xac9c (2x) / 0xac9d (7x) = 13 distinct field offsets in 38 byte 영역. byte/short/word mix.
- ⭐ **ASCII 비교 발견** — cmp #0x49 ('I'), #0x58 ('X'), #0x62 ('b'). FUN_000818f0 + FUN_0008d87c 모두 사용 = text/key handling 가능성 있음.
- ⭐ **0x1668 (5736) = small constant** — FUN_0008d87c 에서 3x 사용. medium_int 분류, GOT slot 인지 inline data 인지 추가 검증 필요.

## 1. FUN_000818f0 (5.6KB) 본문 분석

### 1.1 Boundary

| 측면 | 값 |
|---|---|
| 시작 | 0x818f0 |
| 끝 | 0x82f4c (다음 push prologue) |
| size | 5724 byte (5.6KB) — PM-3 5.4KB 추정 일치 |
| instr | 2559 |
| cmp arms | 42 |
| BL count (interesting) | 216 (212 ctx_getter + 4 screen_ptr_getter) |

### 1.2 cmp 분포 — state-by-state if-else chain

| imm | count | 의미 추정 |
|---|---|---|
| 0x00 | 14x | null check |
| 0x0a (10) | 6x | state value or row marker |
| 0x01 | 5x | binary state |
| 0x0c (12) | 4x | range/state |
| 0x02 | 4x | enum state |
| 0x62 ('b') | 2x | ASCII char compare |
| 0x07/0x08 | 각 2x | small enum |
| 0x49 ('I'), 0x12 (18), 0x58 ('X') | 각 1x | char/state |

**spread distribution = JT dispatch 가 아니라 sequential state machine** (한 entity 의 다양한 상태에 대한 분기 처리).

### 1.3 핵심 발견 — Iteration loop 아님

**0 backward branches** in 42 cmp+branch arms. 즉 함수 내부에 loop back-edge 없음.

PM-3 의 가설 정정:
- ~~per-entity update loop~~ (iteration 내부에서 함)
- **per-entity state handler** (외부 caller 가 entity 마다 호출, 함수는 단일 entity 처리)

### 1.4 PC-rel literal 분포 — 0xac78 cluster dominant

| offset | hits | 추정 (entity state slot) |
|---|---|---|
| 0xac7a | 51x | (offset +2 in cluster) |
| 0xac78 | 42x | base offset |
| 0xac98 | 34x | mid-cluster |
| 0xac94 | 20x | mid-cluster |
| 0xac79 | 12x | byte at offset +1 |
| 0xac9d | 7x | byte at offset +0x25 |
| 0xac90 | 5x | (+0x18) |
| 0xac80 | 5x | (+0x08) |
| 0xac84 | 4x | (+0x0c) |
| 0xac92 | 3x | (+0x1a) |
| 0xac9c | 2x | (+0x24) |
| 0xac7c | 2x | (+0x04) |
| 0x9c70 | 17x | byte field |
| 0x9c71 | 15x | byte field |
| 0x9e28 | 5x | sound state |

**0xac78~0xac9d 합계 ~190 hits in 단일 함수** = entity state record 의 거의 모든 field access. cluster size = 0xac9d - 0xac78 + 4 = ~38 byte.

### 1.5 Entity state record (38 byte, 추정 layout)

| offset | (relative) | hits | 추정 |
|---|---|---|---|
| 0xac78 | +0x00 | 42 | byte/word, base field |
| 0xac79 | +0x01 | 12 | byte (= 0xac78 word 의 second byte 또는 별도 byte) |
| 0xac7a | +0x02 | 51 | byte (top access) |
| 0xac7c | +0x04 | 2 | word? |
| 0xac80 | +0x08 | 5 | word |
| 0xac84 | +0x0c | 4 | word |
| 0xac90 | +0x18 | 5 | word |
| 0xac92 | +0x1a | 3 | byte/short |
| 0xac94 | +0x1c | 20 | word |
| 0xac98 | +0x20 | 34 | word |
| 0xac9c | +0x24 | 2 | word |
| 0xac9d | +0x25 | 7 | byte |

→ 38 byte entity state record (mixed byte/word fields).

### 1.6 4x screen_ptr_getter at end — drawing phase

함수 끝 (0x82eaa~0x82f18) 에서 4 screen_ptr_getter calls = **rendering phase**. 즉 함수가:
1. Entity state update (0x818f0 ~ 0x82e?? - 대부분)
2. Entity rendering (0x82eaa ~ 0x82f4c - 마지막)

**update + render 통합 핸들러** 가설 — single entity 의 state 갱신 후 화면에 그리기까지 한 함수에서 처리.

## 2. 0x9bd0-Object vtable[+0x08] sub-call 정체

### 2.1 후속 분석 — 42 raw sites 중 +8 add 패턴 detect

42 raw 0x9bd0 LDR pcrel 사이트 중 forward-window 에서 `+8 add` + `bl` 패턴 매칭:

| target | hits | 정체 |
|---|---|---|
| **0x7cd58** | **6x** | **FUN_0007cd58 (Round 26 leaf 산술 helper, halfword 처리)** |
| 0x9fb78 | 1x | memset_like |
| 0x294a2 | 1x | unknown |
| 0x4c154 | 1x | unknown |
| 0x4ad10 | 1x | context_getter (false-detect — different context) |

**0x7cd58 = 60% dominant target**. 즉 0x9bd0-Object 의 vtable[+0x08] 함수 포인터 가 **FUN_0007cd58 을 가리킴** (또는 caller 가 직접 호출).

### 2.2 결합 모델 (Round 26 + 27 + 28)

```
task_struct[0x9bd0] → ptr to 0x9bd0-Object instance
                       ├─ vtable ptr (in instance)
                       │     ├─ vtable[+0x08] = function pointer  → FUN_0007cd58 (60% case)
                       │     └─ vtable[+0x18] = halfword data    → FUN_0007cd58 가 read
                       └─ instance fields
```

**0x9bd0-Object = "halfword metadata + accessor function" 형식의 generic data class**.

vtable[+0x08] method 는 Round 25/26/27 에 걸쳐 점진적으로 풀림:
- Round 25: "vtable[8] method 호출"
- Round 26: FUN_0007cd58 = leaf 산술 helper (vtable+0x18 halfword 처리)
- Round 28: vtable[+0x08] 자체가 FUN_0007cd58 을 가리킴 (60% dominant)

### 2.3 정체 가설 — sprite/animation slot

`asrs r3, r3, #4` (= signed div 16) 산술 + 16-bit halfword metadata + accessor function = **sprite tile coord 또는 animation frame index** 추정. 16x 단위 (= 16-pixel tile/grid)는 GVM 피처폰 sprite 표준.

다음 라운드에서 0x9bd0-Object 의 instance fields (해당 객체의 size + member layout) 추적이 필요.

## 3. FUN_0008d87c (1.1KB) 본문

### 3.1 Boundary

| 측면 | 값 |
|---|---|
| 시작 | 0x8d87c |
| 끝 | 0x8dcd8 (다음 push prologue) |
| size | 1116 byte (1.1KB) |
| instr | 536 |
| cmp arms | **4** (very few = simple sequential) |
| context_getter | 19 |

### 3.2 PC-rel literal 분포

| offset | hits | 정체 |
|---|---|---|
| 0x9c70 | 7x | byte field |
| 0x9e28 | 5x | sound state #1 |
| 0x1668 | 3x | medium_int (5736) — GOT slot 후보 |

→ **task_struct[0x9c70] + task_struct[0x9e28] dominant**. 0x9c70 cluster + sound subsystem 의 inline handler.

### 3.3 game update flow 위치

PROGRESS.md 의 game update flow:
```
FUN_0008b2e8 (sister entry, record 0x3c4)
  └ inline @ 0x8c19c → FUN_0008d5e4 (jt 0xabaa8)
FUN_0008dcd8 (main entry, record 0x3c4)
  └ inline @ 0x8eb80 → FUN_0008ff18 (jt 0xabc68)
```

**FUN_0008d87c (0x8d87c) ∈ [FUN_0008d5e4, FUN_0008dcd8]** = **sister entry (FUN_0008b2e8) 의 inline 영역**. 즉 record 0x3c4 NPC dispatcher 의 sub-handler. 4 cmp arms + 19 ctx_getter = simple per-record processing.

## 4. 갱신된 게임 시스템 모델

### 4.1 Top entity-handling functions (Round 28)

```
FUN_000818f0 (5.6KB) — single-entity state handler + renderer
  ├─ 212 context_getter calls
  ├─ task_struct[0xac78~0xac9d] = 38 byte entity state record (200+ hits)
  ├─ 0 backward branches → external iteration (caller-driven)
  └─ 4x screen_ptr_getter (rendering phase at end)

FUN_0008d87c (1.1KB) — sister entry inline sub-handler
  ├─ 19 context_getter calls
  ├─ task_struct[0x9c70] + [0x9e28] dominant
  └─ 4 cmp arms (simple sequential)

FUN_0008b2e8 / 0x8dcd8 — sister/main entries (record 0x3c4 NPC dispatchers)
```

### 4.2 task_struct[0xac78~0xac9d] = 38B entity state record

```
+0x00 0xac78: word    (42 hits)  base field
+0x01 0xac79: byte    (12 hits)
+0x02 0xac7a: byte    (51 hits)  ⭐ top access
+0x04 0xac7c: word?   (2 hits)
+0x08 0xac80: word    (5 hits)
+0x0c 0xac84: word    (4 hits)
+0x18 0xac90: word    (5 hits)
+0x1a 0xac92: byte/short (3 hits)
+0x1c 0xac94: word    (20 hits)
+0x20 0xac98: word    (34 hits)  ⭐ second top
+0x24 0xac9c: word    (2 hits)
+0x25 0xac9d: byte    (7 hits)
```

→ 38 byte entity state record. byte+word mix.

### 4.3 0x9bd0-Object 정체 (Round 28 결합)

```
0x9bd0-Object (vtable + halfword data class)
  ├─ vtable[+0x08] = function pointer → FUN_0007cd58 (60% dominant)
  ├─ vtable[+0x18] = halfword metadata (16-bit signed)
  └─ FUN_0007cd58 동작: ldrh [vtable+0x18]; sign-extend; >>4 (div 16)
       = sprite tile coord 또는 animation frame index 추정
```

## 5. Round 29 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2CA | **FUN_000818f0 의 외부 caller 추적** (entity iteration 의 진짜 위치) | `find_xrefs.py 0x818f0` 또는 BL 검색 |
| ⭐⭐ 2CB | task_struct[0xac78~0xac9d] entity record 의 다른 reader 함수 매핑 | `find_task_struct_field_readers.py --field 0xac78` etc |
| ⭐⭐ 2CC | 0x9bd0-Object instance size + member layout (FUN_0007cd58 caller chain) | indirect call 추적 |
| ⭐⭐ 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 의 92% miss) | 도구 추가 확장 |
| ⭐ 2CE | FUN_000818f0 의 4x screen_ptr_getter rendering 영역 본문 (0x82eaa~) | inline disasm |
| ⭐ 2CF | 0x1668 (FUN_0008d87c medium_int) 정체 — GOT slot vs ctx field | usage pattern 검증 |

## 산출물

- `work/h3/entity_update_818f0_disasm.json` — FUN_000818f0 (5.6KB) 본문
- `work/h3/inline_dispatcher_8d87c_disasm.json` — FUN_0008d87c (1.1KB) 본문
