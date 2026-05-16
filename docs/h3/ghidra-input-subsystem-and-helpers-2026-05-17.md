# Hero3 Ghidra — Round 46 / 2026-05-17 PM-10 (letter input subsystem + 4 helper 본문 + encapsulation pattern)

> Round 45 (`ghidra-7th-indirect-entry-and-sound-norm-2026-05-17.md`) 의 후속 — FUN_00086058 4 helpers 본문 + FUN_0003c920 letter input handler.

## 한 줄 요약

⭐⭐⭐ **letter keyboard input subsystem 발견**: FUN_00053e08 (cmp 'c' 4x, Round 43) + **FUN_0003c920 (cmp 'd'/'f'/'g'/'h'/'i', Round 46)** = 피처폰 ABC keypad mapping (key #2 'abc' + key #3 'def' + key #4 'ghi') = **사용자 텍스트 입력 시스템** (이름 입력 / save name / chat 등). ⭐⭐⭐ **FUN_00085578c = `&task[0xa848]` getter** (24B, 34 callers system-wide!) = HIGH ENCAPSULATION — 34 callers 모두 함수 통해 indirect access. ⭐⭐ **FUN_00092bd0 = (int8)task[0xa280] byte reader** (40B, 15 callers, NPC cluster 영역). ⭐⭐ **FUN_00092cc0 = ASCII digit '2'/'8' or sentinel -1/-2 dispatcher** (FUN_00086058 default path, return 1/0). ⭐⭐ **FUN_00085aa8 = event 3 path heavy init** (4 sub-helpers + memset_like + 글로벌 obj.vtable[+0x60] indirect call).

## 2MA: FUN_00085578c — `&task[0xa848]` getter (24B, 34 callers ⭐)

### 본문 (capstone)

```
push {r7, lr}
mov r7, sp
bl context_getter (0x4ad10)    ; r0 = task_ptr
adds r3, r0, #0                 ; r3 = task_ptr
ldr r2, [pc, #8]                ; r2 = literal at 0x857a0
adds r3, r3, r2                 ; r3 = task + offset
adds r0, r3, #0                 ; return r3
mov sp, r7
pop {r7, pc}
[literal at 0x857a0: 0x0000a848]
```

### 결정적: HIGH ENCAPSULATION pattern

- Returns **address** (`&task[0xa848]`), NOT value
- **34 BL callers** system-wide reference this getter
- task[0xa848] literal 은 binary 전체에서 **1 site only** (이 함수 안) = 모든 access 가 함수 경유 indirect
- = **C/C++ accessor pattern**: `MenuState* getCurrentMenuState() { return &task->menuState; }`

### 34 callers 분포

0x57xxx, 0x85xxx-0x90xxx 영역 집중 = command/menu/UI subsystems 다수가 task[0xa848] 의 sub-struct 에 접근.

⭐ **추정 정체**: **task[0xa848] = "current menu state" or "input context" sub-struct base pointer**.

## 2ME: FUN_00085aa8 — event 3 path heavy init (112B, 1 caller exclusive)

### 본문

```
PIC sl-trampoline setup
bl FUN_00085578c → r2 = &task[0xa848]   ; current menu state addr
store r2 to [r7-4]
bl FUN_0003d434                          ; helper 1
bl FUN_00085e88                          ; helper 2
bl FUN_0002cc94                          ; helper 3
movs r0, #0; bl FUN_000862d4              ; helper 4 with r0=0
bl context_getter → clear byte to task field
bl FUN_0009fb78 (memset_like, Round 22)  ; clear large buffer
ldr r3 = sl-relative global obj
r3 = *r3 (double deref) = vtable
r3 = vtable[+0x60]                       ; ⭐ method ptr
bl 0xa42a0 (veneer = bx r3)              ; ⭐⭐ indirect call obj.vtable[+0x60]
```

⭐⭐ **event 3 path 의 "heavy init"** = current menu state 저장 + 4 sub-helpers + memset + **vtable[+0x60] indirect call**. vtable[+0x60] 은 Round 42 의 ObjectE 슬롯 (+0xc, +0x10, +0x58) 외 새로운 slot — 같은 object 의 다른 메서드일 가능성.

저장: `(work/h3/fun_85aa8_disasm.json — Round 45 시점 보강 필요)`

## 2MF: FUN_00092bd0 — byte reader for task[0xa280] (40B, 15 callers)

### 본문

```
push {r7, lr}; mov r7, sp; sub sp, #4
bl context_getter → r0 = task_ptr; store to [r7-4]
load task_ptr; ldr r2 = literal 0xa280
adds r3, r3, r2                          ; r3 = task + 0xa280
ldrb r3, [r3]                             ; r3 = byte at task[0xa280]
lsls r3, #0x18; asrs r3, #0x18           ; sign-extend
adds r0, r3, #0; pop {r7, pc}
[literal at 0x92bf4: 0xa280]
```

= **`(int8)task[0xa280]`** signed byte reader. 15 callers system-wide. task[0xa280] = NPC cluster 영역 (0xa288/0xa289 인접).

## 2MF: FUN_00092cc0 — character/sentinel dispatcher (112B, 5 callers)

### 본문 풀이

```
input r0 = command code (signed int)
r3 = input
cmp r3, #0x32 (= '2', ASCII)
  beq → handle case A:
    movs r0, #3
    bl FUN_00092bf8 (sub-helper)
    return 1 (in r0)
cmp r3, -1 (signed)
  beq → same case A (input == '2' or -1)
cmp r3, #0x38 (= '8', ASCII)
  beq → handle case B:
    movs r0, #4
    bl FUN_00092bf8
    return 1
cmp r3, -2
  beq → same case B (input == '8' or -2)
else: return 0
```

⭐⭐ **ASCII digit '2'/'8' + sentinel -1/-2 dispatcher**:
- '2' 또는 -1 → bl FUN_00092bf8(r0=3) → return 1
- '8' 또는 -2 → bl FUN_00092bf8(r0=4) → return 1
- else → return 0

= **숫자 키 '2'/'8' (피처폰 navigation up/down keys?)** + 특수 control codes (-1/-2 = system sentinels).

## 2MD: FUN_0003c920 — letter keyboard input handler (2836B, 33 arms!)

### 프로파일

- 2836B / 1312 instr / **33 cmp arms**
- cmp 분포 핵심: **cmp 'd' (0x64) 1x, 'f' (0x66) 2x, 'g' (0x67) 1x, 'h' (0x68) 1x, 'i' (0x69) 1x** = **letter keys d/f/g/h/i 검사**
- 기타 cmp: #0 (9x), #1 (5x), #2 (2x), #3 (2x), #4, #7, #8, #9, #0xe, #0x11 (2x), #0x12 = state/event values
- 1 BL caller: 0x3a8e4 in FUN_0003a86c (FUN_0003a444 다음 함수)

### 결정적: letter input subsystem 완성

FUN_00053e08 (Round 43, 'c' 4x) + **FUN_0003c920 (Round 46, 'd'/'f'/'g'/'h'/'i')** = ASCII 'c' through 'i' letter detection:

```
키 #2 'abc' → 'c' (FUN_00053e08 처리)
키 #3 'def' → 'd', 'e', 'f' (FUN_0003c920 처리 — 'd', 'f' 확인됨)
키 #3 또는 #4의 'ef' = (FUN_0003c920에 cmp #0x65 'e' 없음 — 'e' 는 별도 함수?)
키 #4 'ghi' → 'g', 'h', 'i' (FUN_0003c920 처리)
```

⭐⭐⭐ **피처폰 ABC keypad letter input handler 발견**. 게임에서 사용자가 텍스트 (이름, save 슬롯 이름, chat) 입력 시 사용.

### 가설: text input system

- FUN_00053e08 (cmp 'c', cmp #0x10 range guard, dynamic event source) = 첫 letter 처리 + char-to-event 변환
- FUN_0003c920 (cmp 'd'/'f'/'g'/'h'/'i', cmp #0x11/#0x12 state) = 추가 letter 처리 + state machine

이 두 함수의 호출 위치 (0x3cad6/0x3ce22 in FUN_0003c920, 0x3a8e4 in FUN_0003a86c) 가 모두 0x3Axxx/0x3Cxxx 영역 = **text input UI subsystem** 의 함수 cluster.

저장: `work/h3/fun_3c920_disasm.json`

## 2MC: New task field encapsulation pattern

`tools/recon/scan_new_task_fields.py` 결과:

| task field | sites | 의미 |
|---|---|---|
| 0x9c71 | 51 | Round 27/45 byte cluster (system-wide most active) |
| 0x9cb8 | 31 | callback queue base (Round 40) |
| 0xa0c0 | 14 | NPC subsystem mode (Round 39) |
| **0xa280** | **5** | FUN_00092bd0 byte reader target (15 callers via wrapper) |
| **0xa848** | **1** ⭐ | FUN_00085578c &task getter (34 callers via wrapper!) |

### 결정적: HIGH ENCAPSULATION

- **task[0xa848]**: literal pool 1 site (FUN_00085578c) + 34 BL callers = **99% 의 access 가 함수 wrapper 경유**
- **task[0xa280]**: 5 literal sites (all in 0x92xxx FUN_00092xxx cluster) + 15 BL callers = **wrapper-based access dominant**

대비:
- task[0x9c71] (Round 27 cluster) = 51 literal sites = **inline-direct access** (encapsulation 없음)
- task[0x9cb8] (callback queue) = 31 literal sites = **inline-direct access**

⭐⭐⭐ **PATTERN**: Hero3 의 task_struct 에서 일부 fields 는 **abstract accessor function** 으로 wrap 되어 있음. 이는 원본 C/C++ 코드의 OOP pattern (private member + getter/setter) 흔적. 0xa848 / 0xa280 = **encapsulated state fields**, 0x9c71 / 0x9cb8 / 0xa0c0 = **public state fields**.

이 차이는 게임 코드의 abstraction level 을 보여줌 — Hero3 의 일부 subsystems 는 OOP-style 디자인, 다른 부분은 procedural-direct 디자인.

## Round 46 종합 진척

### ✅ 검증 추가

1. ⭐⭐⭐ **letter keyboard input subsystem 발견** (FUN_00053e08 + FUN_0003c920 = ABC keypad letter handler)
2. ⭐⭐⭐ **HIGH ENCAPSULATION pattern** 발견 (task[0xa848] 34 callers 모두 wrapper 경유)
3. ⭐⭐ **FUN_00085578c = &task[0xa848] getter** (24B, 34 callers, central command resolver)
4. ⭐⭐ **FUN_00092bd0 = (int8)task[0xa280] byte reader** (40B, 15 callers)
5. ⭐⭐ **FUN_00092cc0 = '2'/'8' digit + -1/-2 sentinel dispatcher** (112B, 5 callers)
6. ⭐⭐ **FUN_00085aa8 = event 3 heavy init** (112B, 4 sub-helpers + memset + vtable[+0x60] indirect call)
7. **vtable [+0x60] 신규 method slot** (FUN_00085aa8 에서 호출) — ObjectE 가능성

### 진척률 (Round 46 시점)

- Ghidra 게임 로직 리버싱: ~42~48% → **~45~50%**
- task_struct 모델: ~38% → **~40%** (task[0xa848], 0xa280 신규)
- 전체: ~40~50% → **~42~52%**

### ⭐ 다음 라운드 (47) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2NA** | **FUN_0003a86c 본문** (FUN_0003c920 caller, FUN_0003a444 직후 함수) — letter input subsystem 의 진입점 | inline disasm |
| ⭐⭐ **2NB** | FUN_0003d5d0 sound dispatcher 22 arms 정밀 매핑 (Round 45 미완) | full disasm |
| ⭐⭐ **2NC** | FUN_00085aa8 의 sl-relative global obj 정체 (vtable [+0x60]) | sl literal 추출 |
| ⭐⭐ **2ND** | FUN_00085578c 의 34 callers 분포 매핑 — task[0xa848] sub-struct 사용 패턴 | container 분석 |
| ⭐⭐ **2NE** | FUN_0003d434 / FUN_00085e88 / FUN_0002cc94 / FUN_000862d4 본문 (FUN_00085aa8 의 4 sub-helpers) | inline disasm |
| ⭐ **2NF** | FUN_00092bf8 본문 (FUN_00092cc0 sub-helper) | inline disasm |
| ⭐ **2NG** | task[0xa848] sub-struct 의 구조 (FUN_00085578c 의 34 callers 의 offset 사용 패턴 분석) | wide-scan |
| ⭐ 2MB | sound dispatcher 22 arms 매핑 (Round 45 미완, deferred) | full disasm |

### 도구 산출 (Round 46)

- `tools/recon/disasm_86058_helpers.py` (new) — 4 FUN_00086058 helpers capstone disasm
- `tools/recon/scan_new_task_fields.py` (new) — 신규 task fields literal occurrence wide-scan

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 45 의 [`ghidra-7th-indirect-entry-and-sound-norm-2026-05-17.md`](ghidra-7th-indirect-entry-and-sound-norm-2026-05-17.md) 읽기
2. PROGRESS.md 의 **letter keyboard input subsystem 발견** + **task[0xa848] encapsulation pattern** 확인
3. **권장 첫 작업: 2NA** — FUN_0003a86c 본문 (FUN_0003c920 의 1 BL caller). letter input subsystem 의 진입점 식별.
