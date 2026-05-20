# Hero3 Round 100 — Milestone: TAUNT wiring + catalog 통합 트랙 회고 (2026-05-19)

## 0. 한 줄 요약

**R100 milestone.** TAUNT 코드 wiring 으로 catalog stat enum 23종 중 11종 wiring 도달. `ModifierKind` 10종 → 11종, `Status` enum 10종 → 11종 (`TAUNT_BUFF` 신규). `registerSelfBuffsFromSkill` 가 catalog TAUNT primaryModifier > 0 시 actor 자기 buff 등록, `doEnemyAttack` target picker 가 살아있는 TAUNT_BUFF 보유 member 를 우선 선택 (해당이 없으면 기존 random). 119/119 tests (engine 46→47 +1, catalog 59→60 +1) + APK BUILD SUCCESSFUL. **R74~R100 = catalog 통합 27라운드 종료** — 회고는 §4.

## 1. 동기

catalog stat enum 코드 중 TAUNT 는 target picker 변경이라는 새로운 dimension. R96~R99 가 hp/damage/crit/miss/regen/drain 의 수치 변경이었다면 R100 은 행동 결정 logic 의 변경이다. R100 = catalog 통합 27 라운드 milestone — 짧은 회고 + 다음 phase 정렬.

## 2. 산출물

### 2.1 catalog — ModifierKind 10종 → 11종

```kotlin
enum class ModifierKind {
    OFFENSE, HEAL, DEFENSE, CRIT_RATE, CRIT_DEF, ACCURACY, DODGE,
    HP_REGEN, SP_REGEN, HP_DRAIN,
    TAUNT,   // codeName == "TAUNT" — target picker 우선순위
}
```

### 2.2 engine — Status 10종 → 11종

`engine-core/.../Status.kt`

- `TAUNT_BUFF` — perTick 미사용. BattleScene 의 target picker 가 살아있는 보유 member 우선.

### 2.3 BattleScene — register + target picker

- `registerSelfBuffsFromSkill` 가 catalog TAUNT primaryModifier > 0 (clamp 없음, presence flag) 일 때 `TAUNT_BUFF` 3턴 등록.
- `doEnemyAttack` target picker: `taunters = alive.filter { partyStatuses[idx]?.any { it.status == TAUNT_BUFF } == true }`. taunters 비어있지 않으면 그 안에서 random, 비어있으면 alive 전체에서 random (기존 동작).
- 자기 버프 로그에 "도발/TNT" 추가.
- `statusLabel` 에 TAUNT_BUFF → `도발/TNT`. enemy tick `when` no-op 분기 확장.

### 2.4 unit tests +2

- engine `r100_status_enum_has_taunt_buff` — Status size ≥ 11, TAUNT_BUFF 존재.
- catalog `r100_taunt_modifier_kind_matches_only_taunt` — 모든 catalog skill 의 TAUNT 합 == manually computed (exact-match).

## 3. 빌드 / 테스트

```
:engine-core:testDebugUnitTest  → 47/47 pass  (46→47, +1)
:app:testDebugUnitTest          → 72/72 pass  (catalog 59→60, +1)
:app:assembleDebug              → BUILD SUCCESSFUL (APK)
총 119/119, 0 failures
```

## 4. Milestone 회고 — R74~R100 catalog 통합 27 라운드

| 라운드 | 트랙 | 핵심 |
|---|---|---|
| R74-R78 | Data | DES 평문 파싱 (i15/drop/smith/shop/getitem), 17B drop record, archetype clustering, common-pool sentinel. game_balance v1.2. |
| R79-R83 | Bridge | Hero3CatalogBridge + EnemyRegistry catalog-fed + ShopScene region_shop + Hero3CatalogProvider singleton. |
| R84-R87 | Quest | catalog quest 115 entries 파싱, Hero3CatalogQuestIndex, export truncation fix, quest_item_xref 21. |
| R88-R89 | Index | Quest/Skill index 패턴 정착 (byFile/colorOf/fileColors/FILE_PALETTE), CatalogViewer drill-down. |
| R90 | Bridge | SkillScene 첫 catalog 소비 (lookupByName + effectSummary) + Quest.catalogKey 슬롯. |
| R91 | Effect | primaryModifier(OFFENSE/HEAL) — BattleScene 데미지/회복 ±25 보정. |
| R92 | Index | Hero3CatalogItemIndex (패턴 3번째). ITEMS 탭 drill-down. |
| R93 | Effect | ModifierKind 7종 확장 (DEFENSE/CRIT*/ACC/DOD) + CRIT_RATE wiring. |
| R94-R95 | Status | 디버프 4종 (POISON/BURN/SLOW/STUN). enemy.statuses tick / skip. |
| R96-R97 | Status | party buff 4종 (CRIT_DEF/DEFENSE/ACC/DOD). partyStatuses 맵 + hit-roll. catalog ModifierKind 7종 wiring 완성. |
| R98 | Status | HP_REGEN/SP_REGEN ongoing buff. tickPartyStatuses 회복. |
| R99 | Effect | HP_DRAIN life steal. |
| R100 | Status | TAUNT target picker. catalog stat enum 23종 중 11종 wiring + Status enum 11종. |

**누적 진행률**: 분석 ~99.97% → ~99.98% (R73 이후 변동 미미). 리메이크 ~84% (R74 시작 시점) → ~94%. R100 시점에 catalog effect_v2 의 모든 핵심 카테고리가 게임플레이에 도달.

## 5. R101 권장 작업

남은 catalog stat enum (12종 미 wiring 중 의미있는 것):

- ⭐⭐ **CURE_STATUS** — 시전 시 actor status 제거 skill.
- ⭐⭐ **BUFF_REMOVE** — 적 buff 제거 (enemy buff 시스템 선행).
- ⭐⭐ **HP_MAX / SP_MAX** — 일시적 max 증가 buff.
- ⭐⭐ **SP_COST_REDUCE / CD_REDUCE** — SP / cooldown 감소.
- ⭐⭐ **BLOCK / SHIELD_PIERCE** — 방어 무효화.
- ⭐⭐ **REVIVE** — 사망 멤버 부활 skill.
- ⭐⭐ **enemy 측 buff/debuff 시스템** — 더 풍부한 전투.
- ⭐⭐ **recipe bytes[0..1] gold cost 분석**.

## 6. 진행률 갱신

- 분석 ~99.98% (R73 이후 분석 트랙 종료).
- 리메이크 ~93% → ~93-94% (catalog stat enum 11종 wiring, milestone 도달).
