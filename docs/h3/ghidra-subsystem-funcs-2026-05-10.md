# §4.4 후속 — 2026-05-10 PM-4 세션 (FUN_00057394 / FUN_00006334 / FUN_0003d5d0 본문 디스어셈블)

> 2026-05-10 PM-3 의 top 15 stub 카테고리 추정 후속.
> 자동 우선순위 **2K + 2L + 2M** 일괄 진행 — 세 핵심 subsystem 함수의 본문 capstone 디스어셈블.
> 통합 도구 `disasm_subsystem_func.py` 작성 — cmp arm 추출 + BL r0 backtrace + PC-rel LDR 카테고리 통합.

---

## 1. 2K — FUN_00057394 (3.5KB) ⭐ **typed record writer (큐 직렬화)**

### 1A. 본문 통계

```
size=3550 bytes (1656 instr)
arms: 12 cmp+branch (대부분 cmp r3, #0 null check)
interesting BL: 70 (graphics 20 + byte_append 19 + context 11 + memset 10 + flush 7 + memcpy_read 2 + u32_append 1)
PC-rel LDR: 50 (medium_int 21 + neg_signed 13 + got_slot 8 + zero 4)
```

### 1B. ⭐ byte_append immediate 분포 — **typed record format 확정**

| immediate | count | 의미 |
|---|---|---|
| `#0x05` | 7x | **record begin marker (type tag)** |
| `#0x3d` | 3x | sub-opcode A |
| `#0x14` | 1x | sub-opcode B |
| `#0x3f` | 1x | sub-opcode C |
| `#0x03` | 1x | sub-opcode D |
| `#0x40` | 1x | sub-opcode E |
| (unknown) | 5x | register load (indirect) |

**flush_swap 7회 = byte_append #0x05 7회** → **각 record 가 하나의 commit 단위**.

### 1C. record 패턴 (코드 순서)

```
1. site 0x575d2: byte_append(0x05) + byte_append(0x14)        + flush(0x14)        ← record A
2. site 0x576a2: byte_append(0x05) + byte_append(0x3f)        + flush             ← record B
3. site 0x5793c: byte_append(0x05) + byte_append(0x03) + ?    + memcpy_read + flush  ← record C (variable args)
4. site 0x579d8: byte_append(0x05) + byte_append(0x3d) + ?    + flush             ← record D-1
5. site 0x57e60: byte_append(0x05) + byte_append(0x3d) + ?    + flush             ← record D-2
6. site 0x57ea6: byte_append(0x05) + byte_append(0x3d) + ?    + flush             ← record D-3
7. site 0x57fb6: byte_append(0x05) + byte_append(0x40) + ? + u32_append + flush   ← record E (32-bit arg)
```

### 1D. 정체 추정 — typed record stream writer

- 모든 record 가 **type tag 0x05** 로 시작 → 이 함수 출력은 "type-5 record" 단일 카테고리
- subop 별로 args 가 다름 (0x14: 인자 없음, 0x3: memcpy_read 호출 → 가변 길이 read, 0x40: u32_append → 32-bit 정수)
- **이건 display list 단순 OR save game 단순 이라기 보다, typed record stream codec** — 같은 큐 가 여러 type tag (0x05, 다른 함수에서는 다른 tag) 를 사용하는 구조
- graphics_primitive 20x = 화면 렌더링 후 큐에 record 출력 → **render 결과 기록 / replay journal / undo 시스템**

### 1E. 다음 분석 단서

- FUN_00056bf8 (queue read+write) 본문 분석 시 다른 type tag 발견 가능
- FUN_00064048 (default key handler, 큐 사용) 의 byte_append immediate 분석으로 type tag 확장 매핑

---

## 2. 2L — FUN_00006334 (10KB) ⭐⭐ **광범위 dispatcher (main loop 후보 부분 검증)**

### 2A. 본문 통계

```
size=10134 bytes (4871 instr)
arms: 96 cmp+branch (cmp #0 = 53회 null check + 15 distinct nonzero values)
interesting BL: 1 (only context_getter — 추적 중인 helper 외 다른 sub-system 호출)
PC-rel LDR: 162 (got_slot 135 + neg_signed 17 + zero 6)
```

### 2B. cmp arm 분포 — 광범위 dispatcher

```
cmp #0x00: 53x  (null/zero check)
cmp #0x01: 13x  (가장 흔한 nonzero arm)
cmp #0x06: 5x
cmp #0x02: 5x
cmp #0x03: 5x
cmp #0x07: 3x
cmp #0x0d, 0x04, 0x08: 각 2x
cmp #0x0a, 0x0b, 0x11, 0x16, 0x12, 0x05: 각 1x
```

→ **15+ distinct nonzero arms** (이전 추정 17 arms 보다 약간 보수적). 1~22 범위 → 다양한 분기 (state 또는 message ID 검사).

### 2C. 정체 재해석

이전 추정 "main game loop dispatcher" 였으나, 본문 분석 결과:
- ✅ **광범위 분기 dispatcher** (96 arms 확정)
- ⚠️ **추적 중인 helper 호출 0건** (큐/UI/sound 모두 부재) — main loop 라면 보통 render/input/sound 호출이 보일 텐데
- ✅ **162 PC-rel LDR 중 135가 GOT slot offsets** = 글로벌 데이터 heavy 접근 (게임 state 가 모두 GOT 슬롯)
- ✅ +0x18 read 75x + +0x1c/+0x20 reads = 8~12 byte struct iterating

→ **재해석**: main loop 직접보다는 **event/script interpreter** 또는 **save game record processor** 후보. 다양한 record type 별 분기 + GOT 슬롯 액세스.

다른 가능성: **scripting VM** — `_scn` byte stream 의 opcode interpreter 가 여기 있을 수도. PROGRESS 의 §4.4 _scn parser 미발견 항목과 연관 가능.

### 2D. 추가 분석 단서

- 187 internal BL targets 중 top 호출:
  - 0x08aca (70x) = 직접 다음 함수 (FUN_00008aca) — 이 함수의 inner loop body 후보
  - 0x80664 (22x), 0x7d258 (14x), 0x48eec (9x), 0x8ad8 (8x)
- → 다음 세션: FUN_00008aca 본문 분석 → FUN_00006334 의 inner loop body 정체 식별

---

## 3. 2M — FUN_0003d5d0 (4.3KB) ⭐ **sound subsystem dispatcher 확정**

### 3A. 본문 통계

```
size=4288 bytes (2041 instr)
arms: 22 cmp+branch (cmp #0xc3, 0x0f, 0x1e, 0x04, 0x05, 0x15 등 다양)
interesting BL: 60 (sound_trigger 21 + helper_9fd64 17 + context 22)
PC-rel LDR: 127 (medium_int 69 + small_int 31 + got_slot 15)
```

### 3B. (sound_trigger + helper_9fd64) 페어 패턴 ⭐

21 sound_trigger 와 17 helper_9fd64 calls 가 **페어로 호출** (offset 차이 ~8 bytes):

```
0x3d686: sound_trigger; 0x3d68e: helper_9fd64
0x3d8d0: sound_trigger; 0x3d8d8: helper_9fd64
0x3d922: sound_trigger; 0x3d92a: helper_9fd64 (없음)
...
```

→ **sound 명령은 (sound_trigger + helper_9fd64) 한 쌍**. helper_9fd64 가 sound subsystem 의 핵심 worker.

### 3C. cmp arm — 22 sound mode/state

```
cmp #0xc3 (195) — magic value (sound 시스템의 special signature?)
cmp #0x0f (15)
cmp #0x1e (30)
cmp #0x04, 0x05, 0x15 (4, 5, 21)
... 등 22 distinct
```

22 arms → BGM_play / BGM_stop / SFX_trigger / fade_in / fade_out / volume_set 등 sound API 분기 후보.

### 3D. sound ID 추출 한계

```
sound_trigger r0 distribution:
  (21 total, 21 indirect/unknown)
```

모든 sound_trigger 의 r0 args 가 **register load 또는 LDR [base+offset]** — immediate 직접 추출 0건. capstone backtrace 가 직전 1-3 instr 만 추적해서는 부족.

**향후**: 더 깊은 backtrace (10+ instr) + register propagation 추적 시도하면 일부 sound ID 식별 가능. 또는 sound_trigger 본문 (`FUN_00099764`) 의 인자 사용 패턴 분석.

### 3E. PC-rel literals — sound parameters 임베드

127 PC-rel LDR 중:
- medium_int 69 (frequency / channel / sound id 후보)
- small_int 31 (mode flag / volume 후보)
- got_slot 15 (sound state 글로벌)

→ 사운드 함수 본문에 **100+ 정수 상수** 가 임베드. 본문 디스어셈블 + 인자 backtrace 확장으로 sound ID 매핑 가능.

---

## 4. 신규 도구 / 산출물

| 도구 | 산출물 | 용도 |
|---|---|---|
| [disasm_subsystem_func.py](../../tools/recon/disasm_subsystem_func.py) | `work/h3/<label>_disasm.json` | 임의 함수 본문 디스어셈블 + cmp arm 추출 + BL r0 backtrace + PC-rel LDR 카테고리 |

`render_buffer_disasm.json` (FUN_00057394), `main_dispatcher_disasm.json` (FUN_00006334), `sound_dispatcher_disasm.json` (FUN_0003d5d0) 3개 산출물. 향후 다른 핵심 함수 (FUN_00056bf8, FUN_00026a80, FUN_000818f0) 분석에도 같은 도구 재사용.

---

## 5. 큐 record 포맷 가설 (2K 발견)

**큐 byte stream 의 record 포맷** (가설):

```
record:
  byte type_tag      ; 0x05 = type-A (FUN_00057394 emit)
                     ; 다른 type 은 다른 함수가 emit
  byte sub_opcode    ; type 별 의미 다름 (0x03/0x14/0x3d/0x3f/0x40 for type-5)
  variable args      ; 0x03 → memcpy_read, 0x40 → u32_append, 그외 → 인자 없음
  
flush_swap()         ; record 단위 commit
```

→ 각 큐 writer 함수의 byte_append immediate 분석 = type tag 매핑.
→ 큐 reader (FUN_00056bf8 / consumer-only 함수들) 의 cmp arm 분석 = type tag 별 dispatch.

다음 분석으로 큐 protocol 전체 매핑 가능.

---

## 6. 다음 세션 권장

### 자동 진척 가능

- ⭐ **FUN_00056bf8 (queue codec) 본문 분석** — disasm_subsystem_func.py 재사용. 다른 큐 writer 의 type tag 발견 + reader의 cmp arm 분석.
- ⭐ **FUN_00008aca 분석** — FUN_00006334 의 70x inner helper. main_dispatcher inner loop body 정체 식별.
- ⭐ **r0 backtrace 강화** — 10+ instr 거슬러 올라가는 register propagation 으로 sound ID / queue arg immediate 추출 강화. sound_trigger r0 의 21/21 unknown 을 절반 이상 식별 가능.
- **FUN_00026a80 / FUN_000818f0 본문 분석** — top 15 의 미분석 항목.

### 사용자 블로커

- SMAF→OGG (33 BGM/SFX) — sound dispatcher 발견과 시너지: 향후 sound ID 매핑 시 BGM 파일과 매핑 가능
- 대사 LLM 번역 (~$0.66, 9,741 unique 대사)

---

## 7. 핵심 교훈

1. **통합 도구 패턴의 재사용성**: `disasm_subsystem_func.py` 한 도구로 3 함수 분석 — 매번 specific 도구 작성 대비 효율적. 다음 분석에도 그대로 재사용 가능.
2. **cmp arm 패턴이 함수 정체의 강력한 지표**: 12 arms (대부분 null check) = sequential serializer / 96 arms = wide dispatcher / 22 arms (다양한 값) = subsystem dispatcher. 단순 카운트만으로 분류 가능.
3. **BL r0 backtrace 의 한계**: 직전 1-3 instr 검색은 immediate 만 빠르게 추출. register-loaded arg 는 더 깊은 propagation 필요. 21/21 unknown sound IDs 가 그 예.
4. **typed record stream 가설 = 큐 protocol 풀이의 열쇠**: 0x05 type tag 패턴이 다른 큐 writer 에도 있을 가능성. 각 writer 가 자기만의 tag 사용 → 큐 reader 의 cmp arm 으로 매칭 → 전체 protocol 매핑.
5. **"main loop" 가설은 함수 외형보다 helper 호출 패턴으로 검증**: FUN_00006334 가 96 arms 의 큰 dispatcher 임은 확실하지만, render/input/sound helper 호출 0건은 진짜 game loop 라면 부자연스러움. **interpreter / serializer 후보가 더 그럴듯**.
