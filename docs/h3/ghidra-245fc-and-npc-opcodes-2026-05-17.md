# Hero3 Ghidra — Round 39 / 2026-05-17 PM-3 (FUN_000245fc 본문 + NPC 6 special opcodes + FUN_00098904 정정)

> Round 38 (`ghidra-op12-inner-jt-and-6th-entry-2026-05-17.md`) 의 후속 — Round 38 에서 발견한 6번째 indirect entry 의 내부 dispatch 풀이 + NPC vs SCN scripting engine 비교 + FUN_00098904 의 본문 정밀.

## 한 줄 요약

FUN_000245fc(6번째 indirect entry, 388B) 의 진입 dispatch 풀이 → **task_struct[0xa0c0] = "subsystem mode byte"** (신규 식별), mode 0/3/4/7 의 4-way state machine. **mode==3 AND task_struct[0x7c]==4** 조건에서만 cluster #1 state machine (FUN_00040fb0) 실행. NPC vs SCN 의 6 special opcodes 비교 = **opcode 0x10 완벽 동일**, **opcode 0x12 SCN/NPC 차이 8배** (SCN=11720B Korean dialogue interpreter / NPC=1434B 단순 short-message handler). FUN_00098904 정정 = 1524B / 754 instr / 16 arms / **BL=3× screen_ptr only, NO ctx** = **memory-manipulation focused multi-mode renderer** (43 system-wide callers의 swiss-army graphics helper).

## 2FA: FUN_000245fc 본문 정밀 — 6번째 indirect entry 의 state dispatch

### 진입 dispatch 풀이 (capstone)

`tools/recon/disasm_245fc_head.py` 출력:

```
0x245fc: push {r4-r7,lr}
0x245fe: bl context_getter        ; r5 = task_struct (call 1)
0x24604: bl context_getter        ; r4 = task_struct (call 2)
0x2460a: bl FUN_0002bee8           ; ⭐ NEW init helper (604B)
0x2460e: ldr r1 = 0xa0c0           ; field offset literal
0x24614: ldrsb r3, [r4+0xa0c0]     ; ⭐⭐⭐ r3 = task_struct[0xa0c0] = subsystem mode byte
0x24616: cmp r3, #4 → beq 0x246b4  ; mode 4 path → bl 0x983e8 (ObjectA cluster)
0x2461a: cmp r3, #4 → ble 0x24620  ; mode ≤4
0x2461e: b 0x24714                 ; mode >4 (mode 7 path)
0x24620: cmp r3, #3 → beq 0x24626  ; mode 3 path
0x24624: pop {r4-r7,pc}            ; default: return
0x24626: ldr r3, [r5, #0x7c]       ; task_struct[0x7c]
0x24628: cmp r3, #4 → bne 0x24624  ; mode 3 AND task[0x7c]==4 ?
0x2462c: bl FUN_00040fb0           ; ⭐⭐⭐ cluster #1 state machine call!
0x24630: bl FUN_00046de0           ; ⭐ NEW post-cluster#1 helper (752B)
```

### state machine 풀이 (전체 13 cmp arms)

| mode (task_struct[0xa0c0]) | dispatch | BL chain | 의미 추정 |
|---|---|---|---|
| **0** | pop & return | (none) | idle / no-op |
| **3** + task[0x7c]==4 | 0x24626 | bl FUN_00040fb0 → bl FUN_00046de0 → 0x9cb8~0x9cd8 record array 처리 (loop with 0x158 stride) | ⭐⭐⭐ **active update** = cluster #1 cutscene playback |
| **4** | 0x246b4 | bl 0x983e8 (ObjectA cluster) | exit / cleanup (ObjectA 호출) |
| **7** | 0x24714 | gate task[0xa1f6] != 0 → bl FUN_00025f30(r0=18, r1=11, r2=&task[0xa288], r3=&task[0xa289]) → if returns !=0, bl FUN_0002c6a4(r0=0x11=17) | ⭐ **event trigger** (state transition / "cutscene ended" 이벤트) |
| other (≥5, !=7) | fall to 0x24714 | (state-7 gate also reached from "mode >4 && mode !=7" but most likely no-op) | fallback |

### task_struct 필드 사용 종합 (14 GOT slot literals)

- **0xa0c0** ⭐ NEW = subsystem mode byte (primary dispatch)
- **0x7c** = secondary gate (mode 3 condition)
- **0x9cb8 / 0x9cbc / 0x9cc0 / 0x9ccc / 0x9cd4 / 0x9cd8** = record array slots (Round 21+24 record array dispatcher domain, 6 sites)
- **0x9c6c** = byte cluster 인접 (0x9c70 cluster 의 4 bytes 전)
- **0x9c80** (= 0xae << 2 = 0x2b8 offset) = byte field accessed via immediate construction
- **0xa1f6** = mode 7 gate flag (byte)
- **0xa288 / 0xa289** = mode 7 byte pair (16-bit ?)

### 0x158-stride 레코드 배열 처리 (mode 3 path 내부)

mode 3 의 메인 처리 loop (0x24656~0x2467e):

```
0x2465a: r3 = 0xac; r3 <<= 1 → r3 = 0x158        ; ⭐ stride = 344 bytes
0x2465e: r6 = i (loop var)
0x24660: r6 = r3 * r6                              ; offset = i * 0x158
0x24662: r2 = task[+0x9cb8]                        ; record array base
0x24664: r3 = task[+0x9cb8 + i*0x158]              ; record[i] = pointer
0x24666: r3 = *r3                                   ; deref
0x24668: r3 = byte [r3 + 0x11]                     ; flag byte at +0x11 of pointed struct
0x2466a: cmp #0 bne 0x246e8                         ; non-zero → bl FUN_00041a68 (handler)
```

**0x158 = 344 byte record stride** = 어떤 entity record 의 stride. Round 28 의 38B entity state record (0xac78 cluster) 와는 별개 — 더 큰 구조의 다른 entity set.

### 6번째 indirect entry 의 게임 시스템적 역할 — 추정

**가설**: FUN_000245fc 는 **cutscene/event progression slot** — 이유:
1. mode 3 path 가 cluster #1 state machine 호출 → cluster #1 의 4-field state (start/step/main/sub) 가 cutscene 단계 표현에 적합
2. mode 4 path 가 ObjectA cluster 호출 → ObjectA = resource manager (Round 20), cutscene 종료 시 자원 정리
3. mode 7 path 가 FUN_0002c6a4(0x11) = event 17 호출 → state transition / "cutscene 끝" 이벤트
4. 0x158-stride record array = cutscene step records (각 344B 가 단계별 상세 정보)
5. 0xa288/0xa289 byte pair = byte-pair는 자주 (delay, sound_id), (current_step, total_steps) 같은 페어
6. Pure-state (BL=7 ctx only) + small profile (388B) = **시스템 hook function** 표준 형태

**대안 가설**: menu/dialog system — 다음 단계에서 0x9cb8 record array 의 element 의 dump 확인 필요.

저장: `work/h3/fb0_caller1_245fc_disasm.json`, `tools/recon/disasm_245fc_head.py`, `tools/recon/disasm_245fc_state7.py`

## 2FB: FUN_00098904 본문 정정 (op12 inner JT destinations)

### 정정된 통계 (bounded disasm)

기존 Round 38 의 "1806 instr / 41 arms" 는 over-shoot 오인. 정확한 통계:

- 범위: 0x00098904 ~ 0x00098ef8 = **1524 byte**, **754 instructions**, **16 cmp arms**
- cmp imm 분포: **cmp #0 (11x)** + cmp #1 (2x) + **cmp #0x7f (1x)** + cmp #4 (1x) + cmp #5 (1x)
- **BL = 3× screen_ptr_getter only** — ⭐ NO context_getter, NO sound, NO draw, NO helper
- 1 PC-rel literal only (zero)

### 결정적 패턴

**3× screen_ptr_getter + 0× ctx + 0× draw_text** = **task_struct 접근 없이 함수 인자만으로 작동하는 memory-manipulation routine**. SCN/NPC common handler 와 정반대 프로파일 (common = 3× draw + 3× helper + 3× screen + 2× sound + 1× ctx).

### 8 JT entry labels 의 의미

opcode 0x12 inner JT 의 7 dispatch destinations + 1 default (66/74 cases) 모두 FUN_00098904 안의 entry label:

| offset | 위치 | 분기 패턴 (인접 arms) | 추정 의미 |
|---|---|---|---|
| +0x54 | 0x98958 | (head, 첫 진입 후 직진) | special intro / case 0 전용 |
| +0x60 | 0x98964 | (close to +0x54) | special variant / case 11 |
| +0x16a | 0x98a6e | (cmp #0x7f 위치 근처: 0x98a5e) | DEL control / case 13 |
| +0x1c4 | 0x98ac8 | (cmp #0/#1 dispatch 영역: 0x98ab0+) | case 12 standard |
| +0x224 | 0x98b28 | (cmp #4/#5 dispatch 영역: 0x98b22/0x98b2e) | case 14+15 shared |
| +0x2ea | 0x98bee | (mid-function) | case 71 |
| +0x35c | 0x98c60 | (later body, screen_ptr 0x98d2e 근처) | case 73, screen-blit |
| **+0x3b0** | 0x98cb4 | (default tail, 66/74 cases, screen_ptr 0x98d2e + 0x98df0 + 0x98e76) | **default rendering** (3 screen_ptr 모두 이 path에서) |

⭐ 3× screen_ptr_getter 모두 +0x3b0 default path 의 tail (0x98d2e / 0x98df0 / 0x98e76) → **default = 멀티-스크린 buffer 처리** (frame buffer + back buffer + work buffer 시그니처).

### 가설: FUN_00098904 = "screen blitter / pixel-level operator"

- **43 system-wide callers** = utility-class function (Round 38 finding)
- pure memory manipulation + screen pointer 만 외부에서 받음
- 8 entry labels = 8 specialized blit modes (copy / transparent / mirror / clear / fill / scale / 등)
- 66/74 sparse JT = "대부분의 dialogue byte는 default rendering 으로 분기, 7개 byte 만 specialized"

저장: `work/h3/op12_dispatcher_98904_v2_disasm.json`

## 2FD: NPC vs SCN 6 special opcodes 비교

### 일괄 disasm 통계

| opcode | NPC (FUN_0008b2e8 inline) | SCN (FUN_0008dcd8 inline) | 차이 |
|---|---|---|---|
| **0x0d** | 500B / 230 instr / 1 arm / 10 BL | 524B / 240 instr / 1 arm / 9 BL | 거의 동일 (2× each pattern) |
| **0x0e** | 544B / 255 instr / 1 arm / 8 BL | 552B / 262 instr / 1 arm / 7 BL | 거의 동일 |
| **0x0f** | 764B / 364 instr / 2 arms (';' + #0) / 11 BL | 832B / 398 instr / 2 arms (';' + #0) / 11 BL | 거의 동일 (둘 다 ';' 구분자) |
| **0x10** | 586B / 281 instr / 2 arms (';' + #0) / 8 BL | 586B / 281 instr / 2 arms (';' + #0) / 8 BL | ⭐ **완벽 동일** (size + instr + arms + BL 모두 일치) |
| **0x11** | 492B / 228 instr / 1 arm / 10 BL | 338B / 157 instr / 0 arms / 8 BL | NPC가 약간 더 큼 (NPC 의 추가 정리?) |
| **0x12** | **1434B / 669 instr / 3 arms / 27 BL** | **11720B / 5593 instr / 47 arms / 86 BL** | ⭐⭐⭐ **SCN이 8배 큼** |

### 결정적: NPC opcode 0x12 vs SCN opcode 0x12

| 특징 | NPC 0x12 | SCN 0x12 |
|---|---|---|
| size | 1434B | 11720B (8.2×) |
| cmp arms | 3 (cmp #0 ×2, cmp #0x11) | 47 (state 35 + sentinel 6 + EUC-KR 4 + ASCII 2) |
| **EUC-KR 0x89/0x8f** | ❌ 없음 | ✅ 4 arms (CP949 한글 음절 영역) |
| **ASCII tokens (';','I','2')** | ❌ 없음 | ✅ 3 arms |
| **inner 74-entry JT** | ❌ 없음 | ✅ @ 0xabcb4 → FUN_00098904 8 labels |
| **0xa22c sound state literal** | ❌ 거의 없음 | ✅ 32× 참조 |
| BL 패턴 | 11× screen + 7× helper + 4× draw + ... | 41× ctx + 15× screen + ... |

⭐⭐⭐ **NPCs use a stripped-down dialogue interpreter** — short messages only, no Korean multi-byte parsing, no scripting state, no sound integration. **SCN opcode 0x12 만이 full Korean dialogue engine** (cutscenes, events, scripted scenes).

### Android 리메이크 영향

- **NPC dialogue port** = 단순 branching message system (1434B 단순 변환)
- **Scene dialogue port** = 풀 스크립팅 엔진 with Korean parsing (11720B → 복잡한 변환 필요)
- 13 common opcodes (0x00~0x0c) = 둘 다 거의 동일한 text-draw paired-pattern → 한 번 구현으로 양쪽 커버

저장: `work/h3/npc_op0d_8c79c_disasm.json` ~ `work/h3/npc_op12_8d2e2_disasm.json` (6개 JSON)

## Round 39 종합 진척

### ✅ 검증 추가

1. **task_struct[0xa0c0] = subsystem mode byte** 신규 식별 (FUN_000245fc 의 primary dispatch key)
2. **FUN_000245fc state machine 완전 풀이** — 4-way mode dispatch (0/3/4/7) + cluster #1 trigger 조건 (mode==3 AND task[0x7c]==4)
3. **FUN_000245fc 의 dedicated helpers 식별**: FUN_0002bee8 (init, 604B) + FUN_00046de0 (post-cluster#1, 752B) + FUN_00053010 (terminal, 348B)
4. **FUN_00098904 정정**: 1524B / 754 instr / 16 arms / **BL=3× screen_ptr only** = pure memory-manipulation renderer (43 system-wide callers의 swiss-army)
5. **NPC 6 special opcodes 본문**: opcode 0x10 SCN과 완벽 동일, **opcode 0x12 NPC는 SCN의 1/8 크기** (stripped-down short-message interpreter)

### 진척률 (Round 39 시점)

- Ghidra 게임 로직 리버싱: ~20~30% → **~25~33%**
- 전체: ~22~32% → **~25~35%**

### ⭐ 다음 라운드 (40) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2GA** | **task_struct[0x9cb8 record array] 의 0x158-stride record 구조 분석** | record 의 0x11 offset 가 flag byte 임을 확인. 다른 offsets 의 의미 풀이 |
| ⭐⭐ **2GB** | FUN_00025f30 본문 (mode 7 의 r0=18, r1=11, r2/r3=byte addr 호출) 분석 | event/dialog 처리 메커니즘 |
| ⭐⭐ **2GC** | FUN_0002c6a4 본문 (event 0x11 trigger) — Round 30 의 task[+0xf2] event 핸들러와 비교 | event 시스템 통합 |
| ⭐⭐ **2GD** | FUN_00046de0 본문 정밀 (752B, cmp #0x10/#7/#9 의 의미) | post-cluster#1 처리 메커니즘 |
| ⭐ **2GE** | FUN_0002ae44 callers (0x248ce, 0x24fd0) 추적 — secondary state path | Round 39 미완 작업 |
| ⭐ **2GF** | task_struct[0xa0c0/0xa1f6/0xa288/0xa289] 의 system-wide 사용 분포 | mode byte + 페어 byte 의미 |
| ⭐ **2GG** | FUN_00098904 의 8 entry labels 본문 정밀 (각 label 의 진입 동작) | blit mode 별 의미 |
| ⭐ **2GH** | NPC opcode 0x12 (1434B) 본문 — 27 BL 의 BL chain 으로 NPC short-message rendering 풀이 | NPC 대화 처리 정확 |

### 도구 산출 (Round 39)

- `tools/recon/disasm_245fc_head.py` (new) — capstone 윈도우 disasm (0x245fc head)
- `tools/recon/disasm_245fc_state7.py` (new) — state-7 path disasm

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 38 의 [`ghidra-op12-inner-jt-and-6th-entry-2026-05-17.md`](ghidra-op12-inner-jt-and-6th-entry-2026-05-17.md) 읽기
2. PROGRESS.md 의 game update flow + 6 indirect entries 표 확인
3. **권장 첫 작업: 2GA** — 0x9cb8 record array 의 0x158-stride record 구조 분석. record 들이 cutscene step 인지 entity record 인지 확인.
4. 가설 검증을 위해 `work/h3/fb0_caller1_245fc_disasm.json` 의 14 GOT slot literal + 13 arms 의 정확한 위치를 참고.
