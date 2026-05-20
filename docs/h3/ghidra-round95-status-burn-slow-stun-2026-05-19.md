# Hero3 Round 95 — Status enum 확장 (BURN/SLOW/STUN) + BattleScene wiring (2026-05-19)

## 0. 한 줄 요약

R94 의 `Status` enum 1종 (POISON) 을 **4종** (BURN / SLOW / STUN 3 신규) 으로 확장. `BattleScene.tryApplyPoisonFromSkill` 은 catalog `nDebuffs` count 만큼 N 종을 부여 (1=POISON, 2=POISON+BURN, 3=+SLOW, ≥4=+STUN). tick = POISON+BURN 동일 dot, SLOW/STUN 은 `enemyShouldSkipAttack()` 가 적 행동 단계에서 처리 (SLOW 50% skip / STUN 100% skip). 적 HP 바 우측 인디케이터에 4종 모두 표시 (`독/화상/둔화/기절` 또는 `POI/BRN/SLW/STN`). 107/107 tests (engine 38→40 +2) + APK BUILD SUCCESSFUL.

## 1. 동기

R94 가 POISON 만 wiring 한 상태 — catalog skill 의 `nDebuffs` 값이 1 이상이면 무조건 POISON 만 부여하던 좁은 매핑. R95 는 같은 tick 인프라 위에 enum 만 확장하고 effect 분기만 추가해 nDebuffs 가 의미있는 다양화 시그널이 되도록 함. SLOW/STUN 은 도트가 아니라 행동 제어 — 적 공격 단계에서 별도 처리.

## 2. 산출물

### 2.1 engine-core — Status 4종

`engine-core/.../Status.kt`

```kotlin
enum class Status {
    POISON,  // 매 턴 HP -perTick
    BURN,    // 매 턴 HP -perTick (POISON 와 효과 동일, 별개 stack)
    SLOW,    // 적 행동 50% skip
    STUN,    // 적 행동 100% skip
}
```

`StatusEffect` 는 그대로 — `perTick` 는 SLOW/STUN 에서는 unused.

### 2.2 BattleScene — N 종 적용 + tick + skip

`android/app/.../scene/BattleScene.kt`

- `tryApplyPoisonFromSkill` 가 `nDebuffs` 만큼 `[POISON, BURN, SLOW, STUN]` 앞에서부터 take 해 모두 부여 (`turnsLeft = 3`). 중복은 refresh. 로그 한 줄에 모든 부여 status 표시 (`[독/화상/둔화] 부여`).
- `tickEnemyStatuses` 의 `when`: `POISON, BURN -> hp -= perTick`, `SLOW, STUN -> 효과 없음`. tick 후 만료 제거.
- 신규 `enemyShouldSkipAttack(): Boolean` — STUN 있으면 항상 skip + 로그, SLOW 있으면 50% skip + 로그.
- `updateEnemyTurn` 의 호출 순서: tick 먼저 (적이 dot 으로 죽으면 즉시 victory), 살아있으면 skip 판정 → 아니면 `doEnemyAttack`.
- render: 적 HP 바 우측 인디케이터가 4종 라벨 (`독/화상/둔화/기절` / `POI/BRN/SLW/STN`) 자동 처리 (`statusLabel(st, isEn)` 헬퍼).

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 40/40 pass  (38→40, +2 from R94)
:app:testDebugUnitTest          → 67/67 pass
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 107/107, 0 failures
```

신규 engine tests:
- `r95_status_enum_has_burn_slow_stun` — enum 4종 확인.
- `r95_burn_tick_decays_like_poison` — BURN 와 POISON 가 동일 dot 시뮬에서 같은 hp 결과.

## 4. R96 권장 작업

- ⭐⭐⭐ **CRIT_DEF wiring** — engine 측에 character.statuses 도입 후, `damage()` 의 1.7 multiplier 를 target 의 CRIT_DEF 합산으로 감쇄.
- ⭐⭐⭐ **DEFENSE wiring** — actor 의 가장 최근 사용 skill 에 P_DEF/M_DEF 가 있으면 다음 받는 데미지 -X% (자기 버프 status 도입 필요).
- ⭐⭐ **ACCURACY/DODGE 시스템** — engine BattleScene 에 miss/dodge 도입 (현재 무존재) + catalog 보정.
- ⭐⭐ §1.5 ForgeScene recipe bytes[0..1] = gold cost 가설 검증.
- ⭐ Phase C: Dialogue LLM 번역 ($4.09, 사용자 API key 필요).

R94+R95 로 `nDebuffs` 시그널이 풍부해졌으니, 남은 4 ModifierKind (DEFENSE/CRIT_DEF/ACCURACY/DODGE) 는 모두 buff/debuff status 시스템 확장이 자연스러운 길.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~90% → ~90-91% (catalog `nDebuffs` 가 dot 1종 → 4종 (dot+행동 제어) 의 의미 있는 다양화에 도달).
