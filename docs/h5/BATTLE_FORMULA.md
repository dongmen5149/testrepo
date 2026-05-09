# Hero5 — 전투/데미지 공식 .so 분석 (capstone+lief)

산출 도구: `tools/h5_extract_battle_funcs.py`
원본 dump: `work/h5/analysis/battle_damage_funcs.txt`

분석 대상은 `libHeroesLore5.so` ARM 모드 함수들. 모두 LSB=0 (Thumb 아님).

---

## 1. BATTLER 클래스 — 핵심 멤버 offset (확정)

`BATTLER::IncreaseHP(int delta)` (0x0004b41c, 292B) 디스어셈블 결과:

| offset | 타입 | 의미 |
|---:|---|---|
| `+0xf0` | s32 | **current HP** |
| `+0x180` | s32 | **max HP** |
| `+0x210` | s32 | **spirit buffer / shield HP** (음의 delta 적용 시 우선 차감) |

`Monster::HitedProc` 도 같은 offset 을 통해 HP 를 읽음 (cross-ref 확인).

---

## 2. `BATTLER::IncreaseHP(int delta)` 동작 ─ 의사 코드

```
if cur_hp <= 0:   return           # 죽었으면 부활 없음
if delta < 0 and spirit_buffer > 0:
    # spirit 흡수 경로 (0x4b480~)
    spirit_buffer += delta         # 단, 0 미만 underflow 시 잔량을 HP 로 넘김
elif delta < 0:
    # 일반 데미지 경로 (0x4b490~)
    cur_hp = max(0, cur_hp + delta)
else:
    # 회복 경로
    new_hp = max(0, cur_hp + delta)
    cur_hp = min(new_hp, max_hp)
```

`bic r1, r1, r1, asr #31` 는 `clamp(>= 0)` 의 ARM 관용구 — sign-extend mask 제거.

---

## 3. `EventProc::Event_PlayerDamage(char percent)` ─ **완전 추출**

0x0006d230 (100B). 100% 디스어셈블 가능. 의사 코드:

```python
def Event_PlayerDamage(percent: int) -> None:
    cur = player.hp
    max_ = player.max_hp
    dmg = (percent * max_) // 100        # 0~100% 비율 데미지

    # 즉사 방지: percent == 100 일 때만 cur_hp 까지 떨어뜨림
    if percent == 100:
        dmg = cur
    elif dmg >= cur:
        dmg = cur - 1                    # 1HP 살려둠

    BATTLER.IncreaseHP(-dmg)             # 음수 → 감소
```

이는 **스크립트(.scn) 가 호출하는 환경 데미지 공식** — 함정/추락/이벤트 스크립트의
"체력 N% 감소" 의 정확한 동작이다. 게임이 절대 0% percent 의 즉사를 안 시키는 건 이 보호로직 때문.

`interpreter.gd` 가 이 opcode 를 만나면 이대로 적용하면 된다.

---

## 4. 분석된 함수 요약

| 함수 | 크기 | callee 수 | 비고 |
|---|---:|---:|---|
| `BATTLER::IncreaseHP(int)` | 292 | 3 | HP 증감의 단일 진입점 (위 2 절 참조) |
| `BATTLER::ApplyAddEffect(short, HeroSkillInfo*)` | 496 | 1 | 스킬→배틀러 효과 적용 |
| `BATTLER::InitStatusComputation()` | 212 | 0 | 스탯 합산 초기화 |
| `BATTLER::ApplyBuildupEffect(short, int)` | 712 | 0 | 누적 효과 (poison/bleed) |
| `Monster::AddEffectDamage(short)` | 212 | 10 | 몬스터 데미지 표시(팝업) + IncreaseHP |
| `Monster::HitedProc(int*, int*)` | 340 | 14 | 몬스터 피격 흐름 (palette blend → KnockDown 분기) |
| `EventProc::Event_PlayerDamage(char)` | 100 | 0 | **완전 추출 (3절)** |
| `HERO::HitedProc()` | 108 | 5 | 플레이어 피격 |
| `HERO::HeroSkillAtkHardCode(...)` | 888 | 37 | 클래스/스킬별 하드코드 분기 |
| `TargetEffect::NewHitEffect(...)` | 796 | 20 | 타깃 이펙트 인스턴스화 |
| `HERO::NewHitEffect(...)` | 1712 | 39 | 가장 큰 ─ 모든 데미지 공식의 마스터 |

`HERO::NewHitEffect` 와 `HeroSkillAtkHardCode` 는 callee 만 30+ 개라 추가 분석 시
스킬 multiplier (skill.dat 의 stats[5] = damage% 가설 검증 가능) 와 크리티컬 공식을
정확히 빼낼 수 있다 — 다음 세션 후속 과제로 적합.

---

## 5. 현재 Godot 측 격차

`apps/hero5-godot/scripts/core/battle_system.gd`:
- 플레이어 공격: `dmg = max(1, atk + rand(0..7) - enemy_def/2)` — 임시 공식
- 적 공격: `dmg = max(1, enemy_atk + rand(0..4) - player_def/2)` — 임시 공식
- spirit_buffer / max_hp clamp / 즉사 방지 로직 **미구현**

---

## 6. 후속 진행 (남은 분석)

- `HERO::NewHitEffect` 1712B → 정공식 (atk × pct − def × ?) 추출.
- `HeroSkillAtkHardCode` → 스킬별 분기 (대시/베기/원거리 modifier).
- Event_PlayerDamage 처럼 100% 추출 가능한 `Event_PlayerHeal`, `Event_QuestBoss` 등 시리즈도 동일 패턴 가능.
