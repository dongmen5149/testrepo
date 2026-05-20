# Hero3 Round 107 — HP_MAX / SP_MAX 일시 buff wiring (2026-05-20)

## 0. 한 줄 요약

catalog `ModifierKind` 에 `HP_MAX` / `SP_MAX` 두 종 추가, `Status` enum 에 `HP_MAX_BUFF` / `SP_MAX_BUFF` 추가. BattleScene 에 `effectiveHpMax(idx)` / `effectiveSpMax(idx)` 헬퍼 도입 후 모든 hpMax/spMax 사용처를 effective max 로 교체 (HP_REGEN tick, useSkill heal, potion, HP_DRAIN, HUD bar 렌더링). grant 시 즉시 bonus 만큼 HP/SP 회복, 만료 시 tickPartyStatuses 가 새 effective max 로 clamp. **132/132 tests + APK BUILD SUCCESSFUL.**

## 1. 코드 변경

### 1.1 `engine-core/Status.kt`

`HP_MAX_BUFF`, `SP_MAX_BUFF` 두 enum 항목 추가. `perTick` = flat HP/SP 가산.

### 1.2 `android/catalog/Hero3CatalogSkillIndex.kt`

`ModifierKind` 17종 → 19종. matcher: `s.codeName == "HP_MAX"` / `"SP_MAX"` (exact).

### 1.3 `android/scene/BattleScene.kt`

- `effectiveHpMax(memberIdx)` = `c.hpMax + buffPercent(idx, HP_MAX_BUFF)`
- `effectiveSpMax(memberIdx)` = `c.spMax + buffPercent(idx, SP_MAX_BUFF)`
- `isBuff()` 에 `HP_MAX_BUFF`, `SP_MAX_BUFF` 추가.
- `registerSelfBuffsFromSkill` 에서 `hpMaxBoost` / `spMaxBoost` (clamp 0..200) 읽음. 신규 부여 시 actor.hp/sp 에 즉시 bonus 만큼 가산 (refresh 시는 turnsLeft 만 갱신, 중복 가산 방지).
- `tickPartyStatuses` 마지막에 c.hp/c.sp 를 새 effective max 로 clamp (만료 후 자연 감소).
- HP_REGEN_BUFF / SP_REGEN_BUFF tick → effective max 기준 부족분만 회복.
- useSkill 의 heal, useConsumable (potion / ether), HP_DRAIN 회복 → 모두 effective max 사용.
- HUD bar 렌더링: `c.hp/c.hpMax` → `c.hp/effectiveHpMax(i)`, ratio coerceAtMost(1f).
- `tickEnemyStatuses` when-exhaustive: HP_MAX_BUFF / SP_MAX_BUFF 분기 추가 (enemy 측 효과 없음 — 현재 buff 적용처 없음).
- `statusLabel` HUD label 추가: HPM/SP최, SPM/SP최.

### 1.4 `Hero3CatalogLoaderTest.kt`

`r107_hp_max_modifier_kind_exact_match`, `r107_sp_max_modifier_kind_exact_match` 두 테스트 추가. 기존 `r93_modifier_kinds_handle_null_effect` / `r93_modifier_kind_engine_lookup_returns_zero_for_unknown_name` 는 enum.values() 순회라 신규 종도 자동 cover.

## 2. 검증

```
./gradlew.bat -p android :engine-core:testDebugUnitTest :app:testDebugUnitTest :app:assembleDebug
→ BUILD SUCCESSFUL in 14s
→ catalog 66→68 (+2), 총 132/132 pass
```

## 3. R108 후속

- party debuff render UI (멤버 행 인디케이터 buff 만 있음 — debuff 도)
- *_BASE 영구 stat (서적/장신구)
- boss skill 매핑 (R74) — 큰 작업
- CD_REDUCE — cooldown 시스템 선행
- recipe bytes[0..1] gold cost 분석
