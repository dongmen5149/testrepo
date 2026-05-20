# Hero3 Round 93 — ModifierKind 확장 + BattleScene crit rate 가산 (2026-05-19)

## 0. 한 줄 요약

R91 의 `ModifierKind { OFFENSE, HEAL }` 2종을 **7종** (DEFENSE / CRIT_RATE / CRIT_DEF / ACCURACY / DODGE 5 신규) 으로 확장. 5 신규 카테고리의 데이터는 `Hero3CatalogSkillIndex.primaryModifier` 에서 즉시 조회 가능. **`CRIT_RATE` 는 `BattleScene.damage(extraCritPercent)` 에 실 가산** — engine "연사" 등의 catalog 매칭 hit 에 `CRI_RATE` slot 이 있으면 8% 기본 crit chance 에 percent 단위 가산 (clamp [0,50%]). DEFENSE/CRIT_DEF/ACCURACY/DODGE 는 engine 측 수신 데미지/명중/회피 시스템이 아직 없어 인덱스 노출만, 추후 라운드 wiring. 99/99 tests (catalog 50→53, +3) + APK BUILD SUCCESSFUL.

## 1. 동기

R91 OFFENSE/HEAL 도입 시 catalog effect_v2 의 stat enum 23종 중 ATT*/HP_HEAL*/HP_REGEN* 5종만 매핑. 남은 P_DEF/M_DEF/CRI_RATE/CRI_DEF/ACC/DOD 6 종은 R92 의 ItemIndex 가 끝난 후 R93 의 자연스러운 다음 단계. CRIT_RATE 는 engine `damage()` 가 이미 `Random.nextFloat() < 0.08f` 형태로 crit 을 하고 있어 가산만 하면 즉시 가시화. DEFENSE 등은 engine 측 시스템 확장이 선행되어야 해서 보류.

## 2. 산출물

### 2.1 `Hero3CatalogSkillIndex.ModifierKind` 확장

`android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogSkillIndex.kt`

- 신규 enum constants: `DEFENSE`, `CRIT_RATE`, `CRIT_DEF`, `ACCURACY`, `DODGE`.
- `primaryModifier` 의 `when (kind)` 에 5 신규 분기:
  - DEFENSE   = `codeName == "P_DEF" || codeName == "M_DEF"`
  - CRIT_RATE = `codeName == "CRI_RATE"`
  - CRIT_DEF  = `codeName == "CRI_DEF"`
  - ACCURACY  = `codeName == "ACC"`
  - DODGE     = `codeName == "DOD"`
- buglet 수정: KDoc 안의 `HP_HEAL*/HP_REGEN*` 가 `*/` 로 KDoc 을 조기 종료시키던 문제 → `HP_HEAL* / HP_REGEN*` 공백 분리.

### 2.2 `BattleScene` — CRIT_RATE wiring

`android/app/src/main/java/com/hero3/remake/scene/BattleScene.kt`

- 신규 `catalogCritBonusFor(nameKo)` — `primaryModifierForEngineName(nameKo, CRIT_RATE)` 결과 ±25 clamp.
- `damage(atk, def, extraCritPercent = 0)` 시그니처 확장 — `critChance = (0.08f + extraCritPercent / 100f).coerceIn(0f, 0.5f)`.
- `useSkill` 공격 분기:
  ```kotlin
  val critBonus = catalogCritBonusFor(s.nameKo)
  val dmg = damage(atk, enemy.def.def, extraCritPercent = critBonus)
  ```
- 기본 공격 `doActorAttack` / 적 공격 `doEnemyAttack` 은 변경 없음 (catalog skill 매칭이 없으므로).

### 2.3 unit tests (catalog 50→53, +3)

`android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt`

- `r93_modifier_kinds_match_distinct_code_names` — 5 신규 kind 의 합산이 manually computed expected 와 일치 (모든 catalog skill 검사).
- `r93_modifier_kinds_handle_null_effect` — effectV2=null → 7 kind 모두 0.
- `r93_modifier_kind_engine_lookup_returns_zero_for_unknown_name` — sentinel 입력 → 7 kind 모두 0.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 34/34 pass
:app:testDebugUnitTest          → 65/65 pass  (catalog 50→53, +3, bridge 8, provider 4)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 99/99, 0 failures
```

## 4. R94 권장 작업

- ⭐⭐⭐ **DEFENSE 실 wiring** — `BattleScene.doEnemyAttack` 의 받는 데미지에 catalog DEFENSE bonus 적용. 단, 매칭이 캐릭터 단위 skill 이 아니라 시점 정의 필요 (가장 최근 사용한 skill? 클래스의 평균? 라스트 skill?).
- ⭐⭐ **디버프 통합** — engine 측 `Status` enum (POISON / BURN / SLOW / STUN) 신설 + BattleScene 에 상태 부여 + 턴마다 tick + UI 표시.
- ⭐⭐ **ACCURACY/DODGE 시스템** — engine 측 miss/dodge 도입 + catalog 보정 적용.
- ⭐⭐ §1.5 ForgeScene recipe bytes[0..1] = gold cost 가설 검증.
- ⭐ Phase C: Dialogue LLM 번역 ($4.09, 사용자 API key 필요).

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~89% → ~89-90% (catalog ModifierKind 7종 전체 인덱싱 + CRIT_RATE 실 wiring, 게임플레이 가산 효과 추가).
