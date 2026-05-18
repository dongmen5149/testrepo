# Round 72 — Android scene 통합 (CatalogViewerScene + BestiaryScene boss rating) (2026-05-19)

> 이번 라운드 목표: R71 의 Hero3Catalog 가 실제 scene 코드에서 사용되도록 통합. MASTER_SPEC §13 의 step 3-4 (stat/item system 통합) 시작.

## 0. 핵심 결과 한 줄

- ⭐⭐⭐⭐⭐ **MainActivity 에 Hero3Catalog lazy 로더 통합** — `MainActivity.catalog: Hero3Catalog by lazy { Hero3CatalogLoader.load(AndroidAssetReader(this)) }`. 모든 scene 에서 접근 가능
- ⭐⭐⭐⭐⭐ **CatalogViewerScene 신규 작성** — R71 catalog 의 raw 데이터 7-tab brower (Overview / Stat Enum / Rarity / Items / Skills / Bosses / DES Status). 메인 메뉴 debug 항목에 추가
- ⭐⭐⭐⭐ **BestiaryScene 에 boss combat_rating 표시 추가** — 선택된 enemy 가 catalog 의 boss 목록과 매칭되면 "권장 lvl: 51" + sprite_idx + misc/story 표시
- ⭐⭐⭐ **build 성공 + 12 unit tests 모두 통과** — graceful degrade 검증 (catalog 없으면 기존 동작 유지)

## 1. MainActivity catalog lazy 통합 (★★★★★)

### 1.1 변경

```kotlin
class MainActivity : ComponentActivity() {

    /** R71 산출물 — game_balance.json v1.1 (582KB) 의 typed Kotlin 표현.
     *  Lazy 로딩 — 첫 사용 시점에 한 번만 파싱. */
    val catalog: Hero3Catalog by lazy {
        Hero3CatalogLoader.load(AndroidAssetReader(this))
    }
}
```

### 1.2 SceneRequest 신규 항목

```kotlin
data object CatalogViewer : SceneRequest()
```

dispatcher:
```kotlin
SceneRequest.CatalogViewer -> pushScene(
    CatalogViewerScene(ctx, input, settings, catalog, cb)
)
```

### 1.3 lazy 의 장점

- TitleScene / MainMenuScene 등 catalog 가 필요하지 않은 scene 진입 시 비용 0
- CatalogViewerScene / BestiaryScene (boss section) 진입 시점에만 582KB JSON 파싱
- 두 번째 진입 시는 cache hit

## 2. CatalogViewerScene 신규 (★★★★★)

### 2.1 7 tab 구조

```
1. Overview         — 총 개수 요약 (items 529 / skills 105 / enemies 161 / bosses 15 ...)
2. Stat Enum        — 24/25 codes (R66 의 0x15 TAUNT 포함)
3. Rarity           — 6 prefix (magic/legendary/epic/boss_drop/endgame/quest_reward)
4. Item Categories  — 18 카테고리 (i0~i18) + n_items per category
5. Skill Sets       — 7 weapon (s4~s10) + n_skills per weapon (15)
6. Boss Roster      — 15 normal boss + combat_rating + skill_slots
7. DES Status       — 8 pending files (i15/drop/smith/shop 등)
```

### 2.2 조작

```
< >  : tab 전환
^ v  : row 선택
OK / R : pop (메인 메뉴 복귀)
```

### 2.3 i18n 지원

각 tab 의 label 이 한국어 (settings.isEn=false) 또는 영어 (true) 로 표시.

### 2.4 화면 layout

- 상단 header: "자료집 / 보스 명단" + schema version + "(6/7)" tab index
- tab row: 7 tabs 한 줄로 표시 (current 하이라이트)
- main box: 선택된 tab 의 rows 목록 (scroll 지원)
- footer: 조작 힌트

## 3. BestiaryScene boss combat_rating 추가 (★★★★)

### 3.1 변경

```kotlin
// R72: MainActivity 의 catalog 에서 보스 목록 lazy access
private val catalogBosses: List<Hero3Boss>? by lazy {
    (context as? MainActivity)?.catalog?.bossesNormal
}

private fun bossInfoFor(enemyName: String): Hero3Boss? =
    catalogBosses?.firstOrNull { it.name == enemyName }
```

### 3.2 render 보강

선택된 enemy 가 보스이면 추가 정보 표시:

```
HP 14080
ATK 35
DEF 12
EXP 1200
1200G
★ 보스 권장 lvl: 51              ← R72 신규
sprite #0  story                ← R72 신규
드롭:
- 아이템 70%
- ...
```

### 3.3 graceful degrade

- Context 가 MainActivity 가 아니거나 catalog 로딩 실패 → 기존 BestiaryScene 동작 유지
- 보스가 아닌 일반 enemy → boss 정보 미표시
- EnemyRegistry 의 nameKo 와 catalog 의 name 매칭 안 되면 미표시

## 4. 메인 메뉴 통합

```kotlin
MenuItem(R.string.scene_catalog_viewer, MainActivity.SceneRequest.CatalogViewer, isDebug = true),
```

- res/values/strings.xml: `scene_catalog_viewer` = "Catalog Viewer"
- res/values-ko/strings.xml: `scene_catalog_viewer` = "자료집 (catalog)"

## 5. 빌드 + 검증 결과

```
:app:compileDebugKotlin             BUILD SUCCESSFUL in 4s
:app:testDebugUnitTest              BUILD SUCCESSFUL in 2s
  Hero3CatalogLoaderTest 12 tests   ALL PASSED
```

graceful degrade 검증: BestiaryScene 의 boss 매칭 실패 시 NPE 없이 기존 동작 유지.

## 6. R72 산출물

### 6.1 신규 코드 (1개)

- `android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt` (171 lines, 7-tab catalog browser)

### 6.2 수정 코드 (4개)

- `android/app/src/main/java/com/hero3/remake/MainActivity.kt` (+lazy catalog, +SceneRequest.CatalogViewer)
- `android/app/src/main/java/com/hero3/remake/scene/MainMenuScene.kt` (+1 menu item)
- `android/app/src/main/java/com/hero3/remake/scene/BestiaryScene.kt` (+boss combat_rating display)
- `android/app/src/main/res/values/strings.xml` + `values-ko/strings.xml` (+scene_catalog_viewer)

### 6.3 진행률 갱신

- **R71 종료 ~99.7%** → **R72 종료 ~99.8%** (+0.1%p)
- Android 통합도: MASTER_SPEC §13 step 2 완료 → step 3-4 시작 (stat/item system 부분 통합)
- catalog 의 실제 게임 화면 통합 1개 (BestiaryScene boss rating) + 신규 brower scene 1개

## 7. Round 73 후속 작업

### 7.1 자동 가능 (Android scene 통합 계속)

1. ⭐⭐⭐ **InventoryScene rarity color 표시** — catalog.rarity 활용. item prefix (`|` magic 등) 별 color
2. ⭐⭐⭐ **StatusScene 가 catalog.statName() 사용** — stat 표시 (ATT1/P_DEF 등) 의 일관된 이름
3. ⭐⭐ **BattleScene 의 catalog.statEnum 활용** — skill effect 적용 시 stat enum 매칭
4. ⭐⭐ **SkillScene 의 catalog.skills 활용** — 105 skill 목록 표시
5. ⭐ **ShopScene catalog.items 가격 정보** — game_balance.json 의 price 사용

### 7.2 사용자 환경 필수

R70-R71 동일: DES 8 파일 + LLM 번역 + audio.

## 8. 참고

- ★★★★★ [MASTER_SPEC.md](MASTER_SPEC.md) — Hero3 single reference (§13 step 2-4)
- [Round 71](ghidra-round71-catalog-loader-2026-05-19.md) — Catalog data classes + loader
- [Round 70](ghidra-round70-master-spec-exp-groups-2026-05-19.md) — Master Spec
- (R56-R69) — see MASTER_SPEC §14
- `android/app/src/main/java/com/hero3/remake/catalog/Hero3Catalog.kt` — R71 data classes
- `android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt` — R72 brower
