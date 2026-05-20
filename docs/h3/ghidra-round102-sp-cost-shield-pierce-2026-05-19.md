# Hero3 Round 102 — SP_COST_REDUCE (self-buff) + SHIELD_PIERCE (공격 modifier) wiring (2026-05-19)

## 0. 한 줄 요약

catalog stat enum 두 종 wiring. **SP_COST_REDUCE** = R96 self-buff 패턴 (3턴), `effectiveSpCost(memberIdx, base) = base * (100 - reducePct) / 100` 가 SP 검사 + 차감에 사용. **SHIELD_PIERCE** = single-shot 공격 modifier — useSkill 의 공격 분기에서 적 방어력을 `def * (100 - piercePct) / 100` 로 effective 적용. `ModifierKind` 13종 → 15종, `Status` enum 12종 → 13종 (`SP_COST_REDUCE_BUFF`). 125/125 tests (engine 48→49 +1, catalog 62→64 +2) + APK BUILD SUCCESSFUL. catalog stat enum 23종 중 15종 wiring.

## 1. 동기

R101 후속. catalog stat enum 의 두 종 — 하나는 R96 buff 패턴 재사용 (SP_COST_REDUCE), 하나는 single-shot 공격 modifier (SHIELD_PIERCE). 같은 라운드에 묶어 wiring.

## 2. 산출물

### 2.1 catalog — ModifierKind 13종 → 15종

```kotlin
SP_COST_REDUCE,  // 자기 buff — 이후 스킬 SP 비용 perTick% 감소
SHIELD_PIERCE,   // 공격 시 적 방어력 perTick% 무시
```

### 2.2 engine — Status 12종 → 13종

`engine-core/.../Status.kt`

- `SP_COST_REDUCE_BUFF` (perTick = % 감소).

### 2.3 BattleScene — effectiveSpCost + SHIELD_PIERCE

`android/app/.../scene/BattleScene.kt`

- 신규 `effectiveSpCost(memberIdx, baseCost): Int` — `baseCost * (100 - reducePct) / 100`, reducePct clamp `0..90` (≥1 보장).
- `updateSkillPick` 의 SP 검사 (`actor.sp < cost`) + `useSkill` 의 `actor.sp -= ...` 모두 `effectiveSpCost(actorIdx, s.spCost)` 사용.
- `registerSelfBuffsFromSkill` 가 catalog SP_COST_REDUCE 0..25 clamp 후 `SP_COST_REDUCE_BUFF` 3턴 등록. 로그에 "SP비-N%".
- useSkill 공격 분기에 SHIELD_PIERCE 적용 — catalog SHIELD_PIERCE 0..100 clamp, `effectiveEnemyDef = (def * (100 - piercePct) / 100).coerceAtLeast(0)`, 이걸 `damage(atk, effectiveEnemyDef, extraCritPercent)` 에 전달. piercePct > 0 면 "(방어 관통 -N%)" 로그.
- `statusLabel` + enemy tick `when` 확장.

### 2.4 unit tests +3

- engine `r102_status_enum_has_sp_cost_reduce_buff` — size ≥ 13, BUFF 존재.
- catalog `r102_sp_cost_reduce_modifier_kind_exact_match` / `r102_shield_pierce_modifier_kind_exact_match` — exact-match 검증.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 49/49 pass  (48→49, +1)
:app:testDebugUnitTest          → 76/76 pass  (catalog 62→64, +2)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 125/125, 0 failures
```

## 4. R103 권장 작업

catalog stat enum 23종 중 8종 미 wiring:

- ⭐⭐ **CURE_STATUS / BUFF_REMOVE** — cleanse. 의미 있는 wiring 은 party debuff 시스템 (enemy 처럼) 도입 후.
- ⭐⭐ **HP_MAX / SP_MAX** — 일시 max 증가 buff. battle-scoped 별도 트랙.
- ⭐⭐ **CD_REDUCE** — skill cooldown 시스템 신설 후 의미.
- ⭐⭐ **ATT1_BASE / *_BASE** — 영구 stat (서적/도구 사용). engine + 저장 호환성.
- ⭐⭐ **enemy 측 buff/debuff 시스템** — 더 풍부한 전투.
- ⭐⭐ **recipe bytes[0..1] gold cost 분석**.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~94% → ~94-95% (SP 비용 감소 + 방어 관통, catalog stat enum 15종 wiring).
