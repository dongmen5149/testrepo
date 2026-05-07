# Hero4 Remake — 진행 상황 & 핸드오프

> 다음 세션에서 가장 먼저 읽기. 디테일은 분류별 폴더 / 파일 참조.

## ⚡ 다음 세션 — 시작 전 30초 체크

| 질문 | 답 위치 |
|---|---|
| 이번 세션에 뭐 했나 | 이 문서 §스냅샷 |
| 자산 포맷 분석 디테일 | [`formats/`](formats/) (5 + README) |
| 바이너리 정찰 결과 | [`binary/recon-results.md`](binary/recon-results.md) |
| Ghidra GUI 분석 가이드 | [`ghidra-guide.md`](ghidra-guide.md) |
| **앞으로 뭐 해야 하나** | [`next-steps.md`](next-steps.md) |
| 프로젝트 전체 (Hero3 포함) 컨텍스트 | [`../../Readme.md`](../../Readme.md), 메모리 `project_hero4_remake.md` |

---

## 📊 현재 상태 스냅샷 (2026-05-07 갱신)

### Phase A — 자산 변환 ✅ **종료**

```
python tools/converter/convert_all.py work/h4/extracted work/h4/converted

Done. txt=5 pa=196 bm_files=30 bm_frames=200 cif=148 mp=0 scn=350
      scn_dialogues=4078 dat=26 h4_map=97 exd=117 h4_tile=276
      skipped=564 errors=0
```

| 카테고리 | 결과 |
|---|---|
| _TXT, _CIF, _DAT, _SCN, _MMF | Hero3 호환 (자세히는 [`formats/README.md`](formats/README.md)) |
| _PAL (8byte/color) | **196/196** — [`formats/pal.md`](formats/pal.md) |
| _MAP_M_NNN (3가지 헤더 버전 + 풀 body) | **97/97** — [`formats/map.md`](formats/map.md) |
| _EXD (헤더 추출, payload 보존) | **117/117** — [`formats/exd.md`](formats/exd.md) |
| TILE/, OBJ/{000,001,002}/ (single-frame 0x0c 8-bit dense) | **30 + 246 PNG** — [`formats/bm-tile-obj.md`](formats/bm-tile-obj.md) |
| HDAT/ (그룹 분류만) | 25 (Phase B 후 파싱) — [`formats/hdat.md`](formats/hdat.md) |

### 인프라 완성

- ✅ `tools/_game.py` — 게임-aware path 중앙 관리 (`HERO_GAME` 환경변수)
- ✅ `apps/hero4-android/` — Android 모듈 스켈레톤 (com.hero4.remake), 자산 699 file 배포
- ✅ `work/h4/converted_hd/` — scale4x 4× HD 209 PNG
- ✅ `work/h4/converted/dialogue_corpus.json` — 4,078 대사 corpus
- ✅ `work/h4/converted/asset_catalog.json` — 97 maps + 30 sprite dirs

### 핵심 발견

- ⭐ **0x0c BM = 8-bit dense palette indexed** (Ghidra `FUN_00010fe4` 분석). Hero3 미해독 91 BM (theme 47 + obj 44) 도 동시 unblocking
- **_PAL** 8byte/color (Hero3 4byte 의 2배) — primary + secondary RGB 페어
- **_MAP_M_** 헤더 버전 일반화: `0xff` separator 개수 = v, `nlen` offset = `2v+1`
- **_MAP_M_** post-NUL body = Hero3 `_mp` 100% 동일 layout
- Hero4 zone 이름 = **켈트 신화 Tuatha Dé Danann** 패러디 (뮤리아스/핀디아스/팔리아스)
- Hero3+Hero4 = **같은 한빛 내부 엔진의 진화형** (`'frameBuf is NULL'` 동일 에러)
- `client.bin387872` 안에 **WIPI/JLet API 임베드** (`org/kwis/msp/lcdui/*`) — Clet+KTF 호환 빌드
- 모든 자산 path string 이 binary 에 명시되어 디스어셈블 없이도 자산 로딩 흐름 파악 가능

---

## 📁 디렉토리 구조

### 코드/도구
```
tools/
├── _game.py                      ← 게임 path/binary 설정 중앙 관리
├── converter/
│   ├── convert_all.py            ← 게임-aware 일괄 변환
│   ├── convert_palette.py        ← Hero3 4byte + Hero4 8byte 듀얼
│   ├── convert_h4_map.py         ← Hero4 _MAP_M_NNN
│   ├── convert_h4_tile.py        ← Hero4 single-frame BM (TILE/OBJ)
│   ├── convert_exd.py            ← Hero4 _EXD 헤더
│   ├── convert_bm_v2.py          ← BM 디코더 (0x0b dense 4-bit, 0x0c dense 8-bit)
│   └── ... (Hero3 와 공유)
├── recon/                        ← `HERO_GAME` env 로 게임 선택
└── i18n/                         ← `HERO_GAME` env 로 게임 선택
```

### 자산
```
Hero4/010100D4.jar               ← 원본 (수정 금지)
work/h4/                         ← gitignore
├── extracted/                   ← JAR 추출 (1,850 file)
├── converted/                   ← PNG/JSON 변환 결과
├── converted_hd/                ← scale4x 4× upscale
└── ghidra_proj/                 ← Phase B 시 생성

apps/hero4-android/              ← 모노레포 옵션 A
├── app/src/main/
│   ├── java/com/hero4/remake/MainActivity.kt   ← Phase 3 placeholder
│   ├── assets/                  ← 변환된 자산 699 files
│   └── res/values/strings.xml + values-ko/strings.xml
├── build.gradle.kts             ← com.hero4.remake
└── README.md
```

### 문서
```
docs/h4/
├── PROGRESS.md                  ← 이 문서 (메인 핸드오프)
├── next-steps.md                ← 앞으로 해야 할 것 (★ 다음 작업 시 읽기)
├── ghidra-guide.md              ← Ghidra GUI 분석 가이드
├── formats/                     ← 자산 포맷 분석 디테일
│   ├── README.md                ← 인덱스
│   ├── pal.md                   ← _PAL 8byte/color
│   ├── map.md                   ← _MAP_M_NNN
│   ├── exd.md                   ← _EXD 캐릭터 데이터
│   ├── bm-tile-obj.md           ← BM 0x0b/0x0c, TILE, OBJ 디코더
│   └── hdat.md                  ← HDAT/ 25 파일 그룹 분류
└── binary/
    └── recon-results.md         ← client.bin387872 정찰 결과
```

---

## 🔧 재현 명령

### 자산 재변환

```bash
cd c:/gameRemake/testrepo

# Hero4 (default 가 h3 라 환경변수 명시)
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted

# Hero4 Android assets 배포
python tools/converter/prepare_android_assets.py work/h4/converted apps/hero4-android/app/src/main/assets

# Hero4 HD 업스케일
HERO_GAME=h4 python tools/hd/batch_upscale.py

# Hero4 대사 corpus + asset catalog
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/i18n/build_asset_catalog.py
```

### 바이너리 정찰

```bash
HERO_GAME=h4 python tools/recon/extract_strings.py     # 8,167 strings
HERO_GAME=h4 python tools/recon/find_f81f.py           # 0xf81f 위치 10
HERO_GAME=h4 python tools/recon/disasm_thumb.py        # 첫 256 byte 디스어셈블
```

### Android 빌드 (스켈레톤)

```bash
cd apps/hero4-android
./gradlew assembleDebug
# 결과: app/build/outputs/apk/debug/app-debug.apk
# 현재 placeholder Activity (검은 화면 + "Phase 3 통합 대기 중")
```

---

## ⚠️ 알려진 이슈 / 보류

- ~~**`_TILE_030`**~~ ✅ **풀림 (2026-05-07)**: 컨테이너 prefix `01 00 00 00 <size LE32>` 감지 → inner BM 으로 재진입. [convert_h4_tile.py](../../tools/converter/convert_h4_tile.py) 에 반영. h4_tile=276→**277**, skipped=564→563
- **work/h3/ghidra_proj/*.lock** — Hero3 Ghidra 프로젝트 락이 걸려있어 work/h3/ 일부 이동 못 함. Ghidra 닫고 락 정리 필요
- ~~**`tools/recon/find_xrefs.py`, `find_pic_xrefs.py`, `find_base.py`** — hardcoded TARGETS~~ ✅ **풀림 (2026-05-07)**: [extract_strings.py](../../tools/recon/extract_strings.py) `--json` 옵션 + [_targets.py](../../tools/recon/_targets.py) 헬퍼 도입. 3 스크립트 모두 game-aware. h3/h4 양쪽 검증
- **`_PAL` secondary RGB 의미** — 미확정. 가장 유력한 가설은 alpha mask. Phase B 에서 확정
- **_EXD payload, _MAP_M_ extras, HDAT entry layout** — 모두 Phase B 후 확정
- **Hero4 binary 의 string xref 추적** — h3 와 다른 addressing (PIC LDR+ADD T1 인접 패턴 거의 없음). Phase B Ghidra GUI 에서는 32-bit LDR.W (T4) 또는 다른 sequence 추적 필요

---

## 📜 이번 세션 (2026-05-06) 작업 압축

1. **모노레포 옵션 A 결정** + 디렉토리 분리 (work/h{3,4,5}, docs/h{3,4,5})
2. **`tools/_game.py`** 게임-aware 모듈 + 모든 hardcoded path 리팩터
3. **Hero4 JAR 추출** 후 Hero3 컨버터 dry-run → 호환률 ~80% 측정
4. **`_PAL` 8byte/color 분기 추가** → 196/196 변환
5. **`_MAP_M_NNN` 파서 작성** (헤더 v1/v2/v3 + 풀 body) → 97/97 변환
6. **`_EXD` 헤더 파서** 작성 → 117/117 변환 (payload 보존)
7. **TILE/OBJ single-frame BM 디코더** (`convert_h4_tile.py`) → 276 PNG
8. **0x0c BM 디코더 풀이** (Ghidra `FUN_00010fe4` 분석 결과를 사용자가 docstring 으로 반영, 코드 동기화). Hero3 미해독 91 BM 동시 unblocking
9. **client.bin387872 정찰** (extract_strings 8,167개, find_f81f 10 위치)
10. **Hero4 Android 모듈 스켈레톤** (`apps/hero4-android/`, com.hero4.remake) 생성 + 자산 699 file 배포
11. **Hero4 i18n / HD / dialogue corpus** 인프라 구동 (build_asset_catalog 의 폴더 카테고리 game-aware 화)
12. **문서 재구성** — `formats/` (5+1), `binary/` (1), `next-steps.md`, 메인 PROGRESS

errors=0 양 게임 모두. 다음: [`next-steps.md`](next-steps.md) 의 Phase B 또는 A1/A4 자동 작업.

---

## 📜 세션 (2026-05-07) 작업 압축

1. **A4 — recon 도구 game-aware 리팩토링 완료**
   - [extract_strings.py](../../tools/recon/extract_strings.py): `--json OUT` / `--game` / `--quiet` 옵션. path-like + 라벨을 자동 추출, `code_end_estimate` 도 path-like 최소 offset 으로 자동 산출
   - [_targets.py](../../tools/recon/_targets.py) 신규: `load_targets(priority_only=...)` 게임별 JSON 로더
   - [find_xrefs.py](../../tools/recon/find_xrefs.py), [find_pic_xrefs.py](../../tools/recon/find_pic_xrefs.py), [find_base.py](../../tools/recon/find_base.py) 의 hardcoded TARGETS 모두 제거
   - 산출: `work/h3/converted/string_offsets.json` (105 targets), `work/h4/converted/string_offsets.json` (93 targets)
   - Hero4 정찰로 발견: code/data 경계 ≈ **0x77000**, 핵심 라벨 4개 (`====> Alpha Palette Index Not Found` @0x820dc, `====> frameBuf is NULL` @0x82104, `java/lang/NullPointerException`, `(null)`)

2. **A5 — `_TILE_030` 풀림**
   - 컨테이너 포맷: `01 00 00 00` (count?) + size LE32 (0x8d=141) + inner BM
   - [convert_h4_tile.py](../../tools/converter/convert_h4_tile.py) 의 `decode_h4_tile` 에 prefix 감지 분기 추가
   - 결과: 16×16 dark blue placeholder tile. h4_tile 카운트 +1
   - `01 00 00 00` prefix 가 있는 파일은 TILE/OBJ 통틀어 단 1개 (`_TILE_030`) — 일회성 케이스

3. **인프라 정리**
   - Hero3 layout 마이그레이션: `work/extracted/` → `work/h3/extracted/` (`_game.py` 가 기대하는 nested 레이아웃)
   - Hero4 JAR 추출: `work/h4/extracted/client.bin387872`

4. **문서**
   - [docs/REMAKE_METHODOLOGY.md](../REMAKE_METHODOLOGY.md) 신규 — "리메이크" 의 정의 + JAR/APK 케이스별 작업 방식 + 시리즈 진행 기록
   - [Readme.md](../../Readme.md) 상단에 방법론 문서 링크 추가

---

## 📜 세션 (2026-05-07 후속) — A3 + DES 발견

1. **A3 — translation_dict.py game-aware 리팩토링 완료**
   - `CHARACTERS_H3` / `CHARACTERS_H4`, `PLACES_H3` / `PLACES_H4` 분리 (이전 `CHARACTERS` / `PLACES` 는 H3 alias 로 보존 → 기존 호출자 무회귀)
   - `for_game(id)` / `all_translations(id)` 게임별 묶음 조회 API 추가
   - [translate_dialogues.py](../../tools/i18n/translate_dialogues.py) 의 `build_system_prompt` 가 `_g.id` 기반으로 게임 헤더 (`GAME_HEADERS`) + dict 자동 선택
   - Hero4 zone 12개 prefill: 뮤리아스/핀디아스/팔리아스/고리아스 (켈트 4 보물 도시) + 수레바퀴섬/매도우힐/이름없는섬/아눈섬/검은바위섬/은바위섬/해적소굴/환영의검
   - `--dry-run` 이 corpus 부재시에도 system prompt 검증 가능하도록 수정
   - 검증: `HERO_GAME=h4 python translate_dialogues.py --dry-run` → 219 항목, Hero4 헤더 + Tuatha Dé Danann 설명 정상 출력. Hero3 회귀 없음 (249 항목 그대로)

2. **🚨 A1 차단 원인 발견 — Hero4 SCN = DES 암호화**
   - 증상: `dialogue_corpus.json` 에 한자/깨진 문자 (`曝삑킴`, `承孼`, `偉煌`) — Hero3 의 EUC-KR extractor 가 random 바이트를 garbage 로 디코딩
   - Hero3 SCN 첫 64B = `00 00 00 ff ff ff ...` plaintext bytecode
   - Hero4 SCN 첫 64B = `28 69 6c 88 a4 2a ca 09 ...` **high-entropy 암호 바이트**
   - **결정적 단서**: `work/h4/extracted/DAT/_DAT_DES` (824 bytes) 가 표준 DES 알고리즘 테이블 (PC-1, E-box, P-box, S1) 을 그대로 담고 있음을 검증. 따라서 Hero4 는 표준 DES (custom 알고리즘 아님)
   - Hero5 의 `KEY4ENCRYPT` (`ff 00 00 00 0a 33 22 3c 31 11 21 39 02 09 13 2a`) 패턴을 Hero4 binary 에서 검색 → **NOT FOUND**. Hero4 는 별도 키 사용
   - **다음 단계 (Phase B 1순위)**: Ghidra 에서 `/DAT/_DAT_DES` (string @ 0x86ecc) xref 추적 → SCN decryption 진입점 → DES key 8 bytes 추출. 키 발견 후 SCN 재복호화 → corpus 재생성 → A1 진행 가능

3. **문서 갱신**
   - [next-steps.md](next-steps.md): A1 ⛔ DES 차단 표시, Phase B 우선순위 표 최상단에 **DES key (8 bytes)** 추가
   - 해당 발견 요약 inline note 추가

다음 작업: **Phase B (Ghidra GUI)** — A2 (Ghidra 프로젝트 셋업) 부터 사용자 환경 작업 필요. 1순위 함수: `_DAT_DES` xref → SCN decrypt 진입점 → 8-byte key 발굴.
