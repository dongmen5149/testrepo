# Hero3 인수인계 노트 (Round 84 종료 시점, 2026-05-19 업데이트)

> **다음 세션 시작 명령**: 사용자가 `"영웅서기3 다음 내용 진행해줘"` 또는 `"Hero3 이어서"` 라고 하면 이 문서를 본다.

## 0. 현재 상태 한 줄

**분석 ~99.998% / Catalog ~98% / 실제 remake ~85-87%**. R84: **catalog 115 quests** (R58/R62 의 quest_00/01/10/11_dat × 37/7/38/33 entries) 가 Hero3Catalog.questFiles 에 정식 로딩 + CatalogViewer **Quests tab 신규** + overview 카운트. **71/71 tests** + APK BUILD SUCCESSFUL. R85 권장: QuestRegistry catalog-fed (한국어 이름 매칭) / R66 skill effect_v2 BattleScene 통합 / CatalogViewer Skills detail panel / R62 item_xref 21 매핑 / ForgeScene gold cost.

## 1. 다음 세션 즉시 시작 가이드 (R75)

### 1.0 R74 결과 (참고)

- `tools/recon/parse_h3_des_plain.py` 실행 시 8 파일 모두 JSON 출력
- 핵심 카운트: i15=38, drop=161, droph=161, smith=80, smithh=80, shop=5, shoph=5, getitem=96
- drop_dat 161 = R56 enemy_dat 161 1:1 확정
- BSKILL set hit: 98/161 records (H4 confirmed)
- 자세히: [ghidra-round74-des-plain-parsers-2026-05-19.md](ghidra-round74-des-plain-parsers-2026-05-19.md)

### 1.1 ⭐⭐⭐⭐⭐ Phase A2: 17B drop record / i15 6B trailer 정밀 (R75 권장 우선)

1. **drop_dat 17B field map**:
   - byte 0-1: low-frequency = enemy_id? (0..160) 또는 drop count
   - byte 5/9/13 = boss skill ID 위치 후보 (98/161 ≥3 hits)
   - byte N (gold?) 변동 폭 정밀 측정
   - droph_dat 대비 normal: scaling factor 추출

2. **i15 6B trailer**:
   - 38 entries 의 마지막 6B (예: `00 00 00 0f ff 00`, `04 02 02 0f ff 00`, ...)
   - 5번째 byte `0f` 고정, 다른 byte 들이 stat (ATK/DEF/MP?)
   - i0~i12 catalog 의 stat block 과 cross-check

3. **smith → Hero3Recipe data class**: Hero3Catalog.kt 확장 + Loader + 12 unit tests 갱신

4. **shop → Hero3RegionShop data class**: 5 regions × level tier + item slot

5. **export_game_balance.py** → game_balance.json v1.2 (예상 ~700KB)

### 1.x (구) Phase A: DES 평문 정밀 파서 (자동, 권장 우선)

R73 의 8 plain 파일 (`work/h3/decrypted/*.plain`) 을 typed Kotlin object 로 디코드.
**도구 설치 불필요, 즉시 진행 가능.**

#### A-1. i15_dat parser (master shop catalog)
- 평문 7,400B, 한글 description 직접 포함
- entry 구조: `[size:1B][reserved:1B][name_len:1B][name:EUC-KR][body:desc text]`
- body 예: `"레벨 10 투구; 머리띠; 보스용도 15년; "`
- 신규: `tools/recon/parse_h3_i15_dat.py`
- 결과: `work/h3/recon/i15_shop_catalog.json` (shop entry list)

#### A-2. drop_dat / droph_dat parser (enemy 별 drop table)
- 평문 3,080B, 18-byte stride entry + `11 00` separator
- 가설: enemy_id (1B?) + drop items[N] × (item_id + drop_rate%)
- normal vs hard 비교로 enemy_id ↔ R56 의 161 enemies 매칭 가능
- 신규: `tools/recon/parse_h3_drop_dat.py`
- 결과: `work/h3/recon/drop_table.json`

#### A-3. smith_dat / smithh_dat parser (조합 레시피)
- 평문 896B, entropy 3.84 (매우 낮음)
- 가설: input items (i14 조합재료) + output item (i0~i12 결과물) + cost(gold)
- R69 의 i14 7 카테고리와 매칭
- 신규: `tools/recon/parse_h3_smith_dat.py`

#### A-4. shop_dat / shoph_dat parser (상점 NPC 별 판매 목록)
- 평문 1,008B
- 가설: NPC_id + items[] × (item_id + price modifier)
- R57 의 8 main regions 와 매칭 (네오솔티아 / 토레즈 / 엔자크 등)
- 신규: `tools/recon/parse_h3_shop_dat.py`

#### A-5. getitem_dat parser (fixed drops)
- 평문 400B (작음, 50 entries × 8B)
- 가설: quest 보상 / scripted drop 의 fixed item table

#### A-6. boss skill ID H4 가설 최종 검증 (R67/R68 후속)
- R67 H4 (별도 boss skill table) 가설.
- DES 평문 데이터에서 boss skill ID (1..20 range) 검색
- distinct IDs: {1, 2, 3, 5, 7, 8, 9, 10, 13, 14, 19, 20}
- 패턴 (3,2,1,2), (19,13,9,9) 등을 drop_dat / smith_dat / shop_dat 안에서 검색
- 가능성: drop_dat 의 18-byte stride entry 가 사실 boss skill encounter table

#### A-7. Hero3Catalog 확장
- R71 의 Hero3Catalog 에 다음 data class 추가:
  - `Hero3ShopEntry(name, level, category, description, classRestriction, ...)`
  - `Hero3DropEntry(enemyId, drops: List<Hero3DropItem>)`
  - `Hero3DropItem(itemId, ratePercent)`
  - `Hero3Recipe(inputs: List<ItemRef>, output: ItemRef, goldCost)`
  - `Hero3ShopCatalog(npcId, region, sellsItems: List<ShopItemRef>)`

#### A-8. game_balance.json v1.2 출력
- export_game_balance.py 수정 → DES 평문 데이터 통합
- 예상 크기: 582KB → ~700KB

### 1.2 ⭐⭐⭐ Phase B: SMAF→OGG 변환 (사용자 신뢰도 정책 대기)

**상태**: R73 에서 pipeline 스크립트 + 설치 가이드 작성 완료. 외부 도구 부재로 변환 미실행.

**사용자 정책**: "신뢰도 높은 것만 다운로드" → smaf-converter.jar (개인 GitHub) 와 FluidR3_GM.sf2 (비공식 미러) 보류.

**신뢰도 높은 도구만 진행 가능한 경로**:

| 도구 | 신뢰도 | 출처 | 설치 명령 |
|---|---|---|---|
| FFmpeg | 🟢 매우 높음 | winget 공식 | `winget install Gyan.FFmpeg` |
| FluidSynth | 🟢 매우 높음 | winget 공식 | `winget install FluidSynth.FluidSynth` |
| `mido` | 🟢 높음 | PyPI 공식 | `pip install mido` |
| `pyFluidSynth` | 🟢 높음 | PyPI 공식 | `pip install pyFluidSynth` |
| `pydub` | 🟢 높음 | PyPI 공식 | `pip install pydub` |
| Windows `gm.dls` | 🟢 매우 높음 | OS 동봉 (`C:\Windows\System32\drivers\gm.dls`) | (이미 있음) |
| smaf-converter.jar | 🔴 낮음 | 개인 GitHub repo | (보류) |
| FluidR3_GM.sf2 | 🟡 보통 | 비공식 미러 | (보류) |

**대안 전략 (R74 Phase B)**:
1. winget + PyPI 만 사용해서 도구 설치
2. **SMAF→MIDI 변환을 Pure Python 자체 구현** (third-party JAR 회피)
   - SMAF format spec 기반 직접 작성
   - score chunk → MIDI events 변환
   - 음색 정확도 낮음 but 멜로디/리듬 100% 보존
   - 코드 review 가능 (repo 안)
3. MIDI+gm.dls → WAV (FluidSynth 또는 pyFluidSynth)
4. WAV → OGG (FFmpeg)

**다음 세션에서 결정 필요**:
- 사용자가 winget + pip 설치 승인하면 → R74 Phase B 진행
- 보류하면 → R74 Phase A (DES 평문 파서) 만 진행 후 R75 이후에 Phase B

### 1.3 ⭐⭐ Phase C: Dialogue LLM 번역

- 9,740 entries, $4.09 추정 (Claude Sonnet 4.6)
- R69 의 `work/h3/translation_queue.json` 사용
- 사용자가 LLM API key 또는 Claude API 직접 호출 가능 시 자동 진행

## 2. 작업 순서 권장 (다음 세션)

```
1. git status + git log --oneline -5   (현재 상태 확인)
2. 이 문서 + MASTER_SPEC.md 확인
3. Phase A 의 8 parser 작업 시작 (즉시):
   - A-1 i15_dat parser
   - A-2 drop_dat parser
   - A-3 smith_dat parser
   - A-4 shop_dat parser
   - A-5 getitem_dat parser
4. A-6 boss skill ID H4 가설 검증
5. A-7 Hero3Catalog 확장 + 12 unit tests 갱신
6. A-8 game_balance.json v1.2
7. (사용자 승인 시) Phase B SMAF
8. Round 74 doc + commit
```

목표 진행률 (R74 종료): **~99.98%**.

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
- [PROGRESS.md](PROGRESS.md) — 전체 진행 기록
- [Round 73](ghidra-round73-des-success-smaf-pipeline-2026-05-19.md) — DES 8/8 + SMAF
- [smaf_conversion_guide.md](smaf_conversion_guide.md) — SMAF 외부 도구 가이드
- [Round 72](ghidra-round72-scene-integration-2026-05-19.md) — Android scene 통합
- [Round 71](ghidra-round71-catalog-loader-2026-05-19.md) — Catalog data layer
- [Round 70](ghidra-round70-master-spec-exp-groups-2026-05-19.md) — Master Spec
- (R56-R69) — see MASTER_SPEC §14
- `tools/h5_des.py` — Hero5 mx_des_decrypt Python 포팅 (R68 산출, R73 적용)
- 모든 round docs: `docs/h3/ghidra-*-2026-05-1[0-9].md`
- 모든 recon scripts: `tools/recon/`
- 모든 converter scripts: `tools/converter/`

## 7. 빠른 시작 (다음 세션 첫 5 분)

```bash
# 1. 현재 git 상태 확인
git status
git log --oneline -3

# 2. DES 평문 파일 확인 (R73 산출)
ls work/h3/decrypted/

# 3. Phase A 시작 — i15_dat parser 작성
# 새 파일: tools/recon/parse_h3_i15_dat.py
# 입력: work/h3/decrypted/i15_dat.0EP@KO91.plain
# 출력: work/h3/recon/i15_shop_catalog.json
```

또는 사용자가 SMAF 진행 의사가 있으면 Phase B 도구 설치부터 시작.

---

**다음 세션 시작 시 가장 먼저 할 일**: 이 문서 §1 의 Phase A 또는 Phase B 중 선택. **기본 권장 = Phase A** (도구 설치 불필요, 즉시 진행).
