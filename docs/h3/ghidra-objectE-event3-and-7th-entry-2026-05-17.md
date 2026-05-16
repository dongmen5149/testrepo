# Hero3 Ghidra — Round 44 / 2026-05-17 PM-8 (event 3 = ObjectE.method0x10 + 7th indirect entry 발견)

> Round 43 (`ghidra-event-id-mapping-2026-05-17.md`) 의 후속 — event 3 specific path 의 graphics object 정체 + event 3 helpers + 신규 indirect entry 발견.

## 한 줄 요약

⭐⭐⭐ **event 3 = ObjectE.method0x10(0xb0, 0xa0) 호출 확정** — sl-relative literal 추출로 GOT[+0x78] = ObjectE (Round 42 식별) 의 vtable [+0x10] graphics 메서드 호출. ⭐⭐⭐ **task_struct[0xac78] (38B entity state record, Round 28) 가 event 3 path 에서 2회 참조** = **entity state record (Round 28) ↔ ObjectE 의 graphics 메서드 = KEY LINK 발견**. entity update loop → event 3 → ObjectE.method0x10 = entity 상태 변화가 screen transition / overlay 발동. ⭐⭐⭐ **FUN_00086058 = 7번째 indirect entry 후보** (336B, 0 BL caller, pure-state 6 ctx, +0x6a 에서 event 3 fire) → **시스템 진입점 6 → 7개 확장 가능성**. ⭐⭐ **FUN_00053e08 = command/key input handler** (2112B, 21 arms, cmp 'c' 4x, 44 ctx + 1 other, dynamic event source = NPC arg+7). event 3 dedicated helpers (FUN_00081744 + FUN_00081688) 본문 = small state inspectors.

## 2KA: event 3 specific path 의 sl-relative graphics obj 정체

### sl-relative literal 추출 결과

`tools/recon/trace_event3_sl_global.py` 출력:

```
sl base = 0x000b2c40 (= GOT base ✓ Round 23+33+42)

event 3 specific path sl-relative literals:
  ldr@0x2c84e: 0xac78  → task[0xac78] (entity state record, Round 28!)
  ldr@0x2c85c: 0x0078  → ⭐⭐⭐ GOT[+0x78] = ObjectE (Round 42)
  ldr@0x2c870: 0x0140  → GOT[+0x140] = ObjectE pending flag ptr
  ldr@0x2c88a: 0x0078  → GOT[+0x78] = ObjectE (재참조)
  ldr@0x2c892: 0x0140  → GOT[+0x140] = ObjectE pending flag (재참조)
  ldr@0x2c8aa: 0x0074  → GOT[+0x74] = ObjectE 인접
  ldr@0x2c8f6: 0xac6c  → task[0xac6c] (38B entity record 인접)
  ldr@0x2c90c: 0x9c71  → task[0x9c71] (byte cluster, Round 27)
  ldr@0x2c91a: 0xac78  → task[0xac78] (38B entity record, 2회 참조!)
  ldr@0x2c92e: 0xac7a  → task[0xac7a] (38B entity record 인접)
```

### 결정적 발견 1: event 3 = ObjectE.method0x10 graphics 호출

```
0x2c85c: ldr r3 = GOT[+0x78] (ObjectE ptr address)
0x2c860: ldr r3, [r3]                       ; r3 = *(GOT[+0x78]) = ObjectE pointer value
0x2c862: ldr r3, [r3]                       ; r3 = *ObjectE = vtable
0x2c864: ldr r3, [r3, #0x10]                ; ⭐ r3 = vtable[+0x10] = method function pointer
0x2c866: movs r0, #0xb0                     ; r0 = 0xb0 (= 176)
0x2c868: movs r1, #0xa0                     ; r1 = 0xa0 (= 160)
0x2c86a: bl 0xa42a0                         ; veneer = bx r3 (indirect call!)
                                              => ObjectE.vtable[+0x10](0xb0, 0xa0)
```

= **ObjectE.method0x10(x=176, y=160) graphics call**.

### 결정적 발견 2: entity state record ↔ ObjectE 연결

⭐⭐⭐ **task_struct[0xac78] (Round 28 의 38B entity state record) 가 event 3 path 에서 2회 참조** (0x2c84e + 0x2c91a).

추가 entity record 인접 fields:
- task[0xac6c] @ 0x2c8f6
- task[0xac7a] @ 0x2c92e

= **entity state record (Round 28) 와 ObjectE 가 같은 핸들러에서 사용** = **KEY ARCHITECTURAL LINK**.

### 전체 chain 가설 (검증된 사실 + 추론)

```
[entity update loop FUN_000818f0 - Round 28, 5.6KB]
    └─ task_struct[0xac78~0xac9d] = 38B entity state record 갱신 (200+ access)
    └─ JT dispatch 직후: movs r0, #3; bl FUN_0002c6a4         ← Round 43 발견
       ↓
[FUN_0002c6a4 event dispatcher - Round 41]
    └─ event_id=3 → (3-3)=0 → cmp #0 beq → specific path 0x2c848 ← Round 43
       ↓
[event 3 specific path 0x2c848 - Round 43+44 풀이]
    └─ task[0xac78] read (entity state record!)                ← Round 44
    └─ ObjectE.vtable[+0x10](0xb0, 0xa0) ← graphics call        ← Round 44 ⭐⭐⭐
    └─ sound_trigger 0x20 + 0x7 (Round 43 신규)
    └─ state byte transitions 2 → 0 → 1
```

⭐⭐ **ObjectE 정체 정밀화**: 0xDxxx 영역 (FUN_00006334 main state machine, Round 17) 의 46 sites 집중 사용 + entity state record (0xac78) 와의 연결 = **"entity-driven screen transition / overlay renderer"**. method [+0x10] 이 좌표 인자 (0xb0, 0xa0) 를 받음 = 명백한 graphics primitive.

## 2KB: event 3/15 dedicated helpers

### FUN_00081744 (event 3 exclusive helper, 428B)

- 1 BL caller: 0x2c902 (event 3 path 안에서만)
- 2 cmp arms: cmp #0 + cmp #5
- BL = 1 context_getter only
- 8 PC-rel literals (4 GOT slot offsets + 2 medium + 1 binary + 1 small)
- 바로 다음 함수 = **FUN_000818f0 (entity update loop)** = 메모리 인접 (interesting layout)

→ **event 3 의 byte arg processing helper** (input r0 = byte from task field 0x2c8f2 사이트 from event 3 path)

### FUN_00081688 (event 15 exclusive helper, 188B)

- 1 BL caller: 0x2c954 (event 15 path 안에서만)
- 2 cmp arms: cmp #0 (2x)
- BL = 4 context_getter only
- 11 PC-rel literals

→ **event 15 의 task field walker** (4 ctx_getter 로 여러 fields 순차 점검)

### 결론

두 helper 모두 single-caller dedicated → event 3 / event 15 의 sub-routine 으로 묶여 있음.

## 2KC: event 3 다중 helpers (FUN_00024a6c + FUN_0002cb78)

### FUN_00024a6c (788B)

- 5 BL callers: 0x249aa, 0x2af7c, 0x2b622, **0x2c8e2** (event 3 path), **0x2c8e8** (event 3 path)
- = **event 3 path 에서 2번 호출** (alternative branches: 0x2c8e2 + 0x2c8e8)

### FUN_0002cb78 (284B)

- 4 BL callers: **0x2c8ec** (event 3 path), 0x48c70, 0x859e6, 0x93ae2
- = event 3 + 3개의 다른 system caller

두 함수의 정확한 본문 분석은 Round 45+ 작업.

## 2KD: event 3 trigger functions (FUN_00086058 + FUN_000933e8)

### ⭐⭐⭐ FUN_00086058 = 7번째 indirect entry 후보 (336B)

- 4 cmp arms: cmp #0/1/1/2 (4-way state dispatch, range guard `cmp #1 bhi`)
- BL = **6 context_getter + 0 other** (pure-state, no graphics/sound)
- **6 ctx 모두 `r0=#3` 일관** = 동일한 field index 3 hardcoded 사용
- **0 BL callers** ⭐⭐⭐
- +0x6a (0x860c2) 에서 event 3 fire (Round 43 확정)

### 후보 판단 근거

- 0 BL callers (FUN_000245fc 와 같은 패턴, Round 38)
- pure-state profile (6 ctx + 0 other BL — 표준 indirect entry 시그니처)
- Event 시스템 직접 트리거 (event 3 fire)
- Small size (336B, FUN_000245fc 388B 와 유사 범위)
- state dispatch on r3 (0/1/2)

→ **FUN_00086058 이 indirect entry function 이면 시스템 진입점 7개로 확장**:
```
1. FUN_0006619c    paint/tick callback
2. FUN_00070f34    key handler
3. FUN_0008b2e8    sister entry / NPC
4. FUN_0008dcd8    main entry / scene
5. FUN_000241dc    system event dispatcher (74-entry JT)
6. FUN_000245fc    NPC subsystem (cluster #1 entry, Round 38)
7. FUN_00086058    NEW (Round 44 후보, state-dispatch 0/1/2 + event 3 source)
```

Round 45 작업: FUN_00086058 의 6 ctx `r0=#3` literals 정밀 분석 + 실제 호출 패턴 검증.

### FUN_000933e8 (156B, 1 caller)

- 2 cmp arms: cmp #0x1f (31), cmp #0xe (14)
- BL = 7 context_getter + 0 other (state inspector)
- 1 BL caller: 0x933ac (자체 영역 별도 함수)
- +0x6c 에서 event 3 fire

→ **state inspector**, NOT indirect entry (1 BL caller 있음).

## 2KE: FUN_00053e08 = command/key input handler (2112B)

### 프로파일

- 2112B, 990 instructions, **21 cmp arms**
- cmp 분포: cmp #0 (6x), **cmp #0x63 ('c') 4x** ⭐ 'c' character detection!
- 기타 cmp: #0x12, #0x10, #0x04, #0x03, #0x01, #0x08, #0x02, #0x13, #0x07, #0x05 (=wide range)
- BL = **44 context_getter + 1 other** (HEAVY task_struct reader)
- cmp #0x10 bls = 16 range guard

### dynamic event source 확정

Round 43 발견: 이 함수의 +0x2be (0x540c6) 에서 `r3 = halfword[task+0x3b8] + 7` 계산 후 bl FUN_0002c6a4.

⭐⭐ **추정 정체**: **command / text input processor** — cmp 'c' (4회) 가 키 'c' 또는 명령 문자 'c' 검출 = menu/dialog 입력 처리. NPC record 의 +0x3b8 short (Round 14 = "arg short") 를 읽어 dynamic event_id 생성.

3 BL callers: 0x3cad6, 0x3ce22, 0x430d6 (모두 0x3Cxxx/0x43xxx 영역) — Round 45+ 에서 caller context 분석.

## 2KG: 신규 sound IDs 자산 매핑 (부분)

### 자산 폴더 구조 (33 files)

- 19 BGM files: bgm0_mf .. bgm18_mf
- 14 SFX files: sd000_mf .. sd013_mf

### sound_id 추정 매핑

| sound_id | 추정 매핑 | 비고 |
|---|---|---|
| 0x07 | bgm7_mf (BGM 7) | direct file 0-indexed 가설 |
| 0x20 (32) | 33-file 범위 밖 | sound dispatcher internal table mapping 필요 |

⭐ FUN_0003d5d0 (sound dispatcher, 22 cmp arms, Round 22) 의 jump table 정밀 분석이 정확한 mapping 위해 필요. Round 22 의 기존 분석은 sound dispatcher 구조만 식별, sound_id → file 매핑은 미완.

## Round 44 종합 진척

### ✅ 검증 추가

1. ⭐⭐⭐ **event 3 = ObjectE.method0x10(0xb0, 0xa0) graphics call 확정** (Round 42 ObjectE 식별 + Round 43 event 3 풀이 + Round 44 sl-relative literal 추출 = 3 round 누적 검증)
2. ⭐⭐⭐ **entity state record (task[0xac78], Round 28) ↔ ObjectE 연결 발견** — KEY architectural link
3. ⭐⭐⭐ **FUN_00086058 = 7번째 indirect entry 후보** (336B, 0 BL caller, pure-state, event 3 source) — Round 45 검증 필요
4. ⭐⭐ **FUN_00053e08 = command/key input handler** (2112B, 21 arms, cmp 'c' 4x, 44 ctx, dynamic event source)
5. ⭐ FUN_00081744 / FUN_00081688 = event 3 / 15 dedicated single-caller helpers
6. ⭐ FUN_000933e8 = state inspector (156B, NOT indirect entry, 1 caller)
7. ⭐ sound asset 구조 = 19 BGM + 14 SFX (33 total)

### 진척률 (Round 44 시점)

- Ghidra 게임 로직 리버싱: ~38~45% → **~40~47%**
- 전체: ~35~45% → **~37~48%**

### ⭐ 다음 라운드 (45) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2LA** | **FUN_00086058 indirect entry 검증** — `r0=#3` literal 의 GOT 슬롯 위치 + caller 패턴 정밀 (BX register / movt 등 비표준 caller 검색) | trace_event3_sl_global 패턴 재사용 + 정밀 caller scan |
| ⭐⭐ **2LB** | FUN_0003d5d0 sound dispatcher 22 arms 매핑 — sound_id → snd/ 파일 정확한 mapping | inline disasm + arm 별 BL target 추적 |
| ⭐⭐ **2LC** | FUN_00024a6c (788B) 본문 — event 3 path 의 2 calls + 다른 system contexts | inline disasm |
| ⭐⭐ **2LD** | FUN_0002cb78 (284B) 본문 — event 3 + 3 외부 caller helper | inline disasm |
| ⭐⭐ **2LE** | FUN_00053e08 의 3 callers (0x3cad6/0x3ce22/0x430d6) 분석 — command input flow | container 분석 |
| ⭐ **2LF** | ObjectE vtable 의 다른 메서드 슬롯 (사용 패턴 wide-scan) — Round 42 의 [+0x10]/[+0xc]/[+0x58] 외 | binary-wide vtable offset 분포 |
| ⭐ **2LG** | task[0xac78~0xac9d] (38B entity record) 의 모든 system-wide reader/writer 매핑 | wide-scan |

### 도구 산출 (Round 44)

- `tools/recon/trace_event3_sl_global.py` (new) — event 3 path sl-relative literal 추출

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 43 의 [`ghidra-event-id-mapping-2026-05-17.md`](ghidra-event-id-mapping-2026-05-17.md) 읽기
2. PROGRESS.md 의 **event 3 = ObjectE.method0x10** + **FUN_00086058 7번째 indirect entry 후보** 확인
3. **권장 첫 작업: 2LA** — FUN_00086058 의 정밀 검증. indirect entry 확정되면 game update flow 가 6 → 7 indirect entries 로 확장, 시스템 모델 완성도 크게 증가.
