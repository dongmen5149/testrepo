# Hero3 Ghidra — Round 35 / PM-25 (2026-05-10)
## 도구 immediate construction + 3 entity-bridge funcs caller chain 확정 + FUN_0008e89e 16.3KB 거대

> Round 34 의 0x274 immediate-construction limitation 후속 — 도구에 `movs Rd, #N; lsls Rd, Rd, #s` 패턴 추가. 결과: 0x274 = 0→2 sites. 또 3 entity-bridge funcs (FUN_00030018, FUN_0008beba, FUN_0008e89e) 의 caller chain 추적으로 game update flow 완전 매핑 확정.

## TL;DR (3줄)

1. ⭐⭐ **도구 immediate construction 패턴 추가** — `find_task_struct_field_readers.py` 에 `movs Rd, #N → const_regs[Rd]=N; lsls Rd, Rd, #s → const_regs[Rd] <<= s` 추적. 결과: **0x274 = 0→2 sites in 2 funcs** (FUN_00040cec + 1개). 0x9b00 cluster 는 여전히 0 = 다른 한계 (multi-hop register chain, branch-crossing).
2. ⭐⭐⭐ **3 entity-bridge funcs caller chain 확정** — 모두 isolated (direct BL 단 1건씩):
   - **FUN_00030018** (UI renderer, 10.1KB) ← caller 0x830d2 in **FUN_00082f4c** (FUN_000818f0 인접 wrapper, args r0=7/r1=arg/r2=task[+0x28] signed short)
   - **FUN_0008beba** (NPC dispatcher 영역, 7.5KB) ← caller 0x8b73e in **FUN_0008b2e8 (sister entry)**
   - **FUN_0008e89e** (SCN dispatcher main entry, **16.3KB**) ← caller 0x8e12a in **FUN_0008dcd8 (main entry)**
3. ⭐⭐⭐ **FUN_0008e89e = 16.3KB 초거대 함수** (7969 instructions, **62 cmp arms**) — Hero3 의 가장 큰 함수 중 하나. cmp #0xff 6x (SCN separator), cmp 0x89/0x8f (ASCII high), cmp 0x32 ('2'), 0x49 ('I'), 0x3b (';') — **SCN bytecode interpreter / dialog dispatcher**.

부수 발견:
- ⭐⭐ **PROGRESS.md game update flow 검증 완료**: sister entry → NPC entity-bridge / main entry → SCN entity-bridge 패턴 raw caller chain 으로 확정.
- ⭐ FUN_00082f4c (FUN_000818f0 인접) = UI renderer invocation wrapper. PIC standard prologue + 0x7c stack frame.
- ⭐ FUN_0008e89e 의 62 cmp arms (cmp #0 32x dominant) = 큰 SCN bytecode handling — 0xff = end marker, 0x89/0x8f = encoded byte markers (EUC-KR 한글 cluster?).

## 1. 도구 immediate construction 패턴 추가

### 1.1 추가 알고리즘

```python
# 신규 (Round 35): immediate construction 추적
const_regs: dict[str, int] = {}

# Step 1: movs Rd, #N → const_regs[Rd] = N
if mnem == "movs" and len(parts) == 2 and parts[1].startswith("#"):
    const_regs[parts[0]] = int(parts[1].lstrip("#"), 0)

# Step 2: lsls Rd, Rs, #shift → const_regs[Rd] = const_regs[Rs] << shift
if mnem == "lsls" and len(parts) == 3 and parts[2].startswith("#"):
    src, dst = parts[1], parts[0]
    if src in const_regs:
        const_regs[dst] = (const_regs[src] << shift) & 0xFFFFFFFF

# Match: const_reg holds known field offset
if ldr_target is None:
    for reg, cval in const_regs.items():
        if cval in fields:
            ldr_target = (j, reg, cval)
            break

# Invalidate const_regs on overwriting writes (best-effort)
```

### 1.2 결과

| field | Round 34 | Round 35 | 변화 |
|---|---|---|---|
| **0x274** | 0 | **2** in 2 funcs | NEW! |
| 0x9bb4 | 71 | 71 | 동일 |
| 0x9b00 cluster | 0 | 0 | 변화 없음 |
| 외 모든 fields | 동일 | 동일 | 동일 |

**0x274 = 2 sites** (FUN_00040cec 의 0x40d04 + 1개 더). 작은 진척.

### 1.3 0x9b00 cluster 여전히 0 hits — 추가 분석

FUN_00042758 본문 (Round 32) 에서 0x9afc/0x9b06/0x9b14/0x9b1c/0x9b3c access 발견했지만 도구 못 잡음. 가능한 원인:
- **Multi-hop register propagation**: `r0 → r6 → r4 → ... → 100+ instr 후 사용`
- **Branch-crossing**: 도구의 branch break 가 끊음
- **다른 immediate construction 패턴**: `adds Rd, Rs, #imm; lsls Rd, Rd, #s` 같은 변형
- **PC-rel ldr value 가 cluster offset 아닌 다른 base + offset 합 형태**: e.g. `ldr Rx, [pc] (=0x9b00)` 후 `adds Rx, #imm` 으로 inflate

다음 라운드에서 0x9b00 cluster 직접 wide-scan (R0 propagation 무시, 모든 ldr+add 조합 검색) 가 더 효율적일 가능성.

## 2. 3 entity-bridge funcs caller chain 확정

### 2.1 caller search 결과

| func | direct BL | literal pool | caller location |
|---|---|---|---|
| FUN_00030018 | 1 | 0 | **0x830d2** (in FUN_00082f4c) |
| FUN_0008beba | 1 | 0 | **0x8b73e** (in FUN_0008b2e8 = sister entry!) |
| FUN_0008e89e | 1 | 0 | **0x8e12a** (in FUN_0008dcd8 = main entry!) |

→ **모두 isolated**, direct BL 단 1건씩, literal pool 0건.

### 2.2 PROGRESS.md game update flow 검증 완료

```
GVM Firmware (indirect entries)
  ├─ FUN_0008b2e8 (sister entry, record 0x3c4) ── BL 0x8b73e ──→ FUN_0008beba (NPC entity-bridge, 7.5KB)
  └─ FUN_0008dcd8 (main entry, record 0x3c4)   ── BL 0x8e12a ──→ FUN_0008e89e (SCN dispatcher main, 16.3KB)
                                                                  └─ 0xac94 9x reader (entity-bridge)
```

→ **NPC/SCN entity-bridge 패턴 raw caller chain 으로 확정**.

또 신규 발견:
```
FUN_00082f4c (UI renderer invocation wrapper)
  └─ BL 0x830d2 → FUN_00030018 (UI/HUD renderer, 10.1KB)
       args: r0=7 (mode?), r1=r4 (state ptr?), r2=task[+0x28] signed short (entity slot index?)
```

### 2.3 FUN_00082f4c context

```asm
0x830c0: bl 0x4ad10                  ; context_getter, r0 = task_ptr
0x830c4: adds r3, r0, #0              ; r3 = task_ptr (saved)
0x830c6: ldr r3, [r3, #0x28]          ; r3 = task_struct[+0x28] word
0x830c8: lsls r3, r3, #0x10
0x830ca: asrs r3, r3, #0x10           ; r3 = signed 16-bit (top 16-bit zero-extended)
0x830cc: movs r0, #7                  ; r0 = 7
0x830ce: adds r1, r4, #0              ; r1 = r4 (caller arg)
0x830d0: adds r2, r3, #0              ; r2 = task[+0x28] signed short
0x830d2: bl 0x30018                   ; FUN_00030018(7, r4, task[+0x28] signed)
```

→ **task_struct[+0x28] = entity slot index 또는 state ID** (signed short). FUN_00030018 의 r2 인자.

## 3. FUN_0008e89e = 16.3KB 초거대 SCN dispatcher main entry

### 3.1 Boundary

| 측면 | 값 |
|---|---|
| 시작 | 0x8e89e |
| 끝 | 0x929e8 |
| size | **16714 byte (16.3KB)** = Hero3 binary 거대 함수 중 최상위 |
| instr | 7969 |
| cmp arms | 62 |

### 3.2 cmp 분포 — SCN bytecode interpreter

| imm | count | 의미 추정 |
|---|---|---|
| 0 | 32x | null/zero check |
| **0xff** | **6x** ⭐ | SCN separator (PROGRESS.md 의 0xff 빈번 separator) |
| 0x03/0x12/0x0c/0x0b/0x01 | 각 2-4x | bytecode opcodes |
| **0x89, 0x8f** | 각 2x | ASCII high (EUC-KR 한글 첫 byte 후보) |
| **0x32 ('2')** | 1x | ASCII '2' (key handler 와 비슷?) |
| 0x49 ('I'), 0x3b (';') | 각 1x | ASCII text/dialog |

**0xff 6x** = SCN file 의 termination/separator. **0x89/0x8f** = EUC-KR 한글 byte 첫 패턴 (KS X 1001 영역의 high byte).

→ **FUN_0008e89e = SCN bytecode interpreter** (text/dialog 처리 + entity bridging).

### 3.3 PROGRESS.md SCN dispatcher 와 일치

PROGRESS.md game update flow:
```
FUN_0008dcd8 (main entry, record 0x3c4)
  └ inline @ 0x8eb80 → FUN_0008ff18 (jt 0xabc68)
```

FUN_0008e89e 의 위치 (0x8e89e) 가 0x8eb80 보다 약간 앞. inline 영역 0x8eb80~ 가 FUN_0008e89e 안의 sub-handler. 즉:
- FUN_0008dcd8 → FUN_0008e89e (entity bridge entry)
- FUN_0008e89e → JT @ 0xabc68 (19 entries SCN dispatcher)
- 19 dispatch entries → 7 distinct handlers (PROGRESS.md 의 4 dispatcher 중 하나)

## 4. FUN_0008beba (NPC dispatcher 영역, 7.5KB)

### 4.1 Boundary

| 측면 | 값 |
|---|---|
| 시작 | 0x8beba |
| 끝 | 0x8dcd8 (= FUN_0008dcd8 main entry 시작) |
| size | 7710 byte (~7.5KB) |
| instr | 3654 |
| cmp arms | 23 |

### 4.2 cmp 분포 — NPC dispatcher

| imm | count |
|---|---|
| 0 | 12x |
| 0x0b, 0x3b (';') | 각 2x |
| 0x12, 0x49 ('I'), 0x09 등 | 각 1x |

ASCII '0x3b ;' / '0x49 I' = 동일한 text/dialog handling. 0xff 검사 없음 = SCN bytecode 처리는 main entry (0x8e89e) 에 한정.

### 4.3 정체

NPC dispatcher (record 0x3c4) 의 sub-handler. FUN_0008b2e8 (sister entry) 안에서 호출.

## 5. 갱신된 game update flow (Round 35 완료)

```
GVM Firmware (binary load 시 5 indirect entries)
  ├─ FUN_0006619c (paint/tick callback)
  │   └─ FUN_00062d1c (state[0x94] page 분기)
  │       ├─ page 0 → FUN_0005c038 → FUN_0005d214 (jt 0xa9cc4)
  │       ├─ page 1 → FUN_0005e6ac → FUN_0005f948 (jt 0xa9d70)
  │       └─ page 2 → FUN_00060ab4 (9KB UI)
  │
  ├─ FUN_00070f34 (key handler)
  │
  ├─ FUN_0008b2e8 (sister entry, record 0x3c4)
  │   ├─ inline @ 0x8c19c → FUN_0008d5e4 (jt 0xabaa8)
  │   └─ BL 0x8b73e → FUN_0008beba (NPC entity-bridge, 7.5KB)
  │
  ├─ FUN_0008dcd8 (main entry, record 0x3c4)
  │   ├─ inline @ 0x8eb80 → (FUN_0008ff18, jt 0xabc68)
  │   └─ BL 0x8e12a → FUN_0008e89e (SCN dispatcher main entry, 16.3KB)
  │
  └─ FUN_000241dc (system event dispatcher, 74-entry JT)
      ├─ 62/74 (84%) → epilogue (no-op)
      └─ 12 진짜 events:
          ├─ 0x24300 (5 events) → FUN_00042758 (entity state initializer, 1.1KB)
          ├─ 0x242c0 (4 events) → FUN_00040cec (event registrar, 240B)
          ├─ 0x24308~ cleanup → ObjectA destructor + state reset → FUN_000818f0
          └─ ... (개별 handlers)

FUN_000818f0 (single-entity state handler + renderer, 5.6KB)
  ├─ task_struct[0xac78~0xac9d] entity record dominant reader
  └─ 4 screen_ptr_getter rendering at end

FUN_00082f4c (UI renderer invocation wrapper)
  └─ BL 0x830d2 → FUN_00030018 (UI/HUD renderer, 10.1KB)
                  └─ 37 screen_ptr_getter, ASCII dialog handling
```

## 6. Round 36 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2DJ | **0x9b00 cluster 직접 wide-scan** (R0 propagation 무시, 모든 ldr+add 조합) | tool 추가 작성 |
| ⭐⭐ 2DL | FUN_00082f4c 본문 (FUN_00030018 invocation wrapper) | `disasm_subsystem_func.py 0x82f4c <next_push>` |
| ⭐⭐ 2DM | FUN_0008e89e 의 19-entry JT @ 0xabc68 디코드 (PROGRESS.md SCN dispatcher) | binary 직접 read |
| ⭐ 2DN | FUN_0008beba 의 inline @ 0x8c19c → FUN_0008d5e4 (PROGRESS.md NPC dispatcher) JT @ 0xabaa8 디코드 | binary 직접 read |
| ⭐ 2DO | 0x274 의 두 번째 reader (FUN_00040cec 외 1개 함수) 정체 | 검색 결과 확인 |
| ⭐ 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 92% miss) | 도구 추가 확장 |

## 산출물

- `tools/recon/find_task_struct_field_readers.py` — immediate construction (`movs+lsls`) 추적 추가
- `work/h3/entity_bridge_8beba_disasm.json` — FUN_0008beba (7.5KB) 본문
- `work/h3/scn_main_8e89e_disasm.json` — FUN_0008e89e (16.3KB) 본문 (큰 분석)
