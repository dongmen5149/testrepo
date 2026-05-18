# Hero3 인수인계 노트 (Round 71 종료 시점, 2026-05-19)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**Hero3 분석 진행률 ~99.7%**. R71 **Android 리메이크 통합 시작** — Hero3Catalog (19 data classes) + Loader + AndroidAssetReader + 12 unit tests 모두 통과. game_balance.json (582KB) Android assets 배포. MASTER_SPEC §13 step 2 (data loader) 완료. **R72+ 는 scene 통합 또는 사용자 환경 (DES 등) 필수**.

마지막 commit: `940f7195 feat:영웅서기3 Round 70 — Master Spec 통합 문서 + exp_gold 4 그룹 + 자동 분석 종결`

**Round 71 산출물 = uncommitted**:
- 신규 doc: [`ghidra-round71-catalog-loader-2026-05-19.md`](ghidra-round71-catalog-loader-2026-05-19.md)
- 신규 코드 3:
  - `android/app/src/main/java/com/hero3/remake/catalog/Hero3Catalog.kt` (data classes 19 + loader)
  - `android/app/src/main/java/com/hero3/remake/platform/AndroidAssetReader.kt`
  - `android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt` (12 tests)
- 신규 asset: `android/app/src/main/assets/game_balance.json` (582,116 bytes)
- build config 변경: `android/app/build.gradle.kts` (testImplementation org.json)
- PROGRESS.md / SESSION_HANDOFF.md / MEMORY.md 갱신

## 1. 즉시 진행 가능한 작업 (R72+)

### 1.1 ⭐⭐⭐ scene 코드에 Hero3Catalog 통합

R71 의 Catalog 가 노출됐으니 기존 scene 들이 사용:
- **InventoryScene**: catalog.items[].items 직접 사용, rarity color 표시
- **BattleScene**: catalog.enemiesNormal/Hard + catalog.statName() 으로 stat 표시
- **BestiaryScene**: 161 enemies + 15 boss + combat_rating
- **MainActivity**: catalog 로드 후 GameState 에 전달
- **NpcDialogueScene**: 246 string + 9,740 dialogue (R69)

스크립트/코드: 각 scene 의 hardcoded data → catalog 의 typed object 로 전환.

### 1.2 ⭐⭐⭐ Strings catalog 통합

기존 `assets/strings/*` 와 game_balance.json 의 stat_enum/rarity 통합. i18n 준비.

### 1.3 ⭐⭐ ChestRegistry / ShopRegistry catalog 연결

engine-core 의 기존 Registry 들이 game_balance.json 의 item 데이터 직접 참조.

### 1.4 ⭐⭐ skill effect simulator

Hero3SkillEffectV2 의 slot1/2/3 chain 으로 실제 damage 계산. R66 의 schema v2 사용.

### 1.5 ⭐ Compose MP UI 마이그레이션 (Phase C Step 4d)

장기 작업 (~1-2주). engine-core 의 GameView/Scene/UiKit/VirtualKeypadView 등을 Compose MP 로 전환.

## 2. 사용자 환경 필수 작업 (R70 와 동일)

### 2.1 ⭐⭐⭐ DES 8 파일 복호화

- i15_dat (master item table)
- drop_dat / droph_dat / getitem_dat
- smith_dat / smithh_dat / shop_dat / shoph_dat

방법: Hero5 NDK runner (key `"0EP@KO91"` + dat/des_dat tables).

### 2.2 ⭐⭐⭐ boss skill ID 매핑 최종 확정 (H4)

DES 파일 안에 boss AI table 발견 가능.
**Hero3Catalog.bossSkillIdsResolved()** 가 현재 false 반환 — DES 후 true 로 갱신 가능.

### 2.3 ⭐⭐ Dialogue LLM 번역 + SMAF→OGG audio

## 3. Round 71 핵심 발견

### 3.1 Hero3Catalog API (★★★★★)

```kotlin
val catalog: Hero3Catalog = Hero3CatalogLoader.load(AndroidAssetReader(context))

catalog.totalItems     // 529
catalog.totalSkills    // 105
catalog.totalEnemies   // 161
catalog.totalBosses    // 15
catalog.statName(0x05) // "ATT1"

catalog.bossesNormal.first { it.name == "리츠" }
  .trailerDecoded?.combatRating  // 51 (= round(14/2 + 44))

catalog.combatRatingFormulaNormal  // "round(lvl/2 + 44)"
catalog.combatRatingFormulaHard    // "round(lvl/2 + 64)"

catalog.desStatus.pendingFiles.size  // 8
catalog.bossSkillIdsResolved()       // false (DES 후 true)
```

### 3.2 unit tests 12개 모두 통과 (★★★★)

```
✓ load_returns_non_null_catalog
✓ catalog_schema_version_is_1_1
✓ stat_enum_has_24_codes
✓ rarity_has_6_prefixes
✓ items_has_18_categories_and_529_total
✓ skills_has_7_weapon_classes_and_105_total
✓ enemies_has_161_normal_and_161_hard
✓ bosses_has_15_normal_and_15_hard
✓ combat_rating_formula_is_documented
✓ boss_combat_rating_matches_formula      ★ 30 boss entries 모두 match
✓ des_status_has_8_pending_files
✓ boss_skill_ids_resolved_returns_false
```

### 3.3 Hero4 패턴 재사용 (★★★)

Hero4Catalog (R69 Phase C Step 5) 의 패턴을 1:1 복사:
- data class 구조
- AssetReader 기반 로더
- AndroidAssetReader platform 구현
- 별도 catalog 패키지 (`com.hero3.remake.catalog.*`)

→ Hero5 에도 동일 패턴 적용 가능.

## 4. 작업 순서 권장 (R72)

1. `git status` + `git log --oneline -5`
2. `git add` + `git commit` Round 71 산출물
3. **scene 통합 작업 시작** (R72 핵심):
   - MainActivity 에 catalog 로드 추가
   - InventoryScene 가 catalog.items 직접 사용
   - BestiaryScene 가 catalog.enemies/bosses 직접 사용
4. **사용자 환경 진행** (병행):
   - DES 8 파일 복호화 (Hero5 NDK runner)
   - Dialogue LLM 번역 (9,740 entries, $4.09)

목표 진행률 (R72 종료): Android 통합도 ~50% (scene 3-4 개 통합 후).

## 5. 참고 문서

- ★★★★★ [MASTER_SPEC.md](MASTER_SPEC.md) — Hero3 single reference (R70)
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 71](ghidra-round71-catalog-loader-2026-05-19.md) — ★ 이번 라운드 (catalog loader)
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
