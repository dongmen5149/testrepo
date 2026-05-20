# Hero3 Round 101 — REVIVE + BLOCK wiring (2026-05-19)

## 0. 한 줄 요약

R101 = catalog 통합 28번째 라운드. **REVIVE** (single-shot KO 부활) + **BLOCK** (확률 무효 buff) 두 종 wiring. `ModifierKind` 11종 → 13종, `Status` enum 11종 → 12종 (`BLOCK_BUFF` 신규). REVIVE 는 useSkill 의 heal/공격 두 분기 끝에서 `tryReviveFromSkill(nameKo)` 호출, KO 된 첫 member 를 hpMax × revivePct% 로 부활. BLOCK 은 R96 self-buff 패턴 (3턴), `doEnemyAttack` 가 hit-roll 통과 후 `Random.nextInt(100) < blockPct` 면 "막아냄!" 로 데미지 0. 122/122 tests (engine 47→48 +1, catalog 60→62 +2) + APK BUILD SUCCESSFUL.

## 1. 동기

R100 milestone 후속. catalog stat enum 의 두 종을 한 라운드에 묶어 wiring:
- **REVIVE** = single-shot effect (R99 HP_DRAIN 패턴).
- **BLOCK** = self-buff status (R96 패턴).

같은 패턴 재사용으로 작업량 작음. catalog stat enum 23종 중 13종 wiring 도달.

## 2. 산출물

### 2.1 catalog — ModifierKind 11종 → 13종

```kotlin
enum class ModifierKind {
    OFFENSE, HEAL, DEFENSE, CRIT_RATE, CRIT_DEF, ACCURACY, DODGE,
    HP_REGEN, SP_REGEN, HP_DRAIN, TAUNT,
    REVIVE,   // 시전 시 KO member 부활 (hpMax × pct%)
    BLOCK,    // 자기 buff — 받는 공격 pct% 무효
}
```

### 2.2 engine — Status 11종 → 12종

`engine-core/.../Status.kt`

- `BLOCK_BUFF` (perTick = 무효 %). BattleScene.doEnemyAttack 가 hit-roll 통과 후 적용.

### 2.3 BattleScene — REVIVE single-shot + BLOCK self-buff

`android/app/.../scene/BattleScene.kt`

- 신규 `tryReviveFromSkill(nameKo)` — catalog REVIVE 값 (0..100 clamp) 이 > 0 이고 KO 된 member 가 있으면 `party.indexOfFirst { hp <= 0 }` 의 hp 를 `(hpMax * revivePct / 100).coerceAtLeast(1)` 로. 황색 popup + 한국어 로그.
- useSkill 의 heal 분기 + 공격 분기 둘 다 끝에서 `tryReviveFromSkill(s.nameKo)` 호출 (heal 분기에 `registerSelfBuffsFromSkill(actorIdx, s.nameKo)` 도 누락 보강).
- `registerSelfBuffsFromSkill` 가 catalog BLOCK 값 0..25 clamp 후 `BLOCK_BUFF` 3턴 등록.
- `doEnemyAttack` 의 hit-roll 통과 후 BLOCK check 추가 — `blockPct > 0 && Random.nextInt(100) < blockPct` 면 "막아냄/blocked!" 로그 + return (데미지 0).
- `statusLabel` 에 BLOCK_BUFF → `블록/BLK`. enemy tick `when` no-op 분기 확장.

### 2.4 unit tests +3

- engine `r101_status_enum_has_block_buff` — size ≥ 12, BLOCK_BUFF 존재.
- catalog `r101_revive_modifier_kind_matches_only_revive` / `r101_block_modifier_kind_matches_only_block` — exact-match 검증.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 48/48 pass  (47→48, +1)
:app:testDebugUnitTest          → 74/74 pass  (catalog 60→62, +2)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 122/122, 0 failures
```

## 4. R102 권장 작업

catalog stat enum 23종 중 10종 미 wiring 후보:

- ⭐⭐ **CURE_STATUS** — 시전 시 actor (혹은 적) 의 status 제거. 의미는 party 측 debuff 시스템 도입 후 풍부해짐.
- ⭐⭐ **HP_MAX / SP_MAX** — 일시적 max 증가 buff. (저장 호환성 신경 써야 하므로 battle-scoped 별도 트랙.)
- ⭐⭐ **SP_COST_REDUCE / CD_REDUCE** — SP 비용 감소.
- ⭐⭐ **SHIELD_PIERCE** — 방어 무효화 (공격 측 modifier).
- ⭐⭐ **BUFF_REMOVE** — 적 buff 제거 (enemy buff 시스템 선행).
- ⭐⭐ **HP_MAX_BASE / ATT1_BASE / 기타 BASE** — 영구 stat 증가 (서적 사용).
- ⭐⭐ **enemy 측 buff/debuff 시스템** — 더 풍부한 전투.
- ⭐⭐ **recipe bytes[0..1] gold cost 분석**.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~93-94% → ~94% (REVIVE + BLOCK 으로 catalog stat enum 13종 wiring + 전투 옵션 풍부화).
