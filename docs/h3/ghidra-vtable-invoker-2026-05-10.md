# Round 19 (2026-05-10 PM-9) — vtable invoker + JT 디코드 + secondary task processor

## 요약

Round 18 의 sub-handler 본문 분석 후속. PM-9 의 핵심 진척:

1. ⭐⭐⭐ **FUN_00098244 = C++ vtable method invoker** (172B 선형, 0 cmp arm, 5 indirect call)
   - Object @ 신규 슬롯 GOT+0x44c (= 0xb308c)
   - vtable method 5개 호출 (offset 0, 0x10, 0x20, 0x68) + task_struct[0x58]
   - 신규 GOT 슬롯 5개 발견: 0x44c, 0xd00, 0xd04, 0xd08, 0x18
2. ⭐⭐ **JT @ 0xa8370 디코드** — type 4 → fall-through (dominant), 5/8 → 0x4425a, 6/9/10 → 0x43a6e (catch-all), 7 → 0x44214
3. ⭐ **FUN_00043508 = secondary task processor** (1176B, 24 cmp arms) — cmp #9 5x dominant + cmp #0xa0 2x. FUN_000439a0 와 동일 슬롯 (0x9bb4/0x9cbc) 공유 → 같은 record array 처리

---

## 1. FUN_00098244 본문 분석 (172B, 79 instr)

### 디스어셈블 핵심 흐름

```asm
0x00098244  push  {r4-r7,lr}; mov r7,sl; mov r6,r8; push {r6,r7}
0x0009824c  ldr   r3, [pc, #0x88]   ; r3 = 0x1a9ea (GOT base offset, PIC)
0x0009824e  mov   sl, r3
0x00098252  add   sl, pc             ; sl = 0xb2c40 (GOT base, 동일)
0x00098254  sub   sp, #4              ; 4B local
0x00098258  adds  r5, r0, #0          ; r5 = param1
0x0009825a  mov   r8, r3              ; r8 = param2 byte
0x0009825c  lsls  r4, r2, #0x18       ; r4 = param3 byte (sign-extend)

;; INIT 단계
0x0009825e  bl    #0x98364            ; FUN_00098364 (sub-init helper)
0x00098262  mov   r1, sp              ; r1 = &local
0x00098264  adds  r0, r5, #0          ; r0 = param1
0x00098266  bl    #0x99a9c            ; FUN_00099a9c → writes result to *sp, returns r0

;; VTABLE METHOD 1 (Object[0] = first method)
0x0009826a  ldr   r3, [pc, #0x70]; add r3, sl; ldr r6, [r3]     ; r6 = *(GOT+0x44c) = ObjectA ptr
0x00098270  ldr   r3, [pc, #0x6c]; add r3, sl; adds r7, r0, #0  ; r7 = saved r0 (from prev call)
                  ldr r0, [r3]                                   ; r0 = *(GOT+0xd04)
0x00098278  ldr   r3, [pc, #0x68]; ldr r1, [r6]                  ; r1 = ObjectA[0] = vtable_ptr
                  add r3, sl; ldr r2, [r3]                       ; r2 = *(GOT+0xd08)
0x00098280  ldr   r3, [r1]                                       ; r3 = vtable[0] = method0
0x00098282  ldr   r1, [sp]; bl 0xa42a0                            ; ⭐ indirect call vmethod[0]
                                                                  ; (a42a0 = bx r3 veneer)

;; VTABLE METHOD 2 (vtable[0x68])
0x00098288  ldr   r3, [pc, #0x5c]; lsrs r4,r4,#0x18; add r3, sl
                  ldr r5, [r3]                                    ; r5 = *(GOT+0xd00)
0x00098292  ldr   r3, [r6]                                        ; r3 = ObjectA[0] = vtable
0x00098296  str   r0, [r5]                                        ; *r5 = method0_result
0x00098298  ldr   r3, [r3, #0x68]                                 ; r3 = vtable[0x68] = method26
0x0009829a  adds  r1, r4, #0
0x0009829c  bl    #0xa42a0                                        ; ⭐ indirect call vmethod[0x68]

;; VTABLE METHOD 3 (vtable[0x10])
0x000982a0  ldr   r3, [r6]; ldr r1, [r7]; ldr r2, [sp]            ; r3 = vtable, r1 = *r7, r2 = sp[0]
0x000982a6  adds  r1, #8                                          ; r1 = *r7 + 8
0x000982a8  ldr   r3, [r3, #0x10]                                 ; r3 = vtable[0x10] = method4
0x000982aa  ldr   r0, [r5]                                        ; r0 = *r5 (saved earlier)
0x000982ac  bl    #0xa42a0                                        ; ⭐ indirect call vmethod[0x10]

;; TASK_STRUCT METHOD (slot @ GOT+0x18, double indirection)
0x000982b0  ldr   r3, [pc, #0x38]; add r3, sl                     ; r3 = GOT+0x18 = 0xb2c58
0x000982b4  ldr   r3, [r3]                                        ; r3 = *(0xb2c58)  ⭐ NEW task slot
0x000982b6  ldr   r3, [r3]                                        ; r3 = double indir = task_struct
0x000982b8  adds  r0, r7, #0
0x000982ba  ldr   r3, [r3, #0x58]                                 ; r3 = task_struct[0x58] = method
0x000982bc  bl    #0xa42a0                                        ; ⭐ indirect call task_method[0x58]

;; VTABLE METHOD 4 (vtable[0x20])
0x000982c0  ldr   r3, [r6]; ldr r0, [r5]                          ; r3 = vtable, r0 = *r5
0x000982c4  ldr   r3, [r3, #0x20]                                 ; r3 = vtable[0x20] = method8
0x000982c6  mov   r1, r8                                          ; r1 = param2 byte (saved)
0x000982c8  bl    #0xa42a0                                        ; ⭐ indirect call vmethod[0x20]

0x000982cc  add   sp, #4
0x000982ce  pop   {r3, r4}; mov r8, r3; mov sl, r4
0x000982d4  pop   {r4, r5, r6, r7, pc}                             ; RETURN
```

### 정체 확정

| 측면 | 발견 |
|---|---|
| **함수 종류** | **C++ vtable method invoker** — 5 indirect calls via veneer 0xa42a0 (bx r3) |
| **분기** | 0 — completely linear (no cmp arms) |
| **사용 객체** | ObjectA @ slot (GOT+0x44c = 0xb308c, NEW slot) — 첫 dword 가 vtable_ptr |
| **vtable methods 호출** | offset 0 (method0), 0x10 (method4), 0x20 (method8), 0x68 (method26) — 4 vtable methods |
| **task method 호출** | task_struct[0x58] via 신규 slot GOT+0x18 = 0xb2c58 (double indir) |
| **추가 init 호출** | FUN_00098364 (sub-init), FUN_00099a9c (returns value to stack) |
| **신규 슬롯** | 0x44c (ObjectA), 0xd00, 0xd04, 0xd08 (helper data ptrs), 0x18 (task_struct) |
| **callers** | 17+ via FUN_00047a14 후속 호출 |

### 가설

**0x0f state write (FUN_00047a14) → vtable method 시퀀스 호출 (FUN_00098244)** = 명확한 RPC/event 패턴.

후보:
- ⭐ **C++ 클래스의 method dispatch** (Object[0]=vtable, methods at fixed offsets) — feature phone GVM 환경에서 C++ runtime 의 일부?
- audio engine subsystem (sound load → init → play sequence)
- save/load operation (state 0xf = "save now", invoker = serialize+write)

GVM 외부에서 주입된 ObjectA 의 vtable 을 게임 코드가 호출 = **GVM API 호출 패턴**. 0xa42a0 veneer 가 모든 indirect call 의 game-side 진입점. 

다음 추적 거리:
1. **FUN_00098364 / FUN_00099a9c** (init helpers) 본문
2. **slot 0x44c / 0x18 의 다른 readers** — ObjectA/task_struct 의 다른 method 들
3. **vtable[0], [0x10], [0x20], [0x68] 의 의미** — Ghidra GUI 에서 ObjectA struct 정의 + vtable type 추론

---

## 2. JT @ 0xa8370 디코드 (FUN_000439a0 의 type 4..10 dispatch)

### 디스어셈블 패턴 재확인

Round 18 에서 잘못 계산했던 JT base 정정 (0x8370 → 0xa8370):

```asm
; FUN_000439a0 후반부:
0x00043a4c  ldr   r3, [pc, #0x2bc]   ; r3 = 0xffff5730 (signed = -0xa8d0)
0x00043a4e  mov   r6, sl              ; r6 = sl (GOT base = 0xb2c40)
0x00043a50  adds  r2, r6, r3          ; r2 = 0xb2c40 + 0xffff5730 = 0xa8370 (32-bit add)
                                       ; ⭐ JT base @ 0xa8370 (binary 내부 .data 영역)
0x00043a52  lsls  r1, r1, #2          ; r1 = (type - 4) * 4
0x00043a54  ldr   r3, [r1, r2]        ; r3 = JT[type - 4]   (signed 32-bit offset)
0x00043a56  adds  r3, r3, r2          ; r3 = JT_base + JT_entry = absolute target
0x00043a58  mov   pc, r3              ; ⭐ JUMP
```

### JT entries (각 4 byte signed offset relative to JT base 0xa8370)

| index | type | offset stored | absolute target | 정체 |
|---|---|---|---|---|
| 0 | 4 | -0x4916 (0xfff9b6ea) | **0x00043a5a** | ⭐ **fall-through** (현재 함수의 다음 instr `movs r4, #1`) |
| 1 | 5 | -0x4116 (0xfff9beea) | 0x0004425a | shared B handler (FUN_000442e4 내부) |
| 2 | 6 | -0x4902 (0xfff9b6fe) | **0x00043a6e** | catch-all (= bhi default) |
| 3 | 7 | -0x4188 (0xfff9bea4) | 0x00044214 | 고유 sub-handler (FUN_000442e4 내부) |
| 4 | 8 | -0x4116 (0xfff9beea) | 0x0004425a | = type 5 (shared B) |
| 5 | 9 | -0x4902 (0xfff9b6fe) | 0x00043a6e | = catch-all |
| 6 | 10 | -0x4902 (0xfff9b6fe) | 0x00043a6e | = catch-all |

### 핵심 패턴

- **type 4 = dominant case** — JT[0] 가 fall-through (jump to next instr = 0x43a5a). 
  - 즉, JT 가 발동되어도 `mov pc, r3` 이 사실상 no-op 처럼 동작 → 함수 본문이 type 4 로 계속 진행.
  - 이는 **type 4 가 default behavior** 임을 강력히 시사.
- **type 6, 9, 10 모두 catch-all** (= bhi default 와 동일 = 0x43a6e). 
  - 사실상 "type > 6 처리 안 함" 의미 → type 4..6 만 진짜 의미 있는 case.
- **type 5, 8 = shared sub-handler** (0x4425a) — FUN_000442e4 (392B) 내부의 중간 점프.
- **type 7 = 고유 path** (0x44214 — also FUN_000442e4 내부, 다른 진입).

### FUN_000442e4 분석 가치

FUN_000442e4 (392B, 11 callers, PROGRESS 의 인접 함수)가 type 5/7/8 의 공통 진입점. 
- **type 5/8 → 0x4425a** (FUN_000442e4 + 0xf76)... 잠깐, FUN_000442e4 는 392B = 0x442e4 ~ 0x4446c. 0x4425a 는 그 RANGE 밖! 

다시 계산: 0x4425a < 0x442e4 → 0x4425a 는 FUN_000442e4 시작 전 위치. 즉, **다른 함수 본문 안의 분기**. 

pic_stubs ranking 의 인접 함수 표에서:
- 0x44034cc (60B) — 0x4425a 가 이 범위
- 0x4348c (64B) — 다른 candidate

⭐ TODO: 0x4425a 와 0x44214 가 어느 함수 본문에 속하는지 정확히 식별 필요. 다음 round 에서 push prologue 검색.

### 결론

FUN_000439a0 의 7-entry JT 는 사실상 **3-way 분기**:
1. type 4 → continue (dominant)
2. type 5/8 → shared B handler (0x4425a)
3. type 7 → unique handler (0x44214)
4. type 6/9/10 → catch-all (no-op fallback)

**의미**: type field 의 의미가 4~6 정도가 메인이고 7+ 는 거의 안 쓰임. 이는 PM-7 의 cmp #6 / cmp #1 가장 인기 패턴과 일치.

---

## 3. FUN_00043508 본문 분석 (1176B, 24 cmp arms)

### Cmp 분포

| imm | 개수 | 의미 |
|---|---|---|
| 0x00 | 12 | gate / null check (가장 흔함) |
| **0x09** | **5** ⭐ | **type-9 reader 강력 후보** (이전엔 약함) |
| 0x06 | 2 | type-6 |
| 0xa0 | 2 | medium 상수 (record stride? offset?) |
| 0x10 | 1 | type-16 |
| 0x07 | 1 | type-7 |
| 0x01 | 1 | type-1 |

### 신규 GOT 슬롯

| slot offset | abs addr | 사용 |
|---|---|---|
| 0x9bb4 | 0xb67f4 | (FUN_000439a0 와 공유) |
| 0x9cbc | 0xb68fc | (FUN_000439a0 와 공유 — 같은 record array) |
| **0x9cfe** | **0xb693e** | ⭐ **신규** — FUN_00043508 고유 |
| **0x9cc0** | **0xb6900** | ⭐ **신규** — FUN_00043508 고유 |

⭐⭐ **FUN_00043508 와 FUN_000439a0 가 동일 record array 처리** (slot 0x9cbc 공유). 같은 0x38 stride entity records 위에서 다른 종류의 처리 수행.

### Cmp #0xa0 (160) 의 의미

cmp r3, #0xa0 → bls — record offset 으로 보임 (0x38 stride 면 record[0xa0]은 record 4번째 인덱스 위치). 다른 가설: 화면 좌표 / 시간값 / 임의 임계값.

### 4 context_getter 호출

호출 위치: 0x4353a, 0x43560, 0x438d6, 0x43942 — 함수 시작 + 중간 4번 분산. 이는 multiple subsystems 와 상호작용 (각 context_getter 는 GVM 글로벌 ctx 반환, 다른 부분 사용).

### 가설

FUN_00043508 (1176B, only 1 caller) = **dedicated entity processing function** for a specific subsystem. Type-9 emphasis (5 cmp #9) 시사: 이 함수가 type-9 records 의 핵심 처리자. PM-7 에서 type-9 readers 를 못 찾았던 이유는 직접 cmp #9 가 한 함수에 집중되어 있기 때문.

---

## 4. GOT 슬롯 wide-scan 누적 통계

Round 18 + Round 19 통합 — **총 14 슬롯 모두 0 direct writes**:

| Slot | Abs Addr | 출처 | 정체 가설 |
|---|---|---|---|
| 0x18 | 0xb2c58 | Round 19 (FUN_00098244) | task_struct (double indir) — 신규 |
| 0x128 | 0xb2d68 | Round 18 | secondary state ptr (write 0xf target) |
| 0x16c | 0xb2dac | Round 18 | alternate task_struct (single indir) — 147 readers ⭐ |
| 0x29e | 0xb2ede | Round 18 | small flag |
| 0x444 | 0xb3084 | PM-7 | primary task_ptr_ptr ⭐ |
| **0x44c** | **0xb308c** | **Round 19** | **ObjectA (C++ vtable obj)** — 신규 ⭐ |
| **0xd00** | **0xb3940** | **Round 19** | helper data ptr — 신규 |
| **0xd04** | **0xb3944** | **Round 19** | helper data ptr — 신규 |
| **0xd08** | **0xb3948** | **Round 19** | helper data ptr — 신규 |
| 0x9bb4 | 0xb67f4 | Round 18 + 19 | router-specific |
| 0x9c70 | 0xb68b0 | PM-7 | widespread (112 readers) |
| 0x9cbc | 0xb68fc | Round 18 + 19 | record array base (FUN_000439a0/00043508 공유) |
| **0x9cc0** | **0xb6900** | **Round 19** | FUN_00043508 고유 — 신규 |
| **0x9cfe** | **0xb693e** | **Round 19** | FUN_00043508 고유 — 신규 |
| 0x9e78 | 0xb6ab8 | Round 18 | per-context flag |

### 슬롯 그룹 분류 (Round 19 갱신)

1. **Task struct pointers** (모두 GVM 외부 주입):
   - 0x444 (primary, double indir)
   - 0x16c (alternate, single indir)
   - 0x18 (vtable invoker용, double indir)

2. **State/flag slots**:
   - 0x128 (state 0xf target)
   - 0x29e (small flag)
   - 0x9e78 (per-context flag)

3. **Object/data slots** (C++ 객체 또는 데이터 테이블):
   - 0x44c (ObjectA with vtable) — Round 19 핵심 발견
   - 0xd00, 0xd04, 0xd08 (helper data ptrs)

4. **Record array slots**:
   - 0x9cbc (0x38 stride record base, FUN_000439a0/43508 공유)

5. **Subsystem-specific slots**:
   - 0x9bb4 (router state)
   - 0x9c70 (widespread)
   - 0x9cc0, 0x9cfe (FUN_00043508 고유)

---

## 5. 다음 세션 권장 다음 단계 (Round 20 후보)

| # | 작업 | 명령 | 산출물 |
|---|---|---|---|
| ⭐⭐ 2AF | **FUN_00098364 / FUN_00099a9c** 본문 (FUN_00098244 init helpers) | `disasm_subsystem_func.py 0x98364 0x983b8` + `0x99a9c <end>` | vtable invoker 의 init/setup 단계 풀이 |
| ⭐⭐ 2AG | **slot 0x44c (ObjectA) 의 다른 readers** | `find_global_slot_writers.py --slot-offset 0x44c` | ObjectA 의 다른 method 호출처 매핑 |
| ⭐ 2AH | **0x4425a / 0x44214 의 enclosing function** | push prologue 검색 + 본문 식별 | type 5/7 sub-handler 정체 |
| 2AI | slot 0x18 (vtable task_struct) readers | `find_global_slot_writers.py --slot-offset 0x18` | task_struct 의 method consumers |
| 2AJ | FUN_00043508 의 cmp #9 5 arms — arm-by-arm BL 매핑 | `analyze_arm_handlers.py 0x43508 0x439a0` | type-9 처리자 식별 |

---

## 6. 산출물

```
work/h3/state0xf_consumer_98244_disasm.json   ; 2AA
work/h3/task_processor_43508_disasm.json      ; 2AC
```

JT 디코드는 별도 JSON 미저장 — 이 문서에 통합.

---

## 7. Round 19 핵심 takeaway

1. **C++ vtable method dispatch 발견** — FUN_00098244 가 ObjectA 의 vtable methods 5개 호출 (offset 0/0x10/0x20/0x68) + task_struct method (offset 0x58). **GVM API 호출 패턴 의 game-side 진입점**.
2. **신규 GOT 슬롯 5개 추가** — 0x44c (ObjectA), 0xd00/d04/d08 (helper data), 0x18 (vtable task_struct). 누적 14 슬롯, 모두 0 direct writes.
3. **JT @ 0xa8370 디코드** — 7-entry JT 의 진짜 의미는 3-way 분기 (type 4 fall-through dominant + 5/8 shared + 7 unique + 6/9/10 catch-all).
4. **FUN_00043508 = type-9 처리자** — cmp #9 5x dominant + FUN_000439a0 와 동일 record array 공유 = 같은 entity 들의 다른 종류 처리.
5. **state 0xf flow 풀이**: FUN_00047a14 (state set) → FUN_00098244 (vtable invoker) → ObjectA 의 5 methods 호출. **명확한 RPC 패턴 도달**.
