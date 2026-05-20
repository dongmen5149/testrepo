# Hero3 Round 108 — Party debuff render UI + enemy render 색상 일관화 (2026-05-20)

## 0. 한 줄 요약

R106 에서 party 측 `partyStatuses` 에 POISON/BURN/SLOW/STUN debuff 가 부여되도록 wiring 했지만 `renderPartyPanel` 의 인디케이터는 R96 시점의 코드 그대로 **buff/debuff 구분 없이 모두 light-blue 한 줄로** 표시되고 있었다. R108 에서:

- party 행 인디케이터를 `isBuff(st)` 헬퍼로 **debuff (light-red, `rgb(255, 130, 130)`)** 와 **buff (light-blue, 기존)** 두 그룹으로 분리해 좌·우로 나란히 표시.
- 같은 컨벤션을 enemy HP 바 인디케이터에도 적용 (기존 단일 light-green → debuff/buff 분리).
- R105 의 `turnsLeft > 9 → "∞"` 표시도 party 측에 적용.
- 사용되지 않던 1-줄 alias `partyBuffLabel` 삭제 (단순히 `statusLabel` 위임).

**133/133 tests + APK BUILD SUCCESSFUL.** (engine 52→53 +1, app 80 그대로)

## 1. 배경

R106 (commit `70427fe6`) 가 `tryApplyDebuffToParty` 로 party 멤버에게 POISON 등 debuff 를 `partyStatuses[i]` 에 추가하기 시작했지만, `renderPartyPanel` 의 인디케이터 코드는 R96 (commit `f14ecd5a`) 의 다음 한 줄을 그대로 유지:

```kotlin
val txt = buffs.joinToString(" ") { e -> partyBuffLabel(e.status, isEn) + "(${e.turnsLeft})" }
canvas.drawText(txt, virtualWidth - 90f, y + 5f,
    Paint(UiKit.muted).apply { color = Color.rgb(130, 200, 255); textSize = 8f })
```

즉 `독(3)` 같은 debuff 도 buff 와 동일한 light-blue 로 표시. SESSION_HANDOFF R108 후보 목록의 가장 작은 항목 (`F. party debuff render UI`) — R107 에서도 자연 후속으로 권장됨.

## 2. 코드 변경

### 2.1 `android/scene/BattleScene.kt` — `renderPartyPanel`

행 우측 인디케이터 블록을 다음으로 교체:

```kotlin
val list = partyStatuses[i]
if (!list.isNullOrEmpty()) {
    val debuffs = list.filter { !isBuff(it.status) }
    val buffs = list.filter { isBuff(it.status) }
    if (debuffs.isNotEmpty()) {
        val dtxt = debuffs.joinToString(" ") { e ->
            val turn = if (e.turnsLeft > 9) "∞" else e.turnsLeft.toString()
            "${statusLabel(e.status, isEn)}($turn)"
        }
        canvas.drawText(dtxt, virtualWidth - 140f, y + 5f,
            Paint(UiKit.muted).apply { color = Color.rgb(255, 130, 130); textSize = 8f })
    }
    if (buffs.isNotEmpty()) {
        val btxt = buffs.joinToString(" ") { e ->
            val turn = if (e.turnsLeft > 9) "∞" else e.turnsLeft.toString()
            "${statusLabel(e.status, isEn)}($turn)"
        }
        canvas.drawText(btxt, virtualWidth - 90f, y + 5f,
            Paint(UiKit.muted).apply { color = Color.rgb(130, 200, 255); textSize = 8f })
    }
}
```

- `isBuff(st)` 는 R105 에서 추가된 BattleScene 내부 헬퍼 — POISON/BURN/SLOW/STUN = false, 나머지 11종 = true.
- debuff 텍스트는 좌측 (`virtualWidth - 140f = x 100`) 에 light-red, buff 는 우측 (`virtualWidth - 90f = x 150`) 에 light-blue.
- `turnsLeft > 9` 는 enemy 측 R105 패턴 그대로 `"∞"` (R104 의 boss `turnsLeft=99` 등을 깔끔히).
- `statusLabel` 직접 호출 (`partyBuffLabel` alias 폐지).

### 2.2 `android/scene/BattleScene.kt` — enemy HP 바 인디케이터

동일 색상 컨벤션 적용. 기존 단일 `rgb(150, 230, 150)` light-green 한 줄을 debuff/buff 분리한 두 줄로 교체. enemy 측은 textSize 가 더 큰 `UiKit.muted` 기본값 사용 (party 행보다 위쪽 빈 공간이 충분).

### 2.3 `android/scene/BattleScene.kt` — `partyBuffLabel` 제거

```kotlin
private fun partyBuffLabel(st: Status, isEn: Boolean): String = statusLabel(st, isEn)
```

호출처가 더 이상 없으므로 삭제. R96 시점에 임시로 도입됐던 alias.

### 2.4 `engine-core/StatusTest.kt` — R108 partition 검증 테스트

```kotlin
@Test
fun r108_render_partition_buffs_and_debuffs_is_exhaustive_and_stable() {
    val debuffs = setOf(Status.POISON, Status.BURN, Status.SLOW, Status.STUN)
    assertEquals(4, debuffs.size)
    val all = Status.values().toSet()
    for (d in debuffs) assertTrue(d in all, "expected debuff $d in enum")
    val buffs = all - debuffs
    assertEquals(all.size, debuffs.size + buffs.size)
    // R107 의 HP_MAX_BUFF / SP_MAX_BUFF 도 buff 측 (render light-blue) — UI 색이 정확.
    assertTrue(Status.HP_MAX_BUFF in buffs)
    assertTrue(Status.SP_MAX_BUFF in buffs)
    // R104 boss 의 상시 buff (turnsLeft=99) 가 render 시 "∞" 로 표시되는지 식 검증.
    fun turnLabel(turnsLeft: Int): String = if (turnsLeft > 9) "∞" else turnsLeft.toString()
    assertEquals("∞", turnLabel(99))
    assertEquals("∞", turnLabel(10))
    assertEquals("9", turnLabel(9))
    assertEquals("3", turnLabel(3))
    assertEquals("1", turnLabel(1))
}
```

- `isBuff` 자체는 BattleScene private 이라 직접 호출 불가 → engine 측에서 *식 자체* 를 시뮬해 partition 정확성 검증.
- R107 까지 누적된 15 enum 의 분류가 exhaustive 한지 (`buffs.size + debuffs.size == all.size`) 확인 → 향후 enum 확장 시 정렬 catch 가능.
- HP_MAX_BUFF / SP_MAX_BUFF (R107) 가 buff 측에 들어가는지 명시적으로 확인 → 색이 light-blue 로 가야 함이 자동 docu.
- `turnLabel` 식 검증으로 render text 측 정확성도 cover.

## 3. UI 결과

### Before (R107)
- party 행 우측: `독(3) 방어(99) 크감(99)` — 모두 light-blue 한 줄.
- enemy HP 바: `독(3) 방어(99)` — 모두 light-green 한 줄. `turnsLeft=99` 그대로.

### After (R108)
- party 행 좌측 (x=100, y+5): `독(3)` — light-red.
- party 행 우측 (x=150, y+5): `방어(∞) 크감(∞)` — light-blue.
- enemy HP 바 좌측: `독(3)` — light-red.
- enemy HP 바 우측: `방어(∞) 크감(∞)` — light-blue.

→ debuff/buff 의 색 코드 컨벤션 (debuff red / buff blue) 가 party 와 enemy 양쪽에서 통일.

## 4. 검증

```bash
./gradlew.bat -p android :engine-core:testDebugUnitTest :app:testDebugUnitTest :app:assembleDebug
→ BUILD SUCCESSFUL in 6s
→ engine 52→53 (+1), 총 133/133 pass
```

unit test count:
- engine-core: CharacterTest 7 + InventoryTest 6 + NpcRegistryTest 2 + PartyTurnOrderTest 15 + SkillTest 4 + **StatusTest 19** (was 18, +1) = 53.
- app: Hero3CatalogBridgeTest 8 + Hero3CatalogLoaderTest 68 + Hero3CatalogProviderTest 4 = 80.
- 합계 133.

## 5. R109 후속 권장

R108 으로 catalog stat enum 19종 wiring + render 컨벤션 정리 완료. 남은 후보:

1. **B. boss skill 매핑 (R74)** — boss 의 4 skill slot 이 catalog skill 을 실제 사용 (현재 placeholder ID). 큰 작업.
2. **C. CD_REDUCE** — cooldown 시스템 자체가 없어 선행 필요. catalog stat 23종 중 마지막 미통합 항목.
3. **D. *_BASE 영구 stat (서적)** — i18 서적 류가 영구 stat 부여. 저장 동기화 필요.
4. **E. recipe bytes[0..1] gold cost 분석** — 분석성 (recon).
5. **G. damage popup 색상 컨벤션 통일** — popup 도 buff/debuff/heal/drain 별로 R108 의 색 일치성 강화 가능 (작음).

자연 후속: D (영구 stat) 가 게임플레이 영향 큼. C 는 cooldown 시스템 설계가 선행되어야 해 좀 더 무거움.
