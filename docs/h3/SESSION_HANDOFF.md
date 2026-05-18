# Hero3 인수인계 노트 (Round 72 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~99.8%**. R72 **Android scene 통합 시작** — MainActivity 에 lazy catalog 통합 + CatalogViewerScene 신규 (7-tab brower) + BestiaryScene boss combat_rating 표시. 빌드 + 12 unit tests 모두 통과. MASTER_SPEC §13 step 2-3 진행 중.

마지막 commit: `ba002199 feat:영웅서기3 Round 71 — Hero3Catalog data classes + Loader + 12 unit tests (Android 통합 시작)`

**Round 72 산출물 = uncommitted**:
- 신규 doc: [`ghidra-round72-scene-integration-2026-05-19.md`](ghidra-round72-scene-integration-2026-05-19.md)
- 신규 코드 1: `scene/CatalogViewerScene.kt` (171 lines, 7-tab catalog browser)
- 수정 코드 4: MainActivity / MainMenuScene / BestiaryScene / strings.xml ×2
- 빌드 + 12 unit tests 통과 검증

## 1. 즉시 진행 가능한 작업 (R73)

### 1.1 ⭐⭐⭐ InventoryScene rarity color 표시

R72 의 패턴 확장. catalog.rarity 활용:
- item name prefix (`|` magic, `'` legendary, `$` epic, `{` boss_drop, `@` endgame, `}` quest_reward)
- 각 rarity 의 color (blue/gold/purple/orange/red/green) 적용
- 가격 modifier 표시 ("(magic 1.13×)" 등)

### 1.2 ⭐⭐⭐ StatusScene 가 catalog.statName() 사용

stat 표시 (ATT1/P_DEF 등) 의 일관된 이름:
- Hero3Catalog.statName(0x05) → "ATT1"
- 기존 hardcoded "STR/INT/VIT" UI 라벨과 internal stat 매핑

### 1.3 ⭐⭐ BattleScene 의 catalog.statEnum 활용

skill effect 적용 시 catalog.statEnum 으로 buff/debuff lookup. R66 의 debuff context split (0x0d STUN_RESIST_DEBUFF, 0x1c STUN_TRIGGER) 적용.

### 1.4 ⭐⭐ SkillScene 의 catalog.skills 활용

105 skill 목록 표시. 4 카테고리 (weapon_passive / active_attack / active_buff / passive_bonus) 별 그룹화.

### 1.5 ⭐ ShopScene catalog.items 가격 정보

game_balance.json 의 price 사용. rarity modifier (boss_drop 0.03x 등) 자동 적용.

## 2. 사용자 환경 필수 작업 (R70-R72 동일)

- ⭐⭐⭐ DES 8 파일 복호화 (i15/drop/smith/shop) — Hero5 NDK runner
- ⭐⭐⭐ boss skill ID 매핑 최종 확정 (DES 후속)
- ⭐⭐ Dialogue LLM 번역 ($4.09)
- ⭐ SMAF→OGG audio

## 3. Round 72 핵심 발견

### 3.1 MainActivity catalog lazy 통합 (★★★★★)

```kotlin
class MainActivity : ComponentActivity() {
    val catalog: Hero3Catalog by lazy {
        Hero3CatalogLoader.load(AndroidAssetReader(this))
    }
}
```

- TitleScene 진입 시 비용 0
- CatalogViewerScene/BestiaryScene boss section 진입 시점 첫 파싱
- 모든 scene 에서 `(context as? MainActivity)?.catalog` 접근 가능

### 3.2 CatalogViewerScene 7-tab brower (★★★★★)

Overview / Stat Enum / Rarity / Items / Skills / Bosses / DES Status

조작: `<>` tab 전환, `^v` row 선택, `OK/R` 뒤로.

R71 의 catalog 가 실제로 사용되는 입증 + 디버그 / 자료 검증용 scene.

### 3.3 BestiaryScene boss combat_rating 표시 (★★★★)

선택된 enemy 가 catalog 의 보스이면:
- "★ 보스 권장 lvl: 51"
- "sprite #0  story"
표시. graceful degrade (catalog 미로딩 시 기존 동작).

### 3.4 빌드 검증

- `:app:compileDebugKotlin` BUILD SUCCESSFUL
- `:app:testDebugUnitTest` BUILD SUCCESSFUL (R71 12 tests 모두 유지)

## 4. 작업 순서 권장 (R73)

1. `git status` + `git log --oneline -5`
2. `git add` + `git commit` Round 72 산출물
3. **InventoryScene rarity color 통합** (R73 핵심):
   - Hero3Item.rarity field 활용
   - 각 rarity 색상 적용 + prefix 표시
4. **StatusScene stat naming 통일**:
   - catalog.statName() 사용
5. **사용자 환경 진행** (병행):
   - DES 8 파일 복호화

목표 진행률 (R73 종료): Android 통합도 ~50% (InventoryScene + StatusScene 통합 후).

## 5. 참고 문서

- ★★★★★ [MASTER_SPEC.md](MASTER_SPEC.md) — Hero3 single reference (R70)
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 72](ghidra-round72-scene-integration-2026-05-19.md) — ★ 이번 라운드 (scene 통합 시작)
- [Round 71](ghidra-round71-catalog-loader-2026-05-19.md) — Catalog data classes + loader
- [Round 70](ghidra-round70-master-spec-exp-groups-2026-05-19.md) — Master Spec + exp 그룹
- [Round 69](ghidra-round69-ammo-enemy-stat-dialogue-2026-05-19.md) — ammo 정정 + stat scaling
- [Round 68](ghidra-round68-boss-skill-search-gun-marker-fun4f358-2026-05-19.md) — boss skill 검색
- [Round 67](ghidra-round67-skill-header-enemy-trailer-boss-skill-id-2026-05-19.md) — skill header
- [Round 66](ghidra-round66-debuff-codes-combat-rating-v1-1-2026-05-19.md) — debuff codes + v1.1
- [Round 65](ghidra-round65-trailer-effect-mask-signed-2026-05-19.md) — effect mask + signed
- [Round 64](ghidra-round64-balance-export-value-scale-2026-05-19.md) — game_balance.json v1.0
- (R56-R63) — see MASTER_SPEC §14
- [Hero4Catalog](../../apps/hero4-android/app/src/main/java/com/hero4/remake/catalog/Hero4Catalog.kt) — R71 의 reference 패턴
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
