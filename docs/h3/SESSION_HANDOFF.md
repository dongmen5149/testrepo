# Hero3 인수인계 노트 (Round 99 종료 시점, 2026-05-19 업데이트)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**분석 ~99.98% / Catalog ~99% / 실제 remake ~93%**. R99 분기 A. catalog `HP_DRAIN` 코드를 life steal 로 wiring. `ModifierKind` 9종 → 10종 (`HP_DRAIN` exact-match). `BattleScene.tryHpDrainFromSkill(actor, nameKo, dmgDealt)` 가 useSkill 공격 분기 끝에서 입힌 데미지 × drainPct% 만큼 actor HP 회복 (cap hpMax). 보라색 popup + "흡혈: +N HP" 로그. 117/117 tests (catalog 57→59 +2) + APK BUILD SUCCESSFUL. R100 권장: CURE_STATUS / TAUNT / HP_MAX·SP_MAX buff / recipe gold cost 분석 / enemy buff 시스템 — R100 milestone 회고 권장.

## 1. 다음 세션 즉시 시작 가이드 (R100 — 짧은 milestone 회고 + 다음 phase)

R73 시점에 분석/DES 는 끝났고, R74~R99 는 catalog 데이터를 Android 리메이크 안으로 끌어들이는 통합 라운드들. R97 ModifierKind 7종, R98 재생 2종, R99 HP_DRAIN. **R100 부터는 CURE_STATUS/TAUNT/HP_MAX 등 남은 catalog 코드 + 분석성 작업 + enemy buff 시스템** 이 메인 트랙. R100 milestone — 회고/scope 재정렬 권장.

### 1.0 R88-R92 결과 (참고)

- R88: `Hero3CatalogQuestIndex` 에 byFile/fileColors/colorOf 추가. Quests 탭 4 파일 색 구분. commit `9b1de921`.
- R89: `Hero3CatalogSkillIndex` 신설 (Quest 패턴 그대로) + Skills 탭 ~115 줄 per-skill drill-down + 7 weapon 색 구분 + lookupByName/lookupByWeapon/effectSummary. commit `92752a1f`.
- R90: `SkillScene` 에 catalog effectSummary 첫 소비 + `Quest.catalogKey: String? = null` 슬롯. commit `2a8b4f54`.
- R91: `Hero3CatalogSkillIndex.primaryModifier`/`primaryModifierForEngineName` (ATT*/HP_HEAL*) + `BattleScene.useSkill` 데미지/회복 보정 (±25 clamp). commit `1c310d47`.
- R92: `Hero3CatalogItemIndex` 신설 (패턴 3번째) + ITEMS 탭 ~547 줄 per-item drill-down + 10 슬롯 palette. commit `6f655854`.
- R93: `ModifierKind` 2종 → 7종 (DEFENSE/CRIT_RATE/CRIT_DEF/ACCURACY/DODGE 5 신규) + `BattleScene.damage(extraCritPercent)` 가 CRIT_RATE 실 가산. commit `04027ebe`.
- R94: engine `Status` enum (POISON) + `EnemyInstance.statuses` + `Hero3CatalogSkillIndex.debuffCountForEngineName` + `BattleScene` POISON 부여/tick/UI 인디케이터. commit `95c043b4`.
- R95: `Status` enum 1종 → 4종 (BURN/SLOW/STUN). BattleScene 이 nDebuffs count 만큼 take + dot tick + SLOW/STUN skip. commit `b18cb7f1`.
- R96: `Status` enum 4종 → 6종 (CRIT_DEF_BUFF/DEFENSE_BUFF, perTick = percent). BattleScene 에 partyStatuses 맵 + useSkill 자기 buff 등록 + doEnemyAttack 에서 합산 반영. commit `f14ecd5a`.
- R97: `Status` enum 6종 → 8종 (ACCURACY_BUFF/DODGE_BUFF) + rollHit + useSkill miss / doEnemyAttack dodge. catalog ModifierKind 7종 wiring 완성. commit `7a66113f`.
- R98: ModifierKind 7종 → 9종 (HP_REGEN/SP_REGEN exact-match). Status enum 8종 → 10종. tickPartyStatuses HP/SP 회복. commit `2f7a95f5`.
- R99: ModifierKind 9종 → 10종 (HP_DRAIN). BattleScene tryHpDrainFromSkill — 입힌 dmg × drainPct% 흡혈. 117/117 tests, +2 (R99).
- 열두 라운드 공통 패턴: catalog index → UI/데미지/crit/디버프/buff/miss-dodge/재생/흡혈 까지 점진 소비.

### 1.1 ✅ R90 완료 — SkillScene catalog effectSummary

(R90 종결, ghidra-round90 참조)

### 1.2 ✅ R91~R98 완료 — ModifierKind 9종 + nDebuffs 4종 + regen 2종 wiring

R91 OFFENSE+HEAL, R93 CRIT_RATE, R94 POISON, R95 BURN/SLOW/STUN, R96 CRIT_DEF+DEFENSE, R97 ACCURACY+DODGE, R98 HP_REGEN+SP_REGEN. catalog effect_v2 의 stat 카테고리가 시전 + 지속 (ongoing buff) 두 측면 모두 실 게임플레이에 도달.

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

## 2. 작업 순서 권장 (R100)

R100 = milestone. 짧은 회고 + 다음 phase 계획 권장. 후보:

```
A. CURE_STATUS — 시전 시 actor status 제거 skill.
B. TAUNT — 적의 target picker 가 TAUNT buff member 우선.
C. HP_MAX / SP_MAX — 일시적 max 증가 buff.
D. BUFF_REMOVE — 적 buff 제거 (enemy buff 시스템 선행).
E. recipe bytes[0..1] gold cost 분석.
F. enemy 측 buff/debuff 시스템.
```

목표 진행률 (R100 종료): **분석 ~99.98% 동일, 리메이크 ~93-94%**.

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
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (R99 최신)
- [Round 99](ghidra-round99-hp-drain-life-steal-2026-05-19.md) — HP_DRAIN (life steal) wiring (이번 라운드)
- [Round 98](ghidra-round98-hp-sp-regen-buff-2026-05-19.md) — HP_REGEN/SP_REGEN ongoing buff wiring
- [Round 97](ghidra-round97-accuracy-dodge-2026-05-19.md) — ACCURACY/DODGE 시스템 + catalog ModifierKind 7종 wiring 완성
- [Round 96](ghidra-round96-party-buffs-critdef-defense-2026-05-19.md) — Party buff status + CRIT_DEF / DEFENSE wiring
- [Round 95](ghidra-round95-status-burn-slow-stun-2026-05-19.md) — Status enum 확장 (BURN/SLOW/STUN) + BattleScene wiring
- [Round 94](ghidra-round94-debuff-status-poison-2026-05-19.md) — 디버프 enum + BattleScene poison apply/tick
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

# 2. R99 분기 A (HP_DRAIN) 완료. R100 후보:
#    A. CURE_STATUS — 시전 시 actor status 제거
#    B. TAUNT — 적 target picker 우선순위
#    C. HP_MAX / SP_MAX 일시 증가 buff
#    D. BUFF_REMOVE — 적 buff 제거 (enemy buff 선행)
#    E. recipe gold cost 분석
#    F. enemy 측 buff/debuff 시스템

# 3. 테스트 (R99 = 117 tests, R100 추가 시 119+ 기대)
./android/gradlew.bat -p android :app:testDebugUnitTest :engine-core:testDebugUnitTest :app:assembleDebug
```

JDK 경로: `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot` (현재 PC). 집 PC 는 `C:\Program Files\Eclipse Adoptium\jdk-21*` 일 수 있음 — 빌드 전 JAVA_HOME 확인 필요.

---

**다음 세션 시작 시 가장 먼저 할 일**: R100 milestone — 짧은 회고 (R74~R99 catalog 통합 트랙 26 라운드) + 다음 phase 계획. 후보 직진 시 CURE_STATUS (R99 패턴 동등) 또는 TAUNT (target picker) 가 깔끔.
