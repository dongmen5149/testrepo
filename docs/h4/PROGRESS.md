# Hero4 Remake — 진행 상황 & 핸드오프

> 다음 세션에서 가장 먼저 읽기. 디테일은 분류별 폴더 / 파일 참조.

## ⚡ 다음 세션 — 시작 전 30초 체크

> **최신 상태 (2026-05-14)**: Hero4 자동 영역 **완전 종결**. DES brute-force v2 + ECB 단정 + HDAT PS schema 추론 완료. Phase B (Ghidra GUI) 만 차단.

| 질문 | 답 위치 |
|---|---|
| 이번 세션에 뭐 했나 | 이 문서 §최신 세션 (2026-05-14) |
| **지금 1순위 차단 이슈** | **DES key 8 bytes (Phase B Ghidra)** — §🚨 핵심 차단 |
| **"영웅서기4 다음 작업 진행" 시 어디부터?** | [`next-steps.md` §빠른 셀렉터](next-steps.md#⏭-영웅서기4-이어서-진행해줘-라고-했을-때--빠른-셀렉터) **★ 첫 줄부터 그대로 따라하면 됨** |
| 사용자가 DES key 가져오면? | 1초 검증: `python -c "from Crypto.Cipher import DES; print(DES.new(bytes.fromhex('<KEY>'), DES.MODE_ECB).decrypt(bytes.fromhex('3b7af9a427907dac')).hex())"` → low-entropy 면 정답 |
| 자산 포맷 분석 디테일 | [`formats/`](formats/) (5 + README, HDAT 는 2026-05-14 갱신) |
| 바이너리 정찰 결과 | [`binary/recon-results.md`](binary/recon-results.md) + 2026-05-14 추가: `J@IWO8N7L0E7E` @0x86edc |
| Ghidra GUI 분석 가이드 | [`ghidra-guide.md`](ghidra-guide.md) (2026-05-14: §5.1 DES key 발굴 절차 추가) |
| **앞으로 뭐 해야 하나** | [`next-steps.md`](next-steps.md) ★ 빠른 셀렉터 |
| 프로젝트 전체 (Hero3 포함) 컨텍스트 | [`../../Readme.md`](../../Readme.md), 메모리 [[project-hero4-state]] / [[project-hero4-des-key]] |

---

## 🚨 핵심 차단 — DES key (다음 세션 1순위)

Hero4 SCN 350개 + 대사 corpus = **표준 DES ECB 로 암호화** (2026-05-14 100% 확정). 자동 brute-force 완전 한계 → Ghidra GUI 작업 필수.

**바로 시작 명령**:
```bash
# 1. Ghidra 락 해제 (열려있으면 먼저 종료)
rm work/h3/ghidra_proj/*.lock work/h3/ghidra_proj/*.lock~ 2>/dev/null

# 2. Hero4 Ghidra 프로젝트 생성
#    File > New Project > work/h4/ghidra_proj/Hero4
#    File > Import > work/h4/extracted/client.bin387872
#    Language: ARM:LE:32:Cortex (gcc)

# 3. 우선 추적 string xref:
#    "/DAT/_DAT_DES" @ 0x86ecc → 사용 함수 = SCN decrypt 진입점
#    그 함수 호출자에서 8-byte literal 또는 키 파생 input 추출
#    🔍 **추가 단서 (2026-05-14)**: `_DAT_DES` 바로 다음 (0x86edc) 에
#       의문의 13-char ASCII 문자열 `J@IWO8N7L0E7E\x00` 존재.
#       label / 스크램블 키 / 별도 자원 명일 가능성. 이 string 의 xref 도 같이 확인.

# 4. 키 발견 후 즉시 (자동 — Claude 가 처리 가능):
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key <KEY_HEX_OR_ASCII> --batch
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py   # corpus 재생성
HERO_GAME=h4 python tools/i18n/translate_dialogues.py          # A1 번역
```

근거 자료 (이미 자동 정찰로 확립):
- [tools/recon/diagnose_h4_scn_cipher.py](../../tools/recon/diagnose_h4_scn_cipher.py): SCN 350개 — 99% 8-byte aligned, 엔트로피 7.9962, 첫 cipher block 22% sharing → ECB DES 강력 시사
- [work/h4/extracted/DAT/_DAT_DES](../../work/h4/extracted/DAT/_DAT_DES) (824 bytes) = 표준 DES 테이블 (PC-1, E-box, P-box, S1) 1:1 매칭 검증 완료. 추가 검증: 마지막 64 byte 도 표준 P-box / IP-Inv 패턴, **별도 키 첨부 없음**
- [tools/recon/find_h4_des_key.py](../../tools/recon/find_h4_des_key.py) (v1): `.data` ASCII (2,311) + sliding-window (59,556) brute force 모두 키 미발견
- [tools/recon/find_h4_des_key_v2.py](../../tools/recon/find_h4_des_key_v2.py) (v2, 2026-05-14): **전체 binary** (566K 바이트, 511,006 sliding 후보) + `__adf__`/`__class__` descriptor 토큰 (736) + AID 파생 (24) + weak/common keys (14) **모두 검증** — Phase 1 last-block sentinel 매치 0건
- [tools/recon/des_key_extended_hypotheses.py](../../tools/recon/des_key_extended_hypotheses.py): MD5/SHA1 of `/DAT/_DAT_DES` / `J@IWO8N7L0E7E` / `010100D4` / `한빛` 등 + SLvl 숫자 BE/LE + sequential bytes 0x79..0x86 + `JIWONLEE` (J@IWO8N7L0E7E 에서 letter-only 추출) — 모두 매치 0건
- Hero5 의 `KEY4ENCRYPT` (`ff 00 00 00 0a 33 22 3c …`) 패턴 Hero4 binary 에 NOT FOUND → Hero4 별도 키

### 🔑 known-ciphertext leverage (Ghidra 키 발견 시 즉시 검증용)

ECB 100% 확정 근거 + 강한 known-plaintext crib (2026-05-14):

| ciphertext (hex) | 출현 위치 | 빈도 | 추정 plaintext |
|---|---|---|---|
| `3b7af9a427907dac` | SCN **마지막** 8 byte | **38 / 350** | EOS sentinel / 공통 종단 opcode |
| `1b7559e5bcf49488` | SCN 마지막 8 byte | 13 / 350 | (다른) 종단 패턴 |
| `ef9c94a1d8247276` | SCN 마지막 8 byte | 12 / 350 | (다른) 종단 패턴 |
| `c0f2daf72c2210e1` | SCN 마지막 8 byte | 11 / 350 | (다른) 종단 패턴 |
| `4655b8f39c0fe0b2` | SCN **첫** 8 byte | 8 / 350 | 공통 헤더 |
| `38d18f6ac1c49c07` | SCN 첫 8 byte | 7 / 350 | 공통 헤더 |
| `0206740aa7b9edea` | SCN 첫 8 byte | 6 / 350 | 공통 헤더 |

**Ghidra 에서 키 후보 발견 시 1차 검증 방법**:
```python
from Crypto.Cipher import DES
key = bytes.fromhex('<KEY_HEX>')  # 또는 ASCII
c = DES.new(key, DES.MODE_ECB)
# 가장 흔한 last block 복호화 — sentinel/low-entropy plaintext 면 키 정답
print(c.decrypt(bytes.fromhex('3b7af9a427907dac')).hex())
# 가장 흔한 first block 복호화 — Hero3 SCN signature `00 00 00 ff ff ff ...` 가설 검증
print(c.decrypt(bytes.fromhex('4655b8f39c0fe0b2')).hex())
```
38회 반복은 CBC 모드에서는 거의 불가능 (per-file IV 라면 마지막 cipher block 도 거의 unique). ECB 단정.

**키 발견 시 100% 최종 검증**: `tools/converter/decrypt_h4_scn.py --key <KEY> --batch` 후 첫 SCN 의 처음 16 byte 가 의미 있는 패턴이거나 (Hero3 처럼 `00 00 00 ff ff ff …`), EUC-KR 한글 (0xa1-0xfe) 시퀀스가 나타나면 성공.

**부수 작업 (Ghidra 진입 후 같이)**: `_PAL` secondary RGB 의미, `_EXD` payload struct, `_MAP_M_` extras 영역 — 모두 string xref 기반.

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
- ⚠️ `work/h4/converted/dialogue_corpus.json` — 4,078 라인이지만 **DES 미복호화 → garbage**. apps/hero4-android assets 에도 garbage 사본 존재. **DES key 발견 후 재생성 필요**
- ✅ `work/h4/converted/asset_catalog.json` — 97 maps + 30 sprite dirs
- ✅ `tools/i18n/translation_dict.py` — game-aware (CHARACTERS_H3/H4, PLACES_H3/H4, `for_game(id)`). Hero4 zone 12개 prefill (켈트 4 보물 도시 + 한국어 zone)
- ✅ `tools/converter/decrypt_h4_scn.py` — DES 키 받아 SCN decrypt (단일/일괄, ECB/CBC). 키 발견 후 즉시 사용
- ✅ `tools/recon/find_h4_des_key.py` — DES brute-force (ASCII/sliding-window). 결과: 키는 binary 안 단순 8-byte 아님
- ✅ `tools/recon/diagnose_h4_scn_cipher.py` — SCN 통계 진단 (size/entropy/ECB hypothesis)

### 핵심 발견

- ⭐ **Hero4 SCN = 표준 DES (ECB 거의 확실) 암호화** — `_DAT_DES` 가 표준 DES 테이블 그대로 (2026-05-07 후속). **키 미발견** → Phase B 1순위
- ⭐ **0x0c BM = 8-bit dense palette indexed** (Ghidra `FUN_00010fe4` 분석). Hero3 미해독 91 BM (theme 47 + obj 44) 도 동시 unblocking
- **_PAL** 8byte/color (Hero3 4byte 의 2배) — primary + secondary RGB 페어
- **_MAP_M_** 헤더 버전 일반화: `0xff` separator 개수 = v, `nlen` offset = `2v+1`
- **_MAP_M_** post-NUL body = Hero3 `_mp` 100% 동일 layout
- Hero4 zone 이름 = **켈트 신화 Tuatha Dé Danann** 패러디 (뮤리아스/핀디아스/팔리아스/고리아스)
- Hero3+Hero4 = **같은 한빛 내부 엔진의 진화형** (`'frameBuf is NULL'` 동일 에러). 단 Hero4 는 SCN 암호화 추가
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
│   ├── decrypt_h4_scn.py         ← ★ Hero4 SCN DES decrypt (키 발견 후 사용)
│   └── ... (Hero3 와 공유)
├── recon/                        ← `HERO_GAME` env 로 게임 선택
│   ├── find_h4_des_key.py        ← DES brute-force (한계 도달, 결과 PROGRESS 참조)
│   ├── diagnose_h4_scn_cipher.py ← SCN 통계 진단
│   └── ... (extract_strings, find_xrefs 등 game-aware)
└── i18n/                         ← `HERO_GAME` env 로 게임 선택
    ├── translation_dict.py       ← game-aware 사전 (for_game/all_translations)
    └── translate_dialogues.py    ← Claude Haiku 번역 (--dry-run 으로 prompt 검증)
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

# DES 진단 / brute force (이미 한계 도달, 참고용)
python tools/recon/diagnose_h4_scn_cipher.py          # SCN 350 통계 (entropy/ECB hint)
python tools/recon/find_h4_des_key.py --source ascii   # ASCII 8-byte 후보 brute force (~수 초)
python tools/recon/find_h4_des_key.py --source all     # sliding-window 전체 (~10초)
```

### DES key 발견 후 자동 파이프라인

```bash
# (Phase B 에서 8-byte 키 발견 가정)
HERO_GAME=h4 python tools/converter/decrypt_h4_scn.py --key <KEY> --batch
#   → work/h4/decrypted/SC/*_scn 350 file 생성

# 그 다음 SCN parser 가 decrypted 디렉토리 읽도록 수정 필요 (현재 convert_all.py 는 extracted 만 봄)
# 임시: cp work/h4/decrypted/SC/*_scn work/h4/extracted/MAP/SC/  (백업 후)
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted
HERO_GAME=h4 python tools/converter/build_dialogue_corpus.py
HERO_GAME=h4 python tools/i18n/translate_dialogues.py
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

- ⛔ **NEW Hero4 SCN = DES 암호화** (2026-05-07 후속 발견) — 350 SCN + 4,078 대사 corpus 가 모두 garbage. ECB DES 거의 확실 (entropy 7.9962, 첫 cipher block 22% sharing, 99% 8-byte aligned). 자동 brute-force 한계 → **Phase B 1순위**. Diagnostic / brute-force 도구는 위 §🚨 참조
- ⛔ **A1 (대사 영어 번역)** — DES key 발굴 후 corpus 재생성 가능해야 의미 있음. `translation_dict.py` / `translate_dialogues.py` 는 Hero4 game-aware 로 이미 준비됨
- ~~**`_TILE_030`**~~ ✅ **풀림 (2026-05-07)**: 컨테이너 prefix `01 00 00 00 <size LE32>` 감지 → inner BM 으로 재진입. [convert_h4_tile.py](../../tools/converter/convert_h4_tile.py) 에 반영. h4_tile=276→**277**, skipped=564→563
- **work/h3/ghidra_proj/*.lock** — Hero3 Ghidra 프로젝트 락이 걸려있어 work/h3/ 일부 이동 못 함. Ghidra 닫고 락 정리 필요
- ~~**`tools/recon/find_xrefs.py`, `find_pic_xrefs.py`, `find_base.py`** — hardcoded TARGETS~~ ✅ **풀림 (2026-05-07)**: [extract_strings.py](../../tools/recon/extract_strings.py) `--json` 옵션 + [_targets.py](../../tools/recon/_targets.py) 헬퍼 도입. 3 스크립트 모두 game-aware. h3/h4 양쪽 검증
- **`_PAL` secondary RGB 의미** — 미확정. 가장 유력한 가설은 alpha mask. Phase B 에서 확정
- **_EXD payload, _MAP_M_ extras, HDAT entry layout** — 모두 Phase B 후 확정
- **Hero4 binary 의 string xref 추적** — h3 와 다른 addressing (PIC LDR+ADD T1 인접 패턴 거의 없음). Phase B Ghidra GUI 에서는 32-bit LDR.W (T4) 또는 다른 sequence 추적 필요
- **2 misaligned SCN** — `e0184_scn` (30B), `e0185_scn` (6313B+1) 8-byte 정렬 안 됨. outlier, DES 적용 시 별도 처리 필요할 수도

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

4. **자동 brute-force 시도 + diagnostic** (Phase B 진입 전 자동 가능 영역 한계 도달)
   - [tools/converter/decrypt_h4_scn.py](../../tools/converter/decrypt_h4_scn.py) 신규 — DES 키 받아 SCN decrypt (단일/일괄, ECB/CBC). 키 발견 즉시 사용 가능
   - [tools/recon/find_h4_des_key.py](../../tools/recon/find_h4_des_key.py) 신규 — binary `.data` 영역 (start=0x77000) 의 ASCII / sliding-window 8-byte 후보를 brute force. Hero3 SCN signature `00 00 00 ff ff ff` 매칭 시 score+200
     - ASCII 후보 (2,311개): max score 81 (BASIC_SM 등 binary 안 부분문자열). 진짜 키 신호 없음
     - sliding-window 전체 (59,556개): max score 87. 여전히 signature 매칭 0건
     - **결론**: ECB 라면 키는 binary 안 단순 8-byte 가 아니거나, plaintext format 이 Hero3 SCN 과 달라 scoring 가정 자체가 빗나감
   - [tools/recon/diagnose_h4_scn_cipher.py](../../tools/recon/diagnose_h4_scn_cipher.py) 신규 — 350 SCN 통계 진단:
     - **99% (348/350) 가 8-byte aligned** → DES 호환 ✓
     - **Shannon entropy 7.9962 bits/byte** (uniform random 8.0) → 강한 암호 (DES/AES) 또는 compressed. XOR 류 약한 obfuscation 배제
     - **반복 cipher block 1~5%** + **첫 cipher block 22% sharing** (273/350 unique) → **ECB DES 강력 시사** (CBC 면 per-file IV 로 거의 100% unique 나와야)
     - Hero5 의 `KEY4ENCRYPT` (`ff 00 00 00 0a 33 22 3c …`) 패턴 검색 → Hero4 binary 에 NOT FOUND. 별개 키
     - misaligned 2개 (e0184_scn=30B, e0185_scn=6313B+1) — outlier, 별도 처리 필요할 수도

다음 작업: **Phase B (Ghidra GUI) — 사용자 환경 작업 필수**. 자동 정찰의 한계는 명확.
1순위: `/DAT/_DAT_DES` (string @ 0x86ecc) xref 추적 → SCN decrypt 진입점 함수 → 그 함수 호출자에서 키 source (literal 8 bytes 또는 키 파생 input)
키 발견 후: `python tools/converter/decrypt_h4_scn.py --key <KEY> --batch` 한 번이면 350 파일 즉시 복호화 → corpus 재생성 → A1 진행 가능.

---

## 📜 세션 (2026-05-14) — DES brute-force v2 + known-ciphertext leverage 확립

자동 영역 추가 시도 (Phase B Ghidra 진입 전 마지막 자동 탐색). 결론: **자동 brute-force 완전 한계 확정**.

1. **SCN ciphertext 정밀 통계** — ECB 모드 100% 단정
   - 마지막 8-byte ciphertext `3b7af9a427907dac` 가 **38 / 350 SCN 에서 반복** (11%)
   - 마지막 8-byte 가 13+회 반복되는 패턴이 최소 3종 (`1b7559e5bcf49488` ×13, `ef9c94a1d8247276` ×12, `c0f2daf72c2210e1` ×11)
   - 첫 8-byte 도 `4655b8f39c0fe0b2` ×8, `38d18f6ac1c49c07` ×7 등 반복
   - CBC 라면 per-file IV 로 거의 100% unique 해야 함 — **ECB 단정**, 38회 반복 last block 은 공통 평문 종단 (sentinel / EOS opcode) 의 강한 known-ciphertext crib

2. **확장 brute-force 도구화** ([tools/recon/find_h4_des_key_v2.py](../../tools/recon/find_h4_des_key_v2.py))
   - v1 한계 (`.data` start=0x77000 만) 해소 → **전체 binary** (start=0, 566K 바이트, 511,006 sliding-window 후보)
   - 추가 후보 소스: `__adf__` / `__class__` SKT descriptor ASCII tokens (736), AID 파생 (24), weak/common DES keys (14)
   - 검증 전략: 가장 흔한 last-block (`3b7af9a427907dac`) decrypt → plaintext 가 sentinel 패턴이면 통과
   - 결과: **Phase 1 survivors 0** (sentinel/low-entropy 가설 모두 미통과)

3. **확장 가설 별도 검증** ([tools/recon/des_key_extended_hypotheses.py](../../tools/recon/des_key_extended_hypotheses.py))
   - MD5/SHA1 of `/DAT/_DAT_DES`, `_DAT_DES`, `DES`, `J@IWO8N7L0E7E`, `010100D4`, `한빛` (UTF-8/EUC-KR) 등 → 0 match
   - `__adf__` 의 SLvl/SLvl2/FSize/Timestamp 를 BE/LE 8-byte → 0 match
   - sequential bytes 0x79..0x86 (binary `_DAT_DES` 근처 ascending pattern) → 0 match
   - `JIWONLEE` (J@IWO8N7L0E7E 에서 letter-only 추출 = "Lee Ji-won" 패턴, 매우 유망 가설) → 0 match
   - `JIWONLEE` reversed / lowercase / 8-byte sliding 변형 → 0 match

4. **`_DAT_DES` 파일 자체 검증**
   - 824 byte 전체가 표준 DES 알고리즘 테이블만 (시작: PC-1 `3a 32 2a 22 1a 12 0a 02` = bit 58,50,42,34,26,18,10,2 ✓)
   - 마지막 64 byte 도 표준 P-box / IP-Inv 패턴 — **별도 key 첨부 없음**

5. **🔍 새 단서 — `J@IWO8N7L0E7E` @0x86edc**
   - `_DAT_DES` 문자열 (@0x86ecc) 바로 다음 위치에 의문의 13-char ASCII null-term 문자열
   - hex: `4a 40 49 57 4f 38 4e 37 4c 30 45 37 45 00 00 00`
   - letter-only 추출 = `JIWONLEE` (8 chars, "Lee Ji-won" 한국 이름 패턴) — 키 직접 매치는 실패했지만 Ghidra 에서 xref 추적 필수
   - 가능성: (a) 스크램블된 키 (XOR/permutation), (b) 다른 자원 식별자, (c) 개발자 서명 string

6. **자동 영역 완전 종결 — 다음 진입은 Ghidra 1순위**
   - 위 known-ciphertext (`3b7af9a427907dac`, `4655b8f39c0fe0b2`) 는 Ghidra 에서 키 발견 시 단발 검증용으로 즉시 사용 가능 — `decrypt_h4_scn.py` 돌리기 전에 `Crypto.Cipher.DES` 로 1초 검증
   - 추적 대상 strings (Ghidra xref): `/DAT/_DAT_DES` @0x86ecc, `J@IWO8N7L0E7E` @0x86edc, `_DAT_DES` @0x86ed1
