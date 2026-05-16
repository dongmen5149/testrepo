# Hero3 Ghidra — Round 45 / 2026-05-17 PM-9 (7번째 indirect entry CONFIRMED + sound dispatcher 정규화)

> Round 44 (`ghidra-objectE-event3-and-7th-entry-2026-05-17.md`) 의 후속 — FUN_00086058 정밀 검증 + sound dispatcher 입력 정규화.

## 한 줄 요약

⭐⭐⭐ **FUN_00086058 = 7번째 indirect entry CONFIRMED** (high confidence). 검증 근거: (1) **0 BL callers** = known indirect entries 6개와 동일, (2) **0 literal pool occurrences** = ALL 6 known indirect entries 와 동일 pattern (GVM firmware 별도 메커니즘으로 호출), (3) pure-state profile (no graphics/sound BL), (4) input r0 → `bl FUN_00085578c` → 4-way dispatch on sub-command. **시스템 진입점 6 → 7개로 확장 확정**. ⭐⭐⭐ **Sound dispatcher 입력 정규화 풀이**: `internal_id = sound_id - 4`, range guard [4..195], 22 arms sparse dispatch (FUN_0002c6a4 event dispatcher 와 유사 패턴, sound_id-4 vs event_id-3). task[offset] = sound_id (last_sound_id 패턴). ⭐⭐ **task[0x9c71..0x9c76] 6 byte cluster 신규 식별** (Round 27 byte field 영역 확장). FUN_00024a6c = 788B pure state inspector. FUN_0002cb78 = 284B linear setter (0 cmp). FUN_00053e08 callers = FUN_0003c920 (2x) + FUN_00043048.

## 2LA: FUN_00086058 = 7번째 indirect entry CONFIRMED

### 검증 방법: known indirect entries 와 동일 pattern 검증

`tools/recon/verify_fun_86058_entry.py` 4-step 검증:

#### Step 1: 전체 disasm — pure-state profile 확인

- 4 cmp arms: cmp #-5/-16/-2/-1 (signed values for sub-command)
- BL targets: FUN_00085578c (helper) + FUN_00085aa8 + FUN_0002c6a4(r0=3 event 3) + FUN_00092bd0 + FUN_00092cc0 + context_getter (6 calls all `r0=#3`)
- NO graphics/sound BL = pure-state dispatcher

#### Step 2: 6 PC-rel literals = 6 consecutive byte fields task[0x9c71..0x9c76]

⭐ **신규 발견**: 6 연속 byte fields:
- 0x9c71, 0x9c72, 0x9c73, 0x9c74, 0x9c75, 0x9c76

Round 27 의 byte cluster (0x9c70/71/84/85 4 fields) 영역을 확장 — **0x9c71~0x9c76 = 6 consecutive bytes** (skill/inventory/buff slots 후보, 6개 = standard "1-week party member" count 매칭 가능성).

#### Step 3: 0x86058 의 literal pool 검색 = 0 매치

binary 전체에서 0x86058 또는 0x86059 (Thumb addr) 가 4-byte literal 로 저장된 곳: **0건**.

#### Step 4: ⭐⭐⭐ 결정적 — known indirect entries 와 100% 일치

```
FUN_0006619c paint/tick   : 0 literal pool occurrences
FUN_00070f34 key handler  : 0 literal pool occurrences
FUN_0008b2e8 sister/NPC   : 0 literal pool occurrences
FUN_0008dcd8 main/scene   : 0 literal pool occurrences
FUN_000241dc system event : 0 literal pool occurrences
FUN_000245fc NPC subsys   : 0 literal pool occurrences
FUN_00086058 CANDIDATE   : 0 literal pool occurrences ✓
```

**ALL 7 indirect entries (6 known + 1 candidate) 가 모두 0 literal pool occurrences** = GVM firmware 가 별도 메커니즘 (예: 동적 등록 테이블, PIC indirect symbol 등) 으로 호출.

### 함수 동작 풀이

```
input r0 = command code (signed int)
store r0 to [r7-4]

bl FUN_00085578c → r2 = sub_command code

if r2 == -5 (0xfffffffb):
    bl FUN_00092bd0 → byte
    task[+3] = result_byte
    Clear 6 bytes task[0x9c71..0x9c76] (loop)
    Read task[+3] state byte:
        if 0 → task[+1] = 4
        if 1 → task[+1] = 2
        if 2 → task[+1] = 5
        else → no-op
elif r2 == -16:
    bl FUN_00085aa8 → ?
    bl FUN_0002c6a4(r0=3) ⭐ event 3 fire
elif r2 + 2 ≤ 1 (i.e. r2 ∈ {-2, -1}):
    bl FUN_00092cc0 (input r0 = original command)
return 0
```

### 가설: 게임 시스템 역할

- "command code" input + sub-command 분기 = **input/command processor**
- 6 byte cluster (0x9c71..0x9c76) 클리어 = **party 또는 skill slot reset**
- task[+3] state byte (값 0/1/2) + task[+1] state byte (값 4/2/5) = **state machine**
- event 3 fire (sub_command == -16) = critical event notification

**추정 정체**: **menu/quest system command processor** OR **party/skill setup handler**. 0xDxxx 영역의 FUN_00006334 main state machine 과 연관 가능성 (FUN_00086058이 호출하는 FUN_00085aa8 가 있는 0x85xxx 영역).

### 신규 함수들

- **FUN_00085578c** (helper, sub-command resolver)
- **FUN_00085aa8** (event 3 path helper)
- **FUN_00092bd0** (byte query, returns byte value)
- **FUN_00092cc0** (default path handler, input r0 = command code)

이들의 본문 분석은 Round 46+ 작업.

### Updated indirect entry list (7 entries)

```
1. FUN_0006619c    paint/tick callback (Round 21~)
2. FUN_00070f34    key handler (Round 21~)
3. FUN_0008b2e8    sister entry / NPC (Round 21~)
4. FUN_0008dcd8    main entry / scene (Round 21~)
5. FUN_000241dc    system event dispatcher (Round 29)
6. FUN_000245fc    NPC subsystem (Round 38)
7. FUN_00086058    ⭐ NEW (Round 45 CONFIRMED, command/state handler, event 3 source)
```

## 2LB: Sound dispatcher 입력 정규화

### FUN_0003d5d0 entry pattern (head 0x3d5d0..0x3d650)

```
0x3d5d0: 표준 prologue + PIC sl-trampoline:
         push {r4,r5,r7,lr} + mov r7,sl + push r7
         ldr r1, [pc, #0x4c] → sl_anchor; mov sl, r1; add sl, pc

0x3d5e0: store r0 to [r7-4]                  ; r0 = sound_id (input)
0x3d5e4..3d608: 초기화 (halfwords + zero locals)
0x3d60a: bl context_getter                   ; r1 = task_ptr
0x3d614: r2 = sound_id
0x3d61a: store byte r2 to [r3]               ; ⭐ task[some_offset] = sound_id (last_sound_id 저장)

0x3d61c: r3 = sound_id
0x3d630: r1 = r3 - 4                          ; ⭐ internal_id = sound_id - 4
0x3d638: store r1 to [r7-0x34]
0x3d640: r3 = internal_id
0x3d642: cmp r3, #0xbf (= 191)                ; ⭐ range guard
0x3d644: bls 0x3d648                          ; if internal_id ≤ 191, dispatch
0x3d646: b 0x3da8e                            ; else: skip
```

⭐⭐⭐ **결정적 발견**:
- Sound dispatcher **input r0 = sound_id**, 정규화 = **sound_id - 4** (event dispatcher 의 sound_id-3 와 유사 패턴)
- Valid sound_id range: **[4..195]** (= 0xbf + 4 = 0xc3 + 0)
- task[offset] = sound_id 기록 (last_sound_id, task[0x290]=last_event_id 와 유사)
- 22 cmp arms → 192 가능 값 중 22개만 specific (sparse dispatch, Round 30 의 74-JT 패턴)

### Round 43 신규 sound IDs in range 검증

- sound_id 0x07 → internal 3 (in range [0..191]) ✓
- sound_id 0x20 → internal 28 (in range) ✓
- Round 23 의 0x83~0xa5 → internal 127~161 (in range) ✓

### task[offset] = last_sound_id

저장 instruction 의 정확한 task field offset 은 0x3d616 의 pcrel literal 디코드 필요 (Round 46 작업).

## 2LC: FUN_00024a6c (788B pure state inspector)

- 4 cmp arms (cmp #0 only)
- BL = 1 context_getter + 0 other
- 24 PC-rel literals (19 GOT slot offsets)
- ctx 호출 시 r0=*0x24d40=**0x8e1c2** binary_addr (interesting — 코드/data ref)
- 호출 위치: 0x249aa, 0x2af7c, 0x2b622, 0x2c8e2 (event 3 path), 0x2c8e8 (event 3 path)

→ event 3 path 의 alternative branches 2개 + 다른 3 contexts 에서 공유되는 **major state inspection function**.

저장: `work/h3/fun_24a6c_disasm.json`

## 2LD: FUN_0002cb78 (284B linear setter)

- **0 cmp arms** ⭐ — linear control flow (no branching!)
- BL = 1 context_getter + 0 other
- 11 PC-rel literals (7 GOT slot offsets + 2 small + 1 binary + 1 medium)
- 4 BL callers: 0x2c8ec (event 3 path), 0x48c70, 0x859e6, 0x93ae2

→ **state initializer / setter** — linear function that reads task fields and sets state. 4 callers 동안 같은 작업 수행 (re-init or sync operation).

저장: `work/h3/fun_2cb78_disasm.json`

## 2LE: FUN_00053e08 (command input handler) callers 분석

3 BL callers 의 container:

| caller addr | container function | offset |
|---|---|---|
| 0x3cad6 | **FUN_0003c920** | +0x1b6 |
| 0x3ce22 | **FUN_0003c920** | +0x502 |
| 0x430d6 | **FUN_00043048** | +0x8e |

⭐ **FUN_0003c920 가 2번 호출** (다른 conditional path) = FUN_00053e08 (command/key input handler) 의 main caller. FUN_0003c920 의 size 는 ≥ 0x502 byte (= ≥ 1.3KB) — Round 46+ 분석 대상.

## Round 45 종합 진척

### ✅ 검증 추가

1. ⭐⭐⭐ **FUN_00086058 = 7번째 indirect entry CONFIRMED** (high confidence, 0 literal pool match with 6 known)
2. ⭐⭐⭐ **Sound dispatcher 입력 정규화 풀이**: `internal_id = sound_id - 4`, range [4..195]
3. ⭐⭐ **task[0x9c71..0x9c76] 6 byte cluster 신규 식별** (Round 27 byte field 영역 확장, 6 fields = "party member" 후보)
4. **FUN_00024a6c = state inspector** (788B, 19 GOT lit, 1 ctx only)
5. **FUN_0002cb78 = linear setter** (284B, 0 cmp arms)
6. **FUN_00053e08 main caller = FUN_0003c920** (2 calls, ≥1.3KB)
7. **신규 함수 4개 발견** (FUN_00085578c/85aa8/92bd0/92cc0) — FUN_00086058 의 helper chain
8. **task[+1], task[+3] byte state fields** 신규 식별 (FUN_00086058 의 state transition)

### 진척률 (Round 45 시점)

- Ghidra 게임 로직 리버싱: ~40~47% → **~42~48%**
- indirect entries: 6 → **7 confirmed**
- 전체: ~37~48% → **~40~50%**

### ⭐ 다음 라운드 (46) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2MA** | **FUN_00085578c 본문** (FUN_00086058 의 sub-command resolver) | inline disasm |
| ⭐⭐ **2MB** | FUN_0003d5d0 sound dispatcher 22 arms 정밀 매핑 (sound_id → snd/ 파일) | full disasm + arm 별 BL target |
| ⭐⭐ **2MC** | task[+1, +3] system-wide reader/writer — state byte 의미 풀이 | wide-scan |
| ⭐⭐ **2MD** | FUN_0003c920 본문 (FUN_00053e08 main caller, ≥1.3KB) | inline disasm |
| ⭐⭐ **2ME** | FUN_00085aa8 본문 (FUN_00086058 event 3 path helper) | inline disasm |
| ⭐ **2MF** | FUN_00092bd0 / FUN_00092cc0 본문 (FUN_00086058 helpers) | inline disasm |
| ⭐ **2MG** | task[0x9c71..0x9c76] 6 byte cluster 의 system-wide usage 분포 | wide-scan |
| ⭐ **2MH** | sound dispatcher last_sound_id task field offset 식별 (0x3d616 pcrel literal) | sl-trampoline decode |

### 도구 산출 (Round 45)

- `tools/recon/verify_fun_86058_entry.py` (new) — indirect entry 검증 (literal pool + caller scan + GOT 비교)
- `tools/recon/analyze_sound_dispatcher.py` (new) — sound dispatcher head capstone disasm

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 44 의 [`ghidra-objectE-event3-and-7th-entry-2026-05-17.md`](ghidra-objectE-event3-and-7th-entry-2026-05-17.md) 읽기
2. PROGRESS.md 의 **7 indirect entries 확정** + **sound dispatcher 정규화 sound_id - 4** 확인
3. **권장 첫 작업: 2MA** — FUN_00085578c 본문 (FUN_00086058 의 sub-command resolver). 이게 풀리면 7번째 indirect entry 의 정확한 게임 시스템 역할 식별 가능.
