# §4.4 후속 — 2026-05-10 PM-7 세션 (task pointer + arm handlers + GOT slot 분석)

> 2026-05-10 PM-6 의 context_getter 정정 후속.
> 자동 우선순위 **2U + 2T + 2V** 일괄 진행.
> 결과: 0xb3084 슬롯 writer 부재 확인 (GVM 외부 주입), task pointer wrapper API 클러스터 식별, FUN_0009b252 의 type-tag reader 가설 약화.

---

## 1. 2U — 0xb3084 슬롯 writer 추적 (도구 `find_global_slot_writers.py`)

### 1A. binary 전체 검색 결과

```
=== tracking writes to slot at GOT+0x444 (= 0x000b3084) ===
=== walking 735760 bytes (350955 instructions) ===

direct [sl, #0x444] write sites: 0   ⚠
direct [sl, #0x444] read sites:  0   ⚠
PC-rel LDR loading literal 0x444: 7 sites (모두 0x4ad10-0x4ae10 클러스터)
movw Rd, #0x444: 0 sites
two-step access: writes 0, reads 0
```

### 1B. ⭐⭐ 결론 — GVM firmware 외부 주입

- **direct write 0건** = 게임 binary 안에 0xb3084 슬롯에 쓰는 instruction 없음
- 7 PC-rel LDR (literal 0x444) 사이트 모두 `FUN_0004ad10` ~ `FUN_0004ae10` 의 작은 클러스터 안
- → **GVM firmware 가 게임 binary 외부에서 슬롯을 셋팅**, 게임은 read-only
- PM-1 의 "함수 포인터 hex 검색 0건 → 동적 주입" 발견과 일관 — GVM 이 task pointer + 함수 포인터 모두 동적 주입

### 1C. 0x4ad10-0x4af10 클러스터 = task pointer wrapper API

해당 영역의 11+ 함수가 모두 GOT+0x444 패턴 사용:

```c
// FUN_0004ad10: task_ptr getter
return *(GOT_BASE + 0x444);  // 단일 글로벌 read

// FUN_0004ad34: task setup
ldr r3, [r3]; ldr r3, [r3];   // double indirect: 0xb3084 → task_ptr → task_struct
load fields, call sub-handlers...

// FUN_0004ae10: parameterized task action
if (param_1 == 2) call FUN_00048b90(task_ptr, param_2)
else if (param_1 == 3) call FUN_00048bc4(task_ptr, param_2)

// FUN_0004ae7c: task struct field setter
*(task_struct + 8) = param_2;
*(task_struct + 0x18) = param_1;
```

→ **단일 글로벌 (0xb3084) 가 task pointer**. 이 클러스터의 함수들이 task struct 의 다양한 필드 액세스 + 액션 처리 wrapper 역할.

`ldr r3, [r3]; ldr r3, [r3]` 패턴 = **double indirection** (`0xb3084 → task_ptr → task_struct`). 즉 0xb3084 는 "pointer to pointer", task pointer 가 또 다른 메모리에서 변경되어도 슬롯 재로드 없이 추적.

---

## 2. 2T — FUN_0009b252 arm-by-arm 분석 (도구 `analyze_arm_handlers.py`)

### 2A. arm 분포 — type-5 reader 가설 약화 ⚠

86+ cmp arms 의 BL target 매핑 결과:

| arm imm | total BLs | 핵심 핸들러 |
|---|---|---|
| **cmp #0x06** | **23** | 7x FUN_000439a0, 6x FUN_00047a14, 4x task_ptr_getter |
| cmp #0x00 | 23 | 13x task_ptr_getter (null check 후 task 가져옴) |
| cmp #0x01 | 16 | 6x task_ptr, 4x FUN_000439a0, 3x FUN_00047a14 |
| cmp #0x02 | 9 | 5x task_ptr, 2x FUN_0009a14e |
| cmp #0x07 | 8 | 다양한 핸들러 |
| cmp #0x04 | 7 | 2x FUN_0009a148 |
| cmp #0x09 | 6 | 4x task_ptr, 2x FUN_0007d31c |
| **cmp #0x05** | **3** | ❗ 매우 적음 (type-5 dispatch 부재) |
| cmp #0x14 | 1 | 1x task_ptr |

### 2B. 결론 — FUN_0009b252 ≠ type-5 reader

- **cmp #0x05 (type-5) arm 단 3 BL** — type-5 가 dominant 인 큐 record 인데 이 함수에서는 거의 처리 안 함
- 가장 무거운 처리는 **cmp #0x06 (23 BLs)** — 즉 type-6 또는 다른 의미의 입력값 6 처리
- → FUN_0009b252 는 **type-5 reader 가 아니라 다른 sub-system 의 광범위 dispatcher**

### 2C. 핵심 sub-handlers 발견 ⭐

| handler | usage in FUN_0009b252 | 이전 분석 |
|---|---|---|
| **FUN_000439a0** | 7x cmp#6, 4x cmp#1, 2x cmp#3, 1x cmp#7, 1x cmp#10 | top stub #7 (37 callers, 188 bytes) — popular helper |
| **FUN_00047a14** | 6x cmp#6, 3x cmp#1, 2x cmp#7, 1x cmp#2/3/4/5/10 | (stub 클러스터 안) |
| FUN_0009a14e | 7x | local helper |
| FUN_000442e4 | 5x | local helper |
| FUN_0007d31c | 4x cmp#9 | top stub (PM-3) |

→ **FUN_000439a0 와 FUN_00047a14 가 가장 광범위하게 재사용되는 sub-handler**. cmp #0x06 처리에 둘 다 7+6=13x 호출. 이 두 함수 본문 분석이 다음 큰 진척.

### 2D. type tag reader 풀이 진척

- ❌ FUN_0009b252 는 type tag reader 가 아님 (type-5 cmp 거의 없음)
- ❌ binary 전체에서 queue-reader → cmp-#type 직접 패턴 단 2건 (PM-6)
- → **단일 type tag reader 함수는 존재하지 않을 가능성**. 큐 reader 는 분산된 구조 (각 sub-system 이 자기 type 만 처리) 또는 jump table 방식 (capstone cmp 추적이 부족).

---

## 3. 2V — FUN_00026a80 / FUN_000818f0 본문 분석

### 3A. FUN_00026a80 (8.4KB main subsystem router)

```
size=8414 bytes (3993 instr)
arms: 다양 (cmp #0x12, #0x16, #0x11 등 큰 값들 등장)
interesting BL: 7 (context_getter 7 + sound_trigger 2 + memset 1)
PC-rel LDR: 177 (got_slot 150 ⭐ + neg_signed 8 + medium_int 9)
top BL (PM-3): 0x294a2 63x, 0x4b134 42x  ← non-PIC helpers
```

→ **150 GOT slot offsets 가 압도적** (177 중 85%). 매우 다양한 글로벌 액세스. helper 호출은 다른 함수들 (FUN_000294a2, FUN_0004b134) 위주 — 이들이 main_subsystem 의 inner workers.

→ **subsystem router 가설 유지**: 51 distinct BL targets (PM-3) + 광범위 글로벌 액세스 = 다양한 sub-system 진입점.

### 3B. FUN_000818f0 (5.4KB entity update loop)

```
size=5380 bytes (2396 instr)
interesting BL: 53 (context_getter 53!)
PC-rel LDR: 244 (got_slot 225 ⭐⭐ + neg_signed 14)
top BL (PM-3): 0x4ad10 (task_ptr) 212x, 0x82df4 42x, 0x3d5d0 (sound) 12x
```

### 3C. ⭐ system-wide GOT slot offsets 발견

FUN_000818f0 의 r0 backtrace 에서 반복 등장하는 슬롯 offsets:

| GOT slot | 등장 횟수 | 다른 함수에서도 |
|---|---|---|
| `0x9c70` | 다수 | default_key_handler, FUN_0009b252 (cmp #6 핸들러) |
| `0x9c71` | 다수 | 동일 |
| `0xac78` | 다수 | 새로 발견 |
| `0x9c84` | (이전 PM-6) | default_key_handler |

→ **system-wide global state slots**. GOT base + 0x9c70/0x9c71/0x9c84/0xac78 = 게임의 다른 핵심 글로벌 (task_ptr 의 0x444 외에도).

각 슬롯의 의미:
- `0xb2c40 + 0x444 = 0xb3084` ✅ task_ptr (PM-6 확인)
- `0xb2c40 + 0x9c70 = 0xbc8b0` — 추가 글로벌 1
- `0xb2c40 + 0x9c71 = 0xbc8b1` — 추가 글로벌 2 (1바이트 옆)
- `0xb2c40 + 0x9c84 = 0xbc8c4` — 추가 글로벌 3
- `0xb2c40 + 0xac78 = 0xbd8b8` — 추가 글로벌 4

이들은 모두 GOT 안의 인접 영역에 있음. 향후 이들 슬롯도 같은 도구 (`find_global_slot_writers.py --slot-offset`) 로 추적 가능.

---

## 4. 신규 도구 / 산출물

| 도구 | 산출물 |
|---|---|
| [find_global_slot_writers.py](../../tools/recon/find_global_slot_writers.py) | `work/h3/global_slot_0x444_writers.json` |
| [analyze_arm_handlers.py](../../tools/recon/analyze_arm_handlers.py) | `work/h3/type_tag_reader_arms.json` |
| (기존) `disasm_subsystem_func.py` 재사용 | `subsystem_router_disasm.json`, `entity_update_loop_disasm.json` |

---

## 5. 종합 — 게임 글로벌 state 구조 (가설)

### 5A. GOT 안의 핵심 슬롯들

```
0xb2c40 (GOT base — 사용자 GUI 검증)
  ├ +0x444 (= 0xb3084) → task_ptr → task_struct  (PM-6 확정)
  ├ +0x9c70 (= 0xbc8b0) → 글로벌 슬롯 (의미 미식별)
  ├ +0x9c71 (= 0xbc8b1) → 인접 글로벌 (1바이트 옆 — flag?)
  ├ +0x9c84 (= 0xbc8c4) → 글로벌
  └ +0xac78 (= 0xbd8b8) → 글로벌
```

### 5B. task pointer 액세스 패턴

```
caller → bl FUN_0004ad10        ; task_ptr_getter
       ↓ r0 = *0xb3084 (task_ptr_ptr)
       ↓ optionally double-deref: ldr r3, [r0]; ldr r3, [r3]
       ↓ task_struct fields (offset 0x8, 0x18, 0x44, 0x54 등)
```

→ task_struct 의 필드 offsets (8, 0x18, 0x44, 0x54, ...) 는 게임 state 의 다양한 카테고리 (current scene, current state machine, key buffer, 등).

### 5C. 큐 record protocol 와의 관계

이전 PM-5 의 큐 record protocol (type-5 dominant) 는 **task_struct 와는 별개의 시스템** 으로 보임:
- 큐는 byte stream serialization (FUN_0007e150 buffer)
- task_struct 는 직접 메모리 접근
- 두 system 의 연결고리: FUN_00057394 / FUN_00064048 등 큐 writer 가 task_ptr 도 사용 (양쪽 액세스)

---

## 6. 다음 세션 권장

### 자동 진척 가능

- ⭐ **FUN_000439a0 (188 bytes, 37 callers) 본문 분석** — type-6 처리의 핵심 sub-handler. PM-3 에서 "popular helper" 였지만 본문 미분석.
- ⭐ **FUN_00047a14 본문 분석** — 또 다른 핵심 sub-handler.
- **다른 GOT slots (0x9c70, 0x9c84, 0xac78) writer 추적** — `find_global_slot_writers.py --slot-offset 0x9c70` 로 검색. GVM 외부 주입 vs 게임 내부 셋팅 구분.
- **task_struct 필드 매핑** — 0x4ad34 클러스터의 모든 함수 본문 분석으로 (offset → 의미) 매핑.

### 사용자 블로커

- SMAF→OGG (33 BGM/SFX)
- 대사 LLM 번역 (~$0.66, 9,741 unique 대사)

---

## 7. 핵심 교훈

1. **direct write 0건 = 외부 주입 신호**: 게임 binary 안에 슬롯에 쓰는 instruction 0개 = GVM firmware 가 외부에서 셋팅. PIC 환경의 표준 패턴.
2. **wrapper API cluster 식별의 가치**: 단일 슬롯 (0xb3084) 액세스가 11+ 함수 클러스터 (0x4ad10-0x4af10) 에 wrapping 되어 있음. 이 클러스터 본문 분석 = task struct 필드 매핑.
3. **arm-by-arm BL 매핑이 dispatcher 정체 식별의 결정적 도구**: cmp #0x05 가 단 3 BL → type-5 reader 가설 즉시 약화. 단순 arm 카운트보다 BL distribution 이 더 정확한 지표.
4. **system-wide global slots 발견**: 0x9c70/0x9c71/0x9c84/0xac78 같은 작은 그룹의 GOT 슬롯들이 여러 함수에 걸쳐 등장 = 게임의 핵심 state 위치들. 각 슬롯 의미 파악이 게임 구조 풀이의 다음 큰 진척.
5. **handler reuse 패턴**: FUN_000439a0 / FUN_00047a14 같은 small popular helper 가 다양한 dispatcher arm 에서 재사용 = 공통 sub-handler. 이런 함수 본문 분석이 multiple sub-system 풀이를 한 번에 진척.
