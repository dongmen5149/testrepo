# Hero5 Quest cond_type 의미 RE (Round 60)

> 2026-05-18 — `tools/recon/disasm_h5_questcheck_dispatch.py` + `disasm_h5_quest_handlers.py` 산출.
> Round 59 [mission_quest_types.md](mission_quest_types.md) 의 후속 — QuestCheck inner BL 추적 결과.

## QuestCheck dispatch 구조 (@ 0xd3acc)

`QuestMgr::QuestCheck(this, event_code, sub_arg, val1, val2)` 는 활성 quest 전체를 순회하며 각 quest 의 3 phase1 objective 와 비교. 핵심 dispatch 는 cond_type 의 값에 따라 5-way 분기 (jumptable):

```
0xd3ca4: ldrb     r1, [r6, #0x114]    ← read cond_type byte (phase1 byte 0)
0xd3cac: asr      r2, r2, #0x18       ← sign-extend
0xd3cb0: cmp      r2, #0x10           ← r2 > 16 인지
0xd3cb4: ble      #0xd3f04            ← ≤ 16 면 default 핸들러로
0xd3cb8: sub      r2, r2, #0x11       ← r2 = cond_type - 17
0xd3cbc: cmp      r2, #3
0xd3cc0: addls    pc, pc, r2, lsl #2  ← 17/18/19/20 jumptable
                                          ↓
        case 17 → 0xd3e98 (monster kill)
        case 18 → 0xd3e58 (quest switch)
        case 19 → 0xd3cd8 (monster grade?)
        case 20 → 0xd3ddc (money)
```

## cond_type 별 의미 (확정)

| cond_type | 빈도 | handler | 의미 | sub_flag / value |
|---:|---:|---|---|---|
| **13** | 8 | 0xd3f04 (default) | **Item bag count (variant A)** — bag 에 보유 중인 (cat, idx) 아이템 갯수 ≥ value 인가 | sub_flag = item index, value = required count |
| **14** | 38 | 0xd3f04 (default) | **Item bag count (variant B)** — same handler as 13, 다른 design code | 동일 |
| **17** | 7 | 0xd3e98 | **Monster kill** — Monster::onDie 에서 `QuestCheck(qm, 0x11, monster_id, 1, 1)` 호출. progress 변수 [+0x69c] 와 target [+0x6b0] 비교 | sub_flag = monster_id, value = kill count |
| **18** | 0 | 0xd3e58 | **Quest switch state** — Event_QuestSwitch 에서 `QuestCheck(qm, 0x12, switch_state, 1, 1)` 호출. `[this + 0x288 + objective_id]` 가 0 아닌지 확인 | (데이터에 없음 — reward type 18 = exp 와 혼동 주의) |
| **19** | 0 | 0xd3cd8 | **Monster grade check** — `[r2, #0x22d]` 로 monster grade 비교 | (데이터에 없음) |
| **20** | 0 | 0xd3ddc | **Money** — HERO::GetBagItemPtr + 0x9f5a4 호출 (gold 조회 추정) | (데이터에 없음) |
| 255 | 400 | — | **Unused** (placeholder) | — |

### 13 vs 14 의 차이

둘 다 0xd3f04 default handler 를 공유 — code 상으로는 **동일한 처리**:

```
ldr r0, [bag context]
bl  #0x890c8                ; HERO::GetBagItemPtr
ldrsb r2, [r3, +0xb]        ; cached objective sub_flag (item idx)
ldrsb r1, [r3, +8]          ; cached objective cat (item category)
bl  #0x9f77c                ; BagItem::GetBagItemTotalBunchCount(bag, cat, idx)
ldr r3, [+0x6b0]            ; target count
cmp r0, r3                  ; bag_count vs target
bge → success path
```

`+0x6a8` 와 `+0x6ab` 가 cached objective (cat, idx) — LoadQuestData 시 phase1 의 byte 들이 여기로 복사됨.

**13 vs 14 의 design 의미는 미해석** — 동일 handler 라 data 분류만 다름.
가설: 14 = "drop pickup 인지", 13 = "specific quest 아이템 인지". 혹은 11 (8건) = 1차 quest 아이템, 14 (38건) = 일반 collection (R56 sample 의 "이삭줍기 type_14 sub=31 v=4" 가 collection 패턴 일치).

> 정확히 구분하려면 quest_NN.dat 의 cond_type 13 인 8 quest 의 sample text 분석 필요 (Round 61+).

## QuestCheck event_code (arg1) 출처

| event_code | 호출 위치 | 의미 |
|---:|---|---|
| **0x11 (17)** | `monster_load.c:6245` (Monster::onDie) | mob 사망 — sub_arg = monster_id |
| **0x12 (18)** | `interpreter_core.c:2894` (EventProc::Event_QuestSwitch) | scn opcode 의 QuestSwitch 처리 |
| **0xff (255)** | `hero_char.c:13691` (HERO::TakeItem) | wildcard — 아이템 획득/삭제 후 전체 re-evaluation |

> event_code 가 quest data 의 cond_type 와 매칭되는 항목만 active 가 됨. 0xff 는 모든 objective 재평가 (default handler 가 매번 bag count 조회).

## 게임 동작 흐름

### 사냥 quest (cond_type 17):
1. mob 사망 → `Monster::onDie` 호출
2. `QuestCheck(qm, 0x11, monster_id, 1, 1)` 트리거
3. 활성 quest 의 objective 중 cond_type=17 인 것만 검사
4. objective 의 cached monster_id (+0x6ab) 와 event_arg2 (monster_id) 일치 시 progress (+0x69c) +1
5. progress >= target (+0x6b0) 면 success path (QuestSetStatus 호출)

### 수집 quest (cond_type 13/14):
1. 아이템 획득 → `HERO::TakeItem` 호출
2. 인라인 (cat, idx) 비교 후 `QuestCheck(qm, 0xff, 0xff, 0, 0)` 트리거
3. 활성 quest 의 objective 전체 재평가 (cond_type ≤ 16 default 분기)
4. `HERO::GetBagItemPtr` + `BagItem::GetBagItemTotalBunchCount(bag, cat, idx)` 호출
5. bag count >= target 면 success path

### Quest switch (cond_type 18):
1. scn opcode 가 `Event_QuestSwitch(switch_id, state)` 호출
2. `QuestCheck(qm, 0x12, switch_state, 1, 1)` 트리거
3. objective 의 cached switch_id (+0x6ab) 에서 `[this + 0x288 + id]` 읽어 state ≠ 0 확인

## Reward type 매핑 (Round 56 sweep + Round 60 RE 결합)

| reward_type | 빈도 | 의미 |
|---:|---:|---|
| 17 | 16 | **Money** (golddust) — same code table as cond_type |
| 18 | 128 | **EXP** (experience) — `QuestRewardData` 가 직접 처리 |
| 15 | 15 | **Item reward** (item index) — Round 56 가설 그대로 |
| 11 | 3 | 미해석 (rare) |
| 12 | 1 | 미해석 (rare) |
| 6 | 1 | 미해석 (rare) |
| 10 | 1 | 미해석 (rare) |
| 14 | 1 | 미해석 (cond 가 38개인 점과 대조) |
| 255 | 287 | Unused |

> 11/12/6/10 등 미해석 reward types 는 `QuestMgr::QuestRewardData` (0xd3...) 디스어셈블로 풀이 가능 — Round 61+ 대상.

## 마이그레이션 영향 (Godot quest_system.gd)

기존 quest_system.gd 의 `reward_label` 가 17/18 만 처리 — 다음 라벨 추가 가능:

```gdscript
# Round 60 RE 결과 — cond_type 정확 라벨
const COND_TYPE_ITEM_HOLD_A := 13         # item bag count (variant A, 8 quests)
const COND_TYPE_ITEM_HOLD_B := 14         # item bag count (variant B, 38 quests)
const COND_TYPE_MONSTER_KILL := 17        # kill N of monster_id
const COND_TYPE_QUEST_SWITCH := 18        # quest switch state == required
# const COND_TYPE_MONSTER_GRADE := 19     # (데이터 없음)
# const COND_TYPE_MONEY := 20             # (데이터 없음)

func objective_label(obj: Dictionary) -> String:
    var t = int(obj.get("type", 255))
    var s = int(obj.get("sub", 0))
    var v = int(obj.get("value", 0))
    match t:
        13, 14: return "[수집] 아이템 #%d × %d개 보유" % [s, v]
        17:     return "[사냥] 몬스터 #%d × %d 처치" % [s, v]
        18:     return "[퀘스트 스위치] slot %d = state %d" % [s, v]
    return "(미해석 cond_type %d)" % t
```

## 참고

- `tools/recon/disasm_h5_questcheck_dispatch.py` — cond_type LDRB 위치 + 0xd3cb0 jumptable 확정
- `tools/recon/disasm_h5_quest_handlers.py` — 5 handler 블록 디스어셈블
- `tools/recon/disasm_h5_questcheck_inner.py` — inner BL 식별 (`QuestSetStatus`, `GetBagItemPtr`)
- `work/h5/analysis/monster_load.c:6245` — Monster::onDie 의 QuestCheck(0x11) 호출
- `work/h5/analysis/interpreter_core.c:2894` — Event_QuestSwitch 의 QuestCheck(0x12) 호출
- `work/h5/analysis/hero_char.c:13691` — HERO::TakeItem 의 QuestCheck(0xff) wildcard 호출
