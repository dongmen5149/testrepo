# Hero5 Monster AI 시스템

> Round 44 (2026-05-17) — Monster AI 12 함수 disasm + token-based bytecode VM 식별.
> Round 45 (2026-05-17) — AI_def 데이터원 식별 (`/c/mon/<id>_ai` × **48 파일**) + EnemyAI struct layout + decoder.
> Ai_onAction = 13 opcode interpreter, IsTriggerEqual = 13 trigger 평가 함수.

## 1. 핵심 발견: token-based bytecode VM

Monster AI 는 **SCN opcode 시스템과 동일한 패턴** — Tokenizer 가 byte stream 을 읽고
opcode handler 가 dispatch. AI 정의는 데이터 파일 (Monster+0x288 의 AI_def_ptr) 로
저장되어 있어 디자이너가 monster 별 행동을 byte code 로 작성.

```
Monster::Ai_Process (entry, frame 당 1회)
├── BATTLER::IsStunFlag → if stunned, return
├── Ai_stateCheck (Monster+0x2c3 byte) — state machine update
├── ActionCheck — 행동 가능 여부 검증
├── Monster+0x2b4 cooldown 감소 (default 9 frames)
└── Ai_Action — 메인 dispatch (13-state machine)
    │
    └── if state allows action:
        ├── Ai_setActionList — load action list 첫 entry from AI_def
        └── Ai_doActionList — 토큰 stream 실행
            └── 각 token → Ai_onAction(opcode)
                └── 13 opcode handler (state mutations)
```

## 2. Monster struct AI 영역 (offset map)

`Monster::Ai_SetPtr / Ai_FreePtr` 가 관리하는 AI 영역:

| offset | size | 의미 |
|---:|---:|---|
| +0x288 | ptr | **AI_def_ptr** (AI 정의 데이터: +0x68=offset_table, +0x6c=action_list_table) |
| +0x28c | ptr | trigger_data 영역 ptr (IsTriggerEqual r3 source) |
| +0x290 | ptr | **Tokenizer** 객체 ptr (byte stream cursor) |
| +0x294 | u8 | current_action_idx (0xff = 종료) |
| +0x295 | u8 | next_action_idx (Ai_setActionList 가 load) |
| +0x297 | s8 | **current_opcode** (Ai_doActionList 가 Token_GetByte 후 저장) |
| +0x29f | u8 | trigger #1 one-shot flag |
| +0x2a8..+0x2ab | 4 B | **opcode operand buffer** (Token_GetData 결과) |
| +0x2b1 | u8 | action counter |
| +0x2b2 | u8 | list_active flag |
| +0x2b4 | u16 | action_cooldown (default 9 frames, Ai_Process 가 감소) |
| +0x2b6 | u8 | trigger #13 one-shot flag |
| +0x2be | u8 | trigger #11 one-shot flag |
| +0x2c2 | u8 | opcode 12 결과 — animation/motion override |
| +0x2c3 | u8 | Ai_stateCheck 의 입력 state byte |
| +0x2c4 | s8 | action_type (Ai_Action jumptable + opcode 0/1 가 set, 0=none, 1=combat) |
| +0x2c5 | u8 | sub_action_id (opcode 2) |
| +0x2c6 | u8 | secondary action data (opcode 0/1) |
| +0x2c7 | u8 | conditional state (opcode 3) |
| +0x2c8 | s8 | action timer (Ai_Action substate 0 가 감소) |
| +0x2c9..+0x2cb | 3 B | **skill slot** (opcode 4: skill_id, target_type, range) |
| +0x2cc..+0x2cf | 4 B | secondary skill params (opcode 5) |
| +0x2d0 | u8 | action_running flag (Ai_doActionList 진입 조건) |
| +0x297 (re-purpose 가능) | | Ai_Action 의 sub-state (jumptable index 0..12) |
| +0x303..+0x304 | 2 B | opcode 6 결과 |
| +0x305..+0x307 | 3 B | opcode 7 결과 |
| +0x308..+0x309 | 2 B | opcode 8 결과 |
| +0x30a..+0x30b | 2 B | **next_skill_id pair** (opcode 9 — Ai_Action 의 skill_use path 가 +0x30a 사용) |
| +0x315 | u8 | skill_disable_flag (Ai_Action 가 != 0 면 skill 사용 차단) |

## 3. Ai_onAction VM opcodes (13개)

| op | data | 효과 |
|---:|---:|---|
| 0 | 2 byte | `+0x2a8 → +0x2c4 (action_type)`, `+0x2a9 → +0x2c6`. action_type=1 이면 SetMonMotion(motion=1) — **WALK** |
| 1 | 2 byte | 동일 set + Rand(0,99) < +0x2a9 시 SetMonMotion(motion=5) — **chance walk** |
| 2 | 1 byte | `+0x2a8 → +0x2c5` — sub-action id set |
| 3 | 1 byte | `+0x2c7 == 0 일 때만 +0x2a8 → +0x2c7` — **first-time-only set** |
| 4 | 3 byte | `+0x2a8/+0x2a9/+0x2aa → +0x2c9/+0x2ca/+0x2cb` — **SKILL slot** (skill_id, target, range) |
| 5 | 4 byte | `+0x2a8..+0x2ab → +0x2cc/+0x2cd/+0x2cf/+0x2ce` — secondary skill params |
| 6 | 2 byte | `+0x2a8/+0x2a9 → +0x303/+0x304` |
| 7 | 3 byte | `+0x2a8..+0x2aa → +0x305/+0x306/+0x307` |
| 8 | 2 byte | `+0x2a8/+0x2a9 → +0x308/+0x309` |
| 9 | 2 byte | `+0x2a8/+0x2a9 → +0x30a/+0x30b` — **next_skill_id** (Ai_Action substate 8 에서 사용) |
| 10 | 1 byte | (skip — token 1 byte 소비만) |
| 11 | variable | Token_GetByte → N → Token_GetData(N bytes) — **variable-length data block** |
| 12 | 1 byte | `+0x2a8 → +0x2c2` — animation override |

## 4. Ai_Action sub-state machine (13 entries)

Monster+0x297 가 sub-state index (0..12). Action_type (Monster+0x2c4) 가 0 이면 SetTargetPoint 후 재진입.

| state | 핸들러 | 의미 |
|---:|---:|---|
| 0 | 0xc11ac | **timer decrement** (Monster+0x2c8 감소, 0 도달 시 hero 방향 추적) |
| 1 | 0xc1254 | move/chase 처리 |
| 2 | 0xc1288 | |
| 3 | 0xc1470 | |
| 4 | 0xc1338 | |
| 5 | 0xc13d8 | |
| 6 | 0xc12b8 | |
| 7 | 0xc12e0 | |
| 8 | 0xc10e4 | **SKILL USE** — IsAttackAble + IsAbleSkill(Monster+0x30a) → HeroTurnDirection → SkillUsed(+0x2c9) → SetCoolTime |
| 9 | 0xc1324 | |
| 10 | 0xc10d8 | (no-op / exit) |
| 11 | 0xc10dc | (no-op / exit) |
| 12 | 0xc11a0 | GetMotion + exit |

## 5. IsTriggerEqual — 13 trigger 평가 함수 (1320B)

AI 가 "조건이 만족하면 action list 전환" 하는 데 사용. Monster::ActionOfTrigger
(140B) 가 이를 호출.

| trigger | 핸들러 | 의미 |
|---:|---:|---|
| 0 | 0xbd2f0 | always false (default no-trigger) |
| 1 | 0xbd31c | `Monster+0x29f` 0 → 1 (**한 번만 발화** trigger) |
| 2 | 0xbd334 | **IRect 위치 검사** (큰 코드 영역 — visibility/range check) |
| 3 | 0xbd4e4 | |
| 4 | 0xbd504 | |
| 5 | 0xbd58c | |
| 6 | 0xbd2f0 | always false |
| 7 | 0xbd5d0 | |
| 8 | 0xbd674 | |
| 9 | 0xbd694 | |
| 10 | 0xbd6b4 | |
| 11 | 0xbd2d4 | `Monster+0x2be` 1 → 0 (one-shot consume) |
| 12 | 0xbd5b0 | |
| 13 | 0xbd2fc | `Monster+0x2b6` 1 → 0 (one-shot consume) |

(Trigger 2 = IRect 검사가 가장 큰 핸들러 — hero 위치 vs monster 시야 범위 비교)

## 6. AI 정의 데이터 (Monster+0x288)

`Ai_def` struct (정확한 type 미식별, +0x68/+0x6c 만 접근 패턴 확인):

| offset | 의미 |
|---:|---|
| +0x68 | offset_table — `u8[current_action_idx]` = action def offset |
| +0x6c | action_list_table — base + offset = action def 시작 위치 |

action def layout:
- byte 0 = (skipped by Ai_setActionList)
- byte 1 = next_action_id (Monster+0x295 에 load)
- byte 2.. = **token stream** (Tokenizer 에 SetOffset)

각 token = opcode byte + N operand bytes (opcode 별 stride 표 § 3 참조).

## 7. AI 정의 데이터 origin — **확정 (Round 45)**

`Map::MonsterAdd` (0xb5814) → `EnemyAI::EnemyAI(ai_type_id)` (0x6a8e8) →
`EnemyAI::LoadData(ai_type_id)` (0x6a62c, 700B) 가 `/c/mon/<id>_ai` 파일 로드.

VFS 에 **48 개 AI 파일** (`c/mon/0_ai` ~ `c/mon/63_ai`, gap 있음). 크기 31~305 byte
(avg 110.5B). DES 미적용 (3/48 만 8의 배수 — plain).

`Monster+0x288 = EnemyAI*` (120 byte heap alloc). EnemyAI 생성자가 ai_type_id 받음.
ai_type_id 는 `Monster+0x22e` (Round 34 의 setEnemyData 로 enemy_*.dat 에서 set).

### EnemyAI 파일 layout (확정)

| offset | size | 의미 |
|---:|---:|---|
| +0 | u8 | trigger_count (n_t) |
| +1..n_t | n_t × u8 | trigger code list (IsTriggerEqual 의 13 trigger id) |
| ... | n_t × u8 | handler size list (각 trigger 의 trigger_data_block 내 size) |
| ... | sum(handlers) | trigger_data_block (trigger 별 추가 데이터) |
| ... | u16 (LE) | action_count (n_a, low byte 만 사용) |
| ... | n_a × u8 | action_lookup_1 |
| ... | n_a × u8 | action_lookup_2 |
| ... | n_a × u16 | action_lookup_3 (u16 array) |
| ... | u16 (LE) | trigger_stream_size (low byte 만 사용) |
| ... | n_ts × u8 | **trigger byte stream** (Tokenizer #1 = Monster+0x28c) |
| ... | u8 | action_list_count (n_l) |
| ... | n_l × u8 | action_list_lookup_1 |
| ... | n_l × u8 | **action_list_offset_table** (AI_setActionList 가 사용) |
| ... | n_l × u8 | action_list_lookup_3 |
| ... | u16 (LE, s16 사실은) | action_stream_size (n_as) |
| ... | n_as × u8 | **action byte stream** (Tokenizer #2 = Monster+0x290, 13 opcode VM) |

### EnemyAI struct (120B) layout

| offset | 의미 |
|---:|---|
| +0x00..+0x07 | vtable + ? |
| +0x24 | trigger_count |
| +0x25..+0x25+n_t | trigger codes |
| +0x2f..+0x2f+n_t | handler bytes |
| +0x39..+0x39+n_t | handler offsets (계산된 cumulative sum) |
| +0x43 | total trigger_data size |
| +0x44 | action_count (n_a) |
| +0x48 | action_lookup_1 ptr |
| +0x4c | action_lookup_2 ptr |
| +0x50 | action_lookup_3 ptr (u16 array, n_a*2 bytes) |
| +0x54 | trigger_data_block ptr |
| +0x58 | trigger_stream_size (u8) |
| +0x5c | trigger_stream ptr — **Tokenizer #1 data** |
| +0x60 | action_list_count (s8) |
| +0x64 | action_list_lookup_1 ptr |
| +0x68 | **action_list_offset_table ptr** — AI_setActionList 사용 |
| +0x6c | action_list_lookup_3 ptr |
| +0x70 | action_stream_size (s32) |
| +0x74 | action_stream ptr — **Tokenizer #2 data** |

### Tokenizer 매핑 (Ai_SetPtr 0xbdb3c)

```
TokenizerC1(size=AI_def+0x58, ptr=AI_def+0x5c) → Monster+0x28c  (trigger eval)
TokenizerC1(size=AI_def+0x70, ptr=AI_def+0x74) → Monster+0x290  (action exec)
```

### Decoder

`tools/converter/decode_h5_monsterai.py` (Round 45 신규):
- 48 AI 파일 일괄 파싱 + 100% file 소비 검증
- action stream 은 Round 44 의 13 opcode 로 disasm
- trigger stream 은 raw hex (trigger handler 의미 매핑은 다음 라운드)
- 산출: `apps/hero5-godot/assets/gamedata/monster_ai.json`

### 통계 (48 AI 파일, 524 action opcodes 추출)

| opcode | 출현 |
|---|---:|
| WALK (0) | 176 |
| CHANCE_WALK (1) | 110 |
| SET_SUB (2) | 72 |
| SET_STATE_FIRST (3) | 59 |
| SET_303 (6) | 34 |
| SET_305 (7) | 18 |
| SKILL_PARAM (5) | 16 |
| SKILL_SET (4) | 12 |
| SET_308 (8) | 8 |
| ANIM_OVERRIDE (12) | 3 |
| VAR_DATA (11) | 1 |
| unknown (skipped, default handler returns 0) | ~17 |

WALK + CHANCE_WALK = 286/524 (55%) — 대부분 monster 가 walking 중심 AI.

## 8. 다음 라운드 작업

1. ~~**Ai_SetPtr / Ai_Initialize 분석** — AI_def 데이터원 식별~~ ✅ Round 45 완료 (`/c/mon/<id>_ai`)
2. **trigger handler 의미 매핑** — trigger_stream 의 opcode + operand 디스어셈블 (현재 raw hex)
3. **state machine 핸들러 정밀 분석** — Ai_Action sub-state 1-9 각각의 동작 (move/chase/skill cast)
4. **trigger 2 (IRect) 정밀 분석** — visibility/range check 의 정확한 거리/각도 공식
5. **trigger 3-12 각각 의미 식별**
6. **enemy_g 의 4 skill block** (Round 33) 과 AI opcode 4 (skill slot) 연동 검증

## 9. 산출

- `work/h5/analysis/ai_action_disasm.txt` (533 lines, Ai_Action 2136B) [R44]
- `work/h5/analysis/ai_onaction_disasm.txt` (~180 lines, Ai_onAction 704B) [R44]
- `work/h5/analysis/istriggerequal_disasm.txt` (~330 lines, IsTriggerEqual 1320B) [R44]
- `work/h5/analysis/enemyai_loaddata_disasm.txt` (~175 lines, EnemyAI::LoadData 700B) [R45]
- `tools/converter/decode_h5_monsterai.py` [R45]
- `apps/hero5-godot/assets/gamedata/monster_ai.json` (48 AI defs + disasm) [R45]
- `docs/h5/MONSTER_AI.md` (이 문서)
