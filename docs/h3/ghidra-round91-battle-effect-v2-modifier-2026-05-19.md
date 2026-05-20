# Hero3 Round 91 — BattleScene 데미지/회복에 catalog effect_v2 보정 (2026-05-19)

## 0. 한 줄 요약

R89 의 `Hero3CatalogSkillIndex` 에 **`primaryModifier(skill, kind)`** + **`primaryModifierForEngineName(nameKo, kind)`** 추가. R90 의 SkillScene UI 표시에 그치던 effect_v2 가 BattleScene 의 **실제 데미지 / 회복 수치에 반영**된다. `ModifierKind.OFFENSE` = `ATT*` slot primarySigned 합, `HEAL` = `HP_HEAL*` / `HP_REGEN*` slot primarySigned 합. catalog 매칭이 없거나 effectV2=null → 0 (현 데미지식 무변동). imbalance 방지 clamp ±25. 92/92 tests (catalog 43→46, +3) + APK BUILD SUCCESSFUL.

## 1. 동기

R90 에서 SkillScene 의 detail box 에 `effectSummary` 가 표시되지만, **데미지 식은 R89 시점 그대로** 였다 (engine `powerMul`/`flatBonus` 만). SESSION_HANDOFF §1.2 = R66 effect_v2 의 살아있는 slot 의 `primarySigned` 를 ATK/회복 modifier 로 적용. R91 은 이 통합의 *minimum viable* 형태:

- 매칭 코드 카테고리는 두 종 (`ATT*` / `HP_HEAL*`+`HP_REGEN*`) 만 — 디버프/상태이상 부여는 보류 (engine 측 상태 enum 미존재).
- 매칭 없음 / catalog 미설치 = 현재 데미지 식 그대로.
- clamp 폭 ±25 — catalog primarySigned 값이 0..0xFF u8 raw 일 수 있어 의미 단위 모를 때 큰 변동 방지.

## 2. 산출물

### 2.1 `Hero3CatalogSkillIndex` 신규 API

`android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogSkillIndex.kt`

- `enum class ModifierKind { OFFENSE, HEAL }`.
- `fun primaryModifier(skill: Hero3Skill, kind: ModifierKind): Int` — 살아있는 slot1/2/3 (`!isSentinel && !isZero`) 만 검사. OFFENSE = `codeName.startsWith("ATT")` (ATT1 / ATT1_BASE / ATT2). HEAL = `codeName.startsWith("HP_HEAL")` 또는 `startsWith("HP_REGEN")`. 합산 후 raw Int 반환 (clamp 없음).
- `fun primaryModifierForEngineName(nameKo: String, kind: ModifierKind): Int` — `lookupByName(nameKo)` → `rank` 최대 hit 1개 → `primaryModifier`. 매칭 0 hits = 0.

### 2.2 `BattleScene.useSkill` — 보정값 가산

`android/app/src/main/java/com/hero3/remake/scene/BattleScene.kt`

- `catalogSkillIndex` lazy field (catalog 미설치 시 null).
- `catalogBonusFor(nameKo, heal)` — 보정값 ±25 clamp.
- `useSkill` 의 데미지 식:
  - heal: `healed = intl*powerMul + flatBonus + catalogBonus` (음수 방지 `coerceAtLeast(0)`, HP 상한 `coerceAtMost(target.hpMax - target.hp)` 그대로).
  - 공격: `atk = effectiveAttack*powerMul + flatBonus + catalogBonus`, `damage(atk, def)` 그대로.
- 보정값이 0 이 아니면 한 줄 로그: `(카탈로그 +N)` / `(catalog +N)`.

### 2.3 unit tests (catalog 43→46, +3)

`android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt`

- `r91_skill_index_primaryModifier_handles_null_effect` — effectV2=null → 0 (OFFENSE/HEAL 둘 다).
- `r91_skill_index_primaryModifier_picks_only_matching_codes` — 모든 catalog skill 의 OFFENSE/HEAL 합이 manually computed expected 와 일치 (살아있는 slot × code prefix filter).
- `r91_primaryModifierForEngineName_returns_zero_for_unknown` — sentinel = 0, engine "연사" 는 Int 반환 (값 검증 X, 데이터 의존).

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 34/34 pass
:app:testDebugUnitTest          → 58/58 pass  (catalog 43→46, +3, bridge 8, provider 4)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 92/92, 0 failures
```

## 4. R92 권장 작업

- ⭐⭐⭐ §1.3 **Hero3CatalogItemIndex** — Quest/Skill 인덱스 패턴 3번째 (18 카테고리 × N items, ITEMS 탭 drill-down).
- ⭐⭐ §1.2 확장 — slot1.codeName 의 더 많은 카테고리 매핑: `P_DEF/M_DEF` → 받는 데미지 감소, `CRI_RATE` → 크리티컬 확률 보정, `ACC/DOD` → 명중/회피.
- ⭐⭐ §1.2 디버프 — `nDebuffs > 0` 시 engine 측 상태이상 enum 도입 + BattleScene 에 적용.
- ⭐⭐ §1.5 ForgeScene recipe bytes[0..1] gold cost 가설 검증.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~88% → ~88-89% (catalog effect_v2 가 SkillScene UI → BattleScene 데미지 식까지 도달, 가시적 게임플레이 영향).
