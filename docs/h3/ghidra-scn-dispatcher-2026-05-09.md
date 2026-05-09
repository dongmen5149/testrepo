# Ghidra GUI 세션 결과 — 2026-05-09 (§4.4 부분 해독)

> §4.4 NPC behavior dispatcher 위치 + jump table + record 구조 해독.
> 외부 caller (NPC update loop) 는 function pointer indirect call 로 진입해 BL 명령어 자동 추적 한계.

---

## 핵심 발견

### `FUN_0008dcd8` — NPC behavior dispatcher (size ~3KB)

Ghidra 자동 분석에서 함수로 인식되지 않은 큰 함수. raw binary 의 `0x8dcd8` 위치에 `b5f0` (push {r4,r5,r6,r7,lr}) prologue 존재. 사용자가 GUI 에서 `F` 키로 함수 생성 후 분석 가능.

이 함수 안에 두 sub-block 이 있고, Ghidra 가 각각 별도 함수로 잘못 분리:

| 주소 | Ghidra 인식 | 실제 |
|---|---|---|
| `0x8dcd8` | (없음, 사용자 수동 생성 필요) | dispatcher 함수 진짜 entry |
| `0x8e112` | `FUN_0008e112` (사용자가 `scn_dispatch_evt` 로 rename) | dispatcher 함수의 sub-block 1 |
| `0x8e89e` | `FUN_0008e89e` | dispatcher 함수의 sub-block 2 (jump table call site) |

두 sub-block 은 서로 BL 호출만 함 (closed loop):
- `0x8e89a` → BL → `0x8e112`
- `0x8e12a` → BL → `0x8e89e`

### `FUN_0008b2e8` — Sister dispatcher (size ~9.6KB)

같은 패턴의 두 번째 dispatcher. `0x8b2e8` prologue + `0x8b726` 안에 jump table 호출. **다른 jump table** 사용 (`DAT_0008c290` offset). 추정: NPC behavior 외 다른 entity (battle units, UI state, dialog) 의 dispatcher.

### Jump table 1 (FUN_0008dcd8 dispatcher용)

알려진 식별 데이터:
- GOT base = `0x000b2c40`
- `DAT_0008ec74 = 0xFFFF9028` (signed -0x6FD8)
- jump_table_base = `0xb2c40 + 0xFFFF9028 = 0x000abc68` (file offset 1:1)

19개 4-byte entry 디코드 결과 (7 distinct targets):

| opcode | handler | 비고 |
|---|---|---|
| 0x00 ~ 0x0c (13개) | `0x95bfe` | 공통 default handler |
| 0x0d | `0x960e8` | special 1 |
| 0x0e | `0x962f4` | special 2 |
| 0x0f | `0x9651c` | special 3 |
| 0x10 | `0x9685c` | special 4 |
| 0x11 | `0x96aa6` | special 5 |
| 0x12 | `0x96bf8` | special 6 |

⚠ Handler 주소들이 **함수 시작이 아님** (push prologue 없음). raw binary 디스어셈블 결과 일반 instruction (sub/ldr/str). 즉 **하나의 큰 dispatch 함수 안의 case label**. Ghidra 가 jump table 자동 복구 실패로 각 case 영역을 작은 stub 함수로 잘못 분리 (`FUN_00095a64` 같은 1-line 함수들).

### NPC slot record 구조

dispatcher 가 처리하는 record:
- stride: `0x3c4` (964 bytes per slot) × `0x3c` (60 bytes per sub-slot)
- `+0x3b3` byte = 활성 flag
- `+0x3b6` short = behavior opcode (0~0x12)
- `+0x3b8` short = 인자

근거 (`FUN_0008e89e` 디컴파일):
```c
*(undefined2 *)(unaff_r7 + -0xc4) =
     *(undefined2 *)(((int)*(char *)(unaff_r7 + -0x35) * (int)*(char *)(unaff_r7 + -0x4d) +
                      (int)*(char *)(unaff_r7 + -0x4e)) * 4 + *(int *)(unaff_r7 + -0xc0));
// ...
if (*(char *)(*(short *)(unaff_r7 + -0xc4) * 0x3c4 + *(short *)(unaff_r7 + -0xc6) * 0x3c +
              *(int *)(unaff_r7 + -0x5c) + 0x3b3) == '\0') { FUN_0008ff18(); }  // flag check
*(undefined2 *)(unaff_r7 + -200) =
     *(undefined2 *)(*(short *)(unaff_r7 + -0xc4) * 0x3c4 + ... + 0x3b6);  // opcode
*(undefined2 *)(unaff_r7 + -0xca) =
     *(undefined2 *)(*(short *)(unaff_r7 + -0xc4) * 0x3c4 + ... + 0x3b8);  // arg
*(int *)(DAT_0008ec70 + unaff_r7) = (int)*(short *)(unaff_r7 + -200);
if (0x12 < *(uint *)(DAT_0008ec70 + unaff_r7)) { FUN_0008fe30(); }
/* WARNING: Could not recover jumptable at 0x0008ec24. Too many branches */
(*(code *)((int)&DAT_000b2c40 + *(int *)((int)&DAT_000b2c40 + opcode * 4 + DAT_0008ec74)
          + DAT_0008ec74))();
```

---

## Caller chain 한계

### 시도 + 결과

| 방법 | 결과 |
|---|---|
| Ghidra Function Call Trees Incoming | `FUN_0008dcd8` / `FUN_0008b2e8` 모두 0건 |
| 절대 주소 binary search (0x8dcd8, 0x8e112, 0x8e89e) | 0건 |
| GOT-relative offset search (target − 0xb2c40) | 0건 |
| Thumb-2 BL 명령어 디코드 (binary 전체) | dispatcher 내부 self-loop 만 발견. 외부 BL 0건 |

### 근본 원인 추정

dispatcher 호출자가 **function pointer indirect call** 만 사용. 호출 경로:
```c
typedef void (*NpcUpdateFn)(void);
NpcUpdateFn npc_update_fn = ... ;  // GOT 또는 RAM data 영역에 저장
// main loop:
npc_update_fn();  // → FUN_0008dcd8 / 0008b2e8
```

또는 NPC state machine 의 함수 포인터 멤버. 이런 경우 binary 안 어떤 데이터 영역 (GOT 또는 .data) 에 함수 주소가 들어있어야 하는데, 절대/상대 모두 매칭 0건 → 호출자가 RAM 에서 동적으로 세팅하는 형태.

---

## 다음 시도 방향 (다음 세션)

### A) Handler 영역 디컴파일 (사용자 GUI, 30~60분)

7 distinct handler (`0x95bfe` ~ `0x96bf8`) 의 의미를 파악.

**방법**:
1. `G` → `0x95bfe` 점프
2. Listing 에서 그 주변 영역 (~`0x96c00` 까지) 우클릭 → `Clear Code Bytes` (현재 stub 함수들 제거)
3. `FUN_0008e89e` 안의 jump table 호출 line 우클릭 → **`Override Signature`** 또는 **`Set Switch Statement`**
4. 19 case + 7 unique target 명시 → Ghidra 재분석 → handler 본문 디컴파일

### B) Caller 추적 — RAM 동적 셋업 위치 찾기

dispatcher 함수 주소를 변수에 저장하는 코드 찾기. 가능한 방법:
1. Ghidra Script (Python) — binary 안 모든 `mov rN, #target` instruction 검색
2. `Search → For Scalars` → `0x8dcd9` 검색 (Thumb LSB+1 형태로 mov 명령어에 인코딩됨)

### C) §4.2 NPC 좌표 가설 검증 (자동 가능)

NPC slot record (0x3c4 stride) 안의 다른 offset 에서 좌표 (x, y short) 찾기. _mp 또는 _scn 데이터 안에 같은 record 형태가 있는지 확인.

### D) 진짜 _scn byte stream parser 찾기

이 dispatcher 는 NPC slot record (short opcode + arg) 처리. 그 record 가 어떻게 만들어지는지 = _scn byte stream 을 record 로 변환하는 parser. _scn 데이터에서 byte 단위 opcode → slot 의 +0x3b6 short opcode 매핑이 있을 것.

---

## 자동화 도구 (이번 세션 추가)

| 도구 | 목적 |
|---|---|
| `tools/recon/find_dispatcher_v3.py` | 1,470 함수 통계로 dispatcher 후보 추출 (UNRECOVERED_JUMPTABLE / switch / chain compare) |
| `tools/recon/extract_candidate_funcs.py` | all_decompiled.c 에서 후보 함수 본문 추출 |
| `tools/recon/rank_size_top.py` | Ghidra Function 표 size sort 결과 우선순위 정렬 |
| `tools/recon/decode_scn_jumptable.py` | raw binary 에서 jump table 19 entry 디코드 |
| `tools/recon/check_handler_prologues.py` | handler 주소가 함수 시작인지 ARM Thumb prologue 검증 |
| `tools/recon/find_real_func_start.py` | 영역에서 push prologue 위치 스캔 → 진짜 함수 boundary |
| `tools/recon/find_dispatcher_caller.py` | 절대/GOT-relative 주소 패턴 검색 |
| `tools/recon/find_bl_callers.py` | Thumb-2 BL 명령어 디코드해서 caller 검색 |

---

## 함수 정리 표 (참고용 — 누적)

| 주소 | 정체 | §섹션 | 발견 일자 |
|---|---|---|---|
| `0x10ea4` | BM mini-header parser | §4.1 | 2026-05-06 |
| `0x10fe4` | BM 0x0c/0x0b dense palette decoder | §4.1 | 2026-05-06 |
| `0x14e68` | HD/blending sprite drawer | §4.1 후속 | 2026-05-08 |
| `0x158c6` | sprite transform mode 2 | §4.1 후속 | 2026-05-08 |
| `0x15a2c` | sprite transform mode 1 | §4.1 후속 | 2026-05-08 |
| `0x15b8c` | BM 0x0b transform-aware drawer | §4.1 후속 | 2026-05-08 |
| `0x182c4` | sprite transform sub | §4.1 후속 | 2026-05-08 |
| `0x1a568` | sprite rotation dispatcher (90/180/270°) | §4.1 후속 | 2026-05-08 |
| `0x33016` | UI menu drawer (calls boss decoder) | renderer | 2026-05-08 |
| `0x410b0` | sprite drawer wrapper | renderer | 2026-05-08 |
| `0x41172` | animation tick handler (frame_idx++) | §4.3 | 2026-05-08 |
| `0x4ac40` | virtual draw + boss decoder | renderer | 2026-05-08 |
| `0x9889c` | animation slot data getter | §4.3 | 2026-05-08 |
| `0x98ef8` | boss/enemy cif cell decoder | §4.3 | 2026-05-08 |
| `0x4ad10` | tail-call panic (Ghidra noreturn) | runtime | 2026-05-08 |
| **`0x8b2e8`** | **NPC behavior dispatcher 2 (sister)** | **§4.4 ⭐ NEW** | **2026-05-09** |
| **`0x8dcd8`** | **NPC behavior dispatcher 1 (main)** | **§4.4 ⭐ NEW** | **2026-05-09** |
| **`0x8e112`** | dispatcher 1 의 sub-block 1 (rename: `scn_dispatch_evt`) | §4.4 | 2026-05-09 |
| **`0x8e89e`** | dispatcher 1 의 sub-block 2 (jump table call site) | §4.4 | 2026-05-09 |
| `0xa6888` | `onEventMessageOkKey()` 디버그 문자열 | §4.4 진입점 (xref 0건) | 2026-05-08 |
| `0xa6ad8` | `eventManager` 디버그 문자열 | §4.4 진입점 (xref 0건) | 2026-05-08 |

⭐ = 이번 세션 발견.
