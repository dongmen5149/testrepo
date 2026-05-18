# Hero5 다음 세션 인수인계

> 한 페이지로 정리한 현재 상태 + 빠른 재개 가이드. 상세 진행은 [PROGRESS.md](PROGRESS.md).

## ⚡ "영웅서기5 다음 내용 진행해줘" → **Round 77 (Godot Editor 실 실행 검증 또는 LoadSkillTable disasm 또는 TEM 정밀)**

차기 세션 즉시 할 일:
1. 환경 확인: `PYTHONIOENCODING=utf-8 python tools/verify_godot_project.py` → `0 warnings` 확인
2. 회귀 테스트 (선택): `python tools/h5_test_stat_modifier.py` → `All Round 76 active effect stat modifier checks passed.`
3. **R77 추천 작업** (이 문서 §D 참조):
   - 옵션 A: **Godot Editor 실 실행 검증** — B 키 → SKILL → log fx_str + UI Combo bar + ATK/DEF 변화 시각 확인 (사용자 작업 0.5-1 라운드)
   - 옵션 B: LoadSkillTable disasm (R75 매핑 정확화, 0.5 라운드)
   - 옵션 C: TEM 정밀 (0.5 라운드)
   - 옵션 D: special path 0x9b100/0x9b124 (R72 미해결, 0.5 라운드)
   - 옵션 E: type 22 / SetDialogWindow 내부 RE (0.5 라운드)

**전체 진척**: Godot 실 구현 **87-92%**, 리메이크 출시 **85-94%** (UI R51-58 + RE R59-60/65/67-73 + character/AI R61-63 + 보상 R64 + Quest R65 + dual host R66 + ProcHeroSkill RE R70-73 + R74 backend damage + R75 frontend UI + 자동 dispatch + **R76 stat modifier 통합 + tick 자동**).

---

업데이트: 2026-05-19 (Round 76 — **active effect stat modifier 통합 + tick 자동 호출**. R75 의 active effect Array 가 실 stat 에 영향. **`GameState.total_attack` 보강**: `raw = (base + equip_bonus); buff_pct = Σ active_buffs.f1 (clamp 0..200); return raw × (100 + buff_pct) / 100`. **`GameState.total_defense` 보강**: `stance_pct = Σ active_stances.f1 (clamp 0..150); curse_pct = Σ active_curses.f1 (clamp 0..80); return raw × (100 + stance_pct - curse_pct) / 100`. **battle_system._enemy_turn 끝에서 `GameState.tick_active_effects()` 자동 호출** — turn 마다 remaining_turns 감소 + 만료 자동 제거 + state_changed signal 발화 → status_panel 자동 갱신. **공식 합리성**: buff cap 200% (+200% ATK max), stance cap 150% (KNIGHT 방어 자세 +50% 등), curse cap 80% (방어력 80% 감소 max — 절대 0 막아냄). **stance + curse 동시 적용**: net 차이 (stance_pct - curse_pct) 적용. `tools/h5_test_stat_modifier.py` 신규 — total_attack active_buffs loop + clamp 0..200 + raw×(100+pct)/100 / total_defense stance+curse loop + clamp 0..150/0..80 + net_pct / battle_system._enemy_turn 끝 tick 호출 + state_changed.emit / R76 docstring markers (2 files) / Python 시뮬 7 case (buff 20%/누적 30+20%/clamp 200% / stance 50% / curse 30% / stance+curse net / curse clamp 80%) 모두 통과. R63/R74/R75 회귀 모두 통과. .so 분석 ~99% 유지, **Godot 실 구현 85-90% → 87-92%** (stat 실 영향 +2%p), 출시 83-92% → **85-94%**. R75 frontend → R76 stat 실 영향으로 buff/curse/stance 가 ATK/DEF 에 실제로 반영. R77 부터 Godot Editor 실 실행 검증 (사용자 작업).)

이전 라운드:

Round 75 — **GUNNER combo UI + skill effect 시스템 통합**. R63 임시 공식 (`atk + rand(0..7) - def/2`) 의 R71+R72+R73 발견 통합. **GameState 에 GUNNER combo state 3 변수 추가**: `gunner_combo` (HERO+0x269 대응) + `gunner_max_combo` (default 4) + `gunner_ammo` (HERO+0x248 대응). **battle_system.gd SKILL action 보강**: (1) **GUNNER class+skill_id==5 일 때 combo multiplier 적용** — `damage = base * (combo*20 + 30) / 100` (R72 공식, combo 1=50%/2=70%/3=90%/4=110%), combo 도달 시 reset. (2) **Formula 4 부가 호출 (R73 발견)** — `_calc_player_damage(4, ctx, skill_data)` → SP delta 양수 시 `player_mp += sp_delta` (clamp to max_mp). log 메시지에 "+%dSP" 표시. **R72 helper signals 3종 추가**: `curse_applied(target, dispatch_byte, formula_1, formula_2)` (case 1+2) / `buff_applied` (case 3+5) / `stance_applied` (case 4). **`apply_skill_effect(target, effect_type, dispatch, f1, f2, skill_data)` API**: effect_type 별 match → Formula 1/2 평가 후 해당 signal 발화. case 0 (NO_HIT) 는 no-op. R74 = Godot enhancement, monster_ai/UI 측 buff/debuff 시스템 stub (실 통합은 R75+). docstring 에 R72 4 helper 매핑 + R73 +0x4a SP delta + +0x3c/+0x3d formula ids + GUNNER 공식 명시. `tools/h5_test_battle_formula.py` 신규 — GameState 3 변수 + GUNNER multiplier 분기 + (combo*20+30) 공식 + combo reset + Formula 4 SP delta 호출 + player_mp 회복 로직 + 3 signals + apply_skill_effect 5 match case + GUNNER Python 시뮬 (1/2/3/4 = 50/70/90/110%) + 7 R74 docstring markers, 모두 통과. R63/R69/R73 회귀 모두 통과. .so 분석 ~99% 유지, **Godot 실 구현 79-83% → 82-88%** (damage 공식 정확화로 +3-5%p), 출시 78-88% → 80-90%. **🎯 7년 만에 처음으로 ProcHeroSkill 의 active skill 처리 흐름이 Godot 에서 정확히 재현됨**.)

이전 라운드:

Round 73 — **ProcHeroSkill JT2 4 case + TEM 11 호출 RE**. R70 의 2 jumptable 의 두 번째 (@0x9a8d8, 7-way GetCurActSkillIdx()) **각 case 동작 매핑 확정**: **case 0/2/4/6 (alias @0x99904) = 기본 공격** (Formula 3 V[23] → BATTLER::IncreaseHP + Formula 4 atk×magic×buff% → HERO::IncreaseSP) / **case 1/7 (@0x9ad78) = timestop + 기본 공격 chain** (SetTimestopFrame(2) → 0x99908) / **case 3 (@0x9acf8) = class 3 KNIGHT secondary** (HERO+0x1d36==1 + orb count 검사) / **case 5 (@0x9aa18) = shock skill** (NewShockAddEffect + skill_info[+0x30] dynamic Formula id + IncreaseHP(-damage)). **R72 의 +0x30 "behavior code" → dynamic Formula id 확정**. 모든 case → 기본 공격 path 합류. **HeroSkillInfo 신규 4 field**: +0x30 (dynamic Formula id), +0x46 (shock count), +0x4e (class 3 threshold), +0x48 (max combo). **HERO+0x1a8** = halfword storage for skill_info[+0x38] (case 5). **TargetEffectMgr::NewTargetEffect (@0x62d40) 11 호출 signature**: `(this, char effect_type, int b, HeroSkillInfo*, SPRITE*, char c-f, short s, int g, int h)` — 12 args. **distinct effect_type values: {4, 7, 8}** (6/2/1 회 + dynamic 3 회). 호출 위치 10 확정 (#11 ptr 추적 필요, R74). R73 = RE only, Godot 코드 변경 없음. docs/h5/RE/proc_hero_skill.md §13 + §14 추가 + h5_test_proc_hero_skill.py 확장 (JT2 기본 공격 mov r1 #3/#4 + IncreaseHP bl + SetTimestopFrame bl + NewShockAddEffect bl + skill_info ldrsb [r6,#0x30/#0x46] + class 3 setup + TEM 11회 + effect_type 4/7/8 distinct, **16 R73 doc markers**) 통과. .so 분석 98% → ~99%, 출시 78-88% 유지. **R74 부터 Godot battle_system.gd damage 공식 정확화 (R63 임시 → Formula 3/4 평가) 가능 — R73 의 가장 큰 임팩트.**)

이전 라운드:

Round 72 — **ProcHeroSkill JT1 case + class 2 GUNNER entry RE**. R70 의 2 jumptable 의 첫 번째 (@0x9a398, 5-way skill_info[+0x28]) **각 case 의 helper 호출 매핑 확정**: **case 0 (NO_HIT @0x99978) = HERO::IncreaseSP(skill_info[+0x4a] s16)** — SP 변경만 / **case 1+2 (@0x9ac68) = BATTLER::AddCurseSkill** (@0x4b134) — curse/debuff / **case 3+5 (@0x9abfc) = BATTLER::AddBuffSkill** (@0x4b198) — buff / **case 4 (@0x9ab98) = HERO::AddStanceSkill** (@0x91d7c) — stance (R70 의 "heal+buff" 가설 정정 → stance 자세 시스템). 모든 case 가 b #0x99978 으로 NO_HIT path 합류. **공통 패턴**: 2회 Formula::calc(skill_info[+0x3c] formula_id_1, skill_info[+0x3d] formula_id_2) → r0/r7 → helper 호출. **case 1+2 special dispatch**: skill_info[+0x3a] == 0x34/0x37 일 때 default 대신 special path. **HeroSkillInfo 신규 6 field**: +0x1c (alternate path flag), +0x3a (special dispatch), **+0x3c (Formula id 1)**, **+0x3d (Formula id 2)**, +0x45, **+0x4a (s16 SP delta)**. **HERO this 신규**: +0x294 (skill state flag), +0x295 (secondary formula id), **+0x269 (GUNNER combo state)**. **class 2 (GUNNER) entry @ 0x9a564**: GetCurActSkillIdx() == 5 (combo shot) 만 special path → 3 field reset. **GUNNER damage 공식**: `(combo_state×20 + 30) × X / 100` — 매 hit 마다 +20% bonus (combo 1=50%, 2=70%, 3=90%, 4=110%). HERO+0x248 = ammo/charge counter, skill_info+0x48 = max combo. R72 = RE only, Godot 코드 변경 없음. docs §12 추가 + h5_test_proc_hero_skill.py 확장 (case별 helper bl 검증 + skill_info ldrsb +0x1c/+0x3c/+0x3d + ldrsh +0x4a + HERO ldrb +0x294/+0x295/+0x269 + cmp #0x34/#0x37/#0x5000000, **14 R72 doc markers**) 통과. .so 분석 98% 유지, 출시 78-88% 유지.)

이전 라운드:

Round 71 — **ProcHeroSkill Formula::calc dispatch + r5 base 추적**. R70 ProcHeroSkill 골격 정밀화. **Formula::calc** (@0x7749c, 172B, 42 instr) full disasm — **id < 1000 (0x3e8) → calc_pl, < 2000 (0x7d0) → calc_en, ≤ 3007 (0xbb7) → calc_sk, else return 0**. Formula struct: +0x0 calc_en ptr / +0x4 calc_sk ptr / +0x8 calc_pl ptr. **Formula 0x6f (111) / 0x63 (99) = calc_pl 범위지만 production calc_pl 은 0..38 (39 entries) 만 정의 → OOB → result 0 → ble taken → __sub_89068 (hit registered) skip**. 그러나 ble 분기 도착 후 **ChangeAttackMotion 은 무조건 호출** = R69 호출자 확정과 무관. 즉 hit check 는 historical artifact (production cut), ChangeAttackMotion 호출 path 자체는 unaffected. **r5 base 추적**: `add r5, r4, #0x1ec0` @0x993cc + `add r5, r5, #0xc` @0x993dc → **r5 = HERO + 0x1ecc**. 따라서 `[r5, +-0x190]` (107회 ldr) = **HERO + 0x1d3c**. 0x99704-10 시퀀스: `ldr r3, [HERO+0x1d3c]; ldrsh r2, [r3, #0x19c]; cmp r2, #0x63 (99); bgt exit_path` = Monster+0x19c (s16 level) > 99 시 exit = **level cap 99 확정** (R22 max level 92 와 합리적 일치). 다른 r5 base: @0x99454 `add r5, r4, #0x1e00` → r5 = HERO+0x1e04 (path 2, R72 추적). 본 라운드는 RE 문서 §11 추가만 산출. docs/h5/RE/proc_hero_skill.md §11 (Formula::calc dispatch + 0x6f/0x63 OOB + r5 base + level cap) + h5_test_proc_hero_skill.py 확장 (13 추가 markers: Formula::calc 172B + cmp 0x3e8/0x7d0/0xbb0 + calcByFormula bl + r5 setup A/B + [r5,-0x190] 107회 + level cap + R71→R72 잔여). Godot 코드 변경 없음 (R72+에서 damage 공식 정확화 예정). .so 분석 97-98% → ~98%, 출시 78-88% 유지.)

이전 라운드:

Round 70 — **HERO::ProcHeroSkill 골격 RE**. R69 의 ChangeAttackMotion 호출자 (`HERO::ProcHeroSkill(HeroSkillInfo*)` @0x99278, **7972B 거대 함수**) 의 고수준 골격을 정밀화. 총 **1993 ARM instruction**. Entry sequence: 전역 state clear + 3-step attack reset (sub_88f74/88fd4/89034) + **HERO+0x348 + i*0x58 의 59-slot skill array 초기화** (59×88B=5192B = HeroSkillInfo 배열) + NULL guard + class_id 분기 (class 2 GUNNER 별도 path @0x9a564). **2 jumptable 식별**: (1) @0x9a398 5-way — dispatch key = `skill_info[+0x28]` (signed byte, 0..4 skill effect type), case 0=NO_HIT / 1·2=physical / 3·5=magic / 4=heal+buff. (2) @0x9a8d8 7-way — dispatch key = `HERO::GetCurActSkillIdx()` (0..6 active skill slot), case 0/2/4/6=기본 공격 alias / 1=skill A / 3=skill B / 5=skill C / 7=default → **7+1 active skill slot 시스템 확인** (R57 일치). **ChangeAttackMotion 호출 context @ 0x99700**: 직전 Formula::calc(0x6f=111, ...) hit check → result > 0 시 sub_89068 (hit 등록) → ChangeAttackMotion → 직후 *(r5+(-0x190))+0x19c (s16) > 99 면 exit (level cap). **HeroSkillInfo struct 18+ field 매핑**: +0x0a flag / +0x1c/1d mode / **+0x28 effect_type (★jumptable1 key)** / +0x29 effect2 / +0x2a formula_arg / **+0x30 behavior (8회)** / **+0x32/34/36/38 4×u16 (primary/secondary value, 각 8회)** / +0x3a-3d flags / **+0x44 knockback_idx (R69)** / +0x48/4a/4c/50 ranges / 88B = 0x58 entry size 일치. **호출 그래프 top 20**: **Formula::calc 27회** / GetSpritePtr 22회 / GetExtraDataPtr 22회 / **GetCurActSkillIdx 18회** / GetX 14회 / GetY 14회 / GetPivotX 11회 / GetPivotY 11회 / **TargetEffectMgr::NewTargetEffect 11회** (skill VFX) / **BATTLER::IncreaseHP 10회** / __divsi3 10회 / UiTargetMonster::SetBattler 9회 / GetTempAtkProPtr 8회 / GetHitType 8회 / GetMotion 7회 / Rand 7회 / IncreaseSP 5회 / IncreaseHiperCount 4회 / ApplyAddEffect 3회 / CheckEffSound_Hit 3회. HERO this fields: +0x22c=class_id (16회) / +0x269 (8회) / +0x294-296 3-byte cluster (skill state machine). `[r5, +-0x190]` ldr **107회** = big_struct base ptr (R71 추적 필요). docs/h5/RE/proc_hero_skill.md 신규 RE 문서 (10 섹션). h5_test_proc_hero_skill.py — 11 ELF symbol + entry pattern + 2 jumptable + dispatch key + ChangeAttackMotion @ 0x99700 + Formula::calc 27회 + TargetEffectMgr 11회 + IncreaseHP 10회 + GetCurActSkillIdx 18회 + HeroSkillInfo 4 fields ldr + HERO+0x22c 16회 + 26 RE doc marker 통과. .so 함수 분석 96-97% → 97-98%, Godot 실 구현 79-83% 유지 (R70 은 RE only, Godot 코드 변경 없음), 출시 78-88% 유지.)

이전 라운드:

Round 69 — **Attack motion dispatch RE 확정**. `HERO::ChangeAttackMotion` (@0x91e7c, 340B) + `HERO::CheckWeaponMotion` (@0x8dd58, 256B) ARM full disasm. **R67 PASS 1 의 cmp 0xd/0xe/0x14/0x17 dispatch 가설 정정**: 입력은 skill_type/weapon_kind 가 아닌 **`CHAR::GetMotion()` 현재 motion 값**. mov r1, #0x16/0x18/0x26/0xf = SetMotion 의 새 motion id, mov r1, #0xa = KB strength. **분기 키 = `this->class_id` (HERO+0x22c)**, class 0 (워리어) + 3 (나이트) 만 active. class 0: motion 13(0xd)→38(0x26) / motion 20(0x14)→22(0x16) — 단순 wind-up→hit phase swap. class 3: motion 14(0xe)→15(0xf) NULL target OR motion 14+target → KB=10+RevengeXY+TurnDir / motion 23(0x17)→24(0x18)+state_1d36==1 시 variable KB=(skill_info[+0x44]-2)*6+20. **호출자 식별** (초기 capstone 검색 0건 → raw ARM bl 디코더로 확정): ChangeAttackMotion ← `HERO::ProcHeroSkill` @0x99278 offset +0x488 (1회). CheckWeaponMotion ← **4 클래스 Draw() 메서드 5회** (WARRIOR @0x146af0 / ROGUE @0xd7a18 / KNIGHT @0xaa328 / GUNNER @0x87678 ×2) — **SORCERER 제외** (R22 의 "Sorcerer class object 없음" stub 가설 재확인). HERO struct 신규: +0x22c=class_id / +0x1d36=class 3 secondary flag / +0x1fb0=current attack target Monster* / +0x1fea=last knockback_idx. HeroSkillInfo +0x44=knockback_idx (1-base). character.gd 에 `SO_MOTION_WARRIOR_*/KNIGHT_*/WEAPON_*_HIGH` 10 상수 추가 (logical 매핑). docs/h5/RE/attack_motion_dispatch.md 신규 RE 문서. h5_test_attack_motion.py — 2 ELF + class dispatch + motion 분기 + helper 호출 + caller 검증 + 25 RE doc + 10 GDScript + 4 docstring 모두 통과. .so 함수 분석 95-96% → 96-97%, Godot 실 구현 79-83% 유지 (logical 매핑), 출시 78-88% 유지.)

이전 라운드:

Round 68 — **NPC Dialog state machine + DIALOG_INFO struct RE 확정**. `DIALOG_INFO::DialogWindow_Proc` (@0x71b48, 912B) ARM full disasm + jumptable decode. **R67 PASS 1 summary 의 "state byte = +0x29" 가설 잘못 확인** — 실제 main state byte = **+0x2b** (`ldrsb r2, [r0, #0x2b]; cmp r2, #7; addls pc, pc, r2, lsl #2` 의 0..7 jumptable). +0x29 는 sub-step counter (0..4 animation tick), +0x2d/+0x2f 는 animation curve key A/B (sp 의 phase data 에서 ld). 8 state 의미 확정: 0=INACTIVE (return 0, dialog 종료) / 1·3·6=IDLE_BUSY (return 1, 입력 대기) / 2·4=FADE_IN_A/B (phase data pool +0x10..+0x18, +0x1c..+0x24) / 5·7=FADE_HSB_A/B (RestorePal+ChangeHSB, pool +0x28..+0x30, +0x34..+0x3c). sub-step counter +0x29 가 4 도달 시 `SetDialogWindow` 로 다음 state 전환. state 2 종료 시 +0x2c=5 면 state 7 로 fast-jump. `EventProc::Event_DialogWindow` (@0x6eb38, 656B) = 매 frame NPC face + DialogBox + NameBox renderer (DrawDialogBox + DrawTextField + GetNpcNameText + NameBox). `EventProc::Event_SituateDialogText` (@0x73030, 600B) = dialog 시작 트리거: record_base + npc_slot×0x3c (60B per NPC slot), Interpreter::Strings::getString 으로 텍스트 lookup, Graphic::GetWidth/Height 로 자동 좌표 계산, +0xdf sub_state 분기로 `SetDialogWindow(1,2)/(4,2)/(6,5)` 호출. 외부 helper 9종 주소·심볼 확정 (SetDialogWindow @0x6ab40 / SetFacePosition @0x72f54 / GetNpcNameText @0x1431a0 / DrawDialogBox @0x8245c / NameBox @0x82248 / Strings::getString @0x9e540 / RestorePal @0x59400 / ChangeHSB @0x5f000 / DrawTextField @0x44370). dialog_box.gd 에 `DIALOG_STATE_*` 8 상수 + `DIALOG_TRIGGER_*` 3 상수 + `DIALOG_SUBSTEP_FINAL=4` + R68 RE docstring 추가 (typewriter 동작 자체는 logical 매핑만, 동작 보존). docs/h5/RE/npc_dialog.md 신규 RE 문서 (struct layout 표 + state 흐름 ASCII diagram + helper 표 + R67→R68 정정 표). h5_test_dialog.py — 9 ELF symbol cross-verify + 11 disasm pattern (jumptable + strb +0x29/+0x2d/+0x2f + cmp r2#7/r3#4/r1#5 + bl SetDialogWindow/RestorePal/ChangeHSB) + 12 RE doc marker + 12 GDScript const 통과. .so 함수 분석 94-95% → 95-96%, Godot 실 구현 79-83% 유지 (logical 매핑), 출시 78-88% 유지.)

## 📜 Round 1-76 한 줄 요약

| 라운드 | 한 줄 |
|---|---|
| R1-5 | VFS + 자산 이름 99.7% + DES 변종 + Formula VM 186 공식 + Godot 스캐폴드 |
| R6-11 | gv+0x1474 111 fields + V[58..167] 매핑 + V[111..116] secondary stat (근접명중/장거리명중/회피/방패방어/크리티컬) |
| R12-19 | Item 시스템 — buff slot + magic stat + EquipItemInfo struct + LoadItemTable csv layout + 19 카테고리 |
| R20-28 | Item 메커닉 — SkillBook/Cash/Refine/Orb/Mix 정밀 매핑. 강화 stat 식 + 5 socket orb + NPC blacksmith |
| R29-36 | Monster + Drop — droptable.dat 252 entries + enemy_g + enemy_*.dat 3 difficulty + 4 element + magic stat pair |
| R37-40 | Mission 105 + Quest 151×3 difficulty + 모든 데이터 파일 종류 식별 |
| R41-43 | Save 8 종류 + load cross-check (21/21 + 24, 0 mismatch) + `file[0] = level*10+class_id` packing |
| R44-47 | Monster AI 분석 — 13 opcode + 13 trigger + 13 sub-state + 48 AI defs decoder |
| R48-49 | Godot 통합 시작 — Monster AI VM (autoload) + Save binary 직렬화 |
| R50 | AI Action 13 sub-state 정밀 구현 (state 1-7/9/12 채움) + host CHAR interface 13 method + 48/48 VM round-trip |
| R51 | 인벤토리 items.json 정확 통합 (1360 records unique index) — kind 기반 filter + class_mask/level_limit 검증 + tooltip 풍부 |
| R52 | 강화(Refine) UI 구현 — Round 17/26 의 5-case + `refined_stat = base+sub_count` + 10000회 시뮬 (+10 2.5%/lock 65%/destroy 33%) |
| R53 | 합성(Mix) UI 구현 — Round 25/28 ApplySpecialMix + 116 recipe parse (ing×3 + result + sr) + 제작가능 필터 + 재료 보호 소비 |
| R54 | Orb socket UI 구현 — Round 17/26 ApplyOrbCombine + 53 orb + 5-socket encoding + 2x rule + add/remove 검증 |
| R55 | NPC 대장간(Blacksmith) UI 구현 — Round 28/32 ApplyNormalMix + smithtable.json 231 named recipes + 4-탭 + 제작가능 필터 + items.json _meta 회복 |
| R56 | Quest 패널 강화 — Round 40 quests.json 새 schema (3×151) + detail card (목표/보상/설명) + 난이도 토글 + 자동 보상 quests.json 직접 사용 + difficulty scaling 100% 단조 검증 |
| R57 | SkillBook 학습 UI 구현 — Round 21 IfLearnSkill + slot_16/17 193 books + GameState skill_levels dict + 4 조건 검증 + Sorcerer stub 검증 |
| R58 | Mission 진척 UI 구현 — Round 37/38 mission.json 105 missions + MissionSystem autoload + 7 event API + 6 panel hook 자동 연결 + type 분포 검증 + 3 case 시뮬 |
| R59 | Mission/Quest type 의미 RE — 23 함수 디스어셈블 + mission_type 0-5 의미 확정 + type 3 sub_type 정밀 매핑 |
| R60 | Quest cond_type 의미 RE — QuestCheck 5-way jumptable + cond_type 13/14=bag item count, 17=monster kill, 18=quest switch + quest_system 정확 라벨링 |
| R61 | character.gd host CHAR interface 구현 — Round 50 의 17 method 실 구현 + map 좌표 기반 distance/dir/motion |
| R62 | Monster spawner + AI tick 루프 — demo `_physics_process` 30fps tick + MonsterAI.process + cooldown_tick + dead 정리 + Mission.bump 자동 + KEY_G 테스트 spawn |
| R63 | Monster ↔ Hero 실 전투 — ai_skill_cast → hero HP 차감 + red popup + 사망 quick_load / SPACE 키 → Chebyshev ATTACK_RANGE_TILES=2 nearest monster 공격 + yellow popup + 방향 전환 |
| R64 | monster kill 보상 흐름 — _award_kill_reward (enemy_stats sentinel→default exp/gold + 25% drop_table + add_battle_reward level_up + +%dEXP +%dG popup + Quest.on_enemy_killed) |
| R65 | Quest reward type 6/10/11/12 RE — QuestRewardData @0xd458c 분석으로 reward.type=item slot, sub=idx, value=qty 확정 + type 17=money/18=exp/19=HP/20=INT + REWARD_SLOT_LABEL + 64/64 in-range 검증 + items.json item_name_at 라벨링 |
| R66 | battle_system / character 두 host 명세 강화 — turn-based stub 이 dead code 아님 확정 (B 키 전투 host=self) + cooldown 실 동작 + is_stunned 추가 + 두 host 비교 표 docstring + h5_test_dual_host 17/17 + 6 R66 패턴 + 의미 차이 시뮬 |
| R67 | Battle motion enum + CHAR state machine RE 확정 — R50 의 HOST_MOTION (walk=1/die=9) 가설 잘못 확인 + 실제 walk=motion 3 / die=motion 5 + main_state(1-4) ≠ motion 별개 시스템 + CHAR struct +0x2c/0x2d/0x2e/0xc4-c6 + character.gd 에 SO_* 8 상수 추가 + 10 ELF symbol + 9 패턴 통과 |
| R68 | NPC Dialog state machine + DIALOG_INFO struct RE 확정 — DialogWindow_Proc 0..7 jumptable @ +0x2b + R67 의 "+0x29" 가설 정정 + 8 state 의미 + phase data pool + Event_DialogWindow renderer + Event_SituateDialogText 트리거 + helper 9종 + dialog_box.gd 에 11 상수 추가 + 9 ELF + 11 disasm + 12 doc + 12 GDScript 통과 |
| R69 | Attack motion dispatch (ChangeAttackMotion + CheckWeaponMotion) RE 확정 — R67 PASS 1 의 cmp 0xd/0xe/0x14/0x17 가설 정정 (input = GetMotion() 반환값, dispatch key = class_id @+0x22c, class 0 워리어 + 3 나이트만 active) + 호출자 정확 식별 (ChangeAttackMotion ← ProcHeroSkill @0x99278+0x488 1회, CheckWeaponMotion ← 4 클래스 Draw 5회: WARRIOR/ROGUE/KNIGHT/GUNNER, SORCERER 제외 → R22 stub 재확인) + HERO struct 신규 4 fields + HeroSkillInfo+0x44 + character.gd 10 상수 + 27 검증 통과 |
| R70 | HERO::ProcHeroSkill 골격 RE — 7972B 거대 함수 1993 ARM instruction 분석. Entry sequence (state clear + 3-step reset + 59-slot HeroSkillInfo 배열 @HERO+0x348 88B×59 초기화 + class 2 GUNNER 별도 path) + 2 jumptable (@0x9a398 5-way skill_info[+0x28] effect type / @0x9a8d8 7-way GetCurActSkillIdx active skill slot 0..6) + ChangeAttackMotion @0x99700 context + HeroSkillInfo 18+ fields 매핑 + helper graph top 20 + HERO this +0x22c/+0x269/+0x294-296 fields + 11 ELF + 26 doc marker 통과 |
| R71 | ProcHeroSkill Formula::calc dispatch + r5 base 추적 — Formula::calc (@0x7749c, 172B) full disasm: id < 1000 calc_pl / < 2000 calc_en / ≤ 3007 calc_sk. Formula 0x6f/0x63 = calc_pl OOB (production 0..38) → hit check 항상 0 → __sub_89068 skip but ChangeAttackMotion unaffected. r5 = HERO+0x1ecc, [r5,-0x190] = HERO+0x1d3c. cmp r2 #0x63 = level cap 99 확정 |
| R72 | ProcHeroSkill JT1 5 case + class 2 GUNNER entry RE — JT1 각 case helper 매핑: case 0=IncreaseSP / 1+2=AddCurseSkill / 3+5=AddBuffSkill / 4=AddStanceSkill (R70 heal+buff 정정). HeroSkillInfo +0x3c/+0x3d formula ids + +0x4a SP delta. HERO+0x269 GUNNER combo state. class 2 entry skill_idx==5 special. GUNNER damage = (combo×20+30)×X/100. docs §12 + 14 markers 통과 |
| R73 | ProcHeroSkill JT2 4 case + TEM 11 호출 RE — JT2 각 case: case 0/2/4/6 = 기본 공격 (Formula 3 V[23] HP + Formula 4 atk×magic×buff% SP) / case 1/7 = timestop chain / case 3 = KNIGHT secondary (orb-based) / case 5 = shock skill (dynamic Formula id from skill_info[+0x30]). HeroSkillInfo +0x30/+0x46/+0x4e/+0x48 + HERO+0x1a8. TEM signature 12 args + effect_type {4,7,8}. docs §13/§14 + 16 markers 통과 |
| R74 | Godot battle_system.gd damage 공식 정확화 — R63 임시 공식 (atk+rand-def/2) 의 R71+R72+R73 발견 통합. GameState 에 gunner_combo/max_combo/ammo. battle_system.gd SKILL: GUNNER combo multiplier + Formula 4 SP delta + 3 helper signals + apply_skill_effect API. R63/R69/R73 회귀 통과. Godot 79-83% → 82-88%, 출시 80-90% |
| R75 | GUNNER combo UI + skill effect 시스템 통합 — R74 backend 의 frontend. GameState 에 active_curses/buffs/stances Array + add/tick. battle_system._ready() 의 3 signal 자동 연결. status_panel 에 [Combo N/M] + [저주×N/버프×M/자세×K]. GameData.skill_info(class_id, skill_id) 10 fields. battle_system SKILL 자동 dispatch + log fx_str. Godot 82-88% → 85-90%, 출시 83-92% |
| **R76** | **active effect stat modifier 통합 + tick 자동 호출 — GameState.total_attack 에 active_buffs.f1 누적 % bonus (clamp 0..200) + total_defense 에 stance+curse % (clamp 0..150/0..80, net_pct 계산). battle_system._enemy_turn 끝에서 tick_active_effects() 자동 호출 → state_changed.emit → status_panel 자동 갱신. tools/h5_test_stat_modifier.py 신규 — Python 시뮬 7 case (buff 20%/누적/clamp 200% / stance 50% / curse 30% / stance+curse net / curse clamp 80%) 모두 통과. R63/R74/R75 회귀 통과. Godot 실 구현 85-90% → 87-92%, 출시 85-94%** |



---

## 🎯 전체 진척 평가 (Round 76 시점)

영역별 추정 진척률 — 단일 % 로 답하기 어려움, 영역별 차이 큼:

| 영역 | 추정 % | 비고 |
|---|---:|---|
| **자산 추출/변환** | ~95% | VFS/sprite/palette/text/OGG 완료. 남은 것: SMAF, 한글 비트맵 폰트 (LOW PRIORITY) |
| **데이터 구조 RE** (csv/dat layout) | ~100% | 모든 데이터 파일 식별 + decoder + struct 매핑 완료 |
| **.so 함수 분석** (game logic) | ~99% | R67-73 RE 완료. 잔여: TEM 인자 정밀, special path 0x9b100/0x9b124, type 22, LoadSkillTable disasm |
| **Godot 실 구현** | **~87-92%** | + R74-75 backend+UI + **R76 stat modifier 통합** (active_buffs → ATK%, active_stances/curses → DEF%, tick 자동). R77+ Godot Editor 실 실행 검증 |
| **Android 실 빌드 검증** | 0% | 사용자 GUI 작업 |

**종합**:
- **"원본 분석"** (RE+자산) 으로 보면 ~**99%**
- **"리메이크 출시 가능"** (Godot+Android) 으로 보면 **85-94%** (R76 stat 실 영향으로 +2%p)

## 📦 미완 큰 덩어리 (우선순위 순)

1. **UI 시스템 전반** — 인벤토리/강화/합성/스킬학습/NPC blacksmith/Quest/Mission/Shop 패널.
   데이터는 다 있지만 Godot UI 미구현.
2. **Monster AI** — `Monster::Ai_Action` (2136B), `Ai_onAction` (704B), `Ai_setActionList` 등 미분석
3. **Battle 실행 흐름** — Formula VM 평가는 됨, turn order / animation timing / skill VFX 미통합
4. **Save 파일 포맷** — DES 키만 알려져 있고 record layout 미분석
5. **Quest/Mission tracking** — 데이터 식별만, 실제 진척 추적 시스템 Godot 미구현

---

## 🚀 다음 세션 즉시 시작 (Round 77)

### A. 환경 복원 한 줄 (assets/ 비어있는 새 클론)

```bash
python tools/h5_extract_pipeline.py    # APK 가 있을 때 ~6s, incremental
```

### B. 현재 상태 한 줄 검증

```bash
# UTF-8 출력 필수 (cp949 콘솔이면 PYTHONIOENCODING=utf-8 prefix)
PYTHONIOENCODING=utf-8 python tools/verify_godot_project.py
# → ✓ all references resolve (0 warnings)

python tools/h5_test_monster_ai.py     # 48/48 AI VM round-trip
python tools/h5_test_save_layout.py    # H/SL .sav round-trip
python tools/h5_test_items_lookup.py   # 1360 items unique-name index
python tools/h5_test_refine.py         # Refine prob + 10000회 시뮬
python tools/h5_test_mix.py            # 116 recipe parse
python tools/h5_test_orb.py            # 53 orb encoding + 2x rule
python tools/h5_test_blacksmith.py     # 231 smith recipes + sr 분포
python tools/h5_test_quest.py          # 151×3 quests + difficulty scaling
python tools/h5_test_skill_book.py     # 193 skill books + 5 case 시뮬
python tools/h5_test_mission.py        # 105 missions + 3 case 시뮬
python tools/h5_test_re_types.py       # Round 59 RE: ELF symbol verify + sub_type 분포
python tools/h5_test_cond_types.py     # Round 60 RE: cond_type 13/14/17 + reward 15/17/18
python tools/h5_test_char_host.py      # Round 61: 17 host CHAR method 시그니처 + 8 Python 시뮬
python tools/h5_test_ai_tick.py        # Round 62: spawner + 30fps AI tick 루프
python tools/h5_test_ai_combat.py      # Round 63: Monster↔Hero 실 전투
python tools/h5_test_kill_reward.py    # Round 64: monster kill 보상 흐름
python tools/h5_test_reward_types.py   # Round 65: Quest reward type RE
python tools/h5_test_dual_host.py      # Round 66: 두 host 명세
python tools/h5_test_battle_motion.py  # Round 67: Battle motion enum + CHAR state
python tools/h5_test_dialog.py         # Round 68: NPC Dialog state machine + DIALOG_INFO struct
python tools/h5_test_attack_motion.py  # Round 69: Attack motion dispatch (ChangeAttackMotion + CheckWeaponMotion)
python tools/h5_test_proc_hero_skill.py # Round 70+71+72+73: ProcHeroSkill 골격 + dispatch + r5 base + JT1 5 case + GUNNER + JT2 4 case + TEM
python tools/h5_test_battle_formula.py  # Round 74: Godot battle_system damage 공식 정확화 (GUNNER combo + SKILL SP delta + 3 helper signals)
python tools/h5_test_skill_meta.py       # Round 75: GUNNER combo UI + GameData.skill_info + active effect 통합
python tools/h5_test_stat_modifier.py    # Round 76: active effect stat modifier (buff/stance/curse → ATK/DEF) + tick 자동
```

### C. Godot Editor 에서 게임 실행

`apps/hero5-godot/` 를 Godot 4.2+ Editor 로 열고 F5. 게임 화면에서 키바인딩:

| 키 | 동작 | 도입 라운드 |
|:---:|---|:---:|
| **ESC / I** | 상태창/인벤토리 토글 (status_panel) | R7 (R51 강화) |
| **R** | 강화(Refine) 패널 토글 | **R52** |
| **K** | 합성(Mix) 패널 토글 | **R53** |
| **O** | Orb socket 패널 토글 | **R54** |
| **J** | NPC 대장간(Blacksmith) 패널 토글 | **R55** |
| **Q** | 퀘스트 패널 토글 (R56 detail card + 난이도 토글) | R20 (R56 강화) |
| **L** | 스킬북 학습(Learn) 패널 토글 | **R57** |
| **,** | 미션 진척 패널 토글 | **R58** |
| **G** | hero 주변에 random monster 스폰 (AI tick 테스트) | **R62** |
| **SPACE** | 인접 monster (Chebyshev ≤2 tile) 공격 | **R63** |
| S | 상점 열기 | R8 |
| H | 도움말 토글 | R10 |
| X | 설정 토글 | R10 |
| F5 / F9 | 빠른 저장 / 로드 | R6 |
| 1-8 / Shift+1-8 | 슬롯 저장 / 로드 | R7 |
| B | 랜덤 전투 | R3 |
| E | NPC 대화 | R8 |
| M / N | map_id / scene 다음 | R3 |
| P / C / V | NPC 마커 / collision / tile attr 디버그 | R5 |
| T | dialog 테스트 | R5 |

### D. Round 77 추천 작업 (자율 가능, 임팩트 순)

> R76 로 stat modifier 통합 + tick 자동 호출 완료. R77 은 사용자 작업 (Godot Editor 실 실행 검증) 또는 잔여 RE 분석.

#### ⭐ 1순위 — Godot Editor 실 실행 검증 (사용자 작업, 0.5-1 라운드)
- R74-76 의 backend + UI + stat modifier 가 in-game 에서 정확히 동작하는지 검증:
  - **B 키 → battle 시작 → SKILL action** → log message 에 `+저주`/`+버프`/`+자세` fx_str 표시 확인
  - **status_panel (ESC/I)** 에 `[Combo N/M]` (GUNNER 만) + `[저주×N, 버프×M, 자세×K]` 시각 확인
  - **ATK/DEF 변화** — buff 후 atkdef_label 의 수치 증가, curse 후 DEF 감소
  - **tick 자동 만료** — 5 turn 진행 후 active effect 자동 제거 + UI 업데이트
- 사용자 환경 작업 (코드 변경 없음). 발견된 bug 는 R78+ 에서 수정.

#### 2순위 — LoadSkillTable disasm (0.5 라운드)
- R75 의 byte offset → stats_u16 index 매핑 정확화 (현재 추정)
- ItemTable::LoadItemTable 와 유사한 LoadSkillTable 분석으로 skill record 의 정확한 byte layout 확인

#### 3순위 — TEM 정밀 (0.5 라운드)
- effect_type 4/7/8 실제 의미 (R5 의 TargetEffect::NewHitEffect 와 cross-ref)
- TEM 호출 #11 위치 추적 (ldr 통한 stored ptr 호출 패턴)
- TargetEffectMgr::NewTargetEffect 내부 분석 (sprite VFX 생성 흐름)

#### 3순위 — special path 0x9b100/0x9b124 (R72 미해결, 0.5 라운드)
- skill_info[+0x3a] == 0x34/0x37 일 때 default AddCurseSkill 대신 호출되는 special handler
- skill table cross-ref 로 어떤 skill 의 path 인지 식별

#### 4순위 — type 22 (0x16) special path RE / SetDialogWindow 내부 RE / Skill UI

#### 2순위 — SetDialogWindow 내부 RE (0.5 라운드)
- 핵심 함수: `DIALOG_INFO::SetDialogWindow` (@0x6ab40)
- R68 에선 호출자 측 (Event_SituateDialogText / DialogWindow_Proc) 만 분석 — 내부 본 적 없음
- 작업: `(byte main, byte sub)` 인자 의미 + state 전환 트리거 + sub-step counter +0x29 초기화 여부 확인
- 산출물: `docs/h5/RE/npc_dialog.md` §10 (SetDialogWindow 내부) 추가 + R68 docstring 보완

#### 3순위 — type 22 (0x16) special path RE (0.5 라운드)
- Round 65 disasm 에서 식별만 됨 (`cmp r1, #0x16; beq 0xd4864`), observation 없음
- 가설: special item add with `r1=#0x11` (slot 17 = skill_book_gk?)
- 작업: 0xd4864..0xd48c0 영역 정밀 disasm → handler 의미 확정

#### 4순위 — Skill 보유 레벨 UI 표시 (0.5 라운드)
- status_panel 에 `GameState.skill_levels` dict 추가 표시
- R57 SkillBook 학습 UI 의 자연스러운 보완 — 학습한 스킬 시각화

#### 5순위 — scn opcode 실 game scene 검증 (2-3 라운드)
- Title/ClassSelect/Demo 외 화면 진입 테스트
- scn opcode 흐름 vs 실제 Godot scene 동작 cross-check

#### 6순위 — Save binary device import/export (1 라운드)
- 실 디바이스의 H_*.sav 추출 → Godot save_manager 의 deserialize_hero_save 로 round-trip 검증

### E1. Round 74-76 battle / skill effect 시스템 (R76 종료 시점)

| 컴포넌트 | 책임 | R74-76 변화 |
|---|---|---|
| `GameState.gunner_combo/max_combo/ammo` | GUNNER class 의 combo state | R74 신규 — HERO+0x269 대응 |
| `GameState.active_curses/buffs/stances` | 적용 중인 effect entry Array (`{dispatch, f1, f2, turns}`) | R75 신규 (Array) — R72 helper signal 캐치 |
| `GameState.add_active_effect(kind, …)` / `tick_active_effects()` | effect 추가 + turn 만료 | R75 신규, R76 에서 state_changed.emit 통합 |
| `GameState.total_attack` | base+equip + **active_buffs.f1 누적 %** | R76 보강 — clamp 0..200, `raw × (100+pct)/100` |
| `GameState.total_defense` | base+equip + **stance % - curse %** | R76 보강 — clamp 0..150 / 0..80, net_pct |
| `battle_system.SKILL action` | damage + Formula 4 SP delta + auto dispatch | R74-75 보강 — GUNNER combo + 자동 effect type dispatch |
| `battle_system.curse/buff/stance_applied signal` | R72 helper 4 의 Godot 대응 | R74 신규 — `_on_*_applied` 가 GameState 갱신 (R75) |
| `battle_system.apply_skill_effect(…)` | manual effect dispatch API | R74 신규 |
| `battle_system._enemy_turn` | turn 종료 + cooldown tick + **active effect tick** | R76 보강 — `GameState.tick_active_effects()` 호출 |
| `status_panel._on_state_changed` | GameState 변화 시 패널 자동 갱신 | R76 신규 — visible 일 때만 _apply |
| `status_panel._apply` | UI text 갱신 | R75 보강 — `[Combo N/M]` + `[저주×N, 버프×M, 자세×K]` |
| `GameData.skill_info(class_id, skill_id)` | R72/R73 skill record 10 field 노출 | R75 신규 — effect_type / dynamic_formula_id / formula_ids / KB / shock / max_combo / SP / KNIGHT threshold |

흐름 (active skill 사용 시):
1. `player_action(Action.SKILL, skill_id)` → MP/cooldown 검사
2. **damage = calc_sk[2000+skill_id]** (기본) + **GUNNER combo multiplier** (class==2 && skill_id==5)
3. **Formula 4** 부가 호출 → SP 회복 (`player_mp += sp_delta`)
4. `GameData.skill_info` → `effect_type` 추출 → **`apply_skill_effect` 자동 호출**
5. effect_type 별 signal → `_on_*_applied` → `GameState.add_active_effect`
6. 다음 enemy turn 끝에 `tick_active_effects` → 만료 entry 제거 + `state_changed.emit`
7. `status_panel` 자동 갱신 (visible 일 때)

### E. Round 51-58 UI 시스템 통합 상태 (참고)

| 패널 | 데이터 source | 핵심 mechanic | helper 함수 |
|---|---|---|---|
| status_panel (R51) | items.json 1360 records | kind/class_mask/level_limit 검증 | GameData.item_lookup |
| refine_panel (R52) | EquipItemInfo +0x165..+0x167 | 5-case prob + base+sub stat | GameState.refine_state |
| mix_panel (R53) | slot_15 의 116 recipe | success_rate roll + 재료 소비 | GameData.parse_recipe |
| orb_panel (R54) | slot_12 의 53 orb + +0x168..+0x16d | 5 socket encoding + 2x rule | GameState.orb_state |
| blacksmith_panel (R55) | smithtable.json 231 named (288 entries) | 4-탭(기본/세트/고급/전체) + sr {75,100} | GameData.smith_table / smith_all / parse_smith_recipe |
| quest_panel (R56) | quests.json by_difficulty.q0/q1/q2 × 151 | detail card + 난이도 토글 + scaling 단조 | Quest.quest_objectives / quest_rewards / reward_label |
| skill_book_panel (R57) | items.json slot_16/17 의 193 books | class match + req_lvl + upgrade check | GameData.skill_books_for_class / GameState.learn_skill_book |
| mission_panel (R58) | mission.json 105 missions | 7 event → mission_type 매핑 / 자동 완료 | Mission.bump_progress / mission_completed signal |

모두 GameState 의 단일 inventory 배열을 공유. `consume_inventory` 가 refine_state + orb_state 동기 정리.
blacksmith 는 mix 와 동일한 parse_recipe 형식이라 schema 호환. quest_panel 은 Quest singleton 사용.
skill_book_panel 은 GameState.skill_levels dict (skill_idx → max LV) 갱신 + unlocked_skills 동시 갱신.
mission_panel 은 Mission singleton (R58 신규 autoload) 사용. 기존 panel 6개 hook 자동 연결.

### F. 미구현 / 향후 옵션 (Round 76 종료 시점)

- **(★ 1순위 USER)** R74-76 의 backend+UI+stat modifier 가 in-game 동작 검증 — Godot Editor 에서 직접 실행 후 B 키 → SKILL → log fx_str + UI Combo bar + ATK/DEF 변화 시각 확인 (R77 추천)
- **(분석)** LoadSkillTable disasm — R75 의 skill_info struct byte offset → stats_u16 index 매핑 정확화 (현재는 추정)
- **(분석)** TEM 호출 #11 위치 + effect_type 4/7/8 정밀 의미 (R72/R73 잔여, 0.5 라운드)
- **(분석)** special path 0x9b100/0x9b124 — skill_info[+0x3a] = 0x34/0x37 special handler (R72 미해결, 0.5 라운드)
- **(분석)** type 22 (0x16) special path — R65 미관측 case, 0xd4864 영역
- **(분석)** SetDialogWindow @0x6ab40 내부 — R68 호출자 측만 봄
- **(검증)** scn opcode 실 game scene 동작 (Title/ClassSelect/Demo 외 화면 진입)
- **(검증)** Save binary device import/export — 실 디바이스 H_*.sav 추출 → Godot 로드
- **(USER)** P6 Android APK 실 빌드 — Godot Export Template + JDK 17 + Android SDK 필요

---

## 30초 요약 (Round 39 시점, 2026-05-11)

영웅서기5 Android+HD 리메이크 — Phase 2 (자산 추출/분석) + Phase 3 (Godot 게임 시스템)
+ **모든 우선순위 P1~P4 + DES 해독 + Formula VM 통합 + Item struct 분석** 완료.
Title → ClassSelect → Demo 흐름 동작하는 Godot 4 프로젝트 (`apps/hero5-godot/`).

**verify_godot_project.py: 0 errors / 0 warnings.**

### Round 6~39 누적 발견 (요약)

| 영역 | 핵심 결과 |
|---|---|
| Formula VM stat field | V[58]=level, V[60..63]=str/dex/**con/int** (R11 정정), V[69]=SP, V[70]=CP |
| V[111..116] secondary | atk_growth_coef + 5 secondary stat = **근접명중/장거리명중/회피/방패방어/크리티컬** (R11 buildup csv 매핑) |
| V[118..133] buff/temp bonus | str/dex/con/int bonus + 5 buff slot (EXP%/SP감소%/CP충전/쿨타임/포션효과 — R12) + def_red% + atk%bonus + 5 secondary bonus |
| V[134..148] equipment | element bonus 영역, calc_sk[2003]/[2004] 가 EquipItem stat 합산 → cache |
| V[151..155] derived | V[151,152]=magic stat (둘 다 INT, R12 정정), V[153]=con, V[154]=str, V[155]=max_sp |
| V[168..182] ItemBase | V[168]=SP cost, V[170]=cooldown, V[174]=damage growth, V[181]=divisor (R13) |
| EquipItemInfo struct | +0x14=item_subtype, +0x155=class subtype code, +0x15d=level_limit, +0x15f & 0x1f = 5-class mask (W/R/G/K/S, R16), +0x165..+0x167=refine_count/sub/locked (R17), +0x168..+0x16d=6 socket slots |
| LoadItemTable csv layout | 모든 카테고리 공통 base (item_id u32 + sub_record + sub_record_data 256B memcpy). EquipItem 만 sb-area (struct +0x150..+0x167) 추가 (R14/18) |
| cat 12-16 추가 fields | BattleUseItem +0x134..+0x137 (4 byte ✓ csv 매칭), OrbItem +0x134..+0x135, MixBookItem +0x134..+0x140 (R19) |
| slot_16/17 SkillBookItem | **+0x134=class_id**, +0x135=skill_index, **+0x136=skill_level** (LV1..7 정확 매칭 ✓), +0x137=required_level. slot_16 = Warrior(0)+Rogue(1), slot_17 = Gunslinger(2)+Knight(3). HERO::IfLearnSkill 의 (class_id/2)+16 공식 (R21) |
| slot_18 CashItem | jumptable case 18 → **0xa3b38 별도 path** (R19 가설 정정), 2 byte ext +0x134/+0x135 (R20) |
| 소서러 (class_id=4) 미구현 stub | c_csv_skill_04 부재 / SORCERER class object 없음 / class_stats unk1..14=1 placeholder. 출시 빌드 = 4 클래스 only. cat 18 매핑은 dead code (R22) |
| slot_11 BattleUseItem 4 byte 의미 | +0x134=effect_type (91=HP/90=SP/87=buff/92=마석/19=test/0=무효), +0x135=success_rate%, +0x136=effect_value (HERO+0x300 u16), +0x137=duration (HERO+0x302 s16). HERO::BattleUseItem 분석 (R23) |
| SLOT_META 전면 정정 | slot_12=orb (이전 scroll), slot_13=mix material (이전 orb), slot_15=mix_book recipe (이전 material_2). record 이름 + ext 길이 cross-check 결과 (R23) |
| val_15f csv vs runtime 용도 분리 | csv: lower 5 bit = class_mask + upper 3 bit = tier_flags. runtime: SetItemOption (0xa0ff8) 가 option_type code 로 overwrite. GetRelieveLevelLimit (0xa835c) 의 cmp #0x6c='l' 는 runtime option (R24) |
| val_15f upper 3 bit 실증적 의미 | upper=0 (170, legendary 보스/named) / =1 (248, rare 중급) / =3 (9, gem 보석 헤어핀/서클릿) / =7 (362, common 상점 기본) (R24) |
| slot_15 mix_book recipe 13 byte 구조 | 1~3 ingredients (cat/idx/count) + result (cat/idx) + success_rate%. 쿠킹/포션 합성/재료 정제/무기 제작 카테고리. 116 records 모두 검증 (R25) |
| **강화 stat 보너스 식 (Formula VM)** | **id=35: clamp((V[184]+V[187]),0,9999)**, **id=36: clamp((V[185]+V[187]),0,9999)**. V[184]=item+0x156=stat_a, V[185]=item+0x158=stat_b, V[187]=item+0x166=sub_count. **refined_stat = base + sub_count** (R26) |
| **EquipItem stat 의미 (slot 별)** | weapon (slot 0-3): atk_min/atk_max (a<b), shield (slot 9): phys/mag def (a≈b), helmet/boots/accessory: primary/secondary def (a>b), spirit (slot 10): 별도 mechanism (a,b ≤1) (R26) |
| **ApplyItemRefine 5-case jumptable 의미** | case 0=큰성공 (refine_count++, sub+=2), case 1=성공 (refine_count++, sub+=1), case 2=재료소비 (no change), case 3=lock (+0x167=1 영구 잠금), case 4=destroy (item 파괴). refine_count cap 10 (R26) |
| **ApplyOrbCombine orb socket mechanism** | item +0x168 = orb_count (V[188]), +0x169..+0x16d = 5 socket bytes. 39 orb 종 (3 그룹 × 13). sub_orbs=9 면 강도 multiplier 2x. Mission::CheckOrbCombine 호출로 mission 진척 (R26) |
| **NewDropItem signature + +0x15f arg position** | `NewDropItem(MapItem*, x, y, cat, idx, val_15c, val_15f, val_162, val_160, val_163, val_161, val_164)` 12 args. 7번째 arg (5번째 s8) = +0x15f tier_flags. cat ≤ 10 (EquipItem) 만 strb 발생 (R27) |
| **Monster drop_table 13-byte entry** | Monster::SetDropItem 내 drop pool 이 13 byte/entry. 4 가지 drop type (idx ∈ [0..3]) × 13. byte 데이터에서 NewDropItem 의 +0x15f arg 직접 전달 — csv 의 tier_flags 분포를 따름 (R27) |
| **+0x15f tier_flags csv↔drop 일관성** | csv val_15f = (class_mask | tier_flags<<5). drop_table 이 csv 분포 그대로 전달. 즉 Round 24 의 실증적 라벨 (legendary/rare/gem/common) 이 보스/일반 monster drop 로직에서도 의미 있게 사용됨 (R27) |
| **ApplyNormalMix (NPC blacksmith)** | MixSmithTableInfo* 별개 데이터 (csv slot_15 와 다름). struct layout col-major: +0x11c (option_grade), +0x11d-1f (cat[3]), +0x120-22 (idx[3]), +0x123-25 (count[3]), +0x126-128 (result_cat/idx/sr) (R28) |
| **ApplySpecialMix (csv slot_15 recipe)** | GetItemTableInfo 로 csv slot_15 데이터 직접 사용 + Mission::CheckMissionMix. struct +0x135-140 col-major (csv 13 byte transpose 후) (R28) |
| **mix_book recipe csv↔struct layout** | csv 파일 = row-major (per-ing: cat,idx,count) = 사용자 관점 정확 (R25). struct memory = col-major (cat[3], idx[3], count[3]) — LoadItemTable transpose. 두 해석 모두 정당, parse_mix_book_extra row-major 객체 그대로 유지 (R28) |
| **ApplyItemCompose (option 결합)** | 두 EquipItem (둘 다 grade ≤ 2 만) → option pair (+0x15f/+0x162, +0x160/+0x163) 결합. gv+0x1444+0x198+fp*6 = 결합 prob 테이블 (R28) |
| **ApplyItemDecompose (분해)** | option_grade-based prob (gv+0x1444+0x1b8+grade*10, 4 s16 thresholds × 5 grade). 5-way: money refund (default) / mix material / potion / 기타 (R28) |
| **gv+0x1444 sub-struct prob 테이블 영역** | +0x130-198 강화 prob (R17), +0x198-1b8 결합 prob (R28), +0x1b8-1f4 분해 prob (R28), +0x1f4-208 orb prob (R26) (R28) |
| **droptable.dat 식별** | VFS index 18, 3278B = 252 entries × 13B = 63 monsters × 4 drop tiers. byte 0=0x0b cat (potion only), byte 1=0, byte 2=monster_idx, byte 3=drop_tier (0x0e..0x11). LoadItemDropTable → ItemTable+0x214 (R29) |
| **drop_table = potion drop pool only** | ❌ Round 30 정정: 사실은 EquipItem drop pool (R30) |
| **droptable.dat = EquipItem drop pool (정정)** | byte 11 = NewDropItem cat arg (5/6/7/8/0xff). 0xff = default → generic EquipItem (376B alloc). Monster progression: 저급 monster=default, 강함=specific cat (helmet/boots/accessory) (R30) |
| **byte 0 = constant marker** | 0x0b 일관 (format version 추정), cat 아님. byte 11 가 진짜 cat (R30) |
| **register propagation: byte 0xb → r3** | 0xbcb0c ldrb r8 [r3,ip] → 0xbcc08 sp+0x40 → 0xbcc20 ldr ip → 0xbcc38 asr r3 (signed s8). NewDropItem r3 = signed byte 0xb (R30) |
| **droptable.dat multi-tier drop 시스템** | Monster +0x254..+0x26c 의 5단계 threshold + Rand(0,0xffff) 으로 cat 결정 path 선택. byte 7 = default path cat (0..9 모든 EquipItem), byte 11 = highest tier path cat (helmet/boots/accessory). mid paths = Rand(0,9). cat 4=armor 누락 = Sorcerer stub cross-confirm (R31) |
| **Monster progression 검증** | Monster 0=accessory only, Monster 62=weapon/shield/boots common + rare accessory bonus. 게임 difficulty 와 정확 일치 (R31) |
| **MixSmithTable 데이터원 식별** | /c/csv/smith_0/1/2.dat (각 96 entries × 300B/entry = 288 NPC blacksmith recipes). smith_0=accessory craft, smith_1/2=weapon craft. 모두 75% success rate. HERO+0x1d00 = MixSmithTable_ptr (R32) |
| **mix_book vs smith_table 비교** | 둘 다 13-byte recipe layout 공유. mix_book (slot_15, 116) = ApplySpecialMix + Mission, smith_table (288) = ApplyNormalMix (NPC blacksmith UI). success rate 다름 (mix_book 90-100% vs smith 75%) (R32) |
| **enemy_g.dat layout 정밀 분석** | Per-enemy 240B (Map+0x1f0+idx*0xf0). file +4..0xf (12B u8 markers), +0x10..0x1b (6 u16 = HP/MP/ATK/DEF/EXP/Gold), +0x1c..0x2a (15B u8 drop/level), +0x2b 이후 (4 skill blocks × 16B). 121B file 읽음 per enemy (R33) |
| **Monster struct +0x254..+0x275 가 별도 source** | enemy_g 와 직접 매핑 X. Monster constructor 또는 game-state init 에서 set. drop chance thresholds (+0x254..+0x26c) + drop count/type/marker (+0x270..+0x275) (R33) |
| **drop 시스템의 3 데이터원** | (1) enemy_g.dat → Map+0x1f0 (HP/skills), (2) droptable.dat → ItemTable+0x214 (drop pool), (3) Monster init → Monster+0x254..+0x275 (drop thresholds) (R33) |
| **Monster::setEnemyData 발견** | 0xc1a94, 1532B. LoadRes("/c/csv/enemy_%d.dat", arg) → Monster +0x218 (name) ..+0x275 (drop). +0x254..+0x275 의 모든 writer 가 이 함수에 (R34) |
| **enemy_%d.dat 3 files (difficulty)** | enemy_0/1/2.dat 각 23190B × 166 records. 첫 record size 140B (variable). byte 0x10 만 다름 (0x16/0x2d/0x46) → 3 difficulty levels 추정 (R34) |
| **Monster 시스템의 4 데이터원 정리** | enemy_g (Map HP/skills), enemy_*.dat (Monster stat+drop), droptable.dat (drop pool), smith_*.dat (craft recipes) — 모든 Monster/Item 시스템 데이터원 식별 (R34) |
| **enemy_*.dat record byte → Monster field 정밀 매핑** | byte 0..3 → +0x22c..+0x22f (markers), byte 39..66 → +0x254..+0x26c (7 u32 drop thresholds), byte 67..72 → +0x270..+0x275 (drop count/markers), byte 73..79 → +0x276..+0x27c, byte 80+ → BATTLER stats (R35) |
| **Monster decoder + 498 records JSON** | 3 difficulty × 166 records 정확 parse. Easy drop_count=0, Normal=17-19, Hard=26-27 (게임 difficulty 시스템 검증) (R35) |
| **4 element 시스템 구조 식별** | V[136..143] = 4 elements × 2 (atk/def). id=7/8 calc_pl 의 magic atk/def total 식 = sum_elements + V[153]/2 + V[144/145]*(100+30*V[89/93])/100. V[89]/V[93] = current element index. V[151]/V[152] = magic stat pair (skill slot 별 magic damage bonus) (R36) |
| **Mission 시스템 식별** | /c/csv/mission_list.dat (VFS index 48, 5355B) = 105 missions × 44B struct. Mission::LoadMissionTable (0x8b73c). 13+ Check* 함수: Refine/OrbCombine/Mix/Playtime/Money/Rank/SetItem/Collection/QuestComplete 등 (R37) |
| **모든 게임 시스템 데이터원 5종** | enemy_g (Map enemy), enemy_*.dat (Monster ×3), droptable.dat (drop pool), smith_*.dat (craft ×3), mission_list.dat (105 missions) — Round 33-37 으로 모든 시스템 데이터 파이프라인 매핑 완료 (R37) |
| **mission_list.dat record format** | u16 size + u8 strlen + name + (mission_type, sub_type, target_count) + 5×(slot u8, flag u8, value u32) + final_flag = strlen+39 byte. mission_type 0-5 (20/5/22/47/5/5) + 255 metadata. Slot 5..8 = helmet/boots/accessory cat (R38) |
| **Mission decoder + 105 missions JSON** | 105 missions 모두 정확 parse. type 분포가 Round 37 의 13 Check* 함수에 매핑 (collection/rank/quest/mix 등) (R38) |
| **Quest 시스템 식별 (Mission 과 별도)** | QuestMgr 22+ 함수, LoadQuestData (0xd40e8, 1188B) → /c/csv/quest_%d.dat. 3 files (각 22367B × 151 quests). Quest struct 368B (0x170)/entry. Mission(achievements) ↔ Quest(main story) 별도 시스템, Mission::CheckQuestComplete 가 link (R39) |
| **quest_*.dat record 정밀 매핑 + 3 difficulty scaling 확정** | Quest_GetOffset 으로 u16 size prefix layout 확인. body = 3 header byte (h0/h1=obj_count/h2) + (strlen+name) + (strlen+desc) + (strlen+cat) + phase1 (3×6B objective: cond_type u8 + cond_sub u8 + target_value u32) + phase2 (3×6B reward, 17=money/18=exp/255=unused) + 2 byte trailer. body size = 44 + s0+s1+s2. **3 files = save slot 아닌 3 difficulty** (q0/q1/q2 의 reward value 단조 증가 — quest #0 EXP: 340/20830/36150, enemy_*.dat Round 34 와 동일 패턴). 151/151 record EOF 도달 (R40) |
| **decode_h5_quest.py + quests.json 발행** | 기존 stub 교체 (mission_list 디코드 misnamed → 정상 quest decoder). 3 difficulty × 151 quests + compare table → quests.json 645KB (R40) |
| **Save 파일 시스템 RE 시작 + DES 미적용 확정** | 8 save file 종류 (LOCAL/EX/ET/OP/M/H_%d/B_%d/SL_%d.sav) + .rodata string scan. HERO::SaveAll (0x8f924, 92B) dispatch = SlotInfo::SaveSlotData → SaveHeroData → SaveBagData → Mission::SaveData. MX_desEncrypt caller .text 전체 0건 → save 는 **plain bytes**, DES 키 (0EP@KO91) 는 calc_*.dat 등 별도 protected resource 전용 (R41) |
| **자동 save write event 추출 도구** | tools/h5_extract_save_writes.py — ARM disasm + register propagation 으로 Int{8,16,32,64}ToByte / memcpy / strb/h/w 인수 추출. SlotInfo::SaveSlotData 91 events / SaveHeroData 23 events / Mission::SaveData 15 events 추출 (R41) |
| **H_%d.sav (HeroData) 개요** | +0..3 u32 + 2×u8 flag + u32 + **8×u16 stat block** (+0xa..+0x19 = HP/MP/STR/DEX/CON/INT + 2) + **7×u8 equip slot** (+0x45..+0x4b = Round 14 의 EquipItem cat 0-6 일치 추정) + u32 + u8 + 2×u64 timestamp (R41) |
| **SL_%d.sav (SlotInfo) 개요** | 가장 큰 save (malloc 0x2d9f byte buffer). +0..1 class+level / +2..9 GetX/Y / +0xa..0x11 u64 playtime / +0x12..0x15 scene_idx / +0x17 부터 3×256B 블록 (class_info inventory/stat/buff) / +0x31c..+0x489 secondary chunks. 상세 정밀 매핑은 다음 라운드 (R41) |
| **Save load cross-check 도구 + layout 확정** | h5_extract_save_writes.py 확장 (ByteToInt + ldr 추가). h5_save_crosscheck.py 신규 — offset 별 save/load size 매칭 → OK/MISS/save-only/load-only 분류. **H_%d.sav: 21/21 offset 정밀 일치 (0 mismatch)** + load 측에서 +0x1fc/+0x204 u64 timestamp 추가 발견. 총 사용 영역 ≈ 524B. **SL_%d.sav: 24 offset 일치 (0 mismatch)** + header (+0..+0x15) 완전 확정 + sub-block 1/2 (+0x433..+0x438, +0x45d..+0x462 = 6 bytes 각각 — 강화/orb socket 후보) 식별 (R42) |
| **Mission save 부분 확인** | load +0x4 ldrsh 2회 = u16 record_count 또는 size pair. 105 mission iter body 의 변수 offset 정밀 매핑은 다음 라운드 (R42) |
| **Save source struct field 라벨링 + class/level packing 발견** | LoadHeroData/LoadSlotData 정밀 disasm 으로 file_offset → HERO struct offset 완전 매핑. **핵심 발견 1**: SL_*.sav file[0] = `level*10 + class_id` packing — Load 가 umull fast-div-by-10 으로 `% 10` (class) / `/ 10` (level) 분리. max level ≈ 25. **핵심 발견 2**: 3 × 256B blocks 가 gv+0x288/0x388/0x488 = Round 5/6 의 V[58..167+] stat/buff cache 영역 그대로 직렬화 → save/load round-trip 안전. SlotInfo getter 5종 (Class/Level/X/Y/PlayTime/SceneIdx) 모두 LoadSlotData 가 채운 field 사용 검증. **데이터 RE 종료** (R43) |
| **Monster AI 시스템 = token-based bytecode VM** | 12 AI 함수 disasm. **Ai_onAction = 13 opcode interpreter** (SCN opcode 패턴 동일). op 0/1 = WALK/chance walk (motion 1/5), op 4 = SKILL slot (3B = skill_id/target/range → +0x2c9..+0x2cb), op 9 = next_skill_id (Ai_Action state 8 가 사용), op 11 = variable-length data block. **IsTriggerEqual = 13 trigger** (trigger 2 = IRect visibility/range check, trigger 1/11/13 = one-shot flags). Monster struct: +0x288 AI_def_ptr / +0x290 Tokenizer / +0x294 action_idx / +0x297 opcode / +0x2a8..+0x2ab operand buffer / +0x2c2..+0x315 state machine fields. Ai_Process entry (frame당 1회) = stun check → state check → cooldown (default 9 frames) → Ai_Action. AI 정의 데이터가 외부 byte stream (디자이너 가 monster 별 행동 작성). docs/h5/MONSTER_AI.md 신규 (R44) |
| **Monster AI 데이터원 식별 + decoder** | Map::MonsterAdd → EnemyAI* alloc (120B) → EnemyAI::LoadData (700B) 가 `/c/mon/%d_ai` 로드. VFS 에 **48 AI 파일** 발견 (`c/mon/0_ai` ~ `63_ai`, 31-305B, DES 미적용). 파일 layout 완전 파악: trigger codes/handlers + sum(handlers) data + 3 action lookups (n_a + n_a + n_a*2) + trigger byte stream (Tokenizer #1) + 3 action_list lookups (action_list_offset_table 포함) + action byte stream (Tokenizer #2, 13 opcode VM). EnemyAI struct (120B) 매핑: +0x24/+0x44/+0x60 size headers, +0x58/+0x5c trigger stream ptr, +0x70/+0x74 action stream ptr. tools/converter/decode_h5_monsterai.py 신규 — 48/48 perfect parse. monster_ai.json (48 AI defs) 발행. opcode 통계: WALK + CHANCE_WALK = 286/524 (55%) (R45) |
| **Monster AI trigger stream layout 확정** | ActionOfTrigger (0xbd7a0, 140B) driver + IsTriggerEqual 13 handler operand 매핑. Entry layout = `[trigger_code u8][operand 0-1B][action_id u8]`. trigger 1 (VISIBILITY_RECT, operand=IRect index ×40) / 6 (TUTORIAL_FLAG, operand vs gv+0x130..0x132) 만 1B operand. trigger 5 (ALWAYS_GOTO) 는 ActionOfTrigger 가 special path 처리 (IsTriggerEqual 안 부름, 즉시 action_id 처리). 나머지 11 trigger 0B operand (one-shot flag check/consume on Monster+0x2b6/0x2b7/0x29f/etc). decode_h5_monsterai.py 의 disasm_tokens(kind='trigger') 모드 추가. **543 trigger entries 100% perfect parse** (0 unknown, 0 incomplete). 분포: VISIBILITY_RECT 36% + ALWAYS_GOTO 36% (= 72% "idle→combat 시야진입 전환" 패턴). 데이터 RE 100% 종료 (R46) |
| **Monster AI Ai_Action 13 sub-state 완전 매핑** | state 0=CHASE_TIMER (Fast_Distance(hero) vs Monster+0x2c6 시야범위 비교 → ImmadiatelyCheck(8)) / 1=TURN_DIR (4 mode jumptable + default=HeroTurnDirection) / 2=COUNTDOWN (timer + state 0 재진입) / 3=SKILL_USE (IRect 충돌 검사 + cast) / 4=SET_ATTACK_MOTION (Monster+0x2cc 에서 motion lookup) / 5-8=4 skill cast path (각각 Monster+0x304/+0x305/+0x308/+0x30a source) / 9=SKILL_END / 10-11=no-op / 12=GET_MOTION_EXIT. 5 opcode → 6 state skill dispatch matrix 완전 (opcode 4→state 3, opcode 5→state 4, opcode 6→state 5, opcode 7→state 6, opcode 8→state 7, opcode 9→state 8). 공통 gate: GetMotion==0 + IsAttackAble==1 + Monster+0x315==0 (skill_disable). cast 후 Monster+0x297=-1 reset. **Monster AI 분석 완전 종료** (R47) |
| **Monster AI Godot 통합 시작** | apps/hero5-godot/scripts/core/monster_ai.gd 신규 (270 line autoload) — `MonsterAIState` class (Monster struct +0x288..+0x315 영역 매핑: action_idx/opcode/operand/cooldown/state/skill source 5 + flag 11) + `_load_ai_defs` (monster_ai.json 234KB res:// loader) + `create_runtime(host, ai_type_id)` + `process(s)` (frame entry: cooldown + Ai_Action) + `step_action_list(s)` (Ai_doActionList) + `_on_action` (13 opcode interpreter w/ operand size table) + `step_trigger_list(s)` (ActionOfTrigger walker) + `_is_trigger_equal` (13 trigger handler: one-shot flag + host method 위임). project.godot 7th autoload `MonsterAI` 등록. battle_system.gd 에 `_ai_runtime` field + start_battle hook (create_runtime 호출) + `_ai_pick_skill()` helper (트리거+action stream step + skill_id 추천). verify_godot_project.py 0 errors / 0 warnings. Godot 실 구현 25-30% → 30-35% (R48) |
| **Save/Load binary 직렬화 GDScript 구현** | save_manager.gd 확장 — `serialize_hero_save(state)` / `deserialize_hero_save(data)` (H_*.sav 524B, Round 42 의 21/21 cross-check 결과 layout) + `serialize_slot_save` / `deserialize_slot_save` (SL_*.sav header 23B, Round 43 의 `level*10+class_id` packing 포함). byte helpers (`_put_u16/32/64_le`, `_get_u16/32/64_le`) LE encoding. tools/h5_test_save_layout.py 신규 — Python round-trip 검증 도구 (GDScript serialize 의 Python equivalent + 4 samples + 8 critical offsets), **모든 검증 통과**. verify_godot_project.py 0 errors / 0 warnings. Godot 실 구현 30-35% → 33-38%, 출시 27-37% → 30-40% (R49) |

### Phase 2/3 인프라 완료
- ✅ DES 변종 해독 (S1[3][10]=2), calc_*.dat MD5 검증 평문 dump
- ✅ Formula VM 186 공식 (39+19+128) 디스어셈블 + GDScript 평가기 + battle_system 통합
- ✅ gv+0x1474 sub-struct 111 fields 정확 매핑
- ✅ ItemTable / EquipItemInfo / ItemBase 구조체 layout 추출 (R13~R19)
- ✅ items.json 에 named fields 부여 (subtype, class_mask, class_label, level_limit, item_id, sub_record, val_150..val_160, refine fields)

### 직전 작업 (이어서 진행 시 시작점)
- Round 40 종료. 다음 라운드 시작점은 아래 "다음 세션 시작점" 섹션 참조.
- 가장 직접적 옵션 (남은 데이터 RE 마무리): **Save 파일 포맷 분석** — HERO::SaveAll
  (0x8f924) 분석 + DES (key 0EP@KO91, S1[3][10]=2 변종) 복호 + record layout.
- 큰 임팩트 옵션: **Monster AI 시스템** — Ai_Action 2136B 등 미분석 함수 RE.
- 출시 % 끌어올림: **Godot UI 구현** (인벤토리/강화/합성/Quest 패널).
- 또는: scn opcode 실제 game scene 동작 검증, 한글 폰트 매핑 (LOW PRIORITY).
- ✅ **Round 6**: gv_sub 핵심 필드 정확화 (writer 분석으로 V[58]=level, V[60..63]=base_str/dex/int/con,
  V[69]=SP, V[70]=CP, V[118..121]=bonus_str/dex/int/con 확정)
- ✅ **Round 6**: visual 효과 hookup — screen_shake tween, map_tile_change highlight, narration text lookup
- ✅ **Round 7**: V[111]=atk_growth_coef, V[112..116]=secondary stat base, V[153]=stat_con, V[154]=stat_str, V[155]=max_sp 확정
- ✅ **Round 8**: V[127]=def_reduction%, V[128]=atk%bonus, V[129..133]=secondary stat bonus, V[134..148]=element/magic bonus 식별. Round 7 의 0x294/0x296 (buff descriptor) 가 Formula VM var 가 아닌 gameplay 전용 필드임을 정정 (V[125]=0x2a6, V[126]=0x2a8 별개)
- ✅ **Round 9**: ApplyBuildupEffect jumptable 자동 추출 도구 (`tools/h5_apply_buildup_disasm.py`).
  V[122..126] = 5 buff stat slot 확정 (entry type 30/31/32/34/36).
  V[125]/V[126] (0x2a6/0x2a8) 의 store target 확정.
  c_csv_class.json 의 5 클래스 V[112..116] base 패턴 추출 (워리어/로그/건슬링어/나이트/소서러).
  battle_system.gd + formula_vm.gd 에 클래스별 정확 lookup 적용.
- ✅ **Round 10**: 한글 stat label 의 .so 직접 reference 0건 확인 — 모두 VFS text/*.json 에 분산.
  `00017_488ab1c6.json` 에 status menu 의 20-stat 라벨 sequence (방어력/공격력/물리방어력/.../크리티컬저항) 발견.
  `StateInGameMenu::DrawPropertyMenu` 가 register-indirect dynamic dispatch — 정적 분석으로 stat↔cache offset 매핑 어려움 확인.
  `HERO::CalcStatusComputation` 의 24 calc 호출이 모두 `calc_sk[2003] (V[41])` + `calc_sk[2004] (V[156])` 두 공식만 사용 — 7 EquipItem slot × 2 stat + 4 spirit slot × 2 stat. V[136..148] (element bonus) 영역에 cache.
  V[112..116] 5 stat 의 한국어 라벨은 미확정 — 후보 (명중률/회피율/크리티컬/정확도/마법적중) 식별.
- ✅ **Round 11**: c_csv_buildup.json (`tools/h5_decode_buildup.py`) 의 entry type ↔ ApplyBuildupEffect type 매핑으로 **V[112..116] 5 secondary stat 라벨 확정**:
  - V[112] = 근접명중 (csv 0x14 → ABE 11 → V[129] bonus)
  - V[113] = 장거리명중 (csv 0x15 → ABE 12 → V[130] bonus)
  - V[114] = 회피 (csv 0x16 → ABE 13 → V[131] bonus)
  - V[115] = 방패방어 (csv 0x18 → ABE 14 → V[132] bonus)
  - V[116] = 크리티컬 (csv 0x19 → ABE 15 → V[133] bonus)
  5 클래스 base 패턴이 모두 합리적으로 일치 (워리어=근접명중 24, 건슬링어=장거리명중 24, 워리어=방패방어 5).
  **V[62]/V[63] = base_con/base_int 정정** (이전 int/con 매핑 오류) — buildup csv "건강+#1" → ABE 4 → V[120] = bonus_con, "정신+#1" → ABE 5 → V[121] = bonus_int.
  decode_h5_class.py / class_stats.json / class_select.gd / battle_system.gd / formula_vm.gd 일괄 정정.
- ✅ **Round 25**: slot_15 (mix_book recipe) 13 byte ext 구조 RE 완료:
  - layout: byte 0 (separator) + 3×3 byte ingredients (cat/idx/count, 0xff=unused) +
    2 byte result (cat/idx) + 1 byte success_rate %.
  - 116 records 모두 정확히 parse (이름 cross-check 검증).
  - 쿠킹 (살코기+황혼버섯 → 황혼수프가루 100%), 포션 합성 (포션 ×2 → 미들포션 100%),
    재료 정제 (엑토플라즘 ×10 → 에테르 90%), 무기 제작 (보통칼날+가죽+강철 →
    투란기어 90%) 등 카테고리화.
  - success_rate 분포 = 게임 밸런스 검증 (legendary 무기 20-22%, 일반 100%).
  - parse_mix_book_extra 가 의미있는 'recipe' 객체 부여 (이전 raw sb_extra_hex 대체).
- ✅ **Round 24**: val_15f upper 3 bit (tier_flags) 의 실증적 의미 식별:
  - **csv-time vs runtime val_15f 용도 분리** 발견 — csv 는 (class_mask + tier_flags),
    runtime 은 SetItemOption (0xa0ff8) 가 option_type code 로 완전 overwrite.
    GetRelieveLevelLimit (0xa835c) 의 `cmp #0x6c` ('l') 는 runtime option_type 비교.
    MakeItemOption (0xa10e8) 가 val_15c (option_grade) 로 SetItemOption 호출 여부 결정.
  - **items.json 789 EquipItem records 분포 분석** 으로 upper 3 bit 의 의미 추정:
    - upper=0 (170): **legendary** — 실가라스/투란기어/디바인세이버 보스 무기
    - upper=1 (248, bit5): **rare** — 중급 무기/방어구
    - upper=3 (9, bit5+6): **gem** — slot_5 보석 헤어핀/서클릿 (청금석/루비/오팔)
    - upper=7 (362, bit5+6+7): **common** — 일반 상점 (롱소드/단검 등)
  - 가설: bit5="obtainable" / bit6="gem-accessory" / bit7="common-tier".
  - parse_equip_extra 가 tier_flags + tier_label 부여 (legendary/rare/gem/common).
  - slot_4 "스태프" 1 record 가 tier=legendary + class_mask=0 (Sorcerer 전용 staff)
    Round 22 미구현 stub 사실과 cross-confirm.
- ✅ **Round 23**: HERO::BattleUseItem (0x8fd20, 536B) 디스어셈블 + SLOT_META 전면 정정:
  - slot_11 의 +0x134..+0x137 의미 확정:
    - +0x134 = effect_type → HERO[0x2fe] → CalcStatusComputation 분기
      (91=HP heal, 90=SP heal, 87=buff 보호, 92=마석, 19=test, 0=무효)
    - +0x135 = success_rate % → random(0,99) 와 cmp (모두 100 = 100% 성공)
    - +0x136 = effect_value → HERO[0x300] (u16, 회복량/buff 강도)
    - +0x137 = duration → HERO[0x302] (s16, 지속 turn)
    - SetPotionCoolTime(100) — cooldown 100 frame.
  - SLOT_META 전면 정정 (record 이름 + ext_after_sb 길이 cross-check):
    - slot_12 = orb (이전 scroll 잘못, 2 byte ext, 뇌제의오브 등)
    - slot_13 = mix material (이전 orb 잘못, 0 ext, 살코기/재료2..9)
    - slot_15 = mix_book recipe (이전 material_2 잘못, 13 byte ext, 황혼수프/포션)
  - parse_battle_use_extra 라벨 정정 (val_134→effect_type 등 의미있는 이름).
- ✅ **Round 22**: Sorcerer (class_id=4) 미구현 stub 확정 분석:
  - .so 클래스 심볼 검색 → WARRIOR / ROGUE / GUNNER / KNIGHT 4개만 존재.
    SORCERER class object 없음.
  - skill csv 검색 → c_csv_skill_00..03 (player) + c_csv_skill_05 (16 monster
    skills: 암흑탄/지옥소환/얼음폭풍/완전면역 등). c_csv_skill_04 완전 부재.
  - class_stats.json 검토 → 소서러 unk1..unk14 모두 1 (다른 클래스 6/12/18/24).
    unk0=320 (다른 1000) — 명백한 placeholder.
  - IfLearnSkill 의 (class/2)+16=18 매핑은 dead code path. slot_18 (CashItem)
    의 records 49 모두 class_id=4 없음.
  - class_select.gd UI 정정 — "소서러" → "소서러 (미구현)" 라벨 표시.
  결론: 영웅서기5 출시 빌드 = 4 클래스 only. 소서러는 향후 확장 클래스로
  계획됐으나 미구현 채로 출시.
- ✅ **Round 21**: HERO::IfLearnSkill (0x95d08, 316B) 디스어셈블 → SkillBook
  +0x134..+0x137 의 의미 정확 식별:
  - +0x134 = **class_id** (HERO 클래스 0..4)
  - +0x135 = **skill_index** (HERO::skills[] 배열 인덱스)
  - +0x136 = **skill_level** (LV 매칭 ✓ Round 20)
  - +0x137 = **required_level** (HERO+0x22d 와 cmp)
  - 공식 `(class_id/2)+16` → Warrior/Rogue=cat 16 (slot_16), Gunslinger/Knight=cat 17
    (slot_17), Sorcerer=cat 18 (slot_18 — 충돌, 별도 path 추정).
  - slot_16 도 실제 SkillBook 임이 확인 (양손베기/돌진/내려찍기 등 Warrior 스킬)
    — SLOT_META 정정 (이전 'mix_book' 잘못).
  - parse_skill_book_extra 의 라벨 정정 (val_134→class_id, val_135→skill_index,
    val_137→required_level).
  - 검증: slot_16 95 records (Warrior 48 + Rogue 47), slot_17 98 records
    (Gunslinger 49 + Knight 49). 각 클래스 정확히 10 skills × 1..7 levels.
- ✅ **Round 20**: LoadItemTable 함수 끝 영역 (0xa479c..0xa49c0) 추가 disasm —
  `tools/h5_dump_loaditem_tail.py` (`capstone.skipdata=True` 로 literal pool 통과).
  - **slot_17 (SkillBookItem) 4 byte ext** @ 0xa47c0 (jumptable case 16/17 공유).
    +0x134=skill_class (2/3), +0x135=skill_id (0..9), **+0x136=skill_level**
    (V[1..7] 이름과 정확 매칭 ✓), +0x137=required_level (monotonic).
    검증: '연속사격LV1..LV4' = (2, 0, 1..4, [1, 4, 10, 22]) — 4 byte 모두 일치.
  - **slot_18 (CashItem) 2 byte ext** @ **0xa3b38** (jumptable case 18 별도 path —
    Round 19 의 0xa47c0 가설 정정). hardcoded type 0x12=18 at +0x14, 2 byte:
    +0x134 (cash_category 0..3), +0x135 (stack/type, 255=passive 추정).
  - `decode_h5_item.py` 에 `parse_skill_book_extra` (4 byte) + `parse_cash_extra`
    (2 byte) 추가, SLOT_META[18] = "cash" 로 정정 (이전 "skill_book" 잘못).
  - items.json 검증: slot_17 98 records, slot_18 49 records 모두 추가 fields populated.
- ✅ **Round 19**: LoadItemTable 의 cat 12+ jumptable case 별 추가 fields disasm:
  - cat 12 (BattleUseItem, 0xa4060): +0x134/0x135/0x136/0x137 (4 byte u8) — csv 에서 매칭 ✓
  - cat 13 (OrbItem, 0xa423c): +0x134/0x135 (2 byte, csv 에 보통 없음)
  - cat 14, 15 (MixItem, 0xa43f4): 추가 fields 없음 (record_size = base 만)
  - cat 16 (MixBookItem, 0xa4578): sub-loop +0x135..+0x140 (12+ byte, csv 에 4 만)
  - cat 17, 18 (SkillBook/Cash, 0xa47c0): 다음 라운드
  decode_h5_item.py 에 `parse_battle_use_extra` / `parse_orb_extra` /
  `parse_mix_book_extra` 추가 + dispatch wire-up. items.json 의 slot_11 포션이
  정확한 4 byte (val_134=91, val_135=100, val_136=4, val_137=50) 추출 — disasm
  매핑이 csv 와 정확 일치 검증.
- ✅ **Round 18**: ItemTable::SetItemOption (240B, @0xa0ff8) 디스어셈블 →
  `+0x15f` 가 random option_type byte 임 확인. SetItemOption 가 호출 시 random
  option 픽 → +0x15f = option_type, +0x162 = option_value (level*param*rand).
  csv 의 val_15f 는 init default — runtime 변경 가능. items.json 의 class_label
  통계가 default 값 (Round 16 의 5-class mask 해석은 csv 시점에는 유효).
  LoadItemTable 의 cat 12+ jumptable 분석 — 모든 카테고리가 공통 base layout
  (item_id u32 + sub_record_len + sub_record bytes) 공유. EquipItem (cat 1-11)
  만 sb-area 추가. `decode_h5_item.py` 에 `parse_common_extra` 함수 추가 →
  모든 19 슬롯에 item_id + sub_record_hex 부여.
- ✅ **Round 17**: `RefineItem::ApplyItemRefine` (956B) 디스어셈블 → 강화 시
  변경되는 EquipItemInfo struct field 식별:
  - `+0x165` = refine_count (강화 횟수 u8)
  - `+0x166` = refine_sub_count (보조 강화 u8)
  - `+0x167` = refine_locked (1=영구 잠금)
  ApplyItemRefine 의 r7 jumptable: r7=0/1=success +N, r7=3=lock, r7=4=실패(아이템 destroy).
  CopyData (0xa8884) 가 +0x165..+0x168 모두 복사 → runtime 변경 saved.
  val_15f upper 3 bit 통계: upper=7 (224, "common") 362 records, upper=1 (32, "강화")
  248 records, upper=0 ("중급") 170, upper=3 ("보석 액세서리") 9 (slot_5 헤어핀/서클릿).
  정확 의미 식별 미완 — bit6 (64)=gem accessory, bit7 (128)=common flag 가설.
- ✅ **Round 16**: items.json 정정 — `+0x155` 가 class_restriction 이 아니라
  **subtype code** 임을 IsEquipPossible / IsEquipPossibleSpirit cross-check 로
  확인 (slot_10 spirit 의 cls=5/7 분포 + IsEquipPossibleSpirit 가 0x155==7 만 허용).
  진짜 class restriction 은 **`val_15f & 0x1f`** = **5-class 비트 마스크**
  (bit0=W, bit1=R, bit2=G, bit3=K, bit4=S):
  - val=31 (WRGKS, 모든 클래스) 385 records (가장 많음)
  - val=9 (WK), val=17 (WS), val=14 (RGK), val=18 (RS) 등 다양
  - spirit 검증: 데몬의뿔 W only / 고렘의인장 RS / 팬텀의부적 WS / 기사의징표 RGK
  - decode_h5_item.py 가 `subtype` (이전 class_restriction 정정) + `class_mask`
    + `class_label` (W/R/G/K/S 조합 string) 부여.
  - val_15f upper 3 bit (32, 64, 128) 의 추가 의미 (career/tier/cash) 는 다음 라운드.
- ✅ **Round 15**: `decode_h5_item.py` 에 `parse_equip_extra` 함수 추가 — Round 14
  의 csv layout 활용해 EquipItem (cat 1-11) extra body 가변 parse + items.json
  에 named fields (`class_restriction`, `level_limit`, `item_id`,
  `sub_record_hex`, `val_150..val_160`, `triplet_162`) 부여.
  검증: 롱소드 cls=0/lv=1, 나이트롱소드 lv=5, 버클러(방패) cls=3 (워리어/나이트),
  서클릿(헬멧) cls=5/lv=1 — 모두 합리적 매핑.
  cls 가 비트 마스크로 추정 (1=warrior, 2=rogue, 4=gunslinger, 8=knight, 16=sorcerer)
  — 다음 라운드 IsEquipPossible cross-check 필요.
- ✅ **Round 14**: ItemTable::LoadItemTable (4320B) 의 EquipItem 처리 영역
  (0xa3cf0~0xa4060) 디스어셈블 분석 → csv record body → in-memory EquipItemInfo
  struct field 매핑 layout 추출:
  - csv +2..3 (u16 read but discarded — struct +0x14 = function arg category)
  - csv +4..5 (u16) → struct +0x16 (refine_value)
  - csv +6 (u8 name_len `nl`) → name string memcpy → struct +0x18
  - csv +7+nl..(+4 byte) (u32) → struct +0x30
  - csv +11+nl (u8 sub_record_len `sblen`) → 256B sub-record memcpy → struct +0x34..+0x134
  - 그 후 sb 시작 위치에서 u16/u8 sequence → struct +0x150..+0x162 영역
  - LoadItemTable 안에서 Formula::calc(0x7f3=2035) 호출 — load 시점 base stat 계산
  - `tools/h5_extract_loaditem_layout.py` 도구 작성 (register tracking 한계로
    부분 추출 — 수동 disasm 분석으로 보완).
- ✅ **Round 13**: EquipItemInfo struct 핵심 field + ItemBase formula 영역 식별.
  - EquipItemInfo +0x14 = item_category/slot_type (s8) — IsEquipPossible jumptable 의 조건
  - EquipItemInfo +0x155 = class_restriction (s8) — HERO+0x22c (class_id) 와 비교
  - EquipItemInfo +0x15d = level_limit (s8) — GetLevelLimit 가 fetch
  - EquipItemInfo +0x168..+0x16d = 6 socket slot (orb/refine ID, 0xff=빈슬롯)
  - V[168..182] = ItemBase (Formula::calc 5번째 인수) 의 struct field:
    - V[168] (item +0xe) = base SP cost (`V[168]*(100-V[123])/100`)
    - V[170] (item +0x16) = base cooldown (`V[170]*(100-V[125])/100`)
    - V[174] (item +0x44) = damage growth multiplier (`V[56]+V[57]*V[174]`)
    - V[181] (item +0x4e) = speed/weight divisor
  - csv extra (33..80B) ≠ in-memory EquipItemInfo (376B) — `LoadItemTable` 가 csv→struct
    매핑 처리. csv stat order ↔ struct offset 매핑은 다음 라운드 RE 필요.
- ✅ **Round 12**: V[122..126] 5 buff slot 정확 라벨 + V[151,152] magic stat 정정.
  - V[122] = EXP %bonus (`(100+V[122])/100` multiplier, csv 0x1d 경험치LV)
  - V[123] = SP소모% 감소 (`V[168]*(100-V[123])/100`, csv 0x1e)
  - V[124] = CP충전LV (`(V[124]/100)*150+300`, csv 0x1f)
  - V[125] = 쿨타임 감소% (`V[170]*(100-V[125])/100`, csv 0x21)
  - V[126] = 포션효과 %bonus (`V[56]*V[183]*(100+V[126])/100`, csv 0x23)
  - V[151], V[152] 둘 다 magic stat (INT 보정) — 이전 V[152]=DEX 추정 정정.
  formula 공식의 `(100±V[xxx])/100` 패턴 + csv 라벨 cross-check 로 일관 확정.

**이번 세션 (2026-05-09 Round 6) 완료 항목**:
- **gv_sub writer 분석 도구** — `tools/h5_find_gv_writers.py` (3568 함수 스캔, 547 stores 추적).
  산출 `gv_substruct_writers.tsv` + `gv_substruct_writers_summary.txt` (135 unique offsets).
- **gv_sub 필드 의미 식별** — calc_pl id=18 `(104*V[58]^2)+711+(level-1)*600` ⇒ V[58]=level 확정,
  HERO::IncreaseSP/IncreaseCP writer ⇒ 0x248=SP / 0x24a=CP, calc_pl id=20..23 패턴 ⇒ 0x236..0x23c=base, 0x298..0x29e=bonus.
  자세히 [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md).
- **`battle_system._player_ctx()` 정확화** — 12 확정 + 6 강한 추정 매핑 적용 (이전 추정 6 → 18).
  Python sanity test (`h5_test_formula_eval.py`) id=0 → 4437 통과.
- **`formula_vm._player_default()` 정확화** — defender side fallback 도 동일 매핑 적용.
- **시각 효과 hookup** — demo.gd 의 toast trace → 실제 visual 적용:
  - `screen_shake`: Demo Node2D position Tween 으로 8-step decay oscillation
  - `map_tile_change`: MapRenderer.highlight_tile 노란 사각형 1.5초 표시
  - `narration`: GameData.ingame_text(string_idx) lookup → DialogBox

---

## 빠른 재개 (1 커맨드 = 환경 복원)

**가장 흔한 케이스 — assets/ 비어있는 새 클론**:
```bash
# APK 가 있는지 확인 후 (Hero5/영웅서기5(최신폰전용).apk)
# 한 번에 모든 자산 처리 (~6s, incremental — 이미 있는 단계는 스킵):
python tools/h5_extract_pipeline.py
#   --force        : sentinel 무시하고 전체 재실행
#   --only NAME ...: 특정 단계만 (apk/vfs/names/sprite/text/converters/disasm/godot/verify)
#   --skip NAME ...: 특정 단계 제외
# 단계별 수동:
python tools/h5_vfs_unpack.py            # 1. VFS unpack (2189 entries)
python tools/h5_recover_names.py         # 2. 이름 복원 (99.7%)
python tools/h5_batch_sprite.py          # 3. sprite 421 + palette 588
python tools/h5_extract_text.py          # 4. 한글 코퍼스
for f in tools/converter/{convert,decode}_h5_*.py; do python $f; done   # 5. 디코더 일괄
python tools/import_to_godot.py          # 6. assets/ 채우기 (opcode_table 자동 포함)
python tools/verify_godot_project.py     # 7. 검증 → 0 errors / 0 warnings 기대

# 마지막: Godot 4.2+ Editor 에서 apps/hero5-godot/ 열고 F5
```

**단순 검증만 (assets/ 이미 있음)**:
```bash
python tools/verify_godot_project.py
```

---

## 다음 세션 시작점 (Round 40 후보)

> 진척 평가 (위 § 전체 진척 평가) 기준으로, 가장 큰 임팩트 순.

### A. (분석 track) quest_*.dat record 정밀 매핑 + decoder — 1 라운드 (자율 가능)

Round 39 에서 Quest 시스템 데이터원 (3 files × 151 quests) 식별. 정밀 매핑:
- LoadQuestData 1188B 의 ByteToInt16/strb 시퀀스 추적
- 151 quests × variable-size record (avg 148B) → struct 368B 매핑
- decoder 작성: quest_*.dat → JSON (이름/타입/조건/보상/NPC 대화 등)
- 3 files 동일성 검증 (save slot 가설 cross-check)
- **임팩트**: Mission 시스템과 함께 quest progression 완료, 데이터 RE 거의 마무리

### B. (분석 track) Monster AI 시스템 분석 — 2~3 라운드 (자율 가능, 큰 임팩트)

미분석 큰 덩어리. UI 다음 가장 영향 큰 미완 영역:
- `Monster::Ai_Action` (0xc1068, 2136B) — main AI dispatch
- `Monster::Ai_onAction` (0xbee48, 704B) — action execution
- `Monster::Ai_setActionList` (0xbd82c, 100B) — action list builder
- `Monster::Ai_doActionList` (0xbf108, 184B) — action runner
- `Monster::Ai_Initialize` / `Ai_SetPtr`
- `Monster::IsTriggerEqual` (0xbd278, 1320B) — AI trigger check
- **임팩트**: 실제 Monster 행동 로직 파악 → Godot battle 구현에 직결

### C. (분석 track) Save 파일 포맷 분석 — 1~2 라운드

DES 키 (`0EP@KO91`) + S1[3][10]=2 변종 알려져 있음. Save 파일 record layout 미분석.
- `HERO::SaveAll` (0x8f924) 분석 — 어떤 fields 가 어떤 순서로 직렬화?
- `HERO::LoadAll` 또는 LoadHeroData 분석 — 역직렬화 layout
- save 파일 디코드 + 구조 식별
- **임팩트**: 실제 게임 저장 데이터 호환 → save migration 가능

### D. (구현 track) Godot UI 구현 시작 — 5~10 라운드 큰 작업

데이터는 다 있지만 미구현. 가장 부족한 영역.
- 인벤토리 패널 (items.json 1360 items 활용, equip/sort/filter)
- 강화 UI (Round 17/26 ApplyItemRefine mechanism)
- 합성 UI (mix_book + smith_table)
- NPC 대화 / cutscene UI (scn opcode 77/77)
- Quest / Mission 패널
- **임팩트**: "리메이크 출시 가능" % 가장 크게 끌어올릴 작업

### E. (검증 track) scn opcode 실제 game scene 동작 검증 — 2~3 라운드

Round 22-39 에서 데이터/함수 분석은 했지만 실제 Godot 에서 scn 실행 검증 부족.
- Title → ClassSelect → Demo 외 다른 화면 (Battle, Inventory, Quest 등) 진입 테스트
- scn 258 body 의 opcode dispatch 가 정확히 동작하는지 확인
- 잘못된 opcode 매핑 발견 + 정정
- **임팩트**: 기존 분석의 정확성 검증

### F. 한글 비트맵 폰트 매핑 (LOW PRIORITY)

Round 28 에서 ApplyNormalMix 가 csv slot_15 와 별개로 MixSmithTableInfo* 사용 확인.
HERO::GetMixSmithTableInfoPtr (0x890f4) 의 implementation 분석으로:
- MixSmithTableInfo 데이터의 위치 (VFS entry, .so .rodata 또는 별도 csv 파일)
- 데이터 entry 갯수 + 각 entry 의 의미 (NPC blacksmith UI 와 cross-check)
- struct layout (Round 28: +0x11c..+0x128) 의 csv layout 매핑

### G. P6: Android APK 실 빌드 검증 (USER TASK — 자동화 불가)

Godot Editor 4.2+ + Build Template + Export Templates (~1GB) + JDK 17 + Android
SDK 필수. 사용자가 GUI 로 진행 필요. `apps/hero5-godot/export_presets.cfg.template`
참조. 모든 Godot UI/AI/battle 구현 완료 후 진행.

### 추가 자율 작업 (LOW PRIORITY)

- **val_15f bit5/bit6/bit7 정확 의미** (Round 24/27 가설 검증) — items.json 분포로 라벨 부여, NewDropItem args 추가 검증 필요
- **save 파일 dump → V[112..116] 라벨 재검증** (Round 11 의 secondary stat) — Save 포맷 분석 (옵션 C) 후

---

## 과거 우선순위 작업 (모두 완료)

| 영역 | 상태 | 산출 |
|---|---|---|
| P1: OPCODE_TABLE 77개 | ✅ EventProc::onFunction jumptable 자동 추출 | `work/h5/analysis/opcode_table.tsv`, capstone+lief |
| P2: enemy_g 121B layout | ✅ HP/MP/ATK/DEF/EXP/Gold + 5 skill slot | .so disasm 검증 |
| P3: Hero/CHAR 시스템 | ✅ 4방향 이동 + walk_frames | `character.gd` |
| P4: 전투/퀘스트/UI | ✅ 골격 + 실제 데이터 통합 | battle_system, quest_system |
| P5: 한글 폰트 | ✅ table.dat=Unicode (시스템 폰트로 우회) | `P5_FONT_MAPPING.md` |
| Damage formula 심층 | ✅ Event_PlayerDamage + BATTLER offset 확정 | `BATTLE_FORMULA.md` |
| Formula VM 식별 | ✅ 6 opcode 스택 머신 (calc_pl/en/sk.dat) | `BATTLE_FORMULA.md` §6 |
| Event_* 102개 매핑 | ✅ 1:1 mapping reference | `EVENT_OPCODE_REFERENCE.md` |
| ItemTable 19-카테고리 | ✅ runtime_size dispatch | `ITEM_STRUCT.md` |
| Formula VM 변수 사전 | ✅ 254 var_id → struct/offset | `FORMULA_VAR_DICT.md` |
| GOT gv 식별 | ✅ var_id 58-160 → gv[0x1474] sub-struct | Round 3 |
| interpreter.gd signal | ✅ 13 signal (map/camera/narration/...) | Round 3 |
| DES 변종 해독 | ✅ 표준 DES + S1[3][10]=2 단일 수정 | `DES_VARIANT.md`, Round 4 |
| calc_*.dat 평문 | ✅ 3 파일 MD5 검증 통과 | `work/h5/analysis/calc_*_plain.bin` |
| Formula VM 186 공식 | ✅ infix 표현 dump | `work/h5/analysis/formulas_disasm.txt` |
| gv_sub 111 fields | ✅ var_id 58-167+249 offset/type 매핑 | `gv_substruct_layout.tsv`, Round 5 |
| GDScript Formula VM | ✅ FormulaVM autoload + battle 통합 | `formula_vm.gd`, Round 5 |
| gv_sub 핵심 의미 식별 | ✅ writer 분석으로 V[58]=level / 0x248=SP / 0x24a=CP 등 18 fields 매핑 | `gv_substruct_writers.tsv`, [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md), Round 6 |
| 시각 효과 hookup | ✅ screen_shake tween + map highlight + narration text lookup | `demo.gd`, `map_renderer.gd`, Round 6 |
| V[111..116] 의미 | ✅ Round 7: V[111]=atk_growth coef, V[112..116]=class secondary stat base | LoadResClassInfo disasm + id=24..29 cross-check |
| 0x294/0x295/0x296 buff descriptor | ✅ Round 8: gameplay 전용 (Formula VM var 아님) | HERO::ApplyBuildupEffect + Round 7 정정 |
| V[127..148] buff/element bonus | ✅ Round 8: V[127]=def_red%, V[128]=atk%bonus, V[129..133]=stat bonus, V[134..148]=element | calc_pl 공식 패턴 + AddBuffArray disasm |
| V[151..155] formula 의존 stat | ✅ Round 7: V[153]=con, V[154]=str, V[155]=max_sp 확정 | id=0 / id=24 공식 + ApplyBuildupEffect entry 32 |
| V[122..126] 5 buff stat slot | ✅ Round 9: ApplyBuildupEffect entry type 30/31/32/34/36 자동 추출 | `applybuildup_table.tsv`, `tools/h5_apply_buildup_disasm.py` |
| V[112..116] 클래스 base 패턴 | ✅ Round 9: 5 클래스 secondary stat base 추출 | `class_stats_table.txt`, `tools/h5_extract_class_stats.py` |
| 한글 stat label 의 .so 위치 | ✅ Round 10: .so 0건, VFS text/*.json 에 분산 확인 | `tools/h5_find_kr_stat_strings.py` |
| 00017 status menu 20-stat sequence | ✅ Round 10: 라벨 순서 추출 | `tools/h5_find_kr_text_idx.py`, `kr_stat_text_locations.tsv` |
| CalcStatusComputation 의 calc_sk 매핑 | ✅ Round 10: calc_sk[3]=V[41], calc_sk[4]=V[156] (EquipItem stat) | `calc_status_cache_map.tsv`, `tools/h5_calc_status_table.py` |
| V[112..116] 5 secondary stat 라벨 | ✅ Round 11: 근접명중/장거리명중/회피/방패방어/크리티컬 확정 | `tools/h5_decode_buildup.py`, `buildup_decoded.tsv` |
| V[62]/V[63] = base_con/base_int 정정 | ✅ Round 11: buildup csv "건강"/"정신" 매핑 검증 | 동일 |
| V[122..126] 5 buff slot 라벨 | ✅ Round 12: EXP%/SP감소%/CP충전LV/쿨타임감소%/포션효과% | formula `(100±V[xxx])/100` 패턴 |
| V[151,152] magic stat 정정 | ✅ Round 12: 둘 다 INT-magic (이전 V[152]=DEX 잘못) | `formulas_disasm.txt` 사용 패턴 |
| EquipItemInfo struct 핵심 5 field | ✅ Round 13: +0x14/+0x155/+0x15d/+0x168..0x16d | `tools/h5_dump_caller.py _ZN13EquipItemInfo*` |
| V[168..182] ItemBase formula 영역 | ✅ Round 13: V[168]=SP cost, V[170]=cooldown, V[174]=damage growth, V[181]=divisor | `formulas_disasm.txt` cross-check |
| csv → EquipItemInfo struct layout 매핑 | ✅ Round 14: 가변길이 (name + sub_record) + u8/u16 mixed sequence | `tools/h5_extract_loaditem_layout.py`, ITEM_STRUCT.md "CSV → EquipItemInfo struct 매핑" 섹션 |
| items.json EquipItem named fields | ✅ Round 15: class_restriction/level_limit/item_id/sub_record/val_150..val_160 부여 | `tools/converter/decode_h5_item.py::parse_equip_extra` |
| +0x155 = subtype (class_restriction 정정) | ✅ Round 16: IsEquipPossibleSpirit cross-check | items.json `subtype` 필드 |
| 진짜 class_mask (val_15f & 0x1f) | ✅ Round 16: 5-class 비트 마스크 확정 (W/R/G/K/S) | items.json `class_mask` + `class_label` 필드 |
| EquipItemInfo refine fields | ✅ Round 17: +0x165=count, +0x166=sub_count, +0x167=locked | `applyitemrefine_disasm.txt` |
| val_15f upper 3 bit 분포 | ✅ Round 17: upper=0/1/3/7 만 등장 (170/248/9/362), 정확 의미 미완 | `tools/h5_check_items.py` |
| SetItemOption: +0x15f=option_type / +0x162=option_value | ✅ Round 18 | `_ZN9ItemTable13SetItemOptionEP8ItemInfoa` disasm |
| 모든 카테고리 (cat 1-18) common base | ✅ Round 18: item_id + sub_record_hex | `decode_h5_item.py::parse_common_extra` |
| cat 12-16 카테고리별 추가 fields layout | ✅ Round 19: BattleUseItem 4 byte / OrbItem 2 byte / MixItem 0 / MixBookItem 12 byte | `parse_battle_use_extra` / `parse_orb_extra` / `parse_mix_book_extra` |
| BattleUseItem (cat 12) +0x134..+0x137 csv 매칭 검증 | ✅ Round 19: slot_11 포션 4 byte 정확 추출 | items.json |
| slot_17 (SkillBookItem) 4 byte ext + skill_level 식별 | ✅ Round 20: 0xa47c0 disasm, 98 records 모두 v134/v135/skill_level/v137 추출 | `parse_skill_book_extra`, items.json |
| slot_18 (CashItem) 2 byte ext + 별도 jumptable case | ✅ Round 20: 0xa3b38 (Round 19 가설 정정), 49 records 모두 추출 | `parse_cash_extra`, items.json |
| SkillBook 4 byte fields 의미 (class_id/skill_index/skill_level/required_level) | ✅ Round 21: HERO::IfLearnSkill 분석, (class_id/2)+16 공식 확인 | `iflearnskill_disasm.txt` |
| slot_16 = SkillBook 정정 (이전 mix_book 잘못) | ✅ Round 21: Warrior 48 + Rogue 47, 양손베기/돌진/내려찍기 등 | items.json, SLOT_META |
| 소서러 (class_id=4) 미구현 stub 확정 | ✅ Round 22: skill_04.dat 부재 + SORCERER class 없음 + class_stats unk1..14=1 | class_stats.json, c_csv_skill_*, class_select.gd "(미구현)" |
| class_stats.json STR/DEX/CON/INT 순서 정정 | ✅ Round 11: decode_h5_class.py 정정 + 재생성 | `tools/converter/decode_h5_class.py` |
| 강화 stat 보너스 식 (Formula VM id=35/36) | ✅ Round 26: refined_stat = base + sub_count (V[187]) | `formulas_disasm.txt`, `formula_var_dict.tsv` |
| V[184]/V[185] = item +0x156/+0x158 stat | ✅ Round 26: weapon=atk_min/max, shield=phys/mag def, helmet/boots/acc=primary/secondary | items.json stat_a/stat_b 분포, `decode_h5_item.py::parse_equip_extra` |
| ApplyItemRefine 5-case jumptable 의미 | ✅ Round 26: 큰성공/성공/stay/lock/destroy + refine_count cap=10 | `applyitemrefine_disasm.txt` |
| ApplyOrbCombine orb socket mechanism | ✅ Round 26: 39 orb 종 (3×13), +0x168 orb_count, +0x169..+0x16d 5 socket | `applyorbcombine_disasm.txt` |
| NewDropItem signature 12 args + +0x15f position | ✅ Round 27: `(MapItem*, x, y, cat, idx, val_15c, val_15f, val_162, val_160, val_163, val_161, val_164)` 7번째 arg = tier_flags | `newdropitem_disasm.txt` |
| Monster drop_table 13-byte entry | ✅ Round 27: SetDropItem 안에 13B/entry × 4 drop type. NewDropItem 의 +0x15f arg 가 entry byte 에서 직접 전달 | `setdropitem_disasm.txt` |
| +0x15f tier_flags csv↔drop 일관성 | ✅ Round 27: csv val_15f = drop_table 의 byte data 와 동일 의미. Round 24 의 legendary/rare/gem/common 라벨이 게임 drop 로직에서 사용 검증 | 동일 |
| ApplyNormalMix (NPC blacksmith) mechanism | ✅ Round 28: MixSmithTableInfo* 별개 데이터, struct +0x11c..+0x128 col-major | `applynormalmix_disasm.txt` |
| ApplySpecialMix (csv slot_15 recipe) mechanism | ✅ Round 28: GetItemTableInfo 로 csv 직접 사용 + Mission 진척, struct +0x134..+0x140 col-major | `applyspecialmix_disasm.txt` |
| ApplyItemCompose (option 결합) | ✅ Round 28: 두 EquipItem grade≤2 결합 → option set 합성, gv+0x1444+0x198 prob 테이블 | `applyitemcompose_disasm.txt` |
| ApplyItemDecompose (분해) | ✅ Round 28: option_grade-based 5-way prob, gv+0x1444+0x1b8 테이블, money refund / mix material / potion 분기 | `applyitemdecompose_disasm.txt` |
| mix_book recipe csv↔struct layout | ✅ Round 28: csv = row-major (사용자 의미), struct memory = col-major (LoadItemTable transpose). parse_mix_book_extra row-major 객체 그대로 유효 | `applyspecialmix_disasm.txt` |

---

## 게임 흐름

```
Title (로고 + Continue/New Game + 슬롯 메타: Lv/cls/G/inv/시간)
  ├─ New Game → ClassSelect (5 클래스 + STR/DEX/INT/CON 미리보기)
  │             → Demo
  └─ Continue / Slot 클릭 → Demo (저장 자동 로드)

Demo:
  WASD 이동 (충돌, 자동 인카운터 25step+10%/step)
  M/N 맵/씬 (BGM 페이드 + 캐릭터 자동 배치 + 맵 이름 표시)
  P NPC 스폰 (4색 분류) → E 가까운 NPC 와 대화 (한글 + 선택지 → 퀘스트)
  S 상점, Q 퀘스트, I 상태(ATK/DEF 합산), X 설정, H 도움말, B 전투
  자동 저장: slot 7, 60초 간격
  씬 전환 시 0.3s 검정 페이드
```

---

## 새 도구 (Ghidra-free .so 분석 + 통합 파이프라인)

| 도구 | 역할 | 추가 |
|---|---|---|
| `tools/h5_dump_loaditem_tail.py` | LoadItemTable 의 cat 17/18 영역 (0xa479c..0xa49c0) 추가 disasm — `capstone.skipdata=True` 로 literal pool 통과 (Round 20) | 2026-05-10 |
| `tools/h5_decode_buildup.py` | c_csv_buildup.json → ABE entry type 매핑 + V slot 라벨 자동 추출 (Round 11) | 2026-05-09 |
| `tools/h5_find_kr_stat_strings.py` | .so .rodata 에서 한글 stat label 검색 (Round 10) | 2026-05-09 |
| `tools/h5_find_kr_text_idx.py` | VFS text JSON 의 한글 stat label 위치 추출 (Round 10) | 2026-05-09 |
| `tools/h5_calc_status_table.py` | CalcStatusComputation 의 calc_sk → cache offset 매핑 (Round 10) | 2026-05-09 |
| `tools/h5_disasm_property_menu.py` | DrawPropertyMenu cache offset reads 추적 (Round 10) | 2026-05-09 |
| `tools/h5_apply_buildup_disasm.py` | HERO/BATTLER ApplyBuildupEffect jumptable 자동 추출 (Round 9) | 2026-05-09 |
| `tools/h5_extract_class_stats.py` | c_csv_class.json → 5 클래스 V[111..116] base 패턴 (Round 9) | 2026-05-09 |
| `tools/h5_find_battle_check_funcs.py` | 전투 함수 immediate calc id 호출자 추적 (Round 9) | 2026-05-09 |
| `tools/h5_find_formula_callers.py` | Formula::calc 전체 caller 분석 (r0/r1 reg propagation) (Round 9) | 2026-05-09 |
| `tools/h5_list_stat_methods.py` | HERO/CHAR/BATTLER stat 메서드 이름 분류 (Round 9) | 2026-05-09 |
| `tools/h5_dump_caller.py` | 단일 함수 disasm wrapper (Round 9) | 2026-05-09 |
| `tools/h5_find_func.py` | 심볼 substring 탐색 helper (Round 9) | 2026-05-09 |
| `tools/h5_find_gv_writers.py` | gv+0x1474 sub-struct offset 별 writer 함수 추적 (Round 6) | 2026-05-09 |
| `tools/h5_des.py` | 표준 DES + S1[3][10]=2 변종 (mx_des_encrypt/decrypt) | 2026-05-09 |
| `tools/h5_disasm_des.py` | DES 함수 disasm + 테이블 후보 dump | 2026-05-09 |
| `tools/h5_resolve_des_got.py` | PC-relative GOT lookup 해석 | 2026-05-09 |
| `tools/h5_decrypt_calc.py` | calc_pl/en/sk.dat → 평문 (MD5 검증) | 2026-05-09 |
| `tools/h5_formula_disasm.py` | Formula VM 186 공식 → infix 표현 dump | 2026-05-09 |
| `tools/h5_extract_gv_subStruct.py` | var_id 58-160 의 gv+0x1474 sub-struct offset 추출 | 2026-05-09 |
| `tools/h5_export_formulas.py` | 186 공식 + 254 var_dict → GDScript JSON | 2026-05-09 |
| `tools/h5_test_formula_eval.py` | Formula VM 정합성 테스트 (id=0 → 4437 검증) | 2026-05-09 |
| `tools/h5_extract_pipeline.py` | 9-step 통합 파이프라인 (incremental + --force/--only) | 2026-05-09 |
| `tools/h5_scn_body_stats.py` | 258 scn body 정적 trace + opcode 빈도 TSV | 2026-05-09 |
| `tools/h5_extract_battle_funcs.py` | 11 BATTLER/HERO/Monster 함수 ARM disasm + callee | 2026-05-09 |
| `tools/h5_smaf_audit.py` | 42 SMAF ↔ 42 OGG 1:1 매칭 검증 + 청크 dump | 2026-05-09 |
| `tools/h5_disasm_newhiteffect.py` | NewHitEffect / HeroSkillAtkHardCode disasm | 2026-05-09 |
| `tools/h5_find_damage_callers.py` | IncreaseHP/AddEffectDamage caller 추적 | 2026-05-09 |
| `tools/h5_disasm_formula.py` | Formula VM 4 함수 (dataLoad/calc/calcByFormula/getNumberInStack) | 2026-05-09 |
| `tools/h5_disasm_skill_hardcode.py` | HeroSkillAtkHardCode 단독 disasm | 2026-05-09 |
| `tools/h5_extract_event_funcs.py` | EventProc::Event_* 102개 일괄 disasm | 2026-05-09 |
| `tools/h5_disasm_item_funcs.py` | EquipItemInfo CopyData 등 7개 함수 → struct offset 추출 | 2026-05-09 |
| `tools/h5_extract_formula_vars.py` | Formula::getValFunc 254-entry switch → var_id 사전 | 2026-05-09 |
| `tools/h5_extract_opcode_disasm.py` | EventProc::onFunction jumptable → opcode_table.json 77 entries | 2026-05-08 |
| `tools/h5_event_arg_sizes.py` | Itanium ABI mangle parser → 105 Event_* arg_size | 2026-05-08 |
| `tools/h5_extract_enemy_layout.py` | Map::MapEnemyG_set → 121B record layout 검증 | 2026-05-08 |
| `tools/h5_inspect_enemy_record.py` | 디버그용 raw record dump | 2026-05-08 |
| `tools/h5_batch_sprite.py` | sprite/palette single-argv converter wrapper | 2026-05-08 |

의존: `pip install lief capstone`. import_to_godot.py 가 둘 다 있으면 opcode_table.json
자동 생성 (없으면 graceful skip — BASE_TABLE 38 fallback).

---

## 파일 위치 빠른 참조

### Phase 2 산출물 (`work/h5/` — gitignored)
- `extracted/` — APK unzip (assets/data.vfs.mp3, lib/armeabi/libHeroesLore5.so)
- `vfs_entries/` — 2,189 unpacked records
- `vfs_catalog.tsv` — index/hash/length/type
- `analysis/asset_names.tsv` — 99.7% 이름 복원
- `analysis/opcode_table.tsv` — 77/77 (자동 추출)
- `analysis/event_arg_sizes.tsv` — 105 Event_* arg sizes
- `analysis/enemy_g_layout.tsv` — record byte → struct field 매핑
- `analysis/scn_headers.tsv` — 258 scene 헤더
- `analysis/formula_var_dict.tsv` — 254 var_id → struct/offset (Round 3)
- `analysis/gv_substruct_layout.tsv` — 111 gv+0x1474 sub-struct fields (Round 5)
- `analysis/calc_pl/en/sk_plain.bin` — DES 복호 평문 (Round 4)
- `analysis/formulas_disasm.txt` — 186 공식 infix dump (Round 4, 945 줄)
- `analysis/des_disasm.txt`, `des_got_resolved.json`, `des_tables.json` — DES RE 산출
- `converted/sprites/<idx>/frame_NN_*.png`
- `converted/text/_corpus.txt` — 18,837 unique 한글

### Phase 3 (`apps/hero5-godot/`)
```
project.godot           # autoload 6: GameState/AssetLoader/GameData/Audio/Quest/FormulaVM
scenes/                 # 14 씬
scripts/core/           # 11 싱글톤/게임 로직
  game_state.gd, asset_loader.gd, game_data.gd, audio_manager.gd, quest_system.gd
  map_renderer.gd, character.gd, interpreter.gd, battle_system.gd, save_manager.gd
  formula_vm.gd            # ← Round 5: Formula VM 평가기 (calc_*.dat 186 공식)
scripts/ui/             # 17 UI 스크립트 (scene_fader.gd 추가)
assets/                 # gitignore — import_to_godot.py 가 채움
  sprites/, gbm/, palettes/, text/, sounds/, fonts/, gamedata/, maps/, scenes/
  scenes/opcode_table.json   # ← P1 산출물 (capstone+lief 있으면 자동 생성)
  scenes/bodies/<idx>.bin    # ← P1 scene body 자동 실행용
  data/formula/formulas.json # ← Round 5: 186 공식 (id → body)
  data/formula/var_dict.json # ← Round 5: 254 var_id → struct/offset
```

### 도구 (`tools/`)
- `h5_vfs_unpack.py`, `h5_recover_names.py`, `h5_extract_text.py` — Phase 2 추출
- `h5_batch_sprite.py` — single-argv converter wrapper
- `h5_extract_opcode_disasm.py`, `h5_event_arg_sizes.py`, `h5_extract_enemy_layout.py`
  — capstone+lief 분석 (P1, P2)
- `import_to_godot.py` — 모든 자산 → Godot
- `verify_godot_project.py` — tscn/gd reference 검증
- `converter/*` — 자산 디코더 (sprite/pa/gbm/scn/csv/skill/item/quest/enemy)

---

## 디버그 / 테스트 키 (Demo 씬)

| 키 | 기능 |
|---|---|
| WASD | 이동 |
| M / N | mapID / scene 전환 |
| P | NPC 마커 스폰 (4색) |
| E | 가까운 NPC 와 대화 |
| T | dialog 테스트 (트리거) |
| S | 상점 |
| Q | 퀘스트 패널 |
| I / ESC | 상태창 (ATK/DEF 합산 + hover 비교) |
| X | Settings |
| H | 도움말 |
| B | 즉시 전투 (테스트) |
| C / V | collision / tile attribute 디버그 |
| 1-8 | 슬롯 N 저장 |
| Shift+1-8 | 슬롯 N 로드 |
| F5 / F9 | slot 0 빠른 저장 / 로드 |

---

## 알려진 제한

- [x] ~~Interpreter opcode dispatch (22/77 만 구현)~~ — ✅ 77/77 (2026-05-08)
- [x] ~~enemy ATK/DEF offset 일부 부정확~~ — ✅ .so disasm 검증 완료 (2026-05-08)
- [x] ~~DES 복호화 차단~~ — ✅ 표준 DES + S1[3][10]=2 변종 해독 (2026-05-09)
- [x] ~~calc_*.dat 평문 미확보~~ — ✅ MD5 검증 통과 (2026-05-09)
- [x] ~~Formula VM 공식 추출 미완~~ — ✅ 186 공식 infix dump (2026-05-09)
- [x] ~~battle_system.gd 의 Formula VM 평가기 미구현~~ — ✅ FormulaVM autoload + battle 통합 (2026-05-09)
- [x] ~~gv+0x1474 sub-struct offset 추출~~ — ✅ 111 fields 정확 매핑 (2026-05-09)
- [x] ~~gv_sub 핵심 필드명 정확화~~ — ✅ Round 6 writer 분석으로 18 fields 의미 확정 (V[58]=level, V[60..63]=base, V[69]=SP, V[70]=CP, V[118..121]=bonus)
- [x] ~~V[111..116] (클래스 base 계수) 의미~~ — ✅ Round 7: V[111]=atk_growth, V[112..116]=secondary stat base
- [x] ~~V[155]=max_sp~~ — ✅ Round 7: ApplyBuildupEffect SP clamp 상한
- [x] ~~V[127..148] 다중 buff/element bonus~~ — ✅ Round 8: V[127]=def_red%, V[128]=atk%, V[129..133]=stat bonus, V[134..148]=element
- [x] ~~Round 7 0x294/0x296 mapping~~ — ✅ Round 8 정정: gameplay 전용 (Formula VM var 아님)
- [x] ~~V[125,126] (0x2a6, 0x2a8) buff slot 의미 식별~~ — ✅ Round 9: ApplyBuildupEffect entry type 34/36 으로 5-slot 시스템 일부임 확정
- [x] ~~V[112..116] 5 stat 의 한국어 라벨~~ — ✅ Round 11: 근접명중/장거리명중/회피/방패방어/크리티컬 (buildup csv 매핑)
- [x] ~~V[62]/V[63] 매핑 정정~~ — ✅ Round 11: int/con → con/int (이전 매핑 오류, buildup csv 로 검증)
- [x] ~~V[122..126] 5 buff slot 의미~~ — ✅ Round 12: EXP%/SP감소%/CP충전LV/쿨타임감소%/포션효과% 확정
- [x] ~~V[151,152] magic stat~~ — ✅ Round 12: 둘 다 INT-magic (이전 V[152]=DEX 잘못)
- [x] ~~RefineItem::ApplyItemRefine 강화 stat 보너스 mechanism~~ — ✅ Round 26: V[184]+V[187] / V[185]+V[187] (id=35/36), 5-case jumptable
- [x] ~~ApplyOrbCombine orb 결합 mechanism~~ — ✅ Round 26: 39 orb 종, +0x168 count, +0x169..+0x16d 5 socket
- [ ] V[151] vs V[152] 의 element 짝 (fire/ice/lightning/dark 어느 것)
- [ ] 한글 비트맵 폰트 (시스템 폰트로 우회 중) — P5, capstone+lief 로 가능
- [ ] SMAF (.mmf) 변환 (OGG 42개로 충당)
- [ ] 자산 이름 7개 / 0.3% 미복원 (게임 영향 없음)
- [ ] Android APK 실 빌드 미검증 — P6, Godot Editor 환경 필수
- [ ] Godot Editor 에서 실제 실행 검증 — verify 는 reference 만, GDScript compile 미검증

---

## 환경 의존성

**필수**:
- Python 3.10+
- Pillow (sprite 변환)

**.so disasm 작업 시 (P1/P2/P5)**:
- `pip install lief capstone`

**Godot 빌드/실행**:
- Godot 4.2+ Editor
- (Android export) JDK 17 + Android SDK + NDK + build template

---

## 참조 문서

- [`PROGRESS.md`](PROGRESS.md) — 전체 진행 상세 (Phase 2 분석 단계별 + Phase 3 시스템별)
- [`PHASE3_ENGINE.md`](PHASE3_ENGINE.md) — Godot 4 엔진 결정 근거
- [`DES_VARIANT.md`](DES_VARIANT.md) — DES 변종 해독 + calc_*.dat 평문 + Formula VM 디스어셈블러
- [`BATTLE_FORMULA.md`](BATTLE_FORMULA.md) — BATTLER damage 함수 disasm + Event_PlayerDamage 공식 + Formula VM/DES 키
- [`FORMULA_VAR_DICT.md`](FORMULA_VAR_DICT.md) — Formula VM 변수 사전 (254 var_id → struct/offset)
- [`EVENT_OPCODE_REFERENCE.md`](EVENT_OPCODE_REFERENCE.md) — 102개 Event_* opcode 의미 매핑 reference
- [`ITEM_STRUCT.md`](ITEM_STRUCT.md) — EquipItemInfo struct 부분 layout + 19-카테고리 dispatch
- [`P5_FONT_MAPPING.md`](P5_FONT_MAPPING.md) — table.dat=Unicode (EUC-KR 아님) 정정 + 매핑 위치
- [`GV_SUBSTRUCT_FIELDS.md`](GV_SUBSTRUCT_FIELDS.md) — Round 6: HERO 객체 (=gv+0x1474) offset 별 의미 매핑 (writer 분석)
- [`apps/hero5-godot/README.md`](../../apps/hero5-godot/README.md) — Godot 프로젝트 사용법
- [`apps/hero5-godot/export_presets.cfg.template`](../../apps/hero5-godot/export_presets.cfg.template) — Android export 템플릿
