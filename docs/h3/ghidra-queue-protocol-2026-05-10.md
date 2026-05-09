# §4.4 후속 — 2026-05-10 PM-5 세션 (큐 protocol 종합 매핑 + epilogue gadget 발견)

> 2026-05-10 PM-4 의 큐 record 포맷 가설 후속.
> 자동 우선순위 **2P (backtrace 강화)** + **2N (FUN_00056bf8 codec)** + **2O (FUN_00008aca = inner)** 일괄.
> 결과: 큐 protocol 의 type tag 종합 + Ghidra "stub" 의 또 다른 패턴 (공유 epilogue gadget) 발견.

---

## 1. 2P — `disasm_subsystem_func.py` backtrace 강화

### 1A. 추가 기능

`track_reg_value(instrs, idx, target_reg, depth=15)` — 재귀 register propagation:
- mov Rd, #imm → 즉시값
- mov Rd, Rs → Rs 로 chain
- ldr Rd, [pc, #imm] → PC-rel literal
- adds Rd, Rs, #imm → chain + offset
- adds/subs Rd, #imm → 자기 모디파이 (recursive)
- lsls/lsrs/asrs Rd, Rs, #imm → shift
- ldr Rd, [Rn, #imm] → unresolved (memory load, return early)
- 최대 depth=15 instr 추적, visited set 으로 cycle 방지

`backtrace_args(instrs, idx)` — r0~r3 동시 추적 + prev_instrs 컨텍스트 dump

### 1B. 효과

- **byte_append immediate 추출**: 거의 모든 케이스 식별 (80~90%). 나머지 unresolved 는 함수 인자로부터 들어오거나 직전 BL return value 사용 케이스.
- **PC-rel literal load**: `r0=*0x000643b0=0x9c71` 형태로 GOT slot offset 추출 — 이전엔 보이지 않던 PIC argument 패턴 식별.
- **Sound ID 추출 한계**: sound_trigger r0 21/21 unresolved (모두 register/memory load 패턴 → backtrace 도 한계). 함수 진입점 인자 또는 prior BL return value.

### 1C. 핵심 발견 — `FUN_0004ad10` 정체 재해석

이전 추정 "단순 GOT context getter" → **실제는 인자 기반 GOT slot fetcher** 가능성:

```
default key handler 안의 BL pattern:
  ... r0 = *0x643b0 = 0x9c71 (literal load)
  bl context_getter (FUN_0004ad10)
```

각 호출마다 **다른 GOT slot offset** (0x9c70, 0x9c71, 0x9c84) 을 r0 로 전달. Ghidra 디컴파일은 `void → undefined4` (인자 없음) 으로 표시했으나 실제는 r0 인자를 받을 가능성. FUN_0004ad10 본문 capstone 재분석 필요.

→ 향후 **모든 stub 함수의 "context_getter" 호출은 다른 글로벌을 가져오는 의미** 가능성. 이전 분석에서 동일 호출로 가정한 것 정정.

---

## 2. 2N — FUN_00056bf8 (큐 codec, 836B) 본문 분석

### 2A. 통계

```
size=836 instr=386
arms: 10 cmp+branch (cmp #0x3d, #0x3e, #0x1f, #0x06, #0x09, #0x07, #0x01, #0x00 등)
interesting BL: 21 (byte_append 10 + flush_swap 4 + memcpy_read 3 + memset_like 2 + context 1 + u32_append 1)
```

### 2B. ⭐ **codec 패턴 — cmp arm 값 = byte_append immediate 값**

**cmp arms 와 byte_append immediate 의 교집합**:

| value | cmp 사용 | byte_append 사용 | 의미 |
|---|---|---|---|
| 0x3d ('=') | ✅ 1x | ✅ 1x | type-1 record 의 sub-op |
| 0x3e ('>') | ✅ 1x | ✅ 2x | type-1/4 record 의 sub-op |
| 0x1f | ✅ 1x | ✅ 1x | type-0x1f record begin |
| 0x06 | ✅ 2x | — | reader-only check |
| 0x09 | ✅ 2x | — | reader-only check |
| 0x07 | ✅ 1x | — | reader-only check |
| 0x01 | ✅ 1x | ✅ 2x | type-1 record begin (writer) |
| 0x00 | ✅ 1x | ✅ 2x | type-0 record begin / null check |
| 0x04 | — | ✅ 1x | type-4 record begin |

→ **이 함수는 양방향 (encode + decode) codec**: 일부 type tag 는 reader 만, 다른 일부는 writer 도 사용.

### 2C. 5 records emit by FUN_00056bf8

```
1. site 0x56d1e: byte(0x01) + byte(0x3d)              + flush      ← type-1 record, sub-op 0x3d
2. site 0x56d84: byte(0x00)                            + flush(0)   ← type-0 record (terminator?)
3. site 0x56dc6: byte(0x04) + byte(0x3e)              + flush      ← type-4 record, sub-op 0x3e
4. site 0x56e08: byte(0x1f) + byte(0x00)              + flush      ← type-0x1f record, sub-op 0
5. site 0x56e5c: byte(0x01) + byte(0x3e) + ?          + flush(0x3e) ← type-1 record, sub-op 0x3e
```

→ FUN_00056bf8 = **multi-type writer + reader** (codec).

---

## 3. 2O — FUN_00008aca 정체 ⚠

### 3A. Ghidra 디컴파일 vs 실제

Ghidra: `void FUN_00008aca(void) { return; }` — 빈 함수로 표시.

Capstone 디스어셈블 (0x8aca):
```
0x00008aca: mov  sp, r7              ← EPILOGUE 시작
0x00008acc: pop  {r3}
0x00008ace: mov  sl, r3               ← restore r10 (GOT base)
0x00008ad0: pop  {r4, r5, r6, r7, pc} ← RETURN
0x00008ad2: 0000 (literal padding)
0x00008ad8: push {r4-r7, lr}          ← 다음 진짜 함수 시작
```

→ **0x8aca 는 별도 함수가 아님!** = FUN_00006334 (10KB) 의 **공유 epilogue gadget**.

### 3B. "70x BL to 0x8aca" 재해석

이전 분석의 "FUN_00006334 → FUN_00008aca 70x" 는:
- ❌ inner helper 호출 70x (오해)
- ✅ **70개 early-exit branches** — FUN_00006334 안 70 위치에서 공유 epilogue 로 BL → 함수 종료

이 패턴은 **shared epilogue gadget** (ARM Thumb 코드 사이즈 절약 컴파일러 최적화). 작은 ISA 의 옛날 컴파일러들이 자주 사용.

→ FUN_00006334 가 **96 cmp arms + 70 early-exit** = 매우 분기가 많은 dispatcher/state machine. main loop 가설 강화 (각 arm 처리 후 곧장 return).

### 3C. 부수 발견 — FUN_00006334 의 마지막 BL = FUN_000031dc

```
0x00008ac4: adds r0, r3, #0          ← r0 셋업
0x00008ac6: bl   #0x31dc             ← FUN_000031dc 호출
0x00008aca: epilogue 시작
```

FUN_00006334 가 epilogue 직전에 FUN_000031dc (또 다른 6.7KB MASSIVE state machine, top stub #14) 를 호출. **두 큰 함수가 chain dispatcher** 가능성:
- FUN_00006334: 1차 분기
- FUN_000031dc: 2차 분기 (또는 continuation handler)

→ 다음 분석 권장: FUN_000031dc 도 같은 도구로 본문 분석.

---

## 4. 큐 record protocol 종합 매핑 (2K + 2N + 추가 writer)

### 4A. byte_append immediate 분포 (4 writer functions 종합)

| record type | FUN_00057394 | FUN_00056bf8 | FUN_00064048 | FUN_000630e8 | 합계 emit |
|---|---|---|---|---|---|
| **type-0** (`0x00`) | — | 2 | — | — | 2 |
| **type-1** (`0x01`) | — | 2 | — | — | 2 |
| **type-3** (`0x03`) | 1 | — | — | — | 1 |
| **type-4** (`0x04`) | — | 1 | — | 2 | 3 |
| **type-5** (`0x05`) ⭐ | 7 | — | 4 | 5 | **16** |
| **type-0x14** (`0x14`) | 1 | — | — | — | 1 |
| **type-0x1f** (`0x1f`) | — | 1 | — | — | 1 |
| **type-0x3d** (`0x3d`='=') | 3 | 1 | 2 | — | 6 (sub-op?) |
| **type-0x3e** (`0x3e`='>') | — | 2 | — | — | 2 (sub-op?) |
| **type-0x3f** (`0x3f`='?') | 1 | — | 2 | — | 3 (sub-op?) |
| **type-0x40** (`0x40`='@') | 1 | — | — | — | 1 (sub-op?) |
| **type-0x41** (`0x41`='A') | — | — | — | 1 | 1 (sub-op?) |

### 4B. ⭐ type-5 = 가장 흔한 record (16 emits)

3 writer 함수가 type-5 emit:
- FUN_00057394 (3.5KB display list builder): 7 records
- FUN_00064048 (default key handler): 4 records
- FUN_000630e8 (cmd processor): 5 records

type-5 의 sub-opcodes: 0x3, 0x14, 0x3d, 0x3f, 0x40, 0x41 (모두 ASCII '=','?','@','A' 부근 — 의미 추정 어려움).

### 4C. record 포맷 가설 정정

이전 가설:
```
record:
  byte type_tag      ; 0x05 / 0x01 / 0x04 등
  byte sub_opcode    ; type 별 의미
  args
  flush_swap()       ; commit
```

정정된 가설 (PM-5):
```
record (variable form):
  byte type_tag      ; 0x00 / 0x01 / 0x03 / 0x04 / 0x05 / 0x14 / 0x1f
  byte sub_opcode    ; (optional) 0x3d / 0x3e / 0x3f / 0x40 / 0x41 등
  args               ; (optional) memcpy_read 또는 u32_append
  flush_swap()       ; commit (record 끝)

  단, type-0 같은 일부는 sub_opcode 없이 standalone
  type-5 는 항상 sub_opcode 가 따라옴 (16 records 모두)
```

### 4D. cmp arm 분석 — reader 분기

FUN_00056bf8 (codec) 의 cmp arms 중 **0x3d / 0x3e / 0x1f / 0x06 / 0x09 / 0x07** 이 reader 분기로 추정.

- type tag (0x1f) 가 cmp 에 등장 = type 별 dispatch
- sub-op (0x3d, 0x3e) 도 cmp = sub-op 별 dispatch
- 0x06, 0x09, 0x07 = sub-op 후보 또는 다른 검사 (length, status 등)

reader 로직:
```
byte = read_byte_from_queue()
if (byte == 0x05) → handle type-5 sub-op
if (byte == 0x1f) → handle type-0x1f
if (byte == 0x06) → handle some condition
...
```

---

## 5. 큐 protocol 정체 추정 진척

### 5A. type-5 의 의미 — **save / journal records**?

- 3 writer 가 type-5 emit (FUN_00057394 = display list, FUN_00064048 = key handler, FUN_000630e8 = cmd processor)
- 모두 **이벤트가 발생할 때 emit** (사용자 입력, 명령 실행, 화면 그리기)
- type-5 의 sub-op 는 ASCII 문자 ('=', '?', '@', 'A') — 특이한 패턴

→ **journal / event log** 가설:
- type-5 = 게임 상태 변경 이벤트 record
- sub-op (0x3d='=' / 0x3f='?' 등) = 이벤트 카테고리 (배정 / 질문 / 호출 / 액션)
- 큐는 **action history / undo buffer / replay log** 일 가능성
- 또는 **save game serialization stream** (각 sub-op 가 다른 데이터 분류)

### 5B. type-0/1/4/0x1f 의 의미

- type-0: standalone (terminator? null marker?)
- type-1: paired (sub-op 0x3d, 0x3e — control flow records?)
- type-4: paired (sub-op 0x3e — secondary action?)
- type-0x1f: paired (sub-op 0x00 — special boundary?)

이 type 들은 FUN_00056bf8 codec 에서만 등장 → **이 codec 이 처리하는 specific protocol** (예: 특정 sub-system 의 message format).

---

## 6. 신규 산출물

| 도구/문서 | 산출물 |
|---|---|
| `disasm_subsystem_func.py` (강화) | r0~r3 backtrace + register propagation + prev_instrs 컨텍스트 |
| `work/h3/queue_codec_disasm.json` | FUN_00056bf8 본문 |
| `work/h3/default_key_v2_disasm.json` | FUN_00064048 강화된 backtrace 결과 |
| `work/h3/cmd_processor_disasm.json` | FUN_000630e8 본문 |
| `work/h3/inner_helper_8aca_disasm.json` | (FUN_00008aca = epilogue 검증) |

---

## 7. 다음 세션 권장

### 자동 진척 가능

- ⭐ **FUN_000031dc 본문 분석** — 6.7KB 또 다른 MASSIVE state machine. FUN_00006334 에서 마지막 BL 호출되는 chain dispatcher 후보. `disasm_subsystem_func.py` 재사용.
- ⭐ **FUN_0004ad10 (context_getter) raw bytes 재분석** — Ghidra 가 `void → undefined4` 로 표시했지만 r0 인자 받을 가능성 검증. capstone 으로 인자 사용 패턴 확인.
- **type-5 reader 함수 발견** — cmp #0x05 arm 가진 함수 검색 → reader 측 로직 식별. byte stream parser candidate.
- **save game record processor 가설 검증** — _save 또는 P 폴더 자산 파일 포맷과 큐 byte stream 의 매핑 시도.

### 사용자 블로커

- SMAF→OGG (33 BGM/SFX) — sound dispatcher 발견과 시너지: 향후 sound ID 매핑 시 BGM 파일과 매핑 가능
- 대사 LLM 번역 (~$0.66, 9,741 unique 대사)

---

## 8. 핵심 교훈

1. **Ghidra 의 또 다른 misleading 패턴**: `void FUN_xxx(void) { return; }` (빈 함수) 도 Ghidra 의 분석 실패 신호일 수 있음. raw bytes 가 epilogue gadget 인 경우 다수. 402 stub + N 빈 함수 = 종합 분석 ceiling.
2. **shared epilogue gadget** = 컴파일러 최적화 패턴. 큰 함수의 다수 early-exit 가 한 epilogue 로 통합. FUN_00008aca 가 그 예.
3. **type tag protocol 매핑은 cumulative**: 각 함수 별 byte_append immediate 분석 → 누적 매트릭스. 4 writer 만 봐도 11 distinct type tags + 6 sub-opcodes 식별. 추가 writer 분석으로 확장 가능.
4. **PIC environment 의 인자 기반 helper**: `bl context_getter` 가 매번 다른 GOT slot offset 을 r0 로 전달. Ghidra 의 `void` 시그니처는 의심해야 함. r0 backtrace 로 인자 식별.
5. **r0 backtrace 의 한계**: 함수 인자 입력 / prior BL return value 케이스는 식별 불가능. dataflow analysis (caller-side 추적) 가 필요한데 ROI 점점 낮아짐.
