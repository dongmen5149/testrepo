# 영웅서기3 Round 83 — Combat formula 크리티컬 + Drop resolution → 실제 catalog items

**Date**: 2026-05-19
**Status**: ✅ **70/70 tests pass** + APK BUILD SUCCESSFUL. 적 처치 시 R74 drop_dat 가 실제 인벤토리 아이템으로 지급.

## 1. 한 줄

R82 의 catalog enemies가 random battle 에 등장하던 흐름 위에 **실제 drop**까지 통합. `buildDropTable`이 drop_dat 의 (cat, id) pair를 catalog.resolveItem 로 해석 → matched 시 engine-core ID `h3_item_<file>_<pos>` 사용 → R82 의 ItemRegistry.registerExtra 와 연결되어 인벤토리에 진짜 catalog item 추가. 추가로 BattleScene 에 8% **크리티컬 히트** (×1.7배 대미지) 도입.

## 2. 변경 사항

### 2.1 Hero3CatalogBridge.buildDropTable (drop resolution)

**Before (R79~R82)**: drop bytes → `"h3_drop_p_<a>_<b>"` placeholder ID 만 생성. ItemRegistry 에 없으므로 인벤토리 add 실패 (가방 가득 lost 메시지).

**After (R83)**: drop bytes (p1, p2) / (s1, s2) 를 `Hero3ItemRef(cat, id)` 로 보고 `catalog.resolveItem` 호출.
- 매칭 → catalog item 의 카테고리 file + pos 로 engine-core ID `h3_item_<file>_<pos>` 사용. **이 ID 는 R82 ItemRegistry.registerExtra 로 이미 등록되어 있어** 실제 Item resolve 가능.
- 미매칭 → 기존 placeholder fallback.

End-to-end 흐름:
```
적 처치 → enemy.def.dropTable 순회 → probability check →
inventory.add(h3_item_i14_5) → ItemRegistry.get(h3_item_i14_5) → "푸른용액" 등
→ 인벤토리 UI 에 한글 이름 표시 + EventBus 알림
```

### 2.2 BattleScene damage() — 크리티컬 히트

```kotlin
private fun damage(atk: Int, def: Int): Int {
    val raw = max(1, atk - def / 2)
    val isCrit = Random.nextFloat() < 0.08f       // 8% crit
    val variance = (raw * (0.8f + Random.nextFloat() * 0.4f)).toInt()
    val final = if (isCrit) (variance * 1.7f).toInt() else variance
    if (isCrit) pushLog(lang("크리티컬!", "Critical!"))
    return max(1, final)
}
```

- 8% 확률로 ×1.7배 대미지 + "크리티컬!" 로그
- variance 그대로 유지 (0.8 ~ 1.2)
- 적/플레이어 양쪽 모두 적용 (damage() 가 양방향 호출)

R63 24 stat enum (P_DEF / ATT_FIRE 등) 과 R66 skill effect_v2 element/debuff codes 통합은 R84+ (combat depth 본격화).

## 3. Tests

Bridge tests 7 → **8**: `r83_drop_table_resolves_some_to_catalog_item_ids`
- 259 drop entries (R79 카운트 보존) 중 일부 이상이 `h3_item_` 로 resolve 됨을 확인

| Suite | Tests |
|---|---|
| Hero3CatalogLoaderTest | 24 |
| **Hero3CatalogBridgeTest** | **8** (+1) |
| Hero3CatalogProviderTest | 4 |
| **app subtotal** | **36** |
| engine-core (5 suites) | 34 |
| **TOTAL** | **70 / 70 PASS** |

`:app:assembleDebug` BUILD SUCCESSFUL 3s.

## 4. 진행률

| 영역 | R82 | R83 |
|---|---|---|
| Catalog/Data layer | 96% | **97%** |
| **데이터-Scene 통합** | **75%** | **80%** (drop end-to-end) |
| Playable Remake | 70% | **74%** (combat + real drops) |
| **종합 remake** | **82-84%** | **84-86%** |

## 5. 게임 플레이 흐름 (R83)

1. MapWalk → random encounter → catalog 161 enemies 풀에서 player level ±5 pick → BattleScene `h3_n_NNN`
2. 전투 시 8% 확률 크리티컬 (×1.7) → "크리티컬!" 로그
3. 적 처치 →
   - exp/gold 보상 (R56 expGold split)
   - R74 drop_dat primary 30% + secondary 15% 확률 굴림
   - 매칭된 catalog item 인벤토리 추가 → "획득: 푸른용액" 등
   - 보스면 영구 기록 + 자동 세이브

## 6. R84 권장

1. ⭐⭐⭐⭐⭐ **R66 skill effect_v2 통합** — debuff codes / element / 3-slot 처리
2. ⭐⭐⭐⭐ **R63 24 stat enum** — P_DEF, ATT_FIRE/ICE 등 element-aware combat
3. ⭐⭐⭐⭐ **QuestRegistry catalog-fed** (44+ quests R58/R62)
4. ⭐⭐⭐ **BattleScene element advantage** (ATT_FIRE vs DEF_ICE 등)
5. ⭐⭐⭐ **ForgeScene gold cost** (현 모든 recipe 무료)
6. ⭐⭐⭐ **MapWalkScene encounter sprites** → catalog 의 `enemy/eXXXX_bm` 자동 매칭 확인
7. ⭐⭐ SMAF Phase B / LLM 번역 (정책)

## 7. 변경 파일

```
M android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogBridge.kt   (buildDropTable resolution)
M android/app/src/main/java/com/hero3/remake/scene/BattleScene.kt             (crit hit + log)
M android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogBridgeTest.kt (+1 test)
A docs/h3/ghidra-round83-combat-formula-drop-resolution-2026-05-19.md
```
