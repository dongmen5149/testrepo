# HeroSkillInfo runtime field source RE (Round 78)

> R77 에서 HeroSkillInfo 88B = file-loaded 68B (+0x00..+0x43) + runtime 20B (+0x44..+0x57)
> 영역 구분 확정. 본 라운드는 runtime 영역 (+0x44..+0x57) 의 **writer 함수** 와
> **각 field 의미** 를 추적한다.

## 1. HeroSkillInfo:: 멤버 함수 4종 (cooldown 시스템)

`.dynsym` 에서 `HeroSkillInfo::` 접두어 함수 4종 발견:

| 주소 | 크기 | 시그니처 | 동작 |
|---|---|---|---|
| `0xd8d38` | 12B | `SetNowCoolTime(short s)` | `entry+0x56 = s; entry+0x54 = s` |
| `0xd8d44` | 8B | `GetNowCoolTime()` | `return s16 [entry+0x54]` |
| `0xd8d4c` | 8B | `GetMaxCoolTime()` | `return s16 [entry+0x56]` |
| `0xd8d54` | 36B | `DecreaseNowCoolTime()` | `entry+0x54 -= 1; if (entry+0x54 < 0) entry+0x54 = 0` |

### SetNowCoolTime disasm
```
0xd8d38: strh r1, [r0, #0x56]   ; max cool time
0xd8d3c: strh r1, [r0, #0x54]   ; current cool time
0xd8d40: bx lr
```

→ **확정**: `+0x54 (u16) = NowCoolTime`, `+0x56 (u16) = MaxCoolTime`. R72 의 "+0x50 ranges" 가설은 정정 — 실제는 +0x54/+0x56 cooldown pair.

### DecreaseNowCoolTime disasm
```
0xd8d54: ldrh r3, [r0, #0x54]
0xd8d58: sub  r3, r3, #1
0xd8d64: tst  r3, #0x8000           ; check if underflow (negative)
0xd8d68: strh r3, [r0, #0x54]
0xd8d6c: movne r3, #0                ; if underflow, clamp to 0
0xd8d70: strhne r3, [r0, #0x54]
0xd8d74: bx lr
```

## 2. ProcHeroSkill entry 의 59-iter 루프 의미 정정 (R70 가설 정정)

R70 doc: "59-slot skill array 초기화 (HeroSkillInfo 배열)". **R78 정정**: 초기화가 아니라 **per-call cooldown tick**.

ProcHeroSkill entry @ 0x992b8 disasm:
```
0x992b8: mov r5, #0              ; i = 0
0x992bc: mov r7, #0x58           ; ENTRY_SIZE = 88
0x992c0: mul r0, r7, r5          ; offset = i * 88
0x992c4: add r5, r5, #1          ; i++
0x992c8: add r0, r0, #0x348      ; offset += 0x348
0x992cc: add r0, r4, r0          ; r0 = HERO + 0x348 + i*88 (slot addr)
0x992d0: bl  #0xd8d54             ; HeroSkillInfo::DecreaseNowCoolTime()
0x992d4: cmp r5, #0x3b            ; i < 59?
0x992d8: bne #0x992c0             ; loop
```

→ **매 ProcHeroSkill 호출마다 59 개 모든 슬롯의 `NowCoolTime` 을 1 감소시켜 0 까지 clamp**. 슬롯 자체의 초기화는 아님.

## 3. HERO::GetHeroSkillInfoPtr(int idx) @ 0x88ce4

```
0x88ce4: mov r3, #0x58
0x88ce8: mul r3, r1, r3
0x88cec: add r3, r3, #0x348
0x88cf0: add r0, r0, r3
0x88cf4: bx lr
```

= `return this + 0x348 + idx * 0x58` (88B stride 확정, R70/R77 일치).

## 4. InitSkillEmpty (@0x88a20, 272B) 정밀 분석

**HeroSkillInfo 배열과 무관**: HERO+0x1b40..+0x1b5f (32 byte 연속 영역) 을 0xFF 로 초기화.

disasm 결과 — 32 개의 `strb r2 (=0xFF), [r0, offset]` 모두 base=0x1b40 에서 offset +0..+0x1f 까지 한 번씩 (순서는 ARM ILP 로 섞임).

→ **새 HERO field cluster 발견**: HERO+0x1b40..+0x1b5f (32B). 의미는 미확정 (active skill slot 매핑 또는 quick-cast slot 후보). R57 의 7+1 active skill slot 시스템과 연관 가능.

## 5. InitSpiritSkillMenu (@0x89198, 132B) 분석

**HeroSkillInfo 배열과 무관**: global 객체 (GOT lookup) 의 menu state offset 0x118/0x11c/0x120/0x122/0x124-0x127/0x278-0x27b 에 sentinel 값 (-1, -100, -99, -999, 1) 설정. HERO+0x1fb6 에 1 (menu enabled flag).

→ menu cursor/index init, skill 데이터와 무관.

## 6. HeroSkillInfo 88B struct 최종 layout (R70..R77+R78)

| offset | type | source | 의미 |
|---|---|---|---|
| +0x00 | u8 | LoadResSkillInfo (loop counter r7) | skill_idx (0..58) |
| +0x04 | char* | LoadResSkillInfo (malloc) | name string |
| +0x08..+0x3d | misc | LoadResSkillInfo (file stats area) | R77 §4 의 27 byte + 10 u16 field |
| +0x3e..+0x3f | pad | — | alignment |
| +0x40 | char* | LoadResSkillInfo (malloc) | description string |
| +0x44 | ? | **HERO 객체 zero-init (default 0)** | R69 의 "kb_idx" 가설은 default 0 으로도 동작 일치 |
| +0x46 | ? | **HERO 객체 zero-init (default 0)** | R73 의 "shock_count" 가설은 default 0 으로도 동작 일치 |
| +0x48 | ? | **HERO 객체 zero-init (default 0)** | R73 의 "max_combo" 가설; default 0 일 때 R74 fallback=4 |
| +0x4a | ? | **HERO 객체 zero-init (default 0)** | R72 의 "SP delta" 가설; default 0 일 때 no SP change |
| +0x4c..+0x4f | ? | zero | R70 의 "+0x50 ranges" 가설은 정정 |
| +0x4e | ? | **HERO 객체 zero-init (default 0)** | R73 의 "knight_threshold" 가설 |
| **+0x54** | **u16** | **SetNowCoolTime / DecreaseNowCoolTime** | **NowCoolTime (current cooldown counter)** |
| **+0x56** | **u16** | **SetNowCoolTime** | **MaxCoolTime (skill cooldown duration)** |

**핵심 정정**: R70/R72 에서 추정한 "+0x50 ranges" 는 실제 **+0x54/+0x56 = NowCoolTime/MaxCoolTime cooldown pair**. R72/R73 의 다른 runtime field 가설 (+0x44/+0x46/+0x48/+0x4a/+0x4e) 은 ProcHeroSkill 의 ldrsb/ldrsh 읽기 자체는 사실이지만, 정상 게임플레이에서는 **HERO 객체 생성 시 zero-init 된 0 값을 읽음** (writer 미확정, R79+ 추적). 단 default 0 일 때도 ChangeAttackMotion/ProcHeroSkill 의 동작은 합리적 fallback 으로 일치.

## 7. HeroSkillInfo:: 멤버 함수 전체 (참고)

`.dynsym` 에서 HeroSkillInfo 를 인자/리시버로 받는 함수 38 개. 주요 처리 흐름:

| 처리 단계 | 함수 |
|---|---|
| getter / cooldown | `GetHeroSkillInfoPtr`, `SetNowCoolTime`, `Get/DecreaseNowCoolTime`, `GetMaxCoolTime` |
| skill main | `HERO::ProcHeroSkill` (R70-R73), `HERO::HeroSkillAtkHardCode` (R78 후속) |
| effect (TEM) | `TargetEffectMgr::NewTargetEffect` (R73, 5 overload), `TargetEffect::ProcTargetEffectSkill` (4276B) |
| hit effect | `TargetEffect::NewHitEffect`, `HERO::NewHitEffect` |
| target | `TargetEffect::SearchTargetBattler`, `HERO::SearchTargetBattler` (7032B), `SearchAddTargetBattler` |
| class별 special | `ROGUE::ProcSkillExcepion` (2956B), `GUNNER::ProcSkillExcepion` (1216B) |
| class별 effect | `ROGUE::NewShadowAttackEffect/NewKnifeEffect/NewShadowEffect`, `GUNNER::NewCannonMissileEffect/NewSentryBodyEffect/NewDecoyBodyEffect/NewAimingShotEffect`, `HERO::NewShockAddEffect`, `HERO::ChangeAttackMotion` (R69) |
| Formula | `Formula::calc/calcByFormula/getNumberInStack/getValFunc` |
| Battler | `BATTLER::ApplyAddEffect` |
| UI | `CommonUi::GetSkillDiscription/DrawSkillDiscription`, `StateInGameMenu::DrawAutoSkillBox` |

R79+ 후속 추적 대상: `HERO::ProcSkillExcepion` (혹시 있는가? 위 list 엔 없음 — 대신 class 별), `BATTLER::ApplyAddEffect` (skill_info 와 BATTLER 간 effect 흐름), `HERO::HeroSkillAtkHardCode` (888B, R78 부분 분석 — class 3 KNIGHT 분기 + skill_info+0x45 읽기 확인).

## 8. R78 결론

| 항목 | 결과 |
|---|---|
| HeroSkillInfo+0x54/+0x56 의미 | **NowCoolTime / MaxCoolTime u16 cooldown pair** 확정 |
| ProcHeroSkill entry 59-iter | **cooldown tick** (R70 "init" 가설 정정) |
| InitSkillEmpty | HERO+0x1b40..+0x1b5f 32B 0xFF init (HeroSkillInfo 와 무관) |
| InitSpiritSkillMenu | global menu state init (HeroSkillInfo 와 무관) |
| R72/R73 의 +0x44/+0x46/+0x48/+0x4a/+0x4e | writer 미확정 → 기본값 **0** 가정 (R79+ 추적, default 0 동작 합리적) |
| R72/R73 의 +0x50 ranges 가설 | **정정** → 실제 +0x54/+0x56 cooldown |

R77 의 file-loaded 영역 정확화 + R78 의 cooldown system 확정으로 **HeroSkillInfo struct field 의미의 9/11 확정** (file 7 + cooldown 2). 남은 5 field (+0x44/+0x46/+0x48/+0x4a/+0x4e) 는 정상 게임플레이에서 default 0 으로 동작.

R79 추천: `BATTLER::ApplyAddEffect` (@0x4bdb4, 496B) + `HERO::HeroSkillAtkHardCode` (@0x9041c, 888B, R78 부분 분석) 분석으로 R72/R73 잔여 5 field 의 writer 추적.
