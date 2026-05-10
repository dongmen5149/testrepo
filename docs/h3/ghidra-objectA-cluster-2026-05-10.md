# Round 20 (2026-05-10 PM-10) — ObjectA cluster + init helpers + FUN_000439a0 SIZE 정정

## 요약

Round 19 의 vtable invoker 발견 후속. PM-10 의 핵심 진척:

1. ⭐⭐⭐ **FUN_000439a0 SIZE 대폭 정정** — 188B (pic_stubs) → **2372B 실제**. 0x43a5c~0x442e4 전 범위 (push prologue 0건) 가 함수 내부. **49 cmp arms** (이전 3 arms 의 16배). FUN_00043508 와 동일 4 GOT 슬롯 사용 (0x9bb4/0x9cbc/0x9cfe/0x9cc0).
2. ⭐⭐⭐ **ObjectA cluster 식별** (slot 0x44c readers 8 함수) — `FUN_00097fa8`, `FUN_00097ffc`, `FUN_000980cc`, `FUN_00098180`, `FUN_00098244`, `FUN_00098364`, `FUN_000983b8` (0x97fa8~0x98474, ~1.2KB) + `FUN_0004ad34` (외부 wrapper).
3. ⭐⭐ **FUN_00098364 = ObjectA destructor** (84B) — sub-object cleanup via vtable[0x1c/0x2c/0xc] + first field clear.
4. ⭐⭐ **FUN_00099a9c = resource acquisition with error handling** (144B) — vtable[0x7c/0x54/0x58/0x80] + POSIX 에러 코드 (-12 ENOMEM, -18 EXDEV).
5. ⭐⭐ **JT 7 targets = FUN_000439a0 내부 sub-paths 확정** — 모두 같은 stack frame 공유, recursive sub-call (0x43a5c, 0x43a6e 도 내부 BL 로 호출됨).

---

## 1. FUN_000439a0 SIZE 정정 (188B → 2372B)

### 발견 경로

Round 19 의 JT 디코드에서 type 7 → 0x44214, type 5/8 → 0x4425a 가 GAP 안의 주소임을 확인. 0x43a60 ~ 0x442e4 영역 push prologue 검색 → **0건**. 이 2.4KB 영역 전체가 단일 함수의 sub-paths.

### 새 metric

| 측면 | 188B 보기 | **2372B 실제** | 변화 |
|---|---|---|---|
| 크기 | 188 bytes | **2372 bytes** | ×12.6 |
| 명령어 수 | 90 | **1124** | ×12.5 |
| cmp arms | 3 | **49** | ×16 |
| context_getter calls | 2 | **4** | ×2 |
| GOT slots used | 3 (0x29e/0x9bb4/0x9cbc) | **4** (+ 0x9cfe, 0x9cc0) | +0x9cc0/0x9cfe |

### Cmp 분포 (full)

| imm | 개수 | 의미 추정 |
|---|---|---|
| 0x00 | 17 | gate / null check (압도적) |
| **0x06** | **10** ⭐ | **cmp #6 dominant** — type-6 처리 핵심 |
| 0x09 | 3 | type-9 |
| 0x01 | 3 | type-1 |
| 0x10 | 2 | (16 진수 16) |
| 0x07 | 2 | type-7 |
| **0xa0** | **2** ⭐ | **cmp #0xa0 (160)** — record offset 또는 임계값 |
| 0x08 | 2 | type-8 |
| 0x02 | 2 | type-2 |
| 기타 | 8 | 0x03/0x04/0x0a/0x0c/0x0e/0x1e 등 1x씩 |

### FUN_00043508 와의 관계

| 함수 | size | cmp arms | GOT slots | 정체 |
|---|---|---|---|---|
| **FUN_000439a0** (정정) | 2372B | 49 | 0x9bb4/9cbc/9cfe/9cc0 | type-mixed (cmp #6 dominant) |
| **FUN_00043508** | 1176B | 24 | 0x9bb4/9cbc/9cfe/9cc0 | type-9 specialized |

**동일한 4 GOT 슬롯 → 동일한 record array (0x9cbc) 의 2개 처리자**. FUN_000439a0 가 main dispatcher (multi-type), FUN_00043508 가 type-9 특화. 다른 sibling 들도 존재할 가능성 (다음 round 검색 가치).

### JT @ 0xa8370 의 7 targets (Round 19 디코드)

이제 모두 FUN_000439a0 내부 sub-paths 임이 확정:

```
JT entry:  type → label_addr (sub-path within FUN_000439a0)
  0  type 4  → 0x43a5a  (fall-through, near dispatcher)
  1  type 5  → 0x4425a  (sub-path B)
  2  type 6  → 0x43a6e  (catch-all = bhi default)
  3  type 7  → 0x44214  (sub-path C, 3-state byte dispatch)
  4  type 8  → 0x4425a  (= type 5)
  5  type 9  → 0x43a6e  (= catch-all)
  6  type 10 → 0x43a6e  (= catch-all)
```

검증 — 각 target 의 실제 코드:

```asm
;; type 7 target (0x44214):
0x00044214  ldr   r0, [sp+0x24]      ; ← shared stack frame (set by prologue)
0x00044216  movs  r3, #0
0x00044218  ldrsb r3, [r0, r3]        ; r3 = signed byte at *r0
0x0004421a  cmp   r3, #2
0x0004421c  beq   0x44254
0x0004421e  cmp   r3, #2; bgt 0x44234
0x00044222  cmp   r3, #1; beq 0x4422a
0x00044226  bl    0x43a6e             ; ⭐ recursive call to catch-all path!

;; type 5/8 target (0x4425a):
0x0004425a  movs  r4, #2
0x0004425c  bl    0x43a5c             ; ⭐ recursive call to type-4 fall-through!
0x00044260  bl    0x4ad10             ; context_getter (#0x1 arg, identified)
0x00044264  ldr   r1, [pc, #0x64]     ; literal 0x9cc0 (slot)
0x00044266  adds  r0, r0, r1; ...

;; catch-all (0x43a6e):
0x00043a6e  lsls  r5, r5, #0x18
0x00043a70  movs  r1, #0
0x00043a72  str   r5, [sp+8]; str r1, [sp+0x2c]   ; ← shared stack frame access
0x00043a76  cmp   r5, #0; bgt 0x43a7c
0x00043a7a  b     0x43bca              ; jump to another internal sub-path
```

⭐ 각 sub-path 가 **`bl` 로 다른 sub-path 호출** (예: 0x44226 BL → 0x43a6e). 즉, 같은 함수 내에서 sub-path 끼리 마치 별도 함수처럼 호출하는 패턴 = **컴파일러가 큰 switch 를 작은 helper-like 함수로 인라인** 생성. Ghidra 가 BL target 을 별도 함수로 인식해서 pic_stubs 에서 188B 만 보고했음.

### 결론

**FUN_000439a0 = 2372B mega-dispatcher** (49 cmp arms). cmp #6 dominant + cmp #9 / cmp #1 / cmp #0xa0 multi-arm. JT 7-target 은 함수 내부 labeled sub-paths.

---

## 2. ObjectA Cluster — slot GOT+0x44c readers 8 함수

### 발견 (slot 0x44c writer trace)

| 주소 | 추정 size | 정체 가설 |
|---|---|---|
| **FUN_0004ad34** | (외부) | task_ptr_wrapper API (PM-7 의 0x4ad10-0x4af10 cluster 일부) |
| **FUN_00097fa8** | ~84B | ObjectA query/getter |
| **FUN_00097ffc** | ~208B | ObjectA setter? |
| **FUN_000980cc** | ~180B | ObjectA method dispatch A |
| **FUN_00098180** | ~196B | ObjectA method dispatch B |
| **FUN_00098244** | ~288B | ⭐⭐⭐ **vtable invoker** (Round 19 분석) |
| **FUN_00098364** | ~84B | ⭐ **destructor** (이번 round 분석) |
| **FUN_000983b8** | ~188B | ObjectA 또 다른 method |

⭐ **0x97fa8 ~ 0x98474 (~1.2KB) = ObjectA C++ class 구현 모듈**. 7 method 함수 + 외부 wrapper FUN_0004ad34 (task_ptr API) = 단일 클래스의 namespace. 이 영역 전체가 한 subsystem (audio/animation/save 의 핵심 모듈 후보).

⭐ **FUN_0004ad34 가 ObjectA cluster 와 연결** = task_ptr_wrapper 가 ObjectA API 를 사용하거나 그 반대. Round 18 의 0x4ad10 cluster 와 ObjectA 모듈 사이 연결고리 발견.

---

## 3. FUN_00098364 본문 — ObjectA destructor (84B)

### 디스어셈블

```asm
0x00098364  push  {r4, r5, lr}; mov r5, sl; push {r5}
0x0009836a  ldr   r3, [pc, #0x40]   ; r3 = literal1 (GOT base offset)
0x0009836c  mov   sl, r3
0x0009836e  ldr   r3, [pc, #0x40]   ; r3 = 0x44c (ObjectA slot offset)
0x00098370  add   sl, pc             ; sl = 0xb2c40 (GOT base, PIC)
0x00098372  add   r3, sl             ; r3 = 0xb308c (ObjectA slot)
0x00098374  ldr   r5, [r3]           ; r5 = *(0xb308c) = ObjectA ptr
0x00098376  ldr   r0, [r5]           ; r0 = ObjectA[0] = sub_obj_ptr (or flag)

0x00098378  cmp   r0, #0
0x0009837a  bne   #0x98382          ; if non-null → cleanup

;; FALL-THROUGH: ObjectA[0] == 0 → no-op return
0x0009837c  pop   {r3}; mov sl, r3
0x0009837e  pop   {r4, r5, pc}      ; RETURN

;; CLEANUP path (ObjectA[0] != 0):
0x00098382  ldr   r3, [pc, #0x30]   ; r3 = ANOTHER slot offset
0x00098384  add   r3, sl
0x00098386  ldr   r4, [r3]           ; r4 = *(slot) = sub-object ptr (parent)
0x00098388  ldr   r3, [r4]           ; r3 = vtable
0x0009838a  ldr   r3, [r3, #0x1c]    ; vtable[0x1c] = method7
0x0009838c  bl    #0xa42a0            ; ⭐ indirect call vmethod[0x1c]
                                      ; (no args set, only r0 = ObjectA[0] from before)

0x00098390  ldr   r3, [r4]; ldr r0, [r5]
0x00098394  ldr   r3, [r3, #0x2c]    ; vtable[0x2c] = method11
0x00098396  bl    #0xa42a0           ; ⭐ indirect call vmethod[0x2c]

0x0009839a  ldr   r3, [r4]; ldr r0, [r5]
0x0009839e  ldr   r3, [r3, #0xc]     ; vtable[0xc] = method3
0x000983a0  bl    #0xa42a0           ; ⭐ indirect call vmethod[0xc]

0x000983a4  movs  r3, #0
0x000983a6  str   r3, [r5]            ; ⭐⭐ ObjectA[0] = NULL  (CLEAR)
0x000983a8  b     #0x9837c            ; jump to common epilogue
```

### 정체 확정

| 측면 | 발견 |
|---|---|
| **함수 종류** | **resource destructor** (= C++ destructor / cleanup func) |
| **분기** | 1 cmp (gate: ObjectA[0] != 0?) |
| **vtable methods 호출** | `[0x1c]`, `[0x2c]`, `[0xc]` — 3 cleanup methods |
| **side effect** | ObjectA[0] = NULL (resource 해제 표시) |
| **idempotent** | 첫 필드가 이미 0 이면 no-op |

### 패턴

**Resource handle pattern**:
- ObjectA = "resource manager"
- ObjectA[0] = "current resource handle" (또는 first field flag)
- alloc: 누군가 ObjectA[0] = handle 셋팅
- use: vtable methods 호출 (FUN_00098244 처럼)
- free: 본 함수 — vtable cleanup methods 호출 + ObjectA[0] = NULL

⭐⭐ FUN_00098244 (Round 19) + FUN_00098364 (Round 20) = **acquire-use-release 라이프사이클**. 이는 **audio engine 또는 animation engine** 의 resource management 패턴.

---

## 4. FUN_00099a9c 본문 — Resource acquisition with error handling (144B)

### 디스어셈블 핵심 흐름

```asm
0x00099a9c  push  {r4-r7,lr}; mov r7,sl; mov r6,r8; push {r6,r7}
0x00099aa4  ldr   r3, [pc, #0x7c]   ; GOT base offset
0x00099aa8  movs  r3, #0; mov r8, r3
0x00099aac  ldr   r3, [pc, #0x78]   ; another slot offset
0x00099ab0  add   r3, sl             ; absolute slot
0x00099ab2  ldr   r6, [r3]           ; r6 = *(slot) = ObjectB ptr (다른 객체)
0x00099ab4  ldr   r3, [r6]            ; r3 = ObjectB[0] = vtable
0x00099ab8  ldr   r3, [r3, #0x7c]    ; vtable[0x7c] = method31
0x00099aba  adds  r7, r1, #0          ; r7 = param2 (output ptr)
0x00099abc  mov   r1, sp               ; r1 = &local
0x00099abe  bl    #0xa42a0            ; ⭐ call vmethod[0x7c] (r0=param1, r1=&local)

0x00099ac2  movs  r3, #0xc; rsbs r3, r3, #0   ; r3 = -12 (= -ENOMEM 후보)
0x00099ac8  cmp   r0, r3
0x00099aca  beq   #0x99b1e            ; ERROR PATH: result == -12

0x00099acc  ldr   r3, [r6]; ldr r0, [sp]
0x00099ad0  ldr   r3, [r3, #0x54]    ; vtable[0x54] = method21
0x00099ad2  bl    #0xa42a0            ; ⭐ call vmethod[0x54]

0x00099ad6  adds  r5, r0, #0
0x00099ad8  cmp   r0, #0
0x00099ada  bne   #0x99af4            ; if result != 0, take SECOND path

;; PRIMARY PATH (result == 0):
0x00099adc  ldr   r3, [r6]; movs r0, #0
0x00099ae0  ldr   r3, [r3, #0x58]    ; vtable[0x58] = method22 (cleanup?)
0x00099ae2  bl    #0xa42a0
0x00099ae6  str   r5, [r7]            ; *output = 0
0x00099ae8  movs  r0, #0
0x00099aea  add   sp, #4; pop {r3,r4}
0x00099af0  mov   sl, r4
0x00099af2  pop   {r4,r5,r6,r7, pc}    ; RETURN 0

;; SECONDARY PATH (result != 0):
0x00099af4  ldr   r3, [r6]; adds r3, #0x80; ldr r3, [r3]   ; r3 = vtable[0x80] (= method32)
0x00099afa  adds  r0, r4, #0; adds r1, r5, #0; ldr r2, [sp]
0x00099b00  bl    #0xa42a0            ; ⭐ call vmethod[0x80]

0x00099b04  movs  r3, #0x12; rsbs r3, r3, #0   ; r3 = -18 (= -EXDEV?)
0x00099b08  cmp   r0, r3
0x00099b0a  beq   #0x99b14
0x00099b0c  ldr   r3, [sp]; str r3, [r7]; adds r0, r5, #0
0x00099b12  b     #0x99aea

;; cleanup-after-fail:
0x00099b14  ldr   r3, [r6]; adds r0, r5, #0
0x00099b18  ldr   r3, [r3, #0x58]    ; vtable[0x58] cleanup
0x00099b1a  bl    #0xa42a0

;; ERROR PATH (-12):
0x00099b1e  mov   r3, r8              ; r3 = 0
0x00099b20  str   r3, [r7]; b 0x99ae8 ; *output = 0, return 0
```

### 정체 확정

| 측면 | 발견 |
|---|---|
| **함수 종류** | **resource acquisition with error handling** |
| **객체** | ObjectB @ 다른 GOT 슬롯 (vtable 더 큰 — 0x7c, 0x80 까지 method index 사용) |
| **vmethod 호출** | `[0x7c]` (acquire), `[0x54]`, `[0x58]` (cleanup), `[0x80]` |
| **에러 코드** | -12 (ENOMEM), -18 (EXDEV) — POSIX-like error codes |
| **error handling** | acquire 실패 시 *output = 0 / cleanup methods 호출 |

### 가설

- ObjectB 의 vtable 이 0x80+ 까지 = ObjectA (0x68 max) 보다 더 큰 인터페이스
- POSIX 에러 코드 사용 = **Symbian/Linux-like RTOS** 인터페이스
- 호출 패턴: try acquire → check error → cleanup or use → store result
- 후보: **file/asset loading** (acquire = open, cleanup = close), **memory allocation wrapper**

---

## 5. GOT 슬롯 누적 통계 (Round 18~20)

### 추가 발견 슬롯 (Round 20)

이번 round 에서는 신규 GOT 슬롯 발견 0건 — 기존 14 슬롯 + ObjectB slot (init helpers 에서 등장) 가 추가 후보 (다음 round 에서 식별).

### 확정된 슬롯 그룹 매핑

| 그룹 | 슬롯 | 역할 |
|---|---|---|
| **Task pointers** | 0x18, 0x16c, 0x444 | task_struct ptrs (다양한 indirection level) |
| **State/flag** | 0x128, 0x29e, 0x9e78 | state-byte / flag |
| **ObjectA C++ class** | 0x44c | resource manager pointer ⭐ |
| **Helper data** | 0xd00, 0xd04, 0xd08 | data table ptrs (FUN_00098244 used) |
| **Record array** | 0x9bb4, 0x9cbc, 0x9cfe, 0x9cc0 | 0x38 stride record array (FUN_000439a0/43508 공유) |
| **Widespread** | 0x9c70, 0x9c71, 0x9c84, 0xac78 | task data (PM-7) |

**총 14 슬롯 확정 + 1 ObjectB 후보** = 15 GOT 슬롯 매핑. 모두 0 direct writes (시스템 표준).

---

## 6. 다음 세션 권장 다음 단계 (Round 21 후보)

| # | 작업 | 명령 | 산출물 |
|---|---|---|---|
| ⭐⭐ 2AK | **ObjectA cluster 의 6 함수 본문 일괄** (FUN_00097fa8 ~ FUN_000983b8 중 미분석 6개) | `disasm_subsystem_func.py` 6번 호출 | ObjectA 의 vtable layout 종합 (vmethod offset → 의미) |
| ⭐⭐ 2AL | **FUN_00099a9c 의 ObjectB slot offset 식별** | 본문 PC-rel literal 1번째 값을 GOT base 와 비교 | ObjectB 정체 — 새 cluster 발견 가능 |
| ⭐ 2AM | **FUN_000439a0 full (2372B) cmp #6 10x arm 별 BL 매핑** | `analyze_arm_handlers.py 0x439a0 0x442e4` | 49 arms 의 sub-handler 매핑 |
| 2AN | FUN_00043508 와 FUN_000439a0 의 sibling 들 검색 | 4 슬롯 (0x9bb4/9cbc/9cfe/9cc0) 모두 readers 합집합 | 같은 record array 처리하는 모든 함수 |
| 2AO | FUN_0004ad34 본문 (ObjectA + task_ptr 연결고리) | `disasm_subsystem_func.py 0x4ad34 0x4ad7c` | task_ptr_wrapper API 와 ObjectA 의 관계 |

---

## 7. 산출물

```
work/h3/popular_helper_439a0_full_disasm.json   ; 2AH (FUN_000439a0 정정 사이즈)
work/h3/vtable_init_98364_disasm.json           ; 2AF
work/h3/setup_helper_99a9c_disasm.json          ; 2AF
work/h3/global_slot_0x44c_writers.json          ; 2AG
```

---

## 8. Round 20 핵심 takeaway

1. **FUN_000439a0 size 188B → 2372B** — pic_stubs 의 size 추정이 frequent BL 로 인한 함수 boundary 오인. 실제로는 49 cmp arm mega-dispatcher.
2. **ObjectA C++ class 구현 모듈 발견** (0x97fa8~0x98474, ~1.2KB, 7 methods + 1 external wrapper) — slot 0x44c = resource manager 객체 ptr.
3. **acquire-use-release 라이프사이클 패턴 확정** — FUN_00099a9c (acquire w/ error handling) → FUN_00098244 (vtable invoker, use) → FUN_00098364 (destructor, release).
4. **POSIX-like error codes (-12 ENOMEM, -18 EXDEV)** = Symbian/RTOS-like 인터페이스 = GVM API 의 game-side 호출 표준.
5. **task_ptr_wrapper 와 ObjectA 연결** — FUN_0004ad34 (PM-7 task_ptr cluster 일부) 가 slot 0x44c 도 사용 → 두 시스템 간 연결고리 발견.
6. **JT 7 targets = 함수 내부 sub-paths** — 모두 같은 stack frame 공유, recursive sub-call (`bl 0x43a6e` 등). 컴파일러가 큰 switch 를 helper-like 함수로 인라인 생성한 흔적.
