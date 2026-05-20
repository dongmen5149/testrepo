# Hero3 인수인계 노트 (Round 109 종료 시점, 2026-05-20 업데이트)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**분석 ~99.98% / Catalog ~99% / 실제 remake ~97-98% (엔지니어링 기준) / 베타 출시 fidelity ~44% (원작 동일 시각·음향 기준)**. R109 (MapWalkScene 타일 그래픽 wiring, byte[0]=theme 규칙 발견 + Android 통합) 완료. 다음 우선 = **R110a obj layer wiring** (3-5 dev day, 그래픽 ~90% → ~95%). 상세 [`round109-map-tile-wiring-phase1-3.md`](round109-map-tile-wiring-phase1-3.md).

## 0.1 베타 출시 진척도 평가 (2026-05-20 세션 추가)

`docs/h3/PROGRESS.md` 의 "리메이크 ~97-98%" 는 **catalog wiring + scene framework 엔지니어링** 기준. **사용자 정의 "베타 = 원작 게임과 시각·음향 동일 + 정상 플레이" 기준에서는 ~40-45%**. 영역별:

| 영역 | 진척도 | 가중치 | 핵심 사실 |
|---|---|---|---|
| A. 엔진 / scene 골격 | ~92% | 12% | 22 scene · GameView · GameState save · 22 status enum wiring · 133 unit test green |
| B. 전투 시스템 | ~85% | 12% | catalog stat 19/23 wiring (R107 HP/SP_MAX, R108 render). 미완: boss skill 매핑 (R74) / CD_REDUCE / *_BASE |
| C. 콘텐츠 매핑 | ~15% | 15% | engine bespoke quest 4/115 · enemy 14/322 · item 17/529 · skill 2/105. catalog 데이터는 적재 완료 |
| D. 그래픽 / 타일 | **~90%** | 10% | R109 byte[0]=theme 규칙 + MapWalkScene drawBitmap 통합 ✓. layer_1 obj sheet 통합만 남음 (R110a) |
| E. 오디오 | **0%** | 10% | SfxBus stub만. 33 SMAF 디크립트 완료지만 OGG 변환 정책 보류 (사용자 신뢰도) |
| F. 스토리 / 대사 | ~3% | 10% | 9,740 dialogue 미통합. 245 scn_v2 event trigger 미연결 |
| G. MapGraph 연결 | ~3% | 5% | 134 맵 중 4 edge placeholder. `_mp.extras_records` 의 exit 정보 미파싱 |
| H. NPC 배치 | ~5% | 5% | 19 NPC (시작 마을 + 던전 입구). 수백 NPC 미배치 |
| I. UI / UX | ~70% | 5% | i18n ko/en · 메뉴 풍부. 인벤토리 스킬 탭 미구현 등 |
| J. 저장 / GameState | ~80% | 5% | 3 슬롯 SharedPreferences · inventory/quest/party 영구 |
| K. 출시 패키징 | ~10% | 5% | ic_launcher 부재 · release keystore 부재 · Manifest 최소 · Play Store metadata 0 |
| L. 테스트 / QA | ~50% | 6% | unit 133/133 ✓. instrumented test 0. 디바이스 QA 기록 없음 |

가중 평균 **~44%** (R109 후, +2%p). 범위 **42~52%**.

### 베타까지의 critical-path (남은 큰 트랙, 비-catalog)

1. ⭐⭐⭐⭐⭐ ~~R109: MapWalkScene 타일 wiring~~ (10~16 dev day) — **2026-05-20 완료**. 그래픽 70% → 90%.
1a. ⭐⭐⭐⭐⭐ **R110a: obj layer wiring** (3~5 dev day) — `obj_<byte[0]>_bm` multi-frame sprite 통합. 그래픽 90% → 95%.
2. ⭐⭐⭐⭐⭐ **사운드 트랙 재개** (10~15 dev day) — SMAF→OGG 33곡 + MediaPlayer 통합. 사용자 신뢰도 정책 재결정 필요.
3. ⭐⭐⭐⭐ **MapGraph 자동화** (10~15 dev day) — `_mp.extras_records` 의 exit 정보 추출로 134 맵 연결.
4. ⭐⭐⭐⭐ **NPC 자동 배치** (20~30 dev day) — `_mp.extras_records` NPC marker 통합.
5. ⭐⭐⭐⭐ **Dialogue 통합 + 번역** (10~30 dev day) — 9,740 라인 ↔ scn_v2 event trigger + LLM 한↔영 ($4.09).
6. ⭐⭐⭐ **콘텐츠 매핑 확장** (30~50 dev day) — engine bespoke ↔ catalog 322 enemy / 115 quest / 529 item / 105 skill.
7. ⭐⭐⭐ **출시 패키징** (3~5 dev day) — ic_launcher · keystore · ProGuard · store metadata.

총 잔여 100~160 dev day. 다른 모델의 "92% / 8% 남음" 평가는 catalog wiring 잔여분만 본 것으로, 위 7개 트랙을 critical-path 에 포함하지 않은 가정. 사용자 정의 (원작 fidelity) 에서는 위 트랙 모두가 필수.

## 1. 다음 세션 즉시 시작 가이드 (R110a)

**R110a 최우선 권고: obj layer wiring** — R109 (`byte[0]=theme`) 패턴을 layer_1 에 확장. `obj_<byte[0]>_bm/frame_NN_*.png` 의 multi-frame sprite 를 `layer_1[i]` 의 (frame_idx, x/y offset) 값과 매핑.

먼저 layer_1 raw 값과 obj sheet frame 의 정확한 매핑 식을 발견해야 함 (R109 Phase 2 와 동일 패턴):
1. `python tools/recon/find_map_to_sheet_mapping_v2.py` 의 obj 적합도 결과 (`shift=6` 이 120/134 map 에서 fit) 분석 재시작.
2. anchor map 4개로 `tools/qa/render_layer1_candidates.py` 신규 작성, 시각 비교.
3. `MapWalkScene.kt` 의 layer_1 색상 loop 도 R109 와 동일한 lookup-or-fallback 패턴으로 교체.

[`round109-map-tile-wiring-phase1-3.md`](round109-map-tile-wiring-phase1-3.md) §6 도 참고.

R73 시점에 분석/DES 는 끝났고, R74~R108 는 catalog 데이터를 Android 리메이크 안으로 끌어들이는 통합 라운드들 — **35 라운드**. catalog stat enum 23종 중 **19종 wiring** + UI 색상 컨벤션 통일 완료. R109 후보 중 catalog wiring 잔여 (boss skill / *_BASE / CD_REDUCE) 는 베타 fidelity 임팩트 작음. **타일 wiring → 사운드 → MapGraph → 콘텐츠** 순서가 베타 출시 정공법.

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
- R99: ModifierKind 9종 → 10종 (HP_DRAIN). BattleScene tryHpDrainFromSkill — 흡혈. commit `e55e4696`.
- R100: ModifierKind 10종 → 11종 (TAUNT). Status enum → 11종 (TAUNT_BUFF). target picker 변경. commit `cf3f45c0`. **catalog 통합 27 라운드 milestone.**
- R101: ModifierKind 11종 → 13종 (REVIVE/BLOCK). Status enum 11종 → 12종 (BLOCK_BUFF). REVIVE single-shot 부활 / BLOCK 확률 무효. commit `85d2c05e`.
- R102: ModifierKind 13종 → 15종 (SP_COST_REDUCE/SHIELD_PIERCE). Status enum 12종 → 13종. SP 비용 buff / 공격 방어 관통. commit `f8adf992`.
- R103: enemy.statuses 컨테이너를 buff 도 담는 일반화 — boss DEFENSE_BUFF 25% 자동 부여. commit `675a5595`.
- R104: 3 메인 boss 별 차별화 buff 조합 + 4 enemy buff 전체 wiring. doActorAttack 에도 hit-roll + block 추가. commit `be9a860f`.
- R105: ModifierKind 15종 → 16종 (BUFF_REMOVE). useSkill 가 enemy buff N (1..3) 제거 + render 의 turnsLeft > 9 → "∞". commit `d6bf54cc`.
- R106: ModifierKind 16종 → 17종 (CURE_STATUS). party debuff 시스템 + STUN/SLOW skip + CURE_STATUS 자기 debuff 제거. 130/130 tests, +1 (R106).
- R107: ModifierKind 17종 → 19종 (HP_MAX/SP_MAX). Status enum 13종 → 15종 (HP_MAX_BUFF/SP_MAX_BUFF). BattleScene effectiveHpMax/effectiveSpMax 헬퍼 + 모든 사용처 wiring + HUD bar effective max. 132/132 tests, +2 (R107).
- R108: party debuff render UI + enemy 색상 컨벤션 일관화. renderPartyPanel 인디케이터 buff/debuff 분리 (debuff light-red 좌측 / buff light-blue 우측). enemy HP 바도 동일 컨벤션. `turnsLeft > 9 → "∞"` party 측에도 적용. partyBuffLabel alias 삭제. StatusTest 의 r108 partition test +1. 133/133 tests.
- R109: MapWalkScene 타일 그래픽 wiring (Phase 1~3). `meta_header_hex[0]` = theme sheet ID 규칙 발견 (4 anchor + 134 map universal 시각 검증). `MapData{themeId, themeShift}` + `themeTileCache` + `loadThemeTiles()` + drawBitmap 통합. 색상 fallback 유지. 그래픽 70% → 90%. 베타 fidelity 42% → 44%. 자세한 내용은 [`round109-map-tile-wiring-phase1-3.md`](round109-map-tile-wiring-phase1-3.md).
- 스물두 라운드 — 전투 양방향 대칭성 + 일시 max 증가 buff + render 색상 컨벤션 통일 + 타일 그래픽 실 sprite 통합까지 완성.

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

## 2. 작업 순서 권장 (R109)

R108 (party debuff render UI + enemy 색상 컨벤션 일관화) 완료. R109 후보 (베타 출시 fidelity 임팩트 순):

```
★★★★★ A. MapWalkScene 타일 그래픽 wiring (r109-plan-map-tile-wiring.md)
         — 10~16 dev day, 베타 fidelity 가장 큰 단일 임팩트 (그래픽 70% → ~90%).
         — 직전 stale 평가 ("타일 BM 0x0c 미해독, 30~50 dev day") 정정 결과
            진짜 작업은 _mp.meta_header_hex ↔ tile sheet 매핑식 발견 + BitmapFactory
            wiring 의 통합 작업.

★★★ B. boss skill 매핑 (R74) — boss 가 catalog skill 사용 (catalog wiring).
★★ C. *_BASE 영구 stat (서적) — i18 영구 stat 부여, 저장 동기화 필요.
★★ D. CD_REDUCE — cooldown 시스템 선행 필요.
★★ E. recipe bytes[0..1] gold cost 분석.
★★ F. damage popup 색상 컨벤션 통일 — heal/drain/dot 별 색 정리.
```

목표 진행률 (R109 = A 완료 시): **분석 ~99.98% 동일, catalog wiring 99% 동일, 베타 fidelity ~42% → ~48%**.

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
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록 (R106 최신)
- ★ [R109 plan: MapWalkScene 타일 wiring](r109-plan-map-tile-wiring.md) — 다음 세션 시작 가이드 (Phase 1~4)
- [Round 108](ghidra-round108-party-debuff-render-2026-05-20.md) — Party debuff render UI + enemy 색상 컨벤션 일관화
- [Round 107](ghidra-round107-hp-sp-max-buff-2026-05-20.md) — HP_MAX / SP_MAX 일시 buff wiring
- [Round 106](ghidra-round106-party-debuff-cure-status-2026-05-19.md) — Party debuff 시스템 + CURE_STATUS wiring
- [Round 105](ghidra-round105-buff-remove-render-2026-05-19.md) — BUFF_REMOVE wiring + enemy buff render 개선
- [Round 104](ghidra-round104-boss-buff-differentiation-2026-05-19.md) — Boss 별 차별화 buff 조합 + 4 enemy buff 전체 wiring
- [Round 103](ghidra-round103-enemy-defense-buff-2026-05-19.md) — Enemy buff 시스템 (boss DEFENSE_BUFF)
- [Round 102](ghidra-round102-sp-cost-shield-pierce-2026-05-19.md) — SP_COST_REDUCE + SHIELD_PIERCE wiring
- [Round 101](ghidra-round101-revive-block-2026-05-19.md) — REVIVE + BLOCK wiring
- [Round 100](ghidra-round100-milestone-taunt-2026-05-19.md) — Milestone: TAUNT wiring + catalog 통합 27 라운드 회고
- [Round 99](ghidra-round99-hp-drain-life-steal-2026-05-19.md) — HP_DRAIN (life steal) wiring
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
# 마지막 commit 기대값: R108 — Party debuff render UI + enemy 색상 컨벤션 일관화

# 2. R108 (party debuff render UI) 완료. R109 최우선 = MapWalkScene 타일 wiring.
#    상세: docs/h3/r109-plan-map-tile-wiring.md (Phase 1~4, 10~16 dev day)
#    Phase 1 첫 스크립트: tools/recon/dump_tile_sheets.py + dump_map_meta_xref.py

# 3. 테스트 (R108 = 133 tests, R109 추가 시 134+ 기대)
./android/gradlew.bat -p android :app:testDebugUnitTest :engine-core:testDebugUnitTest :app:assembleDebug
```

JDK 경로: `C:\Program Files\Microsoft\jdk-21.0.11.10-hotspot` (현재 PC). 집 PC 는 `C:\Program Files\Eclipse Adoptium\jdk-21*` 일 수 있음 — 빌드 전 JAVA_HOME 확인 필요.

---

**다음 세션 시작 시 가장 먼저 할 일**: `docs/h3/r109-plan-map-tile-wiring.md` 를 열고 Phase 1 부터 시작. catalog wiring 라운드 (boss skill 등) 는 베타 fidelity 임팩트가 작으므로 R110 이후로 미룸. 베타 출시 진척도 평가 + critical-path 는 본 문서 §0.1 참고.
