# §4.4 후속 — 2026-05-10 PM-3 세션 (402 PIC stub 우선순위 분류 + 큐 caller 매핑 + top 15 분석)

> 2026-05-10 PM-2 의 **"Ghidra 가 1470 함수 중 402 (~27%) 를 PIC 디컴파일 실패"** 발견 후속.
> 자동 우선순위 **2I (stub ranking)** + **2J (큐 API caller 매핑)** 일괄 진행.
> 결과: 주요 stub 함수의 정체 다수 식별 + 큐 lifecycle owner 발견.

---

## 1. 2I — 402 stub 우선순위 ranking (도구 `rank_pic_stubs.py`)

### 1A. 산출 방식

각 stub 함수에 대해:
- **size** = 다음 함수 entry 까지 거리 (raw bytes)
- **bl_count** = capstone walk_with_skip 으로 함수 내부 BL 개수 카운트
- **caller_count** = binary 전체 BL 디스어셈블 → target ∈ {addr, addr+1} 카운트 (Thumb bit 양쪽)
- **score** = `caller_count*5 + bl_count*1 + log2(size+1)*2`

### 1B. 통계

| metric | min | median | max |
|---|---|---|---|
| size | 16 | 380 | 10134 |
| bl_count | 1 | 5 | 287 |
| caller_count | 0 | 1 | 58 |

- **0 direct callers (PIC-indirect-only)**: 39 / 402 → 전부 함수 포인터로만 진입
- 1 direct caller: 다수 — 단일 호출자가 (대부분 stub 임) → 호출 chain 자체가 PIC-indirect 끊김

### 1C. 카테고리별 top 함수

**top 5 by SIZE (대형 미분석 함수)**:

| addr | name | size | BLs | callers | 추정 |
|---|---|---|---|---|---|
| 0x00006334 | FUN_00006334 | 10134 | 187 | 1 | **MASSIVE state machine** (cmp 99/17arms, +0x18 read 75x → 배열 iterating) |
| 0x00060ab4 | FUN_00060ab4 | 8808 | 155 | 1 | ✅ page 2 UI rendering function (PM-2 분석 완료) |
| 0x00026a80 | FUN_00026a80 | 8414 | 209 | 1 | **subsystem router** (51 distinct BL, 10 cmp arms) |
| 0x000031dc | FUN_000031dc | 6726 | 131 | 1 | state machine (cmp 47/15arms, 0x4c22 30x BL) |
| 0x000818f0 | FUN_000818f0 | 5380 | 287 | 1 | state machine (212x context getter, +0x002 reads 13x → cycle iteration) |

**top 5 by CALLER_COUNT (인기 helper 들)**:

| addr | name | callers | size | 분석 결과 |
|---|---|---|---|---|
| 0x00075b98 | FUN_00075b98 | 58 | 324 | sequential helper (4 BL 만, memset 호출 1회) — **"init/reset buffer" 추정** |
| 0x00040ea0 | FUN_00040ea0 | 38 | 68 | tiny micro-helper (3 BL, state read 0x180/0x2d0) |
| 0x0003d5d0 | FUN_0003d5d0 | 37 | 4288 | **sound subsystem dispatcher** (sound_trigger 21x, cmp 22 arms) |
| 0x000439a0 | FUN_000439a0 | 37 | 188 | sequential helper (state writes/reads 0x01c~0x06c, struct 셋업 추정) |
| 0x0008578c | FUN_0008578c | 34 | 24 | trivial pass-through (1 BL = context getter only) |
| 0x00040ddc | FUN_00040ddc | 32 | 32 | trivial helper (2 BL) |
| 0x00075d44 | FUN_00075d44 | 29 | 1224 | (분석 미진행) |

**top 5 by BL_COUNT (heavy 호출 함수)**:

| addr | name | BLs | size | 추정 |
|---|---|---|---|---|
| 0x000818f0 | FUN_000818f0 | 287 | 5380 | 212x context getter — **per-entity update loop** 후보 |
| 0x00026a80 | FUN_00026a80 | 209 | 8414 | subsystem router |
| 0x00006334 | FUN_00006334 | 187 | 10134 | MASSIVE state machine |
| 0x00060ab4 | FUN_00060ab4 | 155 | 8808 | ✅ page 2 UI |
| 0x0003add0 | FUN_0003add0 | 137 | 3146 | **PIC-indirect-only** (0 direct callers, 109x context getter) |

---

## 2. 2J — GVM 이벤트 큐 API caller 매핑 (도구 `find_queue_callers.py`)

### 2A. 큐 API 사용량 종합

10개 큐 API 함수에 대해 binary 전체 BL 추적:

| target | role | 호출 횟수 |
|---|---|---|
| `0x0007e150` byte_append | producer | **67** |
| `0x0007e890` flush_swap | lifecycle | **27** |
| `0x0007e4c4` set_byte | producer | 15 |
| `0x0007e184` memcpy_read | consumer | 9 |
| `0x0007e63c` consumer_? | consumer | 8 |
| `0x0007e1c4` u32_append | producer | 5 |
| `0x0007e0e4` alloc_buffer | lifecycle | 4 |
| `0x0007e7ac` init_or_helper | lifecycle | 2 |
| `0x0007ea98` buffer_status | consumer | 1 |

**총 138 BL sites, 31 distinct caller functions**.

### 2B. ⭐ 큐 lifecycle owner — `FUN_00057394`

| caller | calls | 분포 |
|---|---|---|
| **FUN_00057394** | 29 | byte_append:19, **flush_swap:7**, memcpy_read:2, u32_append:1 |
| FUN_00056bf8 | 18 | byte_append:10, flush_swap:4, memcpy_read:3, u32_append:1 |
| FUN_00064048 | 16 | byte_append:10, flush_swap:4, memcpy_read:2 |
| FUN_000630e8 | 14 | byte_append:9, flush_swap:4, memcpy_read:1 |

→ 4 함수가 큐 호출의 ~70% 사용 (29+18+16+14 = 77 / 138).

### 2C. FUN_00064048 = 큐 사용자 확정

PM-2 에서 default key handler 의 정체를 "큐 직렬화" 로 추정한 것이 caller 매핑으로 **확정**됨. 16 큐 호출 (10 byte_append + 4 flush + 2 memcpy_read) — producer + lifecycle 동시.

---

## 3. Top 15 stub 함수 정체 추정 (도구 `analyze_top_stubs.py`)

각 stub 의 BL 통계 + cmp 분포 + state offset access 패턴 + 큐/UI helper 호출 여부로 자동 카테고리화.

### 3A. ⭐ `FUN_00057394` (3.5KB) — **큐 lifecycle owner / display list builder**

```
size=3550 BL=116/19d   queue: byte_append:19, flush_swap:7, memcpy_read:2, u32_append:1
ui: graphics_primitive(0x9f624):20, memset_like(0x9fb78):10
top BL: 0x9f624(20) 0x7e150(19) 0x75b98(13) 0x4ad10(11) 0x9fb78(10)
cmp: 12 total / 2 arms (state machine 아님)
```
- **graphics primitive 20x + queue byte append 19x + memset 10x + flush 7x** 패턴
- → **render command buffer / display list builder** 추정
  - 매 frame 그래픽 op 실행 + op description byte queue 직렬화 + 끝에 flush
  - 모바일 게임의 dirty rectangle 추적 / 더블 버퍼링 구현 후보
- state offsets 작음 (0x002~0x00c) → 작은 worker 구조체 사용

### 3B. `FUN_00056bf8` (836B) — **queue read+write (save/load 후보)**

```
size=836 BL=32/13d   queue: byte_append:10, flush_swap:4, memcpy_read:3, u32_append:1
cmp: 10 total / 7 arms (가벼운 state machine)
```
- 큐의 read + write 둘 다 사용 → **save/load** 또는 **bidirectional codec**
- 7개 cmp arm = 작은 분기 — save/load mode 토글 가능성

### 3C. `FUN_000630e8` (3.9KB) — **command processor**

```
size=3888 BL=99/16d   queue: byte_append:9, flush_swap:4, memcpy_read:1
cmp: 41 total / 12 arms (state machine)
top BL: 0x4ad10(37), 0x75b98(19), 0x7e150(9), 0x64018(8)
state reads: +0x002(11), +0x001(10), +0x004(7), +0x008(6), +0x0a0(4)
```
- 12 arms state machine + queue 사용 + FUN_00064018 호출 (default key handler 0x64048 인접!)
- → **명령/이벤트 처리 + 큐 직렬화** 함수. 0x64018 호출은 default_key_handler 이웃 함수와 페어링 시사

### 3D. ⭐⭐ `FUN_00006334` (10KB) — **MASSIVE state machine (main loop 후보)**

```
size=10134 BL=187/30d   ← 30 distinct callees
cmp: 99 total / 17 arms ← STRONG state machine
state writes: +0x004:25, +0x00c:23, +0x008:16, +0x010:11, +0x005:6
state reads:  +0x018:75, +0x00c:42, +0x004:23, +0x01c:22, +0x020:21
top BL: 0x8aca(70) 0x80664(22) 0x7d258(14) 0x48eec(9) 0x8ad8(8)
```
- **17 cmp arms + 99 cmp 총** = 강한 dispatcher / state machine
- **+0x018 75 reads** = 배열/리스트 iterating (4-byte stride 추정)
- **+0x004~+0x020 영역 집중 access** = 큰 구조체의 head 부분 자주 접근
- 70x BL to 0x08aca → 내부 helper 반복 호출 (loop body)
- → **per-frame entity list iteration loop** 또는 **main game loop dispatcher** 후보

### 3E. `FUN_00026a80` (8.4KB) — **subsystem router**

```
size=8414 BL=209/51d   ← 51 distinct callees (다양)
cmp: 45 total / 10 arms
state writes: 0x03c:6, 0x004:4, 0x050:4, 0x048:2
state reads: 0x03c:7, 0x038:7, 0x010:6, 0x012:6, 0x2d0:6
top BL: 0x294a2(63) 0x4b134(42) 0x7d258(8) 0x4ad10(7)
```
- **51 distinct BL targets** (가장 많음) → 광범위한 sub-system 호출
- 0x294a2 BL 63x = 내부 helper 매우 빈번 (주요 helper 후보)
- → **main subsystem router** 후보 (NPC update / map load / battle init 등 다양한 호출)

### 3F. `FUN_000818f0` (5.4KB, 287 BLs) — **per-entity update loop**

```
size=5380 BL=287/17d   ← 287 BLs but only 17 distinct → tight inner loop
cmp: 41 total / 10 arms
state writes: +0x002:8 (only)
state reads: +0x002:13, +0x1c0:3, +0x0a0:2, +0x00c:2, +0x058:1
top BL: 0x4ad10(212) 0x82df4(42) 0x3d5d0(12) 0x92bd0(4)
```
- **212x context getter (74%)** + **42x to 0x82df4** + 12x to FUN_0003d5d0 (sound dispatcher!)
- 매우 좁은 BL diversity (17) + 높은 호출 횟수 → **iteration loop**
- state +0x002 읽기/쓰기에 집중 → 단일 필드 cycle 변수
- → **per-entity update with sound effects** 후보 (NPC tick, animation step, etc.)

### 3G. `FUN_0003d5d0` (4.3KB, 37 callers) — **sound subsystem dispatcher**

```
size=4288 BL=99/9d   callers=37
ui: sound_trigger(0x99764):21
cmp: 37 total / 22 arms ← VERY strong state machine
state reads: +0x054:20, +0x004:13, +0x028:2, +0x0a0:2
top BL: 0x4ad10(22) 0x99764(21) 0x9fd64(17) 0xa42a4(11)
```
- **22 cmp arms + 21 sound triggers** + 37 callers = 게임 전반에서 호출되는 큰 sound dispatcher
- state +0x054 읽기 20x → sound state field
- → **sound 큰 사운드 시스템 진입점** (BGM 변경, SFX 큐, 페이드인/아웃 등)

### 3H. `FUN_00075b98` (324B, 58 callers) — **init/reset helper**

```
size=324 BL=4/4d   callers=58
ui: memset_like(0x9fb78):1
cmp: 2 total / 1 arm (no state machine)
state writes: +0x004:2, +0x040:1
top BL: 0x4ad10(1), 0x9fb78(1), 0xa42a4(1), 0xa42a0(1)
```
- 가장 인기 helper (58 callers) + memset 1회 호출 + 2 veneer indirect call
- 158 instr 하지만 BL 적음 → 인라인 처리 많은 **init/reset routine**
- → **"init/reset object state" 공통 helper** 추정

### 3I. PIC-indirect-only — `FUN_0003add0` (3.1KB, 0 callers)

```
size=3146 BL=137/16d   callers=0   ← PIC-indirect 만으로 진입
cmp: 30 total / 5 arms
state reads: +0x1e8:4, +0x1dc:4, +0x1e4:3, +0x1e0:3, +0x1f0:3
top BL: 0x4ad10(109) 0x3ba1a(7) 0x47aa8(5)
```
- **direct caller 0건** + 109x context getter (80%)
- state +0x1dc~+0x1f0 영역 (16-byte struct) 집중 access
- → **PIC-indirect 으로만 호출되는 frame callback** 일 가능성. 5 arms state machine.

---

## 4. 정체 식별 종합 표

| addr | name | 정체 추정 | 신뢰도 |
|---|---|---|---|
| 0x00057394 | FUN_00057394 | render command buffer / display list builder | 높음 (graphics+queue 패턴) |
| 0x00056bf8 | FUN_00056bf8 | save/load codec | 중간 |
| 0x000630e8 | FUN_000630e8 | command/event processor + queue | 중간 |
| 0x00006334 | FUN_00006334 | main game loop dispatcher / entity list iterator | 중간 (size+pattern) |
| 0x00026a80 | FUN_00026a80 | main subsystem router | 중간 |
| 0x000818f0 | FUN_000818f0 | per-entity update loop | 중간 (212x context+42x helper) |
| 0x0003d5d0 | FUN_0003d5d0 | **sound subsystem dispatcher** | 높음 (sound_trigger 21x) |
| 0x00075b98 | FUN_00075b98 | init/reset helper | 중간 (memset+58callers) |
| 0x00064048 | FUN_00064048 | default key → 큐 직렬화 | ✅ 확정 (PM-2) |
| 0x00060ab4 | FUN_00060ab4 | page 2 UI render | ✅ 확정 (PM-2) |
| 0x0003add0 | FUN_0003add0 | PIC-indirect frame callback | 중간 |

---

## 5. 신규 도구 / 산출물

| 도구 | 산출물 | 용도 |
|---|---|---|
| [rank_pic_stubs.py](../../tools/recon/rank_pic_stubs.py) | `work/h3/pic_stubs_ranked.json` | 402 stub size/BL/caller ranking |
| [find_queue_callers.py](../../tools/recon/find_queue_callers.py) | `work/h3/queue_callers.json` | 10 큐 API 의 138 BL 호출자 매핑 |
| [analyze_top_stubs.py](../../tools/recon/analyze_top_stubs.py) | `work/h3/top_stubs_analysis.json` | top 15 stub 일괄 분석 + 카테고리 추정 |

세 도구 모두 capstone `walk_with_skip` 패턴을 사용. PM-2 의 표준 도구 패턴 재사용.

---

## 6. 다음 세션 권장 — 정정된 우선순위

### 자동 진척 가능

- ⭐ **FUN_00057394 본문 분석** — 큐 lifecycle owner 본문 디스어셈블 → 진짜 display list 인지 확정 (1.5KB inner loop 추정)
- ⭐ **FUN_00006334 본문 분석** — 17 arm state machine 의 entry table → main loop 가설 검증
- **FUN_0003d5d0 dispatcher 22 arm 디코드** — sound subsystem 의 22개 명령 식별 (BGM_play, SFX_trigger, fade 등)
- **FUN_000818f0 inner loop 분석** — 0x82df4 helper 정체 + +0x002 cycle 변수 의미

### 사용자 블로커 (게임 체감 영향 큼)

- SMAF→OGG 변환 (33개 BGM/SFX) — sound dispatcher 발견과 시너지
- 대사 LLM 번역 (~$0.66, 9,741 unique 대사)

---

## 7. 핵심 교훈

1. **stub ranking 은 ROI 큰 자동화**: 402 stubs 중 top 15 만 봐도 핵심 subsystem 다수 식별. 사이즈/호출자/BL 카운트는 단순 통계지만 정체 추정에 충분.
2. **큐 API 같은 "특이" 함수의 caller 추적이 강력**: 138 BL sites → 31 함수만 매핑됐으나 그중 4개가 큐 호출의 70% 차지. **subsystem boundary 탐색의 좋은 출발점**.
3. **카테고리 자동 추정 휴리스틱**: queue_writer / drawing_heavy / state_machine_or_dispatcher / sequential 등 라벨이 1차 분류로 유용. 단 정밀 식별은 본문 디스어셈블 필요.
4. **+0x002 ~ +0x004 영역의 작은 state offsets** = 보통 stack frame 또는 작은 worker 구조체. **큰 게임 state 는 +0x100+ 영역**. 두 패턴 구분으로 함수 역할 추정.
5. **0 direct caller 함수 39개** = PIC-indirect-only. 모두 frame callback / event handler / 동적 dispatch 후보. Ghidra Script (XREF + BLX register 패턴) 가 마지막 수단.
