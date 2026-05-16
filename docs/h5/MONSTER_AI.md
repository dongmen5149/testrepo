# Hero5 Monster AI 시스템

> Round 44 (2026-05-17) — Monster AI 12 함수 disasm + token-based bytecode VM 식별.
> Round 45 (2026-05-17) — AI_def 데이터원 식별 (`/c/mon/<id>_ai` × **48 파일**) + EnemyAI struct layout + decoder.
> Round 46 (2026-05-17) — Trigger stream layout 식별 + 13 trigger operand 매핑 + decoder 확장. 543 trigger entry **100% parse (0 unknown)**.
> Round 47 (2026-05-17) — Ai_Action 13 sub-state 정밀 분석 + 5 opcode → 6 state skill dispatch matrix.
> **Round 48 (2026-05-17) — Godot GDScript VM 구현** (`monster_ai.gd` autoload + battle_system hook).
> Ai_onAction = 13 opcode interpreter, IsTriggerEqual = 13 trigger 평가 함수, ActionOfTrigger = stream driver.

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

## 4. Ai_Action sub-state machine (13 entries) — **확정 (Round 47)**

Monster+0x297 가 sub-state index (0..12). Action_type (Monster+0x2c4) 가 0 이면 SetTargetPoint 후 재진입.

| state | 핸들러 | 의미 (분석 결과) |
|---:|---:|---|
| 0 | 0xc11ac | **CHASE_TIMER**: Monster+0x2c8 timer decrement. 0 도달 + Monster+0x2c4==1 시 hero 위치 비교 (Fast_Distance vs Monster+0x2c6 시야범위) → 시야 안이면 ImmadiatelyCheck(8) 로 SKILL state 진입 |
| 1 | 0xc1254 | **TURN_DIRECTION**: Monster+0x2c5 (target_dir mode 0-3 + default) 에 따라 dir 설정. mode 0/2 = lookup 테이블 / mode 1 = 다른 lookup / mode 3 = flip 180° / default = HeroTurnDirection (face hero) |
| 2 | 0xc1288 | **STATE_COUNTDOWN**: Monster+0x2c7 (countdown timer) 감소. 0 도달 + motion==1 시 state 0 로 재진입 (대기/looping) |
| 3 | 0xc1470 | **SKILL_USE_WITH_TARGETING**: GetMotion + IsAttackAble + IsAbleSkill(Monster+0x2c9). Monster+0x2ca (dir mode) 0-4 jumptable: 0=current dir / 1=face hero / 2=set dir 2 / 3=set dir 3 / 4=set dir 0. 그 후 IRect 충돌 검사 + SkillUsed + SetCoolTime |
| 4 | 0xc1338 | **SET_ATTACK_MOTION**: IsAttackAble + skill_disable (Monster+0x315) check. Monster+0x2cc → 사용 skill_id. Monster+0x2d8 + skill_id*offset 에서 skill data (motion+dir) 가져와 SetAttackMotion. SetCoolTime. Monster+0x297=-1, +0x2b8=0 |
| 5 | 0xc13d8 | **SKILL_CAST_DIR304**: Monster+0x304 → Monster+0x2c9 (skill). GetDir → +0x2ca. IsAbleSkill → SkillUsed + SetCoolTime |
| 6 | 0xc12b8 | **READY_ATTACK_305**: GetMotion + IsAttackAble. Monster+0x305 → state 4 fallthrough (SET_ATTACK_MOTION path) |
| 7 | 0xc12e0 | **READY_ATTACK_308**: GetMotion + IsAttackAble. Monster+0x308 → Monster+0x2c9. IsAbleSkill 후 SkillUsed/CoolTime |
| 8 | 0xc10e4 | **SKILL_USE_30A** (Round 44 식별): IsAttackAble + skill_disable check. Monster+0x30a → Monster+0x2c9 (next_skill_id, opcode 9 가 set). HeroTurnDirection → SetDir → SkillUsed + SetCoolTime. Monster+0x297=-1 |
| 9 | 0xc1324 | **SKILL_END**: Monster+0x2c3 = 1, SkillEnd() 호출 (skill 종료 정리) |
| 10 | 0xc10d8 | no-op (default fall-through to exit) |
| 11 | 0xc10dc | no-op (default fall-through to exit) |
| 12 | 0xc11a0 | **GET_MOTION_EXIT**: GetMotion 호출 후 exit (motion 상태 갱신만) |

**공통 패턴**:
- GetMotion==0 (idle) 조건 필수 — motion 중이면 wait 분기로 회피
- IsAttackAble == 1 조건으로 skill 사용 게이트
- Monster+0x315 (skill_disable flag) != 0 이면 차단
- 모든 SKILL_USE state 가 `Monster+0x297 = -1` 로 sub-state 리셋 (다음 frame 새 dispatch)
- `b 0xc118c` = 함수 exit (sp 복원 + pop)

**skill 사용 path 종합**:
- state 3 = 일반 skill (Monster+0x2c9 직접 사용, dir control)
- state 4 = 동적 skill (Monster+0x2cc → +0x2c9, motion+dir from struct lookup)
- state 5 = +0x304 source skill
- state 6 = +0x305 trigger → state 4
- state 7 = +0x308 source skill
- state 8 = +0x30a source skill (opcode 9 의 next_skill_id)

5 개 skill source 가 다른 opcode/state path 와 매핑:
- opcode 4 (SKILL_SET, 3B) → Monster+0x2c9..+0x2cb → state 3
- opcode 5 (SKILL_PARAM, 4B) → Monster+0x2cc..+0x2cf → state 4
- opcode 6 (SET_303, 2B) → Monster+0x303/+0x304 → state 5
- opcode 7 (SET_305, 3B) → Monster+0x305..+0x307 → state 6
- opcode 8 (SET_308, 2B) → Monster+0x308/+0x309 → state 7
- opcode 9 (NEXT_SKILL, 2B) → Monster+0x30a/+0x30b → state 8

## 5. IsTriggerEqual — 13 trigger 평가 함수 (1320B) — **확정 (Round 46)**

AI 가 "조건이 만족하면 action list 전환" 하는 데 사용. `Monster::ActionOfTrigger`
(140B, 0xbd7a0) 가 driver — trigger stream 을 walk 하며 매 entry 의 trigger_code
를 IsTriggerEqual 에 전달.

**Trigger stream entry layout** (per entry):
```
[trigger_code u8][operand bytes 0-1][action_id u8]
```

trigger 가 fire (return 1) 하면 `action_id` 를 `Monster+0x294` 에 set 하고
`ImmadiatelyInit` 호출. fail 면 다음 entry 로 advance.

| trigger | 핸들러 | operand | 의미 |
|---:|---:|---:|---|
| 0 | 0xbd31c | 0 | **SET_29F**: `Monster+0x29f` == 0 시 1로 set + return 1 (one-shot trigger) |
| 1 | 0xbd334 | **1** | **VISIBILITY_RECT**: operand = IRect index (×40 = base offset into Monster+0x2d8 IRect 배열). hero 위치 vs IRect intersect 검사 |
| 2 | 0xbd4e4 | 0 | **CONSUME_2BC**: `Monster+0x2bc` == 1 시 0으로 set + return 1 (one-shot consume) |
| 3 | 0xbd504 | 0 | **ALL_MONSTERS_DEAD**: 모든 monster Mon_isDie 확인 + Monster+0x2c1 set |
| 4 | 0xbd58c | 0 | **SELF_DEAD**: Mon_isDie + Monster+0x2ba set |
| 5 | 0xbd2f0 (no-op in IsTriggerEqual) | 0 | **ALWAYS_GOTO**: ActionOfTrigger 가 특수 처리 — IsTriggerEqual 안 부르고 즉시 action_id 읽어 jump (unconditional) |
| 6 | 0xbd5d0 | **1** | **TUTORIAL_FLAG**: operand vs gv+0x130/0x131/0x132 (3 tutorial flag) 비교 |
| 7 | 0xbd674 | 0 | **CONSUME_2BF** |
| 8 | 0xbd694 | 0 | **CONSUME_2B9** |
| 9 | 0xbd6b4 | 0 | **CONSUME_2BD** |
| 10 | 0xbd2d4 | 0 | **CONSUME_2BE** |
| 11 | 0xbd5b0 | 0 | **CONSUME_2B7** |
| 12 | 0xbd2fc | 0 | **CONSUME_2B6** |

### Trigger entry stride
- code 1, 6: 3 bytes (code + 1 operand + action_id)
- code 5: 2 bytes (no operand, action_id 만)
- 나머지: 2 bytes

### 통계 (48 AI 파일, 543 trigger entries 추출)

| trigger | 출현 | % |
|---|---:|---:|
| VISIBILITY_RECT (1) | 196 | 36% |
| ALWAYS_GOTO (5) | 195 | 36% |
| CONSUME_2B6 (12) | 76 | 14% |
| SET_29F (0) | 35 | 6% |
| CONSUME_2B7 (11) | 33 | 6% |
| CONSUME_2BD (9) | 7 | 1% |
| CONSUME_2BF (7) | 1 | <1% |

VISIBILITY_RECT + ALWAYS_GOTO = 72% — 대부분 "기본 idle action 으로 가다가
hero 가 시야 범위에 들어오면 combat action 으로 전환" 패턴.

**0 unknown, 0 incomplete** entries — operand size 매핑 완전 검증.

### ActionOfTrigger 동작 (driver, 0xbd7a0, 140B)

```
ActionOfTrigger(this, trigger_code, &offset):
  *offset += 1  ; advance past trigger_code byte
  if trigger_code == 5:                          ; ALWAYS_GOTO special path
    action_id = trigger_stream[*offset]
    Monster+0x294 = action_id
    *offset += 1
    ImmadiatelyInit()
    return 1
  result = IsTriggerEqual(this, trigger_code, &offset)
  if result == 0:
    *offset += 1  ; skip action_id (no match)
    return 0
  else:
    action_id = trigger_stream[*offset]
    Monster+0x294 = action_id
    *offset += 1
    ImmadiatelyInit()
    return 1
```

Trigger stream 은 보통 "default fallback" entry (code 5 = ALWAYS_GOTO) 로 끝나서
어떤 조건도 안 맞을 때 default action 으로 가도록 설계됨.

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
2. ~~**trigger handler 의미 매핑** — trigger_stream disasm~~ ✅ Round 46 완료 (543 entries 100% parse)
3. ~~**state machine 핸들러 정밀 분석** — Ai_Action sub-state 1-9~~ ✅ Round 47 완료 (13 sub-state 의미 전부 식별)
4. **trigger 1 (VISIBILITY_RECT) IRect 영역 정밀 분석** — Monster+0x2d8 의 5개 IRect 배열 의미 (현재는 거리/각도 공식만 식별)
5. **enemy_g 의 4 skill block** (Round 33) 과 AI opcode 4 (skill slot) 연동 검증
6. **action_lookup_3 (u16 array)** + action_list_offset_table 정밀 의미 — n_a/n_l/byte 어떻게 dispatch 되는지
7. **Monster AI Godot 통합** — 48 AI defs JSON + 13 opcode VM → GDScript battle loop

**Monster AI 분석 완전 종료** — 데이터원 / VM (action+trigger opcode) / 상태 머신
모두 매핑. Godot 구현으로 이전 완료 (Round 48).

## 10. Godot 구현 (Round 48 신규)

`apps/hero5-godot/scripts/core/monster_ai.gd` (autoload, 약 270 line):

```gdscript
# create runtime for monster
var ai_state = MonsterAI.create_runtime(monster_node, ai_type_id)

# per-frame entry
MonsterAI.process(ai_state)   # cooldown + Ai_Action

# trigger evaluation (action 전환 시도)
MonsterAI.step_trigger_list(ai_state)

# action stream 1 step
MonsterAI.step_action_list(ai_state)
```

**구성**:
- `MonsterAIState` class — Monster 구조체 +0x288..+0x315 영역 매핑
- `_load_ai_defs()` — `monster_ai.json` 234KB res:// loader
- `create_runtime(host, ai_type_id)` — 48 AI defs 중 선택
- `process(s)` — 매 frame entry (stun → cooldown → Ai_Action)
- `step_action_list(s)` — Ai_doActionList (action stream 1 step)
- `_on_action(s, op, stream)` — 13 opcode interpreter (operand size table)
- `step_trigger_list(s)` — ActionOfTrigger (trigger stream walker)
- `_is_trigger_equal(s, code, operand)` — 13 trigger handler

`battle_system.gd` hook: `_ai_runtime` field + `start_battle` 에서 create_runtime
호출 + `_ai_pick_skill()` helper (트리거 검사 + action stream 진행 후 skill_id 추천).

## 9. 산출

- `work/h5/analysis/ai_action_disasm.txt` (533 lines, Ai_Action 2136B) [R44]
- `work/h5/analysis/ai_onaction_disasm.txt` (~180 lines, Ai_onAction 704B) [R44]
- `work/h5/analysis/istriggerequal_disasm.txt` (~330 lines, IsTriggerEqual 1320B) [R44]
- `work/h5/analysis/enemyai_loaddata_disasm.txt` (~175 lines, EnemyAI::LoadData 700B) [R45]
- `tools/converter/decode_h5_monsterai.py` [R45, R46 trigger disasm 추가]
- `apps/hero5-godot/assets/gamedata/monster_ai.json` (48 AI defs + action+trigger disasm) [R45+R46]
- `docs/h5/MONSTER_AI.md` (이 문서)
