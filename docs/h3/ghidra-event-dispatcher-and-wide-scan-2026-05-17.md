# Hero3 Ghidra — Round 41 / 2026-05-17 PM-5 (event dispatcher 풀이 + NPC subsystem wide-scan)

> Round 40 (`ghidra-callback-queue-and-npc-query-2026-05-17.md`) 의 후속 — FUN_0002c6a4 event dispatcher 의 정확한 동작 + NPC subsystem 의 task field 사용 분포.

## 한 줄 요약

⭐⭐⭐ **FUN_0002c6a4 event dispatcher 풀이**: 입력 event_id 에서 **3을 빼서 정규화** (valid range [3..18]), 정규화 후 cmp arms 가 events 11/16/17/18/19 를 공통 handler 0x2c9ca 로 분기. 공통 handler = `bl FUN_0002cdb4 → obj.vtable[+0xc] indirect call → clear pending flag`. ⭐⭐ **task_struct[0x290] = "last_event_id" 신규 식별** (모든 path 의 tail 에서 write). ⭐⭐ **FUN_000260ec = stack-local NPC query wrapper** (68B, FUN_00025f30 의 2nd caller). ⭐⭐ **wide-scan**: task[0x9cb8] (callback queue base) **31 sites system-wide**, task[0xa0c0] (NPC subsystem mode) **14 sites** = 광범위 사용. FUN_00041a68 4 callers 4 distinct subsystems = task[0x0a5d] gate 광범위 사용. FUN_0002ae44 2 callers (FUN_00024780, FUN_00024da8) = 일반 함수 (indirect entry 아님).

## 2HA: FUN_0002c6a4 event dispatcher 풀이

### Entry dispatch (0x2c6a4..0x2c6f4)

`tools/recon/disasm_2c6a4_branches.py` capstone disasm:

```
0x2c6a4: 표준 prologue + PIC sl-trampoline:
         push {r4,r5,r7,lr} + mov r7,sl + push {r7} + mov r7,sp
         sub sp, #0x30                        ; 48-byte frame
         ldr r1, [pc, #0x350]; mov sl, r1; add sl, pc  ; setup sl

0x2c6b4: r3 = r0 (event_id input, byte)
0x2c6b6: strb r3, [r7-1]                      ; save event_id byte
0x2c6ba: bl context_getter                    ; r0 = task_struct
0x2c6c4: store task_ptr to [r7-8]
0x2c6d0: ldr r0 = (some field offset); r3 += offset
0x2c6d4: store r3 to [r7-0xc]                 ; save task+offset

0x2c6d6: r3 = (int8)event_id
0x2c6de: r1 = r3 - 3                          ; ⭐ event_id - 3 (offset key)
0x2c6e6: store r1 to [r7-0x1c]                ; save normalized index

0x2c6e8: r3 = [r7-0x1c] = (event_id - 3)
0x2c6f0: cmp r3, #0xf
0x2c6f2: bls 0x2c6f6                          ; if (event_id - 3) <= 15 → dispatch
0x2c6f4: b 0x2ca6c                            ; else: tail/return
```

⭐⭐⭐ **결정적 발견**:
- input r0 = event_id
- 내부 dispatch 는 **(event_id - 3)** 을 사용 → valid range = **event_id ∈ [3..18]**
- FUN_000245fc(r0=0x11=17) 호출 시 (17-3) = 14 → `cmp #0xe beq 0x2c9ca` (공통 handler)

### 9 cmp arms 의 event_id 매핑 (정규화 적용)

| arm 위치 | cmp imm | original event_id | dispatch |
|---|---|---|---|
| 0x2c82e | #0 | 3 | specific path 0x2c848 |
| 0x2c950 | #0xc | 15 | specific path (bne → 0x2c95a, fall-through = event 15) |
| 0x2c96c | #0xf | 18 | ⭐ 공통 handler 0x2c9ca |
| 0x2c982 | #0x10 | 19 | ⭐ 공통 handler 0x2c9ca |
| 0x2c998 | #0x08 | 11 | ⭐ 공통 handler 0x2c9ca |
| 0x2c9ae | #0x0d | 16 | ⭐ 공통 handler 0x2c9ca |
| 0x2c9c4 | #0x0e | 17 | ⭐ 공통 handler 0x2c9ca (FUN_000245fc mode 7) |
| 0x2c9d6 | #0 | (inner null check) | inside common handler |

**공통 handler 분기 events**: 11, 16, 17, 18, 19 (= original event_id) → all use **same vtable method [+0xc]** of a sl-relative object.

### 공통 handler 0x2c9ca (events 11/16/17/18/19)

```
0x2c9ca: bl FUN_0002cdb4                ; ⭐ helper (call obj.vtable[+0x58])
0x2c9ce: r3 = sl-relative literal       ; load global object ptr
0x2c9d4: r3 = *r3 (double deref)
0x2c9d6: cmp r3, #0 beq 0x2ca6c        ; if NULL, return
0x2c9da: r3 = sl + offset                ; load object base
0x2c9e0: r2 = *(object_base)            ; vtable
0x2c9ea: r2 = *(vtable + 0xc)            ; method pointer at +0xc
0x2c9ec: r0 = r3 (object)
0x2c9ee: bl 0xa429c                      ; veneer = bx r2 (indirect call to obj.method0c)
0x2c9f2: r3 = sl-relative pending flag
0x2c9fc: *r2 = 0                          ; clear pending flag
0x2c9fe: b 0x2ca6c                        ; return path
```

### FUN_0002cdb4 helper (84B, 5 callers)

`tools/recon/disasm_2cdb4_helper.py` 결과:

```
PIC sl-trampoline
ldr r3, [sl-relative global ptr]
double deref → cmp 0 → if NULL skip
load obj.vtable, r2 = vtable[+0x58]
bl 0xa429c (= bx r2)                     ; indirect call obj.method58
clear another pending flag
return
```

⭐⭐ **double dispatch 패턴**: 공통 handler 는 `obj.method58()` (via FUN_0002cdb4) → `obj.method0c()` 순서로 두 메서드를 호출. 같은 sl-relative 글로벌 object 사용.

5 callers of FUN_0002cdb4: 0x24496 + 0x244ee (FUN_000245fc 근처) + 0x2b626 (FUN_0002ae44 근처) + 0x2c9ca (event 공통 handler) + 0x2ccae (FUN_0002c6a4 내부 다른 path).

### Tail/return path (0x2ca6c..)

모든 path 의 공통 epilogue:

```
0x2ca6c: r3 = [r7-0xc] = task_field_addr
0x2ca74: r0 = 0xa4 << 2 = 0x290         ; offset literal
0x2ca78: r1 = task + 0x290
0x2ca7a: r3 = [r7-1] = event_id
0x2ca7c: *r1 = r3                        ; ⭐⭐ task[0x290] = event_id (last_event_id 저장)
0x2ca7e: standard cleanup + pop
```

⭐⭐⭐ **task_struct[0x290] = "last_event_id" 저장 슬롯** 신규 식별. 모든 event 호출 후 마지막으로 처리한 event_id 를 여기에 보관.

## 2HB + 2HD: NPC table query callers

### FUN_00025f30 의 2 callers

1. **0x24740 in FUN_000245fc** (Round 40, mode 7 path):
   ```
   bl FUN_00025f30(r0=0x12=18, r1=0xb=11, r2=&task[0xa288], r3=&task[0xa289])
   ```
   결과를 task field 에 영구 저장.

2. **0x26124 in FUN_000260ec** (NEW Round 41, 68B stack-local wrapper):
   ```
   bl FUN_00025f30(r0, r1, r2=&stack_local1, r3=&stack_local2)
   ```
   결과를 stack local 에 임시 저장 (반환값만 사용).

### FUN_000260ec 본문 (68B)

```
push {r4,r7,lr}
sub sp, #0x10                       ; 16-byte locals
store r0, r1 to [r7-4], [r7-8]      ; save args
init [r7-c], [r7-10] to 0           ; zero 2 stack locals
reload r0=arg0, r1=arg1
r2 = &[r7-c], r3 = &[r7-10]         ; pointers to stack locals
bl FUN_00025f30                      ; query
return r0
```

FUN_000260ec 의 2 callers: 0x25690 + 0x28d94 = 두 다른 함수에서 NPC table 을 stack-local 결과로 query.

### NPC table 차원

stride 0x3c4 × 0x3c 는 record SIZE 이지 row/col count 가 아님. 실제 row/col 개수는 task_struct 외부의 데이터 테이블에 저장 (자산 _mp 파일 또는 GVM-allocated 영역). FUN_000245fc 의 mode 7 호출은 row=18, col=11 fixed args 사용 = 특정 NPC 위치를 query (단일 hardcoded query, 동적 dimension 검색이 아님).

## 2HF: task field wide-scan (NPC subsystem 분포)

`tools/recon/scan_npc_subsystem_fields.py` (4-byte aligned literal scan):

| task field | sites | 의미 |
|---|---|---|
| **0x9cb8** | **31** ⭐ | callback queue base ptr (system-wide most active) |
| **0x9cbc** | **29** | callback queue src ptr |
| 0x9cc0 | 18 | callback queue count 1 |
| **0xa0c0** | **14** ⭐ | NPC subsystem mode byte (광범위 사용) |
| 0x9cd4 | 14 | callback queue cursor 1 |
| 0x9cd8 | 13 | callback queue base ptr 2 |
| 0xa288 | 7 | NPC index lo |
| 0x9ccc | 5 | callback queue count 2 |
| 0xa1f6 | 4 | mode 7 gate |
| 0xa289 | 2 | NPC index hi |
| 0x290 | 1 | last_event_id (FUN_0002c6a4 only) |
| 0x02b8 | 1 | callback gate 2 (FUN_000245fc only) |

### 핵심 통찰

- **callback queue cluster (0x9cb8~)** 가 task_struct 에서 가장 활발 (31+29 sites = 60+ pcrel literal occurrences) — 시스템 전반 critical infrastructure
- **task[0xa0c0] = 14 sites** = NPC subsystem mode byte 가 **FUN_000245fc 외부 다른 함수에서도 검사/설정**: 0x24508, 0x245f0, 0x24930, 0x29f48, 0x3a7e0 등
- task[0x0a5d] 는 4-byte aligned literal scan 에서 0 hits (실제로는 FUN_00041a68 의 literal pool 에서 4-aligned 가 아닌 형태로 저장됨)

## 2HG: FUN_00041a68 callers — 4 distinct subsystems

4 BL callers 분포:
- 0x246e8 in **FUN_000245fc** (Round 40, cluster #1 record loop gate)
- 0x42f7c in **FUN_00042f24** +0x58 (별개 함수)
- 0x7b248 in **FUN_0007ae9c** +0x3ac (큰 함수, 0x7Bxxx 영역)
- 0x7c8cc in **FUN_0007c844** +0x88 (별개 함수)

⭐ **task[0x0a5d] gate 는 4 distinct subsystems 에서 사용** = 단순한 NPC subsystem 전용이 아니라 **시스템 전반의 글로벌 gate flag**.

## 2HH: FUN_0002ae44 callers (Round 38 미완 작업)

FUN_0002ae44 = 1404B / 15 arms / 3 ctx + 1 screen_ptr_getter (Round 39 식별). 2 callers:

1. **FUN_00024780** (468B, 1 BL caller from 0x48ae8)
2. **FUN_00024da8** (600B, **6 BL callers** system-wide: 0x249e0, 0x253a8, 0x25462, 0x2af6c, 0x2b43c, 0x7d54a)

둘 다 0x24xxx 시스템 영역 함수 — FUN_000241dc(5번째 indirect entry) 와 FUN_000245fc(6번째 indirect entry) 의 이웃. **Indirect entry 가 아닌 정규 함수**들.

FUN_00024da8 의 6 callers 가 0x24/0x25/0x2A/0x7D 영역으로 흩어져 있음 = **시스템 전반 공유 helper**.

## Round 41 종합 진척

### ✅ 검증 추가

1. **FUN_0002c6a4 event dispatcher 의 정규화 방식 확정**: `internal_key = event_id - 3`, valid range [3..18]
2. **공통 handler 0x2c9ca 동작 풀이**: events 11/16/17/18/19 → `obj.method58()` + `obj.method0c()` double dispatch + clear pending flag
3. **FUN_0002cdb4 helper 풀이** (84B, vtable [+0x58] invoker)
4. **task[0x290] = last_event_id 저장 슬롯 신규 식별**
5. **FUN_000260ec stack-local NPC query wrapper 발견** (68B, 2 callers)
6. **task field wide-scan**: 0x9cb8 cluster heavily used (31+29 sites), 0xa0c0 = 14 sites system-wide
7. **FUN_00041a68 4 callers 분포 = 4 distinct subsystems** (NPC subsystem 전용 아님)
8. **FUN_0002ae44 callers = FUN_00024780, FUN_00024da8** (둘 다 정규 함수, indirect entry 아님)

### 진척률 (Round 41 시점)

- Ghidra 게임 로직 리버싱: ~30~38% → **~32~40%**
- task_struct 모델: ~35% → **~37%** (task[0x290] 신규 + 0x9cb8 cluster 빈도 정밀)
- 전체: ~28~38% → **~30~40%**

### ⭐ 다음 라운드 (42) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2IA** | **공통 handler 0x2c9ca 의 sl-relative 글로벌 object 정체 식별** | object 의 vtable 추적, method [+0xc] / [+0x58] 의 실제 함수 위치 |
| ⭐⭐ **2IB** | event 3 specific path (0x2c848) 본문 — event 3 이 무엇을 의미하는지 | inline disasm |
| ⭐⭐ **2IC** | event 15 specific path (0x2c952) 본문 — cmp #0xc bne 의 fall-through | inline disasm |
| ⭐⭐ **2ID** | FUN_0002cdb4 의 5 callers context 분석 (특히 0x24496/0x244ee in FUN_000245fc 근처) | container 분석 |
| ⭐⭐ **2IE** | FUN_00024780 (468B, 1 BL caller) 본문 — 0x48ae8 caller 와 함께 분석 | inline disasm |
| ⭐⭐ **2IF** | FUN_00024da8 (600B, 6 BL callers) 본문 — 시스템 전반 helper 의 역할 | inline disasm |
| ⭐ **2IG** | 17 callers of FUN_0002c6a4 의 caller 위치 분포 — event trigger 사이트 매핑 | wide analysis |
| ⭐ **2IH** | callback queue stage 1 record sub-struct 구조 (+0x11 외 다른 필드들) | record dump |

### 도구 산출 (Round 41)

- `tools/recon/disasm_2c6a4_branches.py` (new) — event dispatcher 분기 capstone disasm
- `tools/recon/disasm_2cdb4_helper.py` (new) — 84B vtable invoker capstone disasm
- `tools/recon/disasm_260ec.py` (new) — 68B stack-local NPC query wrapper disasm
- `tools/recon/scan_npc_subsystem_fields.py` (new) — task field literal occurrence wide-scan

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 40 의 [`ghidra-callback-queue-and-npc-query-2026-05-17.md`](ghidra-callback-queue-and-npc-query-2026-05-17.md) 읽기
2. PROGRESS.md 의 task field 분포 표 확인 (0x9cb8/0x9cbc/0xa0c0/0x290)
3. **권장 첫 작업: 2IA** — 공통 handler 의 sl-relative object 정체 식별. vtable [+0x58] / [+0xc] 가 무엇인지 풀이하면 event 시스템의 게임 객체가 확정됨.
