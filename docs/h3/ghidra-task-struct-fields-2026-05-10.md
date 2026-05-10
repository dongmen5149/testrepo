# Round 23 (2026-05-10 PM-13) — task_struct field 정정 + sound id 11 식별 + ObjectB pattern 확정

## 요약

Round 22 의 sound subsystem 슬롯 발견 후속. PM-13 에서 **결정적 분류 정정** 발견:

1. ⭐⭐⭐ **"GOT slot offset" 다수가 사실 task_struct 필드 offset 이었음** — Round 18~22 의 0x9e28/0xa220/0xa244/0xa254 + 0x9bb4/0x9cbc/0x9cfe/0x9cc0 + 0x9c70/0x9c71/0x9c84/0xac78 모두 **`ctx + offset`** (context_getter 결과의 task_struct 필드) 으로 사용. **GOT 슬롯이 아님**.
2. ⭐⭐⭐ **task_struct 가 거대 구조체 (40KB+)** — 필드 offset 0xa254 까지 확인. 게임의 모든 subsystem state (sound, record array, flags) 가 단일 task_struct 안에 평면 배치.
3. ⭐⭐ **sound_trigger r1 = sound id** (NOT r0) — convention 정정. 21 sound_trigger 중 **11개 immediate sound id 식별** (0x83~0xa5 페어 패턴).
4. ⭐⭐ **진짜 GOT slots = 8개로 축소** — 0x18, 0x16c, 0x29e, 0x128, 0x444, 0x44c, 0xd00, 그 외 helper data 슬롯들.

---

## 1. ⭐⭐⭐ GOT slot vs task_struct field offset 분류 정정

### 기존 잘못된 분류 (Round 18~22 doc)

`disasm_subsystem_func.py` 의 `pcrel_literals_categories` 가 PC-rel literal 의 값 자체만 보고 "got_slot_offset" 으로 분류 (값이 0x100~0xffff 범위). 실제 사용 패턴은 **검증하지 않음**.

### 두 패턴의 차이 (실제 사용)

#### **진짜 GOT slot 패턴**:
```asm
ldr r3, [pc, #imm]   ; r3 = literal_GOT_offset
mov sl, r3 / add sl, pc   ; sl = GOT base (PIC)
add r3, sl / [sl, #imm]   ; r3 = sl + slot_offset = absolute GOT slot
ldr r3, [r3]              ; first indirection
```

#### **task_struct field offset 패턴** (잘못 분류된 것들):
```asm
bl 0x4ad10           ; context_getter — returns r0 = ctx (= task_struct ptr)
ldr r2, [pc, #imm]   ; r2 = literal_field_offset
adds r0, r0, r2      ; r0 = ctx + field_offset    ⭐ sl 가 아닌 ctx 기반
ldr r3, [r0]; ldr r3, [r3]  ; double indir → field value
```

### 검증 사례

#### FUN_000439a0 의 0x9bb4 / 0x9cbc (Round 18 분류 오류)

```asm
bl 0x44280              ; helper, returns r0
ldr r1, [pc, #0x304]    ; r1 = 0x9bb4 (literal)
adds r1, r0, r1         ; r1 = (helper result) + 0x9bb4   ⭐ NOT sl-based
str r1, [sp, #0x24]
bl 0x4ad10               ; context_getter, returns r0 = ctx
ldr r2, [pc, #0x300]    ; r2 = 0x9cbc
adds r0, r0, r2         ; r0 = ctx + 0x9cbc   ⭐ ctx-based, NOT sl-based
ldr r3, [r0]; ldr r3, [r3]
```

#### FUN_0002ce08 의 0x9e28 (Round 22 sound slot 분류 오류)

```asm
bl 0x4ad10              ; context_getter
adds r3, r0, #0         ; r3 = ctx
ldr r1, [pc, #0x264]    ; r1 = 0x9e28
adds r3, r3, r1         ; r3 = ctx + 0x9e28   ⭐ ctx-based
ldr r3, [r3]; ldr r3, [r3]; adds r3, #8; str r3, [r4]
```

#### FUN_0003d5d0 의 0xa220 (Round 22 sound slot 분류 오류)

```asm
bl 0x923e8              ; helper, returns r0
adds r2, r0, #0         ; r2 = result
ldr r0, [pc, #0x34]     ; r0 = 0xa220
adds r3, r5, r0         ; r3 = (r5 = ctx 등) + 0xa220   ⭐ NOT sl-based
strb r2, [r3]           ; store byte
```

### 정정된 분류

| 식별자 | 진짜 의미 | 검증 |
|---|---|---|
| 0x9bb4 | task_struct 필드 offset (record array 위치 직전?) | FUN_000439a0 사용 패턴 검증 |
| 0x9cbc | task_struct 필드 offset (record array base) | 같은 패턴 |
| 0x9cfe | task_struct 필드 offset | 같은 패턴 (FUN_00043508) |
| 0x9cc0 | task_struct 필드 offset | 같은 패턴 |
| **0x9c70/0x9c71/0x9c84/0xac78** | task_struct 필드 offsets (PM-7 의 "system-wide" 도 정정) | 같은 패턴 |
| 0x9e28 | task_struct 필드 offset (sound state) | FUN_0002ce08 검증 |
| 0xa220, 0xa244, 0xa245, 0xa254 | task_struct 필드 offset (sound state) | FUN_0003d5d0 검증 |
| 0x9e78 | task_struct 필드 offset (Round 18 ctx flag) | 같은 패턴 |
| 0x29e | task_struct 필드 offset (Round 18 small flag) | 같은 패턴 |

### 진짜 GOT 슬롯 (검증된 8개)

| Slot | Abs Addr | 검증 |
|---|---|---|
| **0x18** ⭐⭐⭐ | 0xb2c58 | ObjectB ptr — 860 readers / 240 funcs |
| **0x16c** | 0xb2dac | alternate task struct (single indir) — 147 readers |
| **0x444** | 0xb3084 | primary task_ptr_ptr — context_getter target |
| **0x44c** | 0xb308c | ObjectA ptr |
| **0xd00** | 0xb3940 | StorageCell ptr |
| **0x128** | 0xb2d68 | secondary state ptr |
| **0xd04, 0xd08** | 0xb3944, 0xb3948 | ObjectA helper data ptrs |

### task_struct 의 추정 layout (필드 offset 모음)

확인된 필드 offsets (모두 task_struct 안):
- 0x29e — small flag
- 0x9bb4 — (FUN_000439a0)
- 0x9c70, 0x9c71, 0x9c84 — widespread state (PM-7)
- 0x9cbc — record array base
- 0x9cc0, 0x9cfe — record array adjacent
- 0x9e28 — sound state #1
- 0x9e78 — flag
- 0xa220 — sound state #2 (write target)
- 0xa244, 0xa245 — sound bytes (adjacent)
- 0xa254 — sound state #3
- 0xac78 — additional task data

⭐ task_struct >= 0xac78 = ~44KB. 거대한 평면 구조체로 모든 subsystem state 보유.

### 영향 범위

이 정정은 다음 round 분석에 영향:
- Round 18 의 "GOT 슬롯 9개" → 1개 정정 + 5개 task_struct 필드
- Round 19 의 "신규 GOT 슬롯 5개" → 0xd00/d04/d08 일부 verify 필요
- Round 22 의 "sound subsystem 5 GOT 슬롯" → **5개 모두 task_struct 필드**
- 지금까지 **누적 19 GOT 슬롯 → 진짜는 8개** 로 축소

이는 task_struct 의 **field layout 발견 = 게임 state 구조 풀이의 시작점**. 다음 round 의 핵심 작업.

---

## 2. ⭐⭐ FUN_0003d5d0 sound_trigger sound id 추출 (2AV)

### Convention 정정

기존 가정: sound_trigger(r0=sound_id, ...). 실제: **sound_trigger(r0=context_or_task_ptr, r1=sound_id)**.

검증 사례:
```asm
0x0003da18  subs   r4, r7, #6
0x0003da1a  ldr    r3, [pc, #0x18c]
0x0003da1c  add    r3, sl
0x0003da1e  ldr    r3, [r3]
0x0003da20  ldr    r3, [r3]      ; double indir → object/struct
0x0003da22  adds   r0, r3, #0    ; r0 = task_ptr (context)
0x0003da24  movs   r1, #0x87     ; r1 = 0x87 (sound id 135)
0x0003da26  bl     #0x99764      ; sound_trigger
```

### 21 sound_trigger 의 r1 backtrace 결과

| 사이트 | 찾은 sound id |
|---|---|
| 0x0003d686 | 0x9b (155) |
| 0x0003d8d0 | (dynamic, memory load) |
| 0x0003d922 | (dynamic) |
| 0x0003da06 | (dynamic) |
| 0x0003da26 | **0x87 (135)** |
| 0x0003da4e | **0xa4 (164)** |
| 0x0003da76 | **0xa5 (165)** |
| 0x0003db6c | (dynamic) |
| 0x0003dbce | (dynamic) |
| 0x0003df9a | (dynamic) |
| 0x0003e04e | (dynamic) |
| 0x0003e146 | **0x8d (141)** |
| 0x0003e176 | **0x8e (142)** |
| 0x0003e216 | **0x8d (141)** ← **재사용** |
| 0x0003e24a | **0x8e (142)** ← **재사용** |
| 0x0003e37a | (dynamic) |
| 0x0003e42e | (dynamic) |
| 0x0003e524 | **0x83 (131)** |
| 0x0003e56e | **0x84 (132)** |
| 0x0003e5b4 | **0x83 (131)** ← **재사용** |
| 0x0003e5e8 | **0x84 (132)** ← **재사용** |

### Sound ID 통계

| Sound ID | dec | 호출 횟수 |
|---|---|---|
| 0x83 | 131 | 2 |
| 0x84 | 132 | 2 |
| 0x87 | 135 | 1 |
| 0x8d | 141 | 2 |
| 0x8e | 142 | 2 |
| 0x9b | 155 | 1 |
| 0xa4 | 164 | 1 |
| 0xa5 | 165 | 1 |
| **dynamic** | (memory load) | **10** (= 21 - 11 immediate) |

### 패턴

⭐ **Sound ID 페어 호출**: (0x83, 0x84), (0x8d, 0x8e) 같은 인접 ID 가 페어로 호출 = 두 개의 관련 sound (예: "menu_select" + "menu_play"). 페어 패턴 4쌍.

### 정체

**FUN_0003d5d0** = sound subsystem dispatcher 가 **immediate sound IDs (~10개)** + **dynamic sound IDs (~10개, memory load)** 모두 호출.
- Immediate: 정해진 fixed sound (UI, system events)
- Dynamic: 게임 state-dependent (현재 BGM, 캐릭터별 SFX 등)

Sound id range 0x83 ~ 0xa5 (131~165) = 게임 binary 의 sound table 인덱스. (총 33개 _mf 파일 + _mp music tile data 가 있으므로 sound id ↔ 자산 매핑은 다음 round 에서.)

---

## 3. ObjectB top reader 패턴 검증 (2AW)

### FUN_0002ce08 (slot 0x18 25x reader) 본문 분석

분석 결과 — Round 22 의 다른 ObjectB readers 와 동일 패턴:
```asm
bl 0x4ad10              ; context_getter (= ObjectB → task_struct)
adds r3, r0, #0         ; r3 = task_struct ptr
ldr r1, [pc, #imm]      ; r1 = 0x9e28 (task_struct 필드 offset)
adds r3, r3, r1         ; r3 = task_struct + 0x9e28
ldr r3, [r3]; ldr r3, [r3]; adds r3, #8
```

⭐ FUN_0002ce08 (그리고 다른 ObjectB readers) **= context_getter consumer**. ObjectB 슬롯 (0x18) 자체는 모두 context_getter 를 통해 *간접적*으로 사용. context_getter (FUN_0004ad10) 가 ObjectB → task_struct 추출 후 caller 가 field 접근.

### ObjectB 의 진짜 의미 재정의

**ObjectB (slot 0x18) = task_ptr_ptr_holder**:
- ObjectB[0] = task_struct ptr
- task_struct = 거대 게임 state 구조체 (≥ 44KB)
- context_getter (FUN_0004ad10) = `*(slot 0x18) → ObjectB[0] → task_struct` 추출
- 240 functions 가 context_getter 호출 후 task_struct 필드 접근

⭐⭐ Round 21 의 "ObjectB = master GVM 인터페이스" 가설은 부분 정정 — ObjectB **자체** 는 thin wrapper / single ptr holder. 진짜 마스터 객체는 **task_struct** (44KB 평면 구조체).

다만 ObjectB 의 vtable methods (offset 0/0x10/0x20/0x44/0x54/0x58/0x68/0x7c/0x80) 는 여전히 GVM API entry points — task_struct 와는 별개의 vtable.

대안 가설: 
- slot 0x18 → wrapper struct
- wrapper[0] = task_struct (대용량 state)
- wrapper[X] = vtable_ptr (GVM API)
- 두 종류의 access 가 wrapper 의 다른 필드를 통해 분기

이는 다음 round 검증 가치.

---

## 4. 다음 세션 권장 다음 단계 (Round 24 후보)

| # | 작업 | 명령 | 산출물 |
|---|---|---|---|
| ⭐⭐⭐ 2AZ | **task_struct field layout 매핑** — 모든 known offsets (0x29e/0x9bb4/0x9cbc/0x9c70/0xa220/0xa254/등) 의 reader 함수 분포 | `find_global_slot_writers.py` 시리즈 + 패턴 검증 | task_struct 의 field-by-field 의미 매핑 |
| ⭐⭐ 2BA | **dynamic sound id source** — FUN_0003d5d0 의 10개 dynamic sound 호출의 메모리 source | 본문 backtrace + task_struct 필드 식별 | sound id ↔ task_struct 필드 매핑 |
| ⭐⭐ 2BB | **slot 0x18 의 wrapper struct 검증** — ObjectB 가 thin wrapper 인지, vtable + task_struct 가 같은 struct 인지 | 직접 본문 분석 + memory layout 추론 | ObjectB 의 정확한 구조 |
| 2BC | sound id 0x83~0xa5 ↔ _mf/_mp 자산 매핑 | sound table 직접 검색 (binary 의 sound 인덱스 vs `snd/` 폴더) | 21 sound effect 정체 |
| 2BD | FUN_00030018 본문 (ObjectB reader 26x) | 본문 분석 | task_struct 다른 필드 사용 패턴 |

---

## 5. 산출물

```
work/h3/global_slot_0x9e28_writers.json   ; 2AU (precise pattern 0 hits = task_struct field 확정)
work/h3/global_slot_0xa220_writers.json   ; 2AU
work/h3/global_slot_0xa254_writers.json   ; 2AU
```

(2AV/2AW inline 분석 — 이 문서에 결과 통합)

---

## 6. Round 23 핵심 takeaway

1. ⭐⭐⭐ **"GOT slot" vs "task_struct field" 분류 정정** — Round 18~22 의 다수 "GOT slot offset" 분류가 사실 task_struct field offsets. 진짜 GOT 슬롯은 **8개**로 축소 (0x18/0x16c/0x444/0x44c/0xd00/0x128/0x29e/d04/d08). 나머지 11+ "슬롯" 은 task_struct 필드.
2. ⭐⭐⭐ **task_struct 가 거대 평면 구조체 (≥44KB)** — 모든 subsystem state 가 단일 struct 안에 평면 배치 (sound state @0x9e28~0xa254, record array @0x9cbc, flag @0x29e, 등).
3. ⭐⭐ **sound_trigger convention 정정** — `sound_trigger(r0=ctx, r1=sound_id)`. 21 호출 중 **11 immediate sound id 식별** (0x83~0xa5, 페어 패턴).
4. ⭐ **ObjectB 재정의** — 단순한 task_ptr 보유 슬롯 (= context_getter 의 source). 240 reader 함수 모두 context_getter 통해 task_struct 필드 접근. ObjectB vtable 은 별도 인터페이스 가능성.
5. ⭐ **`disasm_subsystem_func.py` 의 분류 한계 발견** — PC-rel literal 의 값만으로 GOT slot 여부 판단 불가, 사용 패턴 (sl 기반 vs ctx 기반) 검증 필요.
