# Hero3 Round 105 — BUFF_REMOVE wiring + enemy buff render 개선 (2026-05-19)

## 0. 한 줄 요약

`ModifierKind.BUFF_REMOVE` 신규 (catalog 16종 wiring 도달). useSkill 공격 분기에서 catalog `BUFF_REMOVE` slot > 0 시 enemy buff 중 N (clamp 1..3) 개 제거 — `isBuff(st)` 헬퍼가 buff/debuff 분류 (POISON/BURN/SLOW/STUN 만 debuff). 적 HP 바 우측 인디케이터의 `turnsLeft > 9` 는 `"∞"` 로 표시 (R103 boss DEFENSE_BUFF 의 turnsLeft=99 등 거추장 회피). 129/129 tests (engine 51→52 +1, catalog 64→65 +1) + APK BUILD SUCCESSFUL.

## 1. 동기

R103/R104 가 enemy buff 시스템 도입 → R105 는 그 buff 를 제거할 수단 추가. catalog `BUFF_REMOVE` 코드가 의미 있게 됨. 함께 R104 의 boss 차별화 buff (turnsLeft=99) 가 인디케이터에 "(99)" 로 거추장하게 보이는 UI 깔끔이.

## 2. 산출물

### 2.1 catalog — ModifierKind 15종 → 16종

```kotlin
BUFF_REMOVE,   // 시전 시 적 buff N (1..3) 개 제거 — debuff 는 보존
```

`primaryModifier when` 에 `codeName == "BUFF_REMOVE"` 분기 추가.

### 2.2 BattleScene — isBuff helper + tryRemoveEnemyBuffsFromSkill

`android/app/.../scene/BattleScene.kt`

- 신규 `isBuff(st: Status): Boolean` — `POISON/BURN/SLOW/STUN = false`, 나머지 9종 buff = true. exhaustive `when`.
- 신규 `tryRemoveEnemyBuffsFromSkill(nameKo)` — catalog BUFF_REMOVE primaryModifier (`coerceIn(0, 3)`) 명 만큼 enemy.statuses 의 buff 부터 앞에서 take. debuff 보존. 제거 시 "적 버프 제거: <라벨/라벨>" 로그.
- useSkill 공격 분기 끝 (REVIVE 호출 다음) 에 `if (enemy.hp > 0) tryRemoveEnemyBuffsFromSkill(s.nameKo)` hook.

### 2.3 render 개선 — turnsLeft > 9 → "∞"

```kotlin
val turn = if (e.turnsLeft > 9) "∞" else e.turnsLeft.toString()
"${statusLabel(e.status, isEn)}($turn)"
```

boss 의 R104 차별화 buff 모두 turnsLeft=99 → `"방어(∞)"` 식으로 표시. POISON 등 일반 debuff (3턴) 는 그대로 `"독(3)"`.

### 2.4 unit tests +2

- engine `r105_buff_remove_filter_keeps_debuffs` — isBuff 분류 검증 (debuff 4종 외 모두 buff, 합 = total).
- catalog `r105_buff_remove_modifier_kind_exact_match` — exact-match.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 52/52 pass  (51→52, +1)
:app:testDebugUnitTest          → 77/77 pass  (catalog 64→65, +1)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 129/129, 0 failures
```

## 4. R106 권장 작업

catalog stat enum 23종 중 16종 wiring. 남은 7종:

- ⭐⭐ **CURE_STATUS** — party debuff 시스템 도입 후. 현재 party 는 debuff 안 받음.
- ⭐⭐ **HP_MAX / SP_MAX** — 일시 max 증가 buff. battle-scoped 별도 트랙.
- ⭐⭐ **CD_REDUCE** — skill cooldown 시스템 신설 선행.
- ⭐⭐ **ATT1_BASE / 기타 *_BASE** — 영구 stat (서적 사용). engine + 저장 호환성.

남은 작업:
- ⭐⭐ boss skill 매핑 (R74 활용) — boss 가 catalog skill 사용 (큰 작업).
- ⭐⭐ party debuff 시스템 — actor 가 dot/SLOW 등 받을 수 있게.
- ⭐⭐ recipe bytes[0..1] gold cost 분석.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~95-96% → ~96% (BUFF_REMOVE 가 catalog 16종 wiring + enemy buff UI 깔끔).
