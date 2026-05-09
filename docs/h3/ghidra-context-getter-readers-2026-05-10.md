# §4.4 후속 — 2026-05-10 PM-6 세션 (FUN_0004ad10 정정 + type-tag reader 발견 + chain dispatcher)

> 2026-05-10 PM-5 의 큐 protocol 매핑 후속.
> 자동 우선순위 **2R + 2S + 2Q** 일괄.
> 결과: context_getter 정정 (단일 슬롯 getter 확정) + 가장 강력한 type-tag reader 후보 (FUN_0009b252) 발견 + chain dispatcher 검증.

---

## 1. 2R — FUN_0004ad10 정체 확정 ⭐⭐

### 1A. raw 디스어셈블

```
0x4ad10: mov ip, r3                 ; preserve caller's r3 in ip
0x4ad12: mov r3, sl                  ; save caller's sl in r3
0x4ad14: push {r3}                   ; stack-save sl
0x4ad16: mov r3, ip                  ; restore r3
0x4ad18: ldr r3, [pc, #0x10]         ; r3 = *0x4ad2c = 0x00067f1e
0x4ad1a: mov sl, r3                  ; sl = 0x67f1e
0x4ad1c: ldr r3, [pc, #0x10]         ; r3 = *0x4ad30 = 0x00000444
0x4ad1e: add sl, pc                  ; sl = 0x67f1e + 0x4ad22 = 0xB2C40 ⭐ GOT base
0x4ad20: add r3, sl                  ; r3 = GOT_base + 0x444 = 0xB3084
0x4ad22: ldr r0, [r3]                ; r0 = *0xB3084 (GOT slot value)
0x4ad24: pop {r3}                    ; restore caller's sl
0x4ad26: mov sl, r3
0x4ad28: bx lr                       ; return
```

### 1B. 결정적 결론

- **인자 받지 않음** — r0/r1/r2/r3 어느 것도 함수 입력으로 사용 안 함
- **단일 GOT 슬롯 getter** — 항상 GOT base + 0x444 (= 0xB3084) 의 값 반환
- 0x444 (1092) 는 literal pool 에 하드코딩
- 이 슬롯은 **매우 자주 호출되는 단일 글로벌** — 2KB default_key 에서 29x, sound_dispatcher 22x, type_tag_reader 53x, render_buffer 11x

### 1C. PM-5 의 backtrace false signal 정정

PM-5 분석에서 발견된 `r0=*0x643b0=0x9c71` 같은 결과는 **FUN_0004ad10 의 인자가 아님**. 실제 컨텍스트:

```
0x64074: ldr r0, [pc, #0x338]    ; r0 = 0x9c71 (literal load)
0x64076: adds r3, r3, r0          ; r3 += r0 ← r0 ACTUAL USE
0x64078: ldrb r3, [r3]             ; r3 = byte at *r3
0x6407a: strb r3, [r4]             ; store byte
0x6407c: bl #0x4ad10               ; ← BL 의 인자가 아님! r0 는 위에서 이미 소비됨
0x64080: adds r2, r0, #0           ; r2 = (FUN_0004ad10 의 return value)
```

→ **backtrace 도구가 r0 의 마지막 writer 만 보고 인자라고 잘못 판단**. 실제로 r0 는 BL 직전에 다른 instruction 에서 사용 + BL 이 r0 를 overwrite 하지만, 인자로 받는 건 아님.

→ **개선 방향**: backtrace 가 r0 의 마지막 writer 를 찾을 때, 그 writer 와 BL 사이에 r0 의 USE 가 있으면 "consumed before BL → not BL's arg" 표기. 하지만 정확한 dataflow analysis 는 ROI 낮아 보류.

### 1D. 호출 의미 재해석

이전 가정: `bl context_getter` = 글로벌 fetcher → 함수 호출 횟수가 곧 글로벌 액세스 빈도.

정확한 해석: `bl FUN_0004ad10` = 항상 **같은 단일 글로벌 (GOT+0x444) 의 현재 값을 r0 로 가져옴**. 함수의 의미가 "context pointer" 또는 "current task pointer" 같은 단일 cached pointer 일 가능성.

→ 이 슬롯은 PIC 환경에서 **모든 함수가 공유하는 single global state pointer**. 매우 자주 호출되는 만큼 게임의 핵심 state 위치.

---

## 2. 2S — type-tag reader 후보 자동 검색 (도구 `find_type_tag_readers.py`)

### 2A. 전체 type tag prevalence (binary 전체 cmp arm 분석)

| type tag | cmp 사이트 | 의미 |
|---|---|---|
| `0x00` | 3511 | null check (대부분 type tag 아님) |
| `0x01` | 459 | boolean check + type-1 reader 일부 |
| `0x03` | 234 | type-3 또는 small int |
| `0x04` | 212 | type-4 reader 후보 |
| **`0x05`** ⭐ | **111** | **type-5 reader 후보 (PM-5 dominant)** |
| `0x14` | 11 | type-0x14 |
| `0x1f` | 24 | type-0x1f |
| `0x3d` | 2 | sub-op 거의 없음 (jump table 예상) |
| `0x3e` | 4 | sub-op |
| `0x3f` | 4 | sub-op |
| `0x40` | 3 | sub-op |
| `0x41` | 0 | (writer 만 있고 reader 없음) |

### 2B. ⭐⭐ Top reader 후보 — `FUN_0009b252` (rank #1)

```
size: 4142 bytes (~4KB)
arms: 86+ cmp arms 중 6 distinct type tags 모두 등장
tag distribution: 0x00:24, 0x01:17, 0x03:12, 0x04:6, 0x05:3, 0x14:1
```

→ **5 distinct nonzero type tags + 가장 많은 cmp arms 분포** = **가장 강력한 type-tag reader 후보**.

### 2C. FUN_0009b252 본문 분석 (도구 `disasm_subsystem_func.py`)

```
size=4142 BL=53 cmp_arms=86+ pcrel_lits=93
top BL: context_getter (FUN_0004ad10) 53x  ← 더 많이 호출
no queue API directly called (BL to 0x7e150/0x7e184 등 0건)
```

→ 큐 API 직접 호출 안 함. cmp arms 풍부 + context_getter heavy. 가설:
- **byte_stream interpreter**: 외부에서 받은 byte 를 cmp 로 분기하는 generic dispatcher
- 또는 **state machine** 으로 6 type tag 를 다양한 게임 sub-system 처리

### 2D. queue reader → cmp #type_tag 직접 패턴 — **단 2건**

```
0x70ee6 (in FUN_00070d88): bl memcpy_read → 0x70ef0: cmp #0x00
0x72960 (in FUN_0007286c): bl buffer_status → 0x7296a: cmp #0x00
```

둘 다 cmp #0x00 (null/status check) 으로 type tag dispatch 패턴 아님. → **큐 → byte → cmp #type 의 직접 형태는 거의 없음**. 더 복잡한 dataflow:
- byte 를 변수에 저장
- 다른 함수로 전달
- 그 함수 안에서 cmp

→ reader 측 분석에는 dataflow 추적이 필요. 자동 식별 한계.

### 2E. 다른 dispatcher 후보들

| rank | 함수 | tags | arms | hint |
|---|---|---|---|---|
| #2 | FUN_000a11e4 | 5 | 84 | 0x00 dominant (78), 다른 tag 적음 — null check 위주 |
| #3 | FUN_00019b5a | 5 | 83 | 비슷 |
| #4 | FUN_000113cc | 5 | 77 | 비슷 |
| #5 | **FUN_00006334** ⭐ | **5** | **74** | **main_dispatcher** (PM-4 분석한 wide dispatcher) — 5 distinct type tags 사용 = type tag dispatch 후보 강화 |
| #25 | FUN_00056bf8 | 5 | 5 | PM-5 codec 함수 (특이한 sub-op 0x3d/0x3e/0x1f) |
| #28 | FUN_00026a80 | 4 | 33 | top stub #4 (PM-3) |
| #30 | FUN_000031dc | 4 | 25 | chain dispatcher (PM-5 발견, 본 세션 분석) |

→ **FUN_00006334 와 FUN_000031dc 가 chain dispatcher 페어** (둘 다 type tag 다수 처리) + **FUN_0009b252 가 별도 reader** 가능성.

---

## 3. 2Q — FUN_000031dc (chain dispatcher) 본문 분석

### 3A. 통계

```
size=6726 bytes (6.7KB)
cmp arms: 47+ (다양한 imm: 0x32='2', 0x46='F', 0x0e, 0x05, 0x0b, 0x06 등)
interesting BL: 3 (context_getter 2 + graphics_primitive 1)
PC-rel LDR: 151 (got_slot 120 + neg_signed 16)
```

### 3B. 정체 추정

- **광범위 dispatcher** (FUN_00006334 와 비슷한 카테고리)
- **추적 helper 호출 거의 없음** (graphics_primitive 1회) — main_dispatcher 와 같은 특징
- 0x32 ('2') / 0x46 ('F') ASCII 문자 cmp arms — 텍스트 기반 처리?
- 4 distinct type tags + 25 arms

→ FUN_00006334 의 마지막 BL 로 호출되는 chain dispatcher 가설 유지. 두 함수 페어로:
- FUN_00006334 (10KB, 96 arms): 1차 dispatch
- FUN_000031dc (6.7KB, 47 arms): 2차 dispatch / continuation

→ 합산 16.7KB 의 dispatch 로직 = 게임 메인 로직의 큰 부분 차지.

---

## 4. 신규 도구 / 산출물

| 도구/산출물 |
|---|
| [find_type_tag_readers.py](../../tools/recon/find_type_tag_readers.py) (신규) — binary 전체 cmp #type_tag 사이트 + 함수별 coverage |
| `work/h3/type_tag_readers.json` |
| `work/h3/chain_dispatcher_disasm.json` (FUN_000031dc) |
| `work/h3/type_tag_reader_disasm.json` (FUN_0009b252) |

---

## 5. 큐 protocol 풀이 진척 종합

### 5A. 확정/유력

- ✅ **type-5 가 dominant**: 16 emit (3 writer) + 111 cmp 사이트 (reader 측에서도)
- ✅ **type-1/3/4 도 reader 측에서 흔함**: 459/234/212 cmp 사이트
- ✅ **sub-op 0x3d~0x40 은 reader 측 cmp 매우 적음** (2~4 each) → jump table 으로 컴파일됐거나 다른 dataflow
- ✅ **FUN_0004ad10 = 단일 슬롯 getter** (인자 없음) — 게임 전역 state pointer
- ⭐ **FUN_0009b252 = 가장 광범위한 type-tag reader 후보** (4KB, 6 distinct tags)

### 5B. 미해결

- ❓ 큐 reader → byte → cmp #type_tag 의 직접 dispatch 패턴 부재 → reader 의 정확한 dataflow 미식별
- ❓ FUN_0009b252 / FUN_00006334 / FUN_000031dc 의 정체 — 모두 광범위 dispatcher 지만 어느 것이 진짜 큐 reader 인지 미확정
- ❓ type tag 의 의미 (event log? save record? command stream?) — 더 많은 reader 본문 분석 필요

---

## 6. 다음 세션 권장

### 자동 진척 가능

- ⭐ **FUN_0009b252 본문 정밀 분석** — 86+ cmp arms 의 분포 + 각 arm 의 BL target → type-5 sub-op 별 핸들러 매핑
- **`disasm_subsystem_func.py` 의 false-signal 정정** — r0 가 BL 직전에 consumed 된 경우 별도 표기 (low ROI 이지만 정확도 향상)
- **기타 top stub 분석** — FUN_00026a80 (8.4KB main subsystem router), FUN_000818f0 (5.4KB per-entity update loop), FUN_00056a40 등.

### 사용자 블로커

- SMAF→OGG (33 BGM/SFX) — 게임 체감 영향 큼
- 대사 LLM 번역 (~$0.66, 9,741 unique 대사)

---

## 7. 핵심 교훈

1. **raw bytes 검증의 가치**: PM-5 의 "FUN_0004ad10 인자 받을 가능성" 가설을 한 capstone disasm 으로 즉시 정정. Ghidra 디컴파일이 misleading 한 경우 raw 디스어셈블이 결정적.
2. **backtrace 도구의 false signal 패턴**: `ldr r0, [pc, #X]; ... use r0 ...; bl <foo>` 같은 패턴에서 r0 가 BL 직전에 이미 consumed 된 경우 도구가 잘못 인자라고 보고. 실제 사용 시 consumer 검증 필요.
3. **binary 전체 패턴 검색의 효율성**: 350K instructions 디스어셈블 → 838 함수의 type tag arm 분포 즉시 매핑. 함수별 specific 분석보다 wide-scan 이 ROI 높을 때 있음.
4. **single-slot global pointer 패턴**: FUN_0004ad10 같은 무인자 getter 가 **prevalent global state pointer** 이라면 = 게임의 핵심 state 위치. 이 슬롯 내용을 알면 게임 구조 풀이 큰 도움.
5. **3 dispatcher 가설**: FUN_00006334 + FUN_000031dc + FUN_0009b252 모두 dispatcher 카테고리지만 helper 호출 패턴 다름 → 서로 다른 sub-system 처리. 큐 reader 는 helper 적은 dispatcher 중 하나 (직접 큐 API 호출 부재로 식별 모호).
