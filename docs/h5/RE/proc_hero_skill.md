# HERO::ProcHeroSkill (@0x99278, 7972B) — 골격 RE 결과 (Round 70)

> R69 에서 `HERO::ProcHeroSkill(HeroSkillInfo*)` 가 `ChangeAttackMotion` 의 유일
> 호출자임을 확인 (offset +0x488 = 0x99700). 본 라운드는 7972B 거대 함수의
> **고수준 골격** + entry sequence + 2 jumptable + helper 호출 그래프 +
> HeroSkillInfo struct field 매핑까지 확정. 각 jumptable case 의 정밀 동작은
> 후속 라운드 (R71+).

## 1. 함수 개요

- 서명: `void HERO::ProcHeroSkill(HeroSkillInfo* skill_info)`
- 위치: 0x99278..0x9b1bc (7972B, ARM mode)
- 총 ARM instruction: **1993개**
- 호출 그래프 진입: skill use frame 마다 호출 (R63 의 SPACE 키 공격 / R67 의 SetAttackMotion 후속 trigger 추정)

## 2. Entry sequence (+0x0..+0x80)

```cpp
void HERO::ProcHeroSkill(this, HeroSkillInfo* skill_info)
{
    // 1. 전역 plain state clear (gv+0x1440+0x60c = 0)
    push {r4-r8, sb, sl, fp, lr};
    *(GOT_base + 0x1440 + 0x60c) = 0;

    // 2. 3-step attack property reset
    HERO::__sub_88f74(this);   // ResetCurAtkProperty?
    HERO::__sub_88fd4(this);   // EndApplyAtkAddEff?
    HERO::__sub_89034(this);   // ResetAtkBuff?

    // 3. 59-iter skill slot 초기화: HERO+0x348 + i*0x58, i ∈ [0, 0x3b)
    // 59 slots × 88B = 5192B skill instance array
    for (int i = 0; i < 0x3b; i++) {
        sub_d8d54(&this->skill_slots[i]);   // HeroSkillInfo::ResetSlot?
    }

    // 4. NULL guard
    if (skill_info == NULL) goto exit_path;  // 0x995dc

    // 5. class dispatch — class 2 (GUNNER) 별도 path
    if (this->class_id == 2) goto class2_gunner_path;  // 0x9a564

    // 6. 메인 처리 (0x992f8 부터, 다른 클래스)
    ...
}
```

핵심 발견:
- **HERO+0x348 부터 59 slots × 88B = HeroSkillInfo 배열** (전체 5192B 영역).
  R57 의 GameState.skill_levels dict 에 대응 — `_ai_runtime` 또는 inventory 의
  active skill 배열일 가능성. R71 에서 LoadSkillTable cross-ref 로 확정 필요.
- **class 2 (건슬링어) 별도 path** — class 0/3 (워리어/나이트) 가 R69 ChangeAttackMotion
  에서 active 였던 것과 대조. ProcHeroSkill 은 class 2 도 active 처리 (R22 의
  Sorcerer 만 stub).

## 3. Jumptable 2개

### Jumptable 1 @ 0x9a398 — Skill effect type dispatch (5-way)

직전 sequence (0x9a384..0x9a394):
```arm
0009a384: bl       #0x143c98          ; r0 = StaticUtil::Rand(0, formula_max)
0009a388: cmp      r7, r0             ; r7 = 이전 Formula::calc 결과 (hit chance?)
0009a38c: ble      #0x99978           ; if hit < rand → goto no_hit (case 0 alias)
0009a390: ldrsb    r3, [r6, #0x28]    ; r3 = skill_info[+0x28] (signed byte)
0009a394: cmp      r3, #4
0009a398: addls    pc, pc, r3, lsl #2 ; jumptable dispatch
```

**dispatch key = `skill_info[+0x28]` (signed byte, 0..4) = skill effect type**:

| case | target | 의미 추정 |
|:---:|:---:|---|
| 0 | 0x99978 | NO_HIT / SKIP (hit chance 실패와 동일 path) |
| 1 | 0x9ac68 | EFFECT_TYPE_1 (예: physical damage) |
| 2 | 0x9ac68 | EFFECT_TYPE_2 (case 1 과 동일 path) |
| 3 | 0x9abfc | EFFECT_TYPE_3 (예: magic damage) |
| 4 | 0x9ab98 | EFFECT_TYPE_4 (예: heal/buff) |
| 5 (≤4 fallthrough = case 5) | 0x9abfc | EFFECT_TYPE_5 (case 3 와 동일) |
| >4 (default) | 0x9a3b4 | 추가 dispatch — GetCurActSkillIdx 0x5/0x9 검사 |

기존 5-way 이지만 표 entry 가 6개 (case 0..5 명시 + 6th = default fallthrough). 즉 `cmp r3, #4` + addls 시 r3≤4 일 때만 jumptable, r3 > 4 면 case 5 entry 도 미실행하고 next instr 로.

### Jumptable 2 @ 0x9a8d8 — Active skill slot dispatch (7-way)

직전 sequence (0x9a8c4..0x9a8d4):
```arm
0009a8c4: mov      r0, r4
0009a8c8: bl       #0x88c9c           ; r0 = HERO::GetCurActSkillIdx()
0009a8cc: lsl      r3, r0, #0x18      ; sign-extend (signed byte)
0009a8d0: asr      r3, r3, #0x18
0009a8d4: cmp      r3, #6
0009a8d8: addls    pc, pc, r3, lsl #2
```

**dispatch key = `HERO::GetCurActSkillIdx()` 반환값 (0..6) = active skill slot index** (총 7 slots):

| case | target | 의미 추정 |
|:---:|:---:|---|
| 0 | 0x99904 | slot 0 (기본 공격?) |
| 1 | 0x9ad78 | slot 1 (skill A) |
| 2 | 0x99904 | slot 2 (slot 0 alias — 기본 공격류 추가 case) |
| 3 | 0x9acf8 | slot 3 (skill B) |
| 4 | 0x99904 | slot 4 (slot 0 alias) |
| 5 | 0x9aa18 | slot 5 (skill C) |
| 6 | 0x99904 | slot 6 (slot 0 alias) |
| 7 (default) | 0x9ad78 | slot 7 (= case 1 alias) |

즉 odd skill slots (1, 3, 5, 7) 만 별도 path, even slots (0, 2, 4, 6) 는 공통
"기본 공격" path. R57 의 7+1 active skill 시스템과 일치.

## 4. ChangeAttackMotion 호출 context (offset +0x488 = 0x99700)

```arm
; --- pre-call: Formula::calc(0x6f, this, NULL, skill_info, NULL) ---
000996c0: beq      #0x996f8                ; conditional skip
000996c4-d8: Formula::calc 인자 셋업 (formula_id = 0x6f = 111)
000996dc: bl       #0x7749c                ; r0 = Formula::calc(0x6f, ...)
000996e0-e4: r1 = signed halfword of result
000996e8: cmp      r1, #0
000996ec: ble      #0x996f8                ; if result ≤ 0 → skip 0x89068 call

000996f0: mov      r0, r4                  ; (only when result > 0)
000996f4: bl       #0x89068                ; HERO::__sub_89068(this) — hit registered?

; --- ChangeAttackMotion call ---
000996f8: mov      r0, r4                  ; r0 = this (HERO*)
000996fc: mov      r1, r6                  ; r1 = skill_info
00099700: bl       #0x91e7c                ; ★ HERO::ChangeAttackMotion(this, skill_info)

; --- post-call: gv+0x19c hp/sp/level cap check ---
00099704: ldr      r3, [r5, #-0x190]       ; r3 = ptr from r5 base
00099708: mov      r2, #0x19c
0009970c: ldrsh    r2, [r3, r2]            ; r2 = *(r3 + 0x19c) (s16)
00099710: cmp      r2, #0x63               ; compare 99
00099714: bgt      #0x995e4                ; > 99 → exit_path

; --- next: Formula::calc(0x63, this, skill_info_byte_2a, ...) ---
00099718: ldr      r0, [r8, sl]            ; GOT load
0009971c: ldrsb    r1, [r6, #0x2a]         ; r1 = skill_info[+0x2a] (signed byte)
00099728: mov      r2, r4
0009972c: stm      sp, {r6, r7}            ; stack args = (skill_info, 0)
00099730: bl       #0x7749c                ; Formula::calc(formula_id_from_GOT, ...)
00099734: mov      r1, #0x63               ; r1 = 99 (level cap?)
...
```

핵심 발견:
- **ChangeAttackMotion 호출은 Formula::calc(0x6f) 의 hit check 결과 후**. Formula 0x6f
  (111) 가 양수면 추가 hit effect (`__sub_89068`) 등록.
- ChangeAttackMotion 직후 **gv struct +0x19c (s16) > 99 면 함수 exit**. 99 = level cap
  추정 (Round 22 의 max level 92 와 일치하는 일반적 cap).
- 다음 Formula::calc 호출은 `skill_info[+0x2a]` 를 인자 r1 로 전달 — 이는 R69 의
  HEROSkillInfo+0x44 (knockback_idx) 와는 다른 field.

## 5. HeroSkillInfo struct field 매핑 (R70 신규)

ProcHeroSkill 안의 r6 = skill_info backup. r6 의 ldr* 패턴 추출:

| offset | type | 빈도 | 의미 추정 |
|---:|---|---:|---|
| +0x0a | s8 | 5 | skill flag/mode byte |
| +0x1c | s8/u8 | 3 | mixed access — skill mode 또는 group |
| +0x1d | s8 | 1 | secondary mode byte |
| +0x28 | s8 | 1 | **★ skill effect type** (Jumptable 1 dispatch key, 0..4) |
| +0x29 | s8 | 3 | secondary effect type |
| +0x2a | s8 | 1 | **Formula::calc 인자 #1** (위 0x9971c 에서 ldrsb) |
| +0x2b | s8 | 1 | adjacent byte |
| +0x2f | s8 | 3 | skill behavior flag |
| +0x30 | s8 | **8** | **★ skill behavior code** (자주 분기됨) |
| +0x32 | u16 | 3 | value field |
| +0x34 | u16 | **8** | **★ skill primary value** |
| +0x36 | u16 | 3 | value field |
| +0x38 | u16 | **8** | **★ skill secondary value** |
| +0x3a | s8 | 4 | sub flag |
| +0x3b | s8 | 1 | Formula::calc 인자 (위 0x9a368) |
| +0x3c | s8 | 3 | flag |
| +0x3d | s8 | 3 | flag |
| +0x44 | s8 | — | **knockback_idx** (R69 확정) |
| +0x45 | s8 | 1 | adjacent |
| +0x46 | s8 | 3 | secondary KB? |
| +0x48 | s16 | 4 | range/distance? |
| +0x4a | s16 | 1 | range |
| +0x4c | s16 | 1 | range |
| +0x4e | s8 | 1 | flag |
| +0x50 | s16 | 1 | range/value |

추정 struct (R69 + R70 종합):
```cpp
struct HeroSkillInfo {  // 88B = 0x58 entry (entry loop size 일치)
    char  flag_0a;          // +0x0a
    // ...
    char  mode_1c;          // +0x1c
    char  mode_1d;          // +0x1d
    // ...
    char  effect_type;      // +0x28  — Jumptable 1 key (0..4)
    char  effect_type_2;    // +0x29
    char  formula_arg_2a;   // +0x2a
    char  flag_2b;          // +0x2b
    // ...
    char  flag_2f;
    char  behavior_30;      // +0x30  — 자주 분기
    char  _pad;
    u16   value_32;         // +0x32
    u16   primary_value;    // +0x34  ★
    u16   value_36;         // +0x36
    u16   secondary_value;  // +0x38  ★
    char  flags_3a[4];      // +0x3a..+0x3d
    // ...
    char  knockback_idx;    // +0x44 (R69)
    char  flag_45;
    char  flag_46;
    char  _pad;
    s16   range_48;         // +0x48
    s16   range_4a;
    s16   range_4c;
    char  flag_4e;
    char  _pad;
    s16   value_50;         // +0x50
    // ... 더 있을 가능성 (struct size = 88B = 0x58, 위 매핑은 +0x52 까지)
};
```

## 6. 외부 helper 호출 그래프 (top 20)

| 주소 | 빈도 | 심볼 | 의미 |
|---:|---:|---|---|
| 0x7749c | **27** | `Formula::calc(int, CHAR*, CHAR*, HeroSkillInfo*, ItemBase*)` | **Formula VM 진입점** (Round 5 의 186 공식) |
| 0x49b6c | 22 | `CHAR::GetSpritePtr()` | sprite anim 데이터 |
| 0xda51c | 22 | `SPRITE::GetExtraDataPtr()` | sprite extra data |
| 0x88c9c | 18 | `HERO::GetCurActSkillIdx()` | **active skill slot index** (Jumptable 2 key) |
| 0xcfd8c | 14 | `OBJECT::GetX()` | x 좌표 |
| 0xcfd9c | 14 | `OBJECT::GetY()` | y 좌표 |
| 0x7457c | 11 | `ExtraData::GetPivotX()` | sprite pivot x |
| 0x7458c | 11 | `ExtraData::GetPivotY()` | sprite pivot y |
| 0x62d40 | **11** | `TargetEffectMgr::NewTargetEffect(char, int, HeroSkillInfo*, SPRITE*, char, char, char, char, short, int, int)` | **skill VFX 생성** |
| 0x4b41c | 10 | `BATTLER::IncreaseHP(int)` | HP 변경 (heal/damage) |
| 0x1536c4 | 10 | `__divsi3` | signed div32 (compiler intrinsic) |
| 0x8c258 | 9 | `UiTargetMonster::SetBattler(BATTLER*, char)` | UI target 표시 |
| 0x88cf8 | 8 | `HERO::GetTempAtkProPtr()` | 임시 AttackProperty 포인터 |
| 0x74538 | 8 | `AttackProperty::GetHitType()` | hit type (0=miss, 1=normal, 2=critical 등) |
| 0x49b74 | 7 | `CHAR::GetMotion()` | 현재 motion (R67 와 일치) |
| 0x143c98 | 7 | `StaticUtil::Rand(int, int)` | 난수 (jumptable 1 직전 hit roll) |
| 0x88e2c | 5 | `HERO::IncreaseSP(int)` | SP 변경 |
| 0x88ed4 | 4 | `HERO::IncreaseHiperCount()` | 하이퍼 카운트 |
| 0x4bdb4 | 3 | `BATTLER::ApplyAddEffect(char, short, HeroSkillInfo*)` | buff/debuff effect 적용 |
| 0x89448 | 3 | `HERO::CheckEffSound_Hit(char)` | hit 사운드 |

핵심 호출 chain:
1. **Hit check**: `Formula::calc(0x6f) → Rand → cmp` → hit 여부 판정
2. **Damage**: `Formula::calc(damage_formula) → BATTLER::IncreaseHP(-damage)` (10회)
3. **VFX**: `TargetEffectMgr::NewTargetEffect(...)` (11회) — skill effect sprite 생성
4. **UI update**: `UiTargetMonster::SetBattler(...)` (9회) — 타겟 박스 갱신
5. **Buff/Debuff**: `BATTLER::ApplyAddEffect(...)` (3회)

## 7. HERO this (r4) field access 정리

| offset | 빈도 | 의미 |
|---:|---:|---|
| +0x22c | **16** | class_id (R43+R69 확정) |
| +0x269 | 8 | 보조 state byte (skill-related?) |
| +0x294 | 2 | skill state byte A |
| +0x295 | 1 | skill state byte B (adjacent) |
| +0x296 | 1 | skill state byte C (adjacent) |
| +0x25f | 1 | rare access |
| +0x284 | 1 | rare access |

+0x294..+0x296 cluster 는 skill use 시 3 byte state machine (예: combo step, cooldown
phase 등).

## 8. r5 의 의미 — 큰 struct 의 +0x190 base

ProcHeroSkill 안에서 `[r5, +-0x190]` ldr 가 **107회** 등장. 이는:
- r5 가 어떤 struct ptr 의 끝 + 0x190 위치를 base 로 잡아 음수 offset 으로 접근.
- 또는 r5 = (big_struct + 0x190), `[r5, -0x190]` = big_struct 시작 ptr.
- 모든 `[r5, -0x190]` 가 동일 ptr load 한다는 점에서 후자가 유력.

0x99704 의 `ldr r3, [r5, #-0x190]` → r3 = big_struct, 그 다음 `r3 + 0x19c` 의 s16
read. **big_struct + 0x19c = level cap field (99)**.

big_struct 가 무엇인지는 R71 에서 r5 setup 추적 필요. 후보:
- gv+0x1474 sub-struct (Round 6 의 111 fields, V[58..167] 영역)
- HERO+0x288 base (skill slot array 시작? 또는 그 외)

## 9. 잔여 미해결 (R71+)

1. **jumptable 1 의 5 case 정밀 동작** (skill effect type 0..4 별 damage 공식)
2. **jumptable 2 의 4 case 정밀 동작** (skill slot odd/even 별 path)
3. **Formula 0x6f (111) 의 의미** — Round 5 formula 매핑에서 cross-ref 필요
4. **Formula 0x63 (99) 의 의미** — level/SP/cooldown formula?
5. **r5 base 추적** — `[r5, -0x190]` 의 base 가 gv vs HERO+0x288 구분
6. **TargetEffectMgr::NewTargetEffect 11개 인자 의미** — skill VFX 시스템 구조
7. **class 2 (GUNNER) 별도 path** (@0x9a564) — 다른 클래스와 어떻게 다른가
8. **HERO+0x269 / +0x294..+0x296** 의미 — skill state machine 의 다음 단계

## 10. Godot 통합 권장 — 현재 라운드는 minimal

R70 은 거대 함수의 **골격** 만 매핑. Godot 의 character.gd 또는 battle_system.gd
에 새 동작을 추가하기엔 정보 부족. 다만:

- HeroSkillInfo struct **88B** 확정 (entry loop size 0x58 일치) — R71 의 GameData 확장 시 정확한 layout 적용 가능
- **active skill slot = 7개** (Jumptable 2 의 0..6 dispatch) — R57 의 GameState.skill_levels 와 일치
- **Formula::calc 27회 호출** = damage/hit/cooldown 계산이 모두 Round 5 의 Formula VM 으로 routing — R71 에서 Formula 0x6f/0x63 의미 확정 시 Godot battle_system 의 damage 공식 정확화 가능

본 라운드는 RE 문서만 산출, Godot 코드 변경 없음.

---

## 11. Formula::calc dispatch + r5 base 정밀 (Round 71)

### 11.1 Formula::calc (@0x7749c, 172B, 42 instr) 완전 RE

서명: `int Formula::calc(this, int id, CHAR* attacker, CHAR* defender, HeroSkillInfo* skill, ItemBase* item)`

```c
int Formula::calc(this, id, attacker, defender, skill, item)
{
    if (id < 0)            return 0;                  // sign 검사

    if (id < 0x3e8) {                                  // id 0..999
        // calc_pl 경로 (0x7751c)
        record = this->calc_pl_base[idx];              // ldr [r0, #8]
        idx = id - 0;                                  // calc_pl 의 idx = id 그대로
    } else if (id < 0x7d0) {                          // id 1000..1999
        // calc_en 경로 (0x77530)
        record = this->calc_en_base[idx];              // ldr [r0]
        idx = id - 1000;
    } else if (id <= 0xbb7) {                         // id 2000..3007
        // calc_sk 경로 (0x774e8)
        record = this->calc_sk_base[idx];              // ldr [r0, #4]
        idx = id - 2000;
    } else {
        return 0;                                      // id > 3007 → 0
    }

    return Formula::calcByFormula(this, idx, attacker, defender, skill, item);
}
```

**Formula struct (this) layout**:

| offset | 의미 |
|---:|---|
| +0x0 | calc_en base ptr (record array 시작) |
| +0x4 | calc_sk base ptr |
| +0x8 | calc_pl base ptr |

(분기 순서와 ldr offset 이 일치)

### 11.2 Formula 0x6f (111) / 0x63 (99) 의미 — production OOB

- **0x6f = 111**: calc_pl 범위 (< 1000). 그러나 production calc_pl 은 id 0..38 (39 entries) 만 정의 — `work/h5/analysis/formulas_disasm.txt` 확인.
- **0x63 = 99**: 동일, calc_pl OOB.
- 호출 결과: calcByFormula 가 invalid record 처리 → **return 0** (또는 lower_bound).
- ProcHeroSkill 의 hit check `cmp r1, #0; ble #0x996f8` 는 **production 에서 항상 true (taken)** → `bl #0x89068` (HERO::__sub_89068 = hit effect 등록) skip.
- **그러나 `bl #0x91e7c` (ChangeAttackMotion) 는 ble 분기 도착 후 무조건 실행** — 즉 hit check 가 dead path 라도 ChangeAttackMotion 은 actively 호출됨 (R69 의 호출자 확정과 모순 없음).

결론: Formula 0x6f / 0x63 호출은 historical artifact (개발 중 hit chance 시스템이 정해진 formula id 였으나 production data 에는 없음). ChangeAttackMotion 호출 흐름 자체는 unaffected.

### 11.3 r5 base 추적 — `[r5, -0x190]` = HERO + 0x1d3c

`work/h5/disasm_proc_hero_skill.txt` (PASS 1) 에서 `[r5, +-0x190]` ldr 가 **107회** 등장. r5 setup 추적 결과:

```arm
000993c8: mov      r3, #0x15c0
000993cc: add      r5, r4, #0x1ec0     ; r5 = this + 0x1ec0
000993d0: add      r3, r3, #0x14
000993d4: mov      r1, r5
000993d8: str      r3, [sp, #0x40]
000993dc: add      r5, r5, #0xc        ; r5 = this + 0x1ecc
```

즉 **r5 = HERO + 0x1ecc**. 따라서 `[r5, -0x190]` = HERO + 0x1ecc - 0x190 = **HERO + 0x1d3c**.

### 11.4 0x99700 ChangeAttackMotion 직후 level cap 검사

```arm
00099704: ldr      r3, [r5, #-0x190]   ; r3 = *(HERO + 0x1d3c) = some ptr (Monster*?)
00099708: mov      r2, #0x19c
0009970c: ldrsh    r2, [r3, r2]        ; r2 = *(r3 + 0x19c) (s16)
00099710: cmp      r2, #0x63           ; compare 99
00099714: bgt      #0x995e4            ; > 99 → exit_path
```

해석:
- **HERO + 0x1d3c = ptr** (Monster* 또는 BATTLER* 추정)
- `*(HERO+0x1d3c)+0x19c` (s16) > 99 시 함수 exit
- **level cap = 99** 확정 (R22 의 max level 92 + 일반 RPG cap 99 의 합리적 일치)
- HERO + 0x1d3c 가 R69 의 +0x1fb0 (current attack target) 과 동일한지 다른지 = R72 추적 필요. 둘은 다른 offset 이므로 별개 ptr 일 가능성 (예: 1d3c=last cast target / 1fb0=current AI target)

다른 r5 base 발견:
- 0x993cc: r5 = this + 0x1ec0 (+0xc 후 0x1ecc — 위 path)
- 0x99454: r5 = this + 0x1e00 (+4 후 0x1e04 — path 2)

즉 **r5 가 path 별로 다른 base** — 여러 sub-struct ptr 영역 (HERO+0x1c00~0x1f00 영역 = active skill processing context).

### 11.5 R71 → R72 잔여 작업

1. **Jumptable 1 의 5 case 정밀** (0x99978 NO_HIT / 0x9ac68 / 0x9abfc / 0x9ab98) — 각 case 의 damage 공식 path
2. **Jumptable 2 의 4 case 정밀** (0x99904 default / 0x9ad78 / 0x9acf8 / 0x9aa18) — active skill slot 별 path
3. **class 2 (GUNNER) 별도 path** @0x9a564 — R69 의 class 0/3 active 와 어떻게 다른가
4. **TargetEffectMgr::NewTargetEffect 11개 인자 의미** — skill VFX 시스템
5. **HERO + 0x1d3c vs +0x1fb0** 차이 분석 — last cast target vs current AI target?
6. **HERO + 0x1ecc 부터 0x1f0c 영역 의미** — active skill context struct?

---

## 12. Jumptable 1 의 5 case path + class 2 GUNNER entry (Round 72)

### 12.1 case 핵심 매핑

R72 zoom disasm (`work/h5/disasm_jt1_cases.txt`) 결과 — **각 case 가 다른 helper
함수를 호출하여 별도 효과 적용**:

| case | skill_info[+0x28] | target addr | helper 호출 | 의미 |
|:---:|:---:|:---:|---|---|
| 0 | 0 | 0x99978 | `HERO::IncreaseSP` (skill_info[+0x4a] s16) | **NO_HIT** — hit 실패 시도, SP 만 변경 |
| 1, 2 | 1·2 | 0x9ac68 | **`BATTLER::AddCurseSkill`** (@0x4b134) | **debuff/curse 적용** |
| 3, 5 | 3·5 | 0x9abfc | **`BATTLER::AddBuffSkill`** (@0x4b198) | **buff 적용** |
| 4 | 4 | 0x9ab98 | **`HERO::AddStanceSkill`** (@0x91d7c) | **stance (자세 스킬) 적용** |

**중요 정정**: R70 의 case 4 가설 "heal+buff" 는 부정확. 실제는 **stance 시스템**
— 자세 (Knight 의 방어 stance, Warrior 의 공격 stance 등) 또는 상태 변환 스킬.

### 12.2 모든 case 공통 패턴

case 1·2 / 3·5 / 4 는 모두 **2회 Formula::calc + helper 호출 + `b #0x99978`** 형식:

```arm
; case path 시작 (예: case 1+2)
ldr r0, [Formula_singleton]
ldrsb r1, [r6, #0x3c]          ; r1 = skill_info[+0x3c] (formula id 1)
mov r2, r4                      ; r2 = this (HERO*)
ldr r3, [r5, #-0x190]           ; r3 = *(HERO+0x1d3c) (target Monster*)
stm sp, {r6, fp}                ; stack args = (skill_info, NULL)
bl #0x7749c                     ; Formula::calc(formula_id_1, this, target, skill, NULL)
; → r0 = formula_1_result

ldrsb r1, [r6, #0x3d]          ; r1 = skill_info[+0x3d] (formula id 2)
mov r7 (or ip), r0              ; r7 = formula_1_result (저장)
bl #0x7749c                     ; Formula::calc(formula_id_2, ...)
; → r0 = formula_2_result

; case 별 helper 호출 (예: case 1+2 의 AddCurseSkill)
ldrsb r2, [r6, #0x3a]          ; r2 = skill_info[+0x3a] (special dispatch)
bl #0x4b134                     ; BATTLER::AddCurseSkill(this, ?, r2, formula_1, formula_2, ...)

b #0x99978                      ; 모두 NO_HIT path 합류 (SP 처리 + 공통 후처리)
```

### 12.3 case 0 (NO_HIT) 의 부가 동작

```arm
00099978: ldrsb r3, [r6, #0x1c]     ; r3 = skill_info[+0x1c]
0009997c: cmp r3, #0
00099980: bne 0x9a300                ; +0x1c != 0 → alternate path 0x9a300
00099984: ldrb r3, [r4, #0x294]     ; r3 = HERO[+0x294]
00099988: cmp r3, #0
0009998c: beq 0x999d8                ; +0x294 == 0 → skip detailed check

; +0x294 != 0 일 때 — self-target 검사
00099990: ldr r3, [r5, #-0x190]      ; r3 = *(HERO+0x1d3c) (current cast target)
00099994: cmp r4, r3
00099998: beq 0x999d8                ; target == self → skip

; secondary hit check
0009999c: ldrb r1, [r4, #0x295]     ; r1 = HERO[+0x295] (secondary formula id?)
000999b0..bc: Formula::calc(formula_id=r1) → r7
000999c0..cc: r0 = Rand(0, 99)
000999d0..d4: if r7 > r0 (Rand) → bgt 0x9a280 (extra path)

; SP 변경 (모든 case 의 합류점)
000999d8: mov r0, r4
000999dc: ldrsh r1, [r6, #0x4a]      ; r1 = skill_info[+0x4a] s16 (SP cost/heal)
000999e0: bl HERO::IncreaseSP

; class_id 분기
000999e4: ldrb r7, [r4, #0x22c]
000999f0: cmp r7, #1
000999f4: beq 0x9a0b0                 ; class 1 (ROGUE) 별도 path
```

### 12.4 case 1+2 의 special dispatch (skill_info[+0x3a])

```arm
0009acac: ldrsb r2, [r6, #0x3a]
0009acb0: cmp r2, #0x34              ; 52
0009acb4: beq 0x9b124                 ; 0x34 → special path A
0009acb8: cmp r2, #0x37               ; 55
0009acbc: beq 0x9b100                 ; 0x37 → special path B
; 둘 다 아니면 default AddCurseSkill 호출
```

skill_info[+0x3a] 가 0x34 (52) / 0x37 (55) 같이 특정 값일 때 curse 가 아닌 special
효과 path 로 분기. 실제 의미는 R73+ 추적 필요 (skill table cross-ref).

### 12.5 HeroSkillInfo 추가 field (R72)

R70 의 18+ field 에 **추가 6 field 확정**:

| offset | type | 의미 (R72 확정) | R70 추정 → R72 정정 |
|---:|---|---|---|
| +0x1c | s8 | **alternate path flag** (case 0 의 dispatch) | "skill mode/group" → 명확화 |
| +0x3a | s8 | **special dispatch byte** (case 1+2 의 cmp 0x34/0x37) | "skill behavior flag" → 정밀 |
| +0x3c | s8 | **Formula id 1** (damage/effect 계산) | "flag" → **formula id 확정** |
| +0x3d | s8 | **Formula id 2** (damage/effect 계산) | "flag" → **formula id 확정** |
| +0x45 | s8 | (case 1+2 의 0x9ad0c 에서 ldrsb [r6, #0x45], 추가 검사) | (R70 1회만) |
| +0x4a | s16 | **SP cost/heal** (case 0 의 IncreaseSP 인자) | "range" → **SP delta** |

### 12.6 HERO this 추가 field (R72)

| offset | type | 의미 (R72 확정) |
|---:|---|---|
| +0x294 | u8 | **skill state flag** (0 = standard, != 0 → secondary path) |
| +0x295 | u8 | **secondary formula id** (case 0 path 의 secondary hit check 용) |
| +0x269 | u8 | **GUNNER combo state** (class 2 path 에서 attack 배수 결정) |

R70 의 "+0x294-296 3-byte cluster" 가 **각 byte 별도 의미** 로 분해:
- +0x294 = skill state flag (case 0 의 secondary check 활성화 여부)
- +0x295 = secondary formula id (인자)
- +0x296 = (R72 미관측, R73 추적)

### 12.7 class 2 (GUNNER) entry @ 0x9a564

```cpp
// class_id == 2 일 때 도달 (R70 entry sequence 의 분기)
void gunner_skill_path(this, skill_info)
{
    int skill_idx = HERO::GetCurActSkillIdx();
    if ((int8_t)skill_idx != 5) goto 0x9a9bc;   // skill slot 5 가 아니면 별도 path

    // skill_idx == 5 (GUNNER 의 5번째 active skill, "combo shot" 추정)
    int16_t hero_248 = *(s16*)(this + 0x248);   // ammo count?
    int16_t skill_48 = skill_info[+0x48];        // s16 (max combo count?)
    if (hero_248 >= skill_48) goto 0x99300;     // 한도 도달 → skip

    // 3 field reset
    *(u16*)(this + 0x286) = 0;
    *(u16*)(this + 0x288) = 0;
    *(u8*)(this + 0x285) = 0;
    goto 0x9a824;   // 다음 단계
}

// 0x9a5ac 영역 (target 검사 후 GUNNER 데미지 공식)
{
    Monster* target = *(this + 0x1d3c);          // current cast target (R71)
    if (target->byte_0xf != 2) skip;             // target type 2 (?) 검사

    int8_t combo_state = this[+0x269];           // GUNNER combo state
    int dmg = (combo_state * 0x14 + 0x1e) * (something) / 0x64;
                                                  // = (combo * 20 + 30) * X / 100
    *(s16*)(fp + offset) = dmg;
}
```

**핵심 발견**:
- GUNNER 의 special skill (skill slot 5) 가 별도 path 사용 — combo shot 시스템
- **HERO+0x269 = GUNNER combo state** (0..N, 다중 hit 시 누적)
- GUNNER damage 공식: `(combo_state × 20 + 30) × target_param × multiplier / 100`
  - 즉 combo 1: 50% / combo 2: 70% / combo 3: 90% / combo 4: 110% — 매 hit 마다 +20% bonus
- HERO+0x248 (s16) = ammo or charge counter
- HeroSkillInfo+0x48 (s16) = max combo count (skill 별로 다름)

### 12.8 R72 → R73 잔여 작업

1. **Jumptable 2 의 4 case 정밀** (0x99904 / 0x9ad78 / 0x9acf8 / 0x9aa18) — active skill slot 별 path
2. **`TargetEffectMgr::NewTargetEffect` 11개 인자 의미** — skill VFX 시스템
3. **`BATTLER::AddCurseSkill` / `AddBuffSkill` / `HERO::AddStanceSkill`** 시그니처 정밀 (인자 의미)
4. **skill_info[+0x3a] 의 0x34/0x37 special path** — 어떤 special skill 인지 (skill table cross-ref)
5. **class 1 (ROGUE) 의 0x9a0b0 path** — case 0 의 class_id==1 분기
6. **alternate path 0x9a300** — skill_info[+0x1c] != 0 일 때
7. **HERO + 0x1ecc 부터 0x1f0c 영역 의미** — active skill context struct?
8. **HERO + 0x1d3c vs +0x1fb0** 차이 — last cast target vs current AI target?

---

## 13. Jumptable 2 의 4 case path (Round 73)

### 13.1 case 핵심 매핑

R73 zoom disasm (`work/h5/disasm_jt2_tem.txt`) 결과:

| case | GetCurActSkillIdx() | target addr | 의미 (R73 확정) |
|:---:|:---:|:---:|---|
| 0, 2, 4, 6 (alias) | 0/2/4/6 | 0x99904 | **기본 공격 (auto-attack)** — Formula 3 (HP) + Formula 4 (SP) |
| 1, 7 | 1, 7 | 0x9ad78 | **timestop + 기본 공격 chain** — SetTimestopFrame(2) 후 0x99908 합류 |
| 3 | 3 | 0x9acf8 | **class 3 (KNIGHT) secondary skill** — HERO+0x1d36==1 + orb check + 기본 공격 합류 |
| 5 | 5 | 0x9aa18 | **shock skill** — NewShockAddEffect + Formula[+0x30] dynamic id + IncreaseHP(damage) |

### 13.2 case 0/2/4/6 = 기본 공격 (auto-attack) @ 0x99904

```arm
00099904: ldr      r3, [r5, #-0x190]       ; r3 = *(HERO+0x1d3c) = target
00099908: ldr      r7, [r8, sl]            ; r7 = Formula_singleton ptr
0009990c: mov      r2, r4                  ; r2 = this (HERO)
00099910: mov      fp, #0
00099914: ldr      r0, [r7]                ; r0 = *Formula_singleton
00099918: mov      r1, #3                  ; r1 = formula_id = 3
0009991c: stm      sp, {r6, fp}            ; sp[0]=skill_info, sp[4]=NULL
00099920: bl       #0x7749c                ; Formula::calc(3, this, target, skill_info, NULL)
00099924: mov      r1, r0                  ; r1 = formula 3 result
00099928: mov      r0, r4                  ; r0 = this
0009992c: bl       #0x4b41c                ; BATTLER::IncreaseHP(r1)
                                            ; ★ 음수 → damage, 양수 → heal (보통 음수)

00099930: ldr      r3, [r5, #-0x190]       ; r3 = target
00099934: ldr      r0, [r7]                ; r0 = Formula
00099938: mov      r2, r4                  ; r2 = this
0009993c: mov      r1, #4                  ; r1 = formula_id = 4
00099940: stm      sp, {r6, fp}
00099944: bl       #0x7749c                ; Formula::calc(4, this, target, skill_info, NULL)
00099948: mov      r1, r0                  ; r1 = formula 4 result
0009994c: mov      r0, r4                  ; r0 = this
00099950: bl       #0x88e2c                ; HERO::IncreaseSP(r1)

; Class 3 KNIGHT 의 secondary skill 검사
00099954-58: r2 = 0x1d00 + 0x36 = 0x1d36
0009995c: r2 = ldrsb HERO[+0x1d36]
00099960: r3 = ldrsb skill_info[+0x4e]
00099964: cmp r2, r3
00099968: blt #0x999f8                      ; HERO+0x1d36 < skill_info[+0x4e] → 0x999f8

; secondary checks
0009996c: r3 = skill_info[+0x3a]
00099970: cmp #0
00099974: bne #0x9a360                      ; +0x3a != 0 → alt path 0x9a360

00099978: ... (R72 case 0 NO_HIT path 합류)
```

**Formula 3 / 4 의 실제 의미**:
- `calc_pl[3]` = `clamp(V[23], 0, 500)` — V[23] 변수 직접 fetch (Round 5 의 formula_disasm.txt)
- `calc_pl[4]` = `clamp((((V[6]+(((V[134]+V[135])/2)+V[151]))*(100+V[24]))/100), 0, 9999)`
  - V[6] = base_atk, V[134]/V[135] = magic_atk avg, V[151] = magic stat, V[24] = atk buff %
  - **= 기본 공격 damage 공식** (atk_base × buff%)

**즉 기본 공격 = (V[24] buff 가 적용된 atk × magic 보정) — `BATTLER::IncreaseHP(-damage)` 로 target HP 감소**.

### 13.3 case 1/7 = timestop + 기본 공격 chain @ 0x9ad78

```arm
0009ad78: ldr r0, [r5, #-0x190]    ; r0 = target
0009ad7c: mov r1, #2                ; r1 = 2 (frames)
0009ad80: bl  #0xcfde0               ; OBJECT::SetTimestopFrame(2)
0009ad84: ldr r3, [r5, #-0x190]
0009ad88: b   #0x99908               ; 기본 공격 path 의 Formula::calc 부분으로 합류
```

**= 시간정지 (2 frames) + 기본 공격 chain**. 타격 시 잠시 멈춤 효과 (Hero/Knight 의 special attack 추정).

### 13.4 case 3 = class 3 KNIGHT secondary skill @ 0x9acf8

```arm
0009acf8-04: r3 = ldrsb HERO[+0x1d36]    ; class 3 secondary flag (R69)
0009ad04: cmp #1
0009ad08: bne #0x99904                   ; != 1 → JT2 case 0 (기본 공격) 합류

0009ad0c: r3 = skill_info[+0x45]
0009ad10: cmp #0
0009ad14: bgt #0x9afc4                   ; > 0 → 다른 special path

0009ad18: r7 = target
0009ad1c-28: r3 = *((gv_struct + 0x1488))   ; some global ptr (EquipItem? Hero 의 equipped weapon?)
0009ad2c: r1 = *(r3 + 0x168)              ; +0x168 (R26 의 EquipItemInfo orb count!)
0009ad30: cmp r1, #0
0009ad34: ble #0x9ad70                   ; orb count == 0 → 합류

0009ad38-40: r3 = *(HERO + 0x1ecc)       ; HERO+0x1ecc (R71 의 r5 base 영역) load
0009ad44: cmp r3, #0
0009ad48-50: 분기 (loop entry / 직접 skip)

0009ad58-6c: array iterate loop (r1 = orb_count, r3 = counter, r2 = array ptr)
0009ad70: r3 = r7
0009ad74: b #0x99908                      ; 기본 공격 path 합류
```

**= class 3 (KNIGHT) 의 orb 기반 secondary skill**. EquipItem 의 socket orb 개수에
따라 추가 효과 (어떤 orb 인지 array iterate 로 검색), 결과적으로 기본 공격에 추가 효과 합산.

### 13.5 case 5 = shock skill @ 0x9aa18

```arm
0009aa18: r3 = skill_info[+0x46]          ; secondary KB count (R72) / shock count
0009aa1c: cmp #0
0009aa20: ble #0x99904                    ; <= 0 → 기본 공격 합류

; target 좌표 추출
0009aa24-2c: r7 = target.GetX()
0009aa30-38: r0 = target.GetY()
0009aa48: bl HERO::NewShockAddEffect(this, skill_info, target_x, target_y)
                                          ; ★ shock VFX 생성 (@0x8fc20)

; HeroSkillInfo +0x34/+0x38 (R70 primary/secondary value) 를 HERO 의 offset 영역에 저장
0009aa4c-54: HERO[+sp[0x50]] = skill_info[+0x34]   ; halfword
0009aa58-64: HERO[+0x1a8] = skill_info[+0x38]      ; halfword (R73 신규 field)

; Formula::calc(skill_info[+0x30] dynamic id, ...)
0009aa68-84: bl Formula::calc(r1=skill_info[+0x30], this, target, skill_info, NULL)
0009aa88: sp[0x48] = formula_result

; class_id == 2 (GUNNER) 분기
0009aa8c-90: r3 = HERO[+0x22c]
0009aa94: ldrne r7, [r5, #-0x190]         ; class != 2 → r7 = target
0009aa98: beq #0x9af88                    ; class == 2 → 다른 path

; damage 적용 (음수)
0009aa9c: lr = formula_result
0009aaa4: r1 = -formula_result            ; rsb r1, lr, #0
0009aaa8: bl BATTLER::IncreaseHP(r1)      ; HP 감소

; UI 업데이트
0009aaac-c0: UiTargetMonster::SetBattler(target, 1)
```

**= shock skill (skill_info[+0x46] count 가 0 보다 클 때만 작동)**:
- shock VFX 생성 (`HERO::NewShockAddEffect` @0x8fc20)
- **`skill_info[+0x30]` 가 dynamic Formula id** — R72 의 "behavior code" 추정 정확히 **formula id 로 사용**
- `Formula::calc(skill_info[+0x30])` 결과를 음수로 변환 → `BATTLER::IncreaseHP(-damage)`
- class 2 (GUNNER) 는 별도 path (0x9af88)

### 13.6 신규 발견 fields

**HeroSkillInfo +0x30 = dynamic Formula id** (R70 의 "behavior code" → R73 의 formula id 확정).
**HeroSkillInfo +0x46 = shock count** (case 5 dispatch).
**HeroSkillInfo +0x4e = class 3 secondary flag 임계값** (case 0/2/4/6 의 0x99960 검사).
**HERO + 0x1a8 (halfword)** = skill_info[+0x38] secondary value 저장 영역 (case 5).

### 13.7 JT2 cases 합류 흐름

모든 JT2 case 가 결국 `b #0x99908` 또는 `b #0x99904` 로 기본 공격 path 에 합류 →
Formula 3 (HP) + Formula 4 (SP) damage 적용. 즉 모든 active skill 사용 시 **기본
공격 damage 가 base** 이고, 각 case 의 special effect (timestop, shock, KNIGHT orb,
heal/stance buff) 가 추가됨.

---

## 14. TargetEffectMgr::NewTargetEffect (@0x62d40) — 11 호출 분석 (Round 73)

### 14.1 함수 시그니처

Mangled: `_ZN15TargetEffectMgr15NewTargetEffectEaiP13HeroSkillInfoP6SPRITEaaaasaii`

= `TargetEffectMgr::NewTargetEffect(this, char a, int b, HeroSkillInfo* skill, SPRITE* sprite, char c, char d, char e, char f, short s, int g, int h)`

ARM AAPCS 인자 배치:
- `r0` = this (TargetEffectMgr*)
- `r1` = char a (effect_type byte)
- `r2` = int b
- `r3` = HeroSkillInfo*
- `sp[0..3]` = SPRITE*
- `sp[4..7]` = char c
- `sp[8..11]` = char d
- `sp[12..15]` = char e
- `sp[16..19]` = char f
- `sp[20..23]` = short s
- `sp[24..27]` = int g
- `sp[28..31]` = int h

### 14.2 11 호출 위치 + effect_type (r1) 분포

| # | 호출 주소 | r1 = effect_type | sp[24] (int g) 셋업 |
|:---:|:---:|:---:|---|
| 1 | 0x995bc | **#4** | 1 |
| 2 | 0x9969c | **#7** | 1 |
| 3 | 0x99b08 | **#8** | 1 |
| 4 | 0x99e3c | **#7** | 1 |
| 5 | 0x99f8c | **#4** | 1 |
| 6 | 0x9a200 | **#4** | 1 (lr) |
| 7 | 0x9a6f4 | (dynamic via ip) | 0x19 (=25) |
| 8 | 0x9a7dc | (dynamic via ip) | 1 (r7) |
| 9 | 0x9a998 | (dynamic via ip) | 1 (r7) |
| 10 | 0x9ab80 | **#4** | 1 |
| 11 | (R73 미관측 — 11번째 호출 위치 zoom 필요) | — | — |

distinct static effect_type values: **{4, 7, 8}** + dynamic (variable from r1=ip pre-set).

**effect_type 의미** (R5 의 TargetEffect::NewHitEffect 와 cross-ref 필요, R73 에선
distinct count 만 식별):
- 4 = 표준 hit effect (가장 흔함, 6/11 호출)
- 7 = secondary hit / chain effect (2 호출)
- 8 = special effect (1 호출)
- dynamic = caller 의 ip register 가 가리키는 값 (skill_info field 의존?)

### 14.3 공통 stack arg 패턴

모든 호출이 동일 stack layout 사용:
- sp[0..0x10] = 5 ptr/char args (대부분 NULL = fp=0 또는 ip=1)
- sp[0x14] (= short s) = `lr` (R5 의 NewHitEffect 와 유사하게 frame counter 또는 PC backup?)
- sp[0x18] = 1 (int g, 첫 정수 인자)
- sp[0x1c..0x20] = 2 int args (target/skill 관련 ptr)

### 14.4 R73 → R74 잔여 작업

1. **TEM 호출 #11 위치 추적** — R73 도구가 ptr 추적 못 한 케이스 (e.g. ldr 통해 stored ptr 호출)
2. **effect_type 4/7/8 의 실제 의미** — TargetEffectMgr::NewTargetEffect 내부 분석 + R5 의 TargetEffect::NewHitEffect 와 비교
3. **skill_info[+0x3a] 의 0x34/0x37 special path** (R72 미해결)
4. **class 1 (ROGUE) 의 0x9a0b0 path** (R72 미해결)
5. **HERO + 0x1d3c vs +0x1fb0** 차이 분석
6. **Godot battle_system.gd 정확화** — R72/R73 의 Formula id 매핑으로 damage 공식을 Round 5 의 Formula VM 평가로 교체

