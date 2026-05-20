# Hero3 Round 106 — Party debuff 시스템 + CURE_STATUS wiring (2026-05-19)

## 0. 한 줄 요약

R94/R95 의 enemy debuff 시스템과 대칭으로 **party 측 debuff 시스템 도입**. `doEnemyAttack` 의 명중 후 8% (boss 15%) 확률로 POISON/BURN/SLOW/STUN 중 1개를 random target 에 3턴 부여. `tickPartyStatuses` 가 POISON/BURN dot 적용 (party hp 감소). 신규 `enterCommandOrSkip()` 가 actor 의 STUN (100%) / SLOW (50%) 시 행동 skip + 로그 + Phase.ANIMATE 로 다음 actor 이동. `ModifierKind.CURE_STATUS` 신규 (catalog 17종 wiring) + `tryCureStatusFromSkill` 가 heal skill 의 CURE_STATUS slot > 0 시 actor 자기 debuff 를 N (1..3) 개 제거 (buff 보존). 130/130 tests (catalog 65→66 +1) + APK BUILD SUCCESSFUL.

## 1. 동기

R102 이후 CURE_STATUS 가 wiring 못 된 이유 = party 가 debuff 안 받음. R106 은 party debuff 시스템 + CURE_STATUS 한 라운드에 묶어 둘 다 의미 있게 함. enemy 측 debuff 4종 (POISON/BURN/SLOW/STUN) 을 player 도 받게 됨 — 전투 양방향 대칭성 완성.

## 2. 산출물

### 2.1 catalog — ModifierKind 16종 → 17종

```kotlin
CURE_STATUS,   // 시전 시 actor 자기 debuff 를 N (1..3) 개 제거
```

### 2.2 BattleScene — debuff apply/tick/skip/cure

`android/app/.../scene/BattleScene.kt`

- 신규 `tryApplyDebuffToParty(memberIdx, lastHitDmg)` — `doEnemyAttack` 의 hit 후 호출. `pct = if (isBoss) 15 else 8`, Random.nextInt(100) ≥ pct 면 no-op. else POISON/BURN/SLOW/STUN 중 random 1, 3턴 부여. POISON/BURN 의 `perTick = max(2, dmg/5)`, SLOW/STUN 의 perTick = 0. 같은 status 있으면 turnsLeft refresh.
- `tickPartyStatuses` 확장 — `when` 에 `POISON, BURN -> hp 감소` 추가. dotDmg 누적 후 popup `rgb(170,220,100)` + 로그 "도트: ... -N HP". SLOW/STUN 는 tick 효과 없음 (skip 시점에서 처리).
- 신규 `partyMemberShouldSkipTurn(memberIdx): Boolean` — STUN 100% / SLOW 50% skip.
- 신규 `enterCommandOrSkip()` — 기존 `phase = Phase.COMMAND` 직접 설정을 대체. skip 시 로그 + `phase = Phase.ANIMATE, animTtl = 400L` 으로 다음 actor 호출 트리거. 호출 site = `updateAnimate` 의 다음 actor 진입 / `updateEnemyTurn` 종료 직후.
- `updateEnemyTurn` 종료 직후 `if (aliveCount() == 0) beginDefeat()` 추가 — tick 이 dot 으로 전 멤버 죽일 수 있음.
- 신규 `tryCureStatusFromSkill(actorMemberIdx, nameKo)` — catalog CURE_STATUS primaryModifier coerceIn(0, 3) 명 만큼 partyStatuses[actorMemberIdx] 의 debuff 부터 앞에서 take, buff 보존. useSkill heal 분기 끝에 hook. 제거 시 "상태이상 회복: <라벨>" 로그.

### 2.3 unit tests +1

`android/.../Hero3CatalogLoaderTest.kt`

- `r106_cure_status_modifier_kind_exact_match` — exact-match 검증.

isBuff 분류는 R105 에 검증됨 (R106 의 CURE_STATUS / BUFF_REMOVE 가 같은 헬퍼 사용).

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 52/52 pass
:app:testDebugUnitTest          → 78/78 pass  (catalog 65→66, +1)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 130/130, 0 failures
```

## 4. R107 권장 작업

catalog stat enum 23종 중 17종 wiring. 남은 6종:

- ⭐⭐ **HP_MAX / SP_MAX** — 일시 max 증가 buff (battle-scoped).
- ⭐⭐ **CD_REDUCE** — skill cooldown 시스템 선행.
- ⭐⭐ **ATT1_BASE / 기타 *_BASE** — 영구 stat (서적, engine + 저장).
- 남은 catalog 코드: BLOCK 등은 이미 wiring (R101).

다른 후보:
- ⭐⭐⭐ boss skill 매핑 (R74 활용).
- ⭐⭐ recipe bytes[0..1] gold cost 분석.
- ⭐⭐ render: party 멤버 행 옆 debuff 인디케이터 (현재 buff 만 표시).

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~96% → ~96-97% (party debuff 시스템 + CURE_STATUS 양방향 대칭성 완성).
