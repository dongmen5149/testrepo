# Hero3 Round 103 — Enemy buff 시스템 (boss DEFENSE_BUFF) (2026-05-19)

## 0. 한 줄 요약

R94 의 `enemy.statuses` (debuff 전용) 컨테이너를 **buff 도 담는 일반화 컨테이너로 확장**. boss 적은 전투 시작 시 자기 `DEFENSE_BUFF 25%` 보유 (99턴 = 사실상 전투 내내). `applyEnemyDefenseBuff(rawDmg)` 가 `doActorAttack` (기본 공격) / `useSkill` 의 공격 분기 (스킬) 모두에서 입힌 데미지를 `rawDmg * (100 - defPct) / 100` 로 감쇄 (clamp `≥ 1`). 일반 적은 변동 없음. 127/127 tests (engine 49→51 +2) + APK BUILD SUCCESSFUL. catalog stat enum 23종 중 15종 wiring 동일, enemy buff 시스템이 첫 등장.

## 1. 동기

R96 부터 R102 까지 모든 buff 가 party 측 (`partyStatuses` 맵) 에만 존재. enemy 측은 R94/R95 debuff (POISON/BURN/SLOW/STUN) 만. 결과적으로 boss 전이 다른 적과 똑같이 hp 만 큰 채로 진행 — 변별력 부족. R103 은 enemy.statuses 컨테이너에 buff 를 함께 담아 boss 전을 본격적인 "tough" 모드로 만든다.

## 2. 산출물

### 2.1 BattleScene — boss enemy buff 초기화

`android/app/.../scene/BattleScene.kt`

- `init` 블록: `if (isBoss) enemy.statuses += StatusEffect(Status.DEFENSE_BUFF, turnsLeft = 99, perTick = 25)`. 일반 적은 변동 없음.
- 신규 `enemyBuffPercent(st: Status): Int` — `enemy.statuses.filter { it.status == st }.sumOf { it.perTick }`. (party `buffPercent` 의 enemy 측 대응 헬퍼.)
- 신규 `applyEnemyDefenseBuff(rawDmg: Int): Int` — `defPct.coerceIn(0, 90)`, 0 이하면 rawDmg 그대로. else `(rawDmg * (100 - defPct) / 100).coerceAtLeast(1)`.
- `doActorAttack`: `damage(...)` 결과 `rawDmg` → `applyEnemyDefenseBuff(rawDmg)` → `dmg`.
- `useSkill` 공격 분기: 같은 패턴 (SHIELD_PIERCE / 일반 데미지 모두에 적용).
- `tickEnemyStatuses` 의 buff 분기 주석을 "enemy 에 부여 안 됨" → "enemy 에도 부여 가능 (R103: boss DEFENSE_BUFF)" 로 갱신. tick 시 효과 없음 (buff 사용처에서 perTick 합산).

### 2.2 unit tests +2

`engine-core/.../StatusTest.kt`

- `r103_enemy_defense_buff_reduces_damage_in_simulation` — apply 식 자체 검증 (5 sample: 100/25→75, 100/50→50, 100/90→10, 100/0→100, 2/90→1 clamp).
- `r103_enemy_statuses_can_hold_buffs_not_just_debuffs` — POISON + DEFENSE_BUFF 같이 컨테이너에 담겨 perTick 합산 시 DEFENSE_BUFF 만 25 로 추출 가능.

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 51/51 pass  (49→51, +2)
:app:testDebugUnitTest          → 76/76 pass
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 127/127, 0 failures
```

## 4. R104 권장 작업

R103 으로 enemy buff 시스템 첫 단추 (boss DEFENSE_BUFF). 자연스러운 확장:

- ⭐⭐⭐ **boss 별 차별화** — boss_guardian/chaos/sealed 등에 따라 다른 buff 조합 (DEFENSE_BUFF / CRIT_DEF_BUFF / DODGE_BUFF 등).
- ⭐⭐⭐ **enemy buff render** — 적 HP 바 우측 인디케이터에 buff 도 표시 (현재 statusLabel 은 buff 종도 다 처리하지만 상시 표시면 boss 전 UI 풍부함).
- ⭐⭐ **BUFF_REMOVE** — 이제 enemy buff 가 있으니 의미 발생. catalog BUFF_REMOVE slot 가진 skill 이 enemy 의 buff 1개 제거.
- ⭐⭐ enemy 측 catalog 보유 skill 매핑 (R74 bossSkillIdsResolved 활용) — boss 가 actual 스킬 사용.
- ⭐⭐ CURE_STATUS — party debuff 시스템 도입 후.
- ⭐⭐ HP_MAX / SP_MAX / CD_REDUCE / *_BASE.
- ⭐⭐ recipe bytes[0..1] gold cost 분석.

## 5. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~94-95% → ~95% (boss 전 변별력 +α, enemy buff 시스템 첫 등장).
