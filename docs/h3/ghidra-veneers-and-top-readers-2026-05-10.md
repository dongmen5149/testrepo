# Round 22 (2026-05-10 PM-12) — veneer 14 완전 매핑 + sound/page2 UI 본문 + 신규 GOT slots

## 요약

Round 21 의 ObjectB master interface 발견 후속. PM-12 의 핵심 진척:

1. ⭐⭐⭐ **veneer 영역 14개 완전 매핑** (0xa4294 ~ 0xa42cc) — 모든 register r0~r7/r8/sb/sl/fp/ip/sp/lr 에 대한 `bx rN` indirect call veneer. PM-7 의 14-byte estimate 가 정확히 맞음.
2. ⭐⭐ **FUN_0003d5d0 (sound dispatcher full 4332B) 본문** — 37 cmp arms, 21 sound_trigger + 17 helper_9fd64 paired calls, 5 GOT slots (0x9e28 / 0xa220 / 0xa244 / 0xa245 / 0xa254). cmp 분포가 sound id 처리 패턴 (0x1f / 0xc3 / 0xbf 등 medium-high values).
3. ⭐⭐ **FUN_00060ab4 (page 2 UI full 8808B) 본문** — 21 cmp arms, 207 PC-rel literals (111 negative_signed = 다수 JT 또는 signed offsets), graphics + sound + memset 호출.
4. ⭐ **FUN_00098364 destructor 의 두 번째 slot 식별** = **GOT+0xd00** (storage cell). cleanup 대상 = AnotherObject (slot 0xd00 → storage_ptr → vtable[0x1c/0x2c/0xc]).
5. ⭐ **신규 GOT 슬롯 5개 추가** (sound dispatcher 사용): 0x9e28 / 0xa220 / 0xa244 / 0xa245 / 0xa254 — sound subsystem 전용 슬롯 cluster.

---

## 1. Veneer 영역 완전 매핑 (2AQ) ⭐⭐⭐

### 0xa4294 ~ 0xa42ce 디스어셈블

| addr | instr | callee register |
|---|---|---|
| 0xa4294 | `bx r0` | r0 |
| 0xa4296 | `mov r8, r8` | NOP (alignment) |
| 0xa4298 | `bx r1` | r1 |
| 0xa429a | `mov r8, r8` | NOP |
| 0xa429c | `bx r2` | r2 |
| 0xa429e | `mov r8, r8` | NOP |
| **0xa42a0** | **bx r3** ⭐ | **r3 (most common)** |
| 0xa42a2 | mov r8, r8 | NOP |
| **0xa42a4** | **bx r4** ⭐ | **r4 (Round 21 발견)** |
| 0xa42a6 | mov r8, r8 | NOP |
| 0xa42a8 | `bx r5` | r5 |
| 0xa42ac | `bx r6` | r6 |
| 0xa42b0 | `bx r7` | r7 |
| 0xa42b4 | `bx r8` | r8 |
| 0xa42b8 | `bx sb` | r9 (sb) |
| 0xa42bc | `bx sl` | r10 (sl) |
| 0xa42c0 | `bx fp` | r11 (fp) |
| 0xa42c4 | `bx ip` | r12 (ip) |
| 0xa42c8 | `bx sp` | r13 (sp) |
| 0xa42cc | `bx lr` | r14 (lr) |

### 결론

**총 14 veneer = 모든 ARM register 에 대한 `bx rN` 매핑**:
- r0~r7 (low Thumb)
- r8 (high)
- r9 (sb), r10 (sl), r11 (fp), r12 (ip)
- r13 (sp), r14 (lr)

각 veneer 4-byte aligned, interleaved with `mov r8, r8` (= NOP). 컴파일러가 generic indirect-call 지원을 위해 표준 veneer 테이블 생성.

이제 binary 의 모든 `bl 0xa42XX` 호출은 step 4-byte 하나로 register 식별 가능:
- 0xa42a0 → bx r3 (압도적으로 많음 — 표준 vtable indirect call)
- 0xa42a4 → bx r4 (FUN_0004ad34 의 첫 BL)
- 그 외 register 도 binary 곳곳에서 사용

이는 **Indirect call 분석의 디코더** — 다음 round 들에서 veneer address 만 보고도 어떤 register 에 method ptr 이 있는지 즉시 식별 가능.

---

## 2. FUN_0003d5d0 (sound dispatcher full 4332B) 본문 분석 (2AP)

### 통계

| 측면 | 값 |
|---|---|
| size | 4332 bytes |
| instr | 2063 |
| cmp arms | 37 |
| sound_trigger calls | 21 |
| ?_helper_9fd64 calls | 17 (paired) |
| context_getter | (외에) |
| PC-rel literals | 127 (15 got_slot_offset + 69 medium_int + 31 small_int + 6 negative_signed) |

### Cmp arm 분포 (sound IDs)

| imm (hex/dec) | count | 추정 |
|---|---|---|
| 0x1f (31) | 3 | sound id 31 |
| **0xc3 (195)** | **3** | ⭐ medium-high sound id |
| **0xbf (191)** | **2** | medium-high |
| 0x13 (19) | 2 | |
| 0xb (11) | 2 | |
| 0x9 (9) | 2 | |
| 0x10 (16) | 2 | |
| **0x65 (101)** | **2** | medium |
| **0xba (186)** | **2** | medium-high |
| 0xf (15) | 2 | |
| 0x5 (5) | 2 | |
| 0x1e (30) | 2 | |
| 그 외 (한 번씩) | 11 | 0x6/0xe/0x11 등 |

### 사용된 GOT 슬롯 (5개 신규)

| slot offset | abs addr | 사용 횟수 |
|---|---|---|
| **0x9e28** | 0xb6a68 | 2x |
| **0xa220** | 0xb6e60 | 6x ⭐ (가장 많이 사용) |
| **0xa244** | 0xb6e84 | 1x |
| **0xa245** | 0xb6e85 | 1x (인접 byte access) |
| **0xa254** | 0xb6e94 | 5x |

⭐ **sound 전용 GOT 슬롯 cluster** (0x9e28, 0xa220~0xa254 영역). 모두 0 direct writes (GVM 외부 주입). Sound subsystem 의 전용 state/object pointers.

### 정체

**FUN_0003d5d0** = **master sound subsystem dispatcher**:
- 21 sound_trigger 호출 (각각 다른 sound id, 아마도 sound 21개 이상)
- helper_9fd64 와 paired (17x) — 매 sound trigger 직후 helper 콜 (Round 18 의 "sound 페어 패턴" 확인)
- 37 cmp arms = 다수 sound case 분기 (id 5/9/11/15/16/19/30/31/101/186/191/195 등)
- 5 GOT 슬롯 = sound state/queue/buffer pointers

이는 PROGRESS PM-3 의 "sound subsystem dispatcher" 가설 정밀 확정. 게임 모든 sound 명령의 진입점.

---

## 3. FUN_00060ab4 (page 2 UI full 8808B) 본문 분석 (2AP)

### 통계

| 측면 | 값 |
|---|---|
| size | 8808 bytes |
| instr | 4191 |
| cmp arms | 21 (작은 비율 — UI rendering 위주) |
| graphics_primitive | 5 calls |
| context_getter | 5 calls |
| sound_trigger | 15 calls |
| memset_like | 2 calls |
| PC-rel literals | **207 (111 negative_signed + 47 medium_int + 24 small_int + 9 got_slot_offset + 9 other + 6 zero + 1 binary_addr)** |

### Cmp arm 분포

| imm (hex/dec) | count | 추정 |
|---|---|---|
| 0x0 (0) | 4 | gates |
| 0x7 (7) | 4 | type-7 처리 |
| 0x3 (3) | 3 | type-3 |
| 0x12 (18) | 2 | type-18 |
| 0xb (11) | 2 | type-11 |
| **0x3b (59)** | **2** | ⭐ medium id |
| 그 외 1x씩 | 6 | 0x1/0xe/0xc/0xa |

### ⭐⭐ 111 negative_signed_offset 의 의미

이 비율 (53% of literals) 은 binary 내 다른 함수 대비 압도적. 가설:
- **다수 JT base 계산** — 함수 곳곳에 jump table 들이 있을 것 (각 negative offset 이 JT base 를 가리킴)
- 또는 **PC-rel data tables** — 그래픽 데이터 (sprite atlas, layout coord) 가 함수 직후에 임베드

PM-2 분석 ("9KB 100% 코드, page 2 UI rendering function") 일관 — 100% 코드지만 다수 인라인 JT 가 있을 수 있음.

### 정체

**FUN_00060ab4** = **page 2 UI rendering function** (확정):
- graphics_primitive 5x = drawing primitives
- sound_trigger 15x = page 2 화면에서 다양한 sound feedback
- memset_like 2x = buffer clear
- 작은 cmp arm 수 (21) + 큰 size = **다양한 menu items / UI elements 의 sequential rendering**

다음 round 에서 negative_signed offsets 위치 분석으로 inline JT 들 위치 매핑 가능.

---

## 4. FUN_00098364 destructor 의 두 번째 slot 식별 (2AR) ⭐

### 디스어셈블 재분석

```asm
;; ObjectA setup
ldr r3, [pc, #0x40]; mov sl, r3       ; r3 = lit1 = 0x1a8cc (GOT base offset)
ldr r3, [pc, #0x40]                   ; r3 = lit2 = 0xd00 (NOTE: 첫 번째 slot offset)
add sl, pc                            ; sl = GOT base
add r3, sl                            ; r3 = GOT + 0xd00 = 0xb3940
ldr r5, [r3]                          ; r5 = *(0xb3940) = StorageCell ptr
ldr r0, [r5]                          ; r0 = *StorageCell = current_resource_ptr

cmp r0, #0; bne 0x98382                ; if non-null → cleanup

;; CLEANUP — uses ANOTHER slot (0x44c = ObjectA)
0x98382:
ldr r3, [pc, #0x30]                   ; r3 = lit3 = 0x44c (ObjectA slot offset)
add r3, sl
ldr r4, [r3]                          ; r4 = ObjectA ptr
ldr r3, [r4]; ldr r3, [r3, #0x1c]     ; r3 = ObjectA.vtable[0x1c]
bl 0xa42a0                             ; ObjectA.method7 (cleanup)
... vtable[0x2c], vtable[0xc] ...

movs r3, #0; str r3, [r5]              ; *StorageCell = NULL
```

### ⭐⭐ 핵심 정정

Round 20 의 분석을 정정합니다:
- **r5 (gate)** 는 slot **0xd00** (NOT ObjectA) — **StorageCell** ptr 슬롯
- **r4 (cleanup target)** 는 slot **0x44c** (ObjectA) — vtable methods 호출
- ObjectA 의 vtable[0x1c/0x2c/0xc] 가 cleanup methods

따라서 정확한 패턴:
- StorageCell @ slot 0xd00 보유 "current resource ptr"
- ObjectA @ slot 0x44c 가 cleanup logic 보유 (vtable methods)
- destructor: if StorageCell.current != NULL → ObjectA.cleanup1, .cleanup2, .cleanup3 → StorageCell.current = NULL

### ObjectA vtable methods (확장 매핑)

기존 (Round 19/20) + 신규 (Round 22):

| offset | method 사용처 |
|---|---|
| 0 | base method (FUN_00098244, FUN_0004ad34) |
| **0xc** | ⭐ **cleanup3** (FUN_00098364) — Round 22 신규 |
| 0x10 | use phase method (FUN_00098244) |
| **0x1c** | ⭐ **cleanup1** (FUN_00098364) — Round 22 신규 |
| 0x20 | use phase method (FUN_00098244) |
| **0x2c** | ⭐ **cleanup2** (FUN_00098364) — Round 22 신규 |
| 0x44 | setup w/ 2-arg (FUN_0004ad34) |
| 0x54 | resource read (FUN_00099a9c) |
| 0x58 | release / cleanup (FUN_00099a9c, FUN_00098244) |
| 0x68 | state notify (FUN_00097fa8, FUN_00098244) |
| 0x7c | resource acquire (FUN_00099a9c) |
| 0x80 | resource write (FUN_00099a9c) |

⭐ 이제 **12 vtable methods 매핑**. ObjectA 의 vtable 인터페이스 점차 명확. 다음 round 에서 ObjectB top reader 들의 vtable 사용으로 **vtable 더 확장 가능**.

---

## 5. GOT 슬롯 누적 통계 (Round 18~22)

### 신규 슬롯 (Round 22)

| Slot | Abs Addr | 출처 | 정체 가설 |
|---|---|---|---|
| **0x9e28** | 0xb6a68 | Round 22 (sound dispatcher) | sound subsystem 전용 |
| **0xa220** | 0xb6e60 | Round 22 (sound, 6x) | sound state/queue ⭐ |
| **0xa244** | 0xb6e84 | Round 22 (sound) | sound buffer ptr |
| **0xa245** | 0xb6e85 | Round 22 (sound, byte access) | adjacent byte field |
| **0xa254** | 0xb6e94 | Round 22 (sound, 5x) | sound state |

총 **19 GOT 슬롯 매핑** (15 → 19, +4 sound + 1 byte). 모두 0 direct writes (시스템 표준).

### 슬롯 그룹 재분류 (Round 22 갱신)

| 그룹 | 슬롯 | scale |
|---|---|---|
| **Master GVM interface** | 0x18 (ObjectB) | 860 readers / 240 funcs |
| **Task pointers** | 0x16c, 0x444 | 147+ / 60+ readers |
| **Widespread state** | 0x9c70 | 112 readers |
| **ObjectA cluster** | 0x44c, 0xd00 (storage cell) | 8+ readers |
| **Sound subsystem** ⭐ | 0x9e28, 0xa220, 0xa244, 0xa245, 0xa254 | sound-specific |
| **Helper data ptrs** | 0xd00, 0xd04, 0xd08 | small (Round 19) |
| **Record array** | 0x9bb4, 0x9cbc, 0x9cfe, 0x9cc0 | 0x38 stride record |
| **State/flag** | 0x128, 0x29e, 0x9e78 | small flags |
| **Subsystem-specific** | 0x9c71, 0x9c84, 0xac78 | varied |

19 슬롯 모두 GVM 외부 주입. 게임의 GVM API 는 multiple subsystems (master ObjectB + sound + ObjectA + task) 으로 명확히 분리됨.

---

## 6. 다음 세션 권장 다음 단계 (Round 23 후보)

| # | 작업 | 명령 | 산출물 |
|---|---|---|---|
| ⭐⭐ 2AU | **sound subsystem 슬롯 (0x9e28/a220/a244/a254) writer/reader** | `find_global_slot_writers.py --slot-offset 0xa220` 등 | sound state machine 정체 |
| ⭐⭐ 2AV | **FUN_0003d5d0 sound id immediate backtrace** | r0 backtrace 강화 (track_reg_value) | 21 sound 의 실제 id 식별 |
| ⭐ 2AW | **ObjectB top reader 추가 (FUN_00030018, FUN_0002ce08)** | `disasm_subsystem_func.py` 2개 | ObjectB vtable 더 매핑 |
| 2AX | FUN_00060ab4 의 111 negative_signed offsets 위치 매핑 | 인라인 분석 | page 2 UI 의 inline JT 발견 |
| 2AY | FUN_000980cc (ObjectA cmp #9 sister) 본문 비교 | 본문 분석 | partial vs full lifecycle |

---

## 7. 산출물

```
work/h3/sound_dispatcher_full_disasm.json   ; 2AP
work/h3/page2_ui_full_disasm.json           ; 2AP
```

(2AQ veneer 매핑 + 2AR destructor 정정은 inline 분석 — JSON 미저장)

---

## 8. Round 22 핵심 takeaway

1. **veneer 영역 14개 완전 매핑** — 모든 register r0~lr 의 `bx rN` veneer 가 0xa4294~0xa42cc 에 4-byte step + NOP 패턴으로 배치. 향후 indirect call 분석의 디코더.
2. **sound subsystem 본문 풀이** — FUN_0003d5d0 4332B 의 37 cmp arms + 21 sound_trigger + 17 paired helper. medium-high sound id (0xc3, 0xbf, 0xba) 위주.
3. **page 2 UI 본문 풀이** — FUN_00060ab4 8808B 의 207 PC-rel literals (111 negative signed = inline JT 다수 후보). 작은 cmp arms (21) + 큰 size = sequential UI element rendering.
4. **destructor 의 진짜 패턴 풀이** — slot 0xd00 (StorageCell) gate + slot 0x44c (ObjectA) cleanup vtable. Round 20 의 분석 정정.
5. **ObjectA vtable 12 methods 매핑** — offset 0/0xc/0x10/0x1c/0x20/0x2c/0x44/0x54/0x58/0x68/0x7c/0x80. ObjectA 가 audio/asset resource manager 의 강력한 후보.
6. **신규 GOT 슬롯 5개** (sound subsystem) — 누적 19 슬롯, 모두 0 direct writes. Sound dispatch 가 5 슬롯 cluster 사용.
