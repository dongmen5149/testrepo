# Battle Motion / CHAR State Machine — RE 결과 (Round 67)

> R50 의 HOST_MOTION 가설 (walk=1, die=9 등) 검증을 위해 .so 의 motion setter 5종을
> 정밀 디스어셈블. **R50 가설 잘못 — 실제 motion enum 정정**.

## 1. 핵심 발견

CHAR/HERO 의 state machine 은 **3개의 별도 byte field** 로 구성:

| 필드 | offset | 의미 | 의미 단위 |
|---|---:|---|---|
| **main_state** | (CHAR 안의 어딘가) | 현재 액션 분류 | 1=walk, 2=attack, 3=attacked, 4=die |
| **next_state** | (HERO+offset) | 다음 turn 전환 마커 | main_state 와 동일 값 |
| **motion** | +0x2c | 애니메이션 frame index | 3=walk, 5=die, attack/attacked=가변 |

**main_state ≠ motion**. 둘은 별개 시스템:
- main_state: 게임 로직 (transitioning 상태)
- motion: 스프라이트 애니메이션 (Frame buffer 의 어떤 sprite 그리기)

## 2. .so 디스어셈블 근거

### CHAR::SetMotion @ 0x4af5c (56B, ARM mode)

```arm
0004af5c: push     {r4, lr}
0004af60: mov      r4, r0           ; this
0004af64: strb     r1, [r0, #0x2c]  ; *(this+0x2c) = motion_id (byte)
0004af68: bl       #0x49b9c          ; CHAR::ResetFrame? (frame state reset)
0004af6c: ldrh     r3, [r4, #0x2e]  ; r3 = *(this+0x2e) u16 (frame counter)
0004af70: mov      r2, #1
0004af74: strb     r2, [r4, #0xc4]  ; motion_change_flag = 1
0004af78: strb     r3, [r4, #0xc5]  ; prev_frame_low byte
0004af7c: mov      r0, r4
0004af80: ldrsb    r1, [r4, #0x2c]  ; motion (signed)
0004af84: ldrsb    r2, [r4, #0x2d]  ; dir (signed)
0004af88: bl       #0x4af34          ; CHAR::GetMaxFrame(motion, dir)
0004af8c: strb     r0, [r4, #0xc6]  ; max_frame for (motion, dir)
0004af90: pop      {r4, pc}
```

CHAR struct 확정 fields:
- **+0x2c = motion** (u8, 현재 애니메이션 index) — R50 추정과 일치
- **+0x2d = dir** (u8) — R50 추정과 일치
- **+0x2e = frame** (u16, anim frame counter) — R50 추정과 일치
- **+0xc4 = motion_change_flag** (u8, motion 바뀐 직후 1)
- **+0xc5 = prev_frame_low** (u8, 이전 frame state save)
- **+0xc6 = max_frame_current** (u8, GetMaxFrame(motion, dir) 결과)

### HERO::SetWalkMotion @ 0x98f6c (116B)

```arm
00098f78: bl       #0x4a2b0          ; BATTLER::InitAddEffectValue
00098f80: mov      r1, #1
00098f84: bl       #0x49b5c          ; CHAR::SetMainState(1)   ★ main_state = 1
00098f8c: mov      r1, #1
00098f90: bl       #0x88940          ; HERO::SetNextState(1)   ★ next_state = 1
00098f98: mov      r1, #3
00098f9c: bl       #0x4af5c          ; CHAR::SetMotion(3)      ★ motion = 3
00098fa0: mov      r1, r5            ; dir (arg)
00098fa4: bl       #0x49b7c          ; CHAR::SetDir(arg)
```

### HERO::SetDieMotion @ 0x98dd8 (128B)

```arm
00098de0: bl       #0x4a2b0          ; BATTLER::InitAddEffectValue
00098de8: mov      r1, #4
00098dec: bl       #0x49b5c          ; CHAR::SetMainState(4)   ★ main_state = 4
00098df4: mov      r1, #4
00098df8: bl       #0x88940          ; HERO::SetNextState(4)   ★ next_state = 4
00098e00: mov      r1, #5
00098e04: bl       #0x4af5c          ; CHAR::SetMotion(5)      ★ motion = 5
00098e08: mov      r1, #0
00098e10: bl       #0x49b7c          ; CHAR::SetDir(0)
```

### HERO::SetAttackMotion @ 0x98870 (160B)

```arm
000988a0: mov      r1, #2
000988a8: bl       #0x49b5c          ; CHAR::SetMainState(2)   ★ main_state = 2
000988b0: mov      r1, #2
000988b4: bl       #0x88940          ; HERO::SetNextState(2)
000988bc: mov      r1, r5            ; r5 = arg1 (caller 가 전달)
000988c0: bl       #0x4af5c          ; CHAR::SetMotion(r5)     ★ motion = caller arg
```

### HERO::SetAttackedMotion @ 0x98e58 (112B)

```arm
00098e64: mov      r1, #3
00098e6c: bl       #0x49b5c          ; CHAR::SetMainState(3)   ★ main_state = 3
00098e74: mov      r1, #3
00098e78: bl       #0x88940          ; HERO::SetNextState(3)
00098e7c: mov      r1, r5            ; r5 = arg1
00098e84: bl       #0x4af5c          ; CHAR::SetMotion(r5)     ★ motion = caller arg
```

## 3. ★ R50 가설 정정 ★

| 구분 | R50 가설 (잘못) | R67 RE 실제 값 |
|---|---:|---:|
| WALK motion | 1 | **3** |
| RUN motion | 5 | 미확인 |
| ATTACK motion | 6 | caller arg (variable) |
| DIE motion | 9 | **5** |
| CAST motion | 12 | 미확인 |

main_state enum 정확:
- 1 = walking
- 2 = attacking
- 3 = attacked (피격)
- 4 = dying
- 0 = idle (default, set 안되면)

motion enum 정확 (관측):
- **3 = walk anim**
- **5 = die anim**
- variable = attack/attacked anim (HeroSkillInfo 등에서 lookup)
- 0/1/2/4 = 미확인 (idle / 다른 motion)

## 4. helper 함수 매핑

| 주소 | 함수 | 인자 |
|---|---|---|
| 0x49b5c | `CHAR::SetMainState(char state)` | state byte |
| 0x49b74 | `CHAR::GetMotion()` | (반환: char) |
| 0x49b7c | `CHAR::SetDir(char dir)` | dir byte |
| 0x4af34 | `CHAR::GetMaxFrame(motion, dir)` | (반환: max frame) |
| 0x4af5c | `CHAR::SetMotion(char motion)` | motion byte |
| 0x88940 | `HERO::SetNextState(char state)` | state byte |
| 0x4a2b0 | `BATTLER::InitAddEffectValue()` | - |
| 0x4a40c | `BATTLER::InitColorChar()` | - |
| 0x950bc | `HERO::InitColorBack()` | - |

## 5. UI 라벨 (Godot character.gd 정정)

기존 character.gd 의 `HOST_MOTION_*` 가 R50 가설 기반 → 정정:

```gdscript
# === BEFORE (R50 가설, 잘못) ===
const HOST_MOTION_IDLE := 0
const HOST_MOTION_WALK := 1   # 실제로는 motion 3
const HOST_MOTION_RUN := 5
const HOST_MOTION_ATTACK := 6
const HOST_MOTION_DIE := 9    # 실제로는 motion 5
const HOST_MOTION_CAST := 12

# === AFTER (R67 RE 정확) ===
# main_state byte (CHAR::SetMainState 의 인자)
const MAIN_STATE_IDLE := 0       # default
const MAIN_STATE_WALK := 1
const MAIN_STATE_ATTACK := 2
const MAIN_STATE_ATTACKED := 3
const MAIN_STATE_DIE := 4

# motion byte (CHAR::SetMotion 의 인자, animation index)
const MOTION_WALK := 3
const MOTION_DIE := 5
# attack/attacked motion: variable (caller arg, skill 기반 lookup)
```

## 6. 부수 효과 + 미해결

- `0x49b9c` (SetMotion 내부 호출) — 아마 frame reset (보지 못한 함수)
- ChangeAttackMotion (0x91e7c, 340B) 의 cmp 분포 (0xd/0x14/0xe/0x17 등) — skill_type 분기 추정, 정밀 분석 미완
- HERO::SetSkillMotion 류 함수 미발견 (cast motion 12 가설 검증 불가)
- BATTLER::Add* 함수 시리즈 (InitAddEffectValue 등) — buff/debuff 영역

## 7. 검증 도구

`tools/h5_test_battle_motion.py` — Python sweep:
- ELF symbol 4 setter (SetWalk/Attack/Attacked/Die) + CHAR::SetMotion 주소 확인
- character.gd 의 MAIN_STATE_* / MOTION_* 상수 정정 검증
- R50 → R67 가설 정정 표 cross-check
