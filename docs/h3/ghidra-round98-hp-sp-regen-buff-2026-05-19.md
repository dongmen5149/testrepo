# Hero3 Round 98 — HP_REGEN / SP_REGEN ongoing buff wiring (2026-05-19)

## 0. 한 줄 요약

R98 분기 선택: **B (Status 확장)**. catalog stat enum 의 `HP_REGEN` / `SP_REGEN` 코드를 ongoing buff 로 wiring. `Hero3CatalogSkillIndex.ModifierKind` 9종 (HP_REGEN/SP_REGEN 2 신규, exact-match), `Status` enum 10종 (HP_REGEN_BUFF/SP_REGEN_BUFF 2 신규). `registerSelfBuffsFromSkill` 가 두 종 추가 등록, `tickPartyStatuses` 가 라운드 종료 시 살아있는 member 의 HP/SP 를 perTick 만큼 회복 (hpMax/spMax cap). HP 회복은 popup + 로그, SP 회복은 로그. 115/115 tests (engine 44→46 +2, catalog 55→57 +2 +) + APK BUILD SUCCESSFUL.

## 1. 동기

R91 의 `HEAL` ModifierKind 가 `HP_HEAL_INSTANT` + `HP_REGEN` 둘 다 startsWith 매칭하면서 시전 시점에 즉시 회복했지만, `HP_REGEN` 의 자연스러운 의미는 "지속 회복". R98 은 `HP_REGEN` 을 별도 `ModifierKind` 로 추출해 시전 시 즉시 회복 + actor 자기 ongoing buff (3턴) 둘 다 적용 (overlap 의도적). `SP_REGEN` 도 같은 패턴.

R91 HEAL kind 의 startsWith 매칭은 그대로 유지 — R91 시점의 즉시-회복 행동 보존, 새 R98 kind 는 ongoing tick 만 담당. 다른 ModifierKind 와 동일하게 `==` exact match 라 HEAL kind 와 sum 가 다름.

## 2. 산출물

### 2.1 catalog — ModifierKind 7종 → 9종

`android/app/.../catalog/Hero3CatalogSkillIndex.kt`

```kotlin
enum class ModifierKind {
    OFFENSE, HEAL, DEFENSE, CRIT_RATE, CRIT_DEF, ACCURACY, DODGE,
    HP_REGEN,  // codeName == "HP_REGEN" only
    SP_REGEN,  // codeName == "SP_REGEN" only
}
```

`primaryModifier when` 에 두 분기 추가.

### 2.2 engine — Status 8종 → 10종

`engine-core/.../Status.kt`

- `HP_REGEN_BUFF` — perTick = HP/턴.
- `SP_REGEN_BUFF` — perTick = SP/턴.

### 2.3 BattleScene — register + tick

`android/app/.../scene/BattleScene.kt`

- `registerSelfBuffsFromSkill` 가 catalog HP_REGEN / SP_REGEN primaryModifier 값을 0..25 clamp 후 actor 자기 buff 로 3턴 등록. 로그에 `HP재생+N/턴 SP재생+M/턴` 추가.
- `tickPartyStatuses` 가 라운드 종료 시 각 살아있는 member 의 buff 리스트를 순회 — HP_REGEN_BUFF / SP_REGEN_BUFF 이면 `c.hp += min(hpMax-hp, perTick)` / `c.sp += min(spMax-sp, perTick)`. HP 회복 시 popup + 로그, SP 회복 시 로그만. 죽은 member 는 skip.
- `statusLabel` 에 `HP_REGEN_BUFF` → `HP재/HPR`, `SP_REGEN_BUFF` → `SP재/SPR`. enemy tick `when` 에 두 종 분기 (party-only, no-op).

### 2.4 unit tests +4

`engine-core/.../StatusTest.kt`:
- `r98_status_enum_has_regen_buffs` — 두 BUFF 존재, size ≥ 10.
- `r98_regen_tick_simulation_caps_at_max` — 50 → 60 → 70 → 80 (perTick=10, hpMax=100, 3턴), turnsLeft = 0.

`android/.../Hero3CatalogLoaderTest.kt`:
- `r98_hp_regen_modifier_kind_matches_only_hp_regen` — 모든 catalog skill 의 HP_REGEN 합 == manually computed (`codeName == "HP_REGEN"` filter).
- `r98_sp_regen_modifier_kind_matches_only_sp_regen` — 같은 패턴.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 46/46 pass  (44→46, +2)
:app:testDebugUnitTest          → 69/69 pass  (catalog 55→57, +2)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 115/115, 0 failures
```

## 4. R99 권장 작업

R98 으로 Status enum 10종. 자주 등장하는 catalog 코드 중 미 wiring 후보:

- ⭐⭐ **HP_DRAIN** — life steal (공격 시 데미지의 N% HP 회복). ModifierKind 추가 + useSkill 적용.
- ⭐⭐ **CURE_STATUS / BUFF_REMOVE** — cleanse skill (자기 / 적 status 제거).
- ⭐⭐ **TAUNT** — 적이 actor 만 노리도록.
- ⭐⭐ A. recipe gold cost 분석.
- ⭐⭐ C. enemy 측 buff/debuff 시스템.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~92% → ~92-93% (HP/SP 재생 buff 가 게임플레이에서 가시. catalog stat enum 23종 중 9종 wiring).
