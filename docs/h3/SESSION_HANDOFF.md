# Hero3 인수인계 노트 (Round 90 종료 시점, 2026-05-19 업데이트)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**분석 ~99.98% / Catalog ~99% / 실제 remake ~88%**. R90: `SkillScene` 하단 detail box (40→54px) 에 catalog effectSummary 첫 소비 — `Hero3CatalogSkillIndex.lookupByName(nameKo)` + `effectSummary` → `<weapon>: rank=N (deb=M)  CODE+x/y | …` 한 줄. 매칭 없음 / catalog 미설치는 muted grey fallback. engine "연사" ↔ catalog 정확 매칭 확인. 함께 `Quest.catalogKey: String? = null` 슬롯 추가 (4 bespoke entries 모두 null 유지). 89/89 tests (catalog 40→43, +3) + APK BUILD SUCCESSFUL. R91 권장: §1.2 R66 effect_v2 BattleScene / §1.3 Hero3CatalogItemIndex / §1.5 recipe bytes[0..1] gold cost.

## 1. 다음 세션 즉시 시작 가이드 (R91)

R73 시점에 분석/DES 는 끝났고, R74~R90 는 catalog 데이터를 Android 리메이크 안으로 끌어들이는 통합 라운드들. **R91 부터는 R66 effect_v2 의 실제 데미지 반영 + Item 인덱스 등 "더 깊은 통합" 이 메인 트랙.** 분석 진척은 거의 0 — 통합/UI 완성도가 진행률의 거의 전부.

### 1.0 R88-R90 결과 (참고)

- R88: `Hero3CatalogQuestIndex` 에 byFile/fileColors/colorOf 추가 + `CatalogViewerScene` rowsForTab 을 `List<Row>` 로 작은 리팩터. Quests 탭 quest_00/01/10/11_dat 4 파일 색 구분. commit `9b1de921`.
- R89: `Hero3CatalogSkillIndex` 신설 (Quest 패턴 그대로) + Skills 탭 ~115 줄 per-skill drill-down + 7 weapon 색 구분 + lookupByName/lookupByWeapon/effectSummary. commit `92752a1f`.
- R90: `SkillScene` 에 catalog effectSummary 첫 소비 — engine `nameKo` → fuzzy `lookupByName` → `<weapon>: rank=N (deb=M)  CODE+x/y | …` 한 줄. detail box 40→54px. catalog 미설치 / no-match graceful fallback. + `Quest.catalogKey: String? = null` 슬롯 도입 (4 bespoke null 유지). 89/89 tests, +3 (R90).
- 세 라운드 공통 패턴: catalog index = `byFile` + `colorOf(file)` + `fileColors()` + `FILE_PALETTE: IntArray` + hash fallback. R90 부터 = "본 scene 안에서 lookup 으로 소비".

### 1.1 ✅ R90 완료 — SkillScene catalog effectSummary

(R90 종결, §2.3 round doc 참조)

### 1.2 ⭐⭐⭐⭐ R66 effect_v2 를 BattleScene 데미지 공식에 반영

**작업 위치**: `android/app/src/main/java/com/hero3/remake/scene/BattleScene.kt`

현재 데미지 = `effectiveAtk * powerMul + flatBonus` (engine Skill). R66 분석에서 발견한 effect_v2 살아있는 slot 의 `primarySigned / secondarySigned` 를 ATK/DEF/회복/디버프 modifier 로 적용.

- catalog 매칭이 없으면 현재 식 그대로.
- 매칭이 있고 slot1.codeName 이 `ATT1` / `DEF` / `HP_HEAL_INSTANT` 등 이면 해당 stat 에 가산/곱 적용.
- 디버프 nDebuffs > 0 일 때 target 에 상태이상 부여 (engine 측 상태 enum 신설 필요할 수 있음 — 미존재 시 로그만).

작업량 중급. SkillScene (1.1) 은 R90 에 완료 → R91 부터는 engine 측 stat code 매핑 정리 → BattleScene 적용.

### 1.3 ⭐⭐⭐ Hero3CatalogItemIndex (R88-R89 패턴 3번째)

**작업 위치**: 신규 `android/app/src/main/java/com/hero3/remake/catalog/Hero3CatalogItemIndex.kt`

18 item categories (i0..i18) × N items 를 같은 byFile/colorOf 패턴으로 인덱싱. CatalogViewerScene 의 ITEMS 탭이 18-줄 카테고리 요약 → ~수백 줄 per-item drill-down 으로 확장.

- R71 의 `Hero3Catalog.items` 그대로 사용 (이미 모든 데이터 적재됨).
- 18 카테고리 ≥ 6-슬롯 팔레트 → palette 확장 또는 hash fallback 의 사용 비율 ↑.
- Quest/Skill 인덱스 코드 거의 그대로 복사 → diff 작음.

### 1.4 ✅ R90 완료 — Quest.catalogKey 슬롯 (legacy 텍스트 보존)

**작업 위치**: `engine-core/src/commonMain/kotlin/com/hero3/remake/engine/Quest.kt`

engine 의 4 quest 는 catalog 의 115 quest 와 narrative 가 다른 bespoke 안. 그러나 향후 catalog 안 quest 이름 → engine quest 매핑을 위한 슬롯 자리만 남겨놓는 것은 의미 있음.

- `Quest` data class 에 `val catalogKey: String? = null` 추가 (4 entries 는 모두 null 그대로).
- QuestScene 에서 catalog 인덱스 lookup hook 자리만 추가 (실제 매칭은 사용자가 narrative 정의 시).

작업량 매우 작음. R90 의 “덤” 으로 같이 묶을 만함.

### 1.5 ⭐⭐ ForgeScene recipe bytes[0..1] 정밀화

**작업 위치**: `tools/recon/` + `Hero3Catalog.kt`

R74 의 11-byte recipe 중 bytes[0..1] 은 미해석. gold cost 후보. 변동 폭 + 정렬 패턴 정밀 측정 후 확정 시 `Hero3Recipe.goldCost` 추가, ForgeScene 행에 가격 표시.

분석성 작업 — recipe.json 변동량 측정 + 가설 검증 1-2일치. 필수는 아님.

### 1.6 ⭐ Phase C: Dialogue LLM 번역 (사용자 API key 필요)

- 9,740 entries, $4.09 추정 (Claude Sonnet 4.6).
- R69 의 `work/h3/translation_queue.json` 사용.
- 사용자가 LLM API key 또는 Claude API 직접 호출 가능 시 자동 진행.

## 2. 작업 순서 권장 (R91)

```
1. git status + git log --oneline -5   (R90 commit 확인)
2. §1.2 BattleScene effect_v2 — engine stat code ↔ catalog slot1.codeName 매핑 → 데미지 modifier
   (catalog 매칭이 없으면 현재 식 그대로, fallback 명확)
3. (병행 가능) §1.3 Hero3CatalogItemIndex — R88-R89 패턴 3번째 (18 카테고리)
4. Hero3CatalogLoaderTest 갱신 + 새 unit tests
5. assembleDebug + 89+/89+ tests
6. Round 91 doc + SESSION_HANDOFF/PROGRESS 갱신 + commit
```

목표 진행률 (R91 종료): **분석 ~99.98% 동일, 리메이크 ~88-90%**. (분석 트랙은 사실상 종료, UI/UX/통합이 메인 트랙)

## 3. R73 까지의 핵심 발견 요약 (참고용)

### 3.1 R56-R63 — 데이터 모델링

- R56: enemy_dat (161×2) 19B stat block 발견
- R57: DES 시스템 식별 (key `"0EP@KO91"`)
- R58: standard 5 변종 모두 실패 (→ R73 에서 정정)
- R59: char_dat (10 playable classes)
- R60: skill 7 파일 (105 skills) + boss HP 위치 + 17 item 파일
- R61: item body 정밀 디코드 (i12 ring, i13/i14, i16 enchant)
- R62: trailer bonus pair (177/346 equip) + rarity 7 prefix
- R63: master stat enum 24 codes 100% (i16 enchant Rosetta Stone)

### 3.2 R64-R69 — 정밀화

- R64: game_balance.json v1.0 + value scale + 0x14/0x19 미사용
- R65: skill effect mask + boss 6B trailer + signed 검증
- R66: debuff codes 정밀 + skill effect v2 (3-debuff 발견) + boss combat_rating 공식
- R67: skill header 14B + enemy 2B trailer + boss skill 가설 H1-H4
- R68: gun marker 0x1f + FUN_4f358 재확인
- R69: i14 ammo system + enemy stat scaling + dialogue queue ($4.09)

### 3.3 R70-R73 — 통합 + Android

- R70: MASTER_SPEC 4,700 lines + exp_gold 4 그룹
- R71: Hero3Catalog 19 data classes + Loader + 12 unit tests
- R72: Android scene 통합 (CatalogViewerScene + BestiaryScene boss rating)
- R73: 🏆 DES 8/8 파일 복호화 성공 + SMAF pipeline 가이드

## 4. 산출물 위치

### 4.1 핵심 reference (Android 리메이크 개발자가 가장 자주 봐야 할 것)

- ★★★★★ [`MASTER_SPEC.md`](MASTER_SPEC.md) — 15 sections, 4,700+ lines
- ★★★★ `work/h3/game_balance.json` (582KB v1.1, gitignored regenerable)
- ★★★ `android/app/src/main/assets/game_balance.json` (582KB, Android assets 배포본)

### 4.2 R73 신규 평문 (작업 대기)

- `work/h3/decrypted/i15_dat.0EP@KO91.plain` (7,400B, master shop catalog)
- `work/h3/decrypted/drop_dat.0EP@KO91.plain` (3,080B, drop table)
- `work/h3/decrypted/droph_dat.0EP@KO91.plain`
- `work/h3/decrypted/smith_dat.0EP@KO91.plain` (896B, recipe)
- `work/h3/decrypted/smithh_dat.0EP@KO91.plain`
- `work/h3/decrypted/shop_dat.0EP@KO91.plain` (1,008B)
- `work/h3/decrypted/shoph_dat.0EP@KO91.plain`
- `work/h3/decrypted/getitem_dat.0EP@KO91.plain` (400B)

### 4.3 R71-R72 Android 통합 코드

- `android/app/src/main/java/com/hero3/remake/catalog/Hero3Catalog.kt` (19 data classes)
- `android/app/src/main/java/com/hero3/remake/platform/AndroidAssetReader.kt`
- `android/app/src/main/java/com/hero3/remake/scene/CatalogViewerScene.kt` (R72 신규)
- `android/app/src/test/java/com/hero3/remake/catalog/Hero3CatalogLoaderTest.kt` (12 tests)

### 4.4 R73 신규 도구

- `tools/converter/decrypt_h3_mx_des.py` — DES batch (Hero5 변종)
- `tools/converter/convert_h3_smaf_pipeline.py` — SMAF 자동 pipeline (도구 가용 시)
- [smaf_conversion_guide.md](smaf_conversion_guide.md) — 외부 도구 설치 가이드

## 5. SMAF 변환 정책 정리 (사용자 의사 반영)

R73 종료 시 사용자 정책 확인: **"신뢰도 높은 것만 다운로드"**.

### 5.1 사용 가능한 도구만으로 진행 시 (R74 Phase B 권장 경로)

```
신뢰도 높음:
  ✓ winget Gyan.FFmpeg
  ✓ winget FluidSynth.FluidSynth
  ✓ pip mido / pyFluidSynth / pydub
  ✓ Windows 내장 gm.dls (System32/drivers)
  ✓ Pure Python SMAF→MIDI 변환 (제가 작성, repo 안에 commit)

보류 (사용자 정책):
  ✗ smaf-converter.jar (개인 GitHub)
  ✗ FluidR3_GM.sf2 (비공식 미러)
```

### 5.2 SMAF→MIDI Pure Python 구현 방향 (R74+)

SMAF format 의 score chunk (track data) 만 파싱:
- magic `MMMD` + chunk size
- `CNTI` (Contents Info)
- `MTR` (Score Track) — 핵심: note events
  - `SETD` (sequence setup) — instrument, channel
  - `MTSQ` (sequence data) — note on/off events with timing
  - `MTSP` (instrument param) — FM synth params (변환 시 무시)

→ MTSQ 의 note events 를 표준 MIDI 1.0 (SMF format) 으로 mapping.

장점:
- 신뢰도 100% (자체 코드)
- third-party JAR 의존 없음

단점:
- Yamaha FM 합성 음색 ≠ GM SoundFont — 음색 정확도 ↓
- 멜로디 / 리듬 / 길이는 100% 보존

### 5.3 다음 세션 결정 사항

R74 Phase B 시작 시 사용자 확인:
1. winget + pip 설치 진행 (FFmpeg + FluidSynth + Python packages) — 승인?
2. Pure Python SMAF parser 작성 진행 — 승인?
3. Windows 내장 gm.dls 사용 — 승인?

## 6. 참고 문서

- ★★★★★ [MASTER_SPEC.md](MASTER_SPEC.md) — Hero3 single reference (R73 §10 갱신)
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (R90 최신)
- [Round 90](ghidra-round90-skill-bridge-quest-catalogkey-2026-05-19.md) — SkillScene catalog effectSummary bridge + Quest.catalogKey 슬롯 (이번 라운드)
- [Round 89](ghidra-round89-catalog-skill-index-2026-05-19.md) — SkillIndex + SKILLS 탭 drill-down
- [Round 88](ghidra-round88-quest-tab-file-color-2026-05-19.md) — Quests 탭 file-색상 + QuestIndex byFile API
- [Round 87](ghidra-round87-quest-item-xref-2026-05-19.md) — R62 Quest Item Xref 21 통합
- [Round 86](ghidra-round86-quest-export-truncation-fix-2026-05-19.md) — Quest export truncation 수정 (67→115)
- [Round 85](ghidra-round85-catalog-quest-index-2026-05-19.md) — Hero3CatalogQuestIndex 신설
- [Round 73](ghidra-round73-des-success-smaf-pipeline-2026-05-19.md) — DES 8/8 + SMAF (분석 트랙 종료)
- [smaf_conversion_guide.md](smaf_conversion_guide.md) — SMAF 외부 도구 가이드 (대기 중)
- (R56-R69) — see MASTER_SPEC §14
- `tools/h5_des.py` — Hero5 mx_des_decrypt Python 포팅 (R68 산출, R73 적용)
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
- 모든 converter scripts: `tools/converter/`

## 7. 빠른 시작 (다음 세션 첫 5 분)

```bash
# 1. 현재 git 상태 확인
git status
git log --oneline -5
# 마지막 commit 기대값: R90 — SkillScene catalog effectSummary bridge + Quest.catalogKey

# 2. 이 문서 §1.2 (BattleScene 데미지 공식에 catalog effect_v2 반영) 부터 시작
#    - 읽기: android/app/src/main/java/com/hero3/remake/scene/BattleScene.kt
#    - 참고: catalog Hero3CatalogSkillIndex.lookupByName + slot1.codeName ↔ engine stat code 매핑 정리 필요
#    - 변경: 데미지 식에 catalog primarySigned/secondarySigned 가산/곱

# 3. 테스트 (R90 = 89 tests, R91 추가 시 90+ 기대)
./android/gradlew.bat -p android :app:testDebugUnitTest :engine-core:testDebugUnitTest :app:assembleDebug
```

JDK 경로: `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot` (현재 PC). 집 PC 는 `C:\Program Files\Eclipse Adoptium\jdk-21*` 일 수 있음 — 빌드 전 JAVA_HOME 확인 필요.

---

**다음 세션 시작 시 가장 먼저 할 일**: 이 문서 §1.2 (BattleScene effect_v2 데미지 반영) — R90 에서 SkillScene 의 catalog 소비 패턴이 잡혔으니, 같은 lookup을 BattleScene 데미지 식에 적용. §1.3 (Hero3CatalogItemIndex) 는 패턴 3번째 — 병행 가능.
