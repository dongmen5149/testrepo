# Hero3 Ghidra — Round 40 / 2026-05-17 PM-4 (callback queue 풀이 + NPC table query + event dispatcher)

> Round 39 (`ghidra-245fc-and-npc-opcodes-2026-05-17.md`) 의 후속 — FUN_000245fc 의 4-way state machine 안의 세부 구조 정밀화.

## 한 줄 요약

⭐⭐⭐ **0x9cb8 cluster = 2-stage frame-callback queue 시스템**: stage 1 (344B records, callback @+0x154, 3-level gating) + stage 2 (28B records, callback @+0x18). cursors 가 frame 마다 8B 씩 advance. ⭐⭐⭐ **FUN_00025f30 = NPC table query** (Round 14 의 0x3c4×0x3c grid 정확히 일치, +0x3b3 flag byte 검사) → **task[0xa0c0] subsystem = NPC dialog/quest 시스템** (cutscene 추측 정정). mode 7 = NPC 조건 쿼리 + event 17 trigger. ⭐⭐ **FUN_0002c6a4 = 17-caller system-wide event dispatcher**, 9 arms (events 8/c/d/e/f/10 공통 handler). ⭐⭐ **FUN_00046de0 = record array cleanup/finalizer** (memset 2× + cursor advance).

## 2GA: 0x9cb8 cluster = 2-stage callback queue

### Stage 1: 0x158-stride heavy callbacks

FUN_000245fc 의 mode 3 path 본문 정밀 트레이스 (capstone, `disasm_245fc_record_loop.py`):

```
# 설정 (after FUN_00040fb0 + FUN_00046de0):
0x24634: r3 = *(task + 0x9cbc)      ; source pointer
0x24638: r3 = *r3                    ; deref pointer
0x2463e: r3 += 8                     ; advance 8 bytes/frame
0x24646: *(task + 0x9cd4) = r3       ; ⭐ store cursor — stream-style cursor advancement

# 카운트 + 루프 진입:
0x2464e: count = (int16)task[0x9cc0]
0x24658: r7 = &task[0x9cb8]          ; base address holder

# 메인 루프:
0x2465a: stride = 0xac << 1 = 0x158  ; ⭐ 344-byte record stride
0x24660: offset = i * 0x158
0x24662: base = *r7 = task[0x9cb8]   ; record array base
0x24664: record_word_0 = *(base + i*0x158)  ; first word of record[i] = pointer
0x24666: sub_struct = *record_word_0          ; double deref
0x24668: flag = byte at sub_struct + 0x11    ; ⭐ flag byte
0x2466a: if flag != 0 → goto special path (0x246e8)

# Special path (when record [+0x11] flag set):
0x246e8: bl FUN_00041a68            ; r0 = task[0x0a5d] (gate flag)
0x246ee: if gate != 0 → skip
0x246f6: r3 = 0xae << 2 = 0x2b8     ; another gate offset
0x246fc: r3 = byte at task[0x2b8]
0x24700: if non-zero → skip
0x24702: r0 = *r7 = task[0x9cb8]    ; base ptr
0x24706: r0 += i*0x158                ; record[i]
0x24708: r1 = 0xaa << 1 = 0x154      ; ⭐ callback offset
0x2470a: r3 = record[i] + 0x154
0x2470c: r3 = *(record[i] + 0x154)    ; load function pointer
0x2470e: bl 0xa42a0                   ; veneer = bx r3 (indirect call)
```

### Stage 2: 0x1c-stride simple callbacks

```
0x246c0: r2 = task[0x9cd8]            ; ⭐ stage 2 base (DIFFERENT from stage 1)
0x246c6: stride = 0x1c = 28           ; ⭐ smaller stride
0x246ca: r0 = i * 0x1c
0x246cc: r0 += base
0x246ce: r3 = *(record[i] + 0x18)    ; ⭐ callback at offset 0x18
0x246d0: bl 0xa42a0                   ; veneer = bx r3
```

### 0x9cb8 cluster 필드 layout (Round 40 정밀)

| offset | size | 용도 |
|---|---|---|
| **0x9cb8** | word | stage 1 record array base pointer (344B records) |
| **0x9cbc** | word | source pointer (advance 8B/frame → stored to 0x9cd4) |
| **0x9cc0** | int16 | stage 1 record count |
| **0x9ccc** | int16 | stage 2 record count |
| **0x9cd4** | word | stage 1 cursor (advances 8B/frame from 0x9cbc) |
| **0x9cd8** | word | stage 2 record array base pointer (28B records) |

### 3-level gating

stage 1 callback 실행 조건 (모두 만족):
1. **per-record gate**: `(*record[i].sub_struct)[+0x11] != 0`
2. **global gate 1**: `task[0x0a5d] == 0` (read via FUN_00041a68)
3. **global gate 2**: `task[0x02b8] == 0` (= 0xae << 2 offset)

### FUN_00041a68 풀이 (20B tiny wrapper)

```
push {lr}
bl ctx_getter            ; r0 = task_ptr
ldr r3 = 0x0a5d           ; literal
adds r0, r0, r3
ldrb r0, [r0]             ; return (uint8)task[0x0a5d]
pop {pc}
```

4 callers: 0x246e8 (FUN_000245fc), 0x42f7c, 0x7b248, 0x7c8cc.

### 해석

**Frame-driven callback queue / job scheduler**:
- Stage 1 = heavy 344B records with payload (sub-struct ptr at +0x00, callback at +0x154)
- Stage 2 = lightweight 28B records (callback at +0x18)
- Both lists scan each frame; callbacks fire when gates clear
- Stream-style cursor advancement (8B/frame from 0x9cbc → 0x9cd4) → **bytecode-like sequential consumption**

## 2GB: FUN_00025f30 = NPC table query (mode 7 의 핵심)

### 호출 위치

```
FUN_000245fc mode 7 path (0x24714):
  bl FUN_00025f30(r0=0x12=18, r1=0xb=11, r2=&task[0xa288], r3=&task[0xa289])
  if (r0 != 0) → bl FUN_0002c6a4(r0=0x11=17, event trigger)
```

### 본문 핵심 패턴 (444B / 221 instr / 3 arms)

```
0x25fc4: r3 = 0xf1 << 2 = 0x3c4    ; ⭐ outer stride = 964 byte (NPC record size)
0x25fc8: r2 = i_outer * 0x3c4

0x25fca: r3 = 0x3c = 60             ; ⭐ inner stride = 60 byte (sub-record)
0x25fcc: r3 = i_inner * 0x3c
0x25fce: r3 = outer + inner
0x25fd0: r3 += base_ptr               ; r3 = absolute address

0x25fd2: r2 = 0xec << 2 = 0x3b0
0x25fd6: r3 += 0x3b0
0x25fd8: r3 = byte at record[+0x3b3] ; ⭐ NPC flag byte
0x25fda: cmp r3, #0 → process if non-zero
```

### Round 14 NPC record layout 완전 일치

Round 14 (PROGRESS.md):
> "NPC slot record: stride 0x3c4, +0x3b3 flag, +0x3b6 opcode short, +0x3b8 arg short."

⭐⭐⭐ **FUN_00025f30 = NPC table search routine** — 입력으로 (row=18, col=11) 받고 해당 위치의 NPC record 의 +0x3b3 flag 검사. 일치하는 NPC 찾으면 r0 != 0 반환.

### task[0xa0c0] subsystem 정정 — **NPC/dialog 시스템**

이전 Round 39 의 "cutscene/event" 가설을 정정:

| mode | 동작 | 의미 |
|---|---|---|
| 0 | return | idle (NPC 비활성) |
| **3** + task[0x7c]==4 | callback queue 실행 (cluster #1 → 0x9cb8 2-stage) | active NPC 진행 (대화/상호작용) |
| 4 | bl 0x983e8 (ObjectA cluster) | NPC 자원 정리 |
| **7** | NPC table query → if found, event 17 trigger | NPC 조건 검사 + 게임 진행 |

⭐⭐⭐ **task[0xa0c0] = "NPC interaction subsystem mode"** (cutscene이 아니라 NPC dialog/quest system).

## 2GC: FUN_0002c6a4 = system-wide event dispatcher (996B)

### 통계

- 17 BL callers system-wide (0x24274, 0x2474c=FUN_000245fc mode 7, 0x28ada, 0x28de8, 0x2ae84, 0x2aeae, 0x2b0d8, 0x2b0ea, 0x3a516, 0x3a66a, 0x3a694, 0x3a828, 0x424c2, 0x540c6, 0x819e4, 0x860c2, 0x93454)
- 9 cmp arms: cmp #0xf (2x), #0x00 (2x), #0xc, #0x10, #0x08, #0x0d, #0x0e
- **events 8, 13, 14, 15, 16 → 공통 handler 0x2c9ca** (similar to Round 30 의 sparse JT 패턴)
- BL = 16 ctx + 2 screen_ptr_getter (r0=0xb0 constant = 176, 화면 번호?)

### task_struct 필드 참조

- `r0=0x9c8c` (2x) — byte field (byte cluster 인접)
- `r0=0x11d` — small offset
- `r0=0xa1f4` — 인접 0xa1f6 (mode 7 gate)
- immediates: 0xf, 0xb0 (2x), 0x1e (30), 0x7 — 인자나 화면 ID

### 해석

**중앙 event dispatcher** — event ID (r0) 에 따라 다른 처리 path 선택. 게임 전체에서 이벤트 발생 시 호출:
- event 0x11 (17) = FUN_000245fc mode 7 에서 호출 = NPC dialog 진행
- event 0x10 (16) = Round 30 의 event -10 → task[+0xf2] short 와 연관
- events 8/13/14/15/16 = 공통 path (대량 유사 처리)

저장: `work/h3/event_trigger_2c6a4_disasm.json`

## 2GD: FUN_00046de0 = record array cleanup/finalizer (752B)

### 프로파일

- 13 cmp arms: cmp #0 (10x), cmp #16/#7/#9 (1x each)
- BL = 1 ctx + **2 memset_like** (0x9fb78)
- task_struct 필드: 0x9cbc, 0x9cb8, 0x9cc0 (cluster #1 stage), 0x9bf0, 0x16c (alternate task ptr), 0x29f, 0x2b3, 0x2b6, 0x2d9, 0x262, 0x398

### 역할

FUN_000245fc 의 mode 3 path 에서 callback queue 실행 직후 호출:
1. 2× memset = stage 1/stage 2 buffer 클리어
2. 카운트 리셋 (writes to 0x9cc0)
3. 커서 진행 (writes to 0x9cbc)
4. 부수 상태 갱신 (0x9bf0, 0x16c, 0x29f 등)

⭐ **매 frame 큐 상태 정리 → 다음 frame 을 위한 준비**.

## Round 40 종합 진척

### ✅ 검증 추가

1. **0x9cb8 cluster 2-stage callback queue 풀이** — stage 1 (344B/callback@0x154) + stage 2 (28B/callback@0x18) + 3-level gating + stream cursor
2. **FUN_00041a68 = task[0x0a5d] flag byte reader** (20B tiny wrapper, 4 callers)
3. **FUN_00025f30 = NPC table query** (Round 14 의 0x3c4×0x3c grid + +0x3b3 flag 정확히 일치) ⭐⭐⭐ 큰 정정
4. **task[0xa0c0] subsystem = NPC dialog/quest 시스템 확정** (cutscene 추측 정정)
5. **FUN_0002c6a4 = 17-caller event dispatcher** (events 8/c/d/e/f/10 공통 handler, sparse 패턴)
6. **FUN_00046de0 = record array cleanup/finalizer** (memset 2× + cursor advance)

### 진척률 (Round 40 시점)

- Ghidra 게임 로직 리버싱: ~25~33% → **~30~38%**
- task_struct 모델: ~32% → **~35%** (0x9cb8 cluster 6 fields 정밀)
- 전체: ~25~35% → **~28~38%**

### ⭐ 다음 라운드 (41) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2HA** | **FUN_0002c6a4 event dispatcher 의 cmp 분기 별 본문 추적** (events 8/c/d/e/f/10 공통 + 0/f 분기 path 의 의미) | inline disasm + arm 별 BL chain 풀이 |
| ⭐⭐ **2HB** | NPC table 의 정확한 차원 (0x3c4 × 0x3c) 의 row/col 개수 확정 — 게임 내 NPC count | 게임 자산 자료 + ctx pcrel 추적 |
| ⭐⭐ **2HC** | callback queue 의 stage 1 record sub-struct 구조 (+0x11 외 다른 필드들) | record dump + sub-struct 분석 |
| ⭐⭐ **2HD** | FUN_00025f30 의 두 번째 caller (0x26124) — 다른 호출 컨텍스트 (NPC 쿼리 다른 용도) | container 함수 분석 |
| ⭐ **2HE** | callback queue 의 함수 포인터 destinations (record[+0x154] / record[+0x18]) — 실제 callback 함수들 | runtime 시뮬레이션 or 자산 분석 |
| ⭐ **2HF** | task[0x0a5d / 0x02b8 / 0xa1f6 / 0xa288 / 0xa289] system-wide 사용 분포 | wide-scan |
| ⭐ **2HG** | FUN_00041a68 의 다른 3 callers (0x42f7c, 0x7b248, 0x7c8cc) — task[0x0a5d] 사용 context | container 함수 분석 |
| ⭐ **2HH** | FUN_0002ae44 callers 추적 (0x248ce, 0x24fd0) — Round 38 미완 | `find_callers_generic.py` |

### 도구 산출 (Round 40)

- `tools/recon/disasm_41a68_tiny.py` (new) — 20B tiny function 디스어셈블
- `tools/recon/disasm_245fc_record_loop.py` (new) — record loop body capstone disasm
- `tools/recon/disasm_25f30.py` (new) — FUN_00025f30 capstone disasm

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 39 의 [`ghidra-245fc-and-npc-opcodes-2026-05-17.md`](ghidra-245fc-and-npc-opcodes-2026-05-17.md) 읽기
2. PROGRESS.md 의 task[0xa0c0] subsystem **NPC dialog/quest 시스템** 정정 확인
3. **권장 첫 작업: 2HA** — FUN_0002c6a4 event dispatcher 의 cmp 분기 별 동작 풀이. events 8/c/d/e/f/10 의 공통 handler 0x2c9ca 가 무엇을 하는지가 핵심.
