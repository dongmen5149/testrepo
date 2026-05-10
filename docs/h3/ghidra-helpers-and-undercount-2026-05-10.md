# Hero3 Ghidra — Round 26 / PM-16 (2026-05-10)
## FUN_0007d31c + FUN_0007cd58 helper 정체 정정 + auto 도구 undercount 발견

> Round 25 의 helper 가설 2건 (bit op / vtable invoker) 을 본문 분석으로 검증한 결과, 두 가설 모두 부정확. 또 `find_task_struct_field_readers.py` 의 auto 통계가 wide-scan 대비 system-wide undercount 임을 확인.

## TL;DR (3줄)

1. ⭐⭐⭐ **FUN_0007d31c ≠ 단순 bit op helper**. 660 byte multi-stage 함수, 318 instr, 23 cmp arms, 8x unrolled `cmp r3, #0; beq 0x7d48a` 패턴. **`ldr r3, [r0, #0x1c]` 가 caller 의 `task_ptr+0x9bb4+0x1c` = `task_ptr+0x9bd0` 을 dereference** → bit flag (0x9bb4) 와 ptr-to-object (0x9bd0) 가 **같은 substructure 의 멤버**.
2. ⭐⭐⭐ **FUN_0007cd58 ≠ vtable invoker**. 1068 byte leaf function, **GOT 미사용** (0 PC-rel literals), 0 BL targets. `ldrh [r0+0x10]; asrs >>0x10; >>4` 후 6 signed branches. Vtable+0x18 의 halfword metadata 산술 helper.
3. ⭐⭐ **`find_task_struct_field_readers.py` auto 통계 = system-wide undercount**. 0x9c70 cluster auto = 0 hits, wide-scan = 303 sites (= 100% miss). 0x9b14 cluster auto = 0, 실측 21+ refs. **PM-7 의 0x9bb4 dominant 통계 (69 sites, 15 funcs) 도 undercount 가능성**.

부수 발견:
- ⭐⭐ **0x9bd0 ptr-to-object = 14 unique funcs 에서 사용** (system-wide 핵심 object). Round 25 의 "FUN_0009a008 안 3 사이트" 가 sub-snapshot.
- ⭐ **0x9bb4~0x9bd0 = 32 byte substructure**: offset 0 (bit flags) + offset 0x1c (ptr-to-object). Object-style 메타데이터 블록.
- ⭐ FUN_00041c6e 가 0x9cb8/9cbc 둘 다 dominant reader (3x/3x).

## 1. FUN_0007d31c (Round 25 의 "bit helper" 가설 정정)

### 1.1 Boundary 와 prologue

| 측면 | 값 |
|---|---|
| 시작 | 0x7d31c |
| 끝 | 0x7d5b0 (다음 push prologue) |
| size | 660 byte (0.6KB) |
| instr | 318 |
| cmp arms | 23 (`cmp #0` 20x dominant) |
| context_getter calls | 1 (early, 0x7d33c) |

```asm
0x7d31c: push {r4-r7, lr}
0x7d31e: mov r7, sl
0x7d320: mov r6, r8
0x7d322: push {r6, r7}             ; PIC standard prologue
0x7d324: ldr r3, [pc, #0x278]       ; GOT base offset
0x7d326: mov sl, r3
0x7d328: ldr r3, [r0, #0x1c]        ; <-- 핵심: r0+0x1c dereference
0x7d32a: ldr r3, [r3]
0x7d32c: sub sp, #0x80
0x7d32e: lsls r1, r1, #0x18
0x7d330: adds r3, #8                ; vtable+8
0x7d332: add sl, pc                  ; GOT base resolve
0x7d334: lsrs r5, r1, #0x18         ; r5 = unsigned byte of r1
0x7d336: str r2, [sp, #0x2c]        ; r2 saved (stack output buffer)
0x7d338: mov r8, r3                  ; r8 = vtable+8 (saved)
```

### 1.2 핵심 발견 — r0+0x1c

Caller 가 `task_ptr+0x9bb4` 를 r0 로 전달했으니:
```
r0+0x1c = task_ptr + 0x9bb4 + 0x1c = task_ptr + 0x9bd0
```

→ **task_ptr+0x9bd0 (= ptr-to-object slot)** 를 dereference.

즉 **task_struct[0x9bb4] (bit flags) 와 task_struct[0x9bd0] (ptr-to-object) 는 동일 substructure 의 두 멤버**:
- offset 0~0x1b: bit flags 영역 (~28 byte)
- offset 0x1c: ptr-to-object (vtable 포함)

이 함수가 **substructure 의 bit flags 와 ptr-to-object 를 함께 처리** → **object-style 메타데이터 블록 처리**.

### 1.3 23 cmp arms 의 패턴

```
cmp #0x00: 20x   ; if-zero check
cmp #0x04: 2x    ; bound/state check
cmp #0x01: 1x    ; binary state
```

**8번 반복 패턴** (0x7d438~0x7d462):
```asm
cmp r3, #0x00 → beq 0x7d48a        ; jump to common 'done'
... (test next bit) ...
cmp r3, #0x00 → beq 0x7d48a
... (8 times)
```

→ **8 bit unrolled scan**. r1 = mask 의 8 bit 를 각각 검사하면서 (set 된 bit 마다 처리). 이는 단순 `set/clear/test` bit op 가 아닌 **bit-by-bit conditional dispatcher**.

### 1.4 의미 추정 (가설)

**FUN_0007d31c = "for each set bit in mask, run handler"** loop. 8 bit max (= byte mask), 각 bit 마다 vtable[8] 의 method 호출 또는 substructure 의 ptr-to-object 의 멤버 처리.

caller 의 r2 = stack output buffer (0x3c byte) → 결과를 buffer 에 누적.

## 2. FUN_0007cd58 (Round 25 의 "vtable invoker" 가설 정정)

### 2.1 Boundary 와 prologue

| 측면 | 값 |
|---|---|
| 시작 | 0x7cd58 |
| 끝 | 0x7d184 (다음 push prologue) |
| size | 1068 byte (1.0KB) |
| instr | 534 |
| cmp arms | 6 (모두 `cmp r3, #0` `bge`) |
| BL targets | **0** (= leaf function) |
| PC-rel literals | **0** (= GOT 미사용) |

```asm
0x7cd58: push {r7, lr}                ; <-- leaf wrapper (no PIC setup)
0x7cd5a: mov r7, sp
0x7cd5c: sub sp, #4
0x7cd5e: subs r3, r7, #4
0x7cd60: str r0, [r3]                 ; r0 saved to local
0x7cd62: subs r3, r7, #4
0x7cd64: ldr r1, [r3]                 ; r1 = r0 (saved)
0x7cd66: subs r3, r7, #4
0x7cd68: ldr r3, [r3]                 ; r3 = r0
0x7cd6a: ldrh r3, [r3, #0x10]         ; <-- r3 = halfword at r0+0x10
0x7cd6c: lsls r3, r3, #0x10
0x7cd6e: asrs r3, r3, #0x10           ; sign-extend to 16-bit
0x7cd70: asrs r3, r3, #4              ; arith shift right by 4 (= signed div 16)
0x7cd72: adds r2, r3, #0              ; r2 = (val/16)
0x7cd74: adds r3, r1, #0              ; r3 = saved r0
```

### 2.2 핵심 발견 — leaf + GOT 미사용

- **0 PC-rel LDR literals**: GOT 를 전혀 사용하지 않음 (= 외부 데이터/함수 의존성 없음)
- **0 BL targets**: 다른 함수 호출 없음 (= leaf function)
- **6 cmp `bge` only**: 단순 산술 함수 (`if signed >= 0` branches)
- 1KB size: 단순 leaf 치고는 큼 (= 큰 산술 처리 또는 lookup 없는 case 분기)

→ **"vtable invoker" 가 아님**. caller 가 vtable+8 을 r0 로 전달하면 `vtable[8]+0x10 = vtable+0x18` 의 halfword 를 읽고 산술 처리.

### 2.3 의미 추정 (가설)

**FUN_0007cd58 = "vtable+0x18 halfword 기반 산술 helper"**. vtable[0x18] 가 어떤 16-bit metadata (signed) 를 보유 → div 16 → 6 signed branch 를 통해 산술 처리.

`signed >> 4` (= div 16) 는 **fixed-point math** 에서 자주 사용 (16-bit Q4 → integer). 또는 **8x16 grid coord** 의 row/column 추출 (display coordinate).

## 3. `find_task_struct_field_readers.py` undercount 발견

### 3.1 Auto vs Wide-scan 비교

| field | auto hits (Round 24~25 도구) | wide-scan inline (Round 25 raw disasm) | 차이 |
|---|---|---|---|
| 0x9afc | 0 | 1+ (FUN_00041c14) | -100% |
| 0x9b01 | 0 | 6 (literal pool 빈도) | -100% |
| 0x9b14 | 0 | 10 (literal pool 빈도) | -100% |
| 0x9b1c | 0 | 4 (literal pool 빈도) | -100% |
| 0x9c70 | 0 | 112 | **-100%** |
| 0x9c71 | 0 | 115 | **-100%** |
| 0x9c84 | 0 | 39 | **-100%** |
| 0x9c85 | 0 | 37 | **-100%** |
| 0x9bb4 | 68 | 39 (FUN_0009a008 만) | partial |
| 0x9bb6 | 5 | 1 (FUN_00041c14) | partial |
| 0x9bd0 | 19 | 3 (FUN_0009a008 만) | partial |
| 0x9cb8 | 11 | 4 (FUN_00044a38 만) | partial |
| 0x9cbc | 17 | 2 (FUN_00041c14) | partial |

### 3.2 도구의 한계 — pattern 매칭 너무 엄격

`find_task_struct_field_readers.py` 의 매칭 패턴:
1. `bl 0x4ad10` (context_getter)
2. 직후 12 instr 안에 `ldr Rx, [pc, #imm]` (lit value = field_offset)
3. 그 다음 `adds Ry, R0, Rx` (R0 직접 사용)

실제 binary 의 사용 패턴 다수가 **1-instr 의 register save 를 거침**:
```asm
bl 0x4ad10              ; r0 = task_ptr
adds r3, r0, #0         ; r3 = r0 (saved before reuse)   <-- 도구는 이 이후 못 잡음
ldr r1, [pc, #N]         ; r1 = field_offset
adds r2, r3, r1         ; r2 = task_ptr + field         <-- R0 가 아닌 r3 사용
```

R0 가 직접 사용되지 않으면 매칭 실패. 0x9c70 cluster 가 100% miss 인 이유.

### 3.3 시사점 — Round 24~25 통계 재해석

| 통계 | Round 24~25 가설 | 정정 후 |
|---|---|---|
| 0x9bb4 dominant (69 sites, 15 funcs) | task_struct 의 핵심 field | **dominant 가 더 클 가능성** (auto undercount) |
| FUN_0009b252 46x | 가장 큰 reader | **system-wide reader 분포가 더 평탄할 가능성** |
| 8 GOT slots | 진짜 GOT slot 의 모든 것 | **추가 검증 필요** (0xd1c 이미 발견) |

**핵심 교훈**: auto 도구의 "0 hits" 는 "field 가 사용 안 됨" 을 의미하지 않음. 패턴이 narrow 하면 false-negative 다수.

### 3.4 0x9bd0 = system-wide 핵심 객체 (14 unique funcs)

Round 25 에서 "FUN_0009a008 안 3 사이트" 로만 봤던 0x9bd0 (ptr-to-object) 가 실은 **14 unique funcs** 에서 사용:
- FUN_0009ada4 (3x), FUN_0009b252 (3x) — FUN_0009a008 의 sub-labels
- FUN_000487ec (2x), FUN_000409d4 (1x), FUN_00040fb0 (1x)
- 외 9 functions

→ **0x9bd0 ptr-to-object = task_struct 의 시스템-와이드 핵심 객체** (ObjectA/ObjectB 와는 별개의 또 다른 핵심 객체).

post_pattern 분석:
- `ldr r3, [r2]` (FUN_000409d4) — 단순 deref
- `adds r3, #0x8c` (FUN_00040fb0) — offset access (object 안의 field 0x8c)
- `adds r2, r0, #0` — r2 saved
- `ldr r3, [r2]` — deref

**즉 0x9bd0-object 의 +0x8c offset 등 다양한 method/field 사용**. ObjectA/B 에 이은 **신규 핵심 object 후보**.

## 4. 갱신된 task_struct 모델

### 4.1 substructure @ 0x9bb4 (32 byte 추정)

```
task_struct + 0x9bb4 (substructure A 시작)
  ├─ +0x00 (= 0x9bb4) bit flags (FUN_0007d31c bit-by-bit scan 사용)
  ├─ +0x02 (= 0x9bb6) byte field (5 sites in 3 funcs)
  ├─ +0x03 (= 0x9bb7) byte field (1 site in FUN_00041c14)
  ├─ +0x14 (= 0x9bc8) field (FUN_00041c14)
  └─ +0x1c (= 0x9bd0) ptr-to-object  (14 unique funcs system-wide)
```

이 substructure 가 task_struct 의 dominant area 를 형성.

### 4.2 신규 helper 정체 (Round 26)

| Helper | 정체 (정정 후) |
|---|---|
| FUN_0007d31c | **substructure A bit-scan dispatcher** (NOT 단순 bit op). 660B, 8 bit unrolled scan, 0x9bb4 + 0x9bd0 함께 사용 |
| FUN_0007cd58 | **vtable+0x18 halfword 산술 helper** (NOT vtable invoker). 1068B leaf, GOT 미사용, 산술 처리 |

## 5. Round 27 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2BO | **`find_task_struct_field_readers.py` 패턴 lenient 화** — `adds Rx, R0, #0` 통한 R0 save 도 추적 | 도구 수정 + 재실행 |
| ⭐⭐ 2BP | **0x9bd0-object 의 vtable layout 매핑** (14 unique funcs 의 method offset 종합) | 각 func 본문 분석 |
| ⭐⭐ 2BQ | FUN_0007d31c 의 vtable[8] method 정체 (sub-call sites 본문) | 0x7d3xx 안의 indirect call 추적 |
| ⭐ 2BR | 0x9bb4 substructure 의 정확한 size + 다른 멤버 발견 | wide-scan 모든 0x9bb4~0x9bd4 offset |
| ⭐ 2BS | FUN_0007cd58 caller chain 추적 | 사용 사이트 (vtable+8 호출) |

## 산출물

- `work/h3/bit_helper_7d31c_disasm.json` — FUN_0007d31c (660B) 본문
- `work/h3/vtable_inv_7cd58_disasm.json` — FUN_0007cd58 (1068B) 본문
- `work/h3/task_struct_field_readers.json` — 확장된 26 fields wide-scan 결과
