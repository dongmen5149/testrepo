# Attack Motion Dispatch (ChangeAttackMotion + CheckWeaponMotion) — RE 결과 (Round 69)

> R67 PASS 1 summary 에서 식별된 미해결 dispatch (`cmp r0, #0xd/#0xe/#0x14/#0x17`
> + `mov r1, #0x18/#0x26/#0x16/#0xa/#0xf`) 의 정밀 분석. ChangeAttackMotion 은
> **`HERO::ProcHeroSkill` (@0x99278) 안에서 1회 호출되는 production active code**
> 임을 확인 (ARM bl-pattern raw scan). 본 라운드 초기에 capstone 기반 검색이
> segment selection 버그로 0건 반환했으나 raw u32 decode 로 진짜 호출자 발견.

## 1. 핵심 발견

1. **R67 가설 정정**: cmp 0xd/0xe/0x14/0x17 의 입력은 **skill_type 도 weapon_kind 도
   아니다**. `bl CHAR::GetMotion()` 의 반환값 = **현재 motion id**. 즉 ChangeAttackMotion
   은 "이미 진행 중인 attack motion 의 mid-frame 에서 hit-frame trigger 시 다음
   motion 으로 전환" 하는 함수.
2. **R67 가설 정정**: mov r1, #0x18/0x26/0x16/0xa/0xf 는 모두 motion id 가 아니다.
   - 0x16 (22), 0x18 (24), 0x26 (38), 0xf (15) = SetMotion 의 새 motion id
   - 0xa (10) = `Monster::AddEffectKnockBack` 의 KB strength
3. **분기 키 = `class_id` (HERO+0x22c)**: class 0 (워리어) 또는 class 3 (나이트)
   에서만 동작. class 1 (로그), 2 (건슬링어), 4 (소서러 stub) 는 NOP.
4. **호출자 확정** (두 함수 모두 production active):
   - `ChangeAttackMotion` ← `HERO::ProcHeroSkill(HeroSkillInfo*)` @ 0x99278 (7972B)
     의 offset **+0x488** (= 0x99700) 1회 호출. skill 처리 중 motion phase 전환.
   - `CheckWeaponMotion` ← **4 클래스의 `Draw(int, int, int)` 메서드 5회 호출**:
     - `WARRIOR::Draw` @0x146af0 +0x8c
     - `ROGUE::Draw` @0xd7a18 +0x8c
     - `KNIGHT::Draw` @0xaa328 +0x8c
     - `GUNNER::Draw` @0x87678 +0x78 (+ +0x94, GUNNER 만 2회)
     - SORCERER 는 미포함 → R22 의 "Sorcerer class object 없음" stub 가설 재확인
   - 즉 매 frame 캐릭터 Draw() 직전에 무기/방패 변경 motion sync.

## 2. ChangeAttackMotion @ 0x91e7c (340B, ARM)

서명 (Itanium ABI):
```cpp
void HERO::ChangeAttackMotion(HeroSkillInfo* skill_info);
```

전체 disasm (압축):

```arm
; class_id 분기
00091e80: ldrb     r3, [r0, #0x22c]          ; class_id = this->class_id
00091e8c-90: lsl/asrs r3, r3, #0x18           ; sign-extend (signed byte)
00091e94: bne      #0x91eb8                   ; class != 0 → 0x91eb8
                                              ;        == 0 → fallthrough (워리어)

; ── class 0 (워리어) path ────────────────────────────────
00091e98: bl       #0x49b74                   ; r0 = CHAR::GetMotion()
00091ea4: cmp      r0, #0xd                   ; motion == 13 ?
00091ea8: beq      #0x91f60                   ;   → SetMotion(0x26=38)
00091eac: cmp      r0, #0x14                  ; motion == 20 ?
00091eb0: beq      #0x91f70                   ;   → SetMotion(0x16=22)
00091eb4: pop                                 ; 다른 motion = NOP, return

; ── class != 0 분기 ────────────────────────────────
00091eb8: cmp      r3, #3                     ; class == 3 (나이트) ?
00091ebc: bne      #0x91eb4                   ; 아니면 return NOP

; ── class 3 (나이트) path ────────────────────────────────
00091ec0: bl       #0x49b74                   ; r0 = CHAR::GetMotion()
00091ecc: cmp      r0, #0xe                   ; motion == 14 ?
00091ed0: beq      #0x91f80                   ;   → 0x91f80 (motion 14 handler)
00091ed4: cmp      r0, #0x17                  ; motion == 23 ?
00091ed8: bne      #0x91eb4                   ; 둘 다 아니면 return

; ── class 3, motion 23 handler ────────────────────────────────
00091edc-e4: SetMotion(this, 0x18 = 24)
00091e8-f4: state_1d36 = this->byte_1d36; if (state_1d36 != 1) return
00091efc: r2 = skill_info[+0x44]            ; knockback_idx (byte)
00091f08: r2 = r2 - 1
00091f1c-24: r1 = (r2 - 1 후 sign-extend) * 6 + 0x14   ; KB value = (kb_idx - 1) * 6 + 20
00091f30: strb r2, [r4, #0x1fea]              ; this->byte_1fea = kb_idx (저장)
00091f34: r0 = *(this + 0x1fb0)               ; target Monster*
00091f3c: bl       #0xc0a18                   ; Monster::AddEffectKnockBack(target, kb_value)
00091f40: r1 = *(this + 0x1fb0)
00091f48: bl       #0x4c5ec                   ; r0 = CHAR::CharTurnDirection(this, target)
00091f5c: b        #0x49b7c                   ; tail-call CHAR::SetDir(this, dir)

; ── class 0, motion 13 handler ────────────────────────────────
00091f60-6c: SetMotion(this, 0x26 = 38) via tail-call
                                              ;   beq #0x91f60: r1=0x26; b SetMotion

; ── class 0, motion 20 handler ────────────────────────────────
00091f70-7c: SetMotion(this, 0x16 = 22) via tail-call
                                              ;   beq #0x91f70: r1=0x16; b SetMotion

; ── class 3, motion 14 handler ────────────────────────────────
00091f80: r5 = 0x1fb0 (=0x1f80 + 0x30)
00091f88: r0 = *(this + 0x1fb0)               ; target Monster*
00091f90: beq      #0x91fc0                   ; target == NULL → 0x91fc0 (no-effect path)
00091f94: r1 = #0xa                            ; KB strength = 10
00091f98: bl       #0xc0a18                   ; Monster::AddEffectKnockBack(target, 10)
00091f9c: r0 = *(this + 0x1fb0)
00091fa0: bl       #0xbacbc                   ; Monster::SetRevengeXY(target)
00091fa8: bl       #0x4c5ec                   ; r0 = CHAR::CharTurnDirection(this, target)
00091fbc: bl       #0x49b7c                   ; CHAR::SetDir(this, dir)

; ── motion 14, no target path ────────────────────────────────
00091fc0-cc: SetMotion(this, 0xf = 15) via tail-call
```

## 3. dispatch 표 (확정)

| class_id | 클래스 | current motion (in) | next motion (out) | side-effect |
|:---:|---|:---:|:---:|---|
| 0 | 워리어 | 13 (0xd) | **38 (0x26)** | (없음) — 단순 motion swap |
| 0 | 워리어 | 20 (0x14) | **22 (0x16)** | (없음) |
| 3 | 나이트 | 14 (0xe), target == NULL | **15 (0xf)** | (없음) — 빈 swing |
| 3 | 나이트 | 14 (0xe), target != NULL | (motion 유지) | KB=10 + RevengeXY + TurnDir + SetDir |
| 3 | 나이트 | 23 (0x17), state_1d36 != 1 | **24 (0x18)** | (없음) |
| 3 | 나이트 | 23 (0x17), state_1d36 == 1 | **24 (0x18)** | KB=(skill_info[+0x44] - 2)*6 + 20 + TurnDir + SetDir |
| 1, 2, 4 | (다른 클래스) | (어느 것이든) | (NOP) | — |

### motion id 의미 (R67 + R69 종합)

- 3 = walk (R67 확정)
- 5 = die (R67 확정)
- 13, 14, 20, 23 = **공격 anticipation/wind-up** (이전 motion, ChangeAttackMotion 의 입력)
- 15, 22, 24, 38 = **공격 release/hit** (변경 후 motion, ChangeAttackMotion 의 출력)

즉 attack motion 은 2 phase: (a) wind-up → (b) ChangeAttackMotion 호출 → (c) release.
나이트 motion 14/23 만 release 시 추가 KB effect.

## 4. CheckWeaponMotion @ 0x8dd58 (256B, ARM) — 무기 변경 동기화

```cpp
void HERO::CheckWeaponMotion();
```

전체 흐름 (압축):

- class_id != 3 path:
  - `IsNoneWeapon() == 0` (무기 있음) → motion 검사:
    - motion 의 high byte == 0x20 → SetMotion(0) + clear motion_change_flag (+0xc4=0)
    - motion 의 high byte == 0x30 → SetMotion(1) + clear motion_change_flag
    - 그 외 → return
  - `IsNoneWeapon() == 1` (무기 없음) → `IsNoneEquipWeapon()` 검사 후 재시도
- class_id == 3 (나이트) path:
  - 동일 motion 검사이지만 무기 없을 때 `IsNoneEquipShield()` 도 검사
  - 무기/방패 모두 없을 때만 SetMotion(1) + clear flag

(주의: `lsl r0, r0, #0x18; cmp r0, #0x2000000` 패턴은 motion = signed byte 비교를
high-byte shift 로 한 것 — motion 32 (`0x20`) 와 motion 48 (`0x30`) 비교.)

motion 0x20 (32), 0x30 (48) = **무기 들고 있을 때만 사용되는 idle/walk 변형 motion**.
무기 변경 (장착 해제) 시 motion 을 0 (idle) 또는 1 (walk) 로 리셋해 sprite 동기.

CheckWeaponMotion 도 호출자 0건 → dead code. 무기 swap 이벤트에서 호출되어야
정상이지만 production 에선 다른 시스템이 처리.

## 5. HERO struct 신규 식별 fields

| offset | type | 의미 | 근거 |
|---:|---|---|---|
| +0x22c | byte (signed) | **class_id** (R43 와 일치 재확인) | `ldrb r3, [r0, #0x22c]` + class 0/3 분기 |
| +0x1d36 | byte | class 3 의 secondary state (e.g. 2nd-hit 활성 flag) | `r3, #0x1d00 + 0x36` ldrsb 후 `cmp #1` |
| +0x1fb0 | ptr (Monster*) | **현재 attack target Monster** | `r5, #0x1f80 + 0x30` 로 base, 그리고 ldr 결과를 AddEffectKnockBack/CharTurnDirection 에 전달 |
| +0x1fea | byte | last knockback_idx (skill_info 의 byte_44 저장) | `r3, #0x1fc0 + 0x2a` 로 base, strb |
| +0xc4 | byte | motion_change_flag (R67 와 일치 재확인) | CheckWeaponMotion 의 SetMotion 직후 `strb r3, [r4, #0xc4]` (r3=0) |

## 6. HeroSkillInfo 신규 식별 field

| offset | type | 의미 | 근거 |
|---:|---|---|---|
| +0x44 | byte | **knockback_idx** (1-base index, 0 이면 KB strength = 14) | class 3 motion 23 handler 의 `r2 = ldrb [r5, #0x44]; r2 -= 1; kb_value = (r2-1)*6 + 20` |

## 7. 외부 helper 함수 확정

| 주소 | 심볼 | 의미 |
|---:|---|---|
| 0x49b74 | `CHAR::GetMotion()` | motion byte 반환 (R67 와 일치) |
| 0x49b7c | `CHAR::SetDir(byte)` | direction 변경 (R67 와 일치) |
| 0x4af5c | `CHAR::SetMotion(byte)` | motion byte 변경 (R67 와 일치) |
| 0x4c5ec | `CHAR::CharTurnDirection(CHAR* other)` | this 가 other 를 바라볼 dir 반환 |
| 0xbacbc | `Monster::SetRevengeXY()` | monster 의 revenge target 좌표 set |
| 0xc0a18 | `Monster::AddEffectKnockBack(s16 strength)` | KB effect 큐에 추가 |
| 0x8930c | `HERO::IsNoneWeapon()` | 현재 무기 motion 활성 여부 |
| 0x8dd20 | `HERO::IsNoneEquipShield()` | 방패 슬롯 비었는지 |
| 0x8dd3c | `HERO::IsNoneEquipWeapon()` | 무기 슬롯 비었는지 |

## 8. R67 → R69 가설 정정 표

| 항목 | R67 PASS 1 추정 | R69 확정 |
|---|---|---|
| cmp r0, #0xd / #0xe / #0x14 / #0x17 의 입력 | skill_type 또는 weapon_kind | **현재 motion** (`CHAR::GetMotion()` 반환값) |
| mov r1, #0x18 / #0x26 / #0x16 / #0xa / #0xf | motion id 별 값 | **SetMotion 의 새 motion** (0x16/0x18/0x26/0xf) **또는 KB strength** (0xa) |
| dispatch 분기 키 | (불명) | **`this->class_id` (HERO+0x22c)** — class 0 (워리어) 또는 3 (나이트) 만 active |
| ChangeAttackMotion 활성 여부 | (R67 PASS 1 미확인) | **production active** — `HERO::ProcHeroSkill` @0x99278 offset +0x488 에서 1회 호출 |
| CheckWeaponMotion 활성 여부 | (R67 PASS 1 미확인) | **production active** — 4 클래스 Draw() 메서드에서 5회 호출 (WARRIOR/ROGUE/KNIGHT/GUNNER, SORCERER 제외 — R22 stub 가설 재확인) |

## 9. Godot 매핑 권장

`apps/hero5-godot/scripts/core/character.gd` (R61) 의 `set_attack_motion()` 메서드는
현재 logical motion id 만 받음. R69 결과로 motion id enum 확장:

- `SO_MOTION_WARRIOR_WINDUP_A = 13`, `SO_MOTION_WARRIOR_HIT_A = 38`
- `SO_MOTION_WARRIOR_WINDUP_B = 20`, `SO_MOTION_WARRIOR_HIT_B = 22`
- `SO_MOTION_KNIGHT_WINDUP_A = 14`, `SO_MOTION_KNIGHT_HIT_A = 15`
- `SO_MOTION_KNIGHT_WINDUP_B = 23`, `SO_MOTION_KNIGHT_HIT_B = 24`
- `SO_MOTION_WEAPON_IDLE_HIGH = 32`, `SO_MOTION_WEAPON_WALK_HIGH = 48` (CheckWeaponMotion 잔여)

본 enum 은 logical 매핑만 — Godot 의 attack motion 처리는 R63 의 SPACE 키 / R62 의
AI tick 으로 이미 단순화되어 동작 중. 미래 .so cross-ref + sprite anim phase 동기
검증 시 안전용.

## 10. 잔여 미해결

- **HERO::ProcHeroSkill (@0x99278, 7972B) 정밀 분석** — 거대 함수. skill_info 의
  hit-frame trigger 가 어디서 ChangeAttackMotion 을 호출하는지 + class 1/2 (로그/
  건슬링어) 의 attack motion 처리 경로 식별. R70 후보.
- `state_1d36` (class 3 의 secondary flag) 의 정확한 의미 — combo 시스템 또는
  charge attack 의 진행 단계?
- `HeroSkillInfo + 0x44` (knockback_idx) 가 어디서 set 되는지 — `LoadSkillTable`
  에서 csv → struct transpose 시 결정될 가능성.
- CheckWeaponMotion 의 class 분기 정밀화 — 4 클래스 Draw() 의 호출 context 확인
  (장착 슬롯 변경 직후의 sync 인지, 매 frame 의 weapon-aware idle/walk anim sync 인지).
- GUNNER::Draw 가 CheckWeaponMotion 을 2회 호출하는 이유 — 양손 무기 처리?
