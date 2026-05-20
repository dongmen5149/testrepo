# Hero3 Round 97 — ACCURACY/DODGE 시스템 + catalog ModifierKind 7종 wiring 완성 (2026-05-19)

## 0. 한 줄 요약

engine `Status` enum 6종 → 8종 (`ACCURACY_BUFF` / `DODGE_BUFF` 2 신규, `perTick` = percent). `BattleScene.rollHit(attackerAccPct, targetDodgePct): Boolean` 신설 (chance = `(90 + acc - dodge).coerceIn(30, 100)`). `useSkill` 의 공격 분기는 actor ACC buff 로 hit-roll, 빗나가면 "$name → 빗나감" 로그 + damage/debuff skip. `doEnemyAttack` 은 target DODGE buff 로 hit-roll, 피하면 "$name → ${target} 회피!" 로그 + 데미지 skip. `registerSelfBuffsFromSkill` 가 catalog ACC/DOD slot 도 R96 패턴으로 buff 등록. **catalog ModifierKind 7종 전체 wiring 완성** (OFFENSE/HEAL/CRIT_RATE/CRIT_DEF/DEFENSE/ACCURACY/DODGE). 111/111 tests (engine 42→44 +2) + APK BUILD SUCCESSFUL.

## 1. 동기

R91~R96 이 ModifierKind 7종 중 5종 wiring. 남은 ACC/DOD 2종을 같은 R96 self-buff 패턴 (battle-scoped `partyStatuses` 맵) 위에 올려 catalog effect_v2 의 모든 stat code 카테고리가 실 게임플레이까지 도달. miss/dodge 시스템은 engine BattleScene 에 처음 도입.

## 2. 산출물

### 2.1 engine-core — Status 2종 추가

```kotlin
enum class Status {
    POISON, BURN, SLOW, STUN,                        // R94/R95 디버프
    CRIT_DEF_BUFF, DEFENSE_BUFF,                     // R96 buff
    ACCURACY_BUFF,    // perTick = +명중 %
    DODGE_BUFF,       // perTick = +회피 %
}
```

### 2.2 BattleScene — hit-roll + ACC/DOD wiring

`android/app/.../scene/BattleScene.kt`

- 신규 `rollHit(attackerAccPct, targetDodgePct): Boolean` — `chance = (90 + acc - dodge).coerceIn(30, 100)`, `Random.nextInt(100) < chance`.
- `useSkill` 공격 분기: actor 의 `ACCURACY_BUFF` 합산 → `rollHit(accPct, 0)`. 실패 시 "빗나감" 로그 + animation 진행 + 데미지/debuff/buff 등록 모두 skip.
- `doEnemyAttack`: target 의 `DODGE_BUFF` 합산 → `rollHit(0, dodgePct)`. 실패 시 "회피!" 로그, 데미지 0.
- `registerSelfBuffsFromSkill`: 기존 CRIT_DEF / DEFENSE 에 더해 catalog `ACCURACY` / `DODGE` primaryModifier 도 ±25 clamp 후 self-buff (3턴) 등록. 로그에 4종 모두 표시 가능.
- `statusLabel` 에 `ACCURACY_BUFF` → `명중/ACC`, `DODGE_BUFF` → `회피/DOD` 추가.
- enemy tick `when` 의 buff 분기에 ACC/DOD 추가 (party-only, no-op).

### 2.3 unit tests (engine 42→44 +2)

- `r97_status_enum_has_accuracy_and_dodge_buff` — 두 BUFF 존재, size ≥ 8.
- `r97_hit_chance_formula_clamps_to_30_100` — `(90 + acc - dodge).coerceIn(30, 100)` 식 검증 (5 sample cases).
- R96 의 `enum == 6` 단정을 `>= 6` 으로 완화.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 44/44 pass  (42→44, +2)
:app:testDebugUnitTest          → 67/67 pass
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 111/111, 0 failures
```

## 4. R98 권장 작업

R97 으로 catalog ModifierKind 7종 + nDebuffs 4종 = **catalog effect_v2 전체 게임플레이 통합 완성**. R98 부터는 catalog 의 다른 dimension / 분석성 작업:

- ⭐⭐ §1.5 **ForgeScene recipe bytes[0..1] = gold cost** 가설 검증 (`tools/recon/` 분석).
- ⭐⭐ Status enum 확장 — REGEN (자기 dot heal) / HASTE (자기 추가 행동) / SHIELD (받는 데미지 흡수).
- ⭐⭐ enemy 측 buff/debuff 시스템 확장 — enemy 가 자기 ACC/DOD buff 부여 가능 → 더 풍부한 전투.
- ⭐⭐ MASTER_SPEC §13 (Android 리메이크 권장 구현 순서) 다음 단계 — region/event 시스템.
- ⭐ Phase C: Dialogue LLM 번역 ($4.09, 사용자 API key 필요).

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~91% → ~92% (catalog effect_v2 stat 카테고리 전체 wiring + miss/dodge 시스템 도입).
