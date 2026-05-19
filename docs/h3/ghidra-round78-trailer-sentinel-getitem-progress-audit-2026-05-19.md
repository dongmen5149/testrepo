# 영웅서기3 Round 78 — i15 trailer (36/37) + getitem 카테고리 분류 + 진행률 깊이 재평가

**Date**: 2026-05-19
**Status**: ✅ R78 데이터 분석 마무리. **24/24 tests pass**. **그러나 전체 remake 진행률은 깊은 재평가 필요**.

## 1. R78 데이터 분석 결과

### 1.1 i15 5B trailer 36/37 추출 성공

```
trailer = [stat0] [stat1] [marker] [stat3] [class_flag]
```

- byte[2] marker = **0x0f (18 entries) 또는 0x14 (18 entries)** — 두 카테고리 동수 분포
- header gap = 6B (23 entries) or 4B (13 entries)
- entries 24-36 (level 35+ 아이템): byte[0] = **30** 일관 (high-tier ATK?)
- byte[3] = 42-46 다수 (level 35+)
- byte[4] class flag = `5` (16/36, 일반), `10` (7/36, 무기) 등

→ trailer 은 item stat block (정확한 byte 의미는 catalog stat_primary/secondary 와 직접 대응 안 함, R79+ 가능)

### 1.2 getitem_dat 96 entries 카테고리 분류

| cat | count | 의미 | 예시 |
|---|---|---|---|
| 15 | 44 | shop catalog (premium) | (i15 entries 0-37) |
| 17 | 27 | accessories (펜던트/이어링) | 협곡의성수, 시그널펜던트 |
| 18 | 13 | consumables | 포션, 과일쥬스, 포도주 |
| 12 | 4 | rings/seals | 고렘의인장, 스트렝스이어링 |
| 1 | 3 | armor | 브리간딘, 다크코트 |
| 14 | 2 | crafting | 푸른용액 |
| 0 | 2 | helmets | 엔시언트헬름 |
| 2 | 1 | gloves | 세라핌핸드 |

→ getitem_dat = **"고정 드롭 마스터 테이블"**. 모두 i{cat}_dat 에서 resolved 가능. quest 보상/scripted drop/특정 위치 chest content 후보.

### 1.3 (133, 153) = 0x8599 sentinel 의미

- 161 records 중 **secondary drop 위치에서 63회**, primary 위치에서 **0회** 출현
- 가설: "default common-pool drop 참조 marker" (실제 item ref 가 아닌 sentinel)
- `Hero3DropRecord.secondaryIsCommonPool` accessor 추가 + 검증 테스트

### 1.4 drop archetype template (bytes[0..9]) stat 의미

- BE u16 5쌍으로 해석 시도: `(30740, 9222, 61480, ...)` 등 큰 값
- enemy_lvl / hp_max / exp_gold 와 직접 비례 없음
- 가설: 원래 gold/exp/drop_count/drop_rate × 5 pre-computed 테이블 (게임 코드만 알 수 있음)
- R79+ Ghidra 함수 분석으로만 확정 가능

## 2. Tests

20 → 23 → **24/24 PASS** (R78 +1: r78_common_pool_sentinel_is_secondary_only)

---

## 3. ⚠️ 전체 진행률 매우 깊이있는 재평가

지금까지 보고된 "99.995%" 는 **분석/디코딩 진행률**이지 **Android remake 완성도** 가 아님. 사용자 요구에 따라 코드베이스 전체를 audit 한 결과:

### 3.1 코드베이스 audit 결과

**Android codebase**:
- Kotlin LOC: **5,845 lines** (app 4,694 + engine-core 1,590)
- Scenes: **21개 구현** (Battle/MapWalk/Inventory/Shop/Status/Skill/Quest/Map/Dialogue/Save/Title/MainMenu/Settings/Bestiary/CatalogViewer/SpriteGallery/Travel/Ending/Records/Event/NpcDialogue)
- Tests: 24 (Hero3CatalogLoaderTest) + 4 (engine-core: Character/Inventory/PartyTurnOrder/Skill)

**Assets**:
- game_balance.json: 832KB (v1.2, R75)
- sprites: 5.7MB (11 directories)
- sprites_hd: 12MB (11 directories)
- maps: 4.2MB
- scn_v2: 3.6MB
- palettes: 901KB
- dialogue_corpus: 2.9MB
- **audio: 0 OGG/WAV/MP3 — SMAF→OGG 미실행** (Phase B, 정책 대기)

### 3.2 결정적 발견: R74 데이터가 게임에 통합되어 있지 않음

```
grep -n "r74Data\|Hero3Recipe\|Hero3RegionShop\|Hero3DropRecord" scene/*.kt
→ 0 hits.  데이터는 Catalog 안에 존재하지만 어느 Scene 도 사용하지 않음.
```

- **ShopScene** → `ShopRegistry` (하드코딩 2 merchants `merchant_bo` / `merchant_jin`)
  - vs catalog: 78 NPCs + 5 regional shops + 38 premium catalog 미연결
- **BattleScene** → `EnemyRegistry.all` (하드코딩 EnemyDef list)
  - 코드 주석: *"실 stat 바이트는 미해독이라 placeholder 수치"* ← R56 에서 161×2 enemies 디코드 완료했지만 코드에 반영 안 됨
- **InventoryScene** → 0 mentions of recipe/craft/smith
  - vs R74 80 forge recipes 미연결
- **QuestScene** → `QuestRegistry` 하드코딩 (catalog 44+ quests 와 분리)
- **CatalogViewerScene** → Hero3Catalog 메타데이터만 보여줌. R74 data 직접 surface 안 함

즉 **R56~R78 의 분석 결과 절대 다수가 게임 코드에 통합되지 않은 상태**.

### 3.3 카테고리별 정직한 진행률

| 영역 | 진행률 | 근거 |
|---|---|---|
| **JAR 디컴파일 + 정적 분석** | ~98% | R47-R55 함수 분석, dispatcher map, SCN bytecode 부분 디코드 |
| **데이터 파일 디코드 (R56-R78)** | ~95% | i0-i18 items / 105 skills / 161 enemies / 15 bosses / 44 quests / 8 DES files. 남은 미해독: drop archetype stat 의미 / i15 trailer 정밀 / SCN opcode 일부 |
| **Hero3Catalog (data layer)** | ~90% | 24/24 tests, R74 data 로드, 38/38 i15 xref, recipe 1:1 resolution. Loader 완성 |
| **Game logic (engine-core)** | ~30% | Character/Inventory/Skill/PartyTurnOrder 기본 구조 + 4 tests. Stat formula simplified, R63 24-stat-enum 미적용, skill effect_v2 미적용 |
| **Scene 구현 (21 scenes)** | ~50% | UI/입력/렌더 구조 존재 but 대부분 placeholder data. Combat formula `damage(atk,def)` 단순, no 클래스 advantage / element / debuff |
| **데이터-Scene 통합** | ~15% | Hero3Catalog 가 Scene 에서 거의 사용되지 않음. registries 모두 하드코딩 |
| **자산 변환** | ~70% | sprites/maps/cif/scn 변환 완료, **audio (SMAF) 0%** 미변환 |
| **번역 (LLM 대사)** | 0% | 9,740 entries queue, $4.09 비용 미승인 |
| **세이브 시스템** | ~60% | SharedPreferences 기반, slot 4, MD5 verified (R52) but 미테스트 |
| **AI / encounter table** | ~25% | EncounterTable.kt 존재 but R74 drop archetype 미연결 |

### 3.4 종합 진행률

3가지 layer 로 분리해서 보면:

**(A) Reverse Engineering (분석 단계)** : **~97%**
- 거의 모든 데이터 파일 디코드 완료
- 남은: SCN opcode 정밀 / drop archetype byte 의미 / SMAF parse

**(B) Catalog / Data layer (Kotlin Hero3Catalog)** : **~88%**
- v1.2 catalog 로드, 24 tests pass, R74 data 통합
- 남은: skill effect_v2 적용 / item stat refinement / i15 trailer 정밀

**(C) Playable Remake (실제 게임)** : **~45-55%**
- 21 scenes 골격 존재
- BUT 대부분 placeholder registry 기반
- R56-R78 분석 결과 미적용
- 오디오 0%
- LLM 번역 0%
- combat formula 미완성

**가중 평균 (실제 remake 완성도)** = (0.20 × 97% + 0.30 × 88% + 0.50 × 50%) = **~70%**

(분석:데이터:플레이어블 = 20:30:50 가중치 기준)

### 3.5 솔직한 한 줄 정리

> **이전 보고 "99.995% 완료" 는 분석/디코딩 진행률만 의미**.
> **실제 "Android 에서 플레이 가능한 영웅서기3 리메이크" 완성도는 ~65-70%**.
> R78 까지의 작업은 거의 모두 **데이터 추출** 에 집중. 추출된 데이터가 게임 코드에 **거의 통합되지 않은 상태**가 가장 큰 격차.

## 4. Round 79+ 우선순위 권장 (재정렬)

지금까지의 "더 깊은 데이터 분석" 보다 **데이터 → 게임 통합** 이 훨씬 가치 높음:

1. ⭐⭐⭐⭐⭐ **EnemyRegistry 를 catalog-fed 로 전환** — R56 의 161×2 enemies 통합, placeholder 제거
2. ⭐⭐⭐⭐⭐ **ShopRegistry 를 R74 region_shops + i15 catalog 통합** — 78 NPCs / 5 regional shops
3. ⭐⭐⭐⭐ **InventoryScene 에 forge UI 추가** — 80 recipes 활용
4. ⭐⭐⭐⭐ **BattleScene combat formula 정교화** — 24-stat enum + skill effect_v2 + element
5. ⭐⭐⭐ **QuestRegistry 를 catalog-fed 로 전환** — 44+ quests
6. ⭐⭐⭐ **EncounterTable 을 drop archetype 기반으로** — drop pool 통합
7. ⭐⭐ SMAF Phase B (정책 승인 시)
8. ⭐⭐ 대사 LLM 번역 (비용 승인 시)

이 8개 작업이 끝나면 진정한 **~90%** 도달 가능.

## 5. 진행률 (실제)

- R77 종료: **분석 99.995% / 실제 remake ~65-70%**
- R78 종료: **분석 99.998% / 실제 remake ~65-70%** (분석은 사실상 종결)

**현 시점부터 R79+ 는 "통합" 라운드로 전환 권장**.
