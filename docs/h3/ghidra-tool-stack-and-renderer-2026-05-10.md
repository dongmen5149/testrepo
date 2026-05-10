# Hero3 Ghidra — Round 34 / PM-24 (2026-05-10)
## 도구 stack save/reload lenient 화 + FUN_00030018 = 10.1KB UI renderer + 0x274 immediate-construction limitation

> Round 33 의 도구 limitation 발견 (0x9b00 cluster auto-detect 0 hits) 를 후속 — 도구 추가 lenient 화 (stack save/reload + 32-instr lookahead). 그러나 0x9b00 cluster 는 여전히 0 hits = 또 다른 한계 발견. FUN_00030018 entity-bridge func 본문 = 10.1KB rendering 함수.

## TL;DR (3줄)

1. ⭐⭐ **도구 stack save/reload lenient 화 효과 미미** — `find_task_struct_field_readers.py` 에 stack save (`str rX, [sp, #N]`) + reload (`ldr rZ, [sp, #N]`) 추적 추가, lookahead 16→32 확장. 결과: 0x9bb4 +2 sites (69→71), 0xac90 +1 site, 그 외 거의 동일. **0x9b00 cluster 여전히 0 hits** = stack 외 다른 register chain (또는 multi-hop propagation, immediate construction) 사용.
2. ⭐⭐⭐ **FUN_00030018 = 10.1KB 거대 UI/HUD renderer** — 4948 instr, 28 cmp arms, **121 interesting BLs (37 screen_ptr_getter calls = 가장 dominant)**, cmp '0x3b ;' / '0x62 b' = ASCII = text/dialog handling. 0xac94 14x reader = entity-별 그리기. **PROGRESS.md 의 page UI rendering 영역 후보** (state[0x94] 분기 후 진입 가능).
3. ⭐⭐ **0x274 도구 limitation 발견** — `find_task_struct_field_readers.py` LDR pcrel 검색 결과 단 1건 (GOT slot 패턴). 실제 FUN_00040cec 의 0x274 access 는 **immediate construction (`movs r2, #0x9d; lsls r2, r2, #2`)** 으로 0x274 = 0x9d*4 만듬 → LDR pcrel 안 거침. 도구가 이 패턴 미커버. 즉 0x9b00 cluster + 0x274 등 작은 task_struct field 의 reader 가 system-wide undercount.

부수 발견:
- ⭐ FUN_00030018 의 PIC standard prologue + **0x16c (364 byte) 거대 stack frame** — local rendering buffer / state.
- ⭐ FUN_00030018 의 BL 121 = drawing helpers (screen_ptr_getter 외에도 다양). cmp #0x12 = 18 distinct drawing modes.
- ⭐ Round 34 의 도구 강화 후 누적 KNOWN_FIELDS 39 fields 의 system-wide reader 통계 거의 안정.

## 1. 도구 stack save/reload lenient 화

### 1.1 추가된 패턴

```python
# 기존 (Round 27): R0 register save 만
adds rZ, r0, #0    # → r0_equiv.add(rZ)
mov rZ, r0          # → r0_equiv.add(rZ)

# 신규 (Round 34): stack save/reload 추적
str rX, [sp, #N]   # if rX in r0_equiv → stack_saved.add(N)
ldr rZ, [sp, #N]   # if N in stack_saved → r0_equiv.add(rZ)

# Lookahead: 16 → 32 instr (extended window)
```

### 1.2 Before / After 통계

| field | Round 27 (16-instr) | Round 34 (32-instr + stack) | 변화 |
|---|---|---|---|
| 0x9bb4 | 69 sites, 20 funcs | **71 sites, 22 funcs** | +2 / +2 |
| 0xac90 | 3, 1 | **4, 1** | +1 |
| 0x9c70 | 9, 2 | 9, 2 | 동일 |
| 0x9c71 | 97, 37 | 97, 37 | 동일 |
| 0x9c84 | 34, 18 | 34, 18 | 동일 |
| 0x9c85 | 31, 11 | 31, 11 | 동일 |
| 0x9bd0 | 25, 21 | 25, 21 | 동일 |
| 0x9e28 | 101, 83 | 101, 83 | 동일 |
| 0xac78 | 43, 4 | 43, 4 | 동일 |
| **0x9b00 cluster** | **0** | **0** | **여전히 0** ⚠ |

**효과 미미** — stack save/reload 패턴은 binary 에서 흔하지 않음 (대부분 register-only propagation). lookahead 32-instr 확장으로 +3 sites 추가만.

### 1.3 0x9b00 cluster 여전히 0 hits — 진짜 원인

FUN_00042758 (Round 32) 의 0x9b00 cluster access 가 stack save/reload 가 아닌 **multi-hop register propagation** 일 가능성:
```asm
bl 0x4ad10
adds r6, r0, #0    ; r6 = task_ptr (Round 27 도구 캐치)
; ... 100+ instr 후 ...
adds r4, r6, #0    ; r4 = r6 (multi-hop, Round 27 도구 부분 캐치)
ldr rX, [pc]       ; field
adds rY, r4, rX    ; r4 in r0_equiv? Round 34 까지 캐치되어야
```

Round 34 의 도구가 `adds r4, r6, #0` 같은 "다른 reg → 다른 reg" save 도 캐치하므로 (r6 in r0_equiv → r4 추가) 이론적으로는 잡혀야 함. 그러나 실제 0 hits = **branch break 가 도중에 끊는 듯** (32-instr window 안에 분기 다수).

근본 해결: branch 추적 (basic block 기반 분석) 또는 cluster 별 직접 wide-scan (R0 propagation 무시).

## 2. FUN_00030018 = 10.1KB UI/HUD renderer

### 2.1 Boundary 와 prologue

| 측면 | 값 |
|---|---|
| 시작 | 0x30018 |
| 끝 | 0x32880 (다음 push prologue) |
| size | **10344 byte (10.1KB)** = Hero3 binary 거대 함수 중 하나 |
| instr | 4948 |
| cmp arms | 28 |
| stack frame | 0x16c (364 byte) — 거대 local buffer |
| BL count (interesting) | 121 |

### 2.2 BL 분포 (가장 dominant 만)

| target | count | 의미 |
|---|---|---|
| **screen_ptr_getter** | **37x** ⭐ | rendering 의 핵심 helper |
| (기타 various) | 84 | drawing primitives, sound triggers, etc. |

37 screen_ptr_getter = 화면을 다수 영역에 그리기 = **main UI/HUD renderer**.

### 2.3 cmp 분포 — text/dialog handling

| imm | count | 의미 추정 |
|---|---|---|
| 0 | 13x | null check |
| 0xc (12) | 3x | range/state |
| 0x12 (18) | 2x | drawing mode? |
| 0x03 | 2x | mode |
| **0x3b (';')** | **2x** | ASCII semicolon = dialog terminator? |
| 0x07/0x02/0x0e/0x01/0x0b/0x06 | 각 1x | small enums |

ASCII 비교 (';' x2) = **dialog/text rendering**.

### 2.4 정체 가설 — page UI renderer

PROGRESS.md 의 game update flow:
```
FUN_00062d1c (state[0x94] = "현재 페이지" 분기)
  ├ page 0 → FUN_0005c038 → FUN_0005d214 (jt 0xa9cc4)
  ├ page 1 → FUN_0005e6ac → FUN_0005f948 (jt 0xa9d70)
  └ page 2 → FUN_00060ab4 (9KB)
```

FUN_00030018 은 위 game update flow 에 직접 등장 안 하지만:
- 10.1KB size = page UI (FUN_00060ab4 의 9KB) 와 비슷 규모
- 37 screen_ptr_getter = 화면 다수 영역 그리기
- 0xac94 14x reader = entity-별 그리기 (HUD overlay)

→ **추정**: FUN_00030018 = **status/inventory/dialog UI renderer** (page UI 보다는 별도 UI 모드, 예: 메뉴 또는 status bar).

caller chain 검증 다음 라운드에 필요.

## 3. 0x274 도구 limitation (immediate construction)

### 3.1 LDR pcrel 검색 결과

```
=== 0x274 LDR pcrel sites: 1 ===
  GOT slot pattern (add+sl): 1
```

단 1 사이트, 그것도 GOT slot 패턴. ctx field 패턴은 0건.

### 3.2 실제 FUN_00040cec 의 0x274 access

```asm
0x40cfa: bl 0x4ad10                 ; r0 = task_ptr
0x40cfe: movs r2, #0x9d              ; r2 = 0x9d
0x40d00: lsls r2, r2, #2             ; r2 = 0x9d << 2 = 0x274
0x40d02: adds r3, r0, r2             ; r3 = task_ptr + 0x274
0x40d04: str r5, [r3]                ; *task_struct[0x274] = caller_arg
```

→ **immediate construction 패턴** (`movs Rd, #N; lsls Rd, Rd, #2` = Rd = N << 2).

도구가 LDR pcrel 만 검색 → 이 패턴 미커버 = 0 hits.

### 3.3 Implications — 작은 task_struct field 의 system-wide undercount

ARM Thumb 의 immediate-construction 패턴:
- `movs Rd, #N` (8-bit immediate)
- `lsls Rd, Rd, #shift` (shift up to 31)

이 패턴으로 만들 수 있는 값: 0..255 << 0..31. 즉 작은 base + shift 조합.

작은 task_struct field offsets (0x100~0x800 range) 가 이 패턴으로 자주 만들어질 가능성:
- 0x100 = 0x40 << 2
- 0x200 = 0x80 << 2  또는 0x40 << 3
- 0x274 = 0x9d << 2
- 0x444 = 0x111 << 2 (또는 다른)
- 0x274 cluster 와 다른 작은 offsets (0x29e, 0x274, 0x444 등) 도 immediate construction 가능

→ **task_struct 의 small offset cluster 의 reader 가 system-wide undercount**. PM-7 / Round 23~25 의 GOT slot vs ctx field 분류도 부분 정정 필요.

### 3.4 도구 추가 강화 제안 (Round 35+)

immediate construction 패턴 추가:
```python
# Track: movs Rd, #N → r2_const = N
# Then: lsls Rd, Rd, #shift → r2_const <<= shift
# If r2_const in fields → 검사 진행
```

이는 도구 다음 라운드 작업.

## 4. 갱신된 모델

### 4.1 도구 한계 분류 (Round 33~34)

| 패턴 | Round 27 | Round 34 |
|---|---|---|
| R0 직접 사용 | ✅ | ✅ |
| `adds rZ, r0, #0` save | ✅ | ✅ |
| `mov rZ, r0` save | ✅ | ✅ |
| stack `str/ldr [sp, #N]` save/reload | ❌ | ✅ |
| 16-instr lookahead | ✅ | extended to 32 |
| **multi-hop register propagation** (rZ → rA → rB) | ⚠ partial | ⚠ partial |
| **branch-crossing** (basic block boundary) | ❌ | ❌ |
| **immediate construction** (`movs+lsls`) | ❌ | ❌ |
| **PC-rel literal pool 외 absolute imm** | ❌ | ❌ |

→ **0x9b00 cluster, 0x274 등 작은/middle offsets 의 system-wide undercount 지속**.

### 4.2 Top entity-related funcs (Round 34 시점)

```
FUN_000818f0 (5.6KB)  single-entity state handler + renderer
                      task_struct[0xac78~0xac9d] entity record dominant reader
                      direct call only from FUN_000241dc 0x24300 path

FUN_00030018 (10.1KB) ⭐ NEW Round 34 — UI/HUD renderer
                      37 screen_ptr_getter, 121 BL, 28 cmp arms
                      0xac94 14x reader = entity-별 그리기
                      ASCII '0x3b ;' = dialog handling

FUN_00042758 (1.1KB)  entity state initializer
                      task_struct[0x9afc~0x9b3c] cluster #1 dominant reader
                      direct call only from FUN_000241dc 0x24300 path

FUN_00040cec (0.24KB) simple event code register
                      *task_struct[0x274] = caller_arg (4 events)
                      direct call only from FUN_000241dc 0x242c0 path

FUN_0008d87c (1.1KB)  sister entry inline sub-handler
                      task_struct[0x9c70/0x9e28/0x1668] dominant reader

FUN_0008beba          NPC dispatcher 영역 (0xac94 14x)
FUN_0008e89e          SCN dispatcher main entry (0xac94 9x)
```

## 5. Round 35 권장 다음 작업

| # | 작업 | 명령 / 접근 |
|---|---|---|
| ⭐⭐⭐ 2DF | **도구 immediate construction 패턴 추가** (`movs Rd, #N; lsls Rd, Rd, #s`) | 도구 코드 수정 |
| ⭐⭐ 2DG | FUN_00030018 caller chain 추적 (어떤 indirect entry 가 호출?) | BL 0x30018 검색 + literal pool |
| ⭐⭐ 2DH | FUN_0008beba 본문 (entity-bridge, NPC dispatcher 영역) | `disasm_subsystem_func.py 0x8beba` |
| ⭐⭐ 2DI | FUN_0008e89e 본문 (SCN dispatcher main entry, 알려진 함수) | `disasm_subsystem_func.py 0x8e89e` |
| ⭐ 2DJ | 0x9b00 cluster 직접 wide-scan (R0 propagation 무시, raw `ctx + offset` 패턴) | tool 추가 작성 |
| ⭐ 2DK | 0x274 (event code) 의 immediate construction reader wide-scan | 패턴 검색 |
| ⭐ 2CD | 0x9c70 stack-load 패턴 추가 lenient 화 (Round 27 92% miss, 같은 한계) | 도구 추가 확장 |

## 산출물

- `tools/recon/find_task_struct_field_readers.py` — stack save/reload + 32-instr lookahead 추가
- `work/h3/entity_bridge_30018_disasm.json` — FUN_00030018 (10.1KB) 본문
