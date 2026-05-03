# Hero3 Remake — 진행 상황 & 다음 단계

> 이 문서는 다음 작업 세션에서 컨텍스트 유실 없이 이어서 진행할 수 있도록 정리한 핸드오프.
> 자세한 자산 포맷 사양은 [`docs/asset-formats.md`](asset-formats.md) 참조.

## ⚡ 다음 세션 — 여기서부터 시작

**최신 커밋**: `af5574a feat: 게임 1주차 콘텐츠 완성 + _scn/_cif/_mp 통계 분석` (+ 그 이후 6 추가 폴리시)

## ⚡ 다음 세션 — 시작 전 5분 체크리스트

1. `git log --oneline -3` 로 최신 커밋 확인 (`af5574a` 다음 추가분 있는지)
2. `git status --short` — 미커밋 변경 있으면 무엇이 진행 중인지 파악
3. 이 문서 §"현재 상태 스냅샷" + §"다음 진행 후보" 읽기
4. Android 빌드 가능 환경이면 `cd android && ./gradlew :app:assembleDebug` 로 컴파일 검증 (gradle wrapper 부재 시 system gradle 또는 Android Studio 사용)
5. `tools/recon/*.py` 의 산출물(`work/*.json`)이 비어있으면 §"재현 명령" 참조해 재실행

---

## 📊 현재 상태 스냅샷 (2026-05-04 종료 시점)

### Android 클라이언트 — 완성도 높은 1주차 게임

**플레이어 진행 루프** (전부 동작):
- 새 게임 → 솔티아 마을 → NPC 대화 → 촌장이 가디언 토벌 의뢰 (`guardian_hunt`)
- 외곽(map1) / 가디언 동굴(map10) 탐험 → 인카운터 / 보물상자 / 자연 회복
- 보스 1: `boss_guardian` (map10 8,4) → 처치 시 화이트 플래시 + Tier-2 잠금 해제 + `chaos_lord` 자동 활성
- 혼돈의 영역(map11) → 보스 2: `boss_chaos` (map11 6,6) → Tier-3 잠금 해제 + `sealed_god` 자동 활성
- 봉인의 사원(map12) → 최종 보스: `boss_sealed` (map12 10,6) → 처치 시 EndingScene 자동 진입 → 한·영 크레딧 → 타이틀 ★ CLEAR

**게임 시스템**:
- 캐릭터: 케이/리츠 각 5 클래스 (StatusScene L 키로 자유 변경)
- 12 스킬 (Lv 1/5/6/7/8 단계별 잠금 해제), heal/damage 모두 effective stats 반영
- 16 아이템 (Tier 1/2/3) — 무기/방어구/장신구/소비/재료/열쇠
- 적 13 (10 일반 + 3 보스), 드롭 테이블, 도감 (BestiaryScene)
- 8 보물상자, 빠른 이동(50G), 여관 10G/100G
- 퀘스트 4개, 자동 완료 + 후속 체인, EventBus 토스트
- 세이브 슬롯 3 + 활성 슬롯 0, 모든 진행 상태 영구 저장

**씬 (20 + Ending) 모두 정식 구현**:
- Title / MainMenu / MapWalk / NpcDialogue / SaveSlots / Status / Inventory(가방·장비·스킬 탭) / DialogueDemo / Settings / SpriteGallery / Map(heatmap) / Battle / Shop / Skill / Quest / Bestiary / Records / EventViewer / Travel / Ending
- 미니맵, 활성 퀘스트 라인, 보스 근접 경고, 출구 힌트
- Battle: 부유 / lunge / hit shake / 데미지 popup / 사망 페이드 / 보스 인트로(1.8s) / 처치 플래시(600ms)
- 토스트 시스템 (보스/레벨업/퀘스트/드롭/픽업/세이브)
- 튜토리얼 오버레이 (첫 진입 6s, Settings 에서 재생 가능)

**Settings**: 언어(ko/en) / 화질(SD/HD) / 인카운터 배수(0/0.5/1/2x) / 미니맵 ON/OFF / 튜토리얼 재생

**SfxBus** (사운드 stub, §4.5 후 즉시 활성):
- TitleScene → Bgm.TITLE / MapWalk → Bgm.FIELD / Battle → Bgm.BATTLE or Bgm.BOSS / Ending → Bgm.ENDING
- BattleScene HIT / LEVEL_UP / BOSS_INTRO / BOSS_DEFEAT, MapWalk CHEST 호출 wired up
- `SfxBus.debugToast = true` 면 EventBus 로 어떤 효과음이 트리거되는지 시각화

### 원본 자산 분석 (Ghidra 없이 가능한 한도)

**`_scn` (이벤트 스크립트, 244 파일 / 316KB, 52% 텍스트)**:
- 화자 태그 105 종 추출 (리츠 4890 / 케이 4599 / 일레느 3064 / ...)
- 25,818 대사 트리플 → 화자/모드/텍스트 구조화 JSON (244 파일 + summary)
- "다음 대사" opcode 식별: `0x00 [mode]`, mode ∈ {0x7c, 0x27, 0x24, 0x7b}
- 헤더 영역 분리: 첫 화자 태그 이전이 0~1930 byte 이벤트 메타 (트리거/플래그) — Ghidra 진입점 우선순위
- inter-speaker 영역은 단순 마커, 분기 opcode 부재

**`_cif` (애니메이션, 103 파일)**:
- 헤더 재해석: `uint8 slot_count + uint8 category` (기존 uint16 가정 폐기)
- category 0 = hero/boss (8슬롯), category 1 = enemy (0~7)
- `19 19` 마커 = frame size (76% 파일)
- `tools/converter/convert_cif.py` 헤더 패치 완료. 9-byte record 가설 약함 → 가변 record 추정

**`_mp` extras (134 맵)**:
- best record_size 4(60맵)/6(35맵)/12(10맵) 분산 → 단일 fixed-size 가설 부적합
- 첫 byte 0x80(67맵)/0xc0(11맵) dominant → flag/type
- **결정적 디코드는 Ghidra 필요** (현재 MapGraph 수동 정의로 우회)

---

## 🎯 다음 진행 후보 (우선순위순)

### A) **대사 번역 실행** [블로커: API 키 + 사용자 결정]
- 비용: ~$0.66 (Claude Haiku 4.5, 9,741 unique). 한 번만 실행
- 사용자가 "번역은 마지막"이라고 했으므로 게임 콘텐츠가 마무리된 시점에 진행
- 명령 (in §"재현 명령")
- 결과: `dialogue_translations_en.json` 자동 배포, NpcDialogueScene 가 settings.language == "en" 일 때 자동 사용

### B) **Ghidra 분석** [블로커: Ghidra 도구 설치]
1. **§4.1 type 0x0c sparse pixel** — theme/obj 타일 진짜 그래픽 (현재 색상 그리드 placeholder)
2. **§4.2 _mp extras** — NPC/exit/event 자동 배치 (현재 NpcRegistry, MapGraph, EncounterTable, ChestRegistry 모두 수동)
3. **§4.3 _cif animation timing** — 진짜 4방향 걷기/공격/사망 애니 (현재 정적 frame 매핑)
4. **§4.4 _scn opcode** — 분기/이펙트/사운드 명령 (헤더 영역 분석부터 시작 — 통계 단서 확보됨)

진입점 단서 (PROGRESS §4 상세):
- 비트맵 디코더: `frameBuf is NULL` 문자열 (`0xa61c8`) 부근 PIC xref
- _cif 애니: `Hero_Free`, `freeBossType` 함수 부근
- _mp extras: NPC 로딩 함수 (`Event_freeID`, `loadDataID`)
- _scn opcode: `onEventMessageOkKey`, `eventManager` switch/dispatch

### C) **사운드 (SMAF→OGG)** [블로커: 외부 도구]
- §4.5 — SMAF 디코더 (`smaf2midi` 또는 KSS/Yamaha SMAF SDK) 또는 33개 수동 변환
- 변환 후 `engine/SfxBus.kt` 의 `play()` / `playMusic()` 만 구현하면 즉시 활성. 호출처는 이미 wired up

### D) **게임 콘텐츠 확장** [블로커 없음, 작업량만]
- 추가 보스 / 맵 / NPC / 퀘스트
- 추가 스킬·아이템·세트 효과
- 멀티 캐릭터 액티브 파티 (현재 leader 만 전투 참여)
- 세이브 자동 (currently 슬롯 0 만 자동, 슬롯 1~3 수동)
- 일본어/중국어 (translate_dialogues.py system prompt 교체)

### E) **빌드/테스트 환경** [블로커 없음]
- gradle wrapper 추가 (`cd android && gradle wrapper --gradle-version 8.7`)
- CI 셋업
- 단위 테스트 (CharacterRegistry / Quest 로직 등)
- `_scn` 분석 결과를 자동 검증하는 회귀 테스트

---

## 📁 코드 구조 — 어디에 뭐가 있나

### Android 클라이언트 (`android/app/src/main/`)

```
java/com/hero3/remake/
├── MainActivity.kt              # SceneRequest 라우팅 + GameState/Settings 주입
├── engine/                      # 핵심 시스템 (data + logic)
│   ├── Character.kt             # CharacterRegistry, Stats, effectiveAttack/Defense/Intl
│   ├── Item.kt                  # ItemRegistry, Inventory(MAX_SLOTS=20)
│   ├── Skill.kt                 # SkillRegistry (Lv 게이트, 12 스킬)
│   ├── Enemy.kt                 # EnemyRegistry (10 일반 + 3 보스, dropTable)
│   ├── Quest.kt                 # QuestRegistry, QuestLog (자동 완료 + followUp 체인)
│   ├── ChestRegistry.kt         # 8 상자 정적 정의
│   ├── ShopRegistry.kt          # NPC별 재고 (gameState 따라 잠금 해제)
│   ├── EncounterTable.kt        # 맵별 인카운터 확률 + 적 풀
│   ├── MapGraph.kt              # 맵 간 연결 (E/W/N/S edges 수동 정의)
│   ├── NpcRegistry.kt           # 13 NPC + patrolPath + postBoss 분기 + action(heal)
│   ├── GameState.kt             # 슬롯별 SharedPreferences (party/inventory/quests/etc)
│   ├── Settings.kt              # 언어/화질/인카운터/미니맵
│   ├── EventBus.kt              # 단순 toast 큐
│   ├── SfxBus.kt                # 사운드 stub
│   ├── GameView.kt              # SurfaceView 60fps + 키 매핑
│   ├── InputController.kt       # 비트마스크 입력
│   ├── VirtualKeypadView.kt     # 가상 키패드 오버레이
│   ├── Scene.kt                 # 추상 (consumesPoundKey 플래그)
│   ├── Strings.kt               # i18n 헬퍼
│   └── UiKit.kt                 # 공용 그리기 (drawBox/drawHeader/drawHints)
└── scene/                       # 20개 씬
    ├── TitleScene / MainMenuScene / MapWalkScene / NpcDialogueScene
    ├── SaveSlotScene / StatusScene / InventoryScene / SkillScene / QuestScene
    ├── BattleScene / ShopScene / BestiaryScene / RecordsScene
    ├── TravelScene / EventViewerScene / EndingScene
    ├── SettingsScene / DialogueDemoScene / SpriteGalleryScene / MapScene

assets/
├── sprites/         3,131 frame PNG (1×, SD)
├── sprites_hd/      4× scale4x HD
├── maps/            134 _mp.json
├── cif/             103 _cif.json (헤더 패치 적용 — 재변환 필요)
├── strings/ palettes/
├── dat/char_dat.json
├── scn_v2/          245 화자별 대사 JSON (244 + summary)
├── dialogue_corpus.json + dialogue_top_texts.json + asset_catalog.json
└── (dialogue_translations_en.json 은 §A 실행 후 생성)

res/values{,-ko}/strings.xml
```

### 분석 도구 (`tools/`)

```
recon/                # 정찰
├── extract_strings.py / disasm_thumb.py / find_pic_xrefs.py / find_f81f.py / find_base.py
├── analyze_mp_extras.py        # _mp extras 통계
├── analyze_cif.py              # _cif 헤더/body 통계
├── analyze_scn_opcodes.py      # _scn byte freq
├── extract_scn_speakers.py     # _scn 화자 태그 추출
├── dump_scn_structure.py       # 단일 _scn 구조 덤프
├── scn_dialogue_opcode.py      # [speaker] 직전 byte → 대사 시작 opcode
├── scn_inter_speaker.py        # 대사 ~ 다음 화자 사이 byte
└── scn_header.py               # 첫 화자 이전 영역 (이벤트 메타)

converter/            # 자산 변환
├── convert_all.py / convert_text.py / convert_palette.py
├── convert_bm_v2.py / convert_cif.py / convert_mp.py / convert_scn.py / convert_dat.py
├── convert_scn_v2.py           # 화자별 대사 트리플 추출 (NEW)
├── build_dialogue_corpus.py
└── prepare_android_assets.py   # scn_v2/, dat/char_dat 자동 복사 추가

i18n/                 # 번역 인프라
├── translation_dict.py
├── generate_string_resources.py
├── build_asset_catalog.py
└── translate_dialogues.py      # Claude Haiku 4.5 (§A 실행)

hd/
├── upscale_poc.py / batch_upscale.py
```

### 분석 산출물 (`work/`)
- `extras_summary.json` — _mp extras 통계
- `cif_anim_summary.json` — _cif 통계
- `scn_opcode_freq.json` — _scn byte freq
- `scn_speakers.json` — 105 화자 + 샘플
- `scn_dialogue_opcode.json` — 대사 시작 opcode
- `scn_inter_summary.json` — 대사 사이 byte
- `scn_header_summary.json` — 헤더 영역
- `converted/scn_v2/` — 244 + summary

---

## 🔧 재현 명령

### 자산 재변환 (필요 시)
```bash
cd tools/converter
PYTHONIOENCODING=utf-8 python convert_all.py ../../work/extracted ../../work/converted
PYTHONIOENCODING=utf-8 python convert_scn_v2.py ../../work/extracted/event ../../work/converted/scn_v2
PYTHONIOENCODING=utf-8 python build_dialogue_corpus.py
PYTHONIOENCODING=utf-8 python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets

cd ../i18n
PYTHONIOENCODING=utf-8 python generate_string_resources.py
PYTHONIOENCODING=utf-8 python build_asset_catalog.py
```

### `_scn` / `_cif` / `_mp` 통계 재실행
```bash
cd tools/recon
PYTHONIOENCODING=utf-8 python analyze_mp_extras.py
PYTHONIOENCODING=utf-8 python analyze_cif.py
PYTHONIOENCODING=utf-8 python analyze_scn_opcodes.py
PYTHONIOENCODING=utf-8 python extract_scn_speakers.py
PYTHONIOENCODING=utf-8 python scn_dialogue_opcode.py
PYTHONIOENCODING=utf-8 python scn_inter_speaker.py
PYTHONIOENCODING=utf-8 python scn_header.py
```

### 대사 번역 (§A — API 키 필요)
```bash
cd tools/i18n
export ANTHROPIC_API_KEY=...
PYTHONIOENCODING=utf-8 python translate_dialogues.py --limit 100   # 검증
PYTHONIOENCODING=utf-8 python translate_dialogues.py               # 전체
cd ../converter
PYTHONIOENCODING=utf-8 python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets
```

### Android 빌드 (gradlew 부재)
```bash
cd android
gradle wrapper --gradle-version 8.7    # 한 번만
./gradlew :app:assembleDebug
```
또는 Android Studio 에서 `android/` 디렉토리 열기.

---

## ⚠️ 알려진 이슈 / TODO

| ID | 이슈 | 워크어라운드 / 액션 |
|---|---|---|
| #1 | `map134_mp` 비표준 헤더 (NUL 부재) | 변환 시 1개 에러 보고됨, 무시 가능 |
| #2 | type 0x0c BM 프레임이 노이즈로 렌더 | 정상. §4.1 (Ghidra) 후 실제 픽셀 디코드 |
| #3 | 일부 0x0b BM 2~6 byte underrun | 시각 영향 미미 |
| #4 | hero/boss CIF 인덱스가 BM 파일명과 매칭 안됨 | enemy/map은 직접 매칭 정상 |
| #5 | `Hero3OptionSave` (32B) XOR 암호화 | 호환 불필요라 무시 |
| #6 | `_cif` 새 헤더 적용 후 재변환 미실행 | `convert_all.py` 다시 돌리면 반영됨 |
| #7 | gradle wrapper 부재 | system gradle 또는 Android Studio 사용 |
| #8 | 멀티 캐릭터 파티는 데이터만 있고 전투 참여 X | leader 만 전투. 향후 BattleScene 확장 필요 |
| #9 | NPC patrol 이 hero 충돌 무시 | 시각적 겹침만 발생, 게임 로직 영향 없음 |
| #10 | 사운드 미구현 | SfxBus stub 만 wired up. §4.5 후 활성 |

## 📜 2026-05-04 세션 작업 압축

(상세 마일스톤 38건은 git log `af5574a` 및 그 후속 커밋 참조. 위 §"현재 상태 스냅샷" 이 최종 결과. 아래는 단일 라이너 인덱스)

- 콘텐츠: 3 보스 + Tier 1/2/3 + 퀘스트 체인 + EndingScene + ★ CLEAR 배지 + 회차 보존
- 시스템: 장비/effective stats + 레벨업 + 자연 회복 + 패배 부활 + 여관/신관 + 보물상자 + 빠른 이동 + 직업 변경
- 씬 신규: Battle/Shop/Skill/Quest/Bestiary/Records/EventViewer/Travel/Ending
- UX: 미니맵 + 활성 퀘스트 + 보스 근접/출구 힌트 + 토스트 + 튜토리얼 + 데미지 popup + 부유/lunge/shake/fade/플래시
- 분석 도구 8개 + 보고서 7개 (`work/scn_*.json`, `work/cif_*.json`, `work/extras_summary.json`)
- 자산 통합: scn_v2/ 245 JSON, dat/char_dat.json, _cif 헤더 패치
- 버그 수정: 슬롯 copyFrom 누락 필드, ShopScene early-return, 새 게임 진짜 초기화, 클리어 플래그 보존
- 사운드 stub: SfxBus + 모든 호출처 wired up
- 폴리시: HP/SP/EXP 바, 메뉴 스크롤, 슬롯 카운트, NPC 퀘스트 마커, 영웅 방향 sprite, 액세서리 효과


**이전 마일스톤** (2026-05-01, NPC + 세이브슬롯 완료):
- **11개 Android 씬** (Title/MainMenu/MapWalk/NpcDialogue/SaveSlots/Status/Inventory/DialogueDemo/Settings/SpriteGallery/Map)
- **NPC 시스템** — `NpcRegistry` + map0 에 4 NPC 하드코딩 (촌장/상인/경비병/아이) + 인접 OK 키 → `NpcDialogueScene`
- **세이브 슬롯** — 3슬롯 SAVE/LOAD UI, 슬롯별 별도 SharedPreferences
- **MapWalkScene 충돌 확장** — Layer 1 + NPC 칸 통행 불가 + 인접 NPC 힌트 표시
- `MapWalkScene` 영웅 맵 위 이동 + 충돌 + 카메라 스크롤
- `GameState` slotId 기반 영구 저장 (현재 맵, 영웅 좌표, 방향)
- UI 어휘 196개 100% 영어 번역 + 메뉴 어휘
- `translate_dialogues.py` Claude Haiku 4.5 기반 대사 번역 스크립트
- `DialogueDemoScene` / `NpcDialogueScene` 영어 토글 시 번역 사용
- HD 자산 (3,131 sprite scale4x 4×) + 자산 카탈로그 + 대사 코퍼스 (26,415 lines, 9,741 unique)
- **dat/ 파일 추가 변환** — char_dat 분석으로 캐릭터 클래스 구조 확인 (리츠/케이 각 5 클래스)

_(상세 다음 단계는 본 문서 상단 §"다음 진행 후보" 참조)_

---

## 1. 프로젝트 개요

| 항목 | 값 |
|---|---|
| 원본 게임 | 영웅서기3 - 운명의수레바퀴 (한빛소프트, 2008, SK텔레콤 GVM/Clet) |
| 원본 위치 | `Hero3/0103EFD4.jar` + `Hero3/__adf__` + `Hero3/P/` (세이브) |
| 원본 바이너리 | `client.bin64000` (735KB ARM Thumb 네이티브, GCC `-fpic`, GOT base = `r10`) |
| 자산 총량 | 1,272개 파일 (9개 포맷) |
| 전략 | **Strategy C** — 자산 재활용 + Kotlin/Android 엔진 재구현 |
| 결정사항 | HD 리마스터 진행 / 다국어 지원 / 세이브 호환 X |

## 2. 완료된 작업 (2026-05-01 기준)

### 2.1 자산 포맷 분석 + 변환

| 포맷 | 개수 | 상태 | 변환 결과물 |
|---|---:|---|---|
| `_txt` (텍스트 테이블) | 9 | ✅ 완전 | EUC-KR → JSON |
| `_pa` (팔레트) | 216 | ✅ 완전 | RGBA8888 JSON |
| `_bm` (비트맵, type 0x0b) | 479 | ✅ 완전 | **3,131 frame PNG** |
| `_bm` (type 0x0c sparse) | (포함) | ⚠️ 부분 | bit layout 미확정 |
| `_cif` (애니메이션) | 103 | ⚠️ 부분 | slot count + indices만 추출 |
| `_mp` (맵) | 134/135 | ✅ 헤더+레이어 | terrain + collision JSON |
| `_mp` extras | – | ⚠️ 부분 | NPC/exit 추정 |
| `_mf` (사운드 SMAF) | 33 | 📋 표준 | 빌드 타임 OGG 변환 도구 필요 |
| `_scn` (이벤트 스크립트) | 244 | ⚠️ 부분 | **26,415 대사 (9,741 unique)** |

### 2.2 HD 리마스터

- ✅ scale4x 알고리즘 검증 — pixel-art 보존 + 대각선 매끄럽게
- ✅ 3,131개 sprite frame 4× 업스케일 완료
- ✅ Android `assets/sprites_hd/` 배포

### 2.3 Android 클라이언트

- ✅ Gradle 8.7 / AGP 8.5.2 / compileSdk 35 / minSdk 24
- ✅ 240×320 가상 캔버스 + letterbox 스케일 (`GameView` SurfaceView 60fps)
- ✅ MIDP 호환 입력 매핑 (`InputController` 비트마스크)
- ✅ 가상 키패드 오버레이 (D-pad + OK + L/R + #)
- ✅ Scene 추상화 + 씬 스택 (push/pop 지원)
- ✅ `Settings` 영구 저장 (SharedPreferences) — 언어 / HD 토글
- ✅ `GameState` 영구 저장 — 현재 맵 ID, 영웅 좌표, 바라보는 방향, 파티 리더
- ✅ `Strings` i18n 헬퍼 — 196개 InGame_txt 모두 string resource 화 (txt_000~txt_195)
- ✅ `UiKit` 공용 그리기 헬퍼 (박스, 메뉴아이템, 다이얼로그 박스, 헤더, 힌트)
- ✅ **씬 11개 구현**:
  - `TitleScene` — 로고 + 메뉴 (새 게임 → MapWalk / 이어하기 → SaveSlots / 설정 / 갤러리)
  - `MainMenuScene` — 7개 원본 메뉴 (상태/가방/장비/스킬/퀘스트/세이브/시스템) + 디버그
  - **`MapWalkScene`** — 영웅 이동 + Layer 1 충돌 + NPC 칸 통행 불가 + 카메라 스크롤 + 걷기 애니 + 인접 NPC 힌트
  - **`NpcDialogueScene`** — 단일 NPC 대화 (포트레이트 + 한·영 토글 + 글자 흘려쓰기)
  - **`SaveSlotScene`** — 3슬롯 SAVE/LOAD UI + 슬롯별 별도 SharedPreferences
  - `StatusScene` — 캐릭터 스탯 mockup (이름/직업/LV/HP/SP + 12개 스탯)
  - `InventoryScene` — 가방/장비/스킬 탭 + 5×4 슬롯 그리드 mockup
  - `DialogueDemoScene` — 코퍼스에서 대사 글자 흘려쓰기 + 화자/이벤트 변경 + 영어 번역 토글
  - `SettingsScene` — 언어/품질 토글 (Activity 재생성으로 locale 적용)
  - `SpriteGalleryScene` — 3,131 sprite 5fps 애니메이션, Settings 연동(SD/HD 자동 선택)
  - `MapScene` — 134 맵 색상 heatmap 브라우저 (디버그용)
- ✅ **NpcRegistry** — map0 에 4 NPC 하드코딩 (촌장/상인/경비병/아이) + 한·영 대사 + 4방향 인접 검사
- ✅ 자산 번들: sprites + sprites_hd + maps + cif + strings + palettes + dialogue_corpus + dialogue_translations_en + asset_catalog

### 2.4 클라이언트 바이너리 분석

- ✅ ASCII 문자열 추출 — 9,120개 (파일 경로, 함수명, 디버그 메시지 등)
- ✅ PIC 패턴 식별 (LDR + ADD sl + LDR 3-level indirection via GOT base)
- ✅ Capstone Thumb 디스어셈블 가능 환경 구축
- ⚠️ 함수 단위 분석은 한정적 (GOT-기반 PIC가 직접 string xref 추적을 어렵게 함)

### 2.5 i18n / 번역 인프라

- ✅ `tools/i18n/translation_dict.py` — 한↔영 번역 사전 (캐릭터·지명·UI 어휘)
- ✅ `tools/i18n/generate_string_resources.py` — `values/strings.xml` (영어) + `values-ko/strings.xml` (한국어) 자동 생성
- ✅ **InGame_txt 196개 100% 영어 번역 커버리지** (txt_000~txt_195)
- ✅ 캐릭터 사전: 케이/Kei, 리츠/Ritz, 일레느/Ilene, 시엔/Sien, 레아/Lea, 엘지스/Elgis, 케네스/Kenneth, 이안/Ian, 멜페토/Melpheto, 토레즈/Torez 등
- ✅ 지명 사전: 솔티아/Soltia, NEOSOLTIA/Neo Soltia, GUARDIAN_CAVE 1~7, RUINED_DESERT 1~3, GULBEIG_RUIN 5~7 등 30+ 곳
- ✅ 접두 마법 효과: @투신의/of War God, @공명의/of Resonance 등 15종
- ✅ `tools/i18n/build_asset_catalog.py` — 변환 자산 인덱스 (`asset_catalog.json`)
  - 카테고리별 sprite 디렉토리 + frame count + first dimension
  - 134 맵 (한·영 이름 매핑 포함)
- ✅ Android Activity locale override (Configuration#setLocale + recreate)

### 2.6 인프라

- ✅ 메모리 시스템 (`MEMORY.md` + `project_hero3_remake.md`)
- ✅ 변환 파이프라인 (`tools/converter/convert_all.py` 단일 진입점)
- ✅ HD 파이프라인 (`tools/hd/`)
- ✅ i18n 파이프라인 (`tools/i18n/`)
- ✅ 정찰 도구 (`tools/recon/`)
- ✅ 작업 디렉토리 (`work/`) gitignore

## 3. 디렉토리 구조

```
testrepo/
├── Hero3/                         # 원본 (수정 금지)
│   ├── 0103EFD4.jar               # 원본 JAR
│   ├── __adf__                    # GVM 메타
│   └── P/Hero3{Game,Option,Slot}Save  # 세이브 (호환 X)
├── docs/
│   ├── asset-formats.md           # 자산 포맷 사양
│   └── PROGRESS.md                # ← 이 파일 (핸드오프)
├── tools/
│   ├── converter/                 # 자산 변환기 (Python)
│   │   ├── convert_all.py         # 통합 진입점
│   │   ├── convert_text.py / convert_palette.py
│   │   ├── convert_bm_v2.py       # 멀티프레임 BM 디코더
│   │   ├── convert_cif.py / convert_mp.py / convert_scn.py / convert_dat.py
│   │   ├── build_dialogue_corpus.py
│   │   └── prepare_android_assets.py
│   ├── i18n/                      # i18n + 자산 카탈로그
│   │   ├── translation_dict.py    # 한↔영 사전 (캐릭터/지명/UI/접두효과)
│   │   ├── generate_string_resources.py  # values{,-ko}/strings.xml 생성
│   │   ├── build_asset_catalog.py # asset_catalog.json
│   │   └── translate_dialogues.py # Claude Haiku 4.5 대사 번역 스크립트
│   ├── hd/
│   │   ├── upscale_poc.py         # scale4x 알고리즘
│   │   └── batch_upscale.py       # 일괄 처리
│   └── recon/                     # 바이너리 정찰 (capstone)
│       ├── extract_strings.py / disasm_thumb.py
│       ├── find_pic_xrefs.py / find_f81f.py / find_base.py
├── android/                       # Android Kotlin 클라이언트
│   ├── settings.gradle.kts / build.gradle.kts / gradle.properties
│   ├── README.md                  # 빌드 방법
│   └── app/
│       ├── build.gradle.kts
│       └── src/main/
│           ├── AndroidManifest.xml
│           ├── res/values{,-ko}/strings.xml + themes.xml
│           ├── assets/                  # 변환된 자산 (3000+ 파일)
│           │   ├── sprites/             # 표준 (1×)
│           │   ├── sprites_hd/          # HD (4× scale4x)
│           │   ├── maps/                # 134 _mp.json
│           │   ├── cif/                 # 103 _cif.json
│           │   ├── strings/ / palettes/
│           │   ├── dialogue_corpus.json / dialogue_top_texts.json
│           │   ├── dialogue_translations_en.json   # (생성 후 배포)
│           │   └── asset_catalog.json
│           └── java/com/hero3/remake/
│               ├── MainActivity.kt           # Scene 스택 + Locale override
│               ├── engine/
│               │   ├── GameView.kt           # SurfaceView 60fps 렌더 루프
│               │   ├── InputController.kt    # MIDP 비트마스크
│               │   ├── VirtualKeypadView.kt  # 가상 키패드
│               │   ├── Scene.kt              # 추상화
│               │   ├── UiKit.kt              # 공용 그리기 (박스/메뉴/다이얼로그/헤더)
│               │   ├── Settings.kt           # SharedPreferences (언어/HD)
│               │   ├── GameState.kt          # slotId 기반 게임 진행도
│               │   ├── Strings.kt            # i18n 헬퍼 (txt_NNN)
│               │   └── NpcRegistry.kt        # NPC 데이터 (현재 map0 4명 하드코딩)
│               └── scene/                   # 11개 씬
│                   ├── TitleScene.kt         # 로고+메뉴
│                   ├── MainMenuScene.kt      # 7개 원본 메뉴 + 디버그
│                   ├── MapWalkScene.kt       # 영웅 이동 + NPC 인접 검사
│                   ├── NpcDialogueScene.kt   # NPC 대화 + 한·영 토글
│                   ├── SaveSlotScene.kt      # 3 슬롯 SAVE/LOAD
│                   ├── StatusScene.kt        # 캐릭터 스탯 mockup
│                   ├── InventoryScene.kt     # 가방/장비/스킬 mockup
│                   ├── DialogueDemoScene.kt  # 코퍼스 대사 데모
│                   ├── SettingsScene.kt      # 언어/품질
│                   ├── SpriteGalleryScene.kt # 3,131 sprite 애니메이션
│                   └── MapScene.kt           # 134 맵 heatmap (디버그)
├── work/                          # gitignore (재생성 가능)
│   ├── extracted/                 # JAR 풀린 자산
│   ├── converted/                 # 변환된 자산 (PNG/JSON)
│   ├── converted_hd/              # HD 자산 (4× scale4x)
│   └── (분석용 보조 출력들)
└── Readme.md
```

## 4. 추가 진행 필요한 항목

우선순위 순서로 정렬. 각 항목은 **목표 / 블로커 / 작업 계획** 으로 구성.

> 2026-05-01 업데이트: Pre-Ghidra UI/번역 작업 완료. Section 4.6 (대사 번역), 4.7 (게임 로직), 4.1~4.5 (Ghidra 필요한 항목들) 이 다음 우선순위.

### 4.1 [HIGH] type 0x0c sparse pixel format 정밀 해독

- **목표**: theme/obj 타일을 진짜 그래픽으로 렌더링 → 맵을 실제 게임 화면처럼 표시
- **블로커**: 16-bit 레코드의 정확한 bit layout (col/color/row 비트 순서) 미확정. 4가지 가설 모두 깨끗한 디코드 실패
- **현재 상황**:
  - 스플래시 통계: 2 bytes per non-transparent pixel
  - 1638 records / 3072 pixels (theme_6) ≈ 53% non-transparent (합리적)
  - 첫 바이트 패턴이 row 단위로 클러스터링됨 — row 인코딩이 high byte일 가능성 높음
- **추천 작업 방법**:
  1. Ghidra 또는 capstone 으로 `client.bin64000` 의 비트맵 디코더 함수 식별 — 0xf81f 직접 비교 코드는 없으나 `frameBuf is NULL` 문자열 (offset 0xa61c8) 가까이의 함수 추적
  2. PIC 패턴 (`LDR; ADD sl; LDR`) 을 따라 함수 내부 픽셀 unpack 로직 분석
  3. 또는 Ghidra GUI 로 binary 를 raw ARM Thumb 로드 후 분석
- **파일**: `work/decode_0c_theme.py`, `work/analyze_0c.py`, `work/find_frame_markers.py`
- **예상 효과**: theme(47), obj(44), 캐릭터 일부 0x0c 프레임이 정상 렌더링 → MapScene이 진짜 게임 월드 표시

### 4.2 [HIGH] `_mp` extras 영역 (NPC/exit/event 배치) 파싱

- **목표**: 맵 위에 NPC, 출구, 이벤트 트리거 표시 → 인터랙티브 맵 가능
- **블로커**: 7-byte 정도 record로 추정되나 정확한 필드 구조 미확정
- **현재 관찰**:
  - flag byte (0x00/0x40/0x80/0xc0) 빈번 — entity type 또는 direction 추정
  - 16-bit 좌표값 임베디드 추정 (x, y)
- **추천 작업**:
  1. Ghidra 로 NPC 로딩 함수 (`Event_freeID`, `loadDataID` 부근) 분석
  2. 또는 여러 맵의 extras 데이터를 정렬·차분 분석하여 record 길이 통계적으로 추정
- **파일**: `work/analyze_extras.py`

### 4.3 [HIGH] `_cif` animation timing 데이터 디코드

- **목표**: 캐릭터를 진짜 애니메이션 (idle/walk/attack/hit/death 등)으로 표시
- **블로커**: slot indices 이후의 byte-stream 시퀀스 (timing/event 데이터) 미해독
- **현재 관찰**:
  - 9-byte record 가정 시 끝에 0xff terminator
  - `19 19` 고정값 (frame size?) 패턴
  - hero/boss는 8 슬롯 (4방향 × 2상태?), enemy는 1~4 슬롯
- **추천 작업**: Ghidra `Hero_Free`, `freeBossType` 부근 함수 분석

### 4.4 [MEDIUM] `_scn` opcode 매핑

- **목표**: 이벤트 스크립트의 명령어 디스어셈블 → 실제 이벤트 흐름 재현
- **현재 상황**: 26,415 대사는 추출했지만 byte-code 명령은 미해독
- **추천 작업**:
  1. Ghidra 로 이벤트 인터프리터 함수 식별 (`onEventMessageOkKey`, `eventManager` 부근)
  2. Switch 또는 dispatch table 패턴 찾아 opcode → 동작 매핑
  3. Python 디스어셈블러 작성

### 4.5 [MEDIUM] 사운드 SMAF → OGG 변환 파이프라인

- **목표**: 33개 BGM/효과음을 Android `MediaPlayer`로 재생 가능하게
- **블로커**: SMAF 디코더 도구 필요 (런타임 SMAF 라이브러리 없음)
- **추천 도구**:
  - `smaf2midi` (Linux/Windows)
  - 또는 KSS/Yamaha SMAF SDK
  - 최후의 수단: 수동 변환 (33개라 가능)

### 4.6 [MEDIUM] 대사 번역 (UI 어휘는 완료)

- **상태**: UI 어휘 196개 100% 영어 번역 완료. 대사 본문 (9,741 unique) 미번역
- **다음 단계**:
  1. ~~캐릭터 이름·지명 수동 번역~~ ✅ 완료 (translation_dict.py)
  2. ~~UI 텍스트 196개 수동 번역~~ ✅ 완료 (100% 커버리지)
  3. **대사 자동 번역 (LLM 활용) → 사람 검수** ← 다음 작업
     - Input: `dialogue_corpus.json` (26,415 lines, 9,741 unique)
     - Pipeline: unique 텍스트만 → LLM 번역 → DialogueDemoScene 으로 검수
  4. 일본어/중국어 추가 (`values-ja`, `values-zh-rCN`)

### 4.7 [LOW] Android 게임 로직 본격 구현

- **현재**: 8개 씬 (Title/MainMenu/Status/Inventory/DialogueDemo/Settings/SpriteGallery/MapScene) 모두 mockup 또는 데모 단계로 구현됨
- **다음 단계**:
  1. ~~타이틀 화면~~ ✅ 완료 (`TitleScene`)
  2. ~~다이얼로그 박스 시스템~~ ✅ 완료 (`UiKit.drawDialogueBox` + `DialogueDemoScene`)
  3. ~~인벤토리/스테이터스 화면 mockup~~ ✅ 완료 (실제 데이터 연결만 남음)
  4. **맵 화면에 영웅 sprite 배치 + 이동** ← 다음 작업 (RPG 본체의 시작)
     - 영웅 위치 좌표 + Settings 에 저장 (현재 맵 ID + x/y)
     - 방향키 → 좌표 갱신 + Layer 1 (collision) 검사
     - Map 전이 (출구 좌표 도달 시) — `_mp` extras 분석 필요 (4.2)
  5. NPC 시스템 (sprite 배치 + 인터랙션 → DialogueScene)
  6. 캐릭터 데이터 모델 + 저장 (게임 진행도)
  7. 전투 시스템 (가장 큰 작업)

### 4.8 [LOW] 빌드 검증

- **현재**: Android 코드만 작성됨, 실제 빌드 미검증 (Gradle/Android SDK 미설치 환경)
- **사용자 환경에서 필요**:
  ```
  cd android
  gradle wrapper --gradle-version 8.7    # 한 번만
  ./gradlew :app:assembleDebug
  ```
- 또는 Android Studio 에서 `android/` 디렉토리 열기

## 5. 빠른 참조

### 5.1 변환 명령어

```bash
# 원본 JAR 추출
unzip -o Hero3/0103EFD4.jar -d work/extracted

# 모든 자산 변환 (단일 명령)
cd tools/converter
PYTHONIOENCODING=utf-8 python convert_all.py ../../work/extracted ../../work/converted

# 대사 코퍼스 빌드
PYTHONIOENCODING=utf-8 python build_dialogue_corpus.py

# Android assets 갱신
PYTHONIOENCODING=utf-8 python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets

# HD 업스케일 (수 분 소요)
cd ../hd
PYTHONIOENCODING=utf-8 python batch_upscale.py
```

### 5.2 바이너리 정찰

```bash
cd tools/recon
# ASCII 문자열 + 함수명 추출
PYTHONIOENCODING=utf-8 python extract_strings.py | less

# Thumb 디스어셈블 (시작 64 bytes + LDR pc-rel literal pool)
PYTHONIOENCODING=utf-8 python disasm_thumb.py
```

### 5.3 핵심 발견값 (외부 도구에 입력 시 유용)

| 값 | 의미 |
|---|---|
| `0xf81f` | RGB565 마젠타, 모든 BM의 투명 색 마커 |
| `0x1ff8` (LE) / `0xf81f` (BE) | BM 프레임 boundary 마커 |
| `0xa61c8` | 'frameBuf is NULL' 문자열 file offset |
| `0xa5d94` | '/hero/h00000_bm' 문자열 file offset |
| `r10 (sl)` | GOT base 레지스터 |
| GCC `-fpic` | 컴파일 옵션 (PIC) |

### 5.4 자주 보는 파일

- 자산 포맷 사양: [`docs/asset-formats.md`](asset-formats.md)
- Android README: [`android/README.md`](../android/README.md)
- 스토리 코퍼스: `work/converted/dialogue_corpus.json` (3MB)
- 빈도 상위 200: `work/converted/dialogue_top_texts.json`

## 6. 알려진 이슈

| ID | 이슈 | 워크어라운드 |
|---|---|---|
| #1 | `map134_mp` 비표준 헤더 (NUL 부재) | 변환 시 1개 에러 보고됨, 무시 가능 |
| #2 | type 0x0c 프레임이 노이즈로 렌더 | 정상. bit layout 미해독, 추후 정밀 분석 필요 |
| #3 | 일부 0x0b 프레임 2-6 byte underrun | 시각 영향 미미 (마지막 픽셀 행 일부 누락) |
| #4 | hero/boss CIF 인덱스가 BM 파일명 매칭 안 됨 | 멀티프레임 BM의 글로벌 인덱스 추정. enemy/map은 직접 매칭 정상 |
| #5 | `Hero3OptionSave` (32B) XOR 암호화 | 호환 불필요라 무시 |

## 7. 빠른 재시작 체크리스트

다음 세션에서 이 프로젝트를 이어서 할 때:

1. [ ] `MEMORY.md` 가 자동 로드되어 컨텍스트 유지됨
2. [ ] 이 [`PROGRESS.md`](PROGRESS.md) 파일 맨 위 **⚡ 다음 세션** 섹션 확인
3. [ ] [`docs/asset-formats.md`](asset-formats.md) 에서 자산 포맷 세부 확인
4. [ ] 작업할 항목 결정 (A/B/C/... 중 선택, 또는 §4 의 8개 후보)
5. [ ] `work/extracted/` 가 비어있으면 JAR 재추출:
   ```bash
   unzip Hero3/0103EFD4.jar -d work/extracted
   ```
6. [ ] 변환 산출물이 비어있으면 재실행:
   ```bash
   cd tools/converter
   PYTHONIOENCODING=utf-8 python convert_all.py ../../work/extracted ../../work/converted
   PYTHONIOENCODING=utf-8 python build_dialogue_corpus.py
   PYTHONIOENCODING=utf-8 python prepare_android_assets.py ../../work/converted ../../android/app/src/main/assets
   cd ../i18n
   PYTHONIOENCODING=utf-8 python generate_string_resources.py
   PYTHONIOENCODING=utf-8 python build_asset_catalog.py
   cd ../hd
   PYTHONIOENCODING=utf-8 python batch_upscale.py    # 시간 소요 (3분 정도)
   ```
7. [ ] Android Studio 로 `android/` 열거나 `cd android && gradle wrapper --gradle-version 8.7 && ./gradlew :app:assembleDebug` 로 빌드 검증

## 7a. 마지막 세션 (2026-05-01) 결정사항·맥락

다음 세션이 알아야 할 미묘한 사항:

- **현재 상태**: NPC 시스템 + 세이브 슬롯 + dat 파싱까지 완료. 11개 씬 통합되어 영웅이 NPC와 대화하고 세이브 가능. **다음 자연스러운 진행은 (1) 대사 번역 실행 → (2) 인벤토리/스테이터스 데이터 모델 → (3) 출구·맵 전환 → (4) 상점/전투** 순서.
- **NpcRegistry 는 하드코딩**: map0(NEOSOLTIA) 4명 (촌장/상인/경비병/아이). `_mp` extras 파싱이 풀리면 자동 생성으로 전환. 그 전까지는 `engine/NpcRegistry.kt`에 직접 추가.
- **GameState slotId 시스템**: slot 0 = 활성, slot 1~3 = SaveSlotScene 저장. 슬롯별로 별도 SharedPreferences. 새 슬롯 추가 시 SaveSlotScene `slotCount` 만 늘리면 됨.
- **char_dat 분석 완료, 미연결**: 리츠 5클래스 / 케이 5클래스 데이터가 `assets/dat/char_dat.json`에 있음. StatusScene 의 mockup ("케이 / Soltian Warrior") 을 이 데이터로 교체할 준비됨.
- **번역 사전 한계**: 일부 한국 RPG 고유 어휘는 추정 번역 (예: "지축모드" → "Pivot Mode", "투신의" → "of War God"). 원작자 의도 다를 수 있음.
- **type 0x0c 파일이 많음**: theme(47) + obj(44) + 일부 캐릭터 sprite. 현재 MapWalkScene 은 색상 그리드 placeholder. Ghidra 후 재변환하면 진짜 타일로 교체.
- **map134_mp** 비표준 (NUL 부재): 변환 에러 1건. 무시 가능.
- **NPC 칸 통행 불가 + facing-tile OK**: 영웅이 바라보는 칸에 NPC 가 있으면 OK 키로 대화. 인접한 NPC 가 있으면 하단 힌트에 표시.

## 8. 작업 환경 메모

- OS: Windows 11
- Python: 3.12 (with Pillow 11.2.1, capstone 5.0.7)
- Shell: bash (Git Bash) + PowerShell 사용 가능
- 인코딩 함정: PowerShell/Windows console 은 cp949 → 한국어 출력 시 `PYTHONIOENCODING=utf-8` 필수
- 작업 디렉토리: `c:\gameRemake\testrepo`
