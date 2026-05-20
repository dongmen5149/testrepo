# Hero3 Round 104 — Boss 별 차별화 buff 조합 + 4 enemy buff 전체 wiring (2026-05-19)

## 0. 한 줄 요약

R103 의 enemy DEFENSE_BUFF 한 종 → **3 메인 boss 별로 다른 buff 조합**.

| boss | 컨셉 | buff |
|---|---|---|
| boss_guardian | tank | DEFENSE_BUFF 25% + CRIT_DEF_BUFF 20% |
| boss_chaos    | evasive | DODGE_BUFF 20% + ACCURACY_BUFF 15% |
| boss_sealed   | endgame | BLOCK_BUFF 15% + DEFENSE_BUFF 20% + CRIT_DEF_BUFF 30% |
| 기타 boss     | default | DEFENSE_BUFF 25% (R103 동일) |

4 enemy buff (DEFENSE / DODGE / ACCURACY / BLOCK / CRIT_DEF) 모두 player → enemy 또는 enemy → party 데미지 path 에 wiring. doActorAttack 에도 R97 의 hit-roll + R101 의 block check 추가 (이전엔 무조건 hit 였음). 127/127 tests 유지 (통합 검증, 식 자체는 기존 검증 재사용) + APK BUILD SUCCESSFUL.

## 1. 동기

R103 boss DEFENSE_BUFF 한 종으로 boss 가 단순히 더 단단해진 것만 — 모든 boss 가 같은 경험. R104 부터는 boss 마다 컨셉이 다르다 (guardian = tank, chaos = evasive, sealed = endgame). 그리고 enemy buff 가 player → enemy 식 전체에 닿도록 wiring 일관성 확보.

## 2. 산출물

### 2.1 BattleScene.applyBossBuffs(bossId)

`android/app/.../scene/BattleScene.kt`

```kotlin
private fun applyBossBuffs(bossId: String) {
    fun add(st: Status, pct: Int) {
        enemy.statuses += StatusEffect(st, turnsLeft = 99, perTick = pct)
    }
    when (bossId) {
        "boss_guardian" -> { add(DEFENSE_BUFF, 25); add(CRIT_DEF_BUFF, 20) }
        "boss_chaos"    -> { add(DODGE_BUFF, 20);   add(ACCURACY_BUFF, 15) }
        "boss_sealed"   -> { add(BLOCK_BUFF, 15);   add(DEFENSE_BUFF, 20); add(CRIT_DEF_BUFF, 30) }
        else            -> { add(DEFENSE_BUFF, 25) }
    }
}
```

`init` 블록의 `enemy.statuses += DEFENSE_BUFF 25%` 인라인 → `if (isBoss) applyBossBuffs(enemy.def.id)` 로 분리.

### 2.2 doActorAttack — hit-roll + block + crit-def

기본 공격이 이전엔 무조건 hit 였음. R104 부터:
1. `rollHit(0, enemyBuffPercent(DODGE_BUFF))` 실패 → "빗나감"
2. `enemyBuffPercent(BLOCK_BUFF)` 확률 무효 → "적이 막아냄!"
3. `damage(base, def, extraCritDefPercent = enemyBuffPercent(CRIT_DEF_BUFF))` — crit multiplier 감쇄
4. R103 `applyEnemyDefenseBuff(rawDmg)` 유지

### 2.3 useSkill (공격 분기) — 같은 4종 wiring

기존 R97 hit-roll 은 `targetDodgePct = 0` 이었음 → `enemyBuffPercent(DODGE_BUFF)` 로. BLOCK 체크 추가. `damage()` 에 `extraCritDefPercent = enemyBuffPercent(CRIT_DEF_BUFF)` 추가. DEFENSE_BUFF + SHIELD_PIERCE stacking 은 R103 그대로.

### 2.4 doEnemyAttack — enemy ACCURACY_BUFF

기존 `rollHit(attackerAccPct = 0, targetDodgePct)` → `attackerAccPct = enemyBuffPercent(ACCURACY_BUFF)` 로. boss_chaos 의 ACCURACY 15% 가 적의 명중률 가산 — 회피 어렵게.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 51/51 pass
:app:testDebugUnitTest          → 76/76 pass
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 127/127, 0 failures
```

신규 테스트는 추가하지 않음 — R103 의 식 자체 검증 (`applyEnemyDefenseBuff`) + R97 의 hit-roll 식 검증이 그대로 적용. boss-specific buff 조합은 통합 동작이라 unit test 외 manual smoke 로 검증.

## 4. R105 권장 작업

- ⭐⭐⭐ **enemy buff render 개선** — 현재 적 HP 바 우측 인디케이터가 turnsLeft=99 를 그대로 표시 ("도발(99)") 거추장. boss 전 buff 는 `(∞)` 또는 갯수만 표시.
- ⭐⭐⭐ **BUFF_REMOVE wiring** — 이제 enemy buff 가 있으니 catalog BUFF_REMOVE slot 가진 skill 이 enemy buff 1-N 개 제거. R96 self-buff 패턴 + 역방향.
- ⭐⭐ boss skill 매핑 (R74 활용) — boss 가 catalog skill 사용.
- ⭐⭐ CURE_STATUS — party debuff 시스템 선행 필요.
- ⭐⭐ HP_MAX / SP_MAX / *_BASE.
- ⭐⭐ recipe bytes[0..1] gold cost 분석.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~95% → ~95-96% (boss 별 차별화, 4 enemy buff 전체 wiring).
