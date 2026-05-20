# Hero3 Round 99 — HP_DRAIN (life steal) wiring (2026-05-19)

## 0. 한 줄 요약

R99 분기 A. catalog stat enum 의 `HP_DRAIN` 코드를 시전 시점 life steal 로 wiring. `Hero3CatalogSkillIndex.ModifierKind` 9종 → 10종 (`HP_DRAIN` 신규, exact-match). `BattleScene.useSkill` 의 공격 분기 끝에 `tryHpDrainFromSkill(actor, nameKo, dmgDealt)` 호출 — 입힌 데미지 × `drainPct%` 만큼 actor HP 회복 (cap hpMax). 보라색 popup + "흡혈: +N HP" 로그. 117/117 tests (catalog 57→59 +2) + APK BUILD SUCCESSFUL.

## 1. 동기

R91 의 HEAL kind 가 "skill 시전 시 공격 외 즉시 HP 회복" 을 담당하는 반면, `HP_DRAIN` 은 "공격하면서 입힌 데미지의 N% 를 회복" — life steal. catalog 분석 (R91 grep) 에서 식별된 `HP_DRAIN` 코드가 있는데 R98 시점까지 미 wiring. 즉시 + 단발성 효과로 R96 self-buff 패턴이 아닌 직접 적용.

## 2. 산출물

### 2.1 catalog — ModifierKind 9종 → 10종

`android/app/.../catalog/Hero3CatalogSkillIndex.kt`

```kotlin
enum class ModifierKind {
    OFFENSE, HEAL, DEFENSE, CRIT_RATE, CRIT_DEF, ACCURACY, DODGE,
    HP_REGEN, SP_REGEN,
    HP_DRAIN,   // codeName == "HP_DRAIN" only — 시전 시 dmg×N% HP 회복
}
```

### 2.2 BattleScene — life steal wiring

`android/app/.../scene/BattleScene.kt`

- `tryHpDrainFromSkill(actor, nameKo, dmgDealt)` — useSkill 공격 분기 끝에서 호출. catalog HP_DRAIN primaryModifier 0..25 clamp 후, `heal = (dmgDealt * drainPct / 100).coerceAtLeast(1).coerceAtMost(hpMax - hp)`. 0 이하면 no-op. 적용 시 보라색 popup (`rgb(220,120,220)`) + "흡혈: +N HP" / "Drain: +N HP" 로그.
- POISON 부여 / self-buff 등록 다음 단계 (animation 진행 전).

### 2.3 unit tests +2

`android/.../Hero3CatalogLoaderTest.kt`:
- `r99_hp_drain_modifier_kind_matches_only_hp_drain` — 모든 catalog skill 의 HP_DRAIN 합 == manually computed (exact-match `codeName == "HP_DRAIN"`).
- `r99_hp_drain_lookup_returns_zero_for_unknown_engine_name` — sentinel = 0.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 46/46 pass
:app:testDebugUnitTest          → 71/71 pass  (catalog 57→59, +2)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 117/117, 0 failures
```

## 4. R100 권장 작업

R99 으로 catalog stat enum 23종 중 10종 wiring. 남은 후보:

- ⭐⭐ **CURE_STATUS** — 시전 시 actor 의 모든 (혹은 일부) status 제거. `tryCureStatusFromSkill` 신규.
- ⭐⭐ **BUFF_REMOVE** — 시전 시 enemy 의 buff/debuff 제거 (적은 현재 buff 없으므로 효과 미미, enemy buff 시스템 도입 후 의미).
- ⭐⭐ **TAUNT** — `doEnemyAttack` 의 target picker 가 TAUNT buff 가진 member 우선.
- ⭐⭐ **HP_MAX / SP_MAX** — 일시적 hpMax/spMax 증가 buff.
- ⭐⭐ recipe gold cost 분석.
- ⭐⭐ enemy 측 buff 시스템.

R100 = milestone — 짧은 회고 + 다음 phase 계획도 권장.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~92-93% → ~93% (life steal 가시 효과 + catalog stat enum 23종 중 10종 wiring).
