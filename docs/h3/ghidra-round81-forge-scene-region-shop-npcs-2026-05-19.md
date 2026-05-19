# 영웅서기3 Round 81 — ForgeScene (단조) + 5 region_shop NPCs

**Date**: 2026-05-19
**Status**: ✅ **67 tests pass (33 app + 34 engine-core) + APK BUILD SUCCESSFUL**. R74 데이터가 실제 게임 기능 (crafting)으로 첫 사용.

## 1. 한 줄

R80 의 catalog provider/bridge 위에 **첫 실제 게임 기능 통합**:
- `ForgeScene` 신규 — 80 R74 recipes 화면 + 인벤토리 ↔ catalog 매핑 + crafting 거래
- NpcRegistry 에 **region_shop_0..4 NPCs 5개** 추가 → ShopScene 의 R80 region_shop 패턴이 실제로 트리거됨

## 2. ForgeScene 신규

- 위치: `android/app/src/main/java/com/hero3/remake/scene/ForgeScene.kt` (140 LOC)
- 라우팅: `SceneRequest.Forge` + MainMenu menu entry "단조" / "Forge"
- 동작:
  1. `Hero3CatalogBridge.forgeRecipesFromCatalog(catalog)` 로 80 ResolvedRecipe 로드
  2. UP/DOWN 으로 navigation, OK 로 craft 시도
  3. crafting transaction:
     - output cleanName ↔ `ItemRegistry.all.nameKo` 매칭
     - 모든 input cleanName 도 ItemRegistry 매칭 시 진행
     - inputs 1개씩 소비 + output 1개 추가 + EventBus 메시지
     - 매칭 실패 시 안내 메시지 (재료/등록 정의 부족)
  4. catalog 미설치 시 안내 메시지
- detail panel: 선택된 recipe 의 output + inputs 한국어 이름 표시

**한계** (R82+ 작업):
- 현재 ItemRegistry 의 15 entries 만 매칭 가능 → 80 recipe 중 craft 가능한 것은 일부
- input quantity = 1 고정 (재료 다중 수량은 R82)
- gold cost 미반영 (R74 byte[8]=0x64=100% 만 사용)

## 3. NpcRegistry — region_shop NPCs 5개

R74 의 5 region_shops 와 1:1 매핑:

| id | mapId | lv tier | nameKo | nameEn |
|---|---|---|---|---|
| region_shop_0 | 0 | 1-15 | 솔티아 상인 | Soltia Merchant |
| region_shop_1 | 1 | 8-22 | 숲의 상인 | Forest Merchant |
| region_shop_2 | 10 | 16-30 | 협곡 상인 | Canyon Merchant |
| region_shop_3 | 11 | 21-35 | 엔자크 상인 | Enzak Merchant |
| region_shop_4 | 12 | 26-40 | 토레즈 상인 | Toreze Merchant |

→ R80 의 `ShopScene.regionShopStock("region_shop_N")` 가 실제로 발화. MapWalkScene 에서 해당 좌표 인접 시 ShopScene 이 열림.

## 4. Tests

| Suite | Tests |
|---|---|
| Hero3CatalogLoaderTest | 24 |
| Hero3CatalogBridgeTest | 5 |
| Hero3CatalogProviderTest | 4 |
| **app subtotal** | **33** |
| CharacterTest | 7 |
| InventoryTest | 6 |
| **NpcRegistryTest (신규)** | **2** |
| PartyTurnOrderTest | 15 |
| SkillTest | 4 |
| **engine-core subtotal** | **34** |
| **TOTAL** | **67/67 PASS** |

`:app:assembleDebug` BUILD SUCCESSFUL 8s.

## 5. 진행률 변화

| 영역 | R80 | R81 |
|---|---|---|
| Catalog/Data layer | 94% | **95%** |
| **데이터-Scene 통합** | **50%** | **60%** (Forge + region_shop NPCs) |
| Playable Remake | 55% | **60%** (첫 crafting feature) |
| **종합 remake** | **74-76%** | **77-79%** |

## 6. R82 권장 (계속 통합)

1. ⭐⭐⭐⭐⭐ **BattleScene combat formula** — 24 stat enum + skill effect_v2 + element advantage
2. ⭐⭐⭐⭐⭐ **EncounterTable** → drop archetype 기반 (region+lvl → 161 enemy 풀)
3. ⭐⭐⭐⭐ **MapWalkScene encounter trigger** → catalog enemies
4. ⭐⭐⭐⭐ **ItemRegistry 확장** → catalog 529 items 의 핵심 50-100 개 등록 (현 15)
5. ⭐⭐⭐ **QuestRegistry** catalog-fed (44+ quests)
6. ⭐⭐⭐ **ForgeScene gold cost / multi-qty** (R74 byte[8] 외 cost 식별)
7. ⭐⭐ SMAF Phase B / LLM 번역 (정책)

## 7. 변경 파일

```
A android/app/src/main/java/com/hero3/remake/scene/ForgeScene.kt           (신규, 140 LOC)
M android/app/src/main/java/com/hero3/remake/MainActivity.kt                (Forge SceneRequest + dispatch + import)
M android/app/src/main/java/com/hero3/remake/scene/MainMenuScene.kt         (Forge menu entry)
M android/app/src/main/res/values/strings.xml                                (scene_forge)
M android/app/src/main/res/values-ko/strings.xml                             (단조)
M engine-core/.../NpcRegistry.kt                                             (5 region_shop NPCs)
A engine-core/.../commonTest/.../NpcRegistryTest.kt                          (신규, 2 tests)
A docs/h3/ghidra-round81-forge-scene-region-shop-npcs-2026-05-19.md
```
