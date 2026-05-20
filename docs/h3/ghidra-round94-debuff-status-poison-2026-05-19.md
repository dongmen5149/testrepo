# Hero3 Round 94 — 디버프 enum + BattleScene poison apply/tick (2026-05-19)

## 0. 한 줄 요약

engine-core 에 **`Status` enum + `StatusEffect` data class** 신설 (`POISON` 1종 초기), `EnemyInstance.statuses: MutableList<StatusEffect>` 필드 추가. `Hero3CatalogSkillIndex.debuffCountForEngineName(nameKo)` 가 catalog 매칭 hit 의 `effectV2.nDebuffs` 를 노출. `BattleScene.useSkill` 가 nDebuffs > 0 인 skill 으로 적을 처치하지 않으면 POISON (3턴, perTick = max(2, dmg/5)) 부여, `updateEnemyTurn` 가 매 턴 시작 시 tick → HP 감소 + popup + 로그, 만료 시 제거. 적 HP 바 우측에 `독(N)` 인디케이터. 105/105 tests (catalog 53→55 +2, engine 34→38 +4) + APK BUILD SUCCESSFUL.

## 1. 동기

R91-R93 의 ModifierKind 7종 wiring 트랙 외에 catalog effectV2 가 노출하는 또 하나의 게임플레이 dimension = `nDebuffs` count. R66 분석에서 발견된 "디버프 슬롯" 의미를 실 게임에 처음 반영하는 라운드. POISON 한 종만 구현 → 작업 범위 작지만 가시 효과 (HP 자동 감소 / 인디케이터 / 로그) 가 크다. R95+ 에서 BURN/SLOW/STUN 등 enum 확장 가능.

## 2. 산출물

### 2.1 engine-core — Status / StatusEffect

`engine-core/src/commonMain/kotlin/com/hero3/remake/engine/Status.kt` (신규)

```kotlin
enum class Status { POISON }

data class StatusEffect(
    val status: Status,
    var turnsLeft: Int,
    val perTick: Int,
)
```

`engine-core/.../Enemy.kt` — `EnemyInstance` 에 `val statuses: MutableList<StatusEffect> = mutableListOf()` 추가. data class 의 equality 는 statuses 포함 (인스턴스 동일성).

### 2.2 catalog — debuffCountForEngineName

`android/app/.../catalog/Hero3CatalogSkillIndex.kt`

- `fun debuffCountForEngineName(nameKo: String): Int` — fuzzy 매칭 + rank 최대 hit 의 `effectV2.nDebuffs`. 매칭 없음 / effectV2=null = 0.

### 2.3 BattleScene — POISON 적용 + tick + UI

`android/app/.../scene/BattleScene.kt`

- `catalogDebuffCountFor(nameKo)` — index null → 0 fallback.
- `tryApplyPoisonFromSkill(nameKo, lastHitDmg)` — useSkill 의 공격 분기 끝에서 호출. nDebuffs > 0 + 적 alive → POISON 3턴 부여, `perTick = max(2, dmg/5)`. 같은 status 가 이미 있으면 turnsLeft 갱신 (refresh).
- `tickEnemyStatuses()` — `updateEnemyTurn` 의 `doEnemyAttack` 직전 호출. POISON = `hp -= perTick`, popup + 로그. tick 후 enemy.hp <= 0 시 `beginVictory()` 즉시 전환.
- render: 적 HP 바 우측 (`barX + barW - 60f`) 에 `독(N)` / `POI(N)` 텍스트 (light green).

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 38/38 pass  (34→38, +4 from R93)
:app:testDebugUnitTest          → 67/67 pass  (catalog 53→55, +2 / bridge 8 / provider 4)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 105/105, 0 failures
```

**engine-core 신규 `StatusTest`** (4 tests): Status enum 존재 / EnemyInstance.statuses 초기 빈 list / 3턴 tick 시뮬레이션 후 hp -15 + statuses 빈 list / data class equality + copy.

**catalog 신규 (2 tests)**:
- `r94_debuff_count_zero_for_unknown_engine_name`.
- `r94_debuff_count_matches_best_hit_nDebuffs` — 모든 catalog skill 에 대해 helper 결과 == manually computed expected.

## 4. R95 권장 작업

- ⭐⭐⭐ **CRIT_DEF wiring** — `BattleScene.damage(extraCritDefPercent)` 도입, 받는 측 crit multiplier 1.7 - (defPct/100) 감쇄.
- ⭐⭐⭐ **Status enum 확장** — BURN (도트, POISON 와 동등) / SLOW (다음 turn skip 확률) / STUN (1턴 행동 봉인). engine-core StatusEffect tick 분기만 추가하면 됨.
- ⭐⭐ **DEFENSE wiring** — `BattleScene.doEnemyAttack` 의 받는 데미지에 catalog DEFENSE bonus 적용. 적용 시점 (가장 최근 사용 skill?) 정의 필요.
- ⭐⭐ §1.5 ForgeScene recipe bytes[0..1] = gold cost 가설 검증.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~89-90% → ~90% (catalog effectV2.nDebuffs 가 실 게임플레이 상태 이상 시스템에 처음 도달, UI 인디케이터 + tick 데미지 가시).
