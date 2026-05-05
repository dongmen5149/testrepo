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

## 📊 현재 상태 스냅샷 (2026-05-06)

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

- **`_TILE_030`** — 다른 헤더 prefix (file header 8 byte 추가). 30개 중 1개만 — 향후 [`formats/bm-tile-obj.md`](formats/bm-tile-obj.md) 참조
- **work/h3/ghidra_proj/*.lock** — Hero3 Ghidra 프로젝트 락이 걸려있어 work/h3/ 일부 이동 못 함. Ghidra 닫고 락 정리 필요
- **`tools/recon/find_xrefs.py`, `find_pic_xrefs.py`, `find_base.py`** — TARGETS 가 Hero3 string offset hardcoded → Hero4 에 noise. game-aware 리팩터 필요 (`next-steps.md` A4)
- **`_PAL` secondary RGB 의미** — 미확정. 가장 유력한 가설은 alpha mask. Phase B 에서 확정
- **_EXD payload, _MAP_M_ extras, HDAT entry layout** — 모두 Phase B 후 확정

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
