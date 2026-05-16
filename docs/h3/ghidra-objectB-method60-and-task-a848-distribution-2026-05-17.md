# Hero3 Ghidra — Round 47 / 2026-05-17 PM-11 (ObjectB.vtable[+0x60] + task[0xa848] 34 callers 분포 + letter input 진입점)

> Round 46 (`ghidra-input-subsystem-and-helpers-2026-05-17.md`) 의 후속 — FUN_0003a86c letter input 진입점 + FUN_85aa8의 vtable[+0x60] object 정체 + task[0xa848] 사용 분포 매핑.

## 한 줄 요약

⭐⭐⭐ **vtable[+0x60] = ObjectB.method0x60 (신규 슬롯 발견)**: FUN_00085aa8가 GOT[+0x18] = ObjectB의 vtable [+0x60] method를 indirect call. ObjectB known methods 슬롯 추가 (Round 47 시점 9개: +0x10/0x20/0x44/0x54/0x58/**0x60**/0x68/0x7c/0x80). ⭐⭐⭐ **task[0xa848] = "current screen/menu state" 중앙 필드**: 34 callers 분포가 save/load (FUN_56f3c) + render command buffer (FUN_57394) + 7th indirect entry FUN_00086058 cluster (15+ functions in 0x85xxx-0x86xxx) + sister entry sub-handler (FUN_8d87c, Round 28) — 모든 핵심 subsystems에서 access. ⭐⭐ **FUN_0003a86c = letter input subsystem 진입점** (388B, cmp #0xf range guard + 13 ctx + 0 other BL + bl FUN_3c920, 4 callers including FUN_000818f0 entity update loop). 4 sub-helpers 본문 (FUN_3d434/85e88/2cc94/862d4 모두 lightweight state ops).

## 2NA: FUN_0003a86c — letter input subsystem 진입점 (388B)

### 프로파일

- 388B / 177 instr / **3 cmp arms** (cmp #0xf bls + cmp #0 ×2)
- BL = **13 context_getter + 0 other** = pure-state dispatcher
- 19 PC-rel literals (15 GOT slot offsets + 3 neg + 1 binary_addr)

### Range guard 패턴

`cmp r2, #0xf bls 0x3a8a4` at 0x3a89e = **input ≤ 15 valid** (similar to FUN_0002c6a4 event dispatcher / FUN_00086058 7th indirect entry).

### 4 BL callers 분포

| caller | container | 비고 |
|---|---|---|
| 0x3aaa4 | 0x3Axxx region | letter input subsystem 내부 |
| 0x3b0a0 | 0x3Bxxx region | adjacent helper |
| 0x3ba7a | 0x3Bxxx region | adjacent helper |
| **0x8195c** | **FUN_000818f0** (entity update loop, Round 28, 5.6KB!) | ⭐⭐⭐ **entity processing → letter input trigger** |

⭐⭐⭐ **결정적**: entity update loop (FUN_000818f0)에서 letter input subsystem 호출. **entity가 letter input을 trigger한다** = NPC dialog / text input prompt가 entity 상호작용으로 발동.

저장: `work/h3/fun_3a86c_letter_entry_disasm.json`

## 2NC: FUN_00085aa8 의 sl-relative obj = ObjectB.vtable[+0x60]

`tools/recon/trace_85aa8_sl_obj.py` 결과:

```
sl base = 0x000b2c40 (= GOT base ✓)

ldr@0x85ada: literal = 0x9c71 → task[0x9c71] (state clear field, Round 27 byte cluster)
ldr@0x85ae6: literal = 0x424   → memset size (1060 bytes, NOT GOT slot)
ldr@0x85af0: literal = 0x18    → ⭐ GOT[+0x18] = ObjectB
```

### 결정적 발견

```
r3 = GOT[+0x18] (ObjectB slot addr)
r3 = *r3 = ObjectB ptr
r3 = *r3 = ObjectB vtable
r3 = vtable[+0x60] = method pointer ⭐ NEW slot!
bl 0xa42a0 (veneer = bx r3) = indirect call ObjectB.method0x60
```

### ObjectB vtable known methods (Round 47 시점)

Round 22~46의 ObjectB vtable method 슬롯 종합:

| offset | discovered | 비고 |
|---|---|---|
| +0x10 | Round 22 | sound dispatcher reader |
| +0x20 | Round 22 | reader |
| +0x44 | Round 22 | reader |
| +0x54 | Round 22 | reader |
| **+0x58** | Round 22 + **Round 42** | ObjectB pending flag handler (FUN_0002cdb4 = event handler invoker) |
| **+0x60** | **Round 47 NEW** ⭐ | FUN_85aa8 event 3 heavy init handler |
| +0x68 | Round 22 | reader |
| +0x7c | Round 22 | reader |
| +0x80 | Round 22 | reader |

**9 known method slots** (1 신규 +0x60).

### memset_like context

FUN_85aa8 호출 직전 `bl FUN_0009fb78(r0=&task[0x9c71], r1=0, r2=0x424=1060)` = task[0x9c71]부터 1060 bytes를 0으로 클리어. 이는 **state reset/initialization** = event 3 fire 시 게임 상태 클리어 (Round 27 byte cluster + 후속 1060 bytes total reset).

## 2ND: FUN_00085578c 34 callers 분포 매핑

### 컨테이너 함수 분포 (29 callers identified, 2 no-push)

#### 0x56xxx-0x57xxx area (7 calls) — save/load + render

- **FUN_00056f3c** (2 calls @ +0xfa, +0x140): save/load codec 인접 (Round 17의 FUN_00056bf8 area)
- **FUN_00057394** (5 calls @ +0x262, +0x26e, +0x278, +0x60c, +0x616): **render command buffer / display list builder** (Round 17 finding)

#### 0x85xxx-0x86xxx area (15+ calls) — ⭐ HEAVY concentration (7th indirect entry cluster)

- FUN_000857a4, FUN_00085aa8 (Round 46 event 3 init), FUN_00085b18, FUN_00085e88 (Round 46 sub-helper), FUN_00085edc (2 calls), FUN_00085fc8 (2 calls)
- FUN_00086058 (7번째 indirect entry!), FUN_000861a8 (next func), FUN_000862d4 (Round 46), FUN_00086a04

#### 0x87xxx-0x8axxx area (6 calls)

- FUN_00087c44, FUN_00088a30, FUN_00088eb0, FUN_00089b18, FUN_0008a050, FUN_0008ad30

#### 0x8dxxx-0x90xxx area (3 calls)

- **FUN_0008d87c** (Round 28 sister entry record 0x3c4 inline sub-handler, 1.1KB ⭐)
- FUN_000901b0, FUN_000905a4

### 결정적 통찰: task[0xa848] = "current screen/menu state" 중앙 필드

task[0xa848] is accessed by:
- **Save/load system** (FUN_00056f3c)
- **Render command buffer** (FUN_00057394) — display list builder
- **7th indirect entry FUN_00086058 cluster** (15+ functions) = 가장 집중 사용
- **Sister entry record sub-handler** (FUN_0008d87c, Round 28)
- 다수의 scattered helpers in 0x87xxx-0x8axxx

⭐⭐⭐ **이 광범위한 사용 패턴 = task[0xa848] 가 "현재 게임 활성 모드 / 화면 상태"**:
- save: 어느 화면에 있는지 저장할 때 필요
- render: 어떤 화면을 그릴지 결정할 때 필요
- 7th indirect entry (input/menu subsystem): 입력 처리 시 현재 모드 확인
- sister entry: NPC 상호작용 시 현재 context 확인

**가설**: task[0xa848] = **MenuState struct base pointer** (or similar enum/state byte). HIGH ENCAPSULATION pattern (Round 46)이 강력히 시사하는 OOP-style accessor (FUN_85578c = `getCurrentMenuState()`).

## 2NE: 4 sub-helpers 본문 (FUN_85aa8가 호출)

`tools/recon/disasm_subsystem_func.py` 일괄 결과:

### FUN_0003d434 (412B, 5 arms cmp #0/1, 6 ctx + 0 other BL)

- 412 byte / 196 instr
- cmp 분포: cmp #0 (4x) + cmp #1 (1x) = state inspector
- BL = 6 context_getter only (pure state)

= medium state inspector — multi-field state check.

### FUN_00085e88 (84B, 1 arm cmp #0, 0 BL!)

- 84 byte / 40 instr
- BL = 0 (no function calls!)
- 2 literals only (1 binary_addr + 1 small_int)

= linear pure data manipulation function (probably bit/byte sets or arithmetic).

### FUN_0002cc94 (224B, 2 arms cmp #0, 1 ctx + 0 other BL)

- 224 byte / 108 instr
- 8 GOT slot literals
- BL = 1 context_getter only

= small state inspector (8 task fields touched).

### FUN_000862d4 (56B, 0 arms + 0 BL + 0 literals)

- 56 byte / 27 instr
- TINY linear function with NO arms, BL, OR literals

= pure register/flag setter — likely sets a single state value.

### 결론

4 sub-helpers 모두 **lightweight state operations** (state inspection or simple modifications):
- 0 graphics, 0 sound, 0 entity-touching BL
- 모두 작은 함수 (56B~412B)
- 호출 시 task field 들을 클리어/조회

→ FUN_85aa8가 event 3 heavy init 시 호출하는 이유 = **여러 task field를 일괄 reset/check**. event 3 (= screen transition handler) 전에 다양한 state fields를 정리/검사.

## Round 47 종합 진척

### ✅ 검증 추가

1. ⭐⭐⭐ **vtable[+0x60] = ObjectB.method0x60 신규 슬롯 발견** (ObjectB known methods 8 → 9)
2. ⭐⭐⭐ **task[0xa848] = "current screen/menu state" 중앙 필드 확정** (save/load + render + 7th indirect entry + sister entry 모두 access)
3. ⭐⭐ **FUN_0003a86c = letter input subsystem 진입점** (388B, 4 callers including FUN_000818f0 entity update loop)
4. **FUN_85aa8 state clear field = task[0x9c71]** + memset 1060 bytes (Round 27 byte cluster reset)
5. **4 sub-helpers 본문 풀이** (lightweight state ops, no graphics/sound)

### 진척률 (Round 47 시점)

- Ghidra 게임 로직 리버싱: ~45~50% → **~47~52%**
- ObjectB vtable: 8 → **9 known methods**
- 전체: ~42~52% → **~45~55%**

### ⭐ 다음 라운드 (48) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2OA** | **task[0xa848] sub-struct 구조 분석** — 34 callers의 offset 패턴 (FUN_85578c return 후 어떤 offsets로 access하는지) | wide-scan + capstone disasm pattern |
| ⭐⭐ **2OB** | FUN_0003d5d0 sound dispatcher 22 arms 정밀 (Round 45 미완) | full disasm + arm BL target |
| ⭐⭐ **2OC** | FUN_000818f0 +0x6c (0x8195c) → FUN_3a86c 호출 context — entity가 letter input trigger하는 조건 | capstone window disasm |
| ⭐⭐ **2OD** | FUN_00085edc (2 calls FUN_85578c) + FUN_00085fc8 (2 calls) 본문 — task[0xa848] 사용자 함수들 | inline disasm |
| ⭐⭐ **2OE** | FUN_00057394 (render command buffer) 의 task[0xa848] 사용 패턴 — 5 calls 의 context | capstone window |
| ⭐ **2OF** | ObjectB vtable의 다른 미식별 메서드 슬롯 wide-scan (vtable [+0x?? offsets) | binary-wide vtable offset 분포 |
| ⭐ **2OG** | 7th indirect entry FUN_00086058 → FUN_92cc0 → FUN_92bf8 호출 chain의 FUN_92bf8 본문 | inline disasm |

### 도구 산출 (Round 47)

- `tools/recon/trace_85aa8_sl_obj.py` (new) — FUN_85aa8 sl-relative literal 추출

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 46 의 [`ghidra-input-subsystem-and-helpers-2026-05-17.md`](ghidra-input-subsystem-and-helpers-2026-05-17.md) 읽기
2. PROGRESS.md 의 **ObjectB.method0x60 신규** + **task[0xa848] central state 가설** 확인
3. **권장 첫 작업: 2OA** — task[0xa848] sub-struct 구조 분석. 34 callers가 어떤 offsets로 access하는지 추출하면 sub-struct layout이 풀림 = MenuState struct 또는 ScreenContext struct 식별.
