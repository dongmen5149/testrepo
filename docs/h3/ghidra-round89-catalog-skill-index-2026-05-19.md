# Hero3 Round 89 — Hero3CatalogSkillIndex + SKILLS 탭 drill-down (2026-05-19)

## 0. 한 줄 요약

R88 의 `Hero3CatalogQuestIndex` 패턴을 그대로 따라 **`Hero3CatalogSkillIndex`** 를 신설 (entries / byWeapon / byFile / colorOf / fileColors / FILE_PALETTE 7색 + effectSummary 헬퍼). `CatalogViewerScene` 의 SKILLS 탭이 기존 7-줄 weapon-요약 → ~115 줄 per-skill drill-down 으로 확장됐고, 7 weapon set 이 sky/orange/mint/magenta/gold/ivory/violet 색으로 즉시 구분된다. effectV2 가 있는 skill 은 한 줄 우측에 `rank=N deb=M  CODE+x/y | ...` 요약 표시. 86/86 tests + APK BUILD SUCCESSFUL.

## 1. 동기

R88 이 quest 인덱스에 byFile/fileColors API 를 추가하면서 “CatalogViewer 의 각 탭이 평탄화 + 색구분 + drill-down 으로 갈 가치가 있다” 는 패턴이 잡혔다. SKILLS 탭은 다음 두 면에서 빈약했다:

1. **요약만 노출**: 7 weapon set 의 `weapon` + `n_skills` 만 보였고, 실제 ~100+ skills 의 name / category / rank / effectV2 가 UI 에서 안 보임.
2. **engine ↔ catalog 미래 bridge**: SkillRegistry (`강타 / 메가 크러쉬 / 광폭난도` 등) 는 weapon-techniques (`섬광 / 창술1..7 / 강타` 등) 와 이름 형태가 달라 단순 1:1 매칭이 불가 — fuzzy lookup API 가 필요.

본 라운드는 (1) 의 UI 노출 + (2) 를 위한 lookup API (`lookupByName` / `lookupByWeapon`) 까지 한 번에 해결.

## 2. 산출물

### 2.1 `Hero3CatalogSkillIndex` (신규)

`android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogSkillIndex.kt`

- `data class Entry(file, weapon, skill)` — weapon set + skill pair 평탄화 view.
- `val entries: List<Entry>` (catalog.totalSkills 와 동일).
- `val byWeapon: Map<String, List<Entry>>` — weapon 라벨별 그룹.
- `val byFile: Map<String, List<Entry>>` — s4..s10_dat 그룹 (7개).
- `fun colorOf(file)` / `fun fileColors()` — R88 quest 인덱스와 동일한 사용성.
- `fun lookupByWeapon(fragment)` / `fun lookupByName(fragment)` — fuzzy 검색.
- `fun effectSummary(skill: Hero3Skill): String?` — effectV2 가 있고 살아있는 slot 이 1개 이상이면 `rank=N (deb=M)  CODE+x/y | …` 한 줄 요약. effectV2=null 이면 null, 모든 slot 이 sentinel/zero 면 `rank=N (no live slot)`.
- `companion val FILE_PALETTE: IntArray` — 7색 (sky / orange / mint / magenta / gold / ivory / violet). R88 quest 팔레트와 충돌 없는 hue spread + 모두 어두운 배경 가독성 OK.

### 2.2 `CatalogViewerScene` SKILLS 탭 확장

`android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt`

- 신규 `skillRows()` 함수 — quest 와 동일한 패턴.
- 헤더: `loaded=N  weapons=M  files=K`.
- weapon 헤더: `=== sX_dat   <weapon>   (n=N) ===` (파일 색).
- skill 행: ` pos=NNN  <name>  [<category>]  r=<rankOrLevel>  · <effectSummary>`.
- 기존 `Row(text, paint?)` 모델 재사용 — alloc 추가 없음, `questPaintCache` 공유.

### 2.3 단위 테스트 5종 추가

`android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt`

- `r89_skill_index_builds_with_seven_weapon_files` — 7 파일 (s4..s10), 평탄화 합계 = catalog.totalSkills.
- `r89_skill_index_groups_by_weapon_label` — byWeapon 키가 비어있지 않고, 알려진 라벨 (창 / 단검) 포함.
- `r89_skill_index_colorOf_distinct_and_stable` — 7 색 distinct, idempotent, 미지 파일 alpha=0xFF.
- `r89_skill_index_lookupByName_finds_known_skill` — "섬광" 검색이 ≥1 결과 + 모든 결과의 name 이 "섬광" 포함.
- `r89_skill_index_effectSummary_handles_null_and_empty` — effectV2 가 있으면 `rank=` 로 시작, 없으면 null.

총: catalog 35 → **40**, 전체 81 → **86**.

## 3. 검증

```
:app:testDebugUnitTest             → 40/40 catalog + 12/12 etc = 52/52, 0 failures
:engine-core:testDebugUnitTest     → 34/34, 0 failures
:app:assembleDebug                 → BUILD SUCCESSFUL, 14M APK
```

## 4. 영향 / 후속

- CatalogViewer SKILLS 탭에서 ~115 skill 의 name / category / rank / effectV2 첫 슬롯 요약을 한눈에 볼 수 있음.
- weapon별 색 구분으로 “지금 보고 있는 스킬이 어느 무기 계열” 인식이 즉시 가능.
- `lookupByName` / `lookupByWeapon` 으로 향후 BattleScene 의 effectV2 적용 / SkillScene 의 catalog 정보 표시가 가능 (engine 의 "강타" → catalog 매칭은 부분 일치 → 사용자가 fuzzy 정책 결정).

## 5. 다음 라운드 (R90) 후보

| 후보 | 가치 | 비고 |
|---|---|---|
| SkillScene 에 catalog effectSummary 표시 | 중상 | engine Skill ↔ Hero3CatalogSkillIndex.lookupByName fuzzy. 일부 (연사 등) 직접 매칭. |
| R66 effect_v2 BattleScene | 상 | catalog 의 살아있는 slot 으로 debuff 적용. |
| QuestRegistry catalogKey | 중 | engine 4 quest 에 optional catalogKey slot 추가 (현재는 null 그대로). |
| ForgeScene recipe bytes[0..1] 정밀화 | 하 | 11-byte recipe 의 미해석 2 byte 가 gold cost 인지 확정. |
| Hero3CatalogItemIndex | 중 | 18 item categories × N items 도 같은 byFile/colorOf 패턴 적용. |

## 6. 산출물 위치

- `android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogSkillIndex.kt` (신규)
- `android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt` (SKILLS 탭 확장)
- `android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt` (R89 tests 5종)
