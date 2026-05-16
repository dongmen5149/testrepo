# Hero3 Ghidra — Round 43 / 2026-05-17 PM-7 (모든 17 event call sites event_id 매핑 + event 3 specific path 풀이)

> Round 42 (`ghidra-objectE-and-event-callers-2026-05-17.md`) 의 후속 — FUN_0002c6a4 의 17 callers 가 각자 어떤 event_id 를 trigger 하는지 정확히 매핑.

## 한 줄 요약

⭐⭐⭐ **17 callers 모두 event_id 추출 성공**: event 3 (8 callers, dominant) / event 4/7/12/13/14 (1 caller each, log-only) / event 17/18 (공통 handler) / dynamic event (FUN_00053e08). ⭐⭐⭐ **event 3 specific path 풀이**: sound 0x20 + 0x7 + vtable[+0x10] graphics call(0xb0, 0xa0 = 좌표 176,160) + state writes + FUN_00081744 byte arg = **screen transition / important state change handler**. ⭐⭐ **3 indirect entry 후보 모두 기존 함수 내부**: 0x28ada/0x28de8 = FUN_00026a80 (8.4KB subsystem router) + 0x424c2 = FUN_00041c14 (cluster #1 SM) → 신규 indirect entry 0개, 하지만 두 함수도 events trigger 한다는 신규 finding. ⭐⭐ **FUN_0003a444 = 1064B state-driven multi-event source** (4 calls 모두 event 3, conditional firing cmp #0xf/#0x10 match).

## 2JA: 3 indirect entry 후보 확인 — NEGATIVE 결과

`tools/recon/verify_indirect_entry_candidates.py` 결과 (extended search 0x4000):

| candidate | push 위치 | offset | 결론 |
|---|---|---|---|
| 0x28ada | 0x26a80 | +0x205a (8282B) | FUN_00026a80 (8.4KB subsystem router, Round 17) |
| 0x28de8 | 0x26a80 | +0x2368 (9064B) | FUN_00026a80 (같은 함수) |
| 0x424c2 | 0x41c14 | +0x8ae (2222B) | FUN_00041c14 (cluster #1 state machine, Round 36) |

⭐ **신규 indirect entry 0개** — 모두 기존 함수의 깊은 곳에 위치. 하지만 **두 함수도 event trigger 한다는 신규 finding**:
- **FUN_00026a80** (subsystem router) → event 13 (0x205a) + event 12 (0x2368)
- **FUN_00041c14** (cluster #1 SM) → event 7

## 2JB: FUN_0003a444 본문 (1064B, NEW multi-event source)

### 프로파일

- 16 cmp arms: cmp #0xf (5x), #2 (3x), #0x10 (3x), #1 (2x), #0xa, #0, #9
- cmp #0xf bls range guard at 0x3a476 (similar to FUN_0002c6a4 pattern)
- BL = **20 context_getter + 1 graphics_primitive** (state-heavy)
- 20 GOT slot literals + 3 medium ints + binary_addr
- 2 BL callers: 0x24242 (FUN_000241dc 5th indirect entry +0x66) + 0x3aa46

### 4 event call sites (모두 event 3)

```
0x3a516: cmp #0x10 beq → movs r0,#3 → bl FUN_0002c6a4   ; condition: byte == 0x10
0x3a66a: cmp #0xf  bne → movs r0,#3 → bl FUN_0002c6a4   ; condition: byte == 0xf
0x3a694: cmp #0xf  bne → movs r0,#3 → bl FUN_0002c6a4   ; condition: byte == 0xf
0x3a828: cmp #0x10 bne → movs r0,#3 → bl FUN_0002c6a4   ; condition: byte == 0x10
```

⭐ **FUN_0003a444 = state-driven event 3 generator** — byte field 가 특정 값 (0xf 또는 0x10) 일 때 event 3 발화.

저장: `work/h3/fun_3a444_multi_event_disasm.json`

## 2JB-2: 17 callers 의 event_id 매핑 종합

`tools/recon/extract_event_ids_3a444.py` 결과:

| event_id | dispatch path | 호출 횟수 | callers |
|---|---|---|---|
| **3** | specific 0x2c848 | **8** ⭐ | FUN_0003a444 (4 conditional) + FUN_000818f0 entity update + FUN_0002ae44 +0x40 + FUN_00086058 + FUN_000933e8 |
| 4 | (log only) | 1 | FUN_0002ae44 +0x6a |
| 7 | (log only) | 1 | FUN_00041c14 cluster #1 SM +0x8ae |
| 12 (0xc) | event 15 path 인접 | 1 | FUN_00026a80 +0x2368 |
| 13 (0xd) | (log only) | 1 | FUN_00026a80 +0x205a |
| 14 (0xe) | (log only) | 1 | FUN_000241dc 5th indirect entry (task[+0xf2] 조건) |
| **17 (0x11)** | 공통 handler | 1 | FUN_000245fc mode 7 ⭐ (Round 38 확정) |
| 18 (0x12) | 공통 handler | 1 | FUN_0002ae44 +0x294 |
| **dynamic** | (event_id = halfword + 7) | 1 | FUN_00053e08 +0x2be (table-driven) |

(Total: 17 callers, 9 distinct event_ids)

### 핵심 통찰

⭐⭐⭐ **Event 3 = "system-wide notification" event** (8 callers, 47% of all firings):
- entity update loop (FUN_000818f0) — entity 상태 변화
- state-driven FUN_0003a444 — 4개 conditional firings
- secondary state path FUN_0002ae44 +0x40
- FUN_00086058, FUN_000933e8 — 알 수 없는 시스템

⭐⭐ **Log-only events (4, 7, 13, 14)** — dispatcher 의 specific cmps 가 잡지 않는 event_id 들. Reach `task[0x290] = event_id` tail 만 실행 = **이벤트 로깅** (디버그 또는 다음 frame 처리용 마커).

⭐⭐ **Dynamic event (FUN_00053e08)** = `r3 = halfword[task+0x3b8] + 7`. NPC record 의 +0x3b8 offset = Round 14 의 "+0x3b8 arg short". 이 short 값 + 7 = event_id. **NPC record 의 arg field 로 dynamic event 발화**.

## 2JD: event 3 + event 15 specific paths 본문 풀이

### event 3 path (0x2c848..0x2c950)

`tools/recon/disasm_event_3_15_paths.py` 결과:

```
0x2c848: bl context_getter             ; r3 = task_ptr
0x2c850: r2 = task + offset
0x2c854: *r2 = 2                        ; state byte = 2 (transition start?)
0x2c856: movs r0, #0x20
0x2c858: bl FUN_0003d5d0                ; ⭐ sound_trigger(0x20) — 신규 sound_id
0x2c85c: load sl-relative global obj
0x2c864: r3 = vtable[+0x10] (method ptr)
0x2c866: movs r0, #0xb0 (= 176)
0x2c868: movs r1, #0xa0 (= 160)
0x2c86a: bl 0xa42a0                     ; ⭐ veneer bx r3 — obj.vtable[+0x10](0xb0, 0xa0) = 좌표 (176,160) graphics call
0x2c870: store r2 to sl-relative obj
0x2c878: bl 0xd53c                      ; helper
0x2c884: bl context_getter (3 more times)
0x2c8a0..0x2c8a8: push 5 args (sp, sp+4, sp+8, sp+0xc)
0x2c8d4: r4 = task[+0x30]
0x2c8d8: r1 = 0, r2 = 0
0x2c8da: r3 = 0xb0
0x2c8dc: bl 0xa42a4                     ; ⭐ 두 번째 veneer bx (0xb0 in r3)
0x2c8e0: b 0x2ca6c (return)

# Alternative paths within event 3:
0x2c8e2/8e8: bl FUN_00024a6c             ; another helper
0x2c8ec: bl FUN_0002cb78                 ; another helper
0x2c8f2: r3 = task[arg] + offset; ldrb
0x2c902: bl FUN_00081744(byte_arg)      ; ⭐ unknown function
0x2c906/914: context_getter + clear byte
0x2c922: movs r0, #7
0x2c924: bl FUN_0003d5d0                ; ⭐ sound_trigger(7) — 두 번째 신규 sound_id
0x2c928: context_getter
0x2c932: state byte = 1                  ; final state
0x2c936: b 0x2ca6c
```

⭐⭐⭐ **event 3 = "important state transition" handler**:
- **2 sounds played** (sound_id 0x20 + 0x7 — Round 23 list 외 신규 ID)
- **graphics call** vtable[+0x10](0xb0, 0xa0) = (x=176, y=160) 좌표에서 그리기
- **5 args pushed to stack** + 2 veneer calls = complex call signature
- **state byte transitions**: 2 → ? → 0 → 1 (lifecycle)
- 다중 helper calls: FUN_00024a6c, FUN_0002cb78, FUN_00081744

가장 가능성 높은 정체: **screen overlay / popup / animated transition** (그래픽 + 사운드 + 상태 전환).

### event 15 path (0x2c952..0x2c9ca)

```
0x2c952: bne 0x2c95a
0x2c954: bl FUN_00081688                 ; helper (NEW)
0x2c958: b 0x2ca6c (return)

# Else path:
0x2c95a: r3 = task + 0xc (offset)
0x2c95e: r3 = *r3
0x2c960: r0 = 0xa4 << 2 = 0x290         ; ⭐ task[0x290] = last_event_id (Round 41 field)
0x2c964: r3 += 0x290
0x2c966: r3 = byte at task[0x290]
```

event 15 = **last_event_id 조회 후 분기 처리** — 매우 짧고 가벼움. **이전 event 의 후속 처리** 시그니처.

## 2JC: FUN_000818f0 entity update 의 event_id = 3

```
0x819e2: movs r0, #3
0x819e4: bl FUN_0002c6a4
```

직전 코드 (0x819d4..0x819e0):
```
0x819d4: add r3, sl
0x819d6: adds r3, r2, r3
0x819d8: ldr r2, [r3]
0x819da: ldr r3, [pc, #0x2ec]
0x819dc: add r3, sl
0x819de: adds r3, r2, r3
0x819e0: mov pc, r3                    ; ⭐ indirect jump via JT (entity dispatch)
```

⭐⭐ **FUN_000818f0 (entity update loop) JT 직후 event 3 trigger** = entity state machine 의 dispatch 결과 처리 완료 후 system-wide event 3 발화. **entity update → event 3 → 시스템 전체 알림**.

## 2JF: 신규 sound IDs

Round 23 의 11 immediate sound IDs: 0x83, 0x84, 0x87, 0x8d, 0x8e, 0x9b, 0xa4, 0xa5.

Round 43 신규 (event 3 specific path 에서 발견):
- **sound_id 0x20** (= 32) — event 3 전반부에서 재생
- **sound_id 0x07** (= 7) — event 3 후반부에서 재생

총 known immediate sound IDs: **13개** (Round 23 11 + Round 43 2).

## Round 43 종합 진척

### ✅ 검증 추가

1. **3 indirect entry 후보 모두 부정** (FUN_00026a80 / FUN_00041c14 내부) — 시스템 진입점은 여전히 6개
2. **FUN_00026a80 (subsystem router) → events 12/13 trigger 신규 finding**
3. **FUN_00041c14 (cluster #1 SM) → event 7 trigger 신규 finding**
4. **17 callers 모두 event_id 매핑 완료** (9 distinct event_ids)
5. **event 3 = dominant (8 callers, 47%)** — system-wide notification
6. **event 3 specific path 본문 풀이** = screen transition handler (sound + graphics + state)
7. **FUN_00053e08 = dynamic event source** — NPC record[+0x3b8] arg + 7 = event_id (Round 14 NPC layout 연결)
8. **신규 sound IDs 0x20, 0x7** (총 13 known)
9. **FUN_0003a444 = state-driven event 3 generator** (4 conditional firings)

### 진척률 (Round 43 시점)

- Ghidra 게임 로직 리버싱: ~35~42% → **~38~45%**
- 전체: ~32~42% → **~35~45%**

### ⭐ 다음 라운드 (44) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2KA** | **event 3 specific path 의 sl-relative global obj 정체** (vtable [+0x10] graphics method) — ObjectF 후보 | sl literal 추출 (Round 42 trace 도구 재사용) |
| ⭐⭐ **2KB** | FUN_00081744, FUN_00081688 본문 — event 3 / event 15 helpers | inline disasm |
| ⭐⭐ **2KC** | FUN_00024a6c, FUN_0002cb78 본문 — event 3 다중 helpers | inline disasm |
| ⭐⭐ **2KD** | FUN_00086058, FUN_000933e8 본문 — event 3 trigger functions | inline disasm |
| ⭐⭐ **2KE** | FUN_00053e08 본문 (dynamic event source, +0x3b8 arg+7) — NPC arg → event 매핑 | inline disasm |
| ⭐ **2KF** | event 17 → 공통 handler 의 ObjectE.method0c (vtable [+0xc]) 정체 정밀 분석 | sl-relative ldr 추출 |
| ⭐ **2KG** | 신규 sound IDs 0x20, 0x7 의 snd/ 자산 매핑 | 자산 파일 점검 |

### 도구 산출 (Round 43)

- `tools/recon/verify_indirect_entry_candidates.py` (new) — push prologue extended search + BL caller scan
- `tools/recon/extract_event_ids_3a444.py` (new) — BL site backward 16-byte disasm 으로 event_id immediate 추출
- `tools/recon/disasm_event_3_15_paths.py` (new) — event 3/15 specific path capstone disasm

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 42 의 [`ghidra-objectE-and-event-callers-2026-05-17.md`](ghidra-objectE-and-event-callers-2026-05-17.md) 읽기
2. PROGRESS.md 의 event_id 매핑 표 확인 (event 3 dominant)
3. **권장 첫 작업: 2KA** — event 3 specific path 의 sl-relative obj 정체 (graphics call vtable [+0x10] 의 메서드). Round 42 의 `trace_2c9ca_sl_global.py` 패턴 재사용 가능.
