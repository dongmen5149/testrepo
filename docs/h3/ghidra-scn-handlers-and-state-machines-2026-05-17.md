# Hero3 Ghidra — Round 37 / 2026-05-17 PM (SCN/NPC handlers + cluster #1 state machine)

> Round 36 (`ghidra-cluster-and-scn-jt-2026-05-11.md`)에서 디코드한 19→7 JT의 destinations 본문을 분석.
> 핵심: SCN/NPC dispatcher가 **동일 통합 아키텍처**임을 검증 + cluster #1 state machine의 2단 paired structure 발견.

## 한 줄 요약

Hero3는 **단일 통합 19-opcode scripting engine**을 가지며, sister entry(NPC, FUN_0008b2e8)와 main entry(scene, FUN_0008dcd8) 둘 다 동일한 JT 구조 + 동일한 BL 패턴(screen_ptr_getter + helper_9fd64 + draw_text_sprite + sound_trigger + context_getter)을 사용한다. 13 공통 opcode = **text output handler 확정**, 6 special opcode 중 0x12 = 11.4KB sub-interpreter (EUC-KR/ASCII multi-byte text parser). task_struct cluster #1 (0x9afc~0x9b3c)는 **FUN_00040fb0 → FUN_00041c14 → FUN_00041c6e** 2단 paired state machine이 담당하며, BL은 100% context_getter + memset_like only (no graphics, no sound).

## 2DP: SCN common handler 0x8ec26 본문 (1258B)

- **size**: 0x8ec26 ~ 0x8f110 = 1258B (605 instructions)
- **cmp arms** (6): `cmp #3 (ble)` + `cmp #0xb (beq)` + `cmp #0xc (bne)` + `cmp #0xb (bgt)` + `cmp #0 (beq)`×2 — opcode r3 ∈ {0..0xc} 내부에서 다시 4-way 분기 (3 sub-groups + 0xc 단독)
- **BL 분포**:
  - 3x `screen_ptr_getter` (frame buffer 획득)
  - 3x `?_helper_9fd64` (sound 페어 helper, Round 22)
  - 3x `draw_text_sprite` (텍스트 스프라이트 그리기) ⭐
  - 2x `sound_trigger` (sound 재생)
  - 1x `context_getter (r0=#0xff)` (task_ptr 획득, 0xff sentinel)
- **literals**: 30 PC-rel, dominated by negative_signed_offset (15x) — internal jumps
- **결론**: ⭐⭐⭐ **text output handler 확정**. 13 opcode(0~0xc)가 공유. 한 frame당 (screen_ptr → text draw → sound paired helper → sound trigger) 사이클을 3회까지 수행 — line break 별 multi-line 텍스트 처리 추정.

저장: `work/h3/scn_common_8ec26_disasm.json`

## 2DR: 6 special SCN opcodes (0x0d~0x12)

각 opcode를 disasm 실행 — 모두 FUN_0008e89e 안의 sub-labels (push prologue 없음, FUN_0008e89e 의 case body).

| opcode | 범위 | size | instr | cmp arms | BL 패턴 | 특징 |
|---|---|---|---|---|---|---|
| **0x0d** | 0x8f110~0x8f31c | 524B | 240 | 1 (cmp #0) | 2× draw_text/screen/helper, 2× sound, 1× ctx(0xff) | common의 축소판 (2-batch) |
| **0x0e** | 0x8f31c~0x8f544 | 552B | 262 | 1 (cmp #0) | 2× screen/helper, 1× draw_text, 1× sound, 1× ctx(0xff) | 1× draw + 1× sound (single line) |
| **0x0f** | 0x8f544~0x8f884 | 832B | 398 | 2 (cmp #0x3b ';', cmp #0) | 2× draw/sound/helper, 3× screen, 2× ctx(0xff, other) | ⭐ **';' 구분자 파서** (text segmentation) |
| **0x10** | 0x8f884~0x8face | 586B | 281 | 2 (cmp #0x3b ';', cmp #0) | 2× sound/screen/ctx, 1× draw/helper | ';' 구분자 + sub-action |
| **0x11** | 0x8face~0x8fc20 | 338B | 157 | **0 (cmp arm 없음)** | 2× sound/screen/helper/draw_text | **pure text emission**, branch 없는 직선 처리 |
| **0x12** | 0x8fc20~0x929e8 | **11720B** | **5593** | **47** | **41× ctx**, 15× screen, ?× draw, 2× sound | ⭐⭐⭐ **거대 sub-interpreter** |

### opcode 0x12 = 거대 sub-interpreter (11.4KB)

- cmp imm 분포: `cmp #0 (25x)`, `cmp #0xff (6x)`, `cmp #0x03 (3x)`, `cmp #0x0c (2x)`, **`cmp #0x89 (2x)` + `cmp #0x8f (2x)`** (= EUC-KR/CP949 한국어 leading byte 영역), `cmp #0x49 ('I')`, `cmp #0x32 ('2')`
- context_getter 41회 호출 — task_struct 필드 다수 참조:
  - `r0=0x9e28` (sound state #1, system-wide most active) ×3
  - `r0=0x9c70` (byte field cluster) ×8 ⭐ dominant
  - `r0=0x18ed` (미식별 field)
  - `r0=0xff` sentinel ×2+
- **추정**: opcode 0x12 = **multi-byte text parser / Korean dialogue interpreter** + state machine. EUC-KR 한글 (0x89XX, 0x8FXX 등 lead byte) 디코드 + ';' 구분자 + 'I'/'2' 같은 형식 토큰. **dialogue 본문 진행 시스템의 핵심**.

저장: `work/h3/scn_op0d_8f110_disasm.json` ~ `work/h3/scn_op12_8fc20_disasm.json` (6개 JSON)

## 2DS: NPC dispatcher JT @ 0xabaa8 (19 entries)

```
case  0..12 (13개) → 0x8c242  (공통 handler)  ⭐
case 13       → 0x8c79c
case 14       → 0x8c990
case 15       → 0x8cbb0
case 16       → 0x8ceac
case 17       → 0x8d0f6
case 18       → 0x8d2e2
```

**SCN dispatcher (FUN_0008e89e @ 0xabc68) 와 완전히 동일한 19→7 구조**.

### NPC common handler 0x8c242 본문 (1370B)

- size: 0x8c242 ~ 0x8c79c = 1370B (658 instr)
- cmp arms (6): `cmp #3 (ble)` + `cmp #0xb (beq)` + `cmp #0xc (bne)` + `cmp #0xb (bgt)` + `cmp #0 (beq)`×2 — **0x8ec26 SCN common과 동일한 4-arm 분기**
- BL 분포:
  - **4× screen_ptr_getter**
  - **4× ?_helper_9fd64**
  - **4× draw_text_sprite** ⭐
  - 3× sound_trigger
  - 2× context_getter (r0=#0xff, r0=other)
- ⭐⭐⭐ **결론**: NPC common handler = SCN common handler의 **거의 1:1 미러**. 4-batch vs 3-batch 차이는 NPC dialogue가 한 줄 더 길게 보이도록 처리하는 정도 — **본질적으로 동일 함수 패밀리**.

저장: `work/h3/npc_common_8c242_disasm.json`

### 통합 아키텍처 결론

```
???_indirect_main_loop
  ├ FUN_0008b2e8  (sister entry / NPC) ──> inline 0x8c19c ─> FUN_0008d5e4  ─JT@0xabaa8─> 0x8c242 (NPC common)
  └ FUN_0008dcd8  (main entry / scene) ──> inline 0x8eb80 ─> FUN_0008ff18  ─JT@0xabc68─> 0x8ec26 (SCN common)
                                                                                 │
                              두 entry 모두 19-opcode set 공유:
                              0x00~0x0c = text output (공통 handler)
                              0x0d~0x12 = special opcodes (각 entry 별 unique)
```

NPC와 scene이 본질적으로 **같은 scripting engine을 호출하지만, 컨텍스트 (caller task_struct + record)가 다르기 때문에 결과적으로 NPC 대화 vs scene 대화로 갈린다**.

## 2DQ: FUN_00041c14 cluster #1 state machine 본문 재분석

### 기본 통계

- 범위: 0x00041c14 ~ 0x00042758 (= 2884B / 2.8KB, 1315 instructions)
- 45 cmp arms (cmp imm 분포: `#0 (24x)` + `#1/#4/#8 (4x each)` + `#6/#7/#9 (2~3x)` + `#16/#2 (1x)`)
- **BL = 16 context_getter + 1 memset_like (FUN_0009fb78)** — ⭐ **NO draw/sound/screen → pure task_struct state logic**

### Cluster #1 (0x9afc~0x9b3c) 참조 분포 (21 LDR sites)

| 필드 | sites | 의미 (추정) |
|---|---|---|
| **0x9b14** | **11** ⭐dominant | main state byte / mode |
| 0x9b01 | 6 | step counter or sub-state |
| 0x9b1c | 4 | sub-state byte |
| 0x9afc | 1 (start) | init/start flag |

### Caller chain

```
FUN_00040fb0  (parent state runner, 3172B / 1524 instr / 35 cmp arms)
  └─ BL @0x40ffe → FUN_00041c14  (child state machine, 2884B / 1315 instr / 45 cmp arms)
                      └─ BL @0x42744 → FUN_00041c6e  (re-entry sub-label, near-end loop)
```

- **FUN_00041c14의 unique BL caller = FUN_00040fb0 +0x4e** (단 1 entry point)
- FUN_00041c6e는 0x42744 (FUN_00041c14 끝 부분) 에서 호출 = **함수 내부 self-loop sub-label**
- FUN_00040fb0의 호출자는 미식별 (별도 추적 필요)

### FUN_00040fb0 본문 (parent runner)

- 범위: 0x00040fb0 ~ 0x00041c14 (3172B / 1524 instr / 35 cmp arms)
- cmp imm 분포: `#0 (12x)` + `#2 (9x)` + `#3 (4x)` + `#1/#9 (3x)` + `#4/#11 (2x)`
- **BL = 18 context_getter + 1 other** — child 와 동일 패턴 (pure state, no graphics/sound)
- 첫 BL @ 0x40fc0 = context_getter (early task_ptr 획득)

### 결론

FUN_00040fb0 + FUN_00041c14는 **2단 paired state machine**으로, cluster #1 (task_struct[0x9afc~0x9b3c]) 의 4개 필드를 read/write 하며 small-immediate 값(0,1,2,3,4,6,7,8,9,11,16) 기반 분기를 수행한다. **0x9b14가 main state byte** (11 read), **0x9b01이 step counter** (6 read), 0x9b1c가 sub-state, 0x9afc가 start flag — 전형적 nested state machine layout.

**graphics/sound BL 부재**가 결정적 특징: 이 state machine은 **gameplay logic 자체** (예: 이벤트 진행, 보스 페이즈 전환, 메뉴 navigation 등) — rendering은 별도 함수 (FUN_000818f0 등) 에 위임.

저장: `work/h3/state_runner_40fb0_disasm.json`, `work/h3/record_disp_41c14_disasm.json` (기존)

## Round 37 종합 진척

### ✅ 검증 추가

1. **SCN common handler 0x8ec26 = text output** 확정 — Round 36 가설(draw + sound + screen 페어) 본문에서 정확히 검증
2. **NPC + SCN dispatcher = 통합 scripting engine** 확정 — 19-opcode set + common handler 패턴 1:1 미러
3. **opcode 0x12 = 11.4KB Korean dialogue sub-interpreter** — EUC-KR (0x89/0x8f) + ASCII (';', 'I', '2') multi-byte parser
4. **cluster #1 state machine** = **FUN_00040fb0 + FUN_00041c14 + FUN_00041c6e** 3단 함수, pure state (no graphics/sound)
5. **FUN_00040fb0 신규 함수 발견** (3.1KB parent runner)

### ⭐ 다음 라운드(38) 권장 작업

| 우선 | 작업 | 명령 / 메모 |
|---|---|---|
| ⭐⭐⭐ **2EA** | opcode 0x12 (11.4KB) 의 47 cmp arms 본문 디코드 — EUC-KR 한글 디코드 path 정확히 풀기 | `disasm_subsystem_func.py 0x8fc20 0x929e8 --label scn_op12_full` (이미 실행됨, JSON에 47 arms 위치 전부 포함) |
| ⭐⭐ **2EB** | FUN_00040fb0 의 18 context_getter 사이트 + 35 cmp arms 분포에서 cluster #1과 별도 task_struct 필드 식별 | parent runner의 state machine 의미 |
| ⭐⭐ **2EC** | FUN_00040fb0 의 unique BL caller 추적 (`tools/recon/find_callers_41c14.py` 확장) | parent runner가 시스템 어디서 호출되는지 — entity update loop 진입 의심 |
| ⭐ **2ED** | NPC 6 special opcodes (0x8c79c/0x8c990/0x8cbb0/0x8ceac/0x8d0f6/0x8d2e2) 본문 디코드 — SCN 6 special과 차이 있는지 | NPC 전용 opcode 의미 |
| ⭐ **2EE** | opcode 0x12 의 EUC-KR pattern: 0x89/0x8f 직후 byte range 확인 (CP949 한글 lead+trail) | dialogue rendering의 정확한 인코딩 |

### 도구 산출

- `tools/recon/analyze_41c14_cluster1.py` (new) — cluster #1 LDR sites + arm/BL 종합
- `tools/recon/analyze_41c14_arms.py` (new) — arm 분포 + cluster 컨텍스트
- `tools/recon/find_callers_41c14.py` (new) — Thumb-2 BL caller 역추적 (재사용 가능)
- `tools/recon/find_function_containing.py` (new) — push prologue 역검색으로 caller 함수 식별

## 핸드오프 — 다음 세션 시작 시

1. 본 문서 + Round 36 의 [`ghidra-cluster-and-scn-jt-2026-05-11.md`](ghidra-cluster-and-scn-jt-2026-05-11.md) 읽기
2. `work/h3/scn_op12_8fc20_disasm.json` 의 47 arms 위치 + 41 context_getter 사이트 확인 — opcode 0x12 의 47 arms를 EUC-KR (0x89/0x8f) / ASCII (';','I','2') / sentinel (0xff) / state (0x00~0x0c) 4 카테고리로 분류하면 dialogue interpreter의 핵심 케이스 풀이 가능
3. cluster #1 state machine 의 의미 = **gameplay event progression** 가설 → FUN_00040fb0의 caller 추적이 결정적
