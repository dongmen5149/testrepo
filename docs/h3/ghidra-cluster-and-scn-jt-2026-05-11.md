# Hero3 Ghidra — Round 36 / PM-26 (2026-05-11)
## 0x9b00 cluster direct wide-scan = 51 sites + FUN_00082f4c UI wrapper + FUN_0008e89e JT @ 0xabc68 디코드

> Round 35 의 도구 limitation 을 우회하기 위해 0x9b00 cluster 에 대해 R0 propagation 무시한 direct wide-scan 실행. 결과: Round 35 까지 1 site 였던 cluster 가 **51 sites in ~12 funcs**. 또 FUN_00082f4c UI invocation wrapper 본문 + FUN_0008e89e SCN dispatcher 의 19-entry JT 디코드.

## TL;DR (3줄)

1. ⭐⭐⭐ **0x9b00 cluster direct wide-scan = 51 sites** (Round 35: 1 site → 51 sites). R0 propagation 무시한 raw LDR pcrel 검색으로 cluster 의 진짜 reader 분포 발견. **FUN_00041c6e (= FUN_00041c14 의 sub-label) = cluster #1 dominant reader** (0x9b01 6x + 0x9b14 10x + 0x9b1c 4x + 0x9afc 1x = **21+ access**). 신규 reader: FUN_00022b50 (0x9b1c 8x), FUN_000409d4 (0x9b3c 5x), FUN_00042740. Round 25 의 cluster #1 가설 정량 확정.
2. ⭐⭐⭐ **FUN_0008e89e JT @ 0xabc68 디코드 완료** — 19 entries → 7 destinations. **case 0..12 (13 common opcodes) → 0x8ec26 shared handler** (default/text output), case 13~18 (6 special opcodes) → 각각 unique. **PROGRESS.md 가설 ("19 entries (opcode 0~0x12) → 7 distinct handlers (0x00~0x0c 공통 + 0x0d~0x12 각 unique)") 정확히 검증**.
3. ⭐⭐ **FUN_00082f4c UI invocation wrapper** (1.6KB, 746 instr, 7 cmp arms, **12 ctx_getter + 8 screen_ptr_getter**). task_struct[0x9c70/0x9c71/0xac78] dominant + BL FUN_00030018 (UI/HUD renderer) = **rendering pipeline** (entity state 처리 + UI overlay).

부수 발견:
- ⭐⭐ **도구 limitation 의 우회 검증** — direct wide-scan 이 R0 propagation 추적보다 50배 효율적 (0x9b00 cluster 1 site → 51 sites). 다음 라운드의 도구 강화 방향 = pattern-aware filtering 으로 false positive 줄이면서 raw scan 도 활용.
- ⭐ FUN_0008e89e 의 SCN bytecode opcode 분포 = 0x00~0x0c (13 common = text output 등) + 0x0d~0x12 (6 special opcodes = jump/conditional/sound/effect 등 추정).
- ⭐ 0x8f110/0x8f31c/0x8f544/0x8f884/0x8face/0x8fc20 = SCN special opcode handlers (다음 라운드 본문 분석 가능).

## 1. 0x9b00 cluster direct wide-scan

### 1.1 통계 비교 (Round 25 ~ 36)

| field | Round 25 발견 | Round 35 (도구 lenient) | Round 36 (direct scan) | 변화 |
|---|---|---|---|---|
| 0x9afc | 1 (FUN_00041c14) | 0 | **6 sites in 6 funcs** | +6 |
| 0x9b01 | 6 (FUN_00041c14) | 0 | **6 (FUN_00041c6e 6x)** | +6 |
| 0x9b06 | 1 | 0 | 2 | +2 |
| 0x9b14 | 10 (FUN_00041c14) | 0 | **11 (FUN_00041c6e 10x)** | +11 |
| 0x9b1c | 4 (FUN_00041c14) | 1 | **19 (FUN_00022b50 8x + FUN_00041c6e 4x)** | +18 |
| 0x9b3c | 1 | 0 | **7 (FUN_000409d4 5x)** | +7 |

**Total: 1 → 51 sites** (Round 36 direct scan).

### 1.2 dominant readers

```
FUN_00041c6e (= FUN_00041c14 의 sub-label, Round 25 발견):
  ├─ 0x9b01: 6x
  ├─ 0x9b14: 10x
  ├─ 0x9b1c: 4x
  └─ 0x9afc: 1x  
  Total: 21+ access  ⭐ cluster #1 dominant

FUN_00022b50 (신규):
  └─ 0x9b1c: 8x

FUN_000409d4 (신규):
  └─ 0x9b3c: 5x

FUN_00042740 (신규):
  └─ 0x9afc/9b06/9b14/9b1c/9b3c 각 1x  (cluster 의 setup/init 함수 후보)

기타 spread:
  0x9afc: FUN_0004115c, FUN_000442e4, FUN_000445b8, FUN_00046590 각 1x
  0x9b06: FUN_00040f04 1x
```

### 1.3 cluster #1 정체 (Round 25 의 가설 정량 확정)

Round 25 발견: FUN_00041c14 의 PC-rel literal 빈도 = 0x9b14 (10x), 0x9b01 (6x), 0x9b1c (4x), 0x9afc (1x) → cluster #1 가설.

Round 36 direct scan = **system-wide** 로 동일 cluster 가 12+ funcs 에서 사용. cluster #1 = task_struct 의 핵심 substructure (entity-related state, ~64 byte 영역).

### 1.4 도구 lenient 화 vs direct wide-scan

| 측면 | 도구 lenient (R0 propagation) | direct wide-scan |
|---|---|---|
| 정밀도 | 높음 (false positive 적음) | 낮음 (모든 ldr pcrel 캐치) |
| Recall | 0x9b00 cluster 의 1/51 = **2%** | 51/51 = **100%** |
| 패턴 다양성 커버 | 일부 (R0 register chain 만) | 전체 (all ldr pcrel) |
| **0x9b00 cluster** | **거의 실패** | **성공** |

**결론**: 도구 lenient 화로는 cluster 의 거의 모든 reader 를 놓침 = R0 chain 이 너무 길거나 branch-crossing 다발. **다음 라운드 도구 = direct wide-scan 기반 (raw ldr pcrel + post-pattern classification)** 이 효율적.

## 2. FUN_0008e89e JT @ 0xabc68 디코드 (SCN dispatcher)

### 2.1 19 entries 매핑

| case_idx (= SCN opcode) | dest | 의미 추정 |
|---|---|---|
| **0..12 (13 cases)** | **0x8ec26** | **common shared handler** (default / text output 등) |
| 13 (0x0d) | 0x8f110 | special opcode #1 |
| 14 (0x0e) | 0x8f31c | special opcode #2 |
| 15 (0x0f) | 0x8f544 | special opcode #3 |
| 16 (0x10) | 0x8f884 | special opcode #4 |
| 17 (0x11) | 0x8face | special opcode #5 |
| 18 (0x12) | 0x8fc20 | special opcode #6 |

### 2.2 PROGRESS.md 가설 정확히 검증

PROGRESS.md (Round 18 이전):
> "19 entries (opcode 0~0x12) → 7 distinct handlers (0x00~0x0c 공통 + 0x0d~0x12 각 unique)"

Round 36 raw decode:
- ✅ 19 entries
- ✅ 7 distinct destinations
- ✅ opcode 0x00~0x0c 공통 (case 0..12 → 0x8ec26)
- ✅ opcode 0x0d~0x12 unique (case 13..18 각각 다른 handler)

### 2.3 SCN bytecode 모델

```
SCN bytecode opcode (0x00..0x12, 19 distinct)
  ├─ 0x00..0x0c (13 opcodes) = "default" / text output 패밀리
  │     → handler 0x8ec26 (FUN_0008e89e 안)
  │     - 일반 텍스트/문자 출력 또는 기본 dialog command 후보
  │
  └─ 0x0d..0x12 (6 special opcodes) = control flow / effect 명령
        → 0x8f110 (opcode 0x0d)
        → 0x8f31c (opcode 0x0e)
        → 0x8f544 (opcode 0x0f)
        → 0x8f884 (opcode 0x10)
        → 0x8face (opcode 0x11)
        → 0x8fc20 (opcode 0x12)
        - 추정: jump / conditional / sound trigger / effect / etc.
```

각 special handler 본문 분석은 다음 라운드 작업 (2DM 후속).

## 3. FUN_00082f4c UI invocation wrapper

### 3.1 Boundary 와 prologue

| 측면 | 값 |
|---|---|
| 시작 | 0x82f4c |
| 끝 | 0x83580 (다음 push prologue) |
| size | 1588 byte (1.6KB) |
| instr | 746 |
| cmp arms | 7 (small) |
| BL count (interesting) | 30 |

```asm
0x82f4c: push {r4, r5, r6, r7, lr}    ; PIC standard prologue
0x82f4e: mov r7, sl
0x82f50: mov r6, r8
0x82f52: push {r6, r7}
0x82f54: mov r7, sp
0x82f56: sub sp, #0x7c                  ; 124 byte stack frame
0x82f58: ldr r2, [pc, #0x284]           ; GOT base
0x82f5a: mov sl, r2
0x82f5c: add sl, pc
0x82f5e: subs r3, r7, #4
0x82f60: str r0, [r3]                   ; caller arg #1 saved
0x82f62: adds r3, r7, #0
0x82f64: subs r3, #8
0x82f66: str r1, [r3]                   ; caller arg #2 saved
```

### 3.2 BL 분포

| target | count | 의미 |
|---|---|---|
| context_getter | 12 | 다양한 task_struct field access |
| screen_ptr_getter | 8 | rendering 의 핵심 helper |
| (기타) | 10 | drawing primitives + FUN_00030018 등 |

### 3.3 핵심 task_struct fields

| field | 의미 |
|---|---|
| 0x9c70 | entity-per byte field (`*0x000831e8=0x9c70`) |
| 0xac78 | entity state record base (`*0x000831fc=0xac78`) |
| 0x9c71 | entity-per byte field (`*0x00083560=0x9c71`) |

### 3.4 정체 — UI overlay rendering pipeline

조합:
- 12 context_getter (entity state 다수 fetch)
- 8 screen_ptr_getter (다양한 화면 영역 그리기)
- 0x9c70/0x9c71/0xac78 dominant (entity record + adjacent fields)
- BL FUN_00030018 (Round 35 발견: UI/HUD renderer)

→ **FUN_00082f4c = entity 의 UI overlay 처리 + UI/HUD renderer 호출** = HUD/dialog/status indicator rendering pipeline.

## 4. 갱신된 모델

### 4.1 task_struct[0x9b00 cluster] = cluster #1 (~64 byte 영역)

```
task_struct + 0x9afc..0x9b3c  cluster #1 (~64 byte)
  +0x9afc  byte/word (6 sites in 6 funcs)
  +0x9b01  byte (6 sites, FUN_00041c6e dominant)
  +0x9b06  byte (2 sites)
  +0x9b14  word (11 sites, FUN_00041c6e dominant)
  +0x9b1c  word (19 sites, FUN_00022b50 + FUN_00041c6e)
  +0x9b3c  byte/word (7 sites, FUN_000409d4 dominant)

Top readers (cluster #1):
  FUN_00041c6e: 21+ access (= FUN_00041c14 의 sub-label, 8.6KB function 안)
  FUN_00022b50: 8x (신규 함수)
  FUN_000409d4: 5x (신규 함수)
  FUN_00042740: 5x spread (cluster setup 후보)
```

### 4.2 PROGRESS.md game update flow (Round 36 검증 완료)

```
GVM Firmware (5 indirect entries)
  ├─ FUN_0008b2e8 (sister entry, record 0x3c4)
  │   └─ inline @ 0x8c19c → FUN_0008d5e4 (jt 0xabaa8, 19 entries)
  │   └─ BL → FUN_0008beba (NPC entity bridge, 7.5KB)
  │
  ├─ FUN_0008dcd8 (main entry, record 0x3c4)
  │   └─ inline @ 0x8eb80 → FUN_0008ff18 (jt 0xabc68, 19 entries) ⭐ Round 36 디코드
  │       ├─ case 0..12 (13 common opcodes) → 0x8ec26 (text output 등)
  │       └─ case 13..18 (6 special opcodes) → 0x8f110/0x8f31c/0x8f544/0x8f884/0x8face/0x8fc20
  │   └─ BL → FUN_0008e89e (SCN dispatcher main entry, 16.3KB)
  │
  ├─ FUN_000241dc (system event dispatcher, 74-entry JT)
  └─ FUN_0006619c (paint/tick) / FUN_00070f34 (key)

Single-entity processing:
  FUN_000818f0 (single-entity state handler, 5.6KB)
    ├─ entity state update (0xac78~0xac9d 38B record)
    └─ basic rendering (4 screen_ptr_getter at end)

  FUN_00082f4c (UI overlay invocation wrapper, 1.6KB) ⭐ Round 36
    ├─ entity state fetch (0x9c70/0x9c71/0xac78)
    ├─ 8 screen_ptr_getter (UI overlay drawing)
    └─ BL → FUN_00030018 (UI/HUD renderer, 10.1KB)
```

## 5. Round 37 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2DP | **FUN_0008e89e 의 0x8ec26 common handler 본문** (13 opcodes 공통 처리, text output 후보) | `disasm_subsystem_func.py 0x8ec26` |
| ⭐⭐ 2DQ | FUN_00041c6e cluster #1 reader 본문 분석 (cluster 의 의미적 사용) | `disasm_subsystem_func.py 0x41c6e` |
| ⭐⭐ 2DR | FUN_0008e89e 의 6 special opcodes 본문 (0x8f110/0x8f31c/...) | inline disasm |
| ⭐⭐ 2DS | FUN_0008b2e8 의 inline @ 0x8c19c → FUN_0008d5e4 JT @ 0xabaa8 디코드 (NPC dispatcher 19 entries) | binary 직접 read |
| ⭐ 2DT | 도구 추가 강화 — direct wide-scan 통합 (raw ldr pcrel + post-pattern classification) | 도구 코드 수정 |
| ⭐ 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 92% miss) | 도구 추가 확장 |

## 산출물

- `work/h3/ui_invocation_82f4c_disasm.json` — FUN_00082f4c (1.6KB) 본문
