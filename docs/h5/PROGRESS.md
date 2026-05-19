# Hero5 (영웅서기5) 진행 상황

> Hero3/4와 다른 트랙. 기존 Android APK 가 존재하지만 32-bit 전용이라 현대 폰 미지원.
> 전략 = **A. 자산 추출 + 엔진 재구현** (Hero3/4 인프라 재사용 가능).

## 📜 라운드 요약 (Round 1-87)

| 라운드 그룹 | 주요 성과 |
|---|---|
| **R1-5: 인프라** | VFS 풀기 + 자산 이름 99.7% 복원 + sprite/palette/text 디코더 + DES 변종 해독 (`S1[3][10]=2`) + Formula VM 186 공식 디스어셈블 + Godot 4 스캐폴드 |
| **R6-11: Formula VM + 캐릭터** | gv+0x1474 sub-struct 111 fields + V[58..167] 라벨 매핑 + 시각효과 + V[111..116] secondary stat (근접명중/장거리명중/회피/방패방어/크리티컬) + V[60..63] base STR/DEX/CON/INT 정정 |
| **R12-19: Item 시스템** | V[122..126] buff slot + V[151..155] magic stat + ItemBase formula + EquipItemInfo struct + LoadItemTable csv layout + 19 카테고리 |
| **R20-28: Item 메커닉** | SkillBook/CashItem/Refine/Orb/Mix 시스템 정밀 매핑. 강화 stat 식 (id=35/36) + 5 socket orb mechanism + mix_book recipe + NPC blacksmith |
| **R29-36: Monster + Drop** | droptable.dat (252 entries) + enemy_g (Map HP/skills) + enemy_*.dat 3 difficulty × 166 records + 4 element 시스템 + V[151]/V[152] magic stat pair |
| **R37-40: Mission + Quest** | Mission 105 + 13 Check* 함수 + mission_list.dat 매핑. Quest 151 × 3 difficulty (save slot 가설 정정 → difficulty scaling) + 모든 게임 데이터 파일 종류 식별 |
| **R41-43: Save 시스템** | 8 save 파일 종류 + SaveAll dispatch + load cross-check (H_*.sav 21/21 + SL_*.sav 24 offset 일치, 0 mismatch) + source struct field 라벨링. **`file[0] = level*10+class_id` packing 발견** |
| **R44-47: Monster AI (분석)** | 12 AI 함수 + token-based bytecode VM 식별. 13 action opcode + 13 trigger + Ai_Action 13 sub-state 완전 매핑. **48 AI defs (`/c/mon/<id>_ai`) decoder**. 543 trigger entries 100% parse |
| **R48-49: Godot 통합 (구현 시작)** | Monster AI Godot VM (`monster_ai.gd` autoload + battle_system hook) + Save binary 직렬화 (524B HERO + SL header) + Python round-trip 검증 |
| **R50: AI Action sub-state 완성** | `_ai_action` 13 sub-state 모두 정밀 dispatch (state 0-12) + host CHAR interface stub (battle_system 13 method) + `h5_test_monster_ai.py` Python simulator. **48/48 AI VM round-trip 통과** (674 action steps + 19 cast). operand 부족 시 graceful stop |
| **R51: 인벤토리 items.json 정확 통합** | game_data.gd 에 `item_lookup` / `item_matches_filter` / `class_mask_allows` / `equip_slot_for_kind` 추가 (1360 records unique-name index). status_panel.gd 의 한국어 substring 매칭 → items.json kind 기반 정확 분류 + tooltip 풍부 (tier/class_label/level_limit/refine_count/skill info/potion effect). class_mask + level_limit 장비 검증. `h5_test_items_lookup.py` — tier 분포 (170/248/9/362) 검증 통과 |
| **R52: 강화(Refine) UI** | `refine_panel.gd` + `.tscn` 신규 — Round 17/26 의 ApplyItemRefine 5-case (큰성공/성공/재료소비/lock/destroy) + `refined_stat = base + sub_count` Godot 구현. GameState 에 `refine_state` dict + `equipment_bonus` refine 보너스 합산. demo.gd R 키 toggle. `h5_test_refine.py` — prob 합 1000 / 단조성 / 10000회 시뮬 (max 2.5% / locked 65.1% / destroyed 32.5%) 검증 |
| **R53: 합성(Mix) UI** | `mix_panel.gd` + `.tscn` 신규 — Round 25/28 의 ApplySpecialMix mechanism. `GameData.mix_recipes()` (116 entries) + `parse_recipe()` (ing×3 + result + success_rate). GameState `inventory_count(name)` / `consume_inventory(name, n)` helper (장착된 슬롯 보호 + refine_state 동기 정리). 제작가능 필터 + 재료 부족 시 disabled. demo.gd K 키. `h5_test_mix.py` — 116 recipe 100% parse / 한국어 이름 0 miss / success_rate 평균 60.6% / 카테고리 분포 검증 |
| **R54: Orb socket UI** | `orb_panel.gd` + `.tscn` 신규 — Round 17/26 의 ApplyOrbCombine mechanism. GameState `orb_state` dict + 4 helper (get_orb_sockets/add_orb_to_socket/remove_orb_from_socket/clear_orbs). EquipItemInfo +0x168 (count) / +0x169..+0x16d (5 socket bytes) 매핑. `equipment_bonus` 에 orb bonus 합산 + 5-socket fill 시 2x rule. GameData `orb_records()` (53 orbs, slot_12) / `orb_bonus_for` / `orb_group` / `orb_name`. demo.gd O 키. `h5_test_orb.py` — 53 orb 0 miss / encoding 5/5 fill / remove 3/3 / 2x rule (12→32) 검증 |
| **R55: NPC 대장간(Blacksmith) UI** | `blacksmith_panel.gd` + `.tscn` 신규 — Round 28/32 의 ApplyNormalMix mechanism (csv slot_15 mix_book 과 별개 데이터원). GameData `smith_table(sid)` / `smith_all()` / `parse_smith_recipe()` — smithtable.json (smith_0/1/2.dat, 288 entries 중 named 231) 파서. 탭(기본/세트/고급/전체) + 제작가능 필터 + 재료 부족 시 disabled. demo.gd J 키. `h5_test_blacksmith.py` — 231 recipe 0 miss / sr 분포 {75,100} / smith_0 단순(2.74 ing) vs smith_1 복합(2.98 ing) 가설 검증. Round 32 의 "모두 75%" 추측은 부분 표본 — 실제로 정제류는 100%. **부수 수정**: 누락됐던 items.json `_meta.category_dispatch` + recipe 필드 재생성 (decode_h5_item.py 재실행). mix/orb/items_lookup 테스트도 동시 회복 |
| **R56: Quest 패널 강화** | `quest_panel.gd/.tscn` 전면 개편 — quests.json 새 schema (`by_difficulty.q0/q1/q2 × 151`) 활용. quest_system.gd 에 `current_difficulty` + `quest_objectives/quest_rewards/quest_description/quest_category/reward_label/objective_label` 추가. 자동 보상 지급이 quests.json 의 rewards 사용 (이전 rewards.json fallback 대체). UI 에 detail card (제목/카테고리/설명/목표/보상/진척) + 난이도 토글. `h5_test_quest.py` — 3×151 entries / name_match 147/151 / category 분포 / cond_type 분포 (top: 14,13,17) / reward 분포 (exp 128, money 16, type_15 item 15) / **difficulty scaling 단조성 100% (141/141)**. 부수 발견: Round 40 의 cond_type 17/18 추측은 부분 표본 — 실제 sub_type 14/13/17 다수 존재 + 미해석 reward type 6/10-15 (item 보상 추정) |
| **R57: SkillBook 학습 UI** | `skill_book_panel.gd` + `.tscn` 신규 — Round 21 의 HERO::IfLearnSkill mechanism Godot 구현. GameState 에 `skill_levels: Dictionary` + `can_learn_skill_book/learn_skill_book/get_skill_level` 추가. GameData 에 `skill_book_slot_for_class((cid/2)+16)` / `skill_books_for_class` / `skill_book_detail` (resolve_skill_desc 호출). 학습 조건 4종 검증 (book.class_id 일치 / required_level / 기존 LV < book LV / 인벤 보유). 인벤토리 보유 책만 필터 + 상세 카드 (스킬/필요레벨/설명). demo.gd L 키. `h5_test_skill_book.py` — slot_16=95 / slot_17=98 / class별 분포 (W=48, R=47, G=49, K=49) / Sorcerer 0 (stub 검증) / 5 case 시뮬 (학습/재학습 거부/다른 클래스 거부/레벨 부족/upgrade) 통과. **부수 발견**: Round 21 의 required_level 가설은 보수적 — 실제 데이터는 max 92 까지 (Lv.7 책은 60-90+ 요구) |
| **R58: Mission 진척 UI** | `mission_system.gd` 신규 autoload + `mission_panel.gd/.tscn` 신규 — Round 37/38 의 mission.json (105 missions) 활용. 7 event API (monster_kill/item_obtained/refine_done/orb_combine/mix_done/playtime/money/quest_done) → 8 event-to-type 매핑. `bump_progress(event_kind, key, amount)` 가 일치 sub_conditions 누적 + target_count 충족 시 자동 완료 (`mission_completed` signal). UI: 4-탭 (전체/진행중/완료/미시작) + detail card (제목/타입 라벨/조건별 진척). 기존 panel hook 6개 연결: refine.refined/mix.mixed/orb.orb_changed (신규 signal)/blacksmith.crafted/battle.battle_completed/Quest.quest_completed. demo.gd `,` 키. `h5_test_mission.py` — type 분포 검증 ({0:20, 1:5, 2:22, 3:47, 4:5, 5:5, 255:1}) + 3 case 시뮬 (사냥 30회 / 누적 100회 / 세트 4종 수집). **부수 식별**: mission_type 의미 — 0/1=사냥, 2=세트, 3=누적, 4=카테고리, 5=달성, 255=튜토리얼 (느슨한 매핑, RE 시 정정) |
| **R59: Mission/Quest type 의미 RE** | `disasm_h5_mission_quest.py` + `disasm_h5_questcheck.py` 신규 — libHeroesLore5.so 의 23 함수(Mission 21 + QuestMgr 3) 주소·심볼·CMP imm 추출. **Round 58 mission_type 가설 확정**: type 0/1=사냥(monster_id), 2=세트수집(slot 5-8), 3=누적도전+sub_type 분기, 4=카테고리수집, 5=달성과제(랭크). type 3 의 sub_type 정밀 매핑: 1=HeroDie, 2=Playtime, 4=BattleUseItem, 6=Refine, 10=OrbCombine. mission_system.gd 에 `EVENT_TO_SUB_TYPES` dict 추가 — bump_progress 가 type 3 매칭 시 sub_type 도 필터. `docs/h5/RE/mission_quest_types.md` 신규 RE 문서 (23 함수 주소 표 + 매핑 근거). `h5_test_re_types.py` — ELF 심볼 cross-verify (8/8 ✓) + sub_type 분포 (Refine 5/OrbCombine 13/Playtime 3/HeroDie 3/BattleUseItem 4건). **Quest cond_type 14/13/17**은 QuestCheck inner BL 추적 필요 (Round 60+) |
| **R60: Quest cond_type 의미 RE** | `disasm_h5_questcheck_inner.py` / `_dispatch.py` / `_handlers.py` 신규 — QuestCheck (@0xd3acc) 내부 dispatch 추적. **5-way jumptable 발견** (`0xd3cb0..0xd3cd0`): cond_type ≤16 → default `0xd3f04`, 17/18/19/20 → 전용 handler. cond_type 매핑 확정: 13/14 (8/38건) = bag item count (default handler 가 GetBagItemPtr + GetBagItemTotalBunchCount 호출), 17 (7건) = monster kill (sub=monster_id), 18 = quest switch (data 에 없음 — reward 측만). 외부 event_code: 0x11=Monster::onDie, 0x12=Event_QuestSwitch, 0xff=HERO::TakeItem wildcard. reward type 15 (item) sub = item_idx 확인. quest_system.gd 에 `COND_TYPE_*` 상수 + objective_label 정확 라벨 (`[수집A/B] 아이템 #X × N`, `[사냥] 몬스터 #X × N`, `[퀘스트 스위치]`). `docs/h5/RE/quest_cond_types.md` 신규 RE 문서. `h5_test_cond_types.py` — cond/reward 분포 매칭 + cond_type 17 monster_id range (0-200) + 13/14 design 차이 (avg 9.6 vs 5.7) + 5 reward type 15 sample (sub=item_idx ✓) |
| **R61: character.gd host CHAR interface 구현** | `character.gd` 에 Round 50 의 host CHAR interface 17 method (13 base + 4 추가) 실 구현. battle_system 의 turn-based stub (`get_motion()→0`, `fast_distance_to_hero()→0`) 대체 — character 가 monster 일 때 map 좌표 기반 정확한 값 반환. 신규 fields: `is_hero` flag, `target_hero` ref, `hp/max_hp/dead/stunned`, `_cooldowns`, `_forced_host_motion`. 신규 method: `is_die/get_motion/is_attack_able/is_able_skill/get_dir/set_dir/hero_turn_direction/fast_distance_to_hero/set_attack_motion/ai_cast_skill/set_cool_time/skill_end/ai_check_irect_hit/ai_check_visibility/ai_all_dead/ai_tutorial_flag/is_stunned/take_damage/cooldown_tick`. signal `ai_skill_cast(skill_id, source)` — demo 가 receive. demo.gd `spawn_monster(monster_id, pos, ai_type_id)` helper 추가 (enemy_stats 의 HP 반영 + MonsterAI runtime meta 저장). HOST_MOTION_* 상수 (Round 50 원본 motion enum: 0=idle/1=walk/5=run/6=attack/9=die/12=cast). _physics_process 가 is_hero=false 시 input skip + anim 만 진행 (_advance_anim 분리). `h5_test_char_host.py` 신규 — 17 method 시그니처 검증 + monster_ai cross-check + 8 Python 시뮬 (Chebyshev 거리/방향 turn/is_able_skill cd-dead-stunned 케이스 통과) |
| **R62: Monster spawner + AI tick 루프** | demo.gd 에 `_monsters: Array` + `_physics_process` 추가 — 30 fps tick (`AI_TICK_PERIOD = 1.0/30.0`, 원본 `Monster::Ai_Process` 와 일치) 마다 active monster 의 `MonsterAI.process(rt)` + `char.cooldown_tick()` 호출. dead monster 자동 제거 + `Mission.bump_progress(EVENT_MONSTER_KILL, monster_id)` 트리거 (Round 58 의 mission hook 자동 연결). spawn_monster 가 `monster_id` meta 저장 → dead 시 정확한 mission 매칭. KEY_G 바인딩 — hero 주변 ±160/±100 px 위치에 random monster 스폰 + 48 AI defs 중 monster_id%48 매핑 (테스트용). `h5_test_ai_tick.py` 신규 — 11 구조 패턴 검증 + AI_TICK_PERIOD 30fps 확인 + Python 시뮬 (3 monster spawn / 30 frame 후 15 tick / dead 정리 + mission progress / cooldown 30→14→0). UI R51-58 + RE R59-60 + character R61 통합 완료 — Godot 게임 루프 first-pass 가능 |
| R63: Monster ↔ Hero 실 전투 | demo.gd 의 `ai_skill_cast` toast-only handler → `_on_monster_skill_cast(skill_id, source, monster_id)` 실 전투 로직. `enemy_stats.attack × (100 + skill_id × 20)% - defense/2` 데미지 공식 (skill_id 별 multiplier). hero 위에 red damage popup + `GameState.hp` 차감 + state_changed emit. HP=0 시 자동 quick_load(0) (death recovery). 신규 `_hero_attack_nearest()` (SPACE 키) — Chebyshev `ATTACK_RANGE_TILES=2` 내 가장 가까운 monster 찾아 `take_damage(total_attack + 0..7)`. hero 가 monster 향해 방향 전환 (dominant axis). monster 위에 yellow damage popup. dead 전환 시 Round 62 AI tick 루프가 list 정리 + mission 트리거 (자동 chain). `h5_test_ai_combat.py` 신규 — 9 구조 패턴 + Python 시뮬: monster skill 0/5 데미지 차이 (12 vs 32) / 누적 사망 / Chebyshev nearest target / out-of-range skip / 데미지 공식 일관성 |
| R64: monster kill 보상 흐름 | demo.gd `_physics_process` 의 `if c.dead:` 분기에 `_award_kill_reward(monster_node, mid)` 호출 추가 (3 신규 helper). `_award_kill_reward` = `GameData.enemy_stats(mid)` lookup + `_kill_stat_or` (65535 sentinel → default `10+rand%20` exp / `5+rand%50` gold) + `_roll_kill_drops` (battle_system `_roll_drops` 와 동일: 25% × 1-2 item) + `GameState.add_battle_reward(exp, gold)` (level_up signal 자동 트리거) + drop name 별 `inventory.append` + 녹색 `+%dEXP +%dG` damage popup + 파랑 "획득: <item>" toast + state_changed emit. dead 분기에 `Quest.on_enemy_killed(mid)` 도 추가 (battle_system `_finish` 와 동일 트리거). `h5_test_kill_reward.py` 신규 — 9 구조 + sentinel(166/166) + 5-case + drop 1000회 + level_up 시뮬 |
| R65: Quest reward type 6/10/11/12 RE 확정 | `QuestMgr::QuestRewardData` @0xd458c (1552B, ARM mode) 디스어셈블. **reward.type = item category (= items.json slot 번호), reward.sub = idx, reward.value = quantity**. R60 의 type 15="item" 가설을 type 0-16 전체로 일반화 (`ItemTable::NewItemToBagEx` 단일 dispatch). type 17=money/18=exp/19=HP/20=INT. 샘플 검증: type 6=boots "엠프리스", type 10=spirit, type 11=potion×수량, type 12=orb "뇌제의 오브", type 14=quest item "소녀의 사진". quest_system.gd reward_label 가 items.json item_name_at 호출, _grant_reward 가 item type → inventory.append + HP/INT 보상 처리. `h5_test_reward_types.py` — 64/64 in-range + 4 ELF symbol + 11/11 라벨 케이스 |
| R66: battle_system / character 두 host 명세 강화 | R65 SESSION_HANDOFF 의 "13 stub = dead code" 가설 잘못 확인. `start_battle` 가 host=self 로 register → **turn-based 전투 (B 키) 의 합리적 default**. R61 character host (real-time AI tick, G 키) 와 별개 정상 경로 둘 다. 정리: battle_system docstring 강화 + 두 host 비교 표 + is_able_skill 가 실 _cooldowns 검사 + set_cool_time 실 동작 + is_attack_able stunned 추가 + 신규 is_stunned method + monster_ai create_runtime docstring 분기 명세. h5_test_dual_host.py 17/17 + 6 R66 패턴 + 의미 차이 시뮬 + cooldown 동작 |
| **R67: Battle motion enum + CHAR state machine RE 확정** | `CHAR::SetMotion` (@0x4af5c, 56B) + HERO 의 4 Set*Motion 함수 (SetWalk @0x98f6c / SetAttack @0x98870 / SetAttacked @0x98e58 / SetDie @0x98dd8) 정밀 디스어셈블. **R50 의 HOST_MOTION 가설 (walk=1, die=9 등) 잘못 확인**. 실제: walk=motion 3, die=motion 5, attack/attacked=caller가 skill 기반 전달 (variable). **main_state 와 motion 은 별개 시스템**: main_state byte (CHAR::SetMainState) = 게임 액션 분류 (1=walk/2=attack/3=attacked/4=die), motion byte (CHAR::SetMotion → +0x2c) = 스프라이트 anim index. CHAR struct field 확정: +0x2c=motion / +0x2d=dir / +0x2e=frame(u16) / +0xc4=motion_change_flag / +0xc5=prev_frame_low / +0xc6=max_frame_current. helper 함수 6종 (SetMotion/GetMotion/SetMainState/SetDir/GetMaxFrame/SetNextState) 주소 확정. character.gd 에 SO_MAIN_STATE_*/SO_MOTION_* 8 상수 신규 — 기존 HOST_MOTION_* 는 Godot 내부 logical code 로 유지 (monster_ai != 0 검사만 사용, 호환). docs/h5/RE/battle_motion.md 신규 RE 문서 (disasm 코드 + 가설 정정 표 + helper 함수 매핑). h5_test_battle_motion.py — 10 ELF symbol cross-verify + 9 character.gd 패턴 + 9 RE 문서 패턴 + R50 → R67 정정 8 case 통과 |
| **R68: NPC Dialog state machine + DIALOG_INFO struct RE 확정** | `DIALOG_INFO::DialogWindow_Proc` (@0x71b48, 912B) ARM full disasm + jumptable decode. **R67 PASS 1 summary 의 "state byte = +0x29" 가설 잘못 확인** — 실제 main state byte = **+0x2b** (0..7 의 `addls pc, pc, r2, lsl #2` jumptable), +0x29 는 sub-step counter (0..4 animation tick), +0x2d/+0x2f 는 animation curve key A/B. 8 state 의미: 0=INACTIVE / 1·3·6=IDLE_BUSY (return 1) / 2·4=FADE_IN_A/B / 5·7=FADE_HSB_A/B (RestorePal+ChangeHSB). phase data pool struct +0x10..+0x3c (각 phase 12B). `EventProc::Event_DialogWindow` (@0x6eb38, 656B) = 매 frame NPC face + DialogBox + NameBox renderer (`DrawDialogBox`+`DrawTextField`+`GetNpcNameText`+`NameBox`). `EventProc::Event_SituateDialogText` (@0x73030, 600B) = dialog 시작 트리거 (record_base + npc_slot×0x3c, `Interpreter::Strings::getString`+`Graphic::GetWidth/Height` 자동 좌표, +0xdf sub_state 분기로 `SetDialogWindow(1,2)/(4,2)/(6,5)` 호출). 외부 helper 9종 주소·심볼 확정 (`SetDialogWindow` @0x6ab40 / `SetFacePosition` @0x72f54 / `GetNpcNameText` @0x1431a0 / `DrawDialogBox` @0x8245c / `NameBox` @0x82248 / `Strings::getString` @0x9e540 등). dialog_box.gd 에 `DIALOG_STATE_*` 8 상수 + `DIALOG_TRIGGER_*` 3 상수 + `DIALOG_SUBSTEP_FINAL=4` + R68 RE docstring 추가 (typewriter 동작 자체는 logical 매핑만, 동작 보존). `docs/h5/RE/npc_dialog.md` 신규 RE 문서 (struct layout 표 + state 흐름 diagram + helper 표 + R67→R68 정정 표). `tools/h5_test_dialog.py` — 9 ELF symbol cross-verify + 11 disasm pattern 검증 (jumptable + strb + cmp + bl) + 12 RE doc marker + 12 GDScript 상수 통과 |
| **R69: Attack motion dispatch (ChangeAttackMotion + CheckWeaponMotion) RE 확정** | `HERO::ChangeAttackMotion` (@0x91e7c, 340B) + `HERO::CheckWeaponMotion` (@0x8dd58, 256B) ARM full disasm. **R67 PASS 1 의 cmp 0xd/0xe/0x14/0x17 dispatch 가설 정정** — 입력은 skill_type/weapon_kind 아닌 **`CHAR::GetMotion()` 현재 motion 값**. `mov r1, #0x16/0x18/0x26/0xf` = SetMotion 의 새 motion id, `mov r1, #0xa` = KB strength. 분기 키 = **`this->class_id` (HERO+0x22c)**, class 0 (워리어) + 3 (나이트) 만 active. **class 0**: motion 13(0xd)→38(0x26), motion 20(0x14)→22(0x16) — wind-up→hit phase swap. **class 3**: motion 14(0xe)→15(0xf) NULL target / motion 14+target → KB=10+RevengeXY+TurnDir / motion 23(0x17)→24(0x18)+state_1d36==1 시 variable KB=(skill_info[+0x44]-2)*6+20. **호출자 식별** (초기 capstone 검색 0건 → raw ARM bl 디코더로 확정): ChangeAttackMotion ← `HERO::ProcHeroSkill` @0x99278 offset +0x488 (1회, skill hit-frame trigger). CheckWeaponMotion ← **4 클래스 Draw() 메서드 5회** (WARRIOR @0x146af0 / ROGUE @0xd7a18 / KNIGHT @0xaa328 / GUNNER @0x87678 ×2) — SORCERER 제외 (R22 stub 가설 재확인). HERO struct 신규: +0x22c=class_id / +0x1d36=class 3 secondary flag / +0x1fb0=current attack target Monster* / +0x1fea=last knockback_idx. HeroSkillInfo +0x44=knockback_idx (1-base). character.gd 에 `SO_MOTION_WARRIOR_*/KNIGHT_*/WEAPON_*_HIGH` 10 상수 추가 (logical 매핑). `docs/h5/RE/attack_motion_dispatch.md` 신규 RE 문서. `tools/h5_test_attack_motion.py` — 2 ELF symbol + class_id load + class 3 분기 + GetMotion bl 2회 + cmp 0xd/0xe/0x14/0x17 + mov r1 #imm 5종 + SetMotion 4회 + AddEffectKnockBack 2회 + SetRevengeXY 1회 + CharTurnDirection 2회 + caller @0x99700 (offset +0x488 within ProcHeroSkill) + CheckWeaponMotion 5 callers 4 classes + 25 RE doc marker + 10 GDScript 상수 + 4 R69 docstring 통과 |
| **R70: HERO::ProcHeroSkill 골격 RE** | R69 에서 발견한 `HERO::ProcHeroSkill(HeroSkillInfo*)` @0x99278 (7972B 거대 함수) 골격 매핑. 총 **1993 ARM instruction**. **Entry sequence**: 전역 state clear → 3-step attack reset (sub_88f74/88fd4/89034) → **HERO+0x348 + i*0x58 의 59-slot skill array 초기화** (59×88B=5192B, HeroSkillInfo 배열) → NULL guard → class_id 분기 (class 2 GUNNER 별도 path @0x9a564). **2 jumptable 식별**: (1) **@0x9a398, 5-way** — dispatch key = `skill_info[+0x28]` (signed byte, 0..4 skill effect type), case 0=NO_HIT / 1·2=physical / 3·5=magic / 4=heal+buff. (2) **@0x9a8d8, 7-way** — dispatch key = `HERO::GetCurActSkillIdx()` (0..6 active skill slot), case 0/2/4/6 = 기본 공격 (alias), 1=skill A, 3=skill B, 5=skill C, 7=default → **7+1 active skill slot 시스템 확인** (R57 일치). **ChangeAttackMotion 호출 context @ 0x99700**: 직전 Formula::calc(0x6f=111, ...) hit check → result > 0 시 sub_89068 (hit 등록) → ChangeAttackMotion → 직후 *(r5+(-0x190))+0x19c (s16) > 99 면 exit (level cap). **HeroSkillInfo struct 18+ field 매핑**: +0x0a flag / +0x1c/1d mode / +0x28 effect_type(★jumptable1) / +0x29 effect2 / +0x2a formula_arg / +0x30 behavior(8회) / +0x32/34/36/38 4×u16 (primary/secondary value, 각 8회) / +0x3a-3d flags / +0x44 knockback_idx (R69) / +0x48/4a/4c/50 ranges / 88B = 0x58 entry size 일치. **호출 그래프 top 20**: Formula::calc 27회 / GetSpritePtr 22회 / GetExtraDataPtr 22회 / GetCurActSkillIdx 18회 / GetX 14회 / GetY 14회 / GetPivotX 11회 / GetPivotY 11회 / **TargetEffectMgr::NewTargetEffect 11회** (skill VFX) / BATTLER::IncreaseHP 10회 / __divsi3 10회 / UiTargetMonster::SetBattler 9회 / GetTempAtkProPtr 8회 / GetHitType 8회 / GetMotion 7회 / Rand 7회 / IncreaseSP 5회 / IncreaseHiperCount 4회 / ApplyAddEffect 3회 / CheckEffSound_Hit 3회. HERO this fields: +0x22c=class_id (16회) / +0x269 (8회) / +0x294-296 3-byte cluster (skill state machine). `[r5, +-0x190]` ldr 107회 = big_struct base ptr (R71 추적 필요). `docs/h5/RE/proc_hero_skill.md` 신규 RE 문서. `tools/h5_test_proc_hero_skill.py` — 11 ELF symbol + entry pattern (class_id load + class 2 분기 + 59-iter loop) + 2 jumptable + dispatch key load + cmp range + ChangeAttackMotion @ 0x99700 + Formula::calc 27회 + TargetEffectMgr 11회 + IncreaseHP 10회 + GetCurActSkillIdx 18회 + HeroSkillInfo +0x28/+0x30/+0x34/+0x38 ldr + HERO+0x22c 16회 + 26 RE doc marker 통과 |
| **R71: Formula::calc dispatch + r5 base 추적** | R70 ProcHeroSkill 골격 보완. `Formula::calc(int id, CHAR* attacker, CHAR* defender, HeroSkillInfo*, ItemBase*)` (@0x7749c, 172B, 42 instr) 정밀 disasm — **id < 1000 (0x3e8) → calc_pl, < 2000 (0x7d0) → calc_en, ≤ 3007 (0xbb7) → calc_sk, else return 0**. Formula struct: +0x0 calc_en ptr / +0x4 calc_sk ptr / +0x8 calc_pl ptr. **Formula 0x6f (111) / 0x63 (99) = calc_pl 범위지만 production calc_pl 은 0..38 (39 entries) 만 정의 → OOB → result 0 → ble taken → __sub_89068 (hit registered) skip, 그러나 ChangeAttackMotion 은 무조건 호출**. 즉 hit check 자체는 historical artifact (production cut), ChangeAttackMotion 호출 path 는 unaffected. **r5 base 추적**: `add r5, r4, #0x1ec0` @0x993cc + `add r5, r5, #0xc` @0x993dc → **r5 = HERO + 0x1ecc**. 따라서 `[r5, +-0x190]` (107회 ldr) = **HERO + 0x1d3c** (ptr 영역, current cast target Monster* 또는 BATTLER* 추정). 0x99704-10: `ldr r3, [HERO+0x1d3c]; ldrsh r2, [r3, #0x19c]; cmp r2, #0x63` = Monster+0x19c (s16 level) > 99 시 exit = **level cap 99 확정** (R22 max level 92 와 합리적 일치). 다른 r5 base 발견: @0x99454 `add r5, r4, #0x1e00` → r5 = HERO+0x1e04 (path 2, R72 추적). 다음 분석: jumptable 1 의 case path 정밀 / class 2 GUNNER path / TEM 11개 인자 / HERO +0x1d3c vs +0x1fb0 차이. `docs/h5/RE/proc_hero_skill.md` §11 추가 + `tools/h5_test_proc_hero_skill.py` 확장 (Formula::calc 172B size + cmp 0x3e8/0x7d0/0xbb0 + calcByFormula bl + r5 setup A/B + [r5,-0x190] 107회 + level cap 99 + 10 R71 doc markers) 모두 통과 |
| **R72: ProcHeroSkill JT1 case + class 2 GUNNER entry RE** | R70 의 2 jumptable 의 첫 번째 (@0x9a398, 5-way skill_info[+0x28]) **각 case 의 helper 호출 매핑 확정**: **case 0 (NO_HIT @0x99978) = HERO::IncreaseSP(skill_info[+0x4a] s16)** — SP 변경만 / **case 1+2 (@0x9ac68) = BATTLER::AddCurseSkill** (@0x4b134) — curse/debuff / **case 3+5 (@0x9abfc) = BATTLER::AddBuffSkill** (@0x4b198) — buff / **case 4 (@0x9ab98) = HERO::AddStanceSkill** (@0x91d7c) — stance (R70 의 "heal+buff" 가설 정정 → stance 자세 시스템). 모든 case 가 b #0x99978 으로 NO_HIT path 합류 (공통 SP 처리 + class 분기). **공통 패턴**: 2회 Formula::calc(skill_info[+0x3c] formula_id_1, skill_info[+0x3d] formula_id_2) 호출 → results r0/r7 → helper 호출. **case 1+2 special dispatch**: skill_info[+0x3a] 가 0x34 (52) / 0x37 (55) 일 때 default AddCurseSkill 대신 special path (0x9b124 / 0x9b100) — skill table cross-ref 필요. **HeroSkillInfo 신규 6 field 확정**: +0x1c (alternate path flag, R70 "mode" → 명확화), +0x3a (special dispatch byte), **+0x3c (Formula id 1, R70 flag → formula 확정)**, **+0x3d (Formula id 2)**, +0x45 (additional check), **+0x4a (s16 SP cost/heal, R70 range → SP delta)**. **HERO this 추가 fields**: +0x294 (skill state flag), +0x295 (secondary formula id, case 0 path), **+0x269 (GUNNER combo state)**. **class 2 (GUNNER) entry @ 0x9a564**: GetCurActSkillIdx() != 5 → 다른 path, == 5 (5번째 active skill = combo shot 추정) → HERO+0x286/+0x288 halfword + +0x285 byte reset → 0x9a824. **GUNNER damage 공식**: `(combo_state * 0x14 + 0x1e) * X / 100` = `(combo*20+30) * mult / 100` — 매 hit 마다 +20% bonus (combo 1=50%, 2=70%, 3=90%, 4=110%). HERO+0x248 (s16) = ammo/charge counter, skill_info+0x48 (s16) = max combo. **R72 = RE only, Godot 코드 변경 없음**. `docs/h5/RE/proc_hero_skill.md` §12 추가 (case 표 + 공통 패턴 + GUNNER 공식 + R72→R73 잔여) + `tools/h5_test_proc_hero_skill.py` 확장 (case 1+2 AddCurseSkill bl + case 3+5 AddBuffSkill bl + case 4 AddStanceSkill bl + case 0 IncreaseSP bl + skill_info ldrsb +0x1c/+0x3c/+0x3d + ldrsh +0x4a + HERO ldrb +0x294/+0x295/+0x269 + cmp #0x34/#0x37/#0x5000000, **14 R72 doc markers**) 통과 |
| **R73: ProcHeroSkill JT2 4 case + TEM 11 호출 RE** | R70 의 2 jumptable 의 두 번째 (@0x9a8d8, 7-way GetCurActSkillIdx()) **각 case 동작 매핑 확정**: **case 0/2/4/6 (alias @0x99904) = 기본 공격 (auto-attack)** — Formula::calc(formula_id=3, …) → BATTLER::IncreaseHP(damage) + Formula::calc(formula_id=4, …) → HERO::IncreaseSP(SP delta). **Formula 3 = `clamp(V[23], 0, 500)`** (calc_pl[3]) / **Formula 4 = atk×magic×buff%** (calc_pl[4] R5 일치). **case 1/7 (@0x9ad78) = timestop + 기본 공격 chain** — OBJECT::SetTimestopFrame(2) → b #0x99908 (기본 공격 path 합류). **case 3 (@0x9acf8) = class 3 KNIGHT secondary skill** — HERO+0x1d36 (R69 secondary flag)==1 검사 + EquipItem +0x168 orb count (R26) 검사 + array iterate + 기본 공격 합류. **case 5 (@0x9aa18) = shock skill** — skill_info[+0x46] (shock count) > 0 일 때 HERO::NewShockAddEffect(@0x8fc20) + skill_info[+0x34/+0x38] → HERO[+sp[0x50]/+0x1a8] 저장 + **Formula::calc(formula_id = skill_info[+0x30] dynamic)** → BATTLER::IncreaseHP(-damage) + UI 업데이트. R72 의 +0x30 "behavior code" → **dynamic Formula id 확정**. **JT2 합류 흐름**: 모든 case → 결국 기본 공격 Formula 3/4 → HP/SP 변경 (active skill 사용 시 기본 공격 damage 가 base + case 별 special effect 추가). **HeroSkillInfo 신규 4 field**: +0x30 (R72 behavior → dynamic Formula id), +0x46 (shock count), +0x4e (class 3 threshold), +0x48 (max combo). **HERO this 신규**: +0x1a8 (halfword storage for skill_info[+0x38] in case 5). **TargetEffectMgr::NewTargetEffect (@0x62d40) 11 호출 분석**: signature `(this, char a effect_type, int b, HeroSkillInfo*, SPRITE*, char c-f, short s, int g, int h)` — 12 args. **distinct effect_type values: {4, 7, 8}** (r1 immediate, 6/2/1 회) + dynamic (3 회 ip register). 호출 위치 10 확정 (#11 ptr 추적 필요, R74). **R73 = RE only, Godot 코드 변경 없음** (R74+ damage 공식 Godot 정확화 예정). `docs/h5/RE/proc_hero_skill.md` §13 (JT2 case) + §14 (TEM signature + 인자) 추가 + `tools/h5_test_proc_hero_skill.py` 확장 (JT2 기본 공격 mov r1 #3/#4 + BATTLER::IncreaseHP bl + SetTimestopFrame bl + NewShockAddEffect bl + skill_info ldrsb [r6,#0x30/#0x46] + class 3 setup + TEM 11회 호출 + effect_type 4/7/8 distinct, **16 R73 doc markers**) 통과 |
| **R74: Godot battle_system.gd damage 공식 정확화 (GUNNER combo + SKILL SP delta + helper signals)** | R63 임시 공식 (`atk + rand(0..7) - def/2`) 의 R71+R72+R73 발견 통합. **GameState 에 GUNNER combo state 3 변수 추가**: `gunner_combo` (HERO+0x269 대응) + `gunner_max_combo` (default 4, skill_info[+0x48] 대응) + `gunner_ammo` (HERO+0x248 대응). **battle_system.gd SKILL action 보강**: (1) **GUNNER class+skill_id==5 일 때 combo multiplier 적용** — `damage = base * (combo*20 + 30) / 100` (R72 공식, combo 1=50%/2=70%/3=90%/4=110%), combo 도달 시 reset. (2) **Formula 4 부가 호출 (R73 발견)** — `_calc_player_damage(4, ctx, skill_data)` → SP delta 양수 시 `player_mp += sp_delta` (clamp to max_mp). log 메시지에 "+%dSP" 표시. **R72 helper signals 3종 추가**: `curse_applied(target, dispatch_byte, formula_1, formula_2)` (case 1+2) / `buff_applied` (case 3+5) / `stance_applied` (case 4). **`apply_skill_effect(target, effect_type, dispatch, f1, f2, skill_data)` API**: effect_type 별 match → Formula 1/2 평가 후 해당 signal 발화. case 0 (NO_HIT) 는 no-op (이미 sp_delta 처리). R74 = Godot enhancement, monster_ai/UI 측 buff/debuff 시스템 stub (실 통합은 R75+). docstring 에 R72 4 helper 매핑 + R73 +0x4a SP delta + +0x3c/+0x3d formula ids + GUNNER 공식 명시. `tools/h5_test_battle_formula.py` 신규 — GameState 3 변수 + GUNNER multiplier 분기 + (combo*20+30) 공식 + combo reset + Formula 4 SP delta 호출 + player_mp 회복 로직 + 3 signals + apply_skill_effect 5 match case + GUNNER Python 시뮬 (1/2/3/4 = 50/70/90/110%) + 7 R74 docstring markers, 모두 통과. R63/R69/R73 회귀 모두 통과. .so 분석 ~99% 유지, **Godot 실 구현 79-83% → 82-88%** (damage 공식 정확화로 +3-5%p), 출시 78-88% → 80-90%. **🎯 7년 만에 처음으로 ProcHeroSkill 의 active skill 처리 흐름이 Godot 에서 정확히 재현됨** |
| **R75: GUNNER combo UI + skill effect 시스템 통합** | R74 backend 의 frontend + GameData 통합. **GameState 에 active effect Array 3종 추가**: `active_curses` / `active_buffs` / `active_stances` (각 entry = {dispatch, f1, f2, turns}). **`add_active_effect(kind, dispatch, f1, f2, turns=5)`** + **`tick_active_effects()`** (매 turn 만료 처리, R76+ 정확한 turn count 통합). **battle_system 의 _ready()** 에서 R74 의 3 helper signal 을 GameState.add_active_effect 자동 연결 (`_on_curse_applied` 등). **status_panel.gd 의 _apply() 보강** (text-only, .tscn 수정 없음): (1) **lvl_label append**: GUNNER (class_id==2 + gunner_combo > 0) 일 때 `[Combo N/M]` 표시. (2) **gold_label append**: active_curses/buffs/stances 수가 양수일 때 `[저주×N, 버프×M, 자세×K]` 표시. **`GameData.skill_info(class_id, skill_id)` 신규 helper**: R72/R73 의 10 fields 노출 — `effect_type` (+0x28) / `dynamic_formula_id` (+0x30) / `special_dispatch` (+0x3a) / `formula_id_1` (+0x3c) / `formula_id_2` (+0x3d) / `knockback_idx` (+0x44) / `shock_count` (+0x46) / `max_combo` (+0x48) / `sp_delta` (+0x4a) / `knight_threshold` (+0x4e). skill_info struct 의 byte offset 을 stats_u16 index 로 변환 (정확한 매핑은 LoadSkillTable disasm 추가 분석 필요, 현재는 추정). `_stat_at(stats, index, default)` 안전 lookup helper. **battle_system SKILL action 자동 dispatch**: `GameData.skill_info` 호출 → `effect_type` 0 이 아니면 자동 `apply_skill_effect(self, effect_type, dispatch, f1, f2, skill_data)` 호출. log fx_str (`+저주` / `+버프` / `+자세`) 표시. effect_type 0 (NO_HIT) 는 no-op. `tools/h5_test_skill_meta.py` 신규 — GameState 3 Array + add/tick method + battle_system signal 자동 연결 (3 connect + 3 handler) + status_panel GUNNER combo + active effect 라벨 (저주×/버프×/자세×) + GameData.skill_info 10 fields + _stat_at + battle_system 자동 dispatch + log fx_str + R75 docstring markers (4 files) + effect_type → kind dispatch Python 시뮬 (0/1/2/3/4/5/6), 모두 통과. R63/R69/R73/R74 회귀 모두 통과. .so 분석 ~99% 유지, **Godot 실 구현 82-88% → 85-90%** (UI 통합 +3%p), 출시 80-90% → 83-92%. R74 의 backend stub 이 R75 의 frontend+자동 dispatch 로 완성 → active skill effect 시각화 가능 |
| **R87: Spirit (class_5) extra_hex full 의미 매핑** | R83 (Sorcerer) + R84 (raw_bytes 변환) 후속 최종화. **`game_data._ensure_spirit_skills_loaded()` 보강**: R84 stats_u16 24 entries 유지 + **R77 LoadResSkillInfo file layout 정확 sub-rel offset 8 explicit field 추출**: `effect_type` (sub-rel 0x1a) / `dynamic_formula_id` (0x26) / `special_dispatch` (0x2b) / `formula_id_1` (0x2d) / `formula_id_2` (0x2e) / `primary_u16` (0x22 LE) / `secondary_u16` (0x24 LE) / `desc_len` (0x2f). 안전 가드: bytes.size() ≥ 48 일 때만. **`game_data.skill_info(5, skill_id)` 정정**: 이전 stats_u16 추정 매핑 → 이제 `class_id == 5 and rec.has("effect_type")` 분기로 explicit field 직접 반환. 다른 class (0..3) 는 기존 추정 매핑 유지. **Spirit data 분석 결과 (16 record)**: effect_type 분포 **0=5 (NO_HIT base) / 2=9 (curse) / 7=2 (timestop)** — debuff 위주 정령 매직 컨셉 확인. formula_id_1 분포 **57=10 / 0=5 / 59=1** — Formula 57 이 spirit 의 통일 공식. 예시: spirit #0 "거대탄" (effect=0, primary=400 big bomb) / #1 "마법기" (effect=2 curse, dyn_F=116, sd=107, F_1=57, F_2=68) / #7 "매혹기술" (effect=7 timestop, sd=44, F_1=57). **Sorcerer 의 spirit fallback 정확화**: 이전 R83/R84 가 spirit 의 R72 5 critical field 를 default 0 반환 → R87 이후 실 effect_type (curse/timestop/base) + formula_id 동작. battle_system 의 SKILL action 자동 dispatch (R75) 가 spirit 사용 시 정확한 effect 발화 (저주/시간정지/기본). `tools/h5_test_spirit_full_mapping.py` 신규 — R87 docstring + R77 sub-rel 참조 + 8 explicit field 추출 + skill_info class_5 명시 분기 + spirit data 검증 (16 record / effect_type 5+9+2=16 / formula_id_1 10+5+1) + 3 sample 정확 매핑 (거대탄/마법기/매혹기술) + R83/R84 회귀, **9/9 통과**. R82-R86 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 27% → **40%** (Sorcerer 70→85, Spirit R77 mapping 90 신규). 종합 가중평균 78.87% → **80.17% (↑1.30%p)** — **80% 돌파**. Godot 91-94% → **92-95%**. 출시 81% → **82%** |
| **R86: Distribution build preset + BUILD_ANDROID + icon.svg** | G 카테고리 (출시 보완) 의 가장 큰 빈 칸 (Distribution 0%) 채움. **`apps/hero5-godot/export_presets.cfg` 신규 (4669 bytes, 2 preset)**: Debug + Release 완전 형식. **공통**: gradle_build=true, min_sdk=23 (Android 6.0), target_sdk=34 (Android 14), arm64-v8a only (32-bit + x86_64 disabled), package=`kr.eamobile.heroeslore5.remake "Hero5 Remake"`, v0.1.0-alpha, immersive_mode, **11 permissions 모두 false** (싱글 플레이). **Release 차이점**: `runnable=false + compress_native_libraries=true` (R8 + native lib 압축 size 절감). 기존 `.template` 은 단일 preset → R86 cfg 는 2 preset 완전 형식. **`apps/hero5-godot/icon.svg` 신규 (1132 bytes)**: 검 + 별 + "HERO 5" 로고. project.godot 의 `config/icon="res://icon.svg"` 참조 충족 (이전 missing). **`.gitignore` 조정**: 이전 `export_presets.cfg` ignore → R86 commit 허용 (개인 프로젝트), 대신 `*.keystore` 추가 ignore (signing 보안). **`docs/h5/BUILD_ANDROID.md` 신규 (8 섹션)**: 사전 요구사항 (JDK 17/21 + Android SDK 34 + NDK r23c+, JDK 경로 memory reference) → Godot Editor 초기 설정 (Build Template 설치) → Export Preset 설명 → Release Keystore 생성 (keytool 명령) → 빌드 절차 (Debug/Release/adb install) → 검증 (R82-R85 모든 기능 + Sorcerer + GameOver + warp fade) → 알려진 이슈 (SMAF/save round-trip/Sorcerer active skill). `tools/h5_test_export_preset.py` 신규 — configparser INI 파싱 + 2 preset 존재 + gradle_build (min/target sdk) + arm64-v8a only + package/version + 11 permissions false + Release compress_native_libraries=true + immersive_mode + icon.svg + project.godot icon 참조 + .gitignore + BUILD_ANDROID.md 20 marker, **13/13 통과**. R82/R83/R84/R85 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: G 카테고리 35% → **55%** (Distribution 0→80, build doc 90). 종합 가중평균 77.27% → **78.87% (↑1.60%p)**. Godot 91-94% 유지 (G 는 Godot 외). 출시 79% → **81%** |
| **R85: Battle UI fade transition** | R82 SceneRouter + R84 warp_fade 의 자연스러운 후속. E 카테고리 (Scene 통합) 의 마지막 큰 빈 칸인 **Battle transition 50→90%** 채움. **`battle_ui.gd start()` 정정**: 이전 instant `visible = true` 토글 → 이제 `await SceneFaderRef.warp_fade(self, func(): _setup_and_show(monster_id, player_state), 0.25, 0.25)`. 검정 페이드아웃 → mid-callback 에서 `_setup_and_show` (in_combat=true + H5Battle instance + signal 연결 + start_battle + visible=true + enemy sprite) → 페이드인. **중복 진입 guard**: `if visible: return` (B 키 multiple press 안전). **`_setup_and_show(monster_id, player_state)` 신규**: start() 의 mid-callback 으로 분리된 setup logic. **`_on_ended()` 정정**: 이전 popup 끝 → instant `visible = false` → emit → cleanup → 이제 popup → `await warp_fade(self, func(): visible=false; in_combat=false; _battle.queue_free(), 0.25, 0.25)` → emit. **emit 순서 정확**: `battle_completed.emit` 가 fade-out 완료 후 호출 (이전엔 fade 진행 중 emit → demo 가 race condition 가능). **`SceneFaderRef preload`**: battle_ui 가 CanvasLayer 라 autoload 직접 못 받음 → `const SceneFaderRef = preload("res://scripts/ui/scene_fader.gd")`. **시각 효과**: B 키 진입 → 검정 0.25s → battle UI 등장 + monster sprite. 종료 → popup → 검정 0.25s → demo map 복귀 + 보상 popup. `tools/h5_test_battle_fade.py` 신규 — SceneFader preload + start() warp_fade + duplicate guard + _setup_and_show split + setup logic + _on_ended fade-out + emit 순서 (fade 완료 후) + closure arg forward + R84 warp_fade 회귀 + R82/R83 회귀, **8/8 통과**. R82/R83/R84 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 70% → **80%** (Battle transition 50→90 +40, 큰 빈 칸 채움). 종합 가중평균 76.07% → **77.27% (↑1.20%p)**. Godot 90-93% → **91-94%**. 출시 78% → **79%** |
| **R84: Map warp fade + Spirit extra_hex 부분 파싱** | R82 Scene routing + R83 Sorcerer 후속 동시 진척. **`scene_fader.gd warp_fade(node, mid_callback, out_dur=0.25, in_dur=0.25)` 신규**: in-scene fade (scene 전환 없이 현재 scene 내부 시각 전환). 검정 페이드아웃 (`ColorRect alpha 0→1, tween`) → `mid_callback.call()` (실제 warp 수행: map_id/hero position 변경) → 검정 페이드인 → overlay 해제. **`demo.gd._on_warp` 정정**: 이전 instant `_apply_scene()` → 이제 `await SceneFader.warp_fade(self, func(): _scene_idx=target; _apply_scene(); _dialog.show_dialog(), 0.25, 0.25)`. **`_warping` boolean guard 추가** (fade 진행 중 재트리거 시 즉시 return, hero 가 warp tile 위에서 multiple emit 해도 1회만). **`game_data._ensure_spirit_skills_loaded` 보강 (R83 → R84)**: 이전 spirit name only → extra_hex hex string `_hex_to_bytes(hex) → PackedByteArray` 변환 → 첫 0x30 byte (48B, R77 stats area 일치) 를 little-endian u16 stride 로 24 entries → `stats_u16` 채움 + `_raw_bytes_size` 메타. 실 검증: spirit record #0 = 131 byte raw, 24 u16 추출. battle_system Sorcerer spirit fallback 이 정상 `mp_cost`/`cooldown`/`damage_pct` lookup (stats[7]/[9]/[5]) 동작 활성. extra_hex 의 정확 byte→field 매핑 (R77 sub-rel offset) R85+. `tools/h5_test_warp_fade.py` 신규 — warp_fade 시그니처 + fade-out → callback → fade-in 구조 + R82 함수 유지 회귀 + `_on_warp` warp_fade 사용 + `_warping` guard + callback 내 scene_idx/_apply_scene/dialog + `_hex_to_bytes` + extra_hex → stats_u16 + Python 시뮬 (bytes[10..11] LE = 0x1e30) + spirit record #0 131B/24 u16 + R82/R83 회귀 잔존, **8/8 통과**. verify_godot_project **0 warnings**. **진척률 갱신**: E 카테고리 62% → **70%** (Map warp fade 90 신규), F 카테고리 24% → **27%** (Sorcerer 60→70, spirit stats_u16 활성). 종합 가중평균 74.81% → **76.07% (↑1.26%p)**. Godot 89-93% → **90-93%**. 출시 77% → **78%** |
| **R83: Sorcerer (class_id=4) 부분 활성화** | R22 stub (c_csv_skill_04 부재) 해제. **class_select.gd UI**: 라벨 `"(미구현)" → "(매직 — 기본+정령 스킬만)"`, docstring 에 R83 부분 활성화 설명. **battle_system.gd `_skill_data` class-aware 리팩토링**: 이전 hardcoded `class_0` lookup → `GameState.class_id` 기반 `_skills_cache.get("class_%d" % cid, [])` 동적. **Sorcerer fallback chain**: class_4 데이터 없으면 → spirit `class_5` fallback (name prefix `"[정령] "`) → 그것도 없으면 generic stub (`"[미구현] "`). **GameState.total_attack 보강**: `class_id == 4` 일 때 `base += stat_int * 2` (Sorcerer INT magic bonus). 시뮬: Lv.1 Sorcerer base 31 (STR=6 + INT*2=16 + Lv*3=3) vs Warrior 27 (STR*2=24 + Lv*3=3) — active skill 부재 보상으로 effective 공격력 동등 이상. **`game_data.gd _ensure_spirit_skills_loaded()` 신규**: spirit skills 16 entries 가 skills.json 이 아닌 별도 `c_csv_skill_05.json` 에 있음 (raw csv `{count, records[{name, extra_hex}]}` 형식) → 첫 `skill_info()` 호출 시 자동 로드 + `_skills_cache["class_5"]` 에 `{name, stats_u16=[], desc=""}` 형식 stored. extra_hex 파싱은 R84+. **demo.gd**: `class_id == 4` 시 entry 후 안내 dialog. **skill_book_panel.gd**: class 4 + 빈 books 시 안내 + disabled 항목. `tools/h5_test_sorcerer.py` 신규 — class_stats class 4 데이터 + skills.json class_4 부재 + c_csv_skill_05 spirit 16 records 별도 존재 + 7 파일 R83 변경 + Sorcerer 31 vs Warrior 27 시뮬, **9/9 통과**. R76/R82 회귀 모두 통과. verify_godot_project **0 warnings**. **진척률 갱신**: F 카테고리 6% → **24%** (Sorcerer 0→60). 종합 가중평균 73.01% → **74.81% (↑1.80%p)**. Godot 88-92% → **89-93%**. 출시 75.5% → **77%** |
| **R82: Scene 흐름 정비 — SceneRouter autoload + GameOver scene** | R81 진척률 재평가의 가장 큰 임팩트 영역 (E. Scene 통합 55%) 의 첫 진척. **`scripts/core/scene_router.gd` 신규 autoload (140 줄)**: State enum (TITLE/CLASS_SELECT/DEMO/GAME_OVER 4) + 4 scene path + 6 public method (`to_title` / `to_class_select` / `to_demo` / `to_demo_with_load(slot)` / `to_game_over(reason)` / `quit_to_title(confirm)`) + 2 signal (`scene_changing`/`scene_changed`) + transition guard (`_transitioning` flag) + `last_game_over_reason()` + `notify_ready()` hook. `project.godot autoload` 등록. **`scenes/game_over.tscn` + `scripts/ui/game_over.gd` 신규**: 반투명 BG + 빨간 "Game Over" 타이틀 + reason 라벨 + 2 버튼 (Continue = `to_demo_with_load(0)` / Title = Give up) + slot 0 미리보기 (Lv/class/Gold) + ui_accept/cancel 매핑. **`demo.gd` hero death 정정 (R63 → R82)**: 이전 silent `quick_load(0)` → 명시적 `SceneRouter.to_game_over(self, "monster #N 의 skill K 에 쓰러졌습니다")`. 사용자가 사망 원인 인지 + Continue/Title 선택. **F10 = Quit-to-Title** (`SceneRouter.quit_to_title(self, true)`) — 확인 popup. **마이그레이션**: title.gd New Game/Continue/slot 선택 + class_select.gd Start 모두 SceneFader 직접 호출 → SceneRouter 경로 (4 호출 변경, SceneFader 직접 호출 0). `tools/h5_test_scene_router.py` 신규 — autoload 등록 + State enum + 4 scene path + 6 method + 2 signal + transition guard + GameOver 파일 + Continue/Title 동작 + reason + slot load + hero death → to_game_over + F10 = quit_to_title + title/class_select 마이그레이션 + notify_ready, **11/11 통과**. `verify_godot_project.py` **0 warnings**. R63/R72-R81 회귀 모두 통과. **진척률 갱신**: E 55→62% / 종합 가중평균 **72.17% → 73.01% (↑0.84%p)**. 코어 한정 87-92% 유효, Godot 88-92% (Scene 통합 +1%p). 출시 75% → 75.5% |
| **R81: ProcTargetEffectSkill overview RE (per-frame skill engine)** | `TargetEffect::ProcTargetEffectSkill` (@0x64a08, 4276B / 1069 ARM instr) 구조 매핑. **Jumptable 없음** (`addls pc` 0 개) — 4276B 전체가 if/else cascade dispatch. **함수 의미**: TargetEffect 100-slot main update loop 에서 active 슬롯마다 호출되는 per-frame skill effect engine. **Top reads**: `r4, +0xf` 9x base char / **HERO+0x22c class_id 6x** (5-class 분기) / **HERO+0x269 gunner_combo 6x** (GUNNER 추가 처리) / skill_info 12 distinct file-loaded field (`+0x32/+0x36 u16` × 3x 각 / `+0x29/+0x2f/+0xa` × 3x 각 / `+0x3a/+0x1c/+0x294` × 2x / `+0x2a/+0x2b` × 1x / R72 special_dispatch + R70 effect2 + R70 4×u16 활용) / **R79 dead reads `+0x4a` (ldrsh) + `+0x4e` (ldrsb) 각 1x 존재** (default 0 으로 no-op path 동작) / TargetEffect 상태 cluster `+0xab..+0xaf` 5 read + `+0xc0` frame counter + `+0x24`. **Top bl call graph**: `Formula::calc 14x` (★ R71 의 damage/value 평가) / `CHAR::GetSpritePtr 15x` / `SPRITE::GetExtraDataPtr 12x` / `OBJECT::GetX/Y 8x 각` / `StaticUtil::Rand 7x` / `ExtraData::GetPivot 6x 각` / **`TEM::NewTargetEffect_min 6x` (★ 재귀 VFX spawn)** / **`BATTLER::IncreaseHP 4x` (★ damage)** / **`BATTLER::AddCurseSkill 3x` (★ curse)** / `UiTargetMonster::SetBattler 3x` / `HERO::IncreaseHiperCount 3x` / `TargetEffect::NewHitEffect 2x` (hit VFX) / `BATTLER::ApplyAddEffect 2x` / `HERO::IncreaseSP 2x`. **흐름**: entry → level cap 99 검사 → cascade dispatch (class × state × frame × skill_info flags) → 각 branch 에서 Formula::calc → IncreaseHP / 재귀 sub-VFX spawn / curse / UI sync / 사운드. **R79 dead reads 일관성**: `+0x4a/+0x4e` 본 함수에도 read 존재 → default 0 path no-op 동작 확정. 정밀 case-by-case (cascade 분기 매트릭스) R82+. `tools/h5_test_proc_target_effect_skill.py` 신규 — symbol + 1069 instr + 0 jumptable + 10 top call count + 9 skill_info field read + R79 dead read 일관성 + HERO 3 field + TargetEffect 6 state cluster + 25 doc marker, **9/9 통과**. R63/R69/R72-R80 회귀 모두 통과. `docs/h5/RE/proc_target_effect_skill.md` 신규 (7 섹션). **.so 분석 ~99% 유지**. **🎯 진척률 매우 깊은 재평가** (8 카테고리 가중평균): A자산 95% + B데이터 96% + C로직 RE 93% + D Godot 코어 88% + E Scene 통합 55% + F 누락 (Sorcerer/Device 빌드) 6% + G 출시 보완 35% + H QA 60% → **종합 72.17%**. 코어 시스템 한정 (UI+전투+RE) 평가 **87-92%** (이전 보고치, 유효). Godot 실 구현 단순 평균 (D만) **88%**. 출시 가능 기준 (D+E+G 가중) **75%**. 현실적 실 게임 플레이 가능 기준 **~72%** — Scene 흐름 (E=55%) + Sorcerer/Device 빌드 (F=6%) + Distribution (G=35%) 미완이 큰 영향. R82+ 가장 큰 임팩트: Scene 흐름 정비 (E 55→75 = +2.4%p) / TEM 정밀 (C 93→95 = +0.3%p) / Sorcerer+Device 빌드 (F 6→30 = +2.4%p) |
| **R80: TargetEffectMgr / TargetEffect VFX 시스템 RE** | R73 의 TEM 11 호출 + effect_type {4,7,8} 발견 위치 + 전체 시스템 구조 매핑. **5 TEM overload chain**: `_min @0x62d40 (100B)` → tail-call `_+s @0x62cd4 (108B)` → `_+sai @0x62c54 (128B)` → **`_full @0x62a34 (408B) 실 구현`**, 평행 wrapper `_+saiih @0x62bcc (136B)` → `_full`. wrapper 들은 default arg 채움. **_full 핵심**: (1) 17 args 인자 분배. (2) **100-slot allocator loop** — `slot = this + fp*0x284` (0x284 = 644B per slot), `Effect::IsEmpty()` 검사로 free slot 찾기. (3) **`bl 0x62840 = TargetEffect::NewTargetEffect base (500B)`** 으로 slot 초기화 — 25+ field strb/strh + 200B memset work area. (4) **post-init dispatch on r6 (arg 17)**: 0/1/2 → 3 manager 채널 (global +0x15d8/+0x15e0/+0x15e4) 등록 (`bl 0xabb94`), 3+ → no-op. **Effect 베이스 클래스 5 멤버 함수 발견 + disasm**: `IsEmpty @0x610d8` (`[+0x11]==0` 검사), **`SetEffectType(char) @0x610f4 → strb [+0x12]` (★ effect_type 저장)**, `SetEffectFrame(short) @0x61114 → strh [+0x14]`, `SetEffectLastFrame(short) @0x61124 → strh [+0x16]`, `SetEffectValue(int) @0x61134 → str [+0x18]`. OBJECT 베이스: `SetXY @0xcfda4`, `SetObjectType @0xcfdac` (TargetEffect ObjectType=3). **Effect struct field 의미**: +0x11 active flag / **+0x12 effect_type** / +0x14 start frame / +0x16 end frame / +0x18 numeric value. **R73 effect_type 4/7/8 의 ProcHeroSkill context 매핑**: 4 = case 0/2/4/6 기본 hit VFX (6 호출), 7 = case 1/7 timestop VFX (2 호출), 8 = case 5 shock VFX (1 호출), dynamic = skill 별 special (3 호출). 실 sprite/animation 의미는 render 단 (R81+ DrawTargetEffect 추정). **TargetEffect struct 0x284B 25+ field 표** (docs §3): active +0x11 / type +0x12 / frame +0x14 / last_frame +0x16 / value +0x18 / int b +0x1c / SPRITE* +0x20 / 메타 +0x8c..+0x9f / sprite mgr +0xa0-+0xa7 / counter +0xc0 / 200B memset +0x18c-+0x253 / state +0x254-+0x281. **ProcTargetEffectSkill @0x64a08 (4276B) 확인**: per-frame skill 처리 함수, Effect+0x12 직접 안 읽고 **skill_info 기반 처리** (Formula::calc @0x7749c 호출 + level cap 99). `tools/h5_test_target_effect_mgr.py` 신규 — **13 ELF symbol** + 5 Effect/OBJECT setter atomic + 4 TEM wrapper chain → _full + _full slot allocator + post-init 3 manager dispatch + TargetEffect base 25+ field + 200B memset + R73 effect_type {4,7,8} immediate 회귀 + ProcTargetEffectSkill size + 27 doc marker, **9/9 통과**. R63/R69/R72-R79 회귀 모두 통과. `docs/h5/RE/target_effect_mgr.md` 신규 (6 섹션). **.so 분석 ~99% 유지** (VFX 시스템 구조 + Effect 베이스 클래스 + slot allocator 확정), Godot 87-92% 유지 (R80 = RE only), 출시 85-94% 유지 |
| **R79: BATTLER effect dispatch 분석 + HSI runtime field 가설 종결** | R78 잔여 (+0x44/+0x46/+0x48/+0x4a/+0x4e writer 추적) 의 결정적 종결. `BATTLER::ApplyAddEffect` (@0x4bdb4, 496B) full disasm = **pure 28-way tail-call dispatcher** (HERO 14-way + Monster 9-way jumptable, struct write 0). `BATTLER::AddCurseSkill` (@0x4b134, 100B) → **curse 저장 위치 = attacker BATTLER+0x130/+0x134/+0x13a/+0x140/+0x1b0** (helper 0x4afd4 호출). `BATTLER::AddBuffSkill` (@0x4b198, 260B) → **buff = BATTLER+0x118/+0x11e/+0x124/+0x12a/+0x1c8** (value>=0x4b 분기 + 2 path). `HERO::AddStanceSkill` (@0x91d7c, 256B) → **stance = HERO+0x284/+0x288/+0x28a + flag HERO+0x1f94**. **active effect 저장 컨테이너는 BATTLER/HERO struct — HeroSkillInfo 와 무관 확정** (R74 GameState active_curses/buffs/stances Array 가 정확한 Godot 대응). **.so 전체 grep** (capstone 으로 .text 의 모든 strb/strh 디스어셈블) 결과: `+0x44/+0x46/+0x48/+0x4a/+0x4c/+0x4e` immediate offset 에 write 하는 함수 중 **HeroSkillInfo 컨텍스트는 0 개** (모두 다른 무관 구조체: BFont 생성자, NETWORK::_NET_ITEM_, ParticleMgr, StateInGameMenu, Battle::DrawSpiritCutIn, HERO::SaveHeroData, EnemyAI, StateMap, FntGroup 의 같은 offset 우연 일치). **R72/R73 의 5 runtime field 가설 종결**: ProcHeroSkill 의 ldrsb/ldrsh +0x44/+0x46/+0x48/+0x4a/+0x4e read 는 **dead reads** — writer 없으므로 항상 HERO 객체 zero-init default 0 값. 정상 게임플레이 영향: +0x44 → class 3 motion 23 KB 일정값 8 / **+0x46 → case 5 shock skill 조건 절대 충족 안 됨 → dead code** / +0x48 → R74 fallback default=4 채택 / +0x4a → case 0 NO_HIT SP delta 0 (no-op) / +0x4e → KNIGHT secondary check 0 (no-op). **HeroSkillInfo 88B 최종 영역 구성 (R77+R78+R79 종합)**: **68B file-loaded (+0x00..+0x43)** + **16B unused (+0x44..+0x53, dead reads)** + **4B cooldown (+0x54 NowCoolTime / +0x56 MaxCoolTime u16)**. **field 의미 11/11 확정** (R77 file 7 + R78 cooldown 2 + R79 dead 5 closure). **`tools/h5_test_battler_effect_dispatch.py` 신규** — 4 ELF symbol + ApplyAddEffect 28-way dispatcher 구조 + AddCurseSkill 5 attacker offset + AddBuffSkill 5 offset + value>=0x4b 분기 + AddStanceSkill 3 HERO offset + .so-wide grep 0 HSI writer + R69/R72/R73 dead read 존재 확인 + 24 doc marker, **8/8 통과**. R63/R69/R72/R73/R74/R75/R76/R77/R78 회귀 모두 통과. `docs/h5/RE/battler_effect_dispatch.md` 신규 (8 섹션, struct field final 표). **.so 분석 ~99% 유지** (effect 저장 위치 확정 + HSI struct 완전 종결로 ProcHeroSkill 의미 100% 명확), Godot 87-92% 유지 (R79 = RE only), 출시 85-94% 유지 |
| **R78: HeroSkillInfo runtime field source 추적 + cooldown system 확정** | R77 의 +0x44..+0x57 runtime 영역 writer 추적. **`.dynsym` 에서 HeroSkillInfo:: 4 멤버 함수 발견 + ARM full disasm**: `SetNowCoolTime(s)` @0xd8d38 (12B) writes both `+0x54 = s` AND `+0x56 = s` / `GetNowCoolTime` @0xd8d44 (8B) reads s16 `+0x54` / `GetMaxCoolTime` @0xd8d4c (8B) reads s16 `+0x56` / `DecreaseNowCoolTime` @0xd8d54 (36B) decrements `+0x54` u16 (underflow → clamp 0). **HeroSkillInfo +0x54 = NowCoolTime u16 / +0x56 = MaxCoolTime u16 cooldown pair 확정** (R72 의 "+0x50 ranges" 가설 정정 → 실제 +0x54/+0x56). **R70 의 "59-slot init" 가설 정정**: ProcHeroSkill entry @0x992b8 의 59-iter 루프는 `bl 0xd8d54` (DecreaseNowCoolTime) 호출 — **매 ProcHeroSkill 호출마다 59 슬롯의 cooldown 1씩 -1 tick + 0 clamp**, 초기화 아님. **InitSkillEmpty @0x88a20 (272B) 정밀 분석**: 32 개 `strb r2 (=0xFF), [r0, offset]` — base 0x1b40 + offset 0..0x1f 의 32 연속 byte 를 0xFF 로 init. **HeroSkillInfo 배열 무관, 새 HERO field cluster 발견** (HERO+0x1b40..+0x1b5f, active skill slot 또는 quick-cast slot 후보, R79+ 의미 추적). **InitSpiritSkillMenu @0x89198 (132B) 분석**: GOT lookup 글로벌 객체 +0x118/+0x11c/+0x120/+0x122/+0x124-127/+0x278-27b menu state init + HERO+0x1fb6=1 flag — HeroSkillInfo 무관. **HERO::GetHeroSkillInfoPtr @0x88ce4 (20B)** 확정: `return this + 0x348 + idx*0x58` (R70/R77 일치 검증). **HERO::HeroSkillAtkHardCode @0x9041c (888B) 부분 분석**: class_id (+0x22c) 분기 + class 3 (KNIGHT) 별도 path + skill_info+0x45 (R72 의 "additional check") 읽기, **skill_info 에 write 없음**. **R72/R73 의 +0x44/+0x46/+0x48/+0x4a/+0x4e writer 추적 결과**: file 출처 아님 (R77 확정) + InitSkillEmpty/Spirit 출처 아님 (R78 확정) + ProcHeroSkill/HeroSkillAtkHardCode write 없음 → **HERO 객체 zero-init default 0** 가정 가장 합리적. ProcHeroSkill 의 `ldrsb`/`ldrsh` 읽기 자체는 사실이지만 정상 게임플레이에서는 default 0 으로 동작 (R74 fallback=4 등이 합리적 보조). R79 후속: `BATTLER::ApplyAddEffect` (@0x4bdb4, 496B) 정밀 분석 또는 `HeroSkillAtkHardCode` 완전 추적. **HeroSkillInfo 88B struct field 의미 9/11 확정** (file-loaded 7 from R77 + cooldown pair 2 from R78). **`tools/h5_test_skill_info_runtime.py` 신규** — 8 ELF symbol + SetNowCoolTime dual write +0x54/+0x56 + GetNow/MaxCoolTime ldrsh + DecreaseNowCoolTime -1/underflow/clamp/store + GetHeroSkillInfoPtr 88B stride + ProcHeroSkill 59-iter cooldown tick (init 가설 정정) + InitSkillEmpty 32 strb at 0x1b40 (skill array 무관) + InitSpiritSkillMenu global state + HeroSkillAtkHardCode skill_info read-only + 4 .dynsym members + 23 doc marker, **12/12 통과**. R63/R69/R72/R73/R74/R75/R76/R77 회귀 모두 통과. `docs/h5/RE/skill_info_runtime.md` 신규 (8 섹션). **.so 분석 ~99% 유지** (cooldown system + R70 init 정정으로 ProcHeroSkill 의미 더 정확), Godot 87-92% 유지 (R78 = RE only), 출시 85-94% 유지 |
| **R77: LoadResSkillInfo file layout RE 확정** | HERO::LoadResSkillInfo (@0x8bba4, 784B, 195 instr) + LoadResClassSkillInfo (@0x9b308, 48B) ARM full disasm. R75 의 `GameData.skill_info` byte offset → stats_u16 index 매핑 가설을 정확화. **파일 layout 확정**: per-record = `3B header (2B unused + 1B name_len) + name + 0x30B stats + desc`. stats sub-rel → HeroSkillInfo entry offset 31 field 매핑 완성 (byte 27 + u16 10). **R72/R73 5 critical field 정확 위치 검증**: effect_type (+0x28 ← stats sub-rel 0x1a), dynamic_formula_id (+0x30 ← sub-rel 0x26), special_dispatch (+0x3a ← sub-rel 0x2b), formula_id_1 (+0x3c ← sub-rel 0x2d), formula_id_2 (+0x3d ← sub-rel 0x2e). **HeroSkillInfo 88B 영역 구분 확정**: **file-loaded +0x00..+0x43 (68B)** + **runtime state +0x44..+0x57 (20B)**. R72/R73 의 6 field 가설 (+0x44 kb_idx / +0x46 shock / +0x48 max_combo / +0x4a sp_delta / +0x4c / +0x4e knight_threshold) **정정**: ProcHeroSkill 의 ldrsb/ldrsh 자체는 사실이지만 출처는 **skill 파일이 아님** — InitSkillEmpty (@0x88a20) 또는 hard-coded table (R78+ 추적). LoadResClassSkillInfo wrapper = `LoadResSkillInfo(class_id) + LoadResSkillInfo(5) + LoadResSkillIcon tail`. 총 **59 슬롯 = 43 class skill + 16 spirit/shared** (R70 의 HERO+0x348 88B×59 와 일치). External helpers: 0x14e4ec (filename), 0x144e80 (file load), 0x1437ec (read_u16), 0xabd18 (malloc), 0x31504 (memset), 0x3130c (memcpy), 0x14cfa4 (free). **`tools/h5_test_load_skill_table.py` 신규** — 5 ELF symbol + 195 instr disasm + 59-slot dispatch (43/16) + HERO+0x348 88B layout + file header 2B skip loop + name malloc/memcpy + 9 critical R72/R73 store + 27 byte + 10 u16 + 23 doc marker + runtime region (+0x44..+0x57) zero file-load 검증 + LoadResClassSkillInfo 2-call wrapper, 14/14 통과. `game_data.gd skill_info` docstring 정정 (file-loaded 5 field 정확 vs runtime 5 field 잠정). `docs/h5/RE/load_skill_table.md` 신규 (8 섹션). R63/R69/R72/R73/R74/R75/R76 회귀 모두 통과. **.so 분석 ~99% → ~99% 유지** (ProcHeroSkill 의 file-source field 신뢰도 100% 확립, runtime field 는 출처 미확정), Godot 실 구현 87-92% 유지 (R77 = RE only), 출시 85-94% 유지 |
| **R76: active effect stat modifier 통합 + tick 자동 호출** | R75 의 active effect Array 가 실 stat 에 영향. **`GameState.total_attack` 보강**: `raw = (base + equip_bonus); buff_pct = Σ active_buffs.f1 (clamp 0..200); return raw × (100 + buff_pct) / 100`. **`GameState.total_defense` 보강**: `stance_pct = Σ active_stances.f1 (clamp 0..150); curse_pct = Σ active_curses.f1 (clamp 0..80); return raw × (100 + stance_pct - curse_pct) / 100`. **battle_system._enemy_turn 끝에서 `GameState.tick_active_effects()` 자동 호출** — turn 마다 remaining_turns 감소 + 만료 자동 제거 + state_changed signal 발화. **status_panel.gd 에 `_on_state_changed` listener 추가** — `_ready()` 에서 `GameState.state_changed.connect(_on_state_changed)` 등록, visible 일 때만 `_apply()` (redraw 회피). 따라서 R75 의 `[Combo N/M]` + `[저주×N, 버프×M, 자세×K]` 가 panel 열린 채로 실시간 갱신 (battle log, skill 사용 직후 등). **공식 합리성**: buff cap 200% (+200% ATK), stance cap 150% (KNIGHT 방어 자세 등), curse cap 80% (방어력 80% 감소 max — 절대 0 막아냄). **stance + curse 동시 적용**: stance_pct - curse_pct (net 차이) 적용 — 양수면 buff, 음수면 debuff 우세. **`tools/h5_test_stat_modifier.py` 신규** — total_attack active_buffs loop + clamp 0..200 + raw×(100+pct)/100 / total_defense stance+curse loop + clamp 0..150/0..80 + net_pct / battle_system._enemy_turn 끝 tick_active_effects 호출 / state_changed.emit / status_panel._on_state_changed listener + visible guard / R76 docstring markers / Python 시뮬 7 case (buff 20%/누적 30+20%/clamp 200% / stance 50% / curse 30% / stance+curse net / curse clamp 80%) 모두 통과. R63/R74/R75 회귀 모두 통과. .so 분석 ~99% 유지, **Godot 실 구현 85-90% → 87-92%** (stat 실 영향 +2%p), 출시 83-92% → 85-94%. R75 의 frontend 통합 → R76 의 stat 실 영향으로 buff/curse/stance 가 ATK/DEF 에 실제로 반영. 다음 라운드 = **Godot Editor 실 실행 검증** (B 키 → SKILL → log + UI + total_attack/defense 변화 시각 확인) |

**현 위치**: 데이터 RE 100% / .so 함수 분석 **~99%** / Godot 실 구현 **87-92%**.
원본 분석 **~99%**, 리메이크 출시 **85-94%**.



업데이트: 2026-05-19 (Round 87 종료) — **Spirit (class_5) extra_hex full 의미 매핑 — 80% 돌파**. R83/R84 후속 최종화. game_data._ensure_spirit_skills_loaded() 가 R77 정확 sub-rel offset 으로 8 explicit field 추출 (effect_type 0x1a, dynamic_formula 0x26, special_dispatch 0x2b, formula_id_1/2 0x2d/0x2e, primary_u16 0x22 LE, secondary_u16 0x24 LE, desc_len 0x2f). skill_info(5,_) 가 explicit field 직접 반환. Spirit 분포 effect_type 0=5/2=9/7=2 (debuff 위주), formula_id_1=57 (10/16). Sorcerer spirit fallback 정확화. tools/h5_test_spirit_full_mapping.py 9/9 PASS, R82-R86 회귀 통과. F 27→40%, 종합 78.87→80.17% (↑1.30%p) — **80% 돌파**. Godot 92-95%, 출시 82%.

이전 라운드 업데이트: 2026-05-19 (Round 86 종료) — **Distribution build preset + BUILD_ANDROID 가이드 + icon.svg**. G 카테고리 (출시 보완) 의 가장 큰 빈 칸 (Distribution 0%) 채움. export_presets.cfg 신규 (Debug + Release 2 preset, gradle_build min/target 23/34, arm64-v8a only, 11 permissions all false, immersive). icon.svg 신규 (project.godot 참조 만족). .gitignore 조정 (export_presets commit + *.keystore ignore). docs/h5/BUILD_ANDROID.md 신규 (8 섹션). tools/h5_test_export_preset.py 13/13 PASS. R82/R83/R84/R85 회귀 통과. G 35→55%, 종합 77.27→78.87% (↑1.60%p), 출시 81%.

이전 라운드 업데이트: 2026-05-19 (Round 85 종료) — **Battle UI fade transition**. R82 SceneRouter + R84 warp_fade 후속. battle_ui.start() 가 warp_fade + _setup_and_show split + 중복 guard. _on_ended 도 fade-out (popup→fade→cleanup→emit) emit 순서 정확 (race 방지). SceneFaderRef preload (CanvasLayer). tools/h5_test_battle_fade.py 8/8 PASS, R82/R83/R84 회귀 통과. E 70→80%, 종합 76.07→77.27% (↑1.20%p), Godot 91-94%, 출시 79%.

이전 라운드 업데이트: 2026-05-19 (Round 84 종료) — **Map warp fade transition + Spirit extra_hex 부분 파싱**. scene_fader.warp_fade(callback) in-scene 전환 + demo._on_warp 가 fade + _warping guard + game_data 의 spirit extra_hex → bytes → 24 u16 변환 + battle_system Sorcerer spirit fallback 실 활성. tools/h5_test_warp_fade.py 8/8 PASS, R82/R83 회귀 통과. E 62→70%, F 24→27%, 종합 74.81→76.07% (↑1.26%p), Godot 90-93%, 출시 78%.

이전 라운드 업데이트: 2026-05-19 (Round 83 종료) — **Sorcerer (class_id=4) 부분 활성화**. R22 stub 해제. class_select 라벨 변경, battle_system._skill_data class-aware 리팩토링 + Sorcerer spirit/stub fallback, GameState.total_attack INT × 2 bonus (class 4), game_data 의 c_csv_skill_05 → class_5 자동 로드, demo + skill_book_panel 안내. tools/h5_test_sorcerer.py 9/9 PASS. R76/R82 회귀 통과. F 카테고리 6→24%, 종합 73.01→74.81% (↑1.80%p), Godot 89-93%, 출시 77%.

이전 라운드 업데이트: 2026-05-19 (Round 82 종료) — **Scene 흐름 정비 (SceneRouter + GameOver + Quit-to-Title)**. R81 의 진척률 재평가에서 가장 큰 임팩트 영역 (E. Scene 통합) 의 첫 진척. SceneRouter autoload (4 state + 6 method + 2 signal + transition guard) + GameOver scene (Continue/Title + reason display + slot 미리보기) + demo death → to_game_over (silent quick_load 제거) + F10 quit_to_title + title/class_select 4 호출 마이그레이션. tools/h5_test_scene_router.py 11/11 PASS. verify_godot_project 0 warnings. E 카테고리 55→62%, 종합 가중평균 72.17→73.01% (↑0.84%p). Godot 88-92% (코어 한정 87-92% 유효), 출시 75.5%.

이전 라운드 업데이트: 2026-05-19 (Round 81 종료) — **ProcTargetEffectSkill overview RE + 진척률 매우 깊은 재평가**. 4276B / 1069 instr per-frame skill engine 구조 매핑 (jumptable 없음, pure cascade, Formula::calc 14x + TEM 재귀 6x + IncreaseHP 4x + AddCurseSkill 3x). **8 카테고리 가중평균 결과 종합 72.17%**: A자산 95% × 8% + B데이터 96% × 14% + C로직 RE 93% × 17% + D Godot 코어 88% × 24% + E Scene 통합 55% × 12% + F 누락 6% × 10% + G 출시 35% × 8% + H QA 60% × 7%. 코어 한정 87-92% 유효, 실 게임 플레이 기준 72%. R82+ 가장 큰 임팩트 = Scene 흐름 (E 55→75) + Sorcerer/Device 빌드 (F 6→30).

이전 라운드 업데이트: 2026-05-19 (Round 80 종료) — **TargetEffectMgr / TargetEffect VFX 시스템 RE**. R73 의 TEM 11 호출 + effect_type {4,7,8} 발견 위치 확정. 5 TEM overload chain (4 wrapper → _full @0x62a34 실 구현). _full = 100 slot × 0x284B allocator + IsEmpty + bl 0x62840 base init (500B, 25+ field) + post-init r6 dispatch (3 manager 채널). **Effect 베이스 5 setter**: IsEmpty +0x11, SetEffectType +0x12 (★), SetFrame +0x14, SetLastFrame +0x16, SetValue +0x18. R73 effect_type 4=hit / 7=timestop / 8=shock VFX. docs/h5/RE/target_effect_mgr.md + tools/h5_test_target_effect_mgr.py 9/9 PASS. .so 분석 ~99% 유지, Godot 87-92% 유지, 출시 85-94% 유지.

이전 라운드 업데이트: 2026-05-19 (Round 79 종료) — **BATTLER effect dispatch 분석 + HeroSkillInfo runtime field 가설 종결**. ApplyAddEffect@0x4bdb4 = pure 28-way dispatcher. AddCurseSkill/AddBuffSkill/AddStanceSkill 분석으로 **active effect 컨테이너 = BATTLER/HERO struct (BATTLER+0x130-0x140 curse, BATTLER+0x118-0x128 buff, HERO+0x284-0x28a stance), HeroSkillInfo 무관 확정**. .so-wide grep 결과 HeroSkillInfo+0x44/+0x46/+0x48/+0x4a/+0x4c/+0x4e writer **0 개** → R72/R73 5 runtime field = **dead reads** (default 0). HeroSkillInfo 88B 최종: 68B file + 16B unused + 4B cooldown. **field 의미 11/11 확정**. docs/h5/RE/battler_effect_dispatch.md + tools/h5_test_battler_effect_dispatch.py 8/8 PASS. .so 분석 ~99% 유지, Godot 87-92% 유지, 출시 85-94% 유지.

이전 라운드 업데이트: 2026-05-19 (Round 78 종료) — **HeroSkillInfo runtime field source 추적 + cooldown system 확정**. HeroSkillInfo:: 4 멤버 함수 (SetNowCoolTime/Get/Decrease/GetMax) disasm 으로 **+0x54 NowCoolTime / +0x56 MaxCoolTime cooldown pair 확정**. R72 의 "+0x50 ranges" 정정. R70 의 "ProcHeroSkill entry 59-slot init" 가설 정정 → 실제 cooldown tick. InitSkillEmpty (HERO+0x1b40 32B 0xFF init), InitSpiritSkillMenu (global menu state) — HeroSkillInfo 무관 확정. R72/R73 의 +0x44/+0x46/+0x48/+0x4a/+0x4e 는 zero-init default 0 가정. HeroSkillInfo field 9/11 확정. docs/h5/RE/skill_info_runtime.md + tools/h5_test_skill_info_runtime.py 12/12 PASS. .so 분석 ~99% 유지, Godot 87-92% 유지, 출시 85-94% 유지.

이전 라운드 업데이트: 2026-05-19 (Round 77 종료) — **HERO::LoadResSkillInfo (@0x8bba4, 784B) + LoadResClassSkillInfo (@0x9b308) ARM full disasm**. R75 매핑 정확화. file layout = 3B header + name + 0x30B stats + desc. HeroSkillInfo 88B = file-loaded 68B (+0x00..+0x43) + runtime 20B (+0x44..+0x57). R72/R73 5 critical field (+0x28/+0x30/+0x3a/+0x3c/+0x3d) 정확 위치 확정. R72/R73 6 runtime field (+0x44/+0x46/+0x48/+0x4a/+0x4c/+0x4e) 는 **file 출처 아님** 으로 정정 (R78+ InitSkillEmpty/hard-coded 추적). docs/h5/RE/load_skill_table.md (8 섹션) + tools/h5_test_load_skill_table.py (14 PASS) + game_data.gd skill_info docstring 정정. .so 분석 ~99% 유지, Godot 87-92% 유지, 출시 85-94% 유지.

이전 라운드 업데이트: 2026-05-19 (Round 76 종료) — **active effect stat modifier 통합 + tick 자동 호출**.
GameState.total_attack 에 active_buffs.f1 누적 % bonus (clamp 0..200). GameState.total_defense
에 active_stances.f1 % bonus + active_curses.f1 % reduction (clamp 0..150/0..80) — net_pct
계산. battle_system._enemy_turn 끝에서 tick_active_effects 자동 호출 → 만료 처리 +
status_panel 자동 갱신. h5_test_stat_modifier.py 7 case Python 시뮬 통과. R63/R74/R75
회귀 통과. Godot 실 구현 85-90% → 87-92%, 출시 83-92% → 85-94%.

이전 라운드:

Round 75 — **GUNNER combo UI + skill effect 시스템 통합**.
R74 backend (GUNNER combo state + helper signals) 의 frontend 통합. GameState 에 active_curses/buffs/stances Array 3종 + add_active_effect/tick_active_effects method.
battle_system 이 3 signal 자동 캐치 → GameState 갱신. status_panel 에 GUNNER combo (`[Combo N/M]`) + active effect 카운트 (`[저주×N, 버프×M, 자세×K]`) 시각화 (text only).
GameData.skill_info(class_id, skill_id) 신규 — R72/R73 의 10 fields 노출. battle_system SKILL 에 자동 dispatch (effect_type → apply_skill_effect 자동 호출 + log fx_str).
tools/h5_test_skill_meta.py 모두 통과. Godot 실 구현 82-88% → 85-90%, 출시 80-90% → 83-92%.

이전 라운드:

Round 74 — **Godot battle_system.gd damage 공식 정확화**.
R63 임시 공식 → R71+R72+R73 발견 통합. GameState 에 gunner_combo/max_combo/ammo
3 변수 추가. battle_system.gd SKILL action 에 GUNNER combo multiplier (combo×20+30)
적용 + Formula 4 부가 SP delta + R72 helper signals (curse/buff/stance_applied) 3종 +
apply_skill_effect API. h5_test_battle_formula.py 모두 통과. R63/R69/R73 회귀 통과.
Godot 실 구현 79-83% → 82-88%, 출시 78-88% → 80-90%.

이전 라운드:

Round 73 — **ProcHeroSkill JT2 4 case + TEM 11 호출 RE**.
JT2 case 0/2/4/6 = 기본 공격 (Formula 3 HP + Formula 4 SP) / case 1/7 = timestop chain /
case 3 = KNIGHT secondary (orb-based) / case 5 = shock skill (dynamic Formula id from
skill_info[+0x30]). 모든 case → 기본 공격 path 합류. TargetEffectMgr 시그니처
+ effect_type 4/7/8 distinct 식별. HeroSkillInfo +0x30 dynamic id / +0x46/+0x4e/+0x48
신규. HERO+0x1a8 halfword storage. docs §13/§14 추가 + 16 R73 markers 통과.

이전 라운드:

Round 72 — **ProcHeroSkill JT1 case + class 2 GUNNER entry RE**.
JT1 의 5 case 각 helper 매핑 확정: case 0=IncreaseSP / 1+2=AddCurseSkill (debuff) /
3+5=AddBuffSkill (buff) / 4=AddStanceSkill (stance, R70 heal+buff 가설 정정).
모든 case → b 0x99978 합류. 공통 패턴: 2회 Formula::calc(+0x3c, +0x3d) → helper.
HeroSkillInfo 신규 6 field (+0x1c, +0x3a, +0x3c formula_id_1, +0x3d formula_id_2,
+0x45, +0x4a SP delta). HERO this +0x294/+0x295/+0x269 (GUNNER combo state).
class 2 GUNNER entry: skill_idx==5 일 때만 special path, damage=(combo×20+30)×X/100.
docs §12 추가 + 14 R72 markers 통과.

이전 라운드:

Round 71 — **ProcHeroSkill Formula::calc dispatch + r5 base 추적**.
Formula::calc (@0x7749c, 172B) full disasm — id < 1000 calc_pl / < 2000 calc_en /
≤ 3007 calc_sk / else 0. Formula struct +0/+4/+8 = en/sk/pl base ptrs.
Formula 0x6f (111) / 0x63 (99) 는 calc_pl OOB (production 0..38 만 정의) → hit check
result 항상 0 → __sub_89068 skip 되지만 ChangeAttackMotion 호출 자체는 unaffected.
r5 base 추적: add r4 #0x1ec0 + add r5 #0xc → r5 = HERO+0x1ecc, [r5,-0x190] = HERO+0x1d3c
(ptr 영역). 0x99710 의 cmp #0x63 = level cap 99 확정 (Monster+0x19c). docs §11 추가.
h5_test_proc_hero_skill.py 확장 (Formula::calc + r5 base + level cap, 13 markers).

이전 라운드:

Round 70 — **HERO::ProcHeroSkill 골격 RE**.
R69 의 ChangeAttackMotion 호출자 (@0x99278, 7972B 거대 함수) 정밀화. 1993 instr.
Entry: 59-slot skill array (HERO+0x348, 88B×59) 초기화 + class 2 (GUNNER) 별도 path.
2 jumptable: @0x9a398 (5-way skill_info[+0x28] = skill effect type 0..4),
@0x9a8d8 (7-way GetCurActSkillIdx = active skill slot 0..6). HeroSkillInfo 18+
fields 매핑 (88B entry). Formula::calc 27회 + TargetEffectMgr::NewTargetEffect 11회.
docs/h5/RE/proc_hero_skill.md + h5_test_proc_hero_skill.py 26 검증 통과.

이전 라운드:

Round 69 — **Attack motion dispatch RE 확정**.
ChangeAttackMotion (@0x91e7c, 340B) + CheckWeaponMotion (@0x8dd58, 256B) ARM full
disasm. R67 의 cmp 0xd/0xe/0x14/0x17 가설 정정 — input = CHAR::GetMotion() 반환값,
분기 키 = class_id (HERO+0x22c). class 0 (워리어) motion 13→38 / 20→22 swap,
class 3 (나이트) motion 14→15+KB10 / 23→24+variable KB. 호출자 확정: ChangeAttackMotion
← ProcHeroSkill @0x99278+0x488 1회, CheckWeaponMotion ← 4 클래스 Draw() 5회
(WARRIOR/ROGUE/KNIGHT/GUNNER, SORCERER 제외 — R22 stub 재확인). HERO struct 신규
fields 4종 + HeroSkillInfo +0x44 식별. character.gd 에 10 상수 추가 + RE 문서 +
h5_test_attack_motion.py 27 검증 통과.

이전 라운드:

Round 68 — **NPC Dialog state machine + DIALOG_INFO struct RE 확정**.
`DialogWindow_Proc` (@0x71b48) ARM disasm 으로 R67 의 state byte=+0x29 가설 정정,
실제 main state byte = +0x2b (0..7 jumptable). +0x29=sub-step counter (0..4),
+0x2d/+0x2f=animation curve key. state 0=inactive / 1·3·6=idle-busy / 2·4=fade-in /
5·7=HSB fade-out (RestorePal+ChangeHSB). Event_DialogWindow + Event_SituateDialogText
까지 full disasm. dialog_box.gd 에 11 상수 추가 + docs/h5/RE/npc_dialog.md 신규.
h5_test_dialog.py — 9 ELF + 11 disasm 패턴 + 12 RE doc + 12 GDScript const 통과.

이전 라운드:

Round 67 — **Battle motion enum + CHAR state machine RE 확정**.
CHAR::SetMotion + 4 Set*Motion 디스어셈블로 R50 의 HOST_MOTION 가설 (walk=1/die=9)
잘못 확인. 실제 walk=motion 3, die=motion 5, attack/attacked=variable. main_state(1-4)
와 motion 별개 시스템. CHAR struct +0x2c/0x2d/0x2e/0xc4-c6 확정. character.gd 에
SO_* 8 상수 추가 (logical HOST_MOTION_* 유지로 호환). h5_test_battle_motion.py 통과.

이전 라운드:

Round 66 — **두 host 명세 강화 (battle_system turn-based + character real-time)**.
R65 SESSION_HANDOFF 의 "dead code" 가설 검토 결과 두 host 모두 정상 경로
확인. battle_system 의 stub 보완 (cooldown 실 동작, is_stunned 추가) + 두 host
비교 표 docstring + monster_ai create_runtime docstring 의 분기 명세.
h5_test_dual_host.py — 17/17 + 6 R66 패턴 + 의미 차이 시뮬 + cooldown 검증.

이전 라운드:

Round 65 — **Quest reward type RE 확정**.
QuestRewardData @0xd458c 디스어셈블로 reward.type=item slot, sub=idx, value=qty
확정. R60 의 type 15="item" 가설을 type 0-16 전체로 일반화. type 17=money,
18=exp, 19=HP, 20=INT. quest_system.gd reward_label 가 items.json item_name_at
호출로 정확한 한국어 이름 표시. h5_test_reward_types.py — 64/64 in-range +
4 ELF symbol + 11/11 라벨 케이스 통과.

이전 라운드:

Round 64 — **monster kill 보상 흐름 완성**.
demo.gd `_physics_process` dead 분기에 `_award_kill_reward` 추가 (3 helper:
`_award_kill_reward` / `_kill_stat_or` / `_roll_kill_drops`). enemy_stats sentinel
→ default 공식 (10+rand%20 exp / 5+rand%50 gold) + 25% drop_table + add_battle_reward
level_up + Quest.on_enemy_killed. SPACE 키 한번에 공격→사망→보상→level_up 자동 흐름.
h5_test_kill_reward.py — 9 구조 + sentinel 분포 + drop 1000회 + level_up 시뮬 통과.

## 🎯 전체 진척 평가 (Round 76 시점)

| 영역 | 추정 % | 비고 |
|---|---:|---|
| 자산 추출/변환 | ~95% | VFS/sprite/palette/text/OGG. 남은 것: SMAF/한글폰트 (LOW PRIORITY) |
| 데이터 구조 RE | ~100% | 모든 데이터 파일 식별 + decoder + struct 매핑 완료 |
| .so 함수 분석 | ~99% | R67-73 RE 완료. 잔여: TEM 인자 정밀 의미, special path 0x9b100/0x9b124, type 22, LoadSkillTable disasm |
| Godot 실 구현 | **~87-92%** | + R74-75 backend+UI + **R76 stat modifier 통합** (active_buffs → ATK%, active_stances/curses → DEF%, tick 자동). R77+ scene 실 실행 검증 |
| Android 실 빌드 | 0% | 사용자 GUI 작업 |

**종합**: 원본 분석 ≈ **~99%**, 리메이크 출시 ≈ **85-94%** (R76 stat 실 영향으로 +2%p).

## 📦 미완 큰 덩어리 (우선순위 순)

1. **UI 시스템 — R51-58 완료** (인벤토리/강화/합성/Orb/NPC blacksmith/Quest/SkillBook/Mission)
2. **AI/Battle 통합 — R61-63 완료** (character host CHAR 17 method + 30fps tick + 실 전투)
3. **보상 흐름 — R64 완료** (kill → exp/gold/drop/level_up 자동 chain)
4. **Reward type RE — R65 완료** (type 0-16 = item slot, 17=money, 18=exp, 19=HP, 20=INT)
5. **두 host 명세 — R66 완료** (battle_system turn-based vs character real-time, 둘 다 정상 경로)
6. **Battle motion RE — R67 완료** (walk=motion 3, die=motion 5, main_state 1-4, CHAR struct fields)
7. **NPC Dialog RE — R68 완료** (DialogWindow_Proc 8 state jumptable @ +0x2b / sub-step @+0x29 / DIALOG_INFO struct +0x10..+0x3c phase data pool)
8. **Attack motion dispatch RE — R69 완료** (ChangeAttackMotion class_id 0/3 + GetMotion switch / ProcHeroSkill 호출 / 4 클래스 Draw 의 CheckWeaponMotion)
9. **ProcHeroSkill 골격 RE — R70 완료** (1993 instr, entry + 2 jumptable + HeroSkillInfo 18+ fields + helper graph)
10. **ProcHeroSkill Formula dispatch + r5 base — R71 완료** (id 분류 < 1000/< 2000/≤ 3007 / 0x6f-0x63 OOB / r5=HERO+0x1ecc / [r5,-0x190]=HERO+0x1d3c / level cap 99)
11. **ProcHeroSkill JT1 case + GUNNER entry — R72 완료** (case 0=IncreaseSP, 1+2=Curse, 3+5=Buff, 4=Stance + GUNNER combo formula + HeroSkillInfo +0x3c/+0x3d formula ids)
12. **ProcHeroSkill JT2 case + TEM — R73 완료** (기본 공격 Formula 3/4 + timestop + KNIGHT + shock + skill_info+0x30 dynamic id + TEM signature + effect_type 4/7/8)
13. **Godot battle_system.gd damage 공식 정확화 — R74 완료** (GUNNER combo state + SKILL Formula 4 SP delta + 3 helper signals + apply_skill_effect API)
14. **GUNNER combo UI + skill effect 시스템 통합 — R75 완료** (GameState active_*, status_panel UI, GameData.skill_info, 자동 dispatch)
15. **active effect stat modifier 통합 — R76 완료** (total_attack 의 buff %, total_defense 의 stance+curse %, tick 자동 호출)
16. **★ Godot Editor 실 실행 검증 — R77 추천** (B 키 → SKILL → log fx_str + UI Combo bar + total_attack/defense 변화 시각 확인 + 사용자가 직접 게임 진행)
17. **type 22 (0x16) special path RE** — R65 미관측 case (0xd4864 영역)
18. **scn opcode 실 검증** — Title/ClassSelect/Demo 외 화면 진입 테스트
19. **Save device import/export** — 실 H_*.sav / SL_*.sav 디바이스 추출 → Godot 로드 검증
20. **SetDialogWindow 내부 RE** — @0x6ab40 의 `(byte main, byte sub)` 인자 의미 (R68 호출자 측만 봄)
21. **TEM 인자 정밀 + #11 호출 + special path 0x9b100/0x9b124** (R72/R73 잔여)
22. **LoadSkillTable disasm** — R75 의 skill_info struct byte offset → stats_u16 index 매핑 정확화

## 🚀 Round 77 즉시 시작 명령

> **다음 세션은 이 섹션 + [SESSION_HANDOFF.md](SESSION_HANDOFF.md) §D 만 보면 됨**

### 1. 환경 검증 한 줄

```bash
PYTHONIOENCODING=utf-8 python tools/verify_godot_project.py   # 0 errors / 0 warnings 기대
# 빠른 회귀 (3초): 가장 최근 5개만
python tools/h5_test_reward_types.py    # R65 Quest reward type RE
python tools/h5_test_dual_host.py       # R66 두 host 명세
python tools/h5_test_battle_motion.py   # R67 Battle motion enum + CHAR state
python tools/h5_test_dialog.py          # R68 NPC Dialog state machine
python tools/h5_test_attack_motion.py   # R69 Attack motion dispatch
python tools/h5_test_proc_hero_skill.py # R70 ProcHeroSkill 골격
```

### 2. Round 77 추천 = **Godot Editor 실 실행 검증** (사용자 작업 0.5-1 라운드)

R74-76 의 backend + UI + stat modifier 통합 완료. R77 은 사용자가 Godot Editor 에서 직접 게임을 실행해 다음 동작들을 검증.

- 검증 시나리오:
  - **B 키 → battle 시작 → SKILL action 실행** → log message 에 `+저주`/`+버프`/`+자세` fx_str 표시 확인
  - **status_panel (ESC/I)** 에 `[Combo N/M]` (GUNNER 만) + `[저주×N, 버프×M, 자세×K]` 시각 확인
  - **ATK/DEF 변화 시각 확인** — buff 적용 후 atkdef_label 의 수치 증가, curse 적용 후 DEF 감소
  - **tick 자동 만료** — 5 turn 진행 후 active effect 자동 제거 + UI 업데이트
- 사용자 환경 작업 (개발 분석 X, in-game 동작 X). 발견된 bug 는 R78+ 에서 수정.
- 대안 1: LoadSkillTable disasm (R75 매핑 정확화, 0.5 라운드)
- 대안 2: TEM 정밀 + #11 호출 (0.5 라운드)
- 대안 3: special path 0x9b100/0x9b124 (R72 미해결, 0.5 라운드)
- 대안 4: type 22 (0x16) special path RE (0.5 라운드)
- 대안 5: SetDialogWindow @0x6ab40 내부 RE (0.5 라운드)

### 3. 대안 옵션

- **ChangeAttackMotion 정밀** (0.5 라운드) — R67 의 cmp 0xd/0x14/0xe/0x17 + mov r1, #0x18/0x26 dispatch
- **type 22 (0x16) special path RE** (0.5 라운드) — R65 disasm 의 r1=#0x11 case (0xd4864 영역)
- **Skill 보유 레벨 UI 표시** (0.5 라운드) — status_panel 에 GameState.skill_levels (R57 보완)
- **scn opcode 검증** (2-3 라운드) — Title/ClassSelect/Demo 외 화면 진입 테스트
- **Save device import/export** — 실 H_*.sav round-trip 검증

한 페이지 인수인계는 [SESSION_HANDOFF.md](SESSION_HANDOFF.md).

새 클론 환경이라면 환경 복원: `python tools/h5_extract_pipeline.py`.

---

## 1. 원본 / 폴더 레이아웃

| 경로 | 내용 |
|---|---|
| `Hero5/영웅서기5(최신폰전용).apk` | 원본 APK (17 MB, 2020-11-03) — **수정 금지** |
| `work/h5/extracted/` | APK unzip 결과 (DEX, .so, assets) |
| `work/h5/vfs_entries/` | **VFS 언팩 결과 2189개** (00000_xxxx.ogg/bin/txt) |
| `work/h5/vfs_catalog.tsv` | 인덱스 / 오프셋 / 해시 / 길이 / 타입 |
| `work/h5/analysis/` | Ghidra 로그, 디컴파일 결과, 분석 스크립트 |
| `work/h5/ghidra_project/Hero5.gpr` | Ghidra 프로젝트 (재실행 시 -overwrite 주의) |
| `tools/h5_vfs_unpack.py` | VFS 언팩커 |
| `tools/ghidra/DecompileHero5Keys.java` | 핵심 함수만 디컴프 (재실행 가능) |

`tools/_game.py` 의 `h5.binary_name` 은 `lib/armeabi/libHeroesLore5.so` 로 갱신됨.

---

## 2. 바이너리 핵심 사실

- **엔진**: Midas (한빛 / EA Mobile Korea 자체엔진) — Hero3/4와 동일 계보
- **APK 패키지**: `co.kr.eamobile.HeroesLore5` v01.00.08, minSdk=23 (Android 6.0)
- **JNI 진입 클래스**: `co.kr.eamobile.CletEntry` (DEX 의 MidasActivity 는 래퍼/라이프사이클)
- **JNI exports (18개)**: nativeInitKernel → nativeInitVFS → nativeInitDisplay → nativeStartApp → nativeLoop … (완전 표준)
- **그래픽**: `libGLESv1_CM` = **OpenGL ES 1.x 고정 파이프라인** (DEX 쪽 EGL_OPENGL_ES2_BIT 는 EGL config 일 뿐)
- **ABI**: armeabi (ARMv5TE) 32-bit only — 현대 Android (특히 14+) 차단
- **debug_info / 심볼 보존**: stripped 안 됨 → Ghidra 가 함수명 그대로 인식 (Hero3/4 보다 분석 쉬움)
- **DRM**: SKT TAD SDK + 통신사 IAP — **리메이크 시 전부 제거**

---

## 3. VFS (`assets/data.vfs.mp3`) — 100% 풀림

**포맷** (little-endian, no header, no encryption):
```
[entry] uint32 hash | uint32 length | bytes data[length]
… 끝까지 반복
```

근거: `MIDASKernelManager::getAssetSizeFromVFS` 디컴프 (`work/h5/analysis/key_funcs.c` 라인 440~). `loadAssetFromVFS` 도 단순 `fread` — VFS 레벨에서는 암호화 없음.

**언팩 결과** (2026-05-06 sniffer 보정 후):
- 총 2,189 entries / 16,399,297 bytes 모두 소진 (잔여 0)
- ogg 42 / **smaf 42** / txt 1 / bin 2,104 (Midas 자체 포맷)
- 초기 sniffer 가 `MMMD` 미인식 → 사운드가 84개임이 드러남 (Hero3 의 `_mf` 와 동일한 SMAF/MMF)

재실행: `python tools/h5_vfs_unpack.py`

---

## 4. DES 키 / 암호화 위치 (열려 있는 채널)

VFS 자체는 평문이지만 **별개 레이어에 DES**가 있음:
- 심볼: `KEY4ENCRYPT` `KEY4REAL` `__DES_KEY__` (모두 .bss → 런타임 초기화)
- 함수: `MX_desInit` / `MX_desEncrypt[PKCS7]` / `MX_desDecrypt[PKCS7]`
- 호출 진입점: `StaticUtil::LoadDecryptFile` / `SaveEncryptFile` / `LoadResDecrypt`

용도 추정: 세이브 파일, 일부 보호된 리소스, 네트워크. 자산 추출 자체에는 **현재 불필요**.

키 추출이 필요해지면: `MX_desInit(char*)` 호출자 추적 → 인자 문자열 찾기 (Ghidra `References to MX_desInit`).

---

## 5. 다음 단계 (우선순위 순)

### Phase 2-A. .bin 포맷 정체 파악

#### 2-A.1 호환성 프로브 — ✅ 완료 (2026-05-06)

`tools/h5_bin_probe.py` 가 2,104개 .bin 에 Hero3/4 파서를 try-except 적용.

산출:
- `work/h5/analysis/bin_probe_matrix.tsv` (파일별 hit 매트릭스)
- `work/h5/analysis/bin_probe_summary.txt` (집계 + 매직 분포)

결과 요약:
| 포맷 | hit | 비고 |
|---|---:|---|
| smaf (`MMMD`) | 42 | ✅ Hero3 와 동일, 변환 그대로 적용 가능 |
| _pa (팔레트) | 557 | ⚠ 후보 강함. `count*4+1==len` 이 다양한 size(53/41/49…)에서 통계적으로 매칭. 색 인코딩(RGBA8888 vs RGB565)은 시각 검증 필요 |
| _cif | 144 | ⚠ 약한 시그니처(`19 19` 마커). false-positive 비율 별도 검증 필요 |
| _mp | 63 | ⚠ 첫 바이트 0x02/0x03 만으로 매칭. parse_mp 가 통과했다면 layout 은 호환 가능성 있음 |
| _txt | 0 | Hero5 스트링은 다른 포맷 |
| _bm | 0 | ❌ Hero3/4 의 `0x1f 0xf8` 프레임 마커 부재 → 스프라이트는 별도 reverse 필요 |
| **미매칭** | **1,341 (62%)** | Hero5 자체 포맷 (스프라이트/애니/맵/폰트 등). 지배 매직 `07 00 00 00`, `0d 00 00 00`, `01 00 01 00` → uint32 entry-count container 추정 |

#### 2-A.2 _pa 인코딩 확정 — ✅ 완료 (2026-05-06)

도구: `tools/h5_pa_swatch.py` (시각화) + 4-byte 위치별 엔트로피 분석.

**결정**: Hero5 _pa = `uint8 count + count × (RGB565 LE pair)` = 총 `2*count` 색.
- 근거: byte[0]/byte[2] (low byte) 와 byte[1]/byte[3] (high byte) 의 분포가 짝지어진 LE uint16 패턴.
- 검증: 557/557 candidate 모두 파싱 성공, 자연스러운 게임 팔레트 (블루-퍼플, 빨강 그라디언트 등).
- Hero3 의 RGBA8888 와는 다른 인코딩 → 별도 파서 `tools/converter/convert_h5_pa.py` 추가.

산출:
- `tools/converter/convert_h5_pa.py` — 정식 파서
- `work/h5/analysis/pa_swatches/_index.html` — 202 샘플 컨택트시트

#### 2-A.3 _mp/_cif 거짓양성 / 미매칭 클러스터링 — ✅ 완료 (2026-05-06)

**_mp 거짓양성 확정**: 63 매칭 중 sane 20개, 그러나 **이름 있는 게 0개**. Hero3 _mp 는 항상 ASCII 맵 이름(NEOSOLTIA 등)을 가짐. → Hero5 맵은 별도 포맷.

**미매칭 1,341개 → 578 distinct magic 으로 클러스터링** (`tools/h5_unknown_cluster.py`, 산출 `work/h5/analysis/unknown_clusters.txt`).

지배 클러스터들의 공통 헤더 구조 (큰 발견):
```
uint32 frame_count        // magic = LE 표현 → 1/4/6/7/12/13/17 등
uint32 total_length
uint8  0x14               // sprite-like 클러스터 거의 전부에서 상수
uint8  variant            // 0x0b — 0x10 (bit-depth / palette index 추정)
uint16 width   LE
uint16 height  LE
... pixel data ...
```

**Hero3 `_bm` 와의 관계**:
- magic `0d000000` 샘플 00760 의 offset 14 에 Hero3 의 frame marker `1f f8` 그대로 존재
- Hero5 sprite = **8-byte outer wrapper (count+length) + Hero3 _bm 계열 inner format**
- 단, Hero5 는 팔레트가 분리되어 별도 _pa 파일로 존재 (Hero3 는 frame 내부에 팔레트 임베디드)

#### 2-A.4 sprite 디코더 — ✅ 완료 (2026-05-06)

`tools/h5_frame_inspect.py` 의 bpp 분석으로 인코딩 확정:

**Outer 구조** (모든 sprite-like 클러스터 100% 일관, 409 파일 검증):
```
u32 frame_count
per frame: u32 frame_length + frame_payload[frame_length]
```

**Frame payload (type=0x14)**:
```
u8  type        // 0x14 = 표준 sprite frame
u8  palcnt      // = variant byte (0x02..0x10) — 팔레트 색 개수
u16 width  LE
u16 height LE
bytes palette[palcnt * 2]              // RGB565 LE, index 0 = 투명
bytes pixels[ ceil(w/2) * h ]          // 4-bit packed, high nibble first, 행단위 패딩
```

**검증**:
- `01252 frame[0]` w=16 h=19 var=0x0f → palette 30B + pixels 152B = 182B ✓
- `00181 frame[0]` w=65 h=22 var=0x0b → palette 22B + pixels 726B = 748B ✓
- 일괄 디코딩 결과: **426 파일 / 4,268 frame / 3,798 렌더링 (89%, 유효 sprite 100%)** / 0 에러
- 샘플 검증: `frame_00_16x19_pal15.png` → 284/304 opaque, 15 unique colors
- type=0x18 검증: `00177 frame[0]` 120x27 pal122 → 2,764/3,240 opaque, 108 unique colors

**type 바이트 의미 확정** (4가지 모두 지원):
- `0x04`, `0x14`: 4-bit packed (행단위 패딩)
- `0x08`, `0x18`: 8-bit indexed (byte-aligned)
- high nibble `0x1` vs `0x0` 의 게임 의미는 미확정 (UI vs character 추정)

**스킵 470개 = 의도적 1×1 더미 stub 전부.** 유효 sprite 미해독 0건.

산출:
- `tools/converter/convert_h5_sprite.py` — 정식 디코더
- `work/h5/converted/sprites/<file>/frame_NN_*.png` — 3,517 프레임
- `tools/h5_frame_inspect.py` — bpp/variant 분석기
- `work/h5/analysis/frame_bpp_distribution.txt`

#### 2-A.5 잔여 분류 + 한글 텍스트 추출 — ✅ 완료 (2026-05-06)

도구: `tools/h5_residual_classify.py` + `tools/h5_extract_text.py`.

**잔여 1,121개 카테고리화** (sprite/_pa/sound 제외):

| 카테고리 | 파일 | 바이트 | 비고 |
|---|---:|---:|---|
| OTHER | 508 | 158K | 50–500B 범위, 다양한 헤더 |
| LARGE_RAW | 288 | 2.4M | >1KB, 19 19 마커 없음 |
| LARGE_ANIM | 177 | 2.7M | >500B, 19 19 마커 다수 |
| TINY_META | 104 | 2.4K | ≤50B, hitbox/offset 추정 |
| MID_SCRIPT | 31 | 447K | 19 19 마커 + 한글 텍스트 다수 |
| SMALL_SCRIPT | 13 | 3.4K | 19 19 마커 포함 짧은 스크립트 |

산출: `work/h5/analysis/residual_categories.txt`

**한글 텍스트 일괄 추출** (453 파일에서 EUC-KR 추출, lead byte 0xB0–0xC8 한글 영역만):
- **46,173 string occurrences / 18,837 unique strings** (한자 false-positive 제거 후)
- 검증 어휘:
  - 캐릭터/직업: 웨이드(107), 슈르츠(64+79), 아일린(58), 나이트(75), 워리어(62), 건슬링어(69), 한손검(59), 양손검(68)
  - 장소: 센트럴(84), 콜크리크(72), 모이투라(60)
  - 몬스터/시스템: 고블린(76), 퀘스트(415), 스킬북(200), 아이템(170), 크리티컬(92), 조합법을(117), 재사용대기(57)
- 산출: `work/h5/converted/text/<file>.json` + `_corpus.txt`

**대표 발견**:
- `00055/00056/00057_641e4*.bin` = **메인 퀘스트 대사 코퍼스** (각 22KB, 동일/거의동일 — i18n 후보)
- "센트럴의 지하도에 자리잡은 고블린들을 퇴치해야…" 류 RPG 표준 퀘스트 대사 검출

#### 2-A.6 한글 필터 개선 + TINY_META 구조 단서 — ✅ 완료 (2026-05-06)

- 한글 추출 필터 개선: lead byte 0xB0–0xC8 한정 → false-positive 제거 (75K→46K, 36K→19K unique).
- TINY_META 구조 후보 발견: `(u16 count, u16 N) + 짧은 prefix record + count개 × 7-byte main record`.
  각 main record = `05 00 XX XX XX XX XX` 패턴, 0x2A–0x2D 마커 빈출.
  → **애니메이션 프레임 타이밍 / 히트박스** 후보. 정확한 의미는 Ghidra 필요.

#### 2-A.7 Hash 함수 복원 + 자산 이름 매칭 시도 — ✅ 부분 완료 (2026-05-07)

`tools/ghidra/DecompileHero5Keys.java` 의 PAT 확장으로 `MIDASKernelManager::hash` 디컴파일 성공.

**해시 함수 = DJB2-like** (`work/h5/analysis/key_funcs.c:479-502`):
```python
def hash_hero5(name: str) -> int:
    h = 0x1505                              # = 5381
    for c in name.encode():
        h = (c + h * 0x21) & 0xFFFFFFFF     # mul = 33
    return h
```

`AndroidService::getUniqueAssetNameFromID` 도 디컴파일했으나 **JNI 브리지** — 실제 이름 테이블은 Java DEX 의 `CletEntry.getUniqueAssetNameFromID(int)` 메소드 내에 있음.

**자산 이름 매칭 시도 결과**: `tools/h5_recover_names.py` 로 `classes.dex` 의 4,046 문자열 + 변형(.bin/.png/.dat 추가, 0–199 numeric suffix, 대소문자) 시도 → 직접 매칭 0건. 1건만 누적 brute-force 에서 false-positive (`IAP_PARITY_BIT148`).
**결론**: 자산 이름은 DEX 메소드 바이트코드 내 switch/case 또는 `resources.arsc` 에서 런타임 구성됨. **jadx/baksmali 없이는 추가 진전 불가**.

산출:
- `tools/h5_recover_names.py` — hash + DEX string 매처 (jadx로 더 많은 후보 확보 시 재실행)
- `work/h5/analysis/asset_names.tsv` — 1건 false-positive
- `work/h5/analysis/key_funcs.c:479-502` — hash 함수 디컴파일

#### 2-A.8 DEX 메소드 분석 — ✅ 완료 (2026-05-07)

`tools/h5_dex_extract_names.py` (순수 Python DEX 파서, 의존성 없음) 으로 `classes.dex` 의
모든 메소드를 walk 하며 const-string 시퀀스 + 메소드 dump 생성.

**핵심 발견** — `getUniqueAssetNameFromID` 는 **양쪽 모두 stub**:
- `Lco/kr/eamobile/CletEntry;::getUniqueAssetNameFromID` (7 code units): `setContentView` 호출 후 return.
- `Lco/kr/eamobile/resource/MidasAssetManager;::getUniqueAssetNameFromID` (13 code units): `getResources/finish` 호출 후 return null.
- → 자산 이름 → ID 매핑은 **빌드 타임에 계산되어 native binary 에만 존재**, Java 측엔 없음.

**brute-force 한계 검증** — `tools/h5_recover_names_v2.py`:
- pool: DEX strings (4,046) + libHeroesLore5.so 식별자 (6,529 unique) = 8,313개
- 변형 (확장자 17종 × 대소문자 × path-sep + numeric suffix 0–999 + 30 prefix × 0–999):
  추정 총 ~30M candidate hash 평가
- 결과: **5건 매칭 (`version.txt` 1건만 진짜)**, 나머지 4건은 32-bit DJB2 충돌 false-positive
- 결론: 8K base × 변형으론 32-bit hash space 충분히 못 메움. **이름 리스트 자체가 native binary 안에 packed 되어 있을 가능성 높음** — Ghidra 로 `loadAssetFromVFS` caller 추적 시 string array 발견 여부 확인 필요.

산출:
- `tools/h5_dex_extract_names.py` — DEX 메소드 파서 + 명령어 dump
- `tools/h5_recover_names_v2.py` — 확장 brute-force
- `work/h5/analysis/dex_const_strings.tsv` — 449 메소드 × const-string 시퀀스
- `work/h5/analysis/asset_name_candidates.txt` — 1,236 unique const-string 값
- `work/h5/analysis/so_strings.txt` — 6,529 unique .so 식별자 후보

#### 2-A.9 TINY_META 정식 파서 — ✅ 완료 (2026-05-07)

`tools/converter/convert_h5_meta.py`. 가설(2-A.6) 검증 후 **kind=row-width 파라미터** 발견 (kind=3, 5 두 종 확인).

**확정 포맷**:
```
u16 total_count
u16 kind                              ; row payload width parameter
prefix row [kind bytes]:
   [0]=kind, [1]=body_count, [2:]=prefix_payload
body_count rows × (kind+2) bytes each:
   [0]=kind, [1]=subtype (보통 0x00), [2:kind+2]=payload (0xff = 빈 슬롯, 0x2a-0x2d = field marker)
```

총 파일 사이즈 = `4 + kind + body_count × (kind+2)`.

검증:
- 00075/76/78 (30B): total=4, kind=5, body=3 → 4+5+21=30 ✓
- 00077 (44B): total=6, kind=5, body=5 → 4+5+35=44 ✓
- 00080 (32B): total=6, kind=3, body=5 → 4+3+25=32 ✓ (kind=3 케이스)

**결과**: ≤50B bin 후보 356개 중 **7개 strict match** (kind 5×6 + kind 3×1). 나머지 349개는 다른 mini-format (`0100`, `09ee`, `0b6a` 등 별도 시그니처). residual 의 TINY_META 카테고리(104) 중 일부만이 이 표준형식이고 나머지는 다른 small-record container.

산출:
- `tools/converter/convert_h5_meta.py` — 파서
- `work/h5/analysis/tiny_meta.tsv` — row-level dump
- `work/h5/analysis/tiny_meta_summary.txt` — 통계

#### 2-A.10 자산 이름 99.3% 복원 — ✅ 완료 (2026-05-07)

**돌파구**: Ghidra 로 `loadAssetFromVFS` caller 추적 → `getAssetSizeFromVFS(this, assetname, ...)`
가 **string 직접 사용** 확인 → 이름이 native binary 안에 sprintf format-string 으로 박혀 있음.

`.so` 의 모든 format string 스캔 (`tools/h5_recover_names.py` pass 1):
```
c/calc/calc_<region>.dat       c/csv/<table>.dat / enemy_/item_/quest_/skill_/etc
c/csv2/help_<region>.dat        c/font/{eng,kor}.fnt + table.dat + type.dat
c/img/<ui>.mgr                  c/sp/img{0..6}/%03d.mgr
c/sp/cif/%03d.cif               c/sp/ext/%03d.ext
c/sp/imgcom/<named>.mgr         c/sp/empty/empty.mgr
c/sp/pal/%03d.pal (557개)       c/map/{face_%02d, obj_%03d, fgi_%03d, tile_%03d}.gbm
c/map/seaani_%03d.pal           c/map/%05d.scn (5-digit numeric scenes)
c/map/(md)%02d                   c/map_sp/{fgi%03d, ms%03d, ms_img%02d.mgr, %03d.ext}
c/mon/%d_ai                     c/par/{p%03d, ps%03d, pimg%02d.mgr, pinfo.dat}
c/snd/{bgm_%02d, eff_%02d}.{ogg,mmf}
c/iconpal/{226..232}_%03d.pal   c/ep/ep_%d/s%d_%03d.scn
```

**결과 진행**:
| 단계 | 매칭 | 누적% |
|---|---:|---:|
| pass 1 (.so suffix slice) | 78 | 3.6% |
| pass 2 (sprite/pal numeric) | 1,205 | 55.0% |
| pass 3 (map/snd/par/mon/ep + map %05d.scn) | 2,171 | 99.2% |
| pass 4–7 (iconpal/csv/named) | 2,174 | **99.3%** |

**잔여 15개**: 짝지어진 동일 크기 (1141/1142, 1644/1645) i18n 추정 + 큰 파일 (37KB) + 작은
isolated bins. 후속 작업으로 보류.

**False-positive 위험**: 32-bit DJB2 충돌 가능성 있으나, 패턴이 매우 구조적
(c/<dir>/<numbered>) 이고 90% 이상이 연속 인덱스 클러스터로 매칭되어 매우 낮음.

산출:
- `tools/h5_recover_names.py` — 통합 복원기 (pass 0–7)
- `tools/h5_dex_extract_names.py` — DEX 파서 (CletEntry/MidasAssetManager 분석 확인)
- `tools/ghidra/FindAssetNameTable.java` — caller XREF + .rodata string-array 스캐너
- `tools/ghidra/DecompileNameLookup.java` — `getUniqueAssetNameFromID` JNI 브리지 본문
- `work/h5/analysis/asset_names.tsv` — **2,174 / 2,189 (99.3%) 복원된 이름**
- `work/h5/analysis/asset_callers.c` — caller 디컴파일
- `work/h5/analysis/name_lookup.c` — JNI 브리지 + hash 함수

**핵심 발견 (PROGRESS 6.2 [P1] 가설 수정)**:
- `MidasAssetManager.assetNameFromNumericHash` (Java Hashtable) 는 **DEX 에서 절대 populate 안 됨**
- C++ `AndroidService::getUniqueAssetNameFromID` 는 JNI 로 빈 Hashtable 을 lookup 하므로 **항상 null 반환**
- → 게임 코드는 native side 에서 **string literal 직접 사용** (`MC_knlGetResourceID(name)` 등)
- → 이름 → ID 매핑은 빌드 타임에만 존재, 런타임에는 hash 만 사용

#### 2-A.11 .scn 포맷 분석 — ✅ 헤더 완료 (2026-05-07)

`EventProc::Scene_Init @ 0x000823a8` 디컴파일 (`work/h5/analysis/scn_loader.c`) 으로
.scn 파일 로드 흐름 확정:

1. **경로 생성**: `MC_knlSprintk(buf, "/c/map/%05d.scn", mapNum)` 또는
   `"/c/ep/ep_%d/s%d_%03d.scn"` (mode 따라 분기).
2. **로드**: `StaticUtil::LoadRes(path, &size)` — `loadAssetFromVFS` 의 사용자 래퍼.
3. **헤더 파싱** (11 bytes, sequential cursor):
   ```
   u8 flag1, flag2, state, mapID, dialogID, b5, startX, startY, startDir, b9, b10
   ```
4. **타일/이미지**: 별도 `c/map/{face,obj,fgi,tile,seaani}_NN.gbm` 파일을
   `mapID` 인덱스로 `Map::LoadData` / `Map::LoadImage` 가 로드.
5. **나머지 body**: `Interpreter::open(scn_buf+11, &cursor, flag1, flag2)` —
   이벤트 스크립트 바이트코드. opcode 정의는 `Token::*` / `Interpreter::execute`
   추가 분석 필요 (Phase 3 진입 후 우선과제).

**결과** (`tools/converter/convert_h5_scn.py`):
- 258/258 .scn 파일 헤더 파싱 성공 (100%)
- 67개 unique mapID → 실제 맵 데이터 세트 67개, 시나리오 258개
- 모두 state=1 → flag2 매직 분기 ('mmonUiC1Ev' 호환) 적용됨
- body 평균 276B (대사+이벤트 스크립트)

산출:
- `tools/ghidra/FindSceneLoader.java`, `DumpScnRef.java`, `DumpInterpreter.java`
- `work/h5/analysis/scn_loader.c` — Scene_Init 본문
- `work/h5/analysis/scn_headers.tsv` — 258개 헤더 dump
- `work/h5/analysis/scn_summary.txt` — mapID/body-size 분포

#### 2-A.12 다음 단계 (Phase 2 마무리)

1. ~~DEX 디컴파일러~~ → **차단 확정** (2-A.8). Java 메소드는 stub. 다음 단계는 **native binary 안의 string array 추적** — Ghidra 에서 `loadAssetFromVFS` 의 caller 들이 참조하는 .rodata 영역 string-pointer 배열을 찾아야 함.
2. ~~TINY_META 정식 파서~~ → 완료 (2-A.9). 다음: **payload 의 5 슬롯 의미 확정** — Ghidra 로 `MIDASKernelManager` 내 7-byte record 를 `fread` 하는 함수 검색.
3. **MID_SCRIPT/LARGE_ANIM 의 19 19 마커 의미** — 청크 분리자/프레임 표지자/end-of-record 후보.
4. **`loadAssetFromVFS` caller 분석** — `assetID` 가 어디서 어떤 컨텍스트로 오는지 → 파일 용도 분류 + 이름 테이블 위치 후보.
5. **Phase 3 진입** — 엔진 결정 (Unity 권장) + 자산 임포트 파이프라인.

### Phase 2-B. 자산 파일명 복원 — ⚠ 부분 완료
- ✅ Hash 함수 복원 (DJB2-like, 2-A.7 참조)
- ✅ `AndroidService::getUniqueAssetNameFromID` 디컴파일 (JNI 브리지로 확인)
- ❌ 이름 테이블은 Java DEX 내부 → **jadx/baksmali 필요**

### Phase 2-C. JNI 호출 흐름 → 게임 루프 정리
`Java_..._nativeLoop` 와 `MIDASKernelManager::timerLoop` 부터 시작. 60fps tick / event handling / render 호출 순서를 그래프로.

### Phase 3. 리메이크 엔진 결정 + 재구현 — ✅ 스캐폴드 완료 (2026-05-07)
**상세는 [PHASE3_ENGINE.md](PHASE3_ENGINE.md) + [apps/hero5-godot/README.md](../../apps/hero5-godot/README.md).**
- 엔진: **Godot 4** 확정.
- 자산 임포트 파이프라인: `tools/import_to_godot.py` — 5,000+ 자산 자동 변환.
  - sprites: 3,798 frame PNG
  - gbm: 342 map/face/obj/fgi 이미지
  - palettes: 588 JSON RGBA
  - text: 453 한글 JSON
  - sounds: 42 OGG (SMAF 미포함)
  - scenes: 258 .scn 메타 인덱스
- 검증 씬: `apps/hero5-godot/scenes/main.tscn` — face 토글 + 한글 코퍼스 표시.

#### 다음 본구현 작업
- [ ] Interpreter opcode → 이벤트 매핑 (164 opcode 의미 매핑)
- [ ] Map 렌더러 (tile/fgi/obj 레이어 합성)
- [ ] CHAR/HERO 시스템 (4방향 애니메이션)
- [ ] kor.fnt 임포트 / 한글 폰트
- [ ] SMAF → OGG 변환

---

## 6. 다음 세션 즉시 재개 체크리스트

### 6.1 현재 상태 한눈에 (2026-05-10, Round 25 종료)

**최근 (Round 6~19) 누적 발견 — Formula VM 변수 라벨 / EquipItemInfo struct / 카테고리 별 layout**:

| 영역 | 라운드 | 핵심 결과 |
|---|---|---|
| Formula VM gv stat | R6~12 | V[58]=level, V[60..63]=str/dex/con/int (R11 정정), V[111..116]=근접명중/장거리명중/회피/방패방어/크리티컬, V[122..126]=5 buff slot (EXP%/SP감소%/CP충전/쿨타임/포션효과), V[151..155]=magic/con/str/max_sp |
| ApplyBuildupEffect entry table | R9 | jumptable 자동 추출 (`tools/h5_apply_buildup_disasm.py`), 56 entry × 2 함수 |
| EquipItemInfo struct field | R13~17 | +0x14=subtype, +0x155=class subtype, +0x15d=level_limit, +0x15f & 0x1f = 5-class mask (W/R/G/K/S), +0x165..+0x167=refine fields, +0x168..+0x16d=6 socket |
| ItemBase struct (Formula VM 5번째 인수) | R13 | V[168..182] = SP cost / cooldown / damage growth / divisor 등 |
| LoadItemTable csv 매핑 | R14/18/19/20/21 | 가변 layout (name + sub_record) + u8/u16 mixed sequence. cat 12-18 모든 카테고리별 추가 fields 추출. R21: slot_16 도 SkillBook 임이 확인 (Warrior+Rogue) |
| items.json named fields | R15/16/19/20/21 | subtype / class_mask / class_label / level_limit / item_id / sub_record / val_134..val_167 / triplet_162 / sub_record_hex / **class_id, skill_index, skill_level, required_level** (slot_16, slot_17) |
| HERO::IfLearnSkill 분석 | R21 | (class_id/2)+16 → ItemTable category 공식. SkillBook +0x134..+0x137 의미 (class_id/skill_index/skill_level/required_level) 확정 |

**전체 진행 (Phase 2/3 완료 항목)**:


| 영역 | 상태 | 산출물 |
|---|---|---|
| VFS 언팩 | ✅ 2,189/2,189 (100%) | `work/h5/vfs_entries/` + `vfs_catalog.tsv` |
| 사운드 (ogg + SMAF) | ✅ 84/84 | `*.ogg`, `*.smaf` (SMAF→OGG 변환 추후) |
| 팔레트 _pa | ✅ 557 파싱 (RGB565 LE pair) | `tools/converter/convert_h5_pa.py` |
| 스프라이트 | ✅ 426 파일 / 3,798 PNG (유효 100%) | `tools/converter/convert_h5_sprite.py`, `work/h5/converted/sprites/` |
| 한글 코퍼스 | ✅ 18,837 unique strings | `work/h5/converted/text/_corpus.txt` |
| Hash 함수 | ✅ DJB2 (init=0x1505, mul=0x21) | `tools/h5_recover_names.py` |
| 자산 이름 복원 | ✅ 2,182 / 2,189 (99.7%) — .so format-string + region 변형 | `tools/h5_recover_names.py`, `work/h5/analysis/asset_names.tsv` |
| Anim/Script 파서 | ✅ 300 파일 record 분리 (sentinel 19 19 + 20 20) | `tools/converter/convert_h5_anim_script.py` |
| .scn 헤더 파서 | ✅ 258/258 파일 — 11B 헤더 + Interpreter 바이트코드 | `tools/converter/convert_h5_scn.py` |
| .scn body 디스어셈블 | ✅ 258 파일, 164 unique opcode | `tools/converter/disasm_h5_scn.py` |
| .gbm 디코더 | ✅ 342/342 (100%) — 4/8-bit indexed → PNG | `tools/converter/convert_h5_gbm.py` |
| Opcode 매핑 | ✅ 77/77 — `EventProc::onFunction` switch 분석 | `tools/h5_extract_opcode_table.py`, `work/h5/analysis/opcode_table.tsv` |
| Map 렌더러 | ✅ 4-layer (tile/obj/fgi/face) Sprite2D 합성 | `apps/hero5-godot/scripts/core/map_renderer.gd` |
| 캐릭터 시스템 | ✅ 4방향 이동 + 자동 frame 애니메이션 (CHAR 클래스 매핑) | `apps/hero5-godot/scripts/core/character.gd` |
| Interpreter 실행기 | ⚠ 골격만 (77 opcode dispatch + console log, dialog/move 실제 처리 후속) | `apps/hero5-godot/scripts/core/interpreter.gd` |
| 타이틀/데모 씬 | ✅ Title → Demo (map+character+interp) 흐름 | `apps/hero5-godot/scenes/title.tscn`, `demo.tscn` |
| 맵 데이터 (md)NN | ✅ 67 파일 헤더+섹션 인덱스 (10–14 sections per file) | `tools/converter/convert_h5_mapdata.py` |
| Interpreter 핸들러 | ✅ Teleport/Direction/Delay/ChangeBgm/TileChange + set_handler 훅 | `apps/hero5-godot/scripts/core/interpreter.gd` |
| 세이브/로드 | ✅ 평문 JSON, 8 slot, version 관리 | `apps/hero5-godot/scripts/core/save_manager.gd` |
| 한글 폰트 | ✅ eng=95×(8×11), kor=581×(16×11) PNG 시트 변환 | `tools/converter/convert_h5_fnt2png.py` |
| Dialog UI | ✅ typewriter 효과 + 한글 표시 + Interpreter 연결 | `apps/hero5-godot/scripts/ui/dialog_box.gd` |
| Status/Inventory UI | ✅ HP/SP/Lv/Gold/인벤토리 패널 (ESC/I 토글) | `apps/hero5-godot/scripts/ui/status_panel.gd` |
| Map Collision | ✅ 67/67 (md) → JSON+col.bin+tile.bin, MapRenderer 통합 | `tools/converter/convert_h5_collision.py` |
| CSV 게임 데이터 | ✅ 85 .dat → JSON (record format 확정), GameData 싱글톤 | `tools/converter/convert_h5_csv.py`, `scripts/core/game_data.gd` |
| 전투 시스템 | ✅ 골격 (4 액션: 공격/스킬/방어/도망) | `apps/hero5-godot/scripts/core/battle_system.gd` |
| Class stats 디코딩 | ✅ 5 클래스 STR/DEX/INT/CON 추출 (워리어/로그/건슬링어/나이트/소서러) | `tools/converter/decode_h5_class.py` |
| 전투 UI | ✅ Enemy/Player HP bar + 4 action 버튼 + 로그 | `apps/hero5-godot/scenes/battle.tscn` |
| Collision 디버그 | ✅ 통과/막힘 오버레이 (C 키 토글) | `MapRenderer.show_collision_debug` |
| 한글 자모 조합 | ⚠ 게임 자체 인코딩 (표준 EUC-KR 아님), 추가 RE 필요 | — |
| DES key | ✅ `0EP@KO91` 추출 (MX_desInit caller @ 0x001688b0) | `tools/ghidra/DumpDes.java` |
| **DES 변종 해독** | ✅ 표준 DES + S1[3][10]=2 단일 수정 — `mx_des_decrypt(body, key)` MD5 검증 통과 | `tools/h5_des.py`, `tools/h5_decrypt_calc.py`, [`DES_VARIANT.md`](DES_VARIANT.md) |
| **calc_*.dat 평문** | ✅ 3개 파일 MD5 검증 통과 (calc_pl 1584B, calc_en 624B, calc_sk 4680B) | `work/h5/analysis/calc_*_plain.bin` |
| **Formula VM 디스어셈블러** | ✅ 186 공식 (39+19+128) infix 표현 dump, size mismatch 0 | `tools/h5_formula_disasm.py`, `work/h5/analysis/formulas_disasm.txt` |
| Fixed-size csv | ✅ enemy_g (166×121B), npc_g (81×27B) → JSON | `tools/converter/decode_h5_fixed.py` |
| GameState 통합 | ✅ 싱글톤 + state_changed signal + battle 보상 적용 + quick save/load | `apps/hero5-godot/scripts/core/game_state.gd` |
| enemy_g 121B layout | ✅ HP/MP/ATK/DEF/EXP/Gold + 5×16B skill slot 추출 (15/166 valid) | `tools/converter/decode_h5_enemy.py` |
| Walk-cycle 애니 | ✅ 4방향 walk_frames + stand_frames 시퀀스 자동 전환 | `character.gd` |
| Interpreter 핸들러 | ✅ 확장 (Camera/Effect/Move/Teleport/Quest/Warp 등 +15 종) | `interpreter.gd` |
| Android export 가이드 | ✅ arm64-v8a 64bit, min SDK 23 / target 34 설정 템플릿 | `apps/hero5-godot/export_presets.cfg.template`, `README.md` |
| MVP 정합성 검증 | ✅ tscn/gd reference 체크, 0 errors / 0 warnings | `tools/verify_godot_project.py` |
| enemy 정확도 | ✅ stride 공식 수정 (4 + i × 121), 75/166 valid HP/MP 확인 | `tools/converter/decode_h5_enemy.py` |
| NPC table | ✅ 81 × 27B 디코딩 + Demo E 키 인터랙션 | `tools/converter/decode_h5_npc.py` |
| Quest 데이터 | ✅ 105 quest 이름 + 72 tree 노드 (mission_list + questTree) | `tools/converter/decode_h5_quest.py` |
| GameData API 확장 | ✅ skills_for_class / items_in_slot / drop_table / shop_inventory / smith_recipes / enemy_stats | `apps/hero5-godot/scripts/core/game_data.gd` |
| 전투 시스템 — 실데이터 | ✅ enemy_table HP 기반 + 클래스 스킬 이름 표시 (양손베기/돌진/...) | `battle_system.gd` |
| Skill 분석 | ✅ 215 스킬 (5×43) 이름 + type + 한글 설명 분리 | `tools/converter/decode_h5_skill.py` |
| Item 디코드 | ✅ 19 슬롯, 1,360 명명 아이템 (포션/스킬북/장비), price=stats[0] | `tools/converter/decode_h5_item.py` |
| Quest tree | ✅ 72 노드 (대부분 root sequential, type=5) | quests.json |
| 사운드 hookup | ✅ Audio 싱글톤 + Event_Scene_ChangeBgm 핸들러, demo 자동 BGM | `apps/hero5-godot/scripts/core/audio_manager.gd` |
| Drop/Shop/Smith/Quest text/Rewards | ✅ 252+9+96+453+285 record 추출 | `tools/converter/decode_h5_misc.py` |
| Quest 진행 시스템 | ✅ Quest 싱글톤 + start/complete + Interpreter QuestStatus 핸들러 | `apps/hero5-godot/scripts/core/quest_system.gd` |
| Title slot 선택 | ✅ New Game / Continue + slot list 표시 | `apps/hero5-godot/scripts/ui/title.gd` |
| Skill 템플릿 resolver | ✅ `#NN` → stats_u16[NN] 치환 (예: 재사용대기 9초, 공격력 120%) | `game_data.gd::resolve_skill_desc` |
| Equipment 슬롯 | ✅ 6 슬롯 (무기/방어구/투구/장화/악세×2) + equip/unequip API | `game_state.gd` |
| Inventory UI 확장 | ✅ 장비 슬롯 표시 + 인벤토리 분리 | `status_panel.gd` |
| Combat 정밀 | ✅ MP 코스트 + cooldown + damage_pct (skill stat 사용) | `battle_system.gd` |
| Map NPC 스폰 | ✅ npc_table flags[0,2,3] = sprite/x/y → 마커 + 라벨 | `map_renderer.gd::spawn_npcs` (P키) |
| Item stat 정밀 | ✅ slot_0 무기 stats[7]=ATK, stats[0]=price 확정 | `game_data.gd::item_stat` |
| Damage popup | ✅ Tween 으로 -N 숫자 떠오름 + 페이드아웃 | `damage_popup.gd` |
| Dialog 선택지 | ✅ show_choices() + Quest 트리거 (NPC 분기 데모) | `dialog_box.gd::show_choices` |
| Scene → Hero 위치 | ✅ scene 헤더 startX/Y 로 캐릭터 tile 좌표 자동 배치 + BGM 전환 | `demo.gd::_apply_scene` |
| 상점 UI | ✅ ShopPanel — 무기 4 슬롯 × 4 offer 구매/판매 + 골드 차감 | `apps/hero5-godot/scripts/ui/shop_panel.gd` |
| 레벨업 자동 | ✅ STR/DEX/INT/CON 클래스별 분배 + lvl 5/10/15... 스킬 해금 | `game_state.gd::add_battle_reward` |
| NPC 가까움 감지 | ✅ Manhattan 거리 기반 nearest_npc(px, py, dist) | `map_renderer.gd::nearest_npc` |
| 다중 세이브 슬롯 | ✅ Title 에 slot 버튼 자동 생성 + Demo 1-8 저장 / Shift+1-8 로드 | `title.gd`, `demo.gd` |
| 레벨업 popup | ✅ DamagePopup으로 "LEVEL UP! → N" + dialog 알림 + 해금 스킬 표시 | `demo.gd::_on_level_up` |
| 장비 stat 자동 적용 | ✅ equipment_bonus / total_attack/defense → 전투에 반영 | `game_state.gd` |
| Quest UI | ✅ 활성/완료 분리 ItemList + 정보 패널 (Q키) | `quest_panel.gd/.tscn` |
| BGM cross-fade | ✅ 0.3+0.3s tween 으로 부드러운 전환 | `audio_manager.gd::_fade_swap` |
| 클래스 선택 화면 | ✅ Title → New Game → Class Select → Demo (5 클래스 + stat) | `apps/hero5-godot/scenes/class_select.tscn` |
| NPC sprite 텍스처 | ✅ sprite_id → sprites/imgN/NNN/frame_00 자동 검색 (없으면 색박스) | `map_renderer.gd::_try_load_npc_sprite` |
| 포션/장비 사용 | ✅ inv 더블클릭 → 포션 사용 (HP+30) / 무기/방어구 자동 장착 | `status_panel.gd::_use_item` |
| 세이브 메타 확장 | ✅ play_time/class_id/stats/equipment/unlocked_skills/quest 포함 | `save_manager.gd::make_payload` |
| Sprite name → dir 매핑 | ✅ 405 sprite_index.json + AssetLoader.sprite_dir() API | `tools/import_to_godot.py`, `asset_loader.gd` |
| Title 로고 자동 | ✅ `c/sp/imgcom/title.mgr` → 자동 첫 frame 로딩 | `title.gd` |
| Stat 분배 UI | ✅ Status panel +STR/+DEX/+INT/+CON 버튼, 레벨업당 +3 점수 | `status_panel.gd`, `game_state.gd::allocate_stat` |
| Battle 적 sprite | ✅ enemy flags_a[0]=sprite_id 로 첫 frame 표시 | `battle_ui.gd::_load_enemy_sprite` |
| Quest 보상 자동 | ✅ complete 시 gold + exp + 미들포션 자동 지급 | `quest_system.gd::_grant_reward` |
| Quest 처치 카운트 | ✅ on_enemy_killed → 카운트/목표 추적 + 자동 complete | `quest_system.gd::on_enemy_killed` |
| Map warp trigger | ✅ collision 0x40-0x7F = 다음 scene 인덱스, hero.moved signal 연동 | `map_renderer.gd::check_warp` |
| NPC 한글 대사 | ✅ quest_text.json 의 한글 발췌 → NPC 대화로 표시 (3 episodes) | `game_data.gd::quest_dialogue` |
| 이펙트 애니메이션 | ✅ EffectAnim.spawn_at() — c/sp/imgcom/eff frame 시퀀스, 12fps | `effect_anim.gd` |
| HUD | ✅ 상단 HP/SP bar + Lv + Gold (state_changed 자동 갱신) | `apps/hero5-godot/scripts/ui/hud.gd` |
| 슬롯 삭제 UI | ✅ Title 에서 우클릭/Shift+클릭 → AcceptDialog 확인 → delete | `title.gd::_confirm_delete` |
| NPC 색상 분류 | ✅ flags[6] 따라 일반/적대/상인/퀘스트 4 색 modulate | `map_renderer.gd` |
| Inventory 필터 | ✅ 전체/무기/방어/포션/기타 5 탭 | `status_panel.gd::_matches_filter` |
| HP/SP 회복 | ✅ 비전투시 2초마다 max/50 HP, max/30 SP 회복 | `game_state.gd::_process` |
| 장비 비교 툴팁 | ✅ inv hover 시 ATK 값 + 현재 무기 대비 차이 표시 | `status_panel.gd::_on_item_hover` |
| Mini-map | ✅ 우상단 64×64 collision + warp + hero/NPC 마커 | `minimap.gd/.tscn` |
| Settings 패널 | ✅ BGM/SFX 볼륨 슬라이더 + FPS/Fullscreen 토글 | `settings_panel.gd` (X키) |
| 자동 적 인카운터 | ✅ 25 step 후 10% 확률 (UI 열림 시 skip) | `demo.gd::_on_hero_moved` |
| 자동 저장 | ✅ slot 7 (AUTO_SLOT) 60초 간격 + oldest_slot() API | `save_manager.gd::auto_save`, `game_state.gd` |
| Tile attribute 디버그 | ✅ V키 토글 — tile_id 별 색상 + 숫자 표시 | `map_renderer.gd::_draw` |
| Quest 보상 정밀 | ✅ rewards.json 의 6B record (type byte) → gold/exp/item 분기 | `quest_system.gd::_grant_reward` |
| Battle turn 표시 | ✅ "턴 N — 플레이어/적이름" + 색 변경 + 버튼 비활성화 | `battle_system.gd`, `battle_ui.gd` |
| Inventory 정렬 | ✅ default/name/price cycle (정렬 버튼) | `status_panel.gd::cycle_sort` |
| Quest 토스트 | ✅ 시작/완료 시 우상단 잠시 + 페이드 | `apps/hero5-godot/scripts/ui/toast.gd` |
| Settings 영구 저장 | ✅ user://config.cfg (BGM/SFX/FPS/fullscreen) | `settings_panel.gd::_save_config` |
| 도주 % 표시 | ✅ flee_chance() (HP%/DEX/turn 기반) → 버튼 라벨 실시간 갱신 | `battle_system.gd`, `battle_ui.gd` |
| Help 패널 | ✅ H 키 — 모든 단축키 BBCode 표시 | `help_panel.gd/.tscn` |
| Map 이름 표시 | ✅ 씬 진입 시 화면 중앙 큰 라벨 2초 + 페이드 | `demo.gd::_show_map_name` |
| 메뉴 별 BGM | ✅ Title bgm_00, ClassSelect bgm_01, Demo mapID%21 | `title.gd`, `class_select.gd` |
| ATK/DEF 합산 표시 | ✅ Status panel 에 total + 장비 보너스 분리 표시 | `status_panel.gd::_apply`, `status_panel.tscn` |
| 방어구 hover 비교 | ✅ 무기/방어구/포션 자동 분류, 슬롯별 ATK 또는 DEF diff | `status_panel.gd::_on_item_hover` |
| Battle 결과 popup | ✅ 승리 시 EXP/Gold/획득 아이템 패널 + 확인 버튼 (4초 자동 닫힘) | `battle_ui.gd::_show_victory_popup` |
| Battle drop | ✅ enemy stats exp/gold + 25% drop_table roll, items 배열 emit | `battle_system.gd::_finish/_roll_drops` |
| 씬 전환 fade | ✅ Title↔ClassSelect↔Demo 0.3s 검정 fade-out / fade-in | `scripts/ui/scene_fader.gd` |
| OPCODE_TABLE 확장 | ✅ 77/77 — BASE_TABLE 38 + 외부 opcode_table.json 자동 머지 (.so disasm 추출) | `interpreter.gd::BASE_TABLE/_try_load_external` |
| Dispatch 정리 | ✅ 중복 case 제거, Quest/Situate/Scene 핸들러 정렬, 외부 JSON 활성화 시 자동 매칭 | `interpreter.gd::_dispatch` |
| Scene body 자동 실행 | ✅ import 시 .scn body 11B 이후를 `assets/scenes/bodies/<idx>.bin` 저장, run_intro 가 step() 호출 | `import_to_godot.py::import_scn_index`, `demo.gd::_run_intro` |
| Quest opcode 핸들러 | ✅ 0x29 Boss / 0x2a QSwitch / 0x2b Status / 0x2c Switch — `.so disasm 검증` | `demo.gd::_on_quest_*` |
| Opcode 77/77 추출 (Ghidra-free) | ✅ ARM disasm + jumptable 추적 → opcode_table.tsv/json 자동 생성 | `tools/h5_extract_opcode_disasm.py`, `apps/hero5-godot/assets/scenes/opcode_table.json` |
| Event 함수 mangle 분석 | ✅ 105 Event_* 식별자 → arg_size 자동 룩업 (Itanium ABI demangle) | `tools/h5_event_arg_sizes.py`, `analysis/event_arg_sizes.tsv` |
| BASE_TABLE 매핑 수정 | ✅ Quest 0x31~0x42 추측 → 정확한 0x29~0x2d (.so 검증), Scene_ChangeBgm dead entry 제거 | `interpreter.gd::BASE_TABLE` |
| 자산 환경 복원 | ✅ APK 재추출 + VFS 2189 unpack + 99.7% 이름 + 421 sprite / 588 pal / 258 scn body | tools 전체 |
| enemy_g layout 검증 | ✅ Map::MapEnemyG_set + ByteToInt16 disasm — HP/MP/ATK/DEF/EXP/Gold offset 0x0c~0x16 LE u16 확정 | `tools/h5_extract_enemy_layout.py`, `decode_h5_enemy.py` |
| Battle 정확도 | ✅ enemy DEF 데미지 차감 + EXP/Gold 검증된 stat 사용 + sentinel(65535) 자동 fallback | `battle_system.gd::_stat_or/_finish` |
| .fnt 분석 | ⚠ 헤더만 (HNF eng=8×11/92 chars, kor=16×11/580 chars) | `tools/converter/convert_h5_fnt.py` |
| SMAF 변환 | ⚠ 미구현 (외부 도구 필요), OGG 42개로 대체 가능 | `tools/converter/convert_h5_smaf.py` |
| TINY_META 파서 | ✅ 7/356 strict match (kind 3·5 변형 확정) | `tools/converter/convert_h5_meta.py` |
| Ghidra 프로젝트 | ✅ 함수 19개 디컴파일 | `work/h5/ghidra_project/Hero5` |

### 6.2 완료된 우선순위 작업 (2026-05-08 일괄 완료)

> Phase 2 (자산 추출/디코딩) + Phase 3 (Godot 엔진 + 게임 시스템) + 모든 우선순위
> 작업 완료. 현재 상태와 다음 작업은 [SESSION_HANDOFF.md](SESSION_HANDOFF.md) 참조.

**[P2] enemy_g 121B layout — ATK/DEF 정확도** — ✅ 완료 (2026-05-08)
- `Map::MapEnemyG_set` 디스어셈블 + `StaticUtil::ByteToInt16` 분석으로 121B record 의
  byte layout 100% 확정. 도구: `tools/h5_extract_enemy_layout.py`.
- 기존 PROGRESS hint (HP@0x0c, MP@0x0e, ATK@0x10, DEF@0x12 LE u16) 가 **이미 정답**
  이었음을 .so disasm 으로 검증. 추측 → 검증 끝.
- 추가 발견: stat5/stat6 = EXP@0x14, Gold@0x16 (LE u16). flags_b 영역은 0x18..0x23
  (12 byte). 5× skill slot 시작은 0x24 (기존 코드의 0x27 보다 3 byte 당김).
- 65535 sentinel 처리 통합: `battle_system._stat_or()` 가 invalid 값 자동 fallback.
- 결과: HP 75/166 valid (PROGRESS 핸드오프와 정확히 일치), ATK 7/166, DEF 4/166.
  나머지는 enemy_g 의 sparse 영역 — 게임이 사용 안 함.

**[P1] Interpreter opcode 자동 dispatch** — ✅ 77/77 완료 (2026-05-08)
- ARM disasm + jumptable 추적으로 `EventProc::onFunction` 의 77 case 모두 자동 추출
  (`tools/h5_extract_opcode_disasm.py`, capstone + lief). Ghidra 불필요.
- 산출: `apps/hero5-godot/assets/scenes/opcode_table.json` (77 entries) — interpreter.gd
  의 외부 로더가 자동 머지 → BASE_TABLE 38 ↔ 외부 77.
- **BASE_TABLE 의 잘못된 추측 매핑 수정** (.so disasm 으로 검증):
  - Quest 계열 0x31~0x42 → 실제 0x29~0x2d (PROGRESS hint 가 추측이었음)
  - `Event_Scene_ChangeBgm` 은 실제로 dispatch table 에 없음 — BGM 변경은
    `demo._apply_scene` 의 `Audio.play_bgm` 직접 호출로만 처리.
- demo.gd `set_handler` 호출 정확한 op 로 수정 (0x29/0x2a/0x2b/0x2c).
- demo.gd `_run_intro` 가 dead `Interp.new()` 대신 멤버 `_interp` 사용 + `body_path`
  존재 시 `step(bytes, 64)` 자동 실행. import 가 .scn body 258개를
  `assets/scenes/bodies/<idx>.bin` 으로 export.
- Itanium C++ ABI mangle 파서 (`tools/h5_event_arg_sizes.py`) 로 105 Event_* 함수의
  arg_size 모두 추출 — `Eh`=1, `Ehh`=2, `Eaht`=4 등.

**[자산 환경 복원] 이 머신에서 처음부터 추출** — ✅ 완료 (2026-05-08)
- APK 압축 풀기 → `work/h5/extracted/` (assets, lib/armeabi/libHeroesLore5.so).
- VFS unpack 2189 entries (path D: → C: 수정).
- 자산 이름 99.7% 복원 (.so 의 sprintf format-string 기반).
- sprite 421 + palette 588 + sound 42 + scn 258 + 한글 코퍼스 18,837 변환.
- import_to_godot.py 로 Godot assets/ 완전 채움 — verify **0 errors / 0 warnings** 처음 달성.
- import 도구 확장: vfs/asset_names 매칭 시 .scn body 258개 자동 export.
- 신규 도구: `tools/h5_batch_sprite.py` (single-file argv converter 의 batch wrapper).

**[P3] Stats UI 합산 표시 + 장비 비교 패널** — ✅ 완료 (2026-05-08)
- Status panel 의 ATK/DEF 총합 라벨 추가 (`status_panel.gd::_apply`).
- 인벤 hover 비교: `_item_kind()` 로 무기/방어구/포션 분류 후 슬롯별 ATK/DEF diff
  표시 (방어구 = SLOT_ARMOR/HELMET/BOOTS 자동 매핑).

**[P4] Battle 결과 화면 + 메뉴 페이드** — ✅ 완료 (2026-05-08)
- 승리 popup: 중앙 패널에 EXP/Gold/획득 아이템 리스트 + 확인 버튼 (4초 자동 닫힘).
  drop_table 25% 확률 + enemy stats exp/gold 우선 사용.
- 씬 전환 fade: `SceneFader.change_scene()` (out 0.3s) +
  `SceneFader.fade_in()` (in 0.3s). Title/ClassSelect/Demo 진입 시 자동 fade-in.
- pre-existing 버그 수정: demo.gd 의 `_battle_ui.has_signal()` 호출이
  `_battle_ui` 인스턴스화 전이라 항상 nil — connect 위치를 인스턴스화 직후로 이동.

### 6.2.1 다음 우선순위 (남은 작업)

**[Round 26 시작점 — 다음 세션에서 진행]**
1. **RefineItem::ApplyItemRefine + ApplyOrbCombine 강화 stat 보너스 식별** (큰 임팩트)
   Round 17 에서 +0x165=refine_count / +0x166=sub_count / +0x167=locked 식별 완료.
   강화 시 어떤 stat (atk/def/etc) 이 어떻게 증가하는지, 강화 단계별 보너스
   공식 식별 필요. ApplyItemRefine (956B, @0xa292c) jumptable 더 분석 +
   ApplyOrbCombine (1208B) socket +0x168..+0x16d read/write 패턴 추적.
2. **val_15f upper 3 bit 정확 의미 추가 검증** (Round 24 가설 검증, 작은 임팩트)
   NewDropItem 의 11 args 추적 + DropTable / ShopInventory 호출 패턴 분석으로
   bit5/6/7 의 정확 의미 (현재 가설: obtainable / gem-accessory / common-tier)
   확정.
3. Save 데이터 구조 검증 (선택) — V[112..116] 라벨 (Round 11) 재검증.
4. P6 Android APK 실 빌드 검증 (USER TASK — 자동화 불가).

빠른 시작은 [SESSION_HANDOFF.md](SESSION_HANDOFF.md) "다음 세션 시작점" 1번 참조.

---

**[Round 54 — 2026-05-18 완료]** Orb socket UI 구현 — Round 17/26 의 ApplyOrbCombine + 53 orb
- ✅ **GameState orb_state 추가**:
  - `orb_state: Dictionary` (inv_idx → {sockets: [u8 ×5]})
  - 원본 EquipItemInfo +0x168 (orb_count V[188]) + +0x169..+0x16d (5 socket bytes) 매핑
  - encoding: 0 = 빈 슬롯, n>0 = slot_12 의 orb_idx (n-1)
  - 4 helper: `get_orb_sockets(inv_idx)` / `add_orb_to_socket(inv_idx, orb_idx)` (빈 슬롯 검색 + insert) / `remove_orb_from_socket(inv_idx, slot)` / `clear_orbs(inv_idx)`
- ✅ **equipment_bonus orb 합산**:
  - 각 채워진 socket 의 `GameData.orb_bonus_for(orb_idx)` 합산
  - Round 26 의 sub_orbs=9 → 2x rule 단순화: 5-socket 전부 채움 시 2x
  - weapon slot → attack, 그 외 → defense
- ✅ **consume_inventory + clear_orbs 연동** — inventory 제거 시 refine + orb 동기 정리
- ✅ **GameData 4 신규 helper**:
  - `orb_records()` — slot_12 의 53 orb 반환
  - `orb_name(orb_idx)` — orb_panel 의 socket 표시용
  - `orb_bonus_for(orb_idx)` — Round 26 정확한 stat 식 미식별 → price log10 등비 (price 100→+1, 1000→+2, ..., max +5)
  - `orb_group(orb_idx)` — Round 26 의 "3 그룹 × 13" 매핑: idx / 13
- ✅ **orb_panel.gd 신규** (~170 line):
  - 3-column layout: 좌측 equip list / 중앙 socket list + remove btn / 우측 보유 orb list
  - equip 카테고리 inventory item 만 (refine 단계 + populated socket 갯수 표시)
  - socket list = 5 entry, 빈 슬롯 "(빈 슬롯)" / 채워진 슬롯 "orb 이름 (+bonus)"
  - 보유 orb 더블클릭 = 빈 socket 자동 장착 + inventory 1개 소비
  - 채워진 socket 선택 + Remove 버튼 = orb 제거 → inventory 로 반환
- ✅ **orb_panel.tscn 신규** — 560×440 3-column layout
- ✅ **demo.gd 통합** — `_orb` 필드 + O 키 = orb 패널 toggle
- ✅ **tools/h5_test_orb.py 신규** — Python 검증:
  - 53 orb 0 name miss, bonus 분포 {0:1, 2:13, 4:39}, group 분포 {0:13, 1:13, 2:13, 3:13, 4:1}, price 분포 {0:1, 100:13, 5000:13, 8000:13, 10000:13}
  - socket encoding 5/5 fill OK, 6번째 -1
  - remove 3/3 케이스 (정상 제거 / 빈 슬롯 / out-of-range)
  - 5-socket 2x rule 검증 (4 socket=12 → 5 socket=32, raw 16)
  - 샘플: "빈소켓" (idx 0, sentinel) / "영제의 오브" / "흡혈의 오브" (low tier +2) / "하이퍼결의" / "하이퍼폭풍" (high tier +4)
- ✅ **verify_godot_project.py 0 errors / 0 warnings**
- 산출: orb_panel.gd (신규 ~170 line), orb_panel.tscn (신규), game_state.gd (orb_state +60 line), game_data.gd (+40 line, 4 helper), demo.gd (O-key bind), tools/h5_test_orb.py
- Godot 실 구현 45-50% → 48-53%. 출시 42-52% → 45-55%
- 다음 라운드: NPC blacksmith (smith_0/1/2.dat 288 recipes) / Quest 패널 강화 / scn 검증 / character.gd host 실 구현

**[Round 53 — 2026-05-18 완료]** 합성(Mix) UI 구현 — Round 25/28 의 ApplySpecialMix + 116 recipe
- ✅ **GameData 3 신규 helper**:
  - `item_name_at(cat, idx)` — (slot, idx) → name lookup (recipe 의 ingredient/result 가 cat/idx 형식)
  - `mix_recipes()` — items.json slot_15 의 116 entry 반환
  - `parse_recipe(rec)` — recipe dict 를 `{ingredients: [{name, count, cat, idx}], result: {name, cat, idx}, success_rate}` 로 해석
- ✅ **GameState 2 신규 helper**:
  - `inventory_count(name)` — 동일 이름 item 갯수 (mix 의 재료 보유량 검사)
  - `consume_inventory(name, n)` — n 개 소비 (장착된 슬롯 보호 + index shift + refine_state 동기 정리)
- ✅ **mix_panel.gd 신규** (~170 line):
  - 116 recipe 리스트 + 제작가능 (✓ prefix) / 불가능 (회색) 시각 구분
  - 필터 버튼 — "전체" / "제작가능만" 토글
  - 선택된 recipe 의 재료 (✓/✗ × 필요/보유) + 결과 + 성공률 preview
  - 재료 부족 시 mix_btn disabled
  - 실행: success_rate 로 100 분의 N roll, 성공 → 결과 inventory 추가, 실패 → 재료만 소비 (Round 28 동작)
- ✅ **mix_panel.tscn 신규** — 480×440 layout (RecipeList 좌측 + 우측 Result/Ingredients/Success/MixBtn + 하단 Log + FilterBtn 우상)
- ✅ **demo.gd 통합** — `_mix` 필드 + K 키 = mix 패널 toggle (M 은 map_id 충돌 회피)
- ✅ **tools/h5_test_mix.py 신규** — Python 검증:
  - 116 recipe 100% parse (ingredient name miss 0 / result name miss 0)
  - success_rate ∈ [0,100] 검증 (out-of-range 0)
  - ingredient 갯수 분포: 1개=11 / 2개=5 / 3개=100 (대부분 3-재료)
  - ingredient 카테고리: slot_13 (mix material) 316 / slot_11 (포션) 5
  - result 카테고리: 무기 4종 ×10=40, helmet 14, boots 10, accessory 16, accessory_2 10, shield 10, 포션 5, 재료 합성 10, 재료 정제 1
  - success_rate 평균 60.6%, ≥90% 26개 / ≤30% 22개, min 20 / max 100
  - 샘플 검증: "살코기×5 + 황혼버섯×5 → 황혼수프가루 (100%)" / "장갑판×47 + 상급마력 금속×19 + 부서진 수호부×3 → 그랜디쉬실드 (20%)"
- ✅ **verify_godot_project.py 0 errors / 0 warnings**
- 산출: mix_panel.gd (신규 ~170 line), mix_panel.tscn (신규), game_data.gd (+50 line, 3 helper), game_state.gd (+30 line, 2 helper), demo.gd (K-key bind), tools/h5_test_mix.py
- Godot 실 구현 42-47% → 45-50%. 출시 39-49% → 42-52%
- 다음 라운드: Quest 패널 강화 / Orb socket UI / scn 검증 / character.gd host 실 구현

**[Round 52 — 2026-05-18 완료]** 강화(Refine) UI 구현 — Round 17/26 의 ApplyItemRefine mechanism
- ✅ **GameState refine_state 추가**:
  - `refine_state: Dictionary` (inv_idx → {refine_count, sub_count, locked})
  - `get_refine(inv_idx)` / `set_refine(inv_idx, rc, sub, locked)` / `clear_refine(inv_idx)` helper
  - 원본 EquipItemInfo +0x165/+0x166/+0x167 매핑 (Round 17/26)
  - cap: refine_count 0..10, locked = +0x167 영구 잠금
- ✅ **equipment_bonus refine 보너스 합산**:
  - `refined_stat = base_stat + sub_count` (Round 26 Formula VM id=35/36)
  - items.json 의 stat_a (Round 26 의 의미있는 weapon ATK / armor DEF) 우선 사용
  - weapon slot 은 attack, 그 외 equip slot 은 defense 누적
- ✅ **refine_panel.gd 신규** (~150 line):
  - 5-case Round 17/26 mechanism Godot 구현
  - REFINE_PROB 10 row × 5 case (큰성공/성공/재료소비/lock/destroy) 각 row sum = 1000
  - 안전 단계 (+0..+2) destroy/lock 0, 위험 단계 (+7..+9) fail 70-85%
  - REFINE_COST 10 row 등비 (50 → 25000 G)
  - inventory 의 equip 카테고리 item 만 리스트 + 강화 단계 표시 (🔒 lock)
  - 다음 단계 prob preview + 골드 비용 + 보유 골드 검증
  - destroy 시 inventory 제거 + equipment[slot] -1 처리 + index shift
- ✅ **refine_panel.tscn 신규** — 380×440 layout (ItemList / Current / Preview / GoldCost / RefineBtn / ResultLog / CloseBtn)
- ✅ **demo.gd 통합**:
  - `_refine` 필드 + 패널 instantiate
  - R 키 = refine 패널 toggle
- ✅ **tools/h5_test_refine.py 신규** — Python 검증:
  - prob row sum = 1000 (10/10 ✓)
  - 안전 단계 destroy/lock 0 ✓
  - 성공률 단조 감소 (900 → 150) + destroy% 단조 증가 (0 → 200) ✓
  - 10000회 시뮬레이션: +10 도달 246 (2.5%), locked 6507 (65.1%), destroyed 3247 (32.5%), timeout 0
  - 평균 시도 횟수 10.5
  - refined_stat = base + sub 산술 검증 4/4 ✓
- ✅ **verify_godot_project.py 0 errors / 0 warnings**
- 산출: refine_panel.gd (신규 ~150 line), refine_panel.tscn (신규), game_state.gd (refine_state +30 line), demo.gd (refine R-key bind), tools/h5_test_refine.py
- Godot 실 구현 39-44% → 42-47%. 출시 36-46% → 39-49%
- 다음 라운드: 합성(Mix) UI / Quest 패널 / scn 검증 / character.gd host 실 구현

**[Round 51 — 2026-05-18 완료]** 인벤토리 패널 items.json 정확 통합 — substring 매칭 → kind 기반
- ✅ **game_data.gd 새 helper 5종**:
  - `_build_item_index()` — 19 slot × 1360 records → unique-name dict (1333 entries, 27 중복 시 slot 낮은 쪽 우선)
  - `item_lookup(name)` — name → {slot, idx, kind, category, level_limit, class_mask, class_label, tier_flags, tier_label, refine_count, sub_count, stat_a/b, price, sockets, subtype} 카테고리별 fields. equip = R13-26, potion = R23 (effect_type/value/duration), skill_book = R21 (class_id/skill_index/skill_level/required_level)
  - `class_mask_allows(class_mask, class_id)` — Round 16 의 5-bit 비트마스크 (W=1/R=2/G=4/K=8/S=16) 검증, 0 = 제약 없음
  - `equip_slot_for_kind(kind)` — kind → GameState.SLOT_* (weapon→SLOT_WEAPON, helmet→SLOT_HELMET, accessory→SLOT_ACC1, accessory_2/shield/spirit→SLOT_ACC2)
  - `item_matches_filter(name, filter_key)` — filter 분류 (weapon/armor/potion/misc) items.json kind 기반
- ✅ **status_panel.gd 정확 분류**:
  - `_matches_filter` → GameData.item_matches_filter (한국어 substring 제거)
  - `_item_kind(name)` → items.json kind (Round 50 이전 의 "검/소드/액스" substring 매칭 정정)
  - `_slot_for_kind(kind, name)` → GameData.equip_slot_for_kind (정확한 slot)
  - `_find_item_price(name)` → 19 slot 순회 → 단일 lookup (성능 + 정확도)
- ✅ **풍부 tooltip** (Round 51 신규 정보):
  - equip: stat_a~stat_b (무기 atk range) / 필요 Lv / 클래스 라벨 / 등급 (legendary/rare/gem/common) / 강화 +N (sub M) / 장착 비교 diff
  - potion: effect_type 라벨 (HP/SP/buff/마석) + value (%) + 지속 턴
  - skill_book: 클래스 이름 + 스킬 번호 + Lv + 필요 Lv
  - 모두: 가격
- ✅ **장비 검증** (`_use_item`):
  - class_mask 검사 → 실패 시 "클래스 제한 (X 만)" 메시지
  - level_limit 검사 → 실패 시 "레벨 부족 (필요 Lv N)" 메시지
  - 통과 시 자동 slot 매핑 + equip
- ✅ **tools/h5_test_items_lookup.py 신규** — Python 검증 도구:
  - 19 slot × 1360 records sweep
  - unique-name index (1333 entries + 27 중복 검증)
  - equip class_mask out-of-range 0 검증
  - tier_flags 분포: 170 (legendary) + 248 (rare) + 9 (gem) + 362 (common) — Round 24 와 정확 일치
  - filter coverage: weapon 344 / armor 445 / potion 16 / misc 555 (sum = 1360, 0 unknown)
  - class_mask_allows 5/5 통과
  - 샘플 lookup: 롱소드 / 나이트롱소드 / 버클러 / 포션 모두 정확
- ✅ **verify_godot_project.py 0 errors / 0 warnings**
- 산출: game_data.gd (+90 line, 5 helper), status_panel.gd (+90 line, _format_item_tooltip + class/level 검증), tools/h5_test_items_lookup.py
- Godot 실 구현 36-41% → 39-44%. 출시 33-43% → 36-46%
- 다음 라운드: 강화(Refine) UI / 합성(Mix) UI / scn 검증 / character.gd host 실 구현

**[Round 50 — 2026-05-18 완료]** Monster AI Action sub-state 1-7/9/12 정밀 구현 + host CHAR interface
- ✅ **monster_ai.gd `_ai_action` 13 sub-state 모두 dispatch** (Round 48 의 state 0/8 stub → 모두 채움):
  - state 0 = `_state_chase_timer` — Fast_Distance vs sight + ImmadiatelyCheck(8)
  - state 1 = `_state_turn_direction` — mode 0/2 lookup / 1 lookup2 / 3 flip180 / default face hero
  - state 2 = `_state_countdown` — first_set_flag decrement + motion==1 시 state 0 재진입
  - state 3 = `_state_skill_use_targeting` — Monster+0x2c9 skill, dir mode 0-4, IRect 충돌 검사
  - state 4/6 = `_state_set_attack_motion(s, skill_id)` — Monster+0x2cc/+0x305 source, motion+dir lookup → cast
  - state 5/7/8 = `_state_skill_cast(s, skill_id)` — Monster+0x304/+0x308/+0x30a source, HeroTurnDirection → cast
  - state 9 = `_state_skill_end` — Monster+0x2c3 = 1, skill_end()
  - state 12 = `_state_get_motion_exit` — GetMotion() 호출만
- ✅ **공통 helper 추가**:
  - `_can_cast_skill(s, skill_id)` — skill_id > 0 + skill_disable==0 + GetMotion==0 + is_attack_able + is_able_skill 5-gate
  - `_do_cast(s, skill_id)` — host.ai_cast_skill + set_cool_time + opcode reset
  - `_immadiately_check(s, new_state)` — 새 sub-state 진입 + timer reset
  - `_host_call_int/_host_call_bool` — host method optional dispatch wrapper
- ✅ **battle_system.gd 에 host CHAR interface 13 method** (turn-based 추상화에 맞춘 stub):
  - `is_die / get_motion / is_attack_able / is_able_skill / get_dir / set_dir / hero_turn_direction`
  - `fast_distance_to_hero / set_attack_motion / ai_cast_skill / set_cool_time / skill_end`
  - `ai_check_irect_hit / ai_check_visibility / ai_all_dead / ai_tutorial_flag`
  - `_ai_pending_skill_id` 필드 + `_ai_pick_skill()` 가 pending → fallback 우선순위로 반환
- ✅ **operand 부족 시 graceful stop** — `_on_action` 의 advance 가 stream 끝을 넘으면 return 1 (action 종료).
  decoder Round 45 의 "trailing bytes 부족 시 break" 동작과 매칭.
- ✅ **tools/h5_test_monster_ai.py 신규** — monster_ai.gd 의 GDScript 로직을 Python 으로 1:1 재구현:
  - 48 AI defs 의 trigger + action stream 전체 walk (overrun 검출)
  - `simulate_ai()` 가 매 step 후 `ai_action(s)` 호출하여 cast event 카운트
  - Ai_Action 13 sub-state 모두 dispatch + cast 발생 검증
  - **48/48 AI round-trip 통과** (62 trigger steps + 674 action steps + 19 cast 발생)
- ✅ **verify_godot_project.py 0 errors / 0 warnings**
- 산출: monster_ai.gd (+170 line, _ai_action 확장 + 12 helper), battle_system.gd (+60 line, host interface), tools/h5_test_monster_ai.py
- Godot 실 구현 33-38% → 36-41%. 출시 30-40% → 33-43%
- 다음 라운드: Godot UI (인벤토리 패널) 또는 scn opcode 실 game scene 검증 또는 Save device import

**[Round 49 — 2026-05-17 완료]** Save/Load binary 직렬화 GDScript 구현 + Python round-trip test
- ✅ **save_manager.gd 확장** (Round 41-43 의 SAVE_FORMAT.md layout 을 GDScript 로 구현):
  - `serialize_hero_save(state)` → PackedByteArray (524B = H_SAV_SIZE)
  - `deserialize_hero_save(data)` → state dict
  - `serialize_slot_save(state)` → PackedByteArray (header 0x17B)
  - `deserialize_slot_save(data)` → state dict
  - byte helpers (`_put_u16_le/u32_le/u64_le`, `_get_u16_le/u32_le/u64_le`) — LE encoding
- ✅ **H_*.sav (HERO 524B) layout 매핑** (Round 42 21/21 cross-check 결과 일치):
  - +0x00 u32 field_f0 / +0x04 class_id / +0x05 hero_22d / +0x06 gold u32
  - +0x0a..+0x19 = **8 × u16 stat block** (HP/MP/STR/DEX/CON/INT + 2)
  - +0x1a..+0x44 = **43B skill_buff** (skill list / buff state)
  - +0x45..+0x4b = **7 × u8 equip slot** (EquipItem cat 0-6)
  - +0x4c u32 / +0x50..+0x5f 16B sub-block / +0x60 record count
  - +0x61..+(0x60+0x29*10) = **10 × 41B skill slot records**
  - +0x1fc u64 timestamp_create / +0x204 u64 timestamp_update
- ✅ **SL_*.sav (SlotInfo header 23B) layout 매핑** (Round 43 packing 규칙 반영):
  - +0x00 = **`level * 10 + class_id` packed byte** (Load 측 umull fast-div-by-10 분리)
  - +0x01 hero_22d / +0x02 pos_x s32 / +0x06 pos_y s32 / +0x0a playtime u64 / +0x12 scene_idx u32 / +0x16 state_flag
- ✅ **tools/h5_test_save_layout.py 신규** — Python round-trip 검증 도구:
  - GDScript serialize 의 Python equivalent 구현 (동일 byte 생성 검증)
  - 4 samples (워리어 lv1 새 캐릭터 / 나이트 lv10 / 워리어 lv1 슬롯 / 소서러 lv25 max)
  - 8 critical offsets (field_f0/class_id/hero_22d/gold/stat[0]/stat[7]/field_4c/SL packed)
  - LE byte order 자동 검증
  - **모든 테스트 통과** (4 samples round-trip + 8 critical offsets)
- ✅ **verify_godot_project.py 0 errors / 0 warnings**
- 산출: save_manager.gd (binary writer/reader 추가, 약 +150 line), tools/h5_test_save_layout.py
- Godot 실 구현 30-35% → 33-38%. 출시 27-37% → 30-40%
- 다음 라운드: AI Action sub-state 정밀 구현 또는 Godot UI (인벤토리 패널)

**[Round 48 — 2026-05-17 완료]** Monster AI Godot 통합 시작 — autoload + VM + battle hook
- ✅ **apps/hero5-godot/scripts/core/monster_ai.gd 신규** — 약 270 line autoload:
  - `monster_ai.json` (Round 45 산출) loader (`_ready` 가 by_id 파싱)
  - `MonsterAIState` inner class — 원본 Monster struct +0x288..+0x315 영역 매핑
    (action_idx / opcode / operand / action_cooldown / state / action_type / sub_action /
     skill_id / skill_target / skill_range / skill_param / 5 skill source fields /
     11 one-shot flag fields)
  - `create_runtime(host, ai_type_id)` — runtime state 생성
  - `process(s)` — 매 frame entry (cooldown decrement + Ai_Action dispatch)
  - `_ai_action(s)` — Round 47 의 13 sub-state machine (state 0 CHASE_TIMER + state 8 SKILL_USE_30A 구현, 나머지 host method 위임)
  - `step_action_list(s)` — Round 44 의 Ai_doActionList (action stream 1 step)
  - `_on_action(s, op, stream)` — 13 opcode interpreter (operand size table 사용)
  - `step_trigger_list(s)` — Round 46 의 ActionOfTrigger (trigger stream walker)
  - `_is_trigger_equal(s, code, operand)` — 13 trigger handler (one-shot flag check/consume + host method 위임 for VISIBILITY/TUTORIAL)
- ✅ **autoload 등록**: `project.godot` 의 [autoload] 섹션에 `MonsterAI="*res://scripts/core/monster_ai.gd"` 추가 (7th autoload)
- ✅ **battle_system.gd hook 추가**:
  - `_ai_runtime` 필드 (MonsterAI.MonsterAIState | null)
  - `start_battle` 끝에 `MonsterAI.create_runtime(self, monster_id)` 호출
  - `_ai_pick_skill()` 메서드 — 트리거 검사 + action stream 진행 후 skill_src_30a 또는 skill_id 반환 (없으면 -1)
- ✅ **verify_godot_project.py: 0 errors / 0 warnings** — 모든 reference 해결
- ✅ **monster_ai.json 234KB** = Godot assets/gamedata/ 에 위치, GDScript loader 가 res:// 경로로 access
- 산출: monster_ai.gd, project.godot (autoload 추가), battle_system.gd (hook)
- **Monster AI 분석 → 구현 트랙 전환** — Godot 실 구현 25-30% → 30-35%
- 다음 라운드: AI VM 의 Ai_Action state 1-7/9/12 정밀 구현 + host method (CHAR interface) 채우기 + Godot Editor 에서 실 컴파일 검증

**[Round 47 — 2026-05-17 완료]** Monster AI Ai_Action 13 sub-state 정밀 분석 (Monster AI 분석 완전 종료)
- ✅ **Ai_Action 13 sub-state 의미 완전 매핑** (Monster+0x297 jumptable):
  - state 0: **CHASE_TIMER** — Monster+0x2c8 decrement, Fast_Distance(hero) vs +0x2c6 시야 비교 → ImmadiatelyCheck(8) trigger
  - state 1: **TURN_DIR** — Monster+0x2c5 (mode 0-3+default) 별 dir 설정 (lookup / flip 180° / face hero)
  - state 2: **COUNTDOWN** — Monster+0x2c7 timer, 0 도달 + motion==1 시 state 0 재진입
  - state 3: **SKILL_USE_WITH_TARGETING** — Monster+0x2c9 skill, Monster+0x2ca (mode 0-4) dir 제어, IRect 충돌 검사 후 cast
  - state 4: **SET_ATTACK_MOTION** — Monster+0x2cc → skill_id, Monster+0x2d8+offset 에서 motion+dir 데이터 가져와 SetAttackMotion
  - state 5: **SKILL_CAST_DIR304** — Monster+0x304 → +0x2c9, GetDir → +0x2ca, IsAbleSkill → SkillUsed
  - state 6: **READY_ATTACK_305** — Monster+0x305 → state 4 fallthrough
  - state 7: **READY_ATTACK_308** — Monster+0x308 → +0x2c9, IsAbleSkill 후 cast
  - state 8: **SKILL_USE_30A** — Monster+0x30a (opcode 9 next_skill) → +0x2c9, HeroTurnDirection → cast
  - state 9: **SKILL_END** — Monster+0x2c3 = 1, SkillEnd() 호출 (skill 종료 정리)
  - state 10, 11: no-op (default fall-through exit)
  - state 12: **GET_MOTION_EXIT** — GetMotion 호출 후 exit
- ✅ **공통 패턴 식별**:
  - 모든 SKILL state 가 GetMotion==0 + IsAttackAble==1 + Monster+0x315==0 (skill_disable) 게이트
  - cast 후 Monster+0x297 = -1 로 sub-state reset (다음 frame 새 dispatch)
- ✅ **5 opcode → 6 state path skill dispatch matrix**:
  ```
  opcode 4 (SKILL_SET, 3B) → +0x2c9..+0x2cb → state 3
  opcode 5 (SKILL_PARAM, 4B) → +0x2cc..+0x2cf → state 4
  opcode 6 (SET_303, 2B) → +0x303/+0x304 → state 5
  opcode 7 (SET_305, 3B) → +0x305..+0x307 → state 6
  opcode 8 (SET_308, 2B) → +0x308/+0x309 → state 7
  opcode 9 (NEXT_SKILL, 2B) → +0x30a/+0x30b → state 8
  ```
- ✅ **MONSTER_AI.md 갱신** — 13 sub-state 표 + 공통 패턴 + skill dispatch matrix
- **Monster AI 분석 완전 종료** — 데이터원 + VM (action 13 op + trigger 13 op) + 13 sub-state 모두 매핑. Godot 구현 가능 상태.

**[Round 46 — 2026-05-17 완료]** Monster AI trigger stream layout 완전 식별 — ActionOfTrigger + 13 trigger operand 매핑 + decoder 확장
- ✅ **IsTriggerEqual 13 handler 정밀 분석**: 각 handler 의 trigger_data_block byte 소비 패턴 추출
  - trigger 1 (VISIBILITY_RECT): 1 byte operand = IRect index (×40 = base offset into Monster+0x2d8)
  - trigger 6 (TUTORIAL_FLAG): 1 byte operand vs gv+0x130/0x131/0x132 (3 tutorial flag)
  - 나머지 11 trigger: 0 operand (one-shot flag check/consume)
- ✅ **ActionOfTrigger (0xbd7a0, 140B) driver 분석**: trigger stream 의 entry walk
  - 매 entry layout: `[trigger_code u8][operand 0-1B][action_id u8]`
  - 트리거 fire → action_id → Monster+0x294 → ImmadiatelyInit
  - 트리거 5 (ALWAYS_GOTO) 는 IsTriggerEqual 안 부르고 즉시 action_id 처리 (special path)
- ✅ **decode_h5_monsterai.py 확장** — trigger stream disasm 지원:
  - TRIGGER_OPERAND table (13개 trigger × operand byte 수)
  - TRIGGER_NAME table (의미 라벨)
  - `disasm_tokens(kind='trigger')` 모드 추가 — entry stride = 1 + operand + 1 자동 처리
- ✅ **48 AI 파일 재파싱 — 543 trigger entries 100% perfect parse** (0 unknown, 0 incomplete)
- ✅ **Trigger 분포 통계**:
  - VISIBILITY_RECT (1): 196 (36%) — hero 시야 검사
  - ALWAYS_GOTO (5): 195 (36%) — default fallback
  - CONSUME_2B6 (12): 76 (14%)
  - SET_29F (0): 35 (6%)
  - CONSUME_2B7 (11): 33 (6%)
  - CONSUME_2BD/BF: 8
- ✅ **AI 패턴 검증**: VISIBILITY_RECT + ALWAYS_GOTO = 72% — 대부분 "기본 idle 가다가 hero 시야 진입 시 combat 전환" 설계
- ✅ **MONSTER_AI.md 갱신** — Round 46 trigger 13 handler 표 + ActionOfTrigger pseudo-code + 통계
- 산출: 갱신된 decode_h5_monsterai.py / monster_ai.json / MONSTER_AI.md
- **데이터 RE 100% 종료** — 모든 데이터 파일 식별 + decoder + struct + opcode/trigger 매핑 완료

**[Round 45 — 2026-05-17 완료]** Monster AI 데이터원 식별 — `/c/mon/<id>_ai` 48 파일 + EnemyAI struct + decoder
- ✅ **AI_def 데이터원 추적**: Map::MonsterAdd (0xb5814) → 메모리 할당 (0x78 = 120 byte) → EnemyAI::EnemyAI(ai_type_id) → str → Monster+0x288
  - ai_type_id = Monster+0x22e (Round 34 setEnemyData 가 enemy_*.dat 에서 set)
- ✅ **EnemyAI::LoadData (0x6a62c, 700B) 정밀 disasm**: filename format = `/c/mon/%d_ai` 추출
- ✅ **VFS 에서 48 AI 파일 발견** (`c/mon/0_ai` ~ `c/mon/63_ai`, gap 있음, 크기 31~305B avg 110.5B)
  - DES 미적용 (3/48 만 8의 배수)
- ✅ **EnemyAI 파일 layout 정확 파악**:
  ```
  u8 n_t (trigger_count)
  n_t × u8 trigger code list (IsTriggerEqual ids)
  n_t × u8 handler size list
  sum(handlers) × u8 trigger_data_block
  u16 n_a (action_count, low byte 만 사용)
  n_a × u8 action_lookup_1
  n_a × u8 action_lookup_2
  n_a × u16 action_lookup_3
  u16 n_ts (trigger_stream_size, low byte)
  n_ts × u8 trigger byte stream (Tokenizer #1)
  u8 n_l (action_list_count)
  n_l × u8 action_list_lookup_1
  n_l × u8 action_list_offset_table (AI_setActionList 사용)
  n_l × u8 action_list_lookup_3
  u16 n_as (action_stream_size, s16)
  n_as × u8 action byte stream (Tokenizer #2, 13 opcode VM)
  ```
- ✅ **EnemyAI struct (120B) layout 매핑**: +0x24 (n_t), +0x25..+0x2f..+0x39 (trigger 3 arrays), +0x44 (n_a), +0x48..+0x54 (action 3 lookups + trigger data), +0x58/+0x5c (trigger stream Tokenizer #1 source), +0x60 (n_l), +0x64..+0x6c (action_list 3 lookups), +0x70/+0x74 (action stream Tokenizer #2 source)
- ✅ **decode_h5_monsterai.py 신규** — 48 AI 파일 일괄 파싱:
  - 48/48 perfect parse (consumed == file_size 모두 일치, 0 errors)
  - action stream 은 Round 44 의 13 opcode 로 disasm 시도 (operand 길이 미정 opcode 는 1 byte 만 소비)
  - trigger stream 은 raw hex (trigger handler 정밀 매핑 다음 라운드)
- ✅ **monster_ai.json 발행** (apps/hero5-godot/assets/gamedata/, 48 AI defs)
- ✅ **524 action opcode 통계**:
  - WALK (0): 176 / CHANCE_WALK (1): 110 / SET_SUB (2): 72 / SET_STATE_FIRST (3): 59
  - SET_303 (6): 34 / SET_305 (7): 18 / SKILL_PARAM (5): 16 / SKILL_SET (4): 12 / SET_308 (8): 8
  - WALK + CHANCE_WALK = 286/524 (55%) — monster 대부분이 walking 중심 AI
- 산출: enemyai_loaddata_disasm.txt, tools/converter/decode_h5_monsterai.py, monster_ai.json, MONSTER_AI.md 갱신

**[Round 44 — 2026-05-17 완료]** Monster AI 시스템 분석 — token-based bytecode VM 식별 + 13 opcode + 13 trigger 완전 매핑
- ✅ **AI 함수 12개 식별**:
  - `Ai_Process` (88B, entry) / `Ai_Action` (2136B, main dispatch) / `Ai_onAction` (704B, opcode interpreter)
  - `Ai_setActionList` (100B) / `Ai_doActionList` (184B) — action list 관리
  - `Ai_Initialize` (148B) / `Ai_SetPtr` (92B) / `Ai_FreePtr` (108B) — life cycle
  - `Ai_stateCheck` (576B) / `ActionCheck` (120B) — state validation
  - `IsTriggerEqual` (1320B) / `ActionOfTrigger` (140B) — trigger 평가
- ✅ **핵심 발견 — token-based bytecode VM**:
  - Monster AI 가 **SCN opcode 시스템과 동일 패턴** 사용
  - AI 정의가 byte stream 으로 외부 데이터에 저장 → 디자이너가 monster 별 행동 작성 가능
  - Tokenizer (Monster+0x290) 가 byte stream cursor
  - AI_def_ptr (Monster+0x288) 의 +0x68=offset_table / +0x6c=action_list_table
- ✅ **Ai_Process dispatch (entry, frame 당 1회)**:
  ```
  if IsStunFlag: return
  Ai_stateCheck(Monster+0x2c3)
  ActionCheck()
  Monster+0x2b4 cooldown 감소 (default 9 frames)
  → Ai_Action (tail call)
  ```
- ✅ **Ai_Action sub-state machine 13 entries** (Monster+0x297 jumptable index):
  - state 8 = SKILL USE (IsAttackAble + IsAbleSkill + HeroTurnDirection + SkillUsed + SetCoolTime)
  - state 0 = timer decrement (Monster+0x2c8 → 0 시 hero 방향 추적)
  - 나머지 1-7, 9-12 = move/chase/cast 처리 (정밀 분석 다음 라운드)
- ✅ **Ai_doActionList token interpreter**:
  - Monster+0x294 (current_action_idx) 가 0xff 또는 Monster+0x2d0 == 0 면 return
  - Token_GetByte → Monster+0x297 → Ai_onAction(opcode)
  - Ai_onAction 반환 0 = 계속, 1 = action 완료 (Monster+0x2d0=0, +0x2b1++)
- ✅ **Ai_onAction VM opcodes 13개 매핑** (Monster+0x2a8..+0x2ab 가 operand buffer):
  - op 0: 2B → +0x2c4 action_type / +0x2c6 + SetMonMotion(motion=1) WALK
  - op 1: 2B → 동일 set + Rand(0,99) < +0x2a9 시 chance walk (motion=5)
  - op 2: 1B → +0x2c5 sub-action id
  - op 3: 1B → +0x2c7 (first-time-only set)
  - **op 4: 3B → +0x2c9/+0x2ca/+0x2cb = SKILL slot** (skill_id, target, range)
  - op 5: 4B → +0x2cc/+0x2cd/+0x2cf/+0x2ce secondary skill params
  - op 6: 2B → +0x303/+0x304
  - op 7: 3B → +0x305/+0x306/+0x307
  - op 8: 2B → +0x308/+0x309
  - **op 9: 2B → +0x30a/+0x30b = next_skill_id** (Ai_Action state 8 가 사용)
  - op 10: 1B (skip)
  - op 11: variable (Token_GetByte → N → Token_GetData(N))
  - op 12: 1B → +0x2c2 animation override
- ✅ **IsTriggerEqual 13 trigger 핸들러 매핑** (조건 평가 → action list 전환):
  - trigger 1 = +0x29f 한 번만 발화
  - **trigger 2 = IRect 위치 검사** (큰 핸들러 — visibility/range check, hero 위치 vs monster 시야)
  - trigger 11 = +0x2be one-shot consume
  - trigger 13 = +0x2b6 one-shot consume
  - 나머지 3-12 = 정밀 분석 다음 라운드
- ✅ **Monster struct AI 영역 매핑** (+0x288..+0x315 전체):
  - +0x288 AI_def_ptr / +0x290 Tokenizer / +0x294 action_idx / +0x297 opcode
  - +0x2a8..+0x2ab operand buffer / +0x2c2..+0x315 = state machine fields
- ✅ **`docs/h5/MONSTER_AI.md` 신규** — 전체 AI 아키텍처 + 13 opcode + 13 trigger + Monster struct map
- 산출: 3 × disasm txt, MONSTER_AI.md
- **다음 라운드**: Ai_SetPtr 추적 → AI_def 데이터원 VFS 위치 식별 + 13 state machine handler 세부 분석

**[Round 43 — 2026-05-17 완료]** Save source struct field 의미 라벨링 완료 (데이터 RE 종료)
- ✅ **LoadHeroData (808B) 정밀 disasm** — file → HERO struct offset 매핑 완전 추출:
  - file+0..3 u32 → HERO+0xf0
  - file+4 u8 → HERO+0x22c (**class_id**, Round 13 확정)
  - file+5 u8 → HERO+0x22d (보조 class field)
  - file+6..9 u32 → HERO+0x230 (EXP/gold)
  - file+0xa..0x19 = 8 × u16 → HERO+0x234, 0x23e, 0x240, 0x242, 0x244, 0x246, 0x248, 0x24a
    - **10 byte 점프 (0x234→0x23e)**: in-memory 만 있는 derived stat 5개 (저장 안 됨) 사이 위치 확정
  - file+0x1a..0x44 (43 bytes) → HERO+0x24c..+0x276 (skill list / buff state)
  - file+0x45 u8 → HERO+0x277 (**equip slot 0** = packed level source — SL_*.sav file[0] 의 `level*10+class` 의 level 부분)
  - file+0x46..0x4b (6 bytes) → HERO+0x1790..+0x1795 (**equip slot 1-6**, EquipItem cat 1-6 정확 일치)
  - file+0x4c..0x4f u32 → HERO+0x1798
  - file+0x50..0x5f (16 bytes) → HERO+0x17a6..+0x17b5 (skill cooldown/buff 추정)
  - file+0x60 u8 → HERO+0x1b61 (record count for next loop)
  - file+0x61..(0x60+0x29*10) = 10 × 41B records → HERO+0x1b62..+(0x1b62+0x19a)
  - file+0x1fc..0x203 u64 → HERO+0x310 + HERO+0x318 (**timestamp #1**, 양쪽 store)
  - file+0x204..0x20b u64 → HERO+0x328 + HERO+0x330 (**timestamp #2**, 양쪽 store)
- ✅ **LoadSlotData (968B) 정밀 disasm** — file → SlotInfo struct 매핑:
  - **file[0] = level*10 + class_id 인코딩 발견** — Load 가 `umull` (fast division by 10) + `rsb` 로 `% 10` / `/ 10` 분리:
    - SlotInfo[0] = file[0] % 10 = class_id (0-4)
    - SlotInfo[1] = file[0] / 10 = level
    - max level ≈ 25 추정 (1 byte container 한도, 5 클래스 × 50 level = 250 < 256 가능하지만 보수적으로 25)
  - file+0x2..0x5 → SlotInfo+4 (OBJECT::GetX, **map X position**)
  - file+0x6..0x9 → SlotInfo+8 (OBJECT::GetY, **map Y position**)
  - file+0xa..0x11 u64 → SlotInfo+0x10 (**playtime** ms/s)
  - file+0x12..0x15 u32 → SlotInfo+0x18 (**scene_idx**, 현재 맵 ID)
  - file+0x16 → SlotInfo+0x1c (game state flag)
  - file+0x17..0x116 (256B) → SlotInfo+0x1d (memcpy block 0, source = gv+0x288)
  - file+0x117..0x216 (256B) → SlotInfo+0x11d (memcpy block 1, source = gv+0x388)
  - file+0x217..0x316 (256B) → SlotInfo+0x21d (memcpy block 2, source = gv+0x488)
- ✅ **gv+0x1474 sub-struct ↔ save 매핑 검증**:
  - 3 × 256B blocks (gv+0x288/0x388/0x488) 가 모두 Round 5/6 의 V[58..167+249] 영역
  - V[58..167] (stat/buff cache) 데이터를 통째로 file 에 직렬화 + Load 시 그대로 복원
  - save/load round-trip 안전 (no derived recompute 필요)
- ✅ **SlotInfo getter 매핑 검증**:
  - GetHeroClass() → SlotInfo+0 ✓
  - GetHeroLevel() → SlotInfo+1 ✓
  - GetHeroX/Y() → SlotInfo+4/8 ✓
  - GetPlayTime() → SlotInfo+0x10 ✓
  - GetSceneIdx() → SlotInfo+0x18 ✓
  - 모든 getter 가 LoadSlotData 가 채운 field 정확히 사용
- ✅ **SAVE_FORMAT.md 갱신**: 모든 file offset 에 size + HERO struct offset + 의미 라벨 부여.
  Round 43 핵심 발견 두 가지 (packing 규칙, gv sub-struct 매핑) 별도 항목으로 정리.
- 산출: `work/h5/analysis/loadherodata_disasm.txt`, `loadslotdata_disasm.txt`, 갱신된 SAVE_FORMAT.md
- **데이터 RE 종료** — items/monster/drop/smith/mission/quest/save 모두 decoder/문서화 완료.

**[Round 42 — 2026-05-17 완료]** Save load 함수 cross-check 로 H_*.sav / SL_*.sav layout 확정 (21+24 offset 일치, 0 mismatch)
- ✅ **h5_extract_save_writes.py 확장** (R41 작성 → R42 강화):
  - load 측 `ByteToInt{16,32,64}` 호출 인수 추출 추가
  - `ldr/ldrb/ldrh/ldrsb/ldrsh` direct memory read 추출 추가
- ✅ **3 load 함수 read event 추출**:
  - `HERO::LoadHeroData` (808B) → 33 events
  - `SlotInfo::LoadSlotData` (968B) → 73 events
  - `Mission::LoadData` (604B) → 33 events
- ✅ **tools/h5_save_crosscheck.py 신규** — save / load write↔read 매칭으로 layout 확정:
  - offset 별 save_size vs load_size 비교
  - OK / MISS / save-only / load-only 분류
- ✅ **H_%d.sav layout 확정** — **21/21 offset 정밀 일치 (0 mismatch)**:
  - +0x0..3 u32 (HERO+0xf0)
  - +0x4..5 = 2×u8 (HERO+0x22c class_id, HERO+0x22d) — Round 13 EquipItemInfo +0x14 와 일관
  - +0x6..9 u32 (EXP/gold)
  - +0xa..0x19 = **8×u16 stat block** confirmed
  - +0x45..0x4b = **7×u8 equip slot** (EquipItem cat 0-6 Round 14 와 정확 일치)
  - +0x4c..0x4f u32, +0x60 u8
  - **+0x1fc..0x203 u64 timestamp #1, +0x204..0x20b u64 timestamp #2** (load 측에서 추가 발견)
  - 총 사용 영역 ≈ 0x20c bytes (524 B)
- ✅ **SL_%d.sav layout 확정** — 24 offset 정밀 일치 (0 mismatch):
  - Header (+0x00..+0x15) 완전 확정: class+level encode / GetX u32 / GetY u32 / playtime u64 / scene_idx u32
  - +0x321..+0x324 (4B item slot marker), +0x425..+0x426 (2B flag pair)
  - **+0x433..+0x438 = 6 bytes sub-block 1** (강화/orb socket 후보)
  - **+0x45d..+0x462 = 6 bytes sub-block 2** (sub-block 1 의 보조)
  - +0x487..+0x489 trailer markers, +0x494..+0x496 in-memory only
  - 13 save-only writes 는 r4=SlotInfo struct 의 in-memory cached fields (file 영역 아님)
- ✅ **Mission save 부분 확인**: load +0x4 에서 ldrsh 2회 = u16 record_count 또는 size pair.
  나머지는 105 mission iter 의 변수 offset (다음 라운드 disasm 분석 필요).
- ✅ **SAVE_FORMAT.md 갱신**: 확정된 layout 표 + cross-check 도구 사용법 + 다음 라운드 작업.
- 산출: tools/h5_save_crosscheck.py, 3 × *_writes.tsv (load), 갱신된 SAVE_FORMAT.md
- **데이터 RE 사실상 마무리** — 남은 작업: source struct field 의미 라벨링 (의미 라벨만 안 붙은 상태)

**[Round 41 — 2026-05-17 완료]** Save 파일 시스템 RE 시작 — 8 파일 종류 + dispatch + write event 자동 추출 (DES 미적용 확정)
- ✅ **8 save 파일 종류 식별** (.rodata string scan):
  - `LOCAL.sav` / `EX.sav` / `ET.sav` / `OP.sav` (게임 옵션/메타)
  - `M.sav` (Mission 진척)
  - `H_%d.sav` / `B_%d.sav` / `SL_%d.sav` (슬롯별: hero/bag/slot info)
  - `DEBUG.sav` (debug only)
- ✅ **HERO::SaveAll (0x8f924, 92B) dispatch 식별**:
  ```
  SaveAll(slot_idx) → SlotInfo::SaveSlotData → SaveHeroData → SaveBagData → Mission::SaveData
  ```
  LOCAL/EX/ET/OP 는 별도 흐름 (게임 옵션/슬롯 무관).
- ✅ **DES 는 save 에 적용 안 됨 확정** (큰 발견):
  - MX_desEncrypt/MX_desEncryptPKCS7/MX_desDecrypt 의 caller 를 .text 전체에서 capstone+symbol map 으로 스캔 → **0건**
  - DES key `0EP@KO91` + S1[3][10]=2 변종은 calc_*.dat (Formula VM) 등 다른 protected resource 전용
  - Save 파일 = **plain bytes** (SD container 안에 저장, _midas_funcSdMakeName 도 filename 15-char truncation 만)
- ✅ **자동 write event 추출 도구 작성** (`tools/h5_extract_save_writes.py`):
  - ARM disasm + register propagation 으로 `Int{8,16,32,64}ToByte` / `memcpy` / `strb/h/(w)` 호출 인수 추출
  - 출력: file_offset, write_size, src_register, instr_addr TSV
- ✅ **3 메인 save 함수 write event 추출**:
  - `SlotInfo::SaveSlotData` (2076B) → **91 events** (가장 큰 save, malloc 0x2d9f byte buffer)
  - `HERO::SaveHeroData` (736B) → **23 events** (header + 8 u16 stat block + 7 byte equip slot + timestamp)
  - `Mission::SaveData` (572B) → **15 events** (Mission flag/count 직렬화)
- ✅ **H_%d.sav layout 개요** (HeroData):
  - +0..3 u32, +4..5 u8 flags, +6..9 u32, +0xa..+0x19 = **8 × u16 stat block** (HP/MP/STR/DEX/CON/INT + 2 ?)
  - +0x45..+0x4b = 7 × u8 (= EquipItem 7 slot, Round 14 의 cat 0-6 일치 추정)
  - +0x4c u32, +0x60 u8, 2 × u64 timestamp
- ✅ **SL_%d.sav layout 개요** (SlotInfo):
  - +0..1 class+level encode, +2..9 GetX/GetY (2 × u32)
  - +0xa..0x11 u64 playtime (MC_knlCurrentTime delta), +0x12..0x15 scene_idx
  - +0x17 부터 3 × 256B 블록 (class_info+0x288/0x388/0x488 — inventory/stat snapshot/buff 추정)
  - +0x31c..+0x489 secondary 영역 (다양한 5/12/28/200B chunk)
- ✅ **상세 documentation**: `docs/h5/SAVE_FORMAT.md` (8 file 타입 + dispatch + layout 개요 + 다음 라운드 작업 목록)
- 산출: `tools/h5_extract_save_writes.py`, 3 × *_writes.tsv, `docs/h5/SAVE_FORMAT.md`, `work/h5/analysis/saveslotdata_disasm.txt`
- **다음 라운드**: load 함수 (SaveHero/SaveSlot/Mission load) cross-check 로 layout 확정 + register propagation 정밀화 + source struct field 의미 라벨링

**[Round 40 — 2026-05-17 완료]** quest_*.dat record byte 정밀 매핑 + decoder 발행 + 3 difficulty scaling 확정 (Round 39 의 save slot 가설 정정)
- ✅ **Quest_GetOffset (0xd40a0, 72B) 분석**:
  - 반환값 = 해당 quest record 의 u16 size 필드 위치
  - 로직: offset=2; for k in 0..idx-1: sz=ByteToInt16(file, offset); offset+=2+sz; → 각 record 가 u16 size prefix + body[size] 구조임 확정
- ✅ **LoadQuestData 1188B 정밀 disasm 추적**:
  - file[r8+2..r8+4] (body[0..2]) = 3 header bytes (h0, h1=obj_count signed, h2)
  - file[r8+5] = strlen0, 그 후 string0 (memcpy → struct[+8], max 28B)
  - 그 다음 strlen1 + string1 (memcpy → struct[+0x24], max 200B)
  - 그 다음 strlen2 + string2 (memcpy → struct[+0xec], max 28B)
  - Phase 1: 3 × 6B objective entries (byte cond_type + byte cond_sub + u32 target_value) → struct[+0x114..+0x128]
  - Phase 2: 3 × 6B reward entries (동일 layout) → struct[+0x140..+0x154]
  - Trailer: 2 byte → struct[+0x16c, +0x16d]
  - obj_count > 0 면 variable sub-loop (151 중 #117 만 obj_count=2 — 실 데이터는 추가 byte 없음)
- ✅ **record body size 공식**: `44 + strlen0 + strlen1 + strlen2`
  - 151/151 records 가 EOF 정확 도달 (22367B == file size)
- ✅ **3 quest files MD5 비교 → 다름 확정** (Round 39 의 "save slot 추정" 정정):
  - q0: b0aa5b...  q1: 3530a4...  q2: d4c26f...  (모두 다름)
  - q0↔q1: 756 byte diff,  q0↔q2: 795,  q1↔q2: 384
  - 차이는 모두 phase1/phase2 의 value 영역에 집중 — type/sub byte 는 거의 동일, value 만 변화
  - **3 difficulty scaling 확정** (enemy_*.dat Round 34 와 동일 패턴):
    - quest #0 EXP reward: q0=340 / q1=20830 / q2=36150 — 단조 증가
    - quest #1: q0=1000 gold + 160 EXP / q2=5000 gold + 12050 EXP
- ✅ **decode_h5_quest.py 새로 작성** (기존 stub 은 mission_list 를 디코드하던 misnamed 코드 — 교체):
  - 3 files 일괄 parse + reward kind 라벨 (17=money, 18=exp, 255=unused) + comparison view
  - `apps/hero5-godot/assets/gamedata/quests.json` (645KB, 3 difficulty × 151 quests + compare table)
- ✅ **h2 (header byte 2) 분포**: 가장 흔한 값 = 255(17), 0(15), 4(11), 6(11), 7(8), 10(8) — quest type 또는 chapter marker 추정
- ✅ **Mission ↔ Quest 데이터 연결 정리**:
  - Mission system (105 achievements, 동일 layout 1 file) 의 type=4 = quest complete (Round 38)
  - Quest system (151 main story, 3 difficulty file) 은 별도 progression
  - 둘 다 phase 구조 (slot/sub/u32) 가 유사 — 공통 design pattern
- 산출: `tools/converter/decode_h5_quest.py`, `apps/hero5-godot/assets/gamedata/quests.json`
- **데이터 RE 거의 마무리** — 남은 큰 데이터원: save 파일 포맷 (DES 키만 알려져 있음)

**[Round 39 — 2026-05-10 완료]** Quest 시스템 식별 (QuestMgr 22+ 함수 + 3 quest 파일 × 151 quests)
- ✅ **QuestMgr 함수 22+ 식별** (Mission 과 별도 시스템):
  - `LoadQuestData` (0xd40e8, 1188B) — quest table loader
  - `QuestStatusList` (0xd4b9c, 2620B), `QuestCheck` (0xd3acc, 1492B)
  - `QuestRewardData` (0xd458c, 1552B), `QuestSetStatus` / `GetQuestStatus`
  - `setQuestViewInfo` (0xd32cc, 2048B), `drawQuestInfo` (0xd2738, 2360B)
  - `LoadNpcBody`, `DrawNpcBody`, `FreeNpcBody` (NPC body asset 처리)
  - `SortQuestList`, `DelQuest`, `QuestListInit`, `Quest_GetOffset`
  - `ItemStringSet`, `DrawQuestString`, `QuestSwitchStatus`
- ✅ **QuestMgr::LoadQuestData 분석**:
  - LoadRes("/c/csv/quest_%d.dat", arg) → arg = save slot index 또는 difficulty
  - r2 = #0x170 (= 368 byte) — Quest struct = 368 byte/entry
  - HERO+0x277 (Round 35 의 Monster +0x277 같은 영역) = quest set selector
- ✅ **VFS 에서 3 quest files 발견**:
  - quest_0.dat: index=55, hash 0x641e44fa, 22367B, count=151
  - quest_1.dat: index=56, hash 0x64305d7b, 22367B, count=151
  - quest_2.dat: index=57, hash 0x644275fc, 22367B, count=151
  - **3 files 모두 동일 내용** (hex dump 일치) → 추정: **save slot 별 quest progress 저장소** (3 save slot 시스템)
- ✅ **Quest record format 개요** (variable-size, avg 148B/record):
  - First record size = 184 byte
  - byte 2..3: record_size u16
  - byte 4..5: 0x0000 (padding/prefix)
  - byte 6: strlen u8 (= 26 첫 record)
  - byte 7..(7+strlen): name string (EUC-KR, 첫 quest 이름 한글)
  - byte (7+strlen)..end: quest data (조건/보상/대화 등 ~120 byte)
- ✅ **Mission 과 Quest 의 관계**:
  - Mission::CheckQuestComplete (Round 37) 가 QuestMgr::QuestCheck 호출
  - Mission = "achievements" (105 metaquests), Quest = "actual story quests" (151 main quests)
  - Mission 이 Quest progress 를 monitoring 하여 achievement 완료 처리
- ✅ **3 quest files 의 의미 추정** (모두 동일):
  - 게임 difficulty 별 quest 변경 없음 (Monster stat 만 difficulty 별 다름 — Round 34/35)
  - 또는 game state 별 master copy/runtime copy/save copy
  - 또는 미사용 redundancy
- 산출: `work/h5/analysis/quest_loadquestdata_disasm.txt` (분석 시작)
- decoder 작성은 다음 라운드 (record 의 quest data 영역 정밀 분석 필요)

**[Round 38 — 2026-05-10 완료]** mission_list.dat record byte → MissionInfo 정밀 매핑 + decoder 발행
- ✅ **LoadMissionTable 460B 정밀 disasm 추적**:
  - r8 (file pos) 변화 추적: 2 (record 시작) → +3 (strlen byte 후) → +strlen (name 후) → +37 (record 끝)
  - 각 byte → MissionInfo struct offset 매핑 식별
- ✅ **File record format 확정** (105 missions × variable size):
  - u16 record_size (body size, header 제외)
  - u8 strlen + name (EUC-KR)
  - u8 mission_type → MissionInfo +4
  - u8 sub_type → MissionInfo +5
  - u8 target_count → MissionInfo +6
  - 5 × 6 byte sub-conditions (각 6 byte: slot u8 + flag u8 + value u32):
    - byte +0 → MissionInfo +7..+0xb (5 slot indices)
    - byte +1 → MissionInfo +0xc..+0x10 (5 sub-flags)
    - bytes +2..+5 (u32) → MissionInfo +0x14, +0x18, +0x1c, +0x20, +0x24 (5 target values)
  - u8 final_flag → MissionInfo +0x28
- ✅ **decode_h5_mission.py 새 도구 작성** + mission.json 발행:
  - 105 missions 모두 정확 parse (named=105/105)
  - **mission_type 분포 (Round 37 의 13 Check* 함수와 매핑)**:
    - type 0 (20 missions): general (sub_type 0/1/2)
    - type 1 (5 missions): single condition
    - type 2 (22 missions): collection (slot=5..8 = helmet/boots/accessory/accessory_2)
    - type 3 (47 missions): rank/achievement (가장 많은 타입, sub_type 0..10)
    - type 4 (5 missions): quest complete (sub_type 0..4)
    - type 5 (5 missions): mix/craft
    - type 255 (1 mission): metadata header
- ✅ **Sub-condition 의미 해석 (mission.json 분석)**:
  - slot=255 (sentinel): empty slot
  - slot=5..8: equipment cat (helmet/boots/accessory/accessory_2 — Round 27 droptable cat 와 일치)
  - sub_flag: condition type modifier (e.g., target item idx, stat threshold 등)
  - target_value: u32 — count, gold amount, level, exp threshold 등
- ✅ **Mission 시스템 호출 흐름 (Round 26/27/28 + Round 37/38 종합)**:
  ```
  플레이어 행동 (강화/orb결합/mix/quest 완료/...)
  → 해당 함수 끝에서 Mission::Check<Type>() 호출
  → mission_list[idx] 의 mission_type / sub_conditions 비교
  → 조건 만족 시 Mission::CompleteMission(idx) → reward 지급
  ```
- 산출: `tools/converter/decode_h5_mission.py` (새 도구), `apps/hero5-godot/assets/gamedata/mission.json`

**[Round 37 — 2026-05-10 완료]** Mission 시스템 데이터원 식별 + 13+ Check* 함수 매핑 (P5 폰트는 LOW PRIORITY — 시스템 폰트 우회 중 영향 없음)
- ✅ **P5 한글 폰트 간단 검토** (게임 동작 영향 없음, 시스템 폰트 Noto Sans CJK KR 우회 중):
  - `_midas_funcFntInvalidate` (156B) = 단순 cache invalidate (glyph index 매핑 아님)
  - `_midas_funcFntJohabToWan` (368B) = Johab → Wansung 변환 lookup loop
  - 정확한 581 glyph 매핑은 시간/임팩트 고려 시 후순위
- ✅ **Mission::LoadMissionTable (0x8b73c, 460B) 분석**:
  - LoadRes("/c/csv/mission_list.dat") → MissionInfo* (entry size 44B)
  - VFS index 48, hash 0x43b86236, 5355B, **count=105 missions**
  - File format: u16 count + variable-size records (record 0 = 41B 등)
- ✅ **13+ Mission Check* 함수 매핑** (Achievement / Quest system):
  - `CheckMissionRefine` (0xa28e0) — 강화 mission (Round 26 ApplyItemRefine 호출)
  - `CheckOrbCombine` (0x8ac0c, 236B) — orb 결합 mission (Round 26 ApplyOrbCombine 호출)
  - `CheckMissionMix` (0x8acf8, 268B) — special mix mission (Round 28 ApplySpecialMix 호출)
  - `CheckMissionPlaytime` (0x8af94, 340B) — playtime achievement
  - `CheckMissionMoney` (0x8b1ac, 212B) — gold achievement
  - `CheckMissionRank` (0x8ab10, 252B) — level/rank achievement
  - `CheckMissionSetItem` (0x8b2e0, 292B) — set item collection
  - `CheckCollection` (0x8a8f0, 372B) — general collection
  - `CheckQuestComplete` (0x8a5ec, 256B) — quest completion
  - `CompleteMission` (0x8a330, 204B) — mark complete
  - `QuestCompleteCounting` (0x89ff0) — quest count tracking
  - `EndingCounting` (0x89fac) — ending counter
  - `SetCheckInit` (0x89ea0, 112B) — init checker
- ✅ **MissionInfo struct = 44B/entry** (105 entries × 44B = 4620B + header 등):
  - 각 mission record: name + condition_type + target_value + reward 등
  - 정확한 byte layout 은 LoadMissionTable 의 BYTEtoInt16/strb 시퀀스 추적 필요 (다음 라운드)
- ✅ **Mission 시스템과 다른 시스템 cross-reference 정리**:
  - Quest 시스템 (별도, _ZN8QuestMgr*) → Mission::CheckQuestComplete 가 link
  - Drop / Refine / Orb / Mix mechanism 의 모든 mission tracking 함수 식별
  - Mission 호출 = 특정 행동 후 trigger (e.g., ApplyItemRefine 끝에서 Mission::CheckMissionRefine)
- ✅ **모든 게임 시스템 데이터원 5종 최종 정리**:
  ```
  enemy_g.dat (1 file)         → Map enemy table
  enemy_*.dat (3 files)        → Monster stat (3 difficulty)
  droptable.dat (1 file)       → Monster drop pool
  smith_*.dat (3 files)        → NPC blacksmith recipes
  mission_list.dat (1 file) ✓  → Achievement/Quest missions ← Round 37 식별
  + slot_15 (item_15.dat, mix_book recipes), c_csv_class.json, c_csv_skill_*, etc
  ```

**[Round 36 — 2026-05-10 완료]** 4 element 시스템 구조 식별 + V[151]/V[152] magic stat pair 의미 정리
- ✅ **4 element 시스템 구조 식별** (formulas_disasm.txt id=7/8 분석):
  - V[136..143] = **8 element bonus fields = 4 elements × 2 dimensions** (각 element 의 atk/def)
    - V[136]/V[137] = element 0 (fire 추정) atk/def
    - V[138]/V[139] = element 1 (ice 추정) atk/def
    - V[140]/V[141] = element 2 (lightning 추정) atk/def
    - V[142]/V[143] = element 3 (dark 추정) atk/def
  - id=7 (calc_pl element atk total): `(sum_4_elements_atk + V[153]/2) * (100+V[27])/100 + V[144]*(100+30*V[89])/100`
  - id=8 (calc_pl element def total): `(sum_4_elements_def + V[153]/2) * (100+V[28])/100 + V[145]*(100+30*V[93])/100`
- ✅ **V[144]/V[145] = current element bonus** (active element 의 main bonus):
  - V[89]/V[93] (HERO +0x262/+0x266) = current element index (atk/def 별 선택)
  - 30% multiplier per element level
- ✅ **V[88..98] = 11 stat fields** (HERO +0x261..+0x26b):
  - id=44 sum 식: `clamp(V[88]+V[89]+...+V[98], 0, 999)` = 11 stats 합산
  - V[89]=atk_element_idx, V[93]=def_element_idx 가 4 byte 간격 — 추정 element class index
- ✅ **V[151]/V[152] = magic stat pair (skill slot 별 magic damage)**:
  - id=4: `(V[6]_skill_atk_phys + (V[134]+V[135])/2 + V[151]) * (100+V[24])/100` — 1차 magic damage
  - id=5: `(V[7]_skill_atk_sec + (V[134]+V[135])/2 + V[152]) * (100+V[25])/100` — 2차 magic damage
  - id=6: `(V[8]_skill_atk_other + V[154]_str) * (100+V[26])/100` — 3차 (다른 type)
  - V[151] vs V[152]: 둘 다 INT-magic 변종, 서로 다른 weapon/skill slot 의 magic bonus
  - 추정: V[151]="phys-derived magic" (str+int), V[152]="pure magic" (int only) 또는 weapon slot 1/2 magic
- ✅ **V[134]/V[135] = magic ATK base pair** (id=4/5 모두에서 평균 사용):
  - 첫 두 element 의 base magic atk
  - 평균 (V[134]+V[135])/2 → 캐릭터의 base magic damage core
- ✅ **V[153]/V[154]/V[155] 의미 재확인**:
  - V[153]: element resistance 또는 element_total_contribution (id=7/8 의 /2 weight)
  - V[154]: stat_str (Round 7)
  - V[155]: max_sp (Round 7)
- ✅ **GV_SUBSTRUCT_FIELDS.md 의 기존 추정과 일치 검증**:
  - 0x2b8/0x2ba = V[134]/V[135] (마법 ATK pair) ✓
  - 0x2bc..0x2ca = V[136..143] (8 element bonus, 4 pair) ✓
  - 0x2cc/0x2ce = V[144]/V[145] (main element bonus) ✓
- ✅ **결론**: V[151]/V[152] 정확한 element 짝 식별은 게임 데이터 + UI 테스트 없이 미완 (BATTLER stat 표시 cross-check 필요), 그러나 **4 element 시스템 구조와 magic damage formula 구조**는 완전 식별.

**[Round 35 — 2026-05-10 완료]** enemy_*.dat record byte → Monster field 정밀 매핑 + decoder 발행
- ✅ **Monster::setEnemyData 1532B disasm 정밀 추적** — record offset 대 Monster field 매핑 추출:
  - record byte 0..3 → Monster +0x22c..+0x22f (4 markers, class/idx codes)
  - byte 4..38 → Monster +0x230..+0x252 (interleaved s16/u8 stats — atk/def/element 등)
  - byte 39..66 → Monster +0x254..+0x26c (7 u32 = drop chance thresholds, Round 31 매핑)
  - byte 67..72 → Monster +0x270..+0x275 (drop count/type/markers)
    - byte 70 = drop_count (Round 27 0xbca68 reader)
    - byte 72 = drop_count_max (Round 27 0xbca44 reader)
  - byte 73..79 → Monster +0x276..+0x27c
  - byte 80..(continues) → Monster +0xf4..+0x114 area (BATTLER stats)
- ✅ **record format 확정**:
  - u16 record_size (per-record variable)
  - u8 name_len + bytes[name_len] (EUC-KR name)
  - data bytes (after name) — 위 매핑
- ✅ **decode_h5_monster.py 새 도구 작성** + monster.json 발행:
  - 3 difficulty × 166 records = **498 monster records 정확 parse**
  - 각 record: name, drop_thresholds (7 tier), drop_markers, stat_f4 (BATTLER stat)
- ✅ **Monster progression 게임 의미 검증** (decode 출력):
  - Easy (enemy_0): drop_count=0 (no drops at all)
  - Normal (enemy_1): drop_count=17~19 (mid drops)
  - Hard (enemy_2): drop_count=26~27 (more drops)
  - **drop chance 가 monster 별 + difficulty 별로 균형 조정** — 게임 difficulty 시스템과 정확 일치
- ✅ **데이터 흐름 완전 매핑 정리**:
  ```
  enemy_*.dat record byte 39..66 → Monster+0x254..+0x26c (drop thresholds)
  → Monster::SetDropItem 가 Rand(0,0xffff) 와 비교 → drop tier 결정
  → droptable.dat 의 monster_idx*4+tier entry 의 byte 들로 NewDropItem 호출
  ```
- 산출: `tools/converter/decode_h5_monster.py` (새 도구), `apps/hero5-godot/assets/gamedata/monster.json` (498 records)

**[Round 34 — 2026-05-10 완료]** Monster::setEnemyData 발견 + enemy_%d.dat 데이터원 식별 — Monster +0x254..+0x275 source 확정
- ✅ **lief+capstone skipdata 로 Monster +0x254..+0x275 writers 전수 검색**:
  - +0x260 (str): 0xc1dac in Monster::setEnemyData
  - +0x264 (str): 0xc1dbc in Monster::setEnemyData
  - +0x268 (str): 0xc1dcc in Monster::setEnemyData
  - +0x26c (str): 0xc1ddc in Monster::setEnemyData
  - +0x270/+0x271/+0x272/+0x273/+0x275 (strb): 0xc1dec..0xc1e30 in Monster::setEnemyData
- ✅ **Monster::setEnemyData (0xc1a94, 1532B) 분석**:
  - 단일 함수가 Monster 의 모든 핵심 stat + drop fields 설정
  - LoadRes("/c/csv/enemy_%d.dat", arg) — arg 가 monster_idx (또는 difficulty)
  - 가변 길이 records (loop 으로 idx 째 record 까지 skip)
  - Monster +0x218 = name string (10 byte 추정)
  - Monster +0x22c..+0x22f, +0x234 (s16), +0x23c, +0x240, +0x244 (s16), ..., +0x254..+0x275: 모든 stat
- ✅ **enemy_%d.dat 데이터원 발견** (VFS):
  - enemy_0.dat: index=19, hash 0xfed40086, 23190B, 166 records
  - enemy_1.dat: index=20, hash 0xfee61907, 23190B, 166 records
  - enemy_2.dat: index=21, hash 0xfef83188, 23190B, 166 records
  - 각 파일 첫 record size = 140B (variable-size records)
  - 3 files 의 difference: byte 0x10 가 다름 (0x16/0x2d/0x46) — 추정 difficulty level
- ✅ **drop 시스템 4 데이터원 최종 정리** (Round 33 의 3 → Round 34 의 4):
  ```
  enemy_g.dat (Map 의 enemy table)        → Map+0x1f0 (HP/MP/ATK/DEF/EXP/Gold + skills, 240B/enemy)
  enemy_0/1/2.dat (Monster stat + drop)   → Monster+0x218..+0x275 (name + stat + drop thresholds + markers)
  droptable.dat (drop pool)               → ItemTable+0x214 (cat × idx × val_15c..val_164)
  smith_0/1/2.dat (NPC blacksmith)        → HERO+0x1d00 (288 craft recipes)
  ```
- ✅ **3 enemy_*.dat 의 의미 추정**:
  - 모두 동일 size (23190B), 첫 14 byte 동일 ("히 고블린" 추정 + 0xc10b prefix + 0xf6 strlen)
  - byte 0x10 (file 첫 record 의 16번째 byte) 만 다름 (0x16/0x2d/0x46) — **3 files = 3 difficulty levels (easy/normal/hard)**
- 산출: `work/h5/analysis/monster_setenemydata_disasm.txt` (382 줄), `monster_mon_init_disasm.txt` (55 줄)

**[Round 33 — 2026-05-10 완료]** enemy_g.dat 121B record layout 정밀 분석 + Monster struct vs enemy_g 분리 식별
- ✅ **Map::MapEnemyG_set (0xae394, 820B) 분석**:
  - LoadRes("/c/csv/enemy_g.dat") + per-enemy 240 byte struct 영역 매핑
  - Per enemy block: Map + (idx * 0xf0) + 0x1f0 (240 byte/enemy)
  - File 의 r7 base 부터 117+ byte 읽음:
    - file +4..0xf (12 byte u8) → struct +0x00..+0x0b: monster markers
    - file +0x10..0x1b (12 byte = 6 u16) → struct +0x0c..+0x17: **HP/MP/ATK/DEF/EXP/Gold** (Round 8 확정)
    - file +0x1c..+0x2a (15 byte u8) → struct +0x18..+0x26: drop / level fields
    - arg2 (sp[0]) → struct +0x27: drop type marker (passed in)
    - file +0x2b 이후: 4 skill blocks × 16 byte = 64 byte skills (struct +0x28..+0xa7)
  - Total file read per enemy ≈ 121 byte (Round 8 결과 일치 확인)
- ✅ **Monster::setEnemyG (0xba358, 68B) 분석**:
  - Monster::setEnemyG(idx) 가 단순 link: Monster +0x2d8 = (gv [0x1488] + idx * 0xf0 + 0x1f0)
  - 즉 Monster +0x2d8 = pointer to enemy_g block (Map struct 안의)
  - **Monster struct 자체의 +0x254..+0x275 fields 는 별도 source**:
    - Monster +0x254/+0x258/+0x25c/+0x260/+0x264/+0x268/+0x26c (5+2 thresholds) — Round 31 의 drop chance thresholds
    - Monster +0x270/+0x271/+0x272/+0x273/+0x274/+0x275 — drop count, type, marker fields
    - 이들은 Monster constructor 또는 game-state init 에서 set, enemy_g 와 직접 매핑되지 않음
- ✅ **enemy_g.dat 의 monster_idx vs droptable.dat 의 monster_idx 매핑 추정**:
  - droptable.dat byte 2 = 0..62 (63 monsters)
  - enemy_g.dat 의 enemy 갯수는 별도 (count u16 in header)
  - 두 데이터원이 같은 monster_idx 공유할 가능성 → cross-check 필요 (다음 라운드)
- ✅ **drop 시스템의 데이터 흐름 정리**:
  ```
  enemy_g.dat → Map+0x1f0 (HP/MP/ATK/DEF/EXP/Gold + skills, 240B/enemy)
  droptable.dat → ItemTable+0x214 (4 drop tiers × 63 monsters × 13B/entry)
  Monster struct +0x254..+0x275 → 별도 init source (drop chance thresholds + markers)
  Monster::SetDropItem (Round 27) 가 위 3 source 모두 사용해 drop 결정
  ```
- 산출: `work/h5/analysis/mapenemyg_set_disasm.txt` (204 줄)

**[Round 32 — 2026-05-10 완료]** MixSmithTableInfo 데이터원 식별 + 288 NPC blacksmith recipes dump
- ✅ **HERO::GetMixSmithTableInfoPtr (0x890f4, 20B)** 분석:
  - 단순 lookup: `r0 = HERO+0x1d00 + r1 * 0x12c (300B)` — entry size 300 byte, base HERO+0x1d00
- ✅ **HERO::LoadMixSmithTableInfo (0x8b958, 588B)** 분석:
  - LoadRes("/c/csv/smith_%d.dat", arg) → HERO+0x1d00
  - Format: u16 count + per entry (record_size + prefix + name + item_id + sub_record + 13byte smith data)
  - 13-byte smith data layout = mix_book recipe (slot_15) 와 동일 (csv row-major, struct column-major)
- ✅ **VFS 에서 smith_*.dat 발견** (3 파일):
  - smith_0.dat: index=70, hash 0x70fbe64d, 5567B, 96 entries
  - smith_1.dat: index=71, hash 0x710dfece, 6302B, 96 entries
  - smith_2.dat: index=72, hash 0x7120174f, 6287B, 96 entries
  - **총 288 NPC blacksmith recipes**
- ✅ **smith table 의 의미 분석** (decoder 출력):
  - **smith_0**: accessory craft (1 ingredient → cat 5/6/7 helmet/boots/accessory, 75%)
  - **smith_1**: weapon craft (3 ingredients [mix material 다양] → cat 0/1/2, 75%)
  - **smith_2**: weapon craft (3 ingredients → cat 0/1/2, 75%)
  - 모두 75% success rate (mix_book recipe 100% 와 다름 — NPC blacksmith 가 더 어려움)
- ✅ **Round 28 의 ApplyNormalMix 가 사용하는 데이터원 확정**:
  - ApplyNormalMix(arg) → GetMixSmithTableInfoPtr(arg) → 288 recipes 중 하나
  - Round 28 의 NPC blacksmith 시스템 = smith_0/1/2.dat 의 recipes
- ✅ **mix_book recipe (slot_15) vs MixSmithTable 비교**:
  - slot_15 (csv item_15.dat): 116 recipes, 다양한 success rate (정제 90%, 일반 100%)
    → ApplySpecialMix (csv 직접 사용 + Mission::CheckMissionMix)
  - smith_0/1/2 (csv smith_*.dat): 288 recipes, 모두 75% success
    → ApplyNormalMix (NPC blacksmith UI 에서 호출)
  - 두 시스템 모두 13-byte smith data layout 공유.
- ✅ **decode_h5_smithtable.py + smithtable.json 발행** (`apps/hero5-godot/assets/gamedata/smithtable.json`):
  - 3 smith tables × 96 entries = 288 records
  - 각 record: name, prefix, item_id, recipe (ing1/ing2/ing3, result_cat, result_idx, success_rate)
- 산출: `tools/converter/decode_h5_smithtable.py`, `work/h5/analysis/loadmixsmith_disasm.txt` (147 줄), smithtable.json

**[Round 31 — 2026-05-10 완료]** droptable.dat byte→arg 정확한 매핑 — Monster::SetDropItem 의 multi-tier drop 시스템 식별
- ✅ **Monster::SetDropItem 의 cat 결정 multi-path 시스템 발견** (Round 30 결론 추가 정정):
  - Rand(0,0xffff) → r0 → 5단계 threshold 체크 (Monster +0x254/+0x258/+0x25c/+0x260/+0x264/+0x268/+0x26c)
  - 각 threshold path 별로 다른 byte 가 cat 으로 사용:
    - **byte 7 = default path cat** (0xbcb54 fall-through 후 0xbcb84 ldr r2 [sp+0x48]=byte 7, 0xbcb98 r8=r2)
    - **byte 11 = highest tier path cat** (0xbce24 → 0xbce70 ldr r2 [sp+0x4c]=byte 11)
    - mid threshold paths (potion/normal/etc): cat = Rand(0,9) (random EquipItem)
  - 최종 NewDropItem cat (r3) = signed s8 of (computed value at sp+0x40)
- ✅ **byte 7 (default path cat) 분포 분석 — 모든 EquipItem cats 0..9 포함**:
  - 0=weapon(28) / 1=weapon_2(28) / 2=weapon_3(27) / 3=weapon_4(28) /
    5=helmet(25) / 6=boots(26) / 7=accessory(26) / 8=accessory_2(24) / 9=shield(28)
  - 0xff (sentinel default) 12 entries
  - **cat 4 (armor) 누락 = Round 22 의 Sorcerer 미구현 stub 사실 cross-confirm** (Sorcerer staff 가 armor 인데 droptable 에 없음)
- ✅ **byte 11 (highest tier path cat) 분포** (Round 30 의 결론 — 정정해서 수용):
  - 5=helmet(27) / 6=boots(14) / 7=accessory(61) / 8=accessory_2(46) / 0xff(default)(104)
  - "rare drop bonus" — 보스급 monster 가 가끔 high-tier accessory drop
- ✅ **Monster progression 정확한 의미 검증** (decode_h5_droptable.py 출력):
  - Monster 0 (저급, 첫 지역): tier 0e/0f/10 common=accessory(7), rare=default. tier 11 common=default.
  - Monster 62 (endgame, 보스): tier 0e common=weapon_4(3) rare=helmet(5), tier 0f common=shield(9) rare=default,
    tier 10 common=shield(9) rare=boots(6), tier 11 common=boots(6) rare=default.
  - **저급 monster = 단순 accessory drop, 고급 monster = 다양한 무기/방어구/방패 + rare accessory bonus**.
- ✅ **caller 2 path (cat=0xe mix material drop) 추가 분석**:
  - SetDropItem 끝에서 `Rand(0, 0xffff) < 0x6665` (=~40% 확률) → 별도 mix material drop
  - sp+0x68 부근 5-byte 배열 (Monster offset table) 에서 random byte pick → drop offset
  - 모든 args (val_15c..val_164) = -1 (sentinel, runtime SetItemOption 가 결정)
- ✅ **caller 1 path 진입 조건**: Monster +0x271 byte != -1 일 때만 NewDropItem 호출 (0xbca40 beq 0xbcbb0)
- ✅ **decode_h5_droptable.py 정정**:
  - 'cat' 필드 → 'cat_default' (byte 7, 0..9 EquipItem) + 'cat_rare' (byte 11, helmet/boots/accessory + default)
  - cat label dictionary 확장 (weapon/weapon_2/weapon_3/weapon_4/armor/helmet/boots/accessory/accessory_2/shield/spirit/default)

**[Round 30 — 2026-05-10 완료]** droptable.dat 재해석 — EquipItem drop pool (Round 29 정정) + monster progression 검증
- ✅ **Round 29 결론 정정**: byte 0 = 0x0b 가 cat 이 아닌 **byte 11 = NewDropItem cat arg** 발견.
  Monster::SetDropItem caller 1 (0xbcc74) 의 register propagation 추적:
  - 0xbcb0c `ldrb r8, [r3, ip]` ← r3=drop_table base, ip=fp+0xb (offset)
  - 0xbcc08 `str r8, [sp+0x40]` ← sp+0x40 = byte 0xb (value)
  - 0xbcc20 `ldr ip, [sp+0x40]` ← reload
  - 0xbcc38 `asr r3, ip, #0x18` ← r3 (NewDropItem cat) = signed s8 of byte 0xb
- ✅ **byte 11 (cat) 분포 분석 — droptable.dat = EquipItem drop pool**:
  - 0x05 (helmet) 27 entries
  - 0x06 (boots) 14 entries
  - 0x07 (accessory) 61 entries
  - 0x08 (accessory_2) 46 entries
  - 0xff (-1, default → EquipItemInfo 376B alloc) 104 entries
  - **총 252 entries — 모두 EquipItem 관련 (potion 아님!)**
- ✅ **Monster progression 분포 검증** (큰 진전):
  - Monster 0 (저급, 초반 지역): 모든 4 tier cat=-1 (default → generic EquipItem drop)
  - Monster 30 (중반): 모든 tier cat=-1 (default)
  - Monster 62 (강함, endgame): tier 0x0e 에 helmet (cat=5), tier 0x10 에 boots (cat=6),
    tier 0x0f/0x11 에 default. **endgame monster 가 specific accessory drop**.
  - 게임 progression 의미와 정확히 일치 — 강한 monster 가 specific cat 의 좋은 EquipItem drop.
- ✅ **byte 0 의 진짜 의미 — constant marker** (format version 추정), cat 아님.
- ✅ **droptable.dat 가 무기 (cat 0..3) drop 을 포함하지 않는 이유**:
  - 무기 drop 은 **default tier (cat=-1)** 의 EquipItemInfo 처리에서 random pick 또는
  - 별도 메커니즘 (Quest reward, Treasure chest 등 — 다음 라운드에서 추가 검증)
- ✅ `decode_h5_droptable.py` + `droptable.json` 정정 발행 (cat / cat_label 의미있는 라벨 부여):
  - 'helmet' / 'boots' / 'accessory' / 'accessory_2' / 'default' 라벨
  - byte 4..10, 12 = NewDropItem 의 다른 args (정확 매핑은 Round 31 작업)
- ✅ NewDropItem 의 r3=cat 이 -1 (=0xff signed) 이면 jumptable miss → default branch
  (0xa7a14 → 0xa7b1c → EquipItemInfo allocation, 376B). 즉 cat=-1 = "generic EquipItem".

**[Round 29 — 2026-05-10 완료]** drop_table 데이터 식별 + dump + decode 도구
- ✅ **ItemTable::LoadItemDropTable (0xa0b54, 80B) 분석**:
  - LoadRes("/c/csv/droptable.dat") → ItemTable+0x214 = drop_table_ptr
  - VFS index 18, hash 0xe58e8176, 3278 byte file
- ✅ **droptable.dat layout 확정**: u16 count(252) + 252 × 13 byte
  - **252 entries = 63 monsters × 4 drop tiers each**
  - byte 0 = 0x0b (cat=11, **potion drop pool**) — all 252 entries 일관
  - byte 1 = 0x00 (sub-flag) — all 252 일관
  - byte 2 = monster_idx (0..62, 4 entries 단위)
  - byte 3 = drop_tier (0x0e/0x0f/0x10/0x11, 4 distinct = 4 tier per monster)
  - byte 4..12 = drop pool 데이터 (NewDropItem args 후보):
    - byte 9 = 0xff sentinel 절반 (108/252) → NewDropItem strb skip 의미 (value < 0)
    - byte 11 = 0xff sentinel 절반 (104/252) → 같은 패턴
    - byte 4 ≈ byte 6 같은 빈도 분포 (paired field?)
    - 정확한 byte ↔ NewDropItem arg 매핑은 caller 1 register propagation 추적 필요
      (0xbcb74..0xbcc74 의 register 변환 — sl/r8/r7/sb 등이 stack 에 store)
- ✅ **droptable.json 발행** (`apps/hero5-godot/assets/gamedata/droptable.json`):
  - flat entries[] (252 records) + by_monster[] (monster_idx 별 group)
  - meta: source/vfs_index/count/monsters/entries_per_monster
- ✅ **droptable.dat 의미**: **monster 의 potion drop pool only**. Monster 가 죽으면
  drop_tier (0..3) 가 random 선택되고 그 entry 의 byte data 가 NewDropItem args 로 전달.
  EquipItem drop 은 별도 메커니즘 (caller 2 의 cat=0xe path 또는 다른 함수) — droptable.dat
  에 포함되지 않음.
- ✅ Round 24 의 tier_flags (legendary/rare/gem/common) 가 **potion drop 에는 무관** —
  potion 은 cat=11 으로 NewDropItem 의 +0x15f strb path (cat ≤ 10) 에 진입하지 않음.
  EquipItem drop 은 별도 데이터원에서 tier_flags 전달.
- 산출: `tools/converter/decode_h5_droptable.py` (새 도구), `apps/hero5-godot/assets/gamedata/droptable.json`

**[Round 28 — 2026-05-10 완료]** RefineItem 의 4 함수 RE (Decompose/Compose/NormalMix/SpecialMix) — 강화 외 모든 mechanism 식별
- ✅ **ApplyNormalMix (0xa7d04, 896B) — 일반 합성 (NPC 대장간)**:
  - 입력: arg = MixSmithTableInfo index (HERO::GetMixSmithTableInfoPtr 로 lookup)
  - csv slot_15 와 **별개 데이터** — MixSmithTableInfo 는 NPC blacksmith table.
  - struct layout: +0x11c (option_grade), +0x11d..+0x11f (cat[3], col-major), +0x120..+0x122 (idx[3]),
    +0x123..+0x125 (count[3]), +0x126 (result_cat), +0x127 (result_idx), +0x128 (success_rate)
  - 동작: IsHaveNormalMixMaterial 검사 → 3 재료 차감 → Rand(0,99) vs success_rate →
    성공 시 result item 생성 + MakeItemOption (cat ≤ 10) + MakeSocket → BagItem::NewBagItem
  - 19-case jumptable (cat 0..18) 별 적절한 ItemInfo 서브클래스 alloc.
- ✅ **ApplySpecialMix (0xa6ed4, 1020B) — special 합성 (csv slot_15 mix_book recipe)**:
  - 입력: arg1 (idx) — slot_15 의 recipe 인덱스
  - GetItemTableInfo(local_item, cat=15, idx=arg1) 로 csv slot_15 데이터를 stack local 에 load
  - struct layout (csv ext byte → struct offset, transpose 후): +0x134 (option_grade), +0x135..+0x137
    (cat[3] col-major), +0x138..+0x13a (idx[3]), +0x13b..+0x13d (count[3]), +0x13e (result_cat),
    +0x13f (result_idx), +0x140 (success_rate)
  - 동작 ApplyNormalMix 와 유사 + Mission::CheckMissionMix 호출 (special mix mission 진척)
- ✅ **csv slot_15 mix_book recipe layout 정정** (Round 25 vs Round 28):
  - csv 파일의 row-major (per-ingredient: cat,idx,count) 분석 (Round 25) = **사용자 관점에서 정확**
  - struct memory 의 column-major (cat[3], idx[3], count[3]) — LoadItemTable 가 transpose 처리
  - parse_mix_book_extra 의 row-major recipe 객체는 **게임 의미상 그대로 유효**, struct memory layout 만 추가 발견
- ✅ **ApplyItemCompose (0xa5f88, 936B) — 두 아이템 option 결합**:
  - 입력: 두 bag pos_index (EquipItem 만, cat ≤ 10)
  - 조건: 둘 다 option_grade ≤ 2 (즉 미강화/약간 강화 상태). 그 이상이면 fail.
  - 동작: 두 item 의 option pair (+0x15f/+0x162, +0x160/+0x163) 모아서 새 option set 생성.
    각 option (option_value > 0) 만 stack 에 모음. 최대 4 option (fp count).
  - gv+0x1444+0x198+fp*6 = 결합 확률 테이블 (6 byte/entry, fp = 모인 option 갯수)
  - Rand(0, 999) vs prob → 성공/실패 결정
- ✅ **ApplyItemDecompose (0xa6330, 1228B) — 아이템 분해**:
  - 입력: bag pos_index + int* out_money
  - 동작: option_grade (cap 4) 기반 확률 테이블 (gv+0x1444+0x1b8+grade*10) → 4 s16 prob thresholds
  - Rand(0, 999) vs prob[0..3] → 5-way 결과:
    - default (가장 높은 prob): money refund (item price / 2 → IncreaseMoney)
    - case 0: cat 13 (mix material) drop
    - case 1: cat 11 (potion) drop
    - case 2/3: 기타 cat
  - option_grade 가 높을수록 좋은 분해 결과 확률 증가 (강화 인 itme 분해 보상 큼)
- ✅ **gv+0x1444 sub-struct 의 RefineItem 확률 테이블 영역 식별**:
  - +0x130..+0x198: ApplyItemRefine 강화 prob table (Round 17 일부 분석)
  - +0x198..+0x1b8: **ApplyItemCompose 결합 prob (6 byte/entry × fp)** ✅ Round 28
  - +0x1b8..+0x1f4: **ApplyItemDecompose 분해 prob (10 byte × 5 grade)** ✅ Round 28
  - +0x1f4..+0x208: ApplyOrbCombine orb prob (Round 26 분석)
- 산출: `work/h5/analysis/applynormalmix_disasm.txt` (225 줄), `applyspecialmix_disasm.txt` (256 줄),
  `applyitemcompose_disasm.txt` (235 줄), `applyitemdecompose_disasm.txt` (305 줄) — 1021 줄 총.

**[Round 27 — 2026-05-10 완료]** NewDropItem signature + Monster::SetDropItem RE — +0x15f tier_flags csv↔drop 일관성 검증
- ✅ **MapItem::NewDropItem (0xa7664, 1696B) signature 식별**:
  - mangle `_ZN7MapItem11NewDropItemEiiaaaaaaaaa` = `(MapItem*, int, int, s8 ×9)` 12 args
  - 매핑: `(this, x, y, cat, idx, val_15c, **val_15f**, val_162, val_160, val_163, val_161, val_164)`
  - 7번째 arg (5번째 s8) = **+0x15f tier_flags**
  - EquipItem path (cat ≤ 10) 만 +0x15c..+0x164 strb 발생 — 각 arg 가 ≥ 0 인 경우만 store (negative arg = "값 없음")
- ✅ **Monster::SetDropItem (0xbc910, 1596B) 의 두 NewDropItem 호출 분석**:
  - Caller 1 (0xbcc74): EquipItem drop path — 13-byte drop_table entry 가 +0x15f arg 결정
    - drop_table 인덱싱: `fp = (random[0..3] * 13) + base`, 그 후 byte 0..12 ldrb 로 entry 읽기
    - sp+0x34 stored value 가 lr 에 load 후 stmib 로 sp+8 (NewDropItem 의 arg7=val_15f) 위치에 store
  - Caller 2 (0xbcf30): mix_material drop path — cat=0xe (14), val_15f = -1 (mvn ip, #0)
    - cat > 10 이므로 NewDropItem 내 +0x15f strb skip. EquipItem 아니므로 tier_flags 무관.
- ✅ **csv↔drop_table 간 +0x15f 일관성 검증**:
  - csv 시점 (LoadItemTable): val_15f = (class_mask | tier_flags << 5)
  - drop 시점 (SetDropItem): drop_table entry 의 byte 데이터에서 그대로 전달
  - runtime 시점 (SetItemOption): option_type code 로 overwrite (Round 24 이미 확인)
  - 결론: **Round 24 의 실증적 라벨 (legendary/rare/gem/common) 이 csv 와 Monster drop pool
    양쪽에서 의미 있게 사용됨**. 보스 monster 가 legendary 무기 drop, 일반 monster 가 common
    drop 같은 게임 로직이 +0x15f tier_flags 로 구분됨.
- ✅ **drop_table entry 13-byte 구조 단서** (mix_book recipe 와 동일 13-byte 단위 — 우연 또는 공유 layout):
  - fp+0 = price/value, fp+5..0xc = drop fields (item_id / cat / val_15c..val_164 candidates)
  - 정확한 byte 매핑은 다음 라운드 (drop_table 데이터 자체 dump + cross-check)
- 산출: `work/h5/analysis/newdropitem_disasm.txt` (419 줄) + `setdropitem_disasm.txt` (397 줄)
- decode_h5_item.py docstring 에 NewDropItem signature + caller 패턴 정리.

**[Round 26 — 2026-05-10 완료]** RefineItem::ApplyItemRefine + ApplyOrbCombine 강화 mechanism RE
- ✅ **강화 stat 보너스 식 발견 (Formula VM id=35/36)**:
  - id=35: `clamp((V[184] + V[187]), 0, 9999)` → refined stat_a = stat_a + sub_count
  - id=36: `clamp((V[185] + V[187]), 0, 9999)` → refined stat_b = stat_b + sub_count
  - V[184] = item +0x156 (s16) = stat_a (무기 atk_min / 방어구 phys_def / 방패 phys_def)
  - V[185] = item +0x158 (s16) = stat_b (무기 atk_max / 방어구 mag_def / 방패 mag_def)
  - V[186] = item +0x165 (s8) = refine_count → Formula VM 미사용 (jumptable cap=10 only)
  - V[187] = item +0x166 (s8) = sub_count = **실제 stat 보너스 양**
- ✅ **EquipItem stat 의미 (items.json 분포 + V[184]/V[185] cross-check)**:
  - weapon (slot 0..3, 86×4=344 records): stat_a < stat_b 일관 (avg 100~140 / 173~308) → atk_min/atk_max
  - shield (slot 9, 81 records): stat_a ≈ stat_b 일관 (avg 30/30) → 균형 phys/mag def
  - helmet (slot 5, 90), boots (slot 6, 93), accessory (slot 7/8, 162): stat_a > stat_b → primary/secondary def
  - spirit (slot 10, 18): stat_a, stat_b 모두 ≤1 → 별도 mechanism (V[184]/V[185] 사용 안함)
  - armor (slot 4, 1 record "스태프"): 1/1 — Sorcerer placeholder (Round 22 cross-confirm)
- ✅ **ApplyItemRefine (0xa292c, 956B) 5-case 결과 jumptable**:
  - case 0 (큰 성공): `refine_count++, sub_count += 2` → +2 stat
  - case 1 (성공)   : `refine_count++, sub_count += 1` → +1 stat
  - case 2 (재료만 소비): no change (random fail before destruction)
  - case 3 (lock)   : `+0x167 = 1` (영구 잠금 — 향후 실패 destroy 방지)
  - case 4 (실패)   : item destroy + `BagItem::DeleteBagItem` + clear EquipItem refs
  - return value cap: refine_count > 9 면 5 (강화 max)
- ✅ **ApplyOrbCombine (0xa1e30, 1208B) 분석**:
  - signature: `ApplyOrbCombine(EquipItemInfo* item, s16 pos, s8 orb_cat, s8 sub_orbs, ItemInfo** out)`
  - orb category arg3 (sl): 3 그룹 (0xe..0x1a / 0x1b..0x27 / 0x28..0x34) × 13 종 = 39 종 orb
  - sub_orbs == 9 면 강도 multiplier 2x (else 1x) — 랜덤 결과 강화
  - item +0x168 = orb_count (현재 채워진 socket 수, V[188])
  - item +0x169..+0x16d = 5 byte orb socket (각 byte = orb_id, 0xff=빈슬롯)
  - 5-case prob outcome jumptable + Mission::CheckOrbCombine 호출 (mission 진척)
- ✅ **decode_h5_item.py::parse_equip_extra 업데이트**:
  - `stat_a` (V[184]) + `stat_b` (V[185]) 의미있는 라벨 추가
  - val_156/val_158 backward-compat 유지
  - refine 식 + ApplyItemRefine jumptable + slot 별 stat 의미 docstring 정리
- ✅ **ITEM_STRUCT.md 정정**:
  - +0x156 (s16 stat_a, V[184])
  - +0x158 (s16 stat_b, V[185])
  - +0x165 (refine_count, V[186])
  - +0x166 (refine_sub_count, V[187]) — **실제 stat 보너스 양**
  - +0x167 (refine_locked)
  - +0x168 (orb_count, V[188])
  - +0x155 = subtype (Round 16 정정 반영, 이전 "class_restriction" 잘못)
- 산출: `work/h5/analysis/applyorbcombine_disasm.txt` (303 줄 disasm)

**[Round 25 — 2026-05-10 완료]** slot_15 (mix_book recipe) 13 byte ext 구조 RE
- ✅ **13 byte recipe layout 확정** (items.json 116 records 분석 + 이름 cross-check):
  - byte 0: 0x00 (separator/version)
  - bytes 1-3 / 4-6 / 7-9: 최대 3 ingredients (cat, idx, count) — 0xff = 미사용
  - bytes 10-11: result (cat, idx) — count=1 implicit
  - byte 12: success_rate %
- ✅ **Recipe 종류 분류**:
  - 쿠킹 (cat 14 결과): 살코기+황혼버섯 → 황혼수프가루 (100%)
  - 포션 합성 (cat 11 결과): 포션 ×2 → 미들포션 (100%)
  - 퀵포션 (cat 11 결과): 포션 ×2 + 지혈초 ×1 → 퀵포션 (100%)
  - 재료 정제 (cat 13 결과): 엑토플라즘 ×10 → 에테르 (90%)
  - 무기 제작 (cat 0..9 결과): 칼날+가죽+강철 → 무기 (60-90% 일반, 20-22% 고급)
- ✅ **success_rate 분포 = 게임 밸런스 검증**: 일반 100%, 정제 90%, 중급 60-70%,
  고급 (legendary 무기) 20-22%. 높은 등급일수록 낮은 성공률.
- ✅ `parse_mix_book_extra` 가 `recipe` 객체 부여 (ing1/ing2/ing3/result_cat/
  result_idx/success_rate). 이전 raw `sb_extra_hex` 대비 의미있는 구조 노출.

**[Round 24 — 2026-05-10 완료]** val_15f upper 3 bit (tier_flags) 의미 식별
- ✅ **핵심 발견: csv val_15f vs runtime val_15f 용도 분리**
  - csv load: lower 5 bit = class_mask, upper 3 bit = tier_flags
  - runtime: SetItemOption (0xa0ff8) 가 +0x15f 를 option_type code 로 덮어씀
  - GetRelieveLevelLimit (0xa835c) 의 `cmp #0x6c` 는 runtime option_type 비교
  - MakeItemOption (0xa10e8) 가 val_15c (option_grade) 로 SetItemOption 호출 여부 결정
- ✅ **upper 3 bit 의 실증적 의미 (items.json 789 EquipItem 분포 분석)**:
  - upper=0 (170 records, no flags): **legendary** — 실가라스/투란기어/디바인세이버 등 보스/named 무기
  - upper=1 (248, bit5): **rare** — 중급 무기/방어구
  - upper=3 (9, bit5+6): **gem** — slot_5 보석 헤어핀/서클릿 (청금석/루비/오팔 등 9종 only)
  - upper=7 (362, bit5+6+7): **common** — 일반 상점 아이템 (롱소드/단검 등)
- ✅ 가설: bit5 = "obtainable", bit6 = "gem-accessory", bit7 = "common-tier"
- ✅ slot_4 (armor) 1 record "스태프" 가 tier=legendary + class_mask=0 인 점이 Round 22
  Sorcerer 미구현 stub 사실과 cross-confirm (Sorcerer 전용 staff 인데 사용 가능 클래스 0개)
- ✅ `decode_h5_item.py::parse_equip_extra` 에 `tier_flags` (정수 0/1/3/7) +
  `tier_label` (legendary/rare/gem/common) string 부여.
- ⏸ 정확한 비트 의미는 더 disasm 필요 (NewDropItem / DropTable cross-check).
  현재 라벨은 records 분포 기반 실증적 추정.

**[Round 23 — 2026-05-10 완료]** HERO::BattleUseItem 분석 + SLOT_META 전면 정정
- ✅ **HERO::BattleUseItem (0x8fd20, 536B) 디스어셈블** → slot_11 의 4 byte fields
  의미 정확 식별:
  - `+0x134` = **effect_type** (HERO[0x2fe] 에 저장 → CalcStatusComputation 분기)
    - 91 (0x5b) = HP heal, 90 (0x5a) = SP heal, 87 (0x57) = buff (보호의 부적)
    - 92 (0x5c) = 마석, 19 (0x13) = test (포션9), 0 = 제련석 (무효)
  - `+0x135` = **success_rate %** (random(0,99) 와 비교, 모든 records 100)
  - `+0x136` = **effect_value** (HERO[0x300] u16: HP/SP 회복량 또는 buff 강도)
    - 포션 LV1/2/3: 4/10/20, 퀵포션: 40/100/160, 엘릭서: 250
  - `+0x137` = **duration** (HERO[0x302] s16: HP buff=50, SP instant=1, 보호의부적=120)
  - 사용 후 SetPotionCoolTime(100) — 100 frame cooldown.
- ✅ SLOT_META 전면 정정 — record 이름 + ext_after_sb 길이 cross-check 결과
  다수 mismatch 발견:
  - slot_12: scroll → **orb** (뇌제의오브/금강의오브, 2 byte ext)
  - slot_13: orb → **mix material** (살코기/재료2..9, 0 ext)
  - slot_15: material_2 → **mix_book recipe** (황혼수프/포션, 13 byte ext)
- ✅ `parse_battle_use_extra` field 라벨 정정 — val_134→effect_type, val_135→
  success_rate, val_136→effect_value, val_137→duration. 의미있는 이름으로.
- ✅ dispatch 정리 — slot_12 (orb) 가 이전에 잘못 battle_use parser 받았던 것
  수정. slot_15 (mix_book) 가 이전 slot_16 위치에서 정정.

**[Round 22 — 2026-05-10 완료]** Sorcerer (class_id=4) 미구현 stub 확정
- ✅ .so 바이너리 클래스 심볼 검색 — 4 player class object 만 존재:
  WARRIOR / ROGUE / GUNNER / KNIGHT. **SORCERER class 없음**.
- ✅ skill csv 검색 — `c_csv_skill_00..03` (4 player class, 각 43 skills) +
  `c_csv_skill_05` (16 monster/boss skills: 암흑탄/지옥소환/얼음폭풍/완전면역 등).
  **`c_csv_skill_04` 완전 부재**.
- ✅ class_stats.json 검토 — 소서러 entry STR/DEX/CON/INT 는 있지만 unk1..unk14
  모두 1 (다른 4 클래스는 6/12/18/24 등 다양). unk0=320 (다른 1000) — 명백한
  placeholder.
- ✅ IfLearnSkill 의 `(class/2)+16=18` 매핑은 dead code path — Sorcerer 가
  실제로 호출돼도 cat 18 (CashItem) 에 학습 가능한 records 없음.
- ✅ class_select.gd UI 정정 — "소서러" → "소서러 (미구현)" 라벨 표시.
  사용자가 선택 시 빈 스킬셋으로 시작하는 문제 인지 가능.
- 결론: **영웅서기5 출시 빌드는 4 클래스 only**. 소서러는 향후 확장 클래스로
  계획됐으나 미구현 채로 출시. cat 18 매핑은 placeholder, slot_18 은 실제로
  cash shop 용도로 재활용.

**[Round 21 — 2026-05-10 완료]**
- ✅ **HERO::IfLearnSkill (0x95d08, 316B) 디스어셈블** → SkillBook +0x134..+0x137
  4 byte fields 의 정확 의미 식별:
  - `+0x134` = **class_id** (0..4 — Warrior/Rogue/Gunslinger/Knight/Sorcerer)
  - `+0x135` = **skill_index** (HERO::skills[] 배열 인덱스, 클래스별 0..9 = 10 skills)
  - `+0x136` = **skill_level** (1..7, 이름 LV 와 정확 매칭)
  - `+0x137` = **required_level** (HERO+0x22d 와 cmp)
- ✅ IfLearnSkill 의 ItemTable category 공식 발견:
  ```
  category = (class_id / 2) + 16   ; signed div, round-toward-zero
  ```
  → Warrior(0)/Rogue(1) → cat 16 (slot_16),
    Gunslinger(2)/Knight(3) → cat 17 (slot_17),
    Sorcerer(4) → cat 18 (slot_18 = CashItem ?? — 별도 path 추정)
- ✅ **slot_16 의 정체 정정** — 기존 SLOT_META 가 'mix_book' 이라 라벨링했으나
  실제 records 모두 Warrior+Rogue 스킬북 (양손베기LV1..3, 돌진LV1..4, 내려찍기LV1..7,
  어깨치기LV1..4, 회전베기 등). SLOT_META[16] 을 `skill_book` 으로 변경.
- ✅ `parse_skill_book_extra` 의 라벨 정정 — val_134/val_135/val_137 을 의미있는
  이름 (`class_id`/`skill_index`/`required_level`) 으로 변경. 기존 `skill_level` 유지.
- ✅ items.json 검증 통계:
  - slot_16: 95 records, class_id=0 (Warrior, 48) + class_id=1 (Rogue, 47)
  - slot_17: 98 records, class_id=2 (Gunslinger, 49) + class_id=3 (Knight, 49)
  - 각 클래스 정확히 10 skills (skill_index 0..9), 각 skill 1..7 levels
- ⏸ Sorcerer (class_id=4) → cat 18 매핑이 CashItem 와 충돌. slot_18 에 class_id=4
  records 없음 — Sorcerer 는 별도 메커니즘 (출시 후 추가 클래스 또는 다른 학습 path)
  으로 추정. 다음 라운드 분석 가능.

**[Round 20 — 2026-05-10 완료]**
- ✅ LoadItemTable 함수 끝 영역 (0xa479c..0xa49c0, 548B) 추가 disasm —
  capstone `skipdata=True` 옵션으로 invalid instruction (literal pool / jumptable
  data) 통과. 새 도구 `tools/h5_dump_loaditem_tail.py` 추가.
- ✅ **slot_17 (SkillBookItem) layout 식별** — jumptable case 16/17 모두
  0xa47c0 으로 분기 (동일 코드 path). record_size=0x138 (312B), 4 byte ext:
  - `+0x134` = u8 skill_class (2 = Gunslinger 계열, 3 = Knight 계열)
  - `+0x135` = u8 skill_id (within class, 0..9)
  - `+0x136` = u8 **skill_level** — '연속사격LV1..LV4' → val=1, 2, 3, 4 정확 매칭 ✓
  - `+0x137` = u8 required_level (LV1..4 = 1, 4, 10, 22 monotonic)
- ✅ **slot_18 (CashItem) layout 발견** — jumptable case 18 → **0xa3b38** 별도
  코드 path (Round 19 가 0xa47c0 으로 추정한 것이 정정됨). hardcoded type 0x12=18
  at +0x14, 2 byte ext:
  - `+0x134` = u8 cash_category (val ∈ {0, 1, 2, 3})
  - `+0x135` = u8 stack/type (val ∈ {0..5, 255} — 255 = passive 추정)
- ✅ `decode_h5_item.py` 에 새 parsers 추가:
  - `parse_skill_book_extra` (slot_17, 4 byte): val_134 / val_135 / **skill_level** / val_137
  - `parse_cash_extra` (slot_18, 2 byte): val_134 / val_135
- ✅ SLOT_META 정정 — slot_18 = `cash` category (이전: skill_book 잘못).
- ✅ items.json 검증:
  - slot_17: 98 records 모두 4 byte fields populated. v134=2 (49 records,
    Gunslinger 계열) + v134=3 (49 records, Knight 계열). 클래스 별 10 skill ID.
  - slot_18: 49 records 모두 2 byte fields populated. v135=255 (31 records,
    passive 추정) + v135∈{0..5} (18 records, active/limited 추정).
- ✅ ITEM_STRUCT.md "Round 20" 섹션 + `parse_skill_book_extra` /
  `parse_cash_extra` parser docstring 업데이트.

**[Round 19 — 2026-05-10 완료]**
- ✅ LoadItemTable 의 cat 12+ jumptable case 별 sb 영역 (struct +0x134..+0x140)
  추가 fields layout 추출:
  - cat 12 (BattleUseItem, 0xa4060): +0x134/0x135/0x136/0x137 (4 byte u8) — slot_11
    포션 csv 와 정확 일치 (val_134=91, 135=100, 136=4, 137=50) ✓
  - cat 13 (OrbItem, 0xa423c): +0x134/0x135 (2 byte, csv 에 보통 없음 — record_size 가 base 만 cover)
  - cat 14, 15 (MixItem, 0xa43f4): 추가 fields 없음
  - cat 16 (MixBookItem, 0xa4578): sub-loop +0x135..+0x140 (12+ byte, csv 에 4 만)
  - cat 17, 18 (SkillBook/Cash, 0xa47c0): 함수 끝 영역 — dump_caller size 부족
- ✅ `decode_h5_item.py` 에 카테고리별 parser 추가:
  - `parse_battle_use_extra`: val_134/135/136/137
  - `parse_orb_extra`: val_134/135
  - `parse_mix_book_extra`: sb_extra_hex (raw 12+ byte)
- ✅ parse_items() 에 SLOT_META[cat]['category'] 별 dispatch 적용:
  - 'equip' (cat 1-11) → parse_equip_extra
  - 'battle_use' (cat 11/12) → parse_battle_use_extra
  - 'orb' (cat 13) → parse_orb_extra
  - 'mix_book' (cat 16) → parse_mix_book_extra

**[Round 18 — 2026-05-10 완료]**
- ✅ `ItemTable::SetItemOption` (240B, @0xa0ff8) 디스어셈블 → `+0x15f` 가
  **random option_type byte** 임을 확인. 함수가 random `option_table[i]` 픽:
  - `+0x15f` (offset+0x15f) = option_type (option_table[i].byte 0)
  - `+0x162` = option_value (level_limit * option_param * randint(0x50,0x78) / 32)
  csv 의 val_15f 는 init default — runtime 변경 가능. items.json 의 class_label
  통계 (Round 16 의 5-class mask 해석) 는 csv 시점에 유효.
- ✅ `LoadItemTable` 의 cat 12+ jumptable cases (0xa4060/0xa423c/0xa43f4/0xa4578/
  0xa47c0) 분석 → 모든 카테고리가 **공통 base layout** 공유:
  - record_size=0x138 (BattleUseItem/Orb), 0x134 (Mix), 0x144 (MixBook), 0x138 (SkillBook/Cash)
  - 공통: csv +2 (read+discarded), +4 (u16 → struct +0x16), +6 (strlen),
    name → struct +0x18, u32 → struct +0x30, sub_record_len + memcpy → struct +0x34..+0x134
  - EquipItem (cat 1-11) 만 sb-area (struct +0x150..+0x167) 추가
  - 다른 카테고리는 struct +0x134.. 에 카테고리별 추가 fields (4..N byte)
- ✅ `decode_h5_item.py` 에 `parse_common_extra` 함수 추가 — 모든 카테고리에
  `item_id` (u32) + `sub_record_len` + `sub_record_hex` 부여. 검증: 19 슬롯
  모두 첫 record 에 새 필드 적용 (롱소드/포션/살코기/양손베기LV1/창고확장 등).

**[Round 17 — 2026-05-10 완료]**
- ✅ `RefineItem::ApplyItemRefine` (956B, @0xa292c) 디스어셈블 → 강화 시
  변경되는 EquipItemInfo struct field 식별:
  - `+0x165` = refine_count (강화 횟수, u8)
  - `+0x166` = refine_sub_count (보조 강화, u8)
  - `+0x167` = refine_locked (1=영구 잠금, u8)
  ApplyItemRefine 의 r7 jumptable 결과:
  - r7=0/1: 강화 +1 success — +0x165 += 1, +0x166 += 1 또는 +2
  - r7=3: refine lock 적용 — +0x167 = 1
  - r7=4: 강화 실패 — `EquipItem::ClearEquipItem` (아이템 destroy)
- ✅ `EquipItemInfo::CopyData` (0xa8884) 가 +0x165, +0x166, +0x168 모두 복사 →
  runtime 강화 결과가 saved 형태로 보존.
- ✅ val_15f upper 3 bit (`>>5`) 분포 통계 추출 (`tools/h5_check_items.py`):
  - upper=0 (no upper bit) — 170 items (중급/희귀 무기)
  - upper=1 (32, bit5) — 248 items (강화/보스 무기 — 스톰브링거/캘라보그)
  - upper=3 (96, bits5+6) — 9 items (slot_5 헤어핀/서클릿 보석 액세서리)
  - upper=7 (224, all) — 362 items (common 기본 아이템 — 롱소드/서클릿)
- ⏸ upper 3 bit 의 정확 의미 식별 미완 — bit6=gem accessory, bit7=common flag
  가설. ItemTable::SetItemOption / DropTable 분석으로 확정 가능 (다음 라운드).

**[Round 16 — 2026-05-10 완료]**
- ✅ items.json 의 `class_restriction` (struct +0x155) 매핑이 **잘못됨**을 발견.
  IsEquipPossible / IsEquipPossibleSpirit cross-check 로 +0x155 가 단순 byte 비교
  (== N) 형태 — 즉 **subtype code** (5=weapon, 7=spirit, 0..4=weapon/armor sub-cat).
  slot_10 spirit 의 cls=5 가 17 records 인데 IsEquipPossibleSpirit 는 cls==7 만
  허용 → cls 가 weapon/armor sub-type 분류 임이 확인.
- ✅ **진짜 class restriction = `val_15f & 0x1f`** (struct +0x15f 의 lower 5 bit).
  비트 마스크: bit0=W (워리어), bit1=R (로그), bit2=G (건슬링어), bit3=K (나이트),
  bit4=S (소서러).
- ✅ items.json 통계 검증:
  - val=31 (WRGKS, 모든 클래스) 385 records (가장 많음 — 일반 무기/방어구)
  - val=9 (WK), val=17 (WS), val=14 (RGK), val=18 (RS), val=15 (WRGK) 다양
  - spirit 검증: 데몬의뿔 W / 고렘의인장 RS / 팬텀의부적 WS / 기사의징표 RGK
- ✅ `decode_h5_item.py` 의 fields 업데이트:
  - `class_restriction` → `subtype` 으로 rename (정확)
  - `class_mask` (val_15f & 0x1f) + `class_label` (W/R/G/K/S 조합 string) 추가
- ⏸ val_15f upper 3 bit (값 32, 64, 128) 의 추가 의미는 다음 라운드.

**[Round 15 — 2026-05-10 완료]**
- ✅ `tools/converter/decode_h5_item.py` 에 `parse_equip_extra` 함수 추가 —
  Round 14 의 csv layout 활용해 EquipItem (cat 1-11) extra body 가변 parse.
- ✅ items.json 에 새 named fields 부여 (cat 1-11 only):
  - `item_id` (u32 from extra+0)
  - `sub_record_hex` (variable len byte sequence)
  - `class_restriction` (u8 — 비트 마스크 추정)
  - `level_limit` (u8)
  - `val_150..val_160` (u8/u16 raw stat slots)
  - `triplet_162` (3-byte triplet)
- ✅ 비-EquipItem (cat 12+) 슬롯은 named fields 없음 (별도 layout 필요).
- ✅ 검증 완료: 롱소드 cls=0/lv=1, 나이트롱소드 lv=5, 버클러(방패) cls=3
  (워리어/나이트), 서클릿(헬멧) cls=5/lv=1 — 모두 합리적 매핑.
  cls 비트 마스크 가설: 1=warrior, 2=rogue, 4=gunslinger, 8=knight, 16=sorcerer
  (다음 라운드 IsEquipPossible cross-check).

**[Round 14 — 2026-05-10 완료]**
- ✅ `tools/h5_extract_loaditem_layout.py` — ItemTable::LoadItemTable (4320B,
  @0xa38e0) 디스어셈블 + csv read → struct store 시퀀스 자동 추출 도구.
  EquipItem 영역 (cat 1-11, 0xa3cf0~0xa4060) 분석.
- ✅ csv record body → in-memory EquipItemInfo struct field 매핑 추출:
  - csv +0..1 = record count (loop init)
  - csv +2..3 = u16 read but discarded (struct +0x14 = function arg category)
  - csv +4..5 → struct +0x16 (refine_value u16)
  - csv +6 (u8 name_len `nl`) → 7..6+nl name string memcpy → struct +0x18
  - csv +7+nl..+10+nl (u32) → struct +0x30
  - csv +11+nl (u8 sub_record_len `sblen`) → 256B sub-record memcpy → struct +0x34
  - 그 후 sb 시작 위치에서 u16/u8 mixed sequence → struct +0x150..+0x162
- ✅ LoadItemTable 안에서 `Formula::calc(formula_id=0x7f3=2035)` 호출 — load
  시점 base stat 즉시 계산 패턴 확인.
- ⏸ csv extra (가변 길이) 는 단순 u16 array 와 다름 — items.json 의 stats_u16
  가 부정확. decode_h5_item.py 정확화는 다음 라운드.

**[Round 13 — 2026-05-10 완료]**
- ✅ EquipItemInfo struct 핵심 field 5개 식별 — `tools/h5_dump_caller.py` 로
  CopyData / IsEquipPossible / GetLevelLimit 디스어셈블:
  - +0x14 = item_category/slot_type (s8) — IsEquipPossible jumptable 의 조건
  - +0x155 = class_restriction (s8) — HERO+0x22c (class_id) 와 비교
  - +0x15d = level_limit (s8) — GetLevelLimit 가 fetch
  - +0x168..+0x16d = 6 socket slot (orb/refine ID, 0xff = 빈슬롯)
- ✅ V[168..182] = ItemBase struct (Formula::calc 5번째 인수) field 영역.
  formulas_disasm.txt 와 cross-check 로 사용 패턴 식별:
  - V[168] (item +0xe) = base SP cost (`V[168]*(100-V[123])/100`)
  - V[170] (item +0x16) = base cooldown (`V[170]*(100-V[125])/100`)
  - V[174] (item +0x44) = damage growth multiplier (`V[56]+V[57]*V[174]`)
  - V[181] (item +0x4e) = speed/weight divisor
- ✅ csv extra (33..80B) ≠ in-memory EquipItemInfo struct (376B) 확인.
  csv stat → struct offset 매핑은 `ItemTable::LoadItemTable` (4320B) 디스어셈블
  필요 — 다음 라운드. decode_h5_item.py 에 layout 차이 코멘트 추가.
- ✅ ITEM_STRUCT.md 의 EquipItemInfo 섹션 + ItemBase 섹션 완전 재작성.

**[Round 12 — 2026-05-10 완료]**
- ✅ V[122..126] 5 buff slot 정확 라벨 확정 — formulas_disasm.txt 의
  `(100±V[xxx])/100` 패턴 + buildup csv 라벨 cross-check:
  - V[122] = EXP %bonus (csv 0x1d "경험치LV")
  - V[123] = SP소모량 감소% (csv 0x1e, 공식 `V[168]*(100-V[123])/100`)
  - V[124] = CP충전LV (csv 0x1f, 공식 `(V[124]/100)*150+300`)
  - V[125] = 쿨타임 감소% (csv 0x21)
  - V[126] = 포션효과 %bonus (csv 0x23)
- ✅ V[151], V[152] 둘 다 magic stat (INT 보정) 확정 — 이전 V[152]=DEX 추정 정정.
  formulas_disasm.txt 에서 V[151]/12, V[152]/12, V[152]/V[13], V[151]*V[56]/100
  같은 magic atk 보정 패턴 일관 확인. 둘은 element 1/2 짝 (id=4 vs id=5 magic
  atk1/2). 정확 element (fire/ice 등) 매핑은 다음 라운드.
- ✅ battle_system.gd / formula_vm.gd 의 V[122..126] / V[151,152] 라벨 정정.

**[Round 11 — 2026-05-09 완료]**
- ✅ `tools/h5_decode_buildup.py` — c_csv_buildup.json (111 buildup entries) 의
  extra_hex 형식 (`[ffff][type:u8][sub:u8][val:u16]` × N) decode + ApplyBuildupEffect
  entry type 자동 매핑.
- ✅ **V[112..116] 5 secondary stat 라벨 확정**:
  - V[112] = 근접명중 (csv 0x14 → ABE 11 → V[129] bonus, id=25 *10 multiplier)
  - V[113] = 장거리명중 (csv 0x15 → ABE 12 → V[130], id=26 *10)
  - V[114] = 회피 (csv 0x16 → ABE 13 → V[131], id=27 flat)
  - V[115] = 방패방어 (csv 0x18 → ABE 14 → V[132], id=28 flat)
  - V[116] = 크리티컬 (csv 0x19 → ABE 15 → V[133], id=29 flat)
  - 5 클래스 base 패턴이 합리적 (워리어 근접명중 24, 건슬링어 장거리명중 24,
    워리어 방패방어 5, 모두 크리티컬 0).
- ✅ **V[62]/V[63] = base_con/base_int 정정** — 이전 라운드 매핑 오류 발견.
  buildup csv "건강+#1" (csv 0x03 → ABE 4 → V[120]) = bonus_con 검증.
  "정신+#1" (csv 0x04 → ABE 5 → V[121]) = bonus_int.
  → V[62] = base_con / V[63] = base_int (이전 int/con 으로 잘못 매핑됨).
- ✅ class_stats.json byte sequence 가 STR/DEX/**CON/INT** 순서임 확인 →
  `tools/converter/decode_h5_class.py` 정정 + class_stats.json 재생성 +
  class_select.gd 표시 순서 정정 + battle_system.gd / formula_vm.gd 일괄 정정.
- ✅ 정정된 5 클래스 stat: 워리어 STR12/DEX8/CON10/INT6 (탱커),
  로그 6/10/8/12, 건슬링어 8/12/6/10, 나이트 10/6/12/8 (방패 탱커),
  소서러 6/8/8/14 (마법사 — INT 압도) — 모두 클래스 컨셉과 일치.

**[Round 10 — 2026-05-09 완료]**
- ✅ `tools/h5_find_kr_stat_strings.py` — .so .rodata 에서 한글 stat label 0건 확인.
  → 한글 라벨이 .so 가 아닌 VFS text/*.json 에 분산 (Hero5 의 string indexing
  방식). 정적 .so 분석으로 stat label↔calc_pl id 직접 매핑은 불가능 입증.
- ✅ `tools/h5_find_kr_text_idx.py` — VFS text JSON 에서 stat label sequence 추출.
  핵심: `00017_488ab1c6.json` first region (offset 142..420) 에 status menu 의
  20-stat 표시 라벨 순서 발견 (방어력/공격력/물리방어력/마법방어력/명중률/회피율/
  정확도/근접방어/장거리방어/마법공격/특수방어/특수공격/근접공격/장거리공격/
  물리회피/문법저항/마법적중/마법방어/크리티컬/크리티컬저항).
- ✅ `tools/h5_calc_status_table.py` — `HERO::CalcStatusComputation` 의 24 calc
  호출 자동 추출. **모두 calc_sk[2003]=V[41] + calc_sk[2004]=V[156]** 두 공식만
  사용 (7 EquipItem slot × 2 stat + 4 spirit slot × 2 stat). 결과는 0x2bc..0x2d6
  (V[136..149] element bonus 영역) cache. → V[112..116] 와 직접 무관 확인.
- ✅ `tools/h5_disasm_property_menu.py` — `StateInGameMenu::DrawPropertyMenu` 가
  Formula::calc 직접 호출 0건이며, stat read 가 모두 register-indirect
  (`ldr ?, [reg, reg]`) 형태임 확인. cache offset 이 GOT/literal pool 동적 lookup
  → 정적 매핑 어려움. V[112..116] 5 stat 라벨 정확 식별을 위해 다른 경로
  (save 데이터 / buildup csv / 동적 디버깅) 가 필요.

**[Round 9 — 2026-05-09 완료]**
- ✅ `tools/h5_apply_buildup_disasm.py` — HERO/BATTLER ApplyBuildupEffect
  jumptable 자동 추출 (56 entry × 2). 산출 `applybuildup_table.tsv`.
- ✅ V[122..126] (0x2a0..0x2a8) = 5 buff stat slot 확정. Entry type 30/31/32/34/36.
- ✅ V[125]/V[126] (0x2a6/0x2a8) buff slot 라벨 확정 (이전 미확정).
- ✅ `tools/h5_extract_class_stats.py` — c_csv_class.json 의 5 클래스 secondary
  stat base 추출 (워리어 24/18/24/5/0, 로그 12/12/18/3/0, 건슬링어 6/24/6/2/0,
  나이트 18/6/12/4/0, 소서러 1/1/1/1/1).
- ✅ `tools/h5_find_battle_check_funcs.py` — 전투 핵심 함수의 immediate calc 호출
  추적. ProcDemageCalc → calc_pl id=1,2,3, CalcStatusComputation → calc_sk
  id=2035,2036 (EquipItem stat bonus 합산).
- ✅ HERO::InitStatusComputation (0x95e44) 가 V[118..133] (0x298..0x2b6) 영역
  전부 0 reset 확인 — buff/temp bonus 영역.
- ✅ battle_system.gd::_player_ctx, formula_vm.gd::_player_default 에 V[111..116]
  클래스별 정확 lookup (class_stats.json) + V[122..133] buff/bonus slot 매핑 적용.
- ⏸ V[112..116] 5 stat 의 한국어 라벨 (적중/회피/크리티컬/블록/속도 중 어느 것)
  식별은 status menu UI 함수 한글 string 매핑 RE 가 필요 — 다음 라운드.

**[Polish 라운드 — 2026-05-09 완료]**
- ✅ 통합 파이프라인 `tools/h5_extract_pipeline.py` (9 단계, incremental, ~6s).
- ✅ Scene body opcode 정적 trace `tools/h5_scn_body_stats.py` (258/258, 99%+ dispatch).
- ✅ BATTLER damage disasm `tools/h5_extract_battle_funcs.py` + `docs/h5/BATTLE_FORMULA.md`.
  Event_PlayerDamage 공식 100% 추출, BATTLER offset (0xf0/0x180/0x210) 확정.
- ✅ SMAF↔OGG audit `tools/h5_smaf_audit.py` — 42:42 1:1 → 변환 작업 영구 클로즈.
- ✅ P5 부분 — table.dat = **Unicode BMP** (EUC-KR 아님) 정정. `docs/h5/P5_FONT_MAPPING.md`.

**[P5 잔여] kor.fnt 581 ↔ Unicode 매핑** — 자율 가능, 게임 영향 X
- 다음 단계: `_midas_funcFntInvalidate` (size 미상) 디스어셈블 → codepoint→glyph_index 함수.
- 현재 시스템 폰트(Noto Sans CJK KR)로 충분 — polish 만.

**[P6] Android APK 실 빌드 검증** — 사용자 직접 진행 필요
- Godot Editor 4.2+ + Install Android Build Template + Export Templates (~1GB)
  + JDK 17 + Android SDK + NDK.
- `apps/hero5-godot/export_presets.cfg.template` 참조.
- 이 머신에서 자동화 불가 — 사용자 GUI 진행 필요.

**[후속 자율 가능]**
- `HERO::NewHitEffect` (1712B, 39 callee) → 정공식 (atk × pct − def × ?) + 스킬 multiplier 추출.
- `HeroSkillAtkHardCode` (888B, 37 callee) → 스킬별 분기 (대시/베기/원거리).
- 100B 급 작은 Event_* 함수들 (Event_PlayerDamage 패턴) 같은 방식으로 100% 추출.

### 6.3 환경 / 도구 빠른 참조

#### 새 클론 / assets 비어있을 때 — 처음부터 복원
필수: `Hero5/영웅서기5(최신폰전용).apk` 가 있어야 함.

```powershell
# 1) APK unzip → work/h5/extracted/
$apk = "Hero5\영웅서기5(최신폰전용).apk"; $out = "work\h5\extracted"
New-Item -ItemType Directory -Force -Path $out | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::ExtractToDirectory($apk, $out)
```

```bash
# 2) Phase 2 — 자산 추출/디코딩 (Python 3.10+ 필요)
python tools/h5_vfs_unpack.py            # VFS 2189 entries
python tools/h5_recover_names.py         # 99.7% 이름 복원
python tools/h5_batch_sprite.py          # sprite 421 + palette 588
python tools/h5_extract_text.py          # 한글 18,837 unique

# 3) 디코더 일괄 (게임 데이터)
for f in tools/converter/{convert,decode}_h5_*.py; do
  python $f 2>/dev/null
done

# 4) Phase 3 — Godot 임포트 + 검증
python tools/import_to_godot.py          # opcode_table.json 자동 포함 (capstone+lief 있을 때)
python tools/verify_godot_project.py     # → 0 errors / 0 warnings 기대
```

#### .so 분석 도구 (capstone+lief 필요)
```bash
pip install lief capstone

python tools/h5_extract_opcode_disasm.py    # 77/77 opcode → opcode_table.json
python tools/h5_event_arg_sizes.py           # 105 Event_* arg sizes
python tools/h5_extract_enemy_layout.py      # enemy_g 121B layout 검증
```

#### Ghidra (옵션 — capstone 으로 대체 가능)
```bash
# 헤드리스 모드 (script 자동 실행)
"D:/ghidra_12.0.4_PUBLIC/support/analyzeHeadless.bat" \
  "D:/testrepo/work/h5/ghidra_project" Hero5 \
  -process libHeroesLore5.so -noanalysis \
  -scriptPath "D:/testrepo/tools/ghidra" \
  -postScript DecompileHero5Keys.java

# tools/ghidra/*.java — 15개 분석 스크립트 (DES/Scene/Interpreter 등)
# capstone+lief 환경이 있으면 대부분 Python 도구로 대체 가능.
```

#### Ghidra (추가 디컴파일 필요시)
```bash
# 헤드리스 모드 (script 자동 실행)
"D:/ghidra_12.0.4_PUBLIC/support/analyzeHeadless.bat" \
  "D:/testrepo/work/h5/ghidra_project" Hero5 \
  -process libHeroesLore5.so -noanalysis \
  -scriptPath "D:/testrepo/tools/ghidra" \
  -postScript DecompileHero5Keys.java

# tools/ghidra/ 스크립트들:
#   DecompileHero5Keys.java   — DES/VFS/JNI 핵심 함수
#   FindAssetNameTable.java   — loadAssetFromVFS caller
#   DecompileNameLookup.java  — JNI 브리지
#   FindSceneLoader.java      — scene 로더 후보
#   DumpScnRef.java           — .scn 참조 함수
#   DumpInterpreter.java      — Interpreter::doScript
#   DumpInterpreterCore.java  — Token/Scripts/Strings/Event_*
#   FindOpcodeDispatch.java   — onFunction 후보
#   DumpGbm.java              — GbmImage::LoadImage
#   DumpHeroChar.java         — HERO/CHAR 클래스
#   DumpMonsterLoad.java      — Monster/EnemyG_set
#   DumpMapInit.java          — Map::Initialize/LoadData
#   DumpDes.java              — MX_des*
#   DumpDesArg.java           — DES key arg trace
#   FindFieldWrites.java      — this+offset 쓰기 검색

# Ghidra GUI (수동 분석)
"D:/ghidra_12.0.4_PUBLIC/ghidraRun.bat"
# → Open project → D:/testrepo/work/h5/ghidra_project/Hero5
```

### 6.4 핵심 산출물 인덱스

#### Phase 2 (자산 추출 / 분석)
| 무엇 | 어디 |
|---|---|
| VFS catalog | `work/h5/vfs_catalog.tsv` |
| 자산 이름 (2,182 / 99.7%) | `work/h5/analysis/asset_names.tsv` |
| 디컴파일 코드 모음 | `work/h5/analysis/*.c` (19+ 함수, 핵심: scn_loader / opcode_dispatch / monster_load / des_key / gbm_loader / interpreter_core) |
| Opcode 매핑 (77종) | `work/h5/analysis/opcode_table.tsv` |
| 스프라이트 PNG (3,798) | `work/h5/converted/sprites/<file>/frame_NN_*.png` |
| 한글 코퍼스 (18,837 unique) | `work/h5/converted/text/_corpus.txt` |
| _pa 시각화 컨택트시트 | `work/h5/analysis/pa_swatches/_index.html` |
| Map collision/tile 매핑 | `work/h5/analysis/mapdata_index.tsv` |
| Scene 헤더 (258개) | `work/h5/analysis/scn_headers.tsv` |
| Ghidra 프로젝트 | `work/h5/ghidra_project/Hero5/` |

#### Phase 3 (Godot 리메이크)
| 무엇 | 어디 |
|---|---|
| Godot 프로젝트 | `apps/hero5-godot/` |
| 임포트된 자산 (gitignored) | `apps/hero5-godot/assets/` |
| 게임 데이터 JSON (15+ 테이블) | `apps/hero5-godot/assets/gamedata/` |
| Map 데이터 (collision + tile) | `apps/hero5-godot/assets/maps/<id>.{json,col.bin,tile.bin}` |
| Sprite name → dir 매핑 | `apps/hero5-godot/assets/sprite_index.json` |
| Scene 인덱스 | `apps/hero5-godot/assets/scenes/index.json` |
| 임포트 파이프라인 | `tools/import_to_godot.py` |
| 정합성 검증 | `tools/verify_godot_project.py` |
| Android export 가이드 | `apps/hero5-godot/export_presets.cfg.template` |

### 6.5 최근 커밋 히스토리 (작업 추적)

```
9b6174b  도주 % + 도움말 + 맵 이름 + 메뉴별 BGM
7c3d422  turn 표시 + 인벤 정렬 + 토스트 + Settings 영구
d619817  자동 인카운터 + auto-save + tile attr + 퀘 보상 정밀
2aa969e  HP회복 + 장비비교 + minimap + settings
a2ec161  HUD + 슬롯 삭제 + NPC 색상 + 인벤 필터
a058070  quest 처치 카운트 + warp trigger + NPC 한글 + 이펙트 애니
c600e11  sprite 매핑 + Title 로고 + stat 분배 + 적 그래픽 + 퀘스트 보상
9b5072c  클래스 선택 + NPC sprite + 포션/장비 사용 + 세이브 메타
4f3265d  레벨업 알림 + 장비 stat + Quest UI + BGM 페이드
4514bd6  상점 UI + 레벨업 + NPC 정밀 + 다중 세이브
7f9dec3  item stat + damage popup + dialog 분기 + scene 전환
e9eff82  equipment + inventory UI + combat 정밀 + NPC 스폰
2ba8534  drop/shop/smith/quest 데이터 + Quest 시스템 + Title 슬롯 + skill resolver
4c91c65  skill/item/quest tree 디코딩 + 사운드 hookup
6ff31e9  GameData API 확장 + 전투/인벤 실데이터 연동
cd57c8d  MVP 검증 + enemy 정확도 + NPC/quest 데이터
0f9f834  enemy stats + walk-cycle + Interpreter 확장 + Android export
7b6b455  DES key + 고정사이즈 csv + GameState 통합
e675855  stats 디코딩 + 전투 UI + collision 디버그
6af2634  한글 폰트 변환 + Dialog/Status UI
2dc2bfa  맵 데이터 + Interpreter 핸들러 + 세이브 골격
daf4be6  캐릭터 + Interpreter + 타이틀/데모 씬
860f997  opcode 매핑 + Map 렌더러 + 폰트/SMAF 분석
78dafe9  .scn 헤더 파서 + Scene_Init 디컴파일
1f7a4b8  자산 이름 99.7% + anim 파서 + Phase3 결정
fc19f8a  자산 이름 99.3% 복원 (Phase 2-B 완료)
dc59407  DEX 메소드 분석 + TINY_META 파서
89a4fdc  Ghidra hash 함수 복원 (DJB2-like)
79759b8  한글 추출 필터 개선
637b164  잔여 분류 + 한글 텍스트 추출
c011eae  sprite 디코더 type=0x04/0x08/0x18
fbfaebe  Phase 2-A.4 sprite 디코더 (84%)
8aec053  Phase 2-A.2~3 _pa 인코딩 + 미매칭 클러스터링
c57be91  Phase 2-A.1 bin 포맷 호환성 프로브
6a1c78a  영웅서기5 리메이크 시작점
```
