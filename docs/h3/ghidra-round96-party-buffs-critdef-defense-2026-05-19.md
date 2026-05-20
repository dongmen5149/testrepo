# Hero3 Round 96 — Party buff status + CRIT_DEF / DEFENSE wiring (2026-05-19)

## 0. 한 줄 요약

engine `Status` enum 4종 → 6종 (`CRIT_DEF_BUFF` / `DEFENSE_BUFF` 2 신규, **perTick 을 percent 단위로 재해석**). `BattleScene` 에 `partyStatuses: MutableMap<Int, MutableList<StatusEffect>>` battle-scoped 맵 도입 (GameState 직렬화 변경 없음). `useSkill` 가 catalog 의 CRIT_DEF / DEFENSE primaryModifier 값을 ±25 clamp 후 actor 자기 buff status 로 3턴 등록. `doEnemyAttack` 가 target 측 두 buff 합산을 `damage(extraCritDefPercent)` + 최종 데미지 reduction 으로 반영. 라운드 종료 시 `tickPartyStatuses()` 가 turnsLeft 감소 + 만료 제거. 109/109 tests (engine 40→42 +2) + APK BUILD SUCCESSFUL.

## 1. 동기

R94+R95 가 적-측 디버프 4종 (POISON/BURN/SLOW/STUN) 을 wiring 한 반면, R93 이 데이터로 노출만 한 4 ModifierKind (DEFENSE/CRIT_DEF/ACCURACY/DODGE) 중 두 종 (CRIT_DEF/DEFENSE) 은 character 측 buff state 가 전제. R96 은 그 buff state 시스템을 도입하면서 동시에 첫 두 wiring 을 완료. ACCURACY/DODGE 는 BattleScene 에 miss/dodge 시스템이 아직 없어 R97+ 분리.

### Character data class 를 건드리지 않은 이유

`Character` 는 `GameState` 직렬화 (parcel/JSON) 대상이라 필드 추가 시 save 호환성 영향 가능. buff/debuff 는 battle-scoped (전투 종료 시 소실) 이므로 `BattleScene` 안의 `MutableMap<Int, List>` 로 충분. R94 의 `EnemyInstance.statuses` 와 동등한 패턴이지만 저장 안 됨.

## 2. 산출물

### 2.1 engine-core — Status 2종 추가

`engine-core/.../Status.kt`

```kotlin
enum class Status {
    POISON, BURN, SLOW, STUN,           // R94/R95
    CRIT_DEF_BUFF,   // perTick = 받는 crit 감쇄 %
    DEFENSE_BUFF,    // perTick = 받는 데미지 reduction %
}
```

### 2.2 BattleScene — buff lifecycle

`android/app/.../scene/BattleScene.kt`

- `partyStatuses: MutableMap<Int, MutableList<StatusEffect>>` — battle-scoped.
- `statusesOf(memberIdx)` / `buffPercent(memberIdx, st)` 헬퍼.
- `registerSelfBuffsFromSkill(actorMemberIdx, nameKo)` — useSkill 의 공격 분기 끝에서 호출. catalog `CRIT_DEF` / `DEFENSE` primaryModifier 값을 0..25 clamp 후 actor.statuses 에 3턴 등록 (중복은 refresh, percent 갱신 아님). 로그 한 줄: `자기 버프: 크감+N% 방어+M% (3턴)`.
- `doEnemyAttack`:
  - `critDefPct = buffPercent(targetIdx, CRIT_DEF_BUFF)` → `damage(..., extraCritDefPercent)`.
  - `defPct = buffPercent(targetIdx, DEFENSE_BUFF)` → 최종 `dmg = rawDmg * (100 - defPct) / 100` (clamp ≥ 1).
  - 두 buff 중 하나라도 활성이면 "(버프 흡수: 크감 N% / 방어 M%)" 로그.
- `damage(atk, def, extraCritPercent, extraCritDefPercent)` 시그니처 확장 — crit multiplier = `(1.7f - extraCritDefPercent/100f).coerceIn(1.0f, 1.7f)`.
- `tickPartyStatuses()` — `updateEnemyTurn` 의 한 라운드 종료 분기에서 호출. 모든 buff turnsLeft -= 1, 만료 제거.
- render: `renderPartyPanel` 가 살아있는 멤버 행 우측에 `크감(N) 방어(M)` 인디케이터 (light blue, textSize 8f).
- `statusLabel` 에 `CRIT_DEF_BUFF` → `크감/CDF`, `DEFENSE_BUFF` → `방어/DEF` 추가. enemy tick `when` 에 buff 분기 추가 (party buff 는 enemy 에 부여 안 됨, no-op).

### 2.3 engine tests +2

`engine-core/.../StatusTest.kt`

- `r96_status_enum_has_buff_kinds` — enum size ≥ 4, 두 BUFF 존재.
- `r96_buff_perTick_used_as_percent_not_dot` — BUFF 가 tick 시뮬에서 HP 감소시키지 않는지 확인 (dot 분기는 POISON/BURN 만).
- R95 의 `enum 크기 == 4` 단정을 `>= 4` 로 완화 (R96 에서 6 으로 확장됐기 때문).

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 42/42 pass  (40→42, +2)
:app:testDebugUnitTest          → 67/67 pass
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 109/109, 0 failures
```

## 4. R97 권장 작업

- ⭐⭐⭐ **ACCURACY/DODGE 시스템 신설** — `damage()` 앞에 miss 판정 도입 (10% 기본 + catalog `ACC` slot 가산 / `DOD` slot 회피). engine BattleScene 신규 시스템.
- ⭐⭐ Status enum 추가 (REGEN buff / HASTE 등) — R96 buff 패턴 재사용.
- ⭐⭐ §1.5 ForgeScene recipe bytes[0..1] = gold cost 가설 검증.
- ⭐ Phase C: Dialogue LLM 번역 ($4.09, 사용자 API key 필요).

R91~R96 으로 catalog ModifierKind 7종 중 5종 (OFFENSE/HEAL/CRIT_RATE/CRIT_DEF/DEFENSE) wiring 완료, nDebuffs 4종 wiring 완료. 남은 ACCURACY/DODGE 만 wiring 후 ModifierKind 전체 게임플레이 통합 완성.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~90-91% → ~91% (catalog ModifierKind 7종 중 5종 wiring, buff status 시스템 도입).
