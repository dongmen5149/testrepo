# Round 24 (2026-05-10 PM-14) — task_struct field layout 매핑 + context_getter 본문 + dynamic sound id

## 요약

Round 23 의 task_struct 필드 정정 후속. PM-14 의 핵심 진척:

1. ⭐⭐⭐ **task_struct field layout 종합 매핑** (신규 도구 `find_task_struct_field_readers.py`) — 15 known fields × 350K instr 검색. **0x9bb4 = 압도적 dominant field** (69 verified sites, 15 funcs, top reader **FUN_0009b252 (PM-6 type-tag reader) 가 46x 사용**).
2. ⭐⭐⭐ **context_getter (FUN_0004ad10) 본문 풀이** — single deref 만 (`r0 = *(slot 0x444)` = task_ptr). 호출자가 추가 deref 로 task_struct 진입. ObjectB 가 wrapper 가 아니라 **slot 0x444 가 진짜 task_ptr_ptr**. ObjectB (slot 0x18) 는 별개의 슬롯.
3. ⭐⭐ **Dynamic sound id source 식별** — 10 dynamic sound 호출 중 첫 번째 패턴 검증. sound_id = `[r7-0x18]` = function frame stack 변수 (parameter 또는 local var).
4. ⭐⭐ **0x9c70 등 multi-level access 패턴 발견** — 단순 `ctx + offset` 이 아니라 `task_ptr + record_idx_byte + 0x9c70 + 2` 같은 **복합 계산 base offset**. record array 의 per-element field 접근.
5. ⭐ **신규 도구 `find_task_struct_field_readers.py`** — context_getter 직후의 field offset 추적 + reader function 매핑.

---

## 1. task_struct field layout 종합 매핑 (2AZ) ⭐⭐⭐

### 신규 도구

`tools/recon/find_task_struct_field_readers.py`:
- binary 350,955 instr 디스어셈블
- 2,112 context_getter (FUN_0004ad10) BL 사이트 검색
- 각 사이트 직후 12 instr 안의 `ldr Rx, [pc, #imm]; adds Ry, R0, Rx` 패턴 매칭
- 15 known field offsets 에 대해 reader 함수 분포 통계

### 매핑 결과 (검증된 verified ctx+field 패턴)

| Field offset | Verified sites | Unique funcs | Top readers | 가설 |
|---|---|---|---|---|
| **0x9bb4** ⭐⭐⭐ | **69** | **15** | **FUN_0009b252 (46x!)**, FUN_00041c6e (5x), FUN_0009ada4 (4x), FUN_0009a186 (3x) | **task_struct 의 dominant field** — type-tag dispatch 의 핵심 |
| 0x9cbc | 25 | 11 | FUN_00041c6e (5x), FUN_00044a38 (5x), FUN_000482c8 (5x), FUN_0009ada4 (2x) | record array base ptr_ptr |
| 0x9e28 | 16 | 10 | FUN_00023f7c (3x), FUN_00045f90 (2x), FUN_0004601c (2x), FUN_00047aa8 (2x), FUN_000484b4 (2x) | sound state field |
| 0x9cc0 | 9 | 5 | FUN_000442e4 (3x), FUN_00044a38 (2x), FUN_000482c8 (2x), FUN_00043508, FUN_00043a6e | record array adjacent field |
| 0x9e78 | 5 | 4 | FUN_00023cd4 (2x), FUN_00047a14, FUN_000947f4, FUN_000983e8 | per-context flag |
| 0xac78 | 5 | 1 | FUN_000241dc (5x) | FUN_000241dc 전용 field |
| 0x29e | 3 | 2 | FUN_00042fbc (2x), FUN_000439a0 | small flag |
| 0x9cfe | 3 | 3 | FUN_00043508, FUN_00043a6e, FUN_00046590 | record array variant |
| 0xa220 | 1 | 1 | FUN_00024780 | sound state (single-use) |
| 0xa244 | 1 | 1 | FUN_000241dc | sound byte (single-use) |
| 0x9c70/9c71/9c84 | **0** | **0** | (다른 패턴) | 복합 계산 base — Round 24 §4 참조 |
| 0xa245/a254 | 0 | 0 | (다른 패턴) | sound 복합 calc 추정 |

### ⭐⭐⭐ 0x9bb4 의 의미

**FUN_0009b252 가 0x9bb4 를 46x 사용** = PM-6 의 "type-tag reader 후보" 가 **task_struct 의 0x9bb4 필드를 핵심 dispatch 키로 사용**.

PM-6 분석에 따르면 FUN_0009b252:
- 86 cmp arms (가장 많음)
- 5 distinct nonzero type tags
- 53 context_getter calls

→ FUN_0009b252 가 매 cmp arm 직전 context_getter + 0x9bb4 접근 = **task_struct[0x9bb4] = type tag** 일 가능성.

다음 추적 거리:
1. FUN_0009b252 본문에서 `task_struct[0x9bb4]` 의 실제 access 패턴 (single byte? word? indir?)
2. 0x9bb4 가 "current state machine state index" 또는 "current event type" 후보

### record array 시스템 (0x9cbc/0x9cc0/0x9cfe)

3 인접 field 가 같은 record array 처리 함수들에서 함께 사용:
- **FUN_00044a38** (5x 0x9cbc + 2x 0x9cc0)
- **FUN_000482c8** (5x 0x9cbc + 2x 0x9cc0)
- **FUN_00041c6e** (5x 0x9cbc)

⭐ 이 3 함수가 record array 의 **alternative dispatcher 들** (FUN_000439a0/00043508 의 sibling). 같은 0x38 stride record array 시스템 처리.

**FUN_00044a38, FUN_000482c8** 는 처음 발견. 이전 round 들에서 매핑 안 됨. Round 25 후보로 본문 분석.

---

## 2. context_getter (FUN_0004ad10) 본문 정정 (2BB) ⭐⭐⭐

### 본문 디스어셈블

```asm
0x0004ad10  mov   ip, r3              ; save r3 in ip (caller r3 보존)
0x0004ad12  mov   r3, sl              ; r3 = sl (caller sl)
0x0004ad14  push  {r3}                ; save sl
0x0004ad16  mov   r3, ip              ; restore r3
0x0004ad18  ldr   r3, [pc, #0x10]    ; r3 = lit1 = GOT base offset (PIC)
0x0004ad1a  mov   sl, r3
0x0004ad1c  ldr   r3, [pc, #0x10]    ; r3 = lit2 = 0x444 (slot offset)
0x0004ad1e  add   sl, pc              ; sl = 0xb2c40 (GOT base, PIC)
0x0004ad20  add   r3, sl              ; r3 = 0xb3084 (= GOT + 0x444)
0x0004ad22  ldr   r0, [r3]            ; ⭐ r0 = *(0xb3084) = task_ptr  (single deref)
0x0004ad24  pop   {r3}                ; restore sl
0x0004ad26  mov   sl, r3
0x0004ad28  bx    lr                  ; return r0
```

### 정정

- ⭐ context_getter 는 **단일 deref** 만 수행: `r0 = *(slot 0x444)`
- 즉 r0 = task_ptr (= struct ptr)
- caller code 에서 추가 `ldr r3, [r3]` 등으로 deref 해서 task_struct 의 fields 접근
- Round 19/PM-7 의 "double indirection" 표현은 caller 의 사용 패턴이지 context_getter 자체의 동작이 아님

### 의미

`*(slot 0x444)` 가 **진짜 task_ptr** (single-pointer). 즉:
- slot 0x444 = task_ptr_storage (위치 0xb3084)
- *(slot 0x444) = task_ptr (= context_getter 반환값)
- *task_ptr = task_struct (caller 가 추가 deref)

이는 **slot 0x444 자체가 task_ptr 보유** 의미 (Round 17/PM-7 의 "task_ptr_ptr" 표현은 정정).

slot 0x18 (ObjectB) 는 **별개의 wrapper** — 240 reader 함수가 ObjectB 를 사용하지만, 그 사용은 context_getter 와 무관 (`add sl, pc; add r3, sl; ldr ...` 직접 패턴).

### ObjectB 와 task_ptr 의 관계

| 슬롯 | 정체 | 사용 패턴 |
|---|---|---|
| GOT+0x444 | task_ptr | context_getter 가 read 후 caller 가 추가 deref 로 task_struct fields 접근 |
| GOT+0x18 | ObjectB | 240 reader 가 직접 (`add sl, pc + add r3, sl`) 으로 ObjectB 접근, vtable methods 호출 |
| GOT+0x16c | alternate task struct | 147 reader 가 직접 single indir 로 접근 |

세 슬롯은 **서로 독립적인 GVM 객체들**. context_getter 는 slot 0x444 만 다룸. ObjectB 의 vtable 은 task_struct field 와는 다른 인터페이스.

---

## 3. Dynamic sound id source (2BA) ⭐⭐

### Sample: sound_trigger @ 0x3d8d0 (r1=None, dynamic)

```asm
0x0003d8be  ldr   r3, [pc, #0xbc]    ; r3 = literal (slot offset)
0x0003d8c0  add   r3, sl              ; r3 = absolute slot addr
0x0003d8c2  ldr   r3, [r3]            ; r3 = *(slot)
0x0003d8c4  ldr   r2, [r3]            ; r2 = *(*(slot)) — task_struct or vtable owner

0x0003d8c6  adds  r3, r7, #0          ; r3 = r7
0x0003d8c8  subs  r3, #0x18           ; r3 = r7 - 0x18  ⭐ stack frame access
0x0003d8ca  ldr   r3, [r3]            ; r3 = *[r7-0x18] = local var or saved param

0x0003d8cc  adds  r0, r2, #0          ; r0 = task_struct
0x0003d8ce  adds  r1, r3, #0          ; r1 = sound_id (from local)
0x0003d8d0  bl    #0x99764             ; sound_trigger
```

### 패턴

⭐ Dynamic sound id 가 **stack frame 의 saved variable** 에서 옴 (`[r7-0x18]`). r7 은 함수 시작 시 sl 또는 frame ptr 보유. 

10 dynamic sound 호출 (FUN_0003d5d0 안에서) 패턴:
- 모두 stack/local 에서 sound_id load (r7-0xN 패턴)
- sound_id 는 **함수 인자** (FUN_0003d5d0 의 param) 또는 **이전 계산 결과** (사용자 입력 또는 게임 state 기반)

### 의미

FUN_0003d5d0 = sound dispatcher 가 두 종류 sound 호출:
1. **Immediate sound** (11x, 0x83~0xa5) — fixed UI/system events
2. **Dynamic sound** (10x, stack-based) — caller-specified sound (battle hits, NPC dialogues, etc.)

Dynamic sound 의 caller 분석은 FUN_0003d5d0 호출자 추적 + 인자 backtrace 로 가능 (Round 25 후보).

---

## 4. 0x9c70 등 복합 계산 패턴 (2AZ 후속) ⭐⭐

### FUN_000818f0 의 0x9c70 사용 sample

```asm
0x00081934  ldrb  r3, [r3]            ; r3 = byte (record index)
0x00081936  lsls/asrs r3, r3, #0x18   ; sign-extend
0x0008193a  adds  r3, r3, r4          ; r3 = signed_byte_index + r4 (= saved task_ptr)
0x0008193c  ldr   r1, [pc, #0x378]    ; r1 = 0x9c70
0x0008193e  adds  r3, r3, r1          ; r3 = task_ptr + record_index + 0x9c70
0x00081940  ldrb  r3, [r3, #2]        ; r3 = byte at task_ptr[+record_index+0x9c70+2]
0x00081942  strb  r3, [r5]
```

### 의미

⭐ 0x9c70 는 **단순 `ctx+offset` 이 아니라 `task_ptr + per_record_offset + 0x9c70 + post_offset`** 형태로 사용. 즉:
- 0x9c70 = task_struct 안의 **record array 의 base offset** (record 가 stride X, 각 record 안의 작은 byte field)
- 그 안에서 `record_index_byte + 0x9c70 + 2` = 특정 record 의 +2 offset 필드

이는 **다른 task_struct 필드들 (0x9cbc 같은 ptr field) 와 다른 형태** — 0x9c70 자체가 task_struct 안의 array start. record stride 는 1 byte 단위 (단순 byte array), 그 안에 +2 offset byte.

### 분류 정정

기존 가정: 0x9c70 = task_struct field offset (단일 word/byte field)
정정: 0x9c70 = **task_struct 안의 byte array base offset**, byte index 로 접근

이는 0x9c70~0x9c84 계열 (PM-7 에서 4개 인접 슬롯) 가 **같은 byte array 의 인접 시작점** 일 가능성 시사. e.g.:
- 0x9c70 = byte array #1 시작
- 0x9c71 = byte array #1 + 1
- 0x9c84 = byte array #2 시작 (= +0x14 offset)

또는 4 개 별개 byte arrays (each ~14 byte stride).

다음 round 의 검증 가치.

---

## 5. 다음 세션 권장 다음 단계 (Round 25 후보)

| # | 작업 | 명령 | 산출물 |
|---|---|---|---|
| ⭐⭐⭐ 2BE | **FUN_0009b252 본문 — 0x9bb4 dispatch 패턴** | `disasm_subsystem_func.py 0x9b252 0x9c280 --label type_tag_dispatcher_v2` (재분석) | task_struct[0x9bb4] dispatch 의 실제 의미 |
| ⭐⭐ 2BF | **신규 record array dispatchers 본문** (FUN_00044a38 / FUN_000482c8 / FUN_00041c6e) | `disasm_subsystem_func.py` 3개 | record array 시스템 의 alternative dispatchers |
| ⭐⭐ 2BG | **0x9c70~0x9c84 byte array 검증** | inline analysis, multiple call sites | task_struct 안의 array layout |
| 2BH | FUN_0003d5d0 호출자 분석 | caller chain | dynamic sound id 의 진짜 source |
| 2BI | FUN_000241dc 본문 (0xac78 5x reader, 단일 함수 전용 field) | 본문 분석 | 0xac78 의 의미 |
| 2BJ | sound id 0x83~0xa5 ↔ snd/ 자산 매핑 | binary sound table | 21 sound effect 정체 |

---

## 6. 산출물

```
work/h3/task_struct_field_readers.json        ; 2AZ 매핑 결과 (15 fields × reader stats)
tools/recon/find_task_struct_field_readers.py ; 신규 도구 (Round 24)
```

(2BA / 2BB / 2BG inline 분석 — 이 문서에 결과 통합)

---

## 7. Round 24 핵심 takeaway

1. ⭐⭐⭐ **0x9bb4 = task_struct 의 dominant field** (69 verified sites, 15 funcs, FUN_0009b252 가 46x). PM-6 의 type-tag reader 가 사실 **task_struct[0x9bb4] dispatch**. 다음 round 의 핵심 추적 대상.
2. ⭐⭐⭐ **context_getter 가 single deref** (`r0 = *(slot 0x444)`). caller 가 추가 deref. ObjectB (slot 0x18) 와 task_ptr (slot 0x444) 는 독립.
3. ⭐⭐ **신규 record array dispatchers** (FUN_00044a38 / FUN_000482c8 / FUN_00041c6e) 발견 — FUN_000439a0/00043508 의 sibling.
4. ⭐⭐ **Dynamic sound id = stack frame 변수** (r7 base) — FUN_0003d5d0 caller 가 sound id 결정.
5. ⭐⭐ **0x9c70 는 단순 field 아니라 byte array base** — task_struct 안의 array 시작점. PM-7 의 "system-wide GOT slots" 가설 정정.
6. ⭐ **신규 도구 `find_task_struct_field_readers.py`** — 향후 task_struct 분석의 표준 도구.
