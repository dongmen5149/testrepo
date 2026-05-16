# Hero3 Ghidra — Round 38 / 2026-05-17 PM-2 (op12 inner JT + 6th indirect entry)

> Round 37 (`ghidra-scn-handlers-and-state-machines-2026-05-17.md`) 에서 식별한 opcode 0x12 (11.4KB Korean dialogue sub-interpreter) 와 cluster #1 paired state machine 의 후속 분석.
> 핵심: (1) opcode 0x12 의 47 arms 정밀 분류 + 내부 74-entry JT 디코드, (2) cluster #1 state machine 의 GVM-side 진입점 = **6번째 indirect entry function 발견**.

## 한 줄 요약

opcode 0x12 의 47 cmp arms 는 4 카테고리로 분류: **small state (0~0x12) 35개 / sentinel 0xff 6개 / EUC-KR (0x89/0x8f) 4개 / ASCII (';','I','2') 2개**. 0x90200 의 `cmp r1, #0x49` 가드 다음에 **표준 Hero3 SL-relative 74-entry JT (@ 0xabcb4) — 7 destinations 모두 FUN_00098904 안의 7개 entry label** = computed-goto 패턴. cluster #1 state machine 의 GVM-side 진입점 = **FUN_000245fc (NEW 6번째 indirect entry, 0 BL caller)**.

## 2EA-1: opcode 0x12 47 arms 정밀 분류

`tools/recon/classify_op12_arms.py` 출력 (입력: `work/h3/scn_op12_8fc20_disasm.json`):

| 카테고리 | 개수 | 대표 imm | 위치 (몇 예시) | 의미 |
|---|---|---|---|---|
| **small state (0~0x12)** | **35/47** | 0/1/2/3/4/0xc/0x11 | 0x8fdb4 .. 0x92786 | 일반 상태 분기 (대부분 cmp #0 = null check, cmp #0xc = 13-record array bound) |
| **sentinel (0xff)** | 6/47 | 0xff | 0x90d74/0xdc8/0xe1c + 0x912b4/0x12e2/0x1310 | EOF/end-of-stream 검사 (두 3-cmp 클러스터 = 두 byte stream 종료) |
| **EUC-KR lead byte** | 4/47 | 0x89, 0x8f | 0x920c2/0x9217c + 0x925b8/0x92698 | CP949 한글 음절 영역 [0x89..0x8f] 검사 (paired bgt + ble) |
| **ASCII format token** | 2/47 | 0x49='I', 0x32='2' | 0x90200, 0x91ac6 | 'I'/'2' 형식 escape 또는 인덱스 |

### 결정적 패턴 — `cmp r1, #0x49 bls` 가 inner JT gate

`0x90200: cmp r1, #0x49; bls 0x90206` 다음 코드 (capstone 디스어셈블):

```
0x90206: movs r2, #0x2c           ; r2 = 0x2c
0x90208: rsbs r2, r2, #0           ; r2 = -0x2c
0x9020a: adds r2, r2, r7           ; r2 = r7 - 0x2c (= 스택 frame offset)
0x9020c: ldr  r3, [r2]              ; r3 = stack[-0x2c] (= scene script 의 sub-opcode byte)
0x9020e: lsls r2, r3, #2            ; r2 = r3 << 2 = index * 4
0x90210: ldr  r3, [pc, #0x2fc]      ; r3 = 0xffff9074 (signed -0x6f8c)
0x90212: add  r3, sl                ; r3 = sl + (-0x6f8c) = JT base 0xabcb4
0x90214: adds r3, r2, r3            ; r3 = JT_base + index*4
0x90216: ldr  r2, [r3]              ; r2 = JT[index] (signed offset)
0x90218: ldr  r3, [pc, #0x2f4]      ; r3 = 0x17ac (literal)
0x9021a: add  r3, sl                ; r3 = sl + 0x17ac = code base 0xb43ec
0x9021c: adds r3, r2, r3            ; r3 = code_base + JT[index] = 점프 대상
0x9021e: mov  pc, r3                ; 점프!
```

⭐ Round 36 의 outer JT @ 0xabc68 (FUN_0008e89e dispatcher) 와 **동일한 SL-relative 모델**.

## 2EA-2: 74-entry inner JT @ 0xabcb4 디코드

코드: `tools/recon/decode_op12_jt_v2.py`

**모델**: `dest = 0xb43ec + signed(JT[index])`, sl = 0xb2c40 (GOT base)

| destination | offset (FUN_00098904 +) | 케이스 수 | cases |
|---|---|---|---|
| 0x00098cb4 | **+0x3b0** | **66/74** ⭐ default (sparse, 89%) | 1~10, 16~70, 72 |
| 0x00098b28 | +0x224 | 2 | 14, 15 |
| 0x00098958 | +0x54 | 1 | 0 |
| 0x00098964 | +0x60 | 1 | 11 |
| 0x00098ac8 | +0x1c4 | 1 | 12 |
| 0x00098a6e | +0x16a | 1 | 13 |
| 0x00098bee | +0x2ea | 1 | 71 |
| 0x00098c60 | +0x35c | 1 | 73 |

**모든 destinations = FUN_00098904 내부의 8개 entry label** = **computed-goto 패턴** (1524B 함수 안에 7+ 진입점).

### FUN_00098904 본문 (1524B / 1806 instr / 41 cmp arms)

> 주의: 1806 instr 는 disasm tool 의 범위 over-shoot (0x99764 까지). FUN_00098904 자체는 0x98904 ~ 0x98ef8 = 1524 byte.

- cmp 분포 핵심: **cmp #0 (27x)** + cmp #1/0x7f/0x04/0x05/0x06/0x07 — 작은 정수 상태 + ASCII DEL (0x7f) 검사
- BL: 10× context_getter (r0 = ?, 일부 r0=*0x4dc)
- ⭐⭐ **43 BL callers system-wide** (find_callers_generic.py 출력): system-wide **인기 helper**. 17 callers 가 0xb0xx~0xc8xx (= FUN_00006334 = 10KB 핵심 state machine, Round 17 의 발견) 안에 있어, **opcode 0x12 의 sub-handler 전용이 아니라 일반-목적 helper** = JT 가 그 안의 7 entry label 로 점프.

### Sparse pattern 시그니처

74 entries 중 66 (89%) = default = Round 30 의 74-entry JT (FUN_000241dc / @ 0xa6710) 과 **동일 패턴** (62/74 = 84% no-op). Hero3 의 **시스템 이벤트 dispatch 표준 형태** — sparse table 로 특정 인덱스만 동작, 나머지는 no-op.

## 2EC: cluster #1 state machine 의 GVM-side 진입점 = 6번째 indirect entry

### Caller chain

`tools/recon/find_callers_41c14.py` + `find_callers_generic.py` 결과:

```
FUN_00040fb0 (cluster #1 parent state runner, 3.1KB):
  ← 2 BL callers @ 0x2462c (in FUN_000245fc +0x30), 0x2b190 (in FUN_0002ae44 +0x34c)

FUN_000245fc (388B, 13 arms, BL=7 ctx only, pure state — like FUN_00040fb0):
  ← 0 BL callers ⭐⭐⭐ = INDIRECT-ONLY ENTRY FUNCTION

FUN_0002ae44 (1404B, 15 arms, BL=3 ctx + 1 screen_ptr_getter(r0=0x9e74)):
  ← 2 BL callers @ 0x248ce, 0x24fd0 (둘 다 0x24xxx 시스템 영역)
```

⭐⭐⭐ **FUN_000245fc 는 0 BL caller** = Round 29 의 5번째 indirect entry (FUN_000241dc) 처럼 **GVM firmware 가 indirect 로 호출**. **Hero3 의 6번째 indirect entry function 발견**.

Round 30 에서 알려진 5 indirect entries:
- FUN_0006619c (paint/tick callback)
- FUN_00070f34 (key handler)
- FUN_0008b2e8 (sister entry / NPC)
- FUN_0008dcd8 (main entry / scene)
- FUN_000241dc (system event dispatcher, 74-entry JT)

**신규 6th entry**:
- **FUN_000245fc** (NEW, 388B, cluster #1 state machine 진입점 — FUN_00040fb0 → FUN_00041c14 chain)

### 완성된 chain

```
GVM Firmware (외부 PIC indirect 호출)
  └─ FUN_000245fc (6th indirect entry, 388B, cluster #1 entry point)
       ├─ BL @0x2462c (+0x30) → FUN_00040fb0 (parent state runner, 3.1KB)
       │    └─ BL @0x40ffe (+0x4e) → FUN_00041c14 (cluster #1 state machine, 2.8KB)
       │         └─ BL @0x42744 (+0xb30) → FUN_00041c6e (internal self-loop sub-label)
       └─ (다른 BL targets — 추가 추적 필요)
```

이로써 **cluster #1 (task_struct[0x9afc~0x9b3c]) 의 update path 가 시스템 진입점부터 완전히 추적됨**. 0x9b14 (main state 11x), 0x9b01 (step counter 6x), 0x9b1c (sub-state 4x), 0x9afc (start flag 1x) 의 4-field state machine 은 GVM 이 매 tick 마다 indirect call 로 호출.

**가설**: FUN_000245fc 는 **별도 게임 시스템 업데이트 슬롯** (예: cutscene/event 진행, 메뉴 상태, save 상태) — paint/tick (FUN_0006619c) 와 system event (FUN_000241dc) 와 동등한 level 의 시스템 hook.

### FUN_0002ae44 = secondary caller

FUN_0002ae44 (1404B) 는 다른 caller chain — screen_ptr_getter (r0=0x9e74) 호출로 **렌더링 영역에 닿는 state handler**. 자체 2 callers (0x248ce, 0x24fd0) 둘 다 0x24xxx 시스템 영역이므로 FUN_000241dc 의 74-entry JT 또는 인접 함수에서 호출될 가능성.

## Round 38 종합 진척

### ✅ 검증 추가

1. **opcode 0x12 47 arms 분류**: state 35 / sentinel 6 / EUC-KR 4 / ASCII 2 = **token-driven multi-byte text parser** 확정
2. **inner 74-entry JT @ 0xabcb4 디코드**: 7 destinations 모두 FUN_00098904 안의 entry labels = computed-goto 패턴 (Round 30 의 sparse 74-JT 패턴 재확인)
3. **FUN_00098904 = 43 callers system-wide popular helper** (1524B, 10× ctx) — opcode 0x12 전용이 아니라 일반 목적
4. **FUN_000245fc = 6번째 indirect entry function 발견** (388B, 0 BL caller, cluster #1 state machine entry point)
5. **cluster #1 state machine 의 완전한 chain**: GVM → FUN_000245fc → FUN_00040fb0 → FUN_00041c14 → FUN_00041c6e

### 진척률 (Round 38 시점)

- Ghidra 게임 로직 리버싱: ~15~25% → **~20~30%** (6 indirect entries 완성 + opcode 0x12 inner JT 디코드)
- 전체: ~18~28% → **~22~32%**

### ⭐ 다음 라운드 (39) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2FA** | **FUN_000245fc 본문 정밀 분석** — 13 arms + 7 ctx 의 task_struct 필드 분포 → cluster #1 의 의미 (cutscene? event? menu?) | 이미 `work/h3/fb0_caller1_245fc_disasm.json` 존재 |
| ⭐⭐ **2FB** | FUN_00098904 본문 (1524B, 41 arms, 8 JT entry labels) — 각 entry label 의 의미 | `disasm_subsystem_func.py 0x98904 0x98ef8` |
| ⭐⭐ **2FC** | FUN_0002ae44 → callers (0x248ce, 0x24fd0) 추적 — FUN_000241dc 74-entry JT 와 관계 | `find_callers_generic.py` 확장 |
| ⭐ **2FD** | NPC 6 special opcodes (0x8c79c~0x8d2e2) 본문 disasm — SCN 6 special 과 차이 식별 | inline disasm |
| ⭐ **2FE** | opcode 0x12 의 0xc-stride record array gate (0x90e38, 0x9131c) — 12-byte record 의 구조 분석 | window disasm |
| ⭐ **2FF** | EUC-KR pair 두 클러스터 (0x920c0, 0x92590) — 한글 문자 처리 path 풀이 | disasm + decode |

### 도구 산출 (Round 38)

- `tools/recon/classify_op12_arms.py` (new) — 47 arms 의미 분류
- `tools/recon/analyze_op12_subjt.py` (new) — JT 후보 스캐닝 (실패 경험)
- `tools/recon/disasm_op12_window.py` (new) — capstone Thumb disasm 윈도우
- `tools/recon/decode_op12_jt_v2.py` (new) — SL-relative 74-entry JT 디코더
- `tools/recon/find_next_function.py` (new) — push prologue 정방향 검색
- `tools/recon/find_callers_generic.py` (new) — 일반 caller 추적

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 37 의 [ghidra-scn-handlers-and-state-machines-2026-05-17.md](ghidra-scn-handlers-and-state-machines-2026-05-17.md) 읽기
2. PROGRESS.md 의 6 indirect entries 표 확인 — FUN_000245fc 신규
3. `work/h3/fb0_caller1_245fc_disasm.json` + `state_runner_40fb0_disasm.json` + `record_disp_41c14_disasm.json` = cluster #1 chain 의 3-tier disasm 종합 데이터
4. 권장 첫 작업: 2FA (FUN_000245fc 정밀 분석) — cluster #1 의 의미가 가장 가치 높은 다음 단계
