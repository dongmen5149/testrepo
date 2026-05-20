# Hero3 인수인계 노트 (Round 94 종료 시점, 2026-05-19 업데이트)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**분석 ~99.98% / Catalog ~99% / 실제 remake ~90%**. R94: engine-core 에 `Status` enum (POISON) + `StatusEffect` data class 신설 + `EnemyInstance.statuses` 필드. `Hero3CatalogSkillIndex.debuffCountForEngineName(nameKo)` 가 catalog `effectV2.nDebuffs` 노출. `BattleScene.useSkill` 가 nDebuffs > 0 skill 으로 적을 처치하지 않으면 POISON (3턴, perTick = max(2, dmg/5)) 부여, 매 턴 시작 시 tick → HP 감소 + popup + 로그. 적 HP 바 우측 `독(N)` 인디케이터. 105/105 tests (catalog 53→55 +2, engine 34→38 +4) + APK BUILD SUCCESSFUL. R95 권장: CRIT_DEF wiring (1.7 multiplier 감쇄) / Status enum 확장 (BURN/SLOW/STUN) / DEFENSE wiring.

## 1. 다음 세션 즉시 시작 가이드 (R95)

R73 시점에 분석/DES 는 끝났고, R74~R94 는 catalog 데이터를 Android 리메이크 안으로 끌어들이는 통합 라운드들. **R95 부터는 catalog ModifierKind 7종 중 wiring 미완료 4종 (DEFENSE/CRIT_DEF/ACCURACY/DODGE) + Status enum 확장 (BURN/SLOW/STUN) + 분석성 작업 (recipe gold cost 등)** 이 메인 트랙. 분석 진척은 거의 0.

### 1.0 R88-R92 결과 (참고)

- R88: `Hero3CatalogQuestIndex` 에 byFile/fileColors/colorOf 추가. Quests 탭 4 파일 색 구분. commit `9b1de921`.
- R89: `Hero3CatalogSkillIndex` 신설 (Quest 패턴 그대로) + Skills 탭 ~115 줄 per-skill drill-down + 7 weapon 색 구분 + lookupByName/lookupByWeapon/effectSummary. commit `92752a1f`.
- R90: `SkillScene` 에 catalog effectSummary 첫 소비 + `Quest.catalogKey: String? = null` 슬롯. commit `2a8b4f54`.
- R91: `Hero3CatalogSkillIndex.primaryModifier`/`primaryModifierForEngineName` (ATT*/HP_HEAL*) + `BattleScene.useSkill` 데미지/회복 보정 (±25 clamp). commit `1c310d47`.
- R92: `Hero3CatalogItemIndex` 신설 (패턴 3번째) + ITEMS 탭 ~547 줄 per-item drill-down + 10 슬롯 palette. commit `6f655854`.
- R93: `ModifierKind` 2종 → 7종 (DEFENSE/CRIT_RATE/CRIT_DEF/ACCURACY/DODGE 5 신규) + `BattleScene.damage(extraCritPercent)` 가 CRIT_RATE 실 가산. commit `04027ebe`.
- R94: engine `Status` enum (POISON) + `EnemyInstance.statuses` + `Hero3CatalogSkillIndex.debuffCountForEngineName` + `BattleScene` POISON 부여/tick/UI 인디케이터. 105/105 tests, +6 (R94).
- 일곱 라운드 공통 패턴: catalog index → UI/데미지 식/crit chance/디버프 까지 점진 소비 확대. R94 부터 = engine 측 시스템 (Status) 도 신설.

### 1.1 ✅ R90 완료 — SkillScene catalog effectSummary

(R90 종결, ghidra-round90 참조)

### 1.2 ✅ R91 + R93 + R94 완료 — ModifierKind 7종 / CRIT_RATE / 디버프 (POISON) wiring / 남은 4 wiring

R91 OFFENSE+HEAL, R93 CRIT_RATE, R94 디버프 (POISON 한 종 wiring). 미 wiring:

- **DEFENSE** (`P_DEF` / `M_DEF`) → 적 공격 받을 때 modifier. 적용 시점 정의 필요.
- **CRIT_DEF** (`CRI_DEF`) → 받는 crit 데미지 감쇄. 가장 쉬운 다음 wiring 후보.
- **ACCURACY** (`ACC`) → engine miss 시스템 신설 후.
- **DODGE** (`DOD`) → engine dodge 시스템 신설 후.
- Status enum 확장: BURN (POISON 와 동등 도트) / SLOW (행동 확률) / STUN (행동 봉인).

### 1.2-legacy ⭐⭐⭐⭐ R66 effect_v2 를 BattleScene 데미지 공식에 반영 (참고용)

**작업 위치**: `android/app/src/main/java/com/hero3/remake/scene/BattleScene.kt`

현재 데미지 = `effectiveAtk * powerMul + flatBonus` (engine Skill). R66 분석에서 발견한 effect_v2 살아있는 slot 의 `primarySigned / secondarySigned` 를 ATK/DEF/회복/디버프 modifier 로 적용.

- catalog 매칭이 없으면 현재 식 그대로.
- 매칭이 있고 slot1.codeName 이 `ATT1` / `DEF` / `HP_HEAL_INSTANT` 등 이면 해당 stat 에 가산/곱 적용.
- 디버프 nDebuffs > 0 일 때 target 에 상태이상 부여 (engine 측 상태 enum 신설 필요할 수 있음 — 미존재 시 로그만).

작업량 중급. SkillScene (1.1) 은 R90 에 완료 → R91 부터는 engine 측 stat code 매핑 정리 → BattleScene 적용.

### 1.3 ✅ R92 완료 — Hero3CatalogItemIndex (legacy 텍스트 보존)

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

## 2. 작업 순서 권장 (R95)

```
1. git status + git log --oneline -5   (R94 commit 확인)
2. CRIT_DEF wiring — `damage(extraCritDefPercent)` 추가, crit multiplier 1.7 - (defPct/100) 감쇄.
   또는 Status enum 확장 (BURN/SLOW/STUN) — R94 의 POISON tick 코드 재사용.
3. Hero3CatalogLoaderTest + StatusTest 갱신
4. assembleDebug + 105+/105+ tests
5. Round 95 doc + SESSION_HANDOFF/PROGRESS 갱신 + commit
```

목표 진행률 (R95 종료): **분석 ~99.98% 동일, 리메이크 ~90-91%**.

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
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (R94 최신)
- [Round 94](ghidra-round94-debuff-status-poison-2026-05-19.md) — 디버프 enum + BattleScene poison apply/tick (이번 라운드)
- [Round 93](ghidra-round93-modifier-kind-expansion-2026-05-19.md) — ModifierKind 7종 확장 + CRIT_RATE wiring
- [Round 92](ghidra-round92-catalog-item-index-2026-05-19.md) — Hero3CatalogItemIndex + ITEMS 탭 drill-down
- [Round 91](ghidra-round91-battle-effect-v2-modifier-2026-05-19.md) — BattleScene 데미지/회복에 catalog effect_v2 보정
- [Round 90](ghidra-round90-skill-bridge-quest-catalogkey-2026-05-19.md) — SkillScene catalog effectSummary bridge + Quest.catalogKey 슬롯
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

# 2. 이 문서 §1.2 의 미 wiring 4종 중 CRIT_DEF 부터 시작 (R95)
#    - 참고: Hero3CatalogSkillIndex.primaryModifier 의 CRIT_DEF 분기 (R93 도입, 데이터는 이미 노출)
#    - 변경: BattleScene.damage 에 extraCritDefPercent 추가 → crit multiplier 1.7 - (defPct/100) 클램프
#    - 또는 Status enum 확장 (BURN/SLOW/STUN) — R94 POISON tick 재사용

# 3. 테스트 (R94 = 105 tests, R95 추가 시 108+ 기대)
./android/gradlew.bat -p android :app:testDebugUnitTest :engine-core:testDebugUnitTest :app:assembleDebug
```

JDK 경로: `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot` (현재 PC). 집 PC 는 `C:\Program Files\Eclipse Adoptium\jdk-21*` 일 수 있음 — 빌드 전 JAVA_HOME 확인 필요.

---

**다음 세션 시작 시 가장 먼저 할 일**: 이 문서 §1.2 미 wiring 중 **CRIT_DEF** wiring (`damage()` crit multiplier 감쇄). 또는 **Status enum 확장** (BURN/SLOW/STUN) — R94 의 POISON tick 코드 그대로 재사용 가능.
