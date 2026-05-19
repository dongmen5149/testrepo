# TargetEffect::ProcTargetEffectSkill overview RE (Round 81)

> R80 에서 TEM 시스템 구조 + Effect 베이스 클래스 setter 확정. 본 라운드는 R80
> 의 후속으로 4276B 거대 함수 `TargetEffect::ProcTargetEffectSkill` (@0x64a08)
> 의 **per-frame 동작 overview** 를 매핑한다. 정밀 case-by-case 분석은 R82+.

## 1. 함수 시그니처 및 호출 컨텍스트

```cpp
void TargetEffect::ProcTargetEffectSkill(this, HeroSkillInfo* skill_info, BATTLER* target);
// @0x64a08, 4276B, ~1069 ARM instructions
```

- this = TargetEffect slot (R80 의 0x284B 슬롯)
- skill_info = ProcHeroSkill 에서 TEM::NewTargetEffect 호출 시 전달했던 ptr (slot 에 저장됨)
- target = effect 대상 BATTLER (HERO or Monster)

호출자: **TargetEffect main update loop** (per-frame, 100 슬롯 순회 중 active 한 슬롯 처리).

## 2. **Jumptable 없음 — pure cascade dispatch**

`addls pc, pc, ...` 패턴 **0 개**. 4276B 전체가 if/else 분기와 case-by-case Formula::calc
호출로 구성. R70 의 ProcHeroSkill (2 jumptable) 과 대조적.

## 3. Top 25 field reads (Effect / skill_info / HERO / BATTLER)

| field | offset | count | 출처 | 의미 |
|---|---|---|---|---|
| `[r4, #0xf]` | +0x0f | 9x | TargetEffect base / OBJECT | 부속 char (좌표 또는 dir?) |
| `[r7, #0x22c]` | HERO+0x22c | 6x | HERO::class_id (R69) | class 분기 |
| `[r7, #0x269]` | HERO+0x269 | 6x | HERO::gunner_combo (R72) | GUNNER combo state 검사 |
| `[r3, #0x24]` | +0x24 | 4x | TargetEffect / BATTLER | 부속 |
| `[r6, #0x32]` u16 | skill_info+0x32 | 3x | R70 4×u16 #1 (primary value) | damage / heal 값 |
| `[r6, #0x36]` u16 | skill_info+0x36 | 3x | R70 4×u16 #3 (secondary) | radius / count |
| `[r6, #0x2f]` | skill_info+0x2f | 3x | R77 file-loaded | 부속 byte (desc_len 위치) |
| `[r6, #0x29]` | skill_info+0x29 | 3x | R70 effect2 (sub-type) | 부속 effect 타입 |
| `[r6, #0xa]` | skill_info+0xa | 3x | R70 flag | flag |
| `[r8, #0x24]` | TargetEffect+0x24 | 3x | R80 (NewTargetEffect 초기화) | 부속 |
| `[r6, #0x3a]` | skill_info+0x3a | 2x | R72 special_dispatch | special path 분기 |
| `[r6, #0x1c]` | skill_info+0x1c | 2x | R70 mode flag | 모드 |
| `[r7, #0x294]` | HERO+0x294 | 2x | R72 skill state flag | state 분기 |
| `[r8, #0xc0]` | TargetEffect+0xc0 | 1x | R80 frame counter | per-frame tick |
| `[r6, #0x2a]` | skill_info+0x2a | 1x | R70 formula_arg | Formula::calc 인자 |
| `[r8, #0xab..#0xaf]` | TargetEffect+0xab-0xaf | 5x | R80 state byte cluster | per-frame state machine |
| `[r6, #0x2b]` | skill_info+0x2b | 1x | R77 file-loaded | flag |
| `[r6, #0x4e]` | skill_info+0x4e | 1x | R79 dead read | **default 0 (knight_threshold 가설)** |
| `[r6, #0x4a]` ldrsh | skill_info+0x4a | 1x | R79 dead read | **default 0 (SP delta 가설)** |

→ skill_info read 12 field × ~25 read = **R77 file-loaded 영역 광범위 활용** + 일부 R79
dead reads (default 0 으로 동작).

## 4. Top 25 bl call targets (per-frame 호출 그래프)

| target | count | 함수 | 역할 |
|---|---|---|---|
| `0x49b6c` | 15x | `CHAR::GetSpritePtr` | sprite 접근 |
| `0x7749c` | **14x** | **Formula::calc (R71)** | **damage/value 계산** |
| `0xda51c` | 12x | `SPRITE::GetExtraDataPtr` | extra data |
| `0xcfd8c` | 8x | `OBJECT::GetX` | X 좌표 |
| `0xcfd9c` | 8x | `OBJECT::GetY` | Y 좌표 |
| `0x143c98` | 7x | `StaticUtil::Rand(min, max)` | 난수 |
| `0x7457c` | 6x | `ExtraData::GetPivotX` | sprite pivot X |
| `0x7458c` | 6x | `ExtraData::GetPivotY` | sprite pivot Y |
| **`0x62d40`** | **6x** | **TEM::NewTargetEffect_min** | **★ 재귀 VFX spawn** |
| **`0x4b41c`** | **4x** | **BATTLER::IncreaseHP** | **★ damage 적용 (음수) / heal (양수)** |
| `0x8c258` | 3x | `UiTargetMonster::SetBattler` | UI hit 표시 |
| `0x88ed4` | 3x | `HERO::IncreaseHiperCount` | hyper 게이지 |
| `0x4b134` | **3x** | **BATTLER::AddCurseSkill (R79)** | **★ curse 적용** |
| `0x6116c` | 3x | `TargetEffect::GetSpritePtr` | self sprite |
| `0x61184` | 2x | `TargetEffect::GetTempAtkProPtr` | atk property |
| `0x74538` | 2x | `AttackProperty::GetHitType` | hit type 결정 |
| `0x88e2c` | 2x | `HERO::IncreaseSP` | SP 변경 |
| **`0x646ec`** | 2x | **`TargetEffect::NewHitEffect`** | **★ hit VFX spawn** |
| `0x4bdb4` | 2x | `BATTLER::ApplyAddEffect (R79)` | additional effect dispatch |
| `0x89448` | 2x | `HERO::CheckEffSound_Hit` | hit 사운드 |
| `0x7cdb8` | 2x | `CommonUi::NewCommonEffectOnce` | common VFX |
| `0xc0930` | 1x | `Monster::SetAttackedMotion` | 적 hit 모션 |

→ 14 Formula::calc + 6 sub-VFX spawn + 4 IncreaseHP + 3 AddCurseSkill = 핵심 동작.

## 5. Per-frame 동작 흐름 추정

```
ProcTargetEffectSkill(this, skill_info, target):
  ── entry (R80 §2.4 와 동일 entry sequence)
  level cap 검사: if target->level > 99: return
  initial Formula::calc(...) for hit check (R71 의 OOB path)
  TargetEffect+0xc0 counter += 1

  ── if/else cascade dispatch (class_id, state, frame, skill_info flags)
  for each branch:
    Formula::calc(...) for damage/value
    if hit: BATTLER::IncreaseHP(target, -damage)
            UiTargetMonster::SetBattler(target)
            spawn TEM::NewTargetEffect(...)   # sub-VFX
            optionally: BATTLER::AddCurseSkill / ApplyAddEffect
            optionally: NewHitEffect
            optionally: Monster::SetAttackedMotion
    if special: HERO::IncreaseSP/HiperCount
    sound: HERO::CheckEffSound_Hit

  ── exit
  return
```

분기 키:
- class_id (HERO+0x22c, 6 read): 5 class 별 처리 분기
- gunner_combo (HERO+0x269, 6 read): GUNNER 만 추가 처리
- skill_info effect_type (+0x28) + special_dispatch (+0x3a) + flags
- TargetEffect state cluster (+0xab..+0xc0)

## 6. R79 의 dead reads 검증

R79 에서 확정한 +0x44/+0x46/+0x48/+0x4a/+0x4e 5 dead reads 중:
- `+0x4a` (ldrsh): ProcTargetEffectSkill 에 **1 회 read 존재** → 본 함수에서도 default 0
- `+0x4e` (ldrsb): **1 회 read 존재** → default 0
- `+0x44/+0x46/+0x48` 은 ProcTargetEffectSkill 에 read 없음

→ R79 결론 (5 field 모두 default 0 으로 동작) 일관성 확인. ProcTargetEffectSkill 의
`+0x4a/+0x4e` read 도 항상 0 으로 처리되어 해당 path 가 no-op 분기로 동작.

## 7. R81 결론 + R82+ 추천

| 항목 | R81 결과 |
|---|---|
| Jumptable | 0 (pure if/else cascade) |
| 함수 크기 | 4276B = ~1069 ARM instr |
| skill_info field read | 12 distinct file-loaded field (R77 영역 광범위 활용) |
| dead reads | +0x4a / +0x4e (R79 일관성 확인) |
| Top call | Formula::calc 14x, TEM 재귀 6x, IncreaseHP 4x, AddCurseSkill 3x |
| 핵심 동작 | per-frame skill effect engine (damage + sub-VFX + curse + UI) |

**R82+ 추천**:
- 본 함수의 cascade 분기 정밀화 (class_id × skill_info+0x28 × frame state 매트릭스)
- TEM 의 3 manager 채널 (global +0x15d8/+0x15e0/+0x15e4) 용도 추적
- ProcTargetEffectSkill 의 sub-VFX 재귀 spawn pattern (effect_type chain)
- Sorcerer class (R22 stub) — class_id 분기에서 어떻게 처리되는지 검증
