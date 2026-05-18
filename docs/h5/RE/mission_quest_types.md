# Hero5 Mission / Quest type 의미 RE (Round 59)

> 2026-05-18 — `tools/recon/disasm_h5_mission_quest.py` + `disasm_h5_questcheck.py` 산출

`work/h5/extracted/lib/armeabi/libHeroesLore5.so` (ARM mode, base VA=0) 의 22개 함수 주소·심볼·CMP imm 패턴을 capstone 디스어셈블로 추출. Round 56 (Quest cond_type 14/13/17) + Round 58 (mission_type 0-5/255) 의 가설을 일부 확인·정정한 결과.

## 함수 주소 (libHeroesLore5.so)

| 주소 | 크기 | 심볼 |
|---:|---:|---|
| 0x089f10 | 156B | `Mission::HuntingCounting(monster_id, type)` |
| 0x089ff0 | 16B | `Mission::QuestCompleteCounting(qid)` |
| 0x08a000 | 16B | `Mission::BossCompleteCounting` |
| 0x08a330 | 204B | `Mission::CompleteMission(mid)` |
| 0x08a3fc | 496B | `Mission::CheckStatistics` |
| 0x08a5ec | 256B | `Mission::CheckQuestComplete` |
| 0x08a6ec | 516B | `Mission::CheckMonsterHunting` |
| 0x08a8f0 | 372B | `Mission::CheckCollection` |
| 0x08aa64 | 112B | `Mission::CheckSpiritSkillAll` |
| 0x08ab10 | 252B | `Mission::CheckMissionRank` |
| 0x08ac0c | 236B | `Mission::CheckOrbCombine(arg)` |
| 0x08acf8 | 268B | `Mission::CheckMissionMix(a, b)` |
| 0x08ae04 | 196B | `Mission::CheckMissionRefine` |
| 0x08aec8 | 204B | `Mission::CheckBattleUseItem(a)` |
| 0x08af94 | 340B | `Mission::CheckMissionPlaytime` |
| 0x08b0e8 | 196B | `Mission::CheckMissionHeroDie` |
| 0x08b1ac | 212B | `Mission::CheckMissionMoney` |
| 0x08b280 | 96B | `Mission::CheckMission99Level` |
| 0x08b2e0 | 292B | `Mission::CheckMissionSetItem` |
| 0x08b73c | 460B | `Mission::LoadMissionTable` |
| 0x0d3acc | 1492B | `QuestMgr::QuestCheck(a,b,c,d)` |
| 0x0d40a0 | 72B | `QuestMgr::Quest_GetOffset` |
| 0x0d40e8 | 1188B | `QuestMgr::LoadQuestData` |

## Mission `mission_type` 매핑 (확정)

`CheckMission*` 함수의 메인 루프가 mission table 을 순회하며 `[record + 4]` (mission_type) 와 비교하는 CMP imm 으로 type 의 의미를 추론.

| type | 빈도 | 의미 | 핵심 evidence | sub_type 역할 |
|---:|---:|---|---|---|
| **0** | 20 | **사냥 (Monster hunt)** | `CheckMonsterHunting` 의 `CMP #0` + loop body. `HuntingCounting` 가 매 mob kill 시 호출 | monster_id (sub_flag) |
| **1** | 5 | **특수 처치 (Boss/event kill)** | `HuntingCounting` 내부 `CMP r3, #1` 분기 (type=1 → boss 카운터 [r0,+0x118] 증가). `BossCompleteCounting` 가 `this[0x22c]==3` (boss flag) 일 때 호출 | enemy_id |
| **2** | 22 | **세트 아이템 수집** | `CheckMissionSetItem` 의 `LDRSB [r0,#4]; CMP r3, #2` (Round 58 가설 확인) | slot (5/6/7/8 = helmet/boots/accessory_1/_2), sub_flag = item_idx |
| **3** | 47 | **누적 도전** (subtype dispatch) | `CheckMissionRefine/Mix/Money/Playtime/HeroDie/OrbCombine` 모두 `CMP #3` 사용 + 그 후 `[r0,#5]` (sub_type) 추가 비교 | sub_type 으로 sub-dispatch (아래 참조) |
| **4** | 5 | **카테고리 수집** | `CheckCollection` 의 `CMP #4` (Round 58 가설 확인) | sub_type = item category (1=무기, 2=방어, 3=장신구) |
| **5** | 5 | **달성 과제 (Rank)** | `CheckMissionRank` 의 `CMP #5` (Round 58 가설 확인). `QuestCompleteCounting` 가 quest 완료 시 cap 99 카운터 증가 | rank threshold |
| **255** | 1 | **튜토리얼 (placeholder)** | 첫 quest "여행자" — 모든 필드 0xFF, target_count=255 (special-cased) | — |

### type 3 누적 도전 — sub_type 매핑

`CheckMission*` 함수가 type=3 매칭 후 `LDRSB [r0,#5]` (sub_type) 으로 추가 분기:

| sub_type | 의미 | Check 함수 |
|---:|---|---|
| **1** | Hero die (사망 카운트) | `CheckMissionHeroDie` 의 `CMP #1` |
| **2** | Playtime (플레이 시간) | `CheckMissionPlaytime` 의 `CMP #2` |
| **4** | Battle item use (포션 등 사용) | `CheckBattleUseItem` 의 `CMP #4` |
| **6** | Refine (강화 카운트) | `CheckMissionRefine` 의 `LDRSB [r0,#5]; CMP #6` |
| **8** | Level/Money 같은 generic threshold (e.g. "모험의 시작" mt=3 st=8) | (CheckMissionMoney/99Level 의 generic check) |
| **0xa(10)** | Orb combine (오브 합성) | `CheckOrbCombine` 의 `CMP #0xa` |

> 미해석 sub_type: 0/3/5/7/9 등은 데이터상 존재 안 하거나 추가 RE 필요.

## QuestMgr `cond_type` / `reward_type` 코드 (부분)

Round 56 의 h5_test_quest.py sweep:
- cond_type 분포: 255(400) / 14(38) / 13(8) / 17(7)
- reward_type 분포: 255(287) / 18=exp(128) / 17=money(16) / 15(15) / 11(3) / 12(1) / 6(1) / 10(1) / 14(1)

**핵심 발견**: cond_type 와 reward_type 는 **같은 코드 테이블**을 공유.
- 17 = money (reward 16건) — cond 측 7건은 "돈 X 보유" 가설
- 18 = exp (reward 128건) — cond 측 0건 (자동 누적, 명시 안 함)
- 14 = ? (cond 38건, reward 1건) — **most common cond**. item 획득 / 특정 NPC 대화 가설
- 13 = ? (cond 8건) — visit 가설
- 15 = item reward (reward 15건) — item 지급
- 6/10/11/12 = 미해석 (rare)

**QuestMgr::QuestCheck dispatch** (@ 0xd3acc, 1492B):
- `CMP r2, #0x10; BLE #0xd3f04` — case 가 ≤ 16 이면 분기 (≥17 는 default)
- `CMP r2, #3; ADDLS pc, pc, r2, lsl #2` — r2 ≤ 3 일 때 jumptable dispatch (case 0/1/2/3)
- LDRB top frequency: `+0x698` (6 reads), `+0x114` (2 reads — phase1 시작!), `+0x6ab`
- 상위 dispatch 는 r2 ≤ 16 만 처리 → cond_type 14/13/17 은 inner BL 에서 처리 가능성

> cond_type 14/13/17 의 정확한 의미는 QuestCheck 의 inner BL (`#0xd1df8` × 3 calls, `#0x890c8` × 2) 추적이 필요. Round 59 범위 외.

## 게임 흐름 → mission 트리거 (in-game flow)

`monster_load.c:6273` 에서 발견된 mob 사망 hook:

```c
if (this[0x27e] == (Monster)0x0) {
    Mission::HuntingCounting(mission_ptr, monster_id, monster_type);
}
if (this[0x22c] == (Monster)0x3) {  // boss
    Mission::BossCompleteCounting(mission_ptr);
}
```

- `this[0x2dc]` = `monster_id`
- `this[0x22c]` = `monster_type` (`3` = boss)
- `this[0x27e] == 0` = 정상 처치 (도주/사라짐 아님)

`HuntingCounting` 내부 카운터:
- `this[+0x64]` = 누적 일반 kill (총 처치 수)
- `this[+0x65]` = monster_id 별 kill (per-mob)
- `this[+0x118]` = boss 처치 수 (`type==1` 일 때만)
- `this[+0x68]` = quest 완료 수 (cap 99 — `QuestCompleteCounting` 가 증가)

## 마이그레이션 영향 (Godot mission_system.gd)

Round 58 의 7 event API + 8 event-to-type 매핑은 RE 결과로 거의 정확:

| event | 원래 가설 | RE 확인 | 정정 사항 |
|---|---|---|---|
| `monster_kill` | type {0, 1} | ✓ | type 1 은 boss 만 (this[0x22c]==3) — 일반 mob 은 type 0 만 |
| `item_obtained` | type {2, 4} | ✓ | 정확 |
| `refine_done` | type 3 | type 3 + sub_type 6 ✓ | sub_type 6 추가 필터 |
| `orb_combine` | type 3 | type 3 + sub_type 10 ✓ | sub_type 10 추가 필터 |
| `mix_done` | type 3 | (sub_type 미해석) | 검증 필요 |
| `playtime` | type 3 | type 3 + sub_type 2 ✓ | sub_type 2 추가 필터 |
| `money` | type 3 | (sub_type 미해석) | 검증 필요 |
| `quest_done` | type 5 | ✓ | QuestCompleteCounting 가 별도 카운터 |

mission_system.gd 의 EVENT_TO_MISSION_TYPES 를 (type, sub_type) 튜플로 정밀화 가능 → Round 59 패치 대상.

## 참고

- `tools/recon/disasm_h5_mission_quest.py` — 22 함수 디스어셈블 + CMP imm 추출 스크립트
- `tools/recon/disasm_h5_questcheck.py` — QuestCheck 의 jumptable + LDRB 분석
- `work/h5/analysis/monster_load.c:6273-6280` — Mission hook in mob death
- `work/h5/analysis/hero_char.c:11197` — Mission::CheckMission99Level 호출 (레벨업 시)
- `work/h5/analysis/hero_char.c:7345` — Mission::CheckBattleUseItem 호출 (포션 사용 시)
