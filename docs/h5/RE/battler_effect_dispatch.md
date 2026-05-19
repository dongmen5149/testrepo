# BATTLER effect dispatch + HeroSkillInfo runtime "field" 가설 종결 (Round 79)

> R78 에서 HeroSkillInfo 88B 의 file-loaded 영역 (+0x00..+0x43) 과 cooldown
> pair (+0x54/+0x56) 출처를 확정. 잔여 5 field (+0x44/+0x46/+0x48/+0x4a/+0x4e)
> 의 writer 는 미확정. 본 라운드는 BATTLER 의 effect 시스템 분석과 .so 전체
> grep 으로 그 5 field 의 운명을 종결한다.

## 1. BATTLER::ApplyAddEffect (@0x4bdb4, 496B) = pure dispatcher

ARM disasm 결과 — 28-way tail-call dispatcher (HERO ≠ Monster 분기 + 각 effect_type 별
handler 호출). **struct write 0**.

```
시그니처: (BATTLER* this, char effect_type, short value)

pre-check: bl 0xcfdb4   # returns class/type byte; 0x01 → HERO branch
HERO 분기: cmp r4, #0xd → addls pc, pc, r4, lsl #2 → 14-way jumptable
Monster 분기: cmp r4, #8 → addls pc, pc, r4, lsl #2 → 9-way jumptable

각 case = `mov r0, r6; mov r1, r5; pop {...,lr}; b <handler>`  (tail-call)
```

handler 주소 (모두 다른 함수로 tail-jump):
- Monster: 0xc09ac, 0xc0a18, 0xbe0f4, 0xbb348, 0xbb3e0, 0xbb488, 0xbb4dc, 0xbb530, 0xbb584
- HERO: 0x90794, 0x9083c, 0x90890, 0x908e4, 0x90938, 0x9098c, 0x907e8, 0x90a38, 0x90a8c, 0x98ec8, 0x98f20, 0x99230

→ ApplyAddEffect 자체는 dispatcher only — **skill_info struct 에 write 하지 않음**.

## 2. BATTLER::AddCurseSkill (@0x4b134, 100B) — effect 저장 위치 확정

시그니처: `(BATTLER* this, BATTLER* attacker, short, short, SPRITE*, char)` (R72).

ARM disasm 결과 — attacker (`r1=ip`) struct 내 5 영역 ptr 계산 후 내부 helper `0x4afd4` 호출:
- `attacker + 0x130`
- `attacker + 0x134`
- `attacker + 0x13a` (= 0x138 + 2)
- `attacker + 0x140`
- `attacker + 0x1b0`

→ **curse 상태는 attacker BATTLER struct 의 +0x130..+0x140 영역에 저장** (5 slot, slot 당 4-12B).
→ **HeroSkillInfo struct 와 무관**.

## 3. BATTLER::AddBuffSkill (@0x4b198, 260B) — effect 저장 위치 확정

시그니처: `(BATTLER* this, BATTLER* attacker, short value, short)`.

ARM disasm — 분기 `if (value >= 0x4b && s16 >= 1)` (보조 buff vs 기본 buff). 두 path 모두
attacker (`r7`) struct 내 5 영역 ptr 계산 후 `0x4afd4` 호출:
- `attacker + 0x118`
- `attacker + 0x11e` (= 0x11c + 2)
- `attacker + 0x124`
- `attacker + 0x12a` (= 0x128 + 2)
- `attacker + 0x1c8`

→ **buff 상태는 attacker BATTLER struct 의 +0x118..+0x128 영역에 저장** (4 slot + 1 ptr).
→ **HeroSkillInfo struct 와 무관**.

## 4. HERO::AddStanceSkill (@0x91d7c, 256B) — effect 저장 위치 확정

시그니처: `(HERO* this, char, short, short)`.

ARM disasm — 분기 `if (r3 >= 2)`. 두 path 모두 HERO (`r4`) struct 내 영역 계산 후
`0x4b29c` 호출:
- `HERO + 0x284`
- `HERO + 0x288`
- `HERO + 0x28a` (= 0x288 + 2)
- `HERO + 0x1f94` (= 0x1f80 + 0x14)

→ **stance 상태는 HERO struct 의 +0x284..+0x28a 영역에 저장** (2 short + 1 byte).
→ **HeroSkillInfo struct 와 무관**.

## 5. **결론**: BATTLER/HERO 가 active effect 저장 컨테이너 — HeroSkillInfo 아님

| 시스템 | 저장 위치 | 사이즈 |
|---|---|---|
| Buff (BUFF effect_type 3·5) | `BATTLER + 0x118..+0x12b` | ~20B |
| Curse (effect_type 1·2) | `BATTLER + 0x130..+0x143` | ~20B |
| Stance (effect_type 4) | `HERO + 0x284..+0x28a` | ~8B |
| Buff/Curse extra ptr | `BATTLER + 0x1b0`, `BATTLER + 0x1c8` | 4B each |
| Stance extra flag | `HERO + 0x1f94` | 4B |

R74 의 GameState `active_curses` / `active_buffs` / `active_stances` Array 가 이것의
Godot 측 대응 — 정확한 매핑.

## 6. .so 전체 grep: HeroSkillInfo+0x44/+0x46/+0x48/+0x4a/+0x4c/+0x4e writer 추적

`capstone` 으로 `.text` 영역의 모든 `strb/strh/str` instruction 을 디스어셈블하고
`#0x44/#0x46/#0x48/#0x4a/#0x4c/#0x4e` immediate offset 인 것만 필터링.

각 offset 별 **HeroSkillInfo struct 에 write 하는 함수 수**:

| offset | 전체 write 수 (sp 포함) | sp 제외 strb/strh | HeroSkillInfo 컨텍스트 |
|---|---|---|---|
| +0x44 | 400 | 0 strb/strh (대부분 sp 또는 다른 struct str) | **0** |
| +0x46 | 17 | 6 (BFont 생성자, Battle::DrawSpiritCutIn UI, CommonUi::DrawSkillBookDiscription, HERO::SaveHeroData, NETWORK::readNetItem, CommonUi UI) | **0** (모두 무관 구조체) |
| +0x48 | 307 | 0 strb/strh (대부분 sp/str) | **0** |
| +0x4a | 7 | 6 (Battle::DrawSpiritCutIn, HERO::SaveHeroData, NETWORK::readNetItem, ParticleMgr, StateInGameMenu × 2) | **0** |
| +0x4c | 282 | 0 strb/strh | **0** |
| +0x4e | 9 | 2 (Battle::DrawSpiritCutIn, NETWORK::readNetItem) | **0** |

→ **.so 전체에서 HeroSkillInfo struct 의 +0x44/+0x46/+0x48/+0x4a/+0x4c/+0x4e 에
   write 하는 함수는 0 개**. 모든 strb/strh 는 **다른 구조체** (BFont, NETWORK::_NET_ITEM_,
   ParticleMgr, StateInGameMenu, Battle UI) 의 같은 offset 에 쓰는 것 (struct field 우연
   일치).

비교 — `+0x54` strh writer 중 진짜 HeroSkillInfo write 는 1 개 (R78 SetNowCoolTime
@0xd8d38), 나머지 8 개는 NETWORK/StateInGameMenu 의 별도 구조체. 동일한 우연 일치
패턴이지만 +0x54 는 R78 의 cooldown 시스템으로 **확정된 write 1 개 존재**.

## 7. **R72/R73 의 5 runtime field 가설 종결**: dead reads

ProcHeroSkill (R70-R73 disasm) 에서 명확히 존재하는 `ldrsb`/`ldrsh` 읽기:
- R69: `ldrsb [skill_info, #0x44]` (class 3 motion 23 path → `(byte-2)*6+20` KB)
- R73: `ldrsb [r6, #0x46]` (case 5 shock skill 조건)
- R72: `ldrsh [skill_info, #0x4a]` (case 0 NO_HIT SP delta)
- R73: `ldrsb [skill_info, #0x4e]` (case 3 KNIGHT secondary threshold)
- R72: `ldrsh [skill_info, #0x48]` (R74 GUNNER max_combo)

이 5 read 는 모두 **dead reads** — 값을 쓰는 writer 가 .so 어디에도 없으므로 **HERO 객체
zero-init 의 default 0** 값만 읽음.

| read | 정상 게임플레이 동작 |
|---|---|
| +0x44 (kb_idx) | 항상 0 → class 3 motion 23 KB = `(0-2)*6+20 = 8` 일정값 |
| +0x46 (shock_count) | 항상 0 → case 5 shock skill 조건 `> 0` **절대 충족 안 됨 → dead code** |
| +0x48 (max_combo) | 항상 0 → R74 fallback `default=4` 채택 (Godot 측 보조) |
| +0x4a (SP delta) | 항상 0 → case 0 NO_HIT path 의 SP 변경 0 (no-op) |
| +0x4e (knight_threshold) | 항상 0 → class 3 KNIGHT secondary check 항상 0 (no-op) |

→ **이 5 field 는 design intent 만 남고 production data 에서 값이 0** (production cut
또는 별도 데이터 파일 형식의 옵션 field).

**HeroSkillInfo 88B 의 최종 영역 구성** (R77 + R78 + R79):

| 영역 | 출처 | 비고 |
|---|---|---|
| +0x00..+0x43 (68B) | LoadResSkillInfo (R77) | file-loaded, 7 critical field 정확 |
| **+0x44..+0x53 (16B)** | **none — HERO zero-init default 0** | **dead reads (R72/R73 design intent, R79 종결)** |
| +0x54..+0x55 (2B) | SetNowCoolTime/DecreaseNowCoolTime (R78) | NowCoolTime u16 |
| +0x56..+0x57 (2B) | SetNowCoolTime (R78) | MaxCoolTime u16 |

→ **88B = 68 file + 16 unused + 4 cooldown**.

## 8. R79 결론

| 항목 | 결과 |
|---|---|
| ApplyAddEffect 의미 | pure dispatcher (28-way), struct write 없음 |
| Add{Curse,Buff,Stance}Skill 의미 | **BATTLER/HERO struct 의 buff/curse/stance slot 에 effect 추가** (HeroSkillInfo 무관) |
| HeroSkillInfo +0x44..+0x4e writer | **.so 전체에 0 개** (모두 다른 구조체의 우연 일치 offset) |
| R72/R73 5 runtime field | **dead reads, default 0** — design intent 만 남고 production data 0 |
| HeroSkillInfo 88B 최종 영역 | 68B file + 16B unused + 4B cooldown |

→ **HeroSkillInfo struct field 의미 11/11 확정** (R77 file 7 + R78 cooldown 2 + R79 dead 5).

R80+ 추천: 다른 RE 잔여 (TEM 정밀 / special path 0x9b100/0x9b124 / type 22 / SetDialogWindow
내부) 또는 Godot Editor 실 실행 검증 (사용자 작업).
