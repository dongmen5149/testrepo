# Round 21 (2026-05-10 PM-11) — ObjectB master interface + ObjectA lifecycle 종합 + FUN_000439a0 49 arms BL 매핑

## 요약

Round 20 의 ObjectA cluster 발견 후속. PM-11 의 핵심 진척:

1. ⭐⭐⭐ **ObjectB (slot 0x18) = 게임의 마스터 GVM 인터페이스 객체** — 860 reader sites in 240 unique functions (slot 0x16c 의 5.8x, slot 0x444 의 14x). **모든 핵심 dispatcher 가 이 슬롯을 읽음** (sound, page UI, SCN, NPC).
2. ⭐⭐⭐ **ObjectA cluster 6 함수 본문 종합** → **acquire-use-release 라이프사이클 완성**:
   - **FUN_00097ffc / FUN_000980cc** (cmp #9 10-way dispatcher) = full lifecycle (cleanup → init → acquire → use)
   - **FUN_00097fa8** = byte setter + conditional vtable notify
   - **FUN_00098180** = 2-gate accessor
   - **FUN_000983b8** = ObjectA query w/ context_getter
   - **FUN_0004ad34** = ⭐⭐ task_ptr ↔ ObjectA bridge (ObjectB.method0 + method17 + ObjectA helpers)
3. ⭐⭐ **FUN_000439a0 (full 2372B) 49 arms BL 매핑** — orchestrator 패턴 확정:
   - **FUN_00047a14 (state transition) + FUN_00047a74** 호출 = Round 18 발견 함수와 직접 연결
   - 17 unique BL targets (0x4ad10 / 0x44534 / 0x445b8 / 0x47a14 / 0x47a74 / 0x464d0 등)
4. ⭐ **신규 veneer 0xa42a4 (bx r4)** — 기존 0xa42a0 (bx r3) 외 추가 발견 (FUN_0004ad34 에서 사용).

---

## 1. ObjectB (slot GOT+0x18) — 마스터 GVM 인터페이스 객체

### Reader 통계 (true PC-rel 패턴 매칭)

| Metric | 값 |
|---|---|
| Reader sites (정확 패턴) | **860** |
| Unique reader functions | **240** |
| Direct writes | 0 (GVM 외부 주입) |
| 패턴 | `ldr Rx, [pc, #imm]` (lit=0x18) + `add Rx, sl` |

### Top 20 reader functions

| 함수 | reads | 정체 |
|---|---|---|
| FUN_0003d5d0 | **31x** | sound subsystem dispatcher (PM-3) |
| FUN_00030018 | 26x | unknown — ObjectB heavy user |
| FUN_0002ce08 | 25x | unknown |
| FUN_0004d238 | 23x | unknown |
| FUN_000682ec | 22x | unknown |
| FUN_0002e80c | 21x | unknown |
| FUN_0008beba | 21x | unknown |
| FUN_0008e89e | **20x** | **SCN dispatcher tail** (§4.4) |
| FUN_00086a04 | 18x | unknown |
| FUN_0005d214 | **17x** | **page 0 dispatcher** (jt @ 0xa9cc4) |
| FUN_00060ab4 | **17x** | **mode 2 / page 2 UI** (PM-2) |
| FUN_00038dbc | 15x | unknown |
| FUN_00032880 | 14x | unknown |
| FUN_000379e8 | 13x | unknown |
| FUN_0005f948 | 13x | page 1 dispatcher (jt @ 0xa9d70) |
| FUN_00066244 | 13x | unknown |
| FUN_00050048 | 12x | unknown |
| FUN_00001fa4 | 10x | unknown |
| FUN_0004cf18 | 10x | unknown |
| FUN_0006ad8e | 10x | unknown |

### ⭐⭐⭐ 핵심 결론

**ObjectB 는 게임의 모든 핵심 subsystem 이 사용하는 마스터 GVM API 객체**:
- sound (FUN_0003d5d0)
- page 0/1/2 UI (FUN_0005d214 / FUN_0005f948 / FUN_00060ab4)
- SCN dispatcher (FUN_0008e89e)
- 그 외 240 함수

ObjectA (slot 0x44c, 8-함수 모듈) 는 ObjectB 의 sub-system 중 하나 (resource manager). ObjectB 는 훨씬 광범위 — 게임 전체의 GVM-side 진입점.

### 슬롯 그룹 재분류

| 슬롯 | 역할 | scale |
|---|---|---|
| **0x18** ⭐⭐⭐ | **마스터 GVM 인터페이스 (ObjectB)** | **860 readers / 240 funcs** |
| 0x16c | alternate task_struct ptr | 147 readers |
| 0x9c70 | widespread task data | 112 readers |
| 0x444 | primary task_ptr_ptr | 60+ readers |
| 0x44c | ObjectA (resource manager) | 8 readers (cluster) |
| 기타 11 슬롯 | 각각 1~30 readers | small/medium |

**0x18 가 압도적**으로 핵심. 모든 GVM API 호출의 진입점.

---

## 2. FUN_00099a9c ObjectB slot 식별 (2AL)

### 디스어셈블 추적

```asm
0x00099aa4  ldr   r3, [pc, #0x7c]   ; r3 = lit @ 0x99b24 = 0x1918e (GOT base offset, PIC)
0x00099aa6  mov   sl, r3
0x00099aac  ldr   r3, [pc, #0x78]   ; r3 = lit @ 0x99b28 = 0x18 (slot offset)
0x00099aae  add   sl, pc             ; sl = GOT base
0x00099ab0  add   r3, sl             ; r3 = GOT + 0x18 = 0xb2c58 (= ObjectB slot)
0x00099ab2  ldr   r6, [r3]           ; r6 = *(slot 0x18) = ObjectB ptr
0x00099ab4  ldr   r3, [r6]            ; r3 = ObjectB[0] = vtable
0x00099ab8  ldr   r3, [r3, #0x7c]    ; vtable[0x7c] = method31
```

### 결론

⭐⭐⭐ **FUN_00099a9c 의 "ObjectB" = slot 0x18** = Round 19 의 "vtable task_struct" 슬롯과 **동일**. 즉 **ObjectB 는 Round 19 에서 이미 부분적으로 발견된 객체**.

Round 19 의 FUN_00098244 도 같은 slot 사용:
```
ldr r3, [pc, #0x38]; add r3, sl; ldr r3, [r3]; ldr r3, [r3]   ; double indir
ldr r3, [r3, #0x58]   ; vtable[0x58]
```

→ FUN_00098244, FUN_00099a9c, FUN_0004ad34, 240 다른 함수 모두 **같은 ObjectB 객체 의 vtable methods** 호출.

### ObjectB vtable methods (현재까지 발견)

| offset | method index | 사용처 | 추정 의미 |
|---|---|---|---|
| 0 | method0 | FUN_00098244 (Round 19), FUN_0004ad34 | base method (init / dispatch) |
| 0x10 | method4 | FUN_00098244 | unknown |
| 0x20 | method8 | FUN_00098244 | unknown |
| 0x44 | method17 | FUN_0004ad34 | setup w/ 2-arg |
| 0x54 | method21 | FUN_00099a9c | resource read |
| 0x58 | method22 | FUN_00099a9c, FUN_00098244 | cleanup / release |
| 0x68 | method26 | FUN_00097fa8, FUN_00098244 | state notify |
| 0x7c | method31 | FUN_00099a9c | resource acquire (returns -12 / 0) |
| 0x80 | method32 | FUN_00099a9c | resource write (returns -18 가능) |

⭐ vtable 가 최소 0x80+ bytes (method32+) — 큰 인터페이스. 더 많은 vtable methods 는 240 readers 분석으로 추가 매핑 가능.

---

## 3. ObjectA cluster 6 함수 분석 종합 (2AK)

### 6 함수 분석 결과

#### FUN_0004ad34 (96B, 0 cmp) — task_ptr ↔ ObjectA bridge

```asm
;; ObjectB call 1
add r3, sl; ldr r3, [r3]; ldr r3, [r3]   ; ObjectB ptr → vtable
ldr r2, [pc, #0x3c]; ldr r4, [r3]        ; r4 = vtable[0] = method0
movs r1, #2; movs r3, #0; movs r0, #0
bl 0xa42a4                                ; ⭐ veneer 0xa42a4 = bx r4 (NEW!)
                                          ; → ObjectB.method0(0, 2, lit, 0)

;; ObjectB call 2
add r3, sl; ldr r3, [r3]; ldr r3, [r3]
movs r1, #1
ldr r3, [r3, #0x44]                       ; vtable[0x44] = method17
movs r0, #3
bl 0xa42a0                                ; ObjectB.method17(3, 1)

;; ObjectA-related calls
add r3, sl; ldr r4, [r3]                  ; r4 = ObjectA ptr
adds r0, r4, #0; bl 0x4884c                ; FUN_0004884c(ObjectA)
adds r0, r4, #0; bl 0x48970                ; FUN_00048970(ObjectA)
```

**정체**: Subsystem init function — ObjectB.method0(0,2,?,0) → ObjectB.method17(3,1) → 2 ObjectA helper calls. 이 함수는 task_ptr cluster (PM-7) 의 일부지만 ObjectA 도 사용 = **task_ptr cluster ↔ ObjectA cluster 의 brige**.

#### FUN_00097fa8 (84B, 1 cmp #0) — byte setter + conditional notify

```asm
;; SETUP
add r3, sl; ldr r3, [r3]   ; ObjectA ptr
strb param1_byte, [r3]      ; ⭐ ObjectA[0] = param1 byte

;; READ-BACK
add r3, sl; ldr r3, [r3]; ldr r0, [r3]   ; r0 = ObjectA[0] (just-stored byte)
cmp r0, #0
bne 0x97fd6                  ; if non-zero → notify

;; FALL-THROUGH (zero) — return
;; NOTIFY (non-zero):
0x97fd6:
add r3, sl; ldr r3, [r3]; ldr r3, [r3]   ; ObjectB ptr → vtable
ldr r3, [r3, #0x68]                       ; vtable[0x68] = method26
bl 0xa42a0                                 ; ObjectB.method26(r0=byte, r1=signed_byte)
```

**정체**: Setter w/ conditional ObjectB notify. 패턴: "set state byte; if state != 0, tell ObjectB".

#### FUN_00097ffc (208B, cmp #9) — full lifecycle dispatcher ⭐⭐

```asm
;; GATE
cmp r0, #9; bls 0x98020   ; if param1 <= 9, proceed; else return

;; FULL LIFECYCLE:
0x98020:
bl 0x98364                  ; ⭐ destructor (cleanup previous resource)

add r3, sl; ldr r3, [r3]   ; ObjectA ptr → vtable
add r4, sp, #4              ; r4 = &local
ldr r1, [other_slot]        ; r1 = some context
adds r0, r4, #0; ldr r3, [r2, #4]   ; r3 = vtable[4] = method1
adds r2, r5, #0
bl 0xa42a0                  ; ObjectA.method1(&local, ctx, param1)

adds r0, r4, #0; mov r1, sp
bl 0x99a9c                  ; ⭐ resource acquisition

;; USE (multi-vtable invoke, similar to FUN_00098244)
add r3, sl; ldr r5, [r3]    ; r5 = *(slot)
... ldr r3, [r3, #0x10]; bl 0xa42a0      ; vtable[0x10]
... ldr r3, [r3, #0x58]; bl 0xa42a0      ; vtable[0x58] cleanup
... ldr r3, [r3, #0x20]; bl 0xa42a0      ; vtable[0x20]
... ldr r3, [r3, #0x68]; bl 0xa42a0      ; vtable[0x68] notify

b 0x98016   ; common epilogue
```

**정체**: ⭐⭐⭐ **complete lifecycle entry point** (cmp #9 = 10-state gate). cleanup → ObjectA.method1 → resource acquire → multi-vtable use → epilogue.

이 함수는 FUN_00098244 (use only) + FUN_00098364 (destructor) + FUN_00099a9c (acquire) 를 한 번에 호출 = **wholesale state transition**. 

#### FUN_000980cc (180B, cmp #9) — sister dispatcher

같은 cmp #9 패턴. 아마 다른 lifecycle entry (acquire+use 만, destructor 없이?).

#### FUN_00098180 (196B, 2 cmp #0) — gate accessor

2 cmp #0 = double null gate (e.g., `if (a && b)` style). small accessor function.

#### FUN_000983b8 (188B, 3 cmp #0 + context_getter) — ObjectA query w/ context

context_getter 1 호출 + 3 cmp #0 gates. ObjectA 와 글로벌 context 를 함께 다루는 query function.

### ObjectA + ObjectB lifecycle 패턴 종합

```
        type-9 entry (FUN_00097ffc — main path)
            ├─ FUN_00098364 (destructor)         — clear previous
            │      └─ ObjectB.vtable[0x1c/0x2c/0xc] (cleanup methods)
            │
            ├─ ObjectA.method1 (vtable[4])        — init / setup
            │
            ├─ FUN_00099a9c (resource acquisition) — alloc/open
            │      └─ ObjectB.vtable[0x7c]        (acquire, returns -12 ENOMEM or 0)
            │      └─ ObjectB.vtable[0x54]        (read)
            │      └─ ObjectB.vtable[0x58]        (cleanup-on-error)
            │      └─ ObjectB.vtable[0x80]        (write, returns -18 EXDEV)
            │
            ├─ ObjectB.vtable[0/0x10/0x20/0x58/0x68]   (use phase)
            │
            └─ epilogue
```

이는 **acquire-use-release 라이프사이클 패턴** 의 완전한 형태. RTOS-like resource management.

---

## 4. FUN_000439a0 49 arms BL 매핑 (2AM)

### BL target frequency (top 17 unique targets)

| target | calls | 정체 |
|---|---|---|
| **0x4ad10** | 2x | task_ptr_getter / context_getter |
| 0x44534 | 1x | (in FUN_000439a0 region) |
| 0x445b8 | 1x | (in FUN_000439a0 region) |
| **0x47a14** | 1x | ⭐ **FUN_00047a14 — state transition** (Round 18) |
| **0x47a74** | 1x | ⭐ **FUN_00047a74 — state transition sister** |
| 0x464d0 | 1x | unknown 0x46xxx helper |
| 0x467a8 | 1x | unknown |
| 0x467d0 | 1x | unknown |
| 0x7d31c | 1x | far helper |
| 0x7cd58 | 1x | far helper |
| **0x99894** | 1x | ⭐ in 0x97fa8~0x9xxxx ObjectA module range |
| **0x9f82c** | 1x | ⭐ in FUN_00098244 cluster range |
| 0x43a68 | 1x | (FUN_000439a0 internal jump) |
| 0x43a5c | 1x | (FUN_000439a0 internal — type-4 fall-through) |
| 0x43a6a | 1x | (FUN_000439a0 internal) |
| 0x7a474 | 1x | far helper |
| 0x43a6e | 1x | (FUN_000439a0 internal — catch-all) |

### Per-cmp arm BL distribution (top arms)

| cmp imm | total BLs | 핵심 발견 |
|---|---|---|
| **cmp #0x00** | 10 BLs | task_ptr_getter, FUN_00047a14 (state transition), FUN_00047a74, 0x464d0, 0x467a8, 0x467d0, 0x445b8, 0x7cd58 — **gate 처리 다양** |
| cmp #0x02 | 3 BLs | 내부 jump (0x43a68, 0x43a5c) + task_ptr_getter |
| cmp #0x04 | 2 BLs | 0x7a474, 0x43a6e (catch-all) |
| cmp #0x07 | 1 BL | 0x44534 |
| cmp #0x0c | 1 BL | 0x7d31c |
| cmp #0x01 | 1 BL | 0x43a6a (internal) |

### ⭐⭐ 핵심 발견

**FUN_000439a0 = orchestrator** — Round 18 의 FUN_00047a14 (state transition) 를 **자기 dispatcher 의 cmp #0 arm 에서 직접 호출**. 즉:
- FUN_000439a0 ← Round 18 sub-handler 가 단순 helper 가 아니라 dispatcher
- FUN_00047a14 ← state-0xf transition 함수
- 다른 BL targets (0x464d0, 0x467a8, 0x467d0) = 추가 sub-handler 들 (다음 round 가치)

---

## 5. 신규 veneer 0xa42a4 발견

| veneer | 추정 instr | 사용처 |
|---|---|---|
| 0xa42a0 | `bx r3` | 모든 vtable indirect call (PM-7 발견) |
| **0xa42a4** | `bx r4` | FUN_0004ad34 의 첫 BL (NEW Round 21) |

veneer 영역 0xa42a0 ~ 0xa42ce (PM-7 에서 14 byte range 로 추정됨 = 7 veneer 가능). r3 외 r4/r5 등 다른 register 에 대한 indirect call veneer 가 있을 가능성.

다음 round 에서 0xa42a0~0xa42ce 영역 스캔 가치.

---

## 6. 다음 세션 권장 다음 단계 (Round 22 후보)

| # | 작업 | 명령 | 산출물 |
|---|---|---|---|
| ⭐⭐ 2AP | **ObjectB top reader 함수 본문** (FUN_0003d5d0/0x60ab4/0x5d214) | `disasm_subsystem_func.py` | sound/page UI 의 ObjectB vtable 사용 패턴 → vtable layout 종합 |
| ⭐⭐ 2AQ | **veneer 0xa42a0 ~ 0xa42ce 영역 스캔** | inline disasm 0xa42a0 0xa42ce | 모든 veneer (bx rN) 식별 |
| ⭐ 2AR | **FUN_00098364 + FUN_00097ffc 의 destructor vtable methods 완전 매핑** | 본문 분석 | ObjectA 와 ObjectB 의 명확한 분리 |
| 2AS | FUN_000439a0 의 0x464d0 / 0x467a8 / 0x467d0 본문 | `disasm_subsystem_func.py` | 추가 sub-handler 정체 |
| 2AT | FUN_000980cc (cmp #9 sister) 본문 비교 | 본문 분석 | FUN_00097ffc 와의 차이점 — partial vs full lifecycle |

---

## 7. 산출물

```
work/h3/objA_method_97fa8_disasm.json     ; 2AK
work/h3/objA_method_97ffc_disasm.json     ; 2AK
work/h3/objA_method_980cc_disasm.json     ; 2AK
work/h3/objA_method_98180_disasm.json     ; 2AK
work/h3/objA_method_983b8_disasm.json     ; 2AK
work/h3/task_objA_link_4ad34_disasm.json  ; 2AK
work/h3/global_slot_0x18_writers.json     ; 2AL (movw false-positives, 실제 패턴은 inline)
work/h3/popular_helper_439a0_full_arms.json ; 2AM
```

---

## 8. Round 21 핵심 takeaway

1. **ObjectB (slot 0x18) = 게임의 마스터 GVM 인터페이스 객체** — 860 readers / 240 functions. sound, page UI, SCN, NPC 등 모든 핵심 dispatcher 가 이 슬롯 사용. ObjectA (8-함수) 의 100x scale.
2. **ObjectB vtable 9 methods 매핑** — offset 0/0x10/0x20/0x44/0x54/0x58/0x68/0x7c/0x80. 다음 round 에서 더 많은 메소드 발견 가능.
3. **ObjectA cluster lifecycle 종합** — FUN_00097ffc 가 cleanup → init → acquire → use 의 **full lifecycle dispatcher**. 다른 5 함수는 해당 단계 단편.
4. **FUN_0004ad34 = task_ptr ↔ ObjectA bridge** — task_ptr cluster (PM-7) 와 ObjectA 의 명시적 연결고리. ObjectB 도 양쪽에서 사용.
5. **FUN_000439a0 = orchestrator** — 49 arms BL 매핑으로 Round 18 의 FUN_00047a14 (state transition) 를 직접 호출 확인. multi-system entry point.
6. **신규 veneer 0xa42a4 (bx r4)** 발견 — vtable indirect call 의 표준은 0xa42a0 (bx r3), 하지만 다른 register 변형 존재.
7. **POSIX-like errors (-12 ENOMEM / -18 EXDEV)** = ObjectB.vtable 이 RTOS-style resource API 임을 강력 시사. file/asset loading 또는 audio engine 후보.
