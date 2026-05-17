# Hero4 Remake — 진행 상황 & 핸드오프

> 다음 세션에서 가장 먼저 읽기. 디테일은 분류별 폴더 / 파일 참조.

## ⚡ 다음 세션 — 시작 전 30초 체크

> **최신 상태 (2026-05-18)**: Hero4 자동 영역에서 **누적 16건 진전** 끝. **DES key 자체** 만 차단 (Phase B Ghidra 의존). 키 발견 시 단일 명령으로 **SCN 348 + HDAT Group A 8 = 356 파일 동시 복호화** + corpus 재생성 + A1 번역 자동.

### 🎯 다음 세션 진입 가이드 (4-way)

```
□ 1. 사용자가 DES key 후보 8 byte 를 제시?
    YES → §⚡ 자동 파이프라인 (1초 검증 + batch decrypt + corpus + A1) — 30분
    NO  → ↓

□ 2. 사용자가 Ghidra GUI 준비 완료?
    YES → ghidra-guide.md §5.1 + §"DES key 추적 string 3개" 안내
    NO  → ↓

□ 3. 사용자가 Phase C/D 결정 (KMM/iOS) 알림?
    YES → docs/h3/PROGRESS.md + Phase C 1단계 (git tag v0.1-pre-kmm)
    NO  → ↓

□ 4. 자동 진행 가능 영역 잔여?
    → 거의 없음. 16개 자동 영역 모두 종결.
    → 사용자 결정 대기 (Hero3 잔여 / Hero5 트랙으로 전환 권장)
```

### 16개 자동 진전 요약 (2026-05-18 세션 누적)

| # | 발견 | 도구/문서 |
|---|---|---|
| 1 | plaintext SCN 2개 (e0184/e0185) | misaligned outlier 정밀 분석 |
| 2 | e0185 글로벌 entity catalog (87 strings) | `work/h4/converted/e0185_name_table.json` |
| 3 | `CHARACTERS_H4` 사전 prefill (52 entries) | [translation_dict.py](../../tools/i18n/translation_dict.py) |
| 4 | SCN known-plaintext signature `01 ?? 01 53 00 01 ?? ??` | 5 byte fixed = 40 known bits |
| 5 | `_DAT_DES` S1[58] 1-byte 변형 (`std=3 → got=2`) | [verify_h4_dat_des.py](../../tools/recon/verify_h4_dat_des.py) |
| 6 | Custom DES 구현 (pure Python) | [custom_des_h4.py](../../tools/converter/custom_des_h4.py) |
| 7 | DES brute-force v3 (Hero4 signature) | [find_h4_des_key_v3.py](../../tools/recon/find_h4_des_key_v3.py) — 0 hit |
| 8 | DES brute-force v4 (custom DES, 513k cand) | [find_h4_des_key_v4.py](../../tools/recon/find_h4_des_key_v4.py) — 0 hit |
| 9 | `_PAL` secondary RGB 통계 (alpha 가설 기각) | [analyze_h4_pal.py](../../tools/recon/analyze_h4_pal.py) |
| 10 | `_EXD` box layout (count=1 subtype 2/3 풀림) | [parse_h4_exd.py](../../tools/converter/parse_h4_exd.py) |
| 11 | `_MAP_M_` extras multi-section (4-8 sections × 8B records) | [parse_h4_map_extras.py](../../tools/converter/parse_h4_map_extras.py) |
| 12 | SCN second-block crib `f7740f758b9a6ae4` (×17) | known-ciphertext 추가 |
| 13 | HDAT Group B (P000-P005) layout 풀림 | [parse_h4_hdat_p.py](../../tools/converter/parse_h4_hdat_p.py) |
| 14 | e0184 SCN bytecode 구조 추론 | [scn.md](formats/scn.md) |
| 15 | **HDAT Group A 8 파일 = SCN 동일 DES 키** | sentinel 92회 cross-ref |
| 16 | HDAT Group D (PDAT/SG) + OBJ 그룹 분포 | [hdat.md §Group D](formats/hdat.md), [bm-tile-obj.md §OBJ 분포](formats/bm-tile-obj.md) |

### 핸드오프 Q&A

| 질문 | 답 위치 |
|---|---|
| 이번 세션에 뭐 했나 | 이 문서 §"세션 (2026-05-18)" 4개 후속 섹션 |
| **지금 1순위 차단 이슈** | **DES key 8 bytes (Phase B Ghidra 필수)** — §🚨 핵심 차단 |
| **"영웅서기4 다음 작업 진행" 시 어디부터?** | 위 §🎯 4-way 셀렉터 → [`next-steps.md`](next-steps.md#-영웅서기4-이어서-진행해줘-라고-했을-때--빠른-셀렉터) |
| 사용자가 DES key 가져오면? | 1초 검증 → `decrypt_h4_scn.py --key <K> --batch` → 자동 파이프라인 |
| **DES key 발견 시 한번에 복호화되는 파일** | **SCN 348 + HDAT Group A 8 = 356 파일** (key 1개로) |
| 자산 포맷 분석 디테일 | [`formats/`](formats/) (6 문서: pal/map/exd/bm-tile-obj/hdat/scn) |
| Ghidra GUI 분석 가이드 | [`ghidra-guide.md`](ghidra-guide.md) §5.1 DES key 발굴 절차 |
| **앞으로 뭐 해야 하나** | [`next-steps.md`](next-steps.md) — 4-way 셀렉터로 분기 |
| **DES key 후보 위치 (Ghidra 추적용)** | `/DAT/_DAT_DES` @0x86ecc, `J@IWO8N7L0E7E` @0x86edc, `_DAT_DES` @0x86ed1 |
| **자동 brute-force 진행 결과** | v1/v2/v3/v4 모두 0 hit. 키는 binary literal 아님 100% 확정 (scramble/derive/외부 셋 중 하나) |
| **번역 사전 H4 갯수** | CHARACTERS_H4=52, PLACES_H4=12, total H4 bundle 271 (Hero3 250 기준) |
| 프로젝트 전체 (Hero3 포함) 컨텍스트 | [`../../Readme.md`](../../Readme.md) |

---

## 🚨 핵심 차단 — DES key (다음 세션 1순위)

Hero4 SCN 348개 (350 중 2개는 plaintext) = **DES ECB 로 암호화** (2026-05-14 100% 확정). 단, **2026-05-18 추가 발견**: `_DAT_DES` 의 S1[58] 1 byte 가 표준 DES 와 다름 (`std=3 → got=2`). 의도적 변형이라면 표준 `Crypto.Cipher.DES` 로는 영원히 풀리지 않고, Ghidra 키 발견 후에도 **custom DES 구현** ([tools/converter/custom_des_h4.py](../../tools/converter/custom_des_h4.py)) 사용 필수. 자동 brute-force 완전 한계 → Ghidra GUI 작업 필수.

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

**더 강한 검증 (2026-05-18 발견)** — Hero4 SCN known-plaintext signature:

| plaintext SCN | first 8 byte | 추론 가능 signature |
|---|---|---|
| `e0184_scn` (30B, misaligned) | `01 00 01 53 00 01 a1 ff` | `01 ?? 01 53 00 01 ?? ??` |
| `e0185_scn` (6313B+1, misaligned) | `01 02 01 53 00 01 c8 ff` | `01 ?? 01 53 00 01 ?? ??` |

5 byte (= 40 known bits) fixed signature. 키 검증 시:
```python
import sys; sys.path.insert(0, 'tools')
from converter.custom_des_h4 import decrypt as h4_decrypt
key = bytes.fromhex('<KEY_HEX>')
# 가장 흔한 first cipher block (8/348)
p = h4_decrypt(key, bytes.fromhex('4655b8f39c0fe0b2'))
assert p[0]==0x01 and p[2]==0x01 and p[3]==0x53 and p[4]==0x00 and p[5]==0x01, '키 오답'
```
Standard `Crypto.Cipher.DES` 와 custom (S1[58]=2) 둘 다 시도 권장.

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
   - ⚠ **2026-05-18 재검증**: 첫 64 byte 는 PC-1 이 아니라 **IP (Initial Permutation)** 임을 확인. 정확한 layout:
     IP(64) + IP-Inv(64) + E(48) + P(32) + S1(64) + S2(64) + ... + S8(64) + PC-1(56) + PC-2(48) = 824
     824 byte 중 **823 byte 가 표준 DES 와 정확히 일치, 1 byte 만 다름** (S1[58]).

5. **🔍 새 단서 — `J@IWO8N7L0E7E` @0x86edc**
   - `_DAT_DES` 문자열 (@0x86ecc) 바로 다음 위치에 의문의 13-char ASCII null-term 문자열
   - hex: `4a 40 49 57 4f 38 4e 37 4c 30 45 37 45 00 00 00`
   - letter-only 추출 = `JIWONLEE` (8 chars, "Lee Ji-won" 한국 이름 패턴) — 키 직접 매치는 실패했지만 Ghidra 에서 xref 추적 필수
   - 가능성: (a) 스크램블된 키 (XOR/permutation), (b) 다른 자원 식별자, (c) 개발자 서명 string

6. **자동 영역 완전 종결 — 다음 진입은 Ghidra 1순위**
   - 위 known-ciphertext (`3b7af9a427907dac`, `4655b8f39c0fe0b2`) 는 Ghidra 에서 키 발견 시 단발 검증용으로 즉시 사용 가능 — `decrypt_h4_scn.py` 돌리기 전에 `Crypto.Cipher.DES` 로 1초 검증
   - 추적 대상 strings (Ghidra xref): `/DAT/_DAT_DES` @0x86ecc, `J@IWO8N7L0E7E` @0x86edc, `_DAT_DES` @0x86ed1

---

## 📜 세션 (2026-05-18) — plaintext SCN 발견 + custom DES 가설 + PAL 통계

자동 영역 추가 발견 — 2026-05-14 의 "자동 영역 완전 종결" 선언을 **재검토**. 4개 신규 발견:

1. **🌟 plaintext SCN 2개 발견** — e0184_scn (30B) / e0185_scn (6313B) misaligned outlier 가 실은 **DES 처리 안 된 raw plaintext** 였음을 확인
   - e0184: `01 00 01 53 00 01 a1 ff …` + ASCII "VALUE" 문자열. 짧은 metadata SCN
   - e0185: `01 02 01 53 00 01 c8 ff …` + 끝부분에 EUC-KR 한글 풀 풀 풀 (`b9ab b1e2 …`)
   - 공통 헤더 signature: **`01 ?? 01 53 00 01 ?? ??`** (5 byte fixed = 40 known bits, DES known-plaintext attack 의 강한 crib)
   - 348 encrypted SCN 중 어느 것도 plaintext signature 와 match 안 됨 (이미 빈 sample, 자명)

2. **🌟 e0185_scn = Hero4 글로벌 entity catalog** — 87 null-terminated 문자열, 게임 전체 NPC/객체 이름 정의
   - 추출 결과: `work/h4/converted/e0185_name_table.json` (offset + text)
   - 켈트 신화 인물 33+: 앨리스(Alice), 브리안(Brian), 디어드리(Deirdre), 노덴스(Nodens), 누아다(Nuada), 티르(Tyr), 브레스(Bres), 케프네스(Kephness) — Tuatha Dé Danann 패러디 확정
   - 일반 명사: 인간/선주/꼬마/병사/대장장이/연금술사/소환술사 등 직업 19개
   - 게임 상태: 출구/결계/블라인드/대미지/넉백/이벤트 등 transition 라벨
   - **CHARACTERS_H4 사전 prefill 완료** (52 entries) — [translation_dict.py](../../tools/i18n/translation_dict.py). h4 system prompt 길이 2,689 chars

3. **🌟 `_DAT_DES` S1 1-byte 변형 발견 — Hero4 custom DES 가설**
   - 정확한 layout 분석: IP(64) + IP-Inv(64) + E(48) + P(32) + 8×S(512) + PC-1(56) + PC-2(48) = 824B
   - 823 byte 표준 DES 와 정확 일치. **단 1 byte 차이**: S1[58] (= S1 row 3, col 10) `std=3, _DAT_DES=2` @ file offset 0x010a
   - 단일 비트 차이 (3 = 0b011, 2 = 0b010, bit 0 toggle). 단순 typo 가능성과 의도적 anti-piracy 가능성 모두 존재
   - **함의**: 의도적 변형이라면 `Crypto.Cipher.DES` / `SunJCE` 로는 영원히 복호화 불가
   - 검증 도구: [tools/recon/verify_h4_dat_des.py](../../tools/recon/verify_h4_dat_des.py) — `824 byte: 1 deviation @S1[58]`
   - 구현: [tools/converter/custom_des_h4.py](../../tools/converter/custom_des_h4.py) — pure Python DES with S1[58]=2, roundtrip self-test 통과 (5,876 blocks/s pure python)

4. **v3 + v4 brute-force 종결 재확인** — Hero4-specific signature + custom DES 둘 다 시도, 키 미발견
   - v3 ([find_h4_des_key_v3.py](../../tools/recon/find_h4_des_key_v3.py)): 표준 DES + 5 top first-cipher × Hero4 signature. binary + DAT_DES + plaintext SCN + JAR 자원 (_LOGO/TITLE_BM/tdf/*) 전체 검색. Phase 2 cross-validation 결과 모두 partial 만, perfect 0건
   - v4 ([find_h4_des_key_v4.py](../../tools/recon/find_h4_des_key_v4.py)): custom DES (S1[58]=2) + 513,941 candidates × 5 ciphers, ~7 분. 백그라운드 실행 결과 동일 — 키는 8-byte literal 로 어디에도 없음
   - 두 결과 모두 0 → **키는 binary 안 8-byte literal 이 아님** (scrambled / derived / 별도 위치)

5. **🌟 `_PAL` secondary RGB 통계 분석** — A1/A2 = 0 padding, identical 0%, scale-darken 만 11%
   - 196 PAL 파일 5,724 entries 분석. 포맷 재확정: `u8 count + N×8B entries`, 8B entry = `R1 G1 B1 A1 R2 G2 B2 A2`
   - **A1 / A2 (byte 3, 7) = 모두 0** (5724/5724) → 이전 가설 "alpha mask" 기각. 순수 padding
   - **primary == secondary 인 entry: 0건** → palette swap 가설도 부분 기각 (identical 이 0% 이면 always 다른 색)
   - 관계 분포: independent 37.3% / darker_no_scale 34.6% / lighter_no_scale 12.9% / scaled_near1 9.2% / scaled_darker 5.8% / scaled_lighter 0.2%
   - "scale-darken (uniform shadow)" 가설은 6% 뿐. **두 separate color slot** (color cycling / two-tone / animation frame / display profile variant) 가 더 유력
   - 도구: [tools/recon/analyze_h4_pal.py](../../tools/recon/analyze_h4_pal.py), 결과 JSON: `work/h4/converted/pal_secondary_stats.json`

요약: 자동 영역에서 **DES key 추가 발굴은 여전히 불가** 이나, **CHARACTERS_H4 사전 + plaintext signature crib + custom DES 구현 + PAL 의미 후보 좁힘** 의 4 가지 누적 진전. Phase B 진입 시 검증 도구가 한 단계 더 강해짐.

---

## 📜 세션 (2026-05-18 후속) — _EXD 파싱 + _MAP_M_ extras multi-section 구조

위 5건 발견 후 추가 진전 3건:

7. **🌟 v4 brute-force 결과 확정 (백그라운드 438s)** — custom DES (S1[58]=2) + 513,941 후보 × 5 cipher = 모두 시도, **0 survivors**. 키는 binary literal 아님 100% 확정 (v3 표준 DES + v4 custom DES 양쪽 fail).

8. **🌟 _EXD payload struct 풀림 (count=1 케이스)** — 117 캐릭터 데이터 파싱
   - count=1, subtype=2 (14 files): 12B entry = 4B head (`00 ?? ff 01`) + 1×8B box (LE int16 dx,dy,w,h)
   - count=1, subtype=3 (26 files): 21B entry = 4B head + box1(8) + sep_byte(0x02) + box2(8)
     - box1 = 캐릭터 발/충돌 영역 (dx~-8, dy~-5, w~14, h~9)
     - box2 = sprite render bounds (dx~-7, dy~-24, w~12, h~25 vertical)
   - count=1, subtype=1 (5 files): 가변 (2/3/7 byte), 미정
   - count>1 (72 files): 첫 entry 21B subtype3 + 나머지 가변 (0x03 box separator 있음)
   - 파서: [tools/converter/parse_h4_exd.py](../../tools/converter/parse_h4_exd.py), JSON: `work/h4/converted/exd_parsed.json`
   - 헤더 check 통과: 112/117

9. **🌟 _MAP_M_ extras 영역 multi-section 구조 풀림** — 97 맵 파일 부분 파싱
   - extras = **N개 section, 각 section = `1B count + N × 8B records`**
   - 8B record layout: `type(1B) + sub_data(3B) + x(LE uint16) + y(LE uint16)`
   - section 수 분포: 4 sections (28 files) / 5 (48) / 6 (15) / 7 (4) / 8 (2)
   - **13/97 파일 완전 소비** (no tail), 84/97 1~40B trailing (variable-length tail section)
   - 모든 파일이 first 4 sections 까지 정상 파싱 → 핵심 layout 확정
   - section 별 의미 추정: sec0=tile/NPC spawn (대량), sec1+=exit/event/trigger (소량) — Ghidra 명명 필요
   - 파서: [tools/converter/parse_h4_map_extras.py](../../tools/converter/parse_h4_map_extras.py), JSON: `work/h4/converted/map_extras_parsed.json`
   - 샘플 `_MAP_M_000` (수레바퀴섬/선착장): 4 sections × (55/26/24/0 records), tail 6B

10. **encrypted SCN second cipher block crib 추가** — `f7740f758b9a6ae4` 가 17/348 회 반복 (이전 last-block 38회, first-block 8회 외에 새로운 3번째 known-ciphertext)
    - Ghidra 에서 키 검증 시 추가 cross-validation 사용 가능
    - `c.decrypt(bytes.fromhex('f7740f758b9a6ae4'))` 도 추가 plaintext signature check

요약 update: Phase B 진입 전 자동 작업이 **추가 3 단계** 진전 — _EXD 파서 + _MAP_M_ extras 파서 + DES 다중 cipher crib. 콘텐츠 wiring (Phase C/D) 단계에서 NPC/exit/event 데이터가 즉시 사용 가능.

---

## 📜 세션 (2026-05-18 후속2) — HDAT Group B layout + e0184 SCN bytecode 분해

추가 자동 발견 2건:

11. **🌟 HDAT Group B (P000-P005) layout 풀림** — 6 파일 progression/cost table
    - **`3B header + N × 50B entries`** 일관된 layout (P000=1ent, P001-3=2ent, P004=3ent, P005=2ent)
    - Entry 50B = **8 × uint16 LE main values** + 1B marker (0xff/0x00) + 5B param block + 28B nested tail u16s
    - main values 패턴: `[level/rank, hp/cost, 0, stat2, 0, gold/EXP, atk, hp_max]`
    - P004 entry[0] outlier: marker=0x00 + val[5]=20000 (boss/special tier?)
    - 파서: [tools/converter/parse_h4_hdat_p.py](../../tools/converter/parse_h4_hdat_p.py), JSON: `work/h4/converted/hdat_p_parsed.json`

12. **🌟 e0184_scn (30B plaintext) 완전 분해 + SCN bytecode 구조 추론**
    - 12B 헤더 signature `01 ?? 01 53 00 01 ?? ?? ff ff ff ff ff` (변수 byte 2개, 나머지 10 byte 고정)
    - 본문 영역: record-based bytecode (opcode + length + body)
      - opcode 0x01: string entry (length-prefixed + null-terminated)
      - opcode 0x0c: small immediate value
      - 0xff: record separator
    - e0184/e0185 의 **bytes 15-20 동일** (`00 00 ff 0c 00 ff`) — sub-header marker
    - 새 문서: [docs/h4/formats/scn.md](formats/scn.md)
    - 함의: DES key 발견 시 348 encrypted SCN 도 같은 구조 파서로 즉시 복원 가능
    - DES key 검증 시 best signature: 첫 8 byte decrypt 결과가 `01 ?? 01 53 00 01 ?? ??` 매칭 (40 known bits)

이번 누적 발견 (총 12 항목): plaintext SCN 2개 + CHARACTERS_H4 prefill + SCN signature + custom DES (S1[58]=2) + v3/v4 brute-force (모두 0건) + PAL 통계 + _EXD box layout + _MAP_M_ multi-section + SCN 2nd-block crib + **HDAT Group B layout + e0184 bytecode 구조**.

---

## 📜 세션 (2026-05-18 후속3) — HDAT Group A 암호화 키 공유 확인 + Group D 풀림 + OBJ 그룹 분포

추가 발견 4건:

13. **🚨 HDAT Group A 8 파일도 SCN 과 동일 DES 키로 암호화 — 확정**
    - 모두 8-byte aligned (entropy 6.3~7.8)
    - **SCN sentinel block `3b7af9a427907dac` (38회 SCN) 가 Group A 에서도 92회 반복**:
      - `_H_SA` 37회 (마지막 8 byte 가 이 sentinel), `_H_SS` 23회, `_H_S001` 9회, `_H_S003` 8회, `_H_S000` 7회, `_H_S002` 5회, `_H_BS` 3회
    - `_H_S000` ↔ `_H_S002` 9 shared blocks (첫 16 byte 동일 + ECB pattern) → 같은 plaintext 변형
    - **함의**: DES key 1개 발견 시 SCN 348 + HDAT Group A 8 = **356 파일 한 번에 복호화**
    - 추정 의미: `_H_BH`=Boss Hero, `_H_BS`=Boss Stat, `_H_SA/SS`=Save template A/Special, `_H_S000-S003`=4 save slots

14. **🌟 HDAT Group D (PDAT, SG) layout 풀림**
    - `_H_SG` (170B): **10 슬롯 × 17B** = 12B constant prefix + 5B variable. 5 slots (group "13 13") + 5 slots (group "12 12") — **2 모드 × 5 캐릭터** 가설 (Normal/Hardcore 또는 Story/Free)
    - var bytes 패턴: 8b ff ff ff 8f → 8c..90 → 8d..91 → 8e..92 (4 캐릭터 × CIF id + zone id)
    - `_H_PDAT` (86B): 17 변수 길이 records, 0xff terminated. 첫 record = `0e 00 00 00 00 00` (header), 이후 character/skill/quest/inventory init data
    - [hdat.md](formats/hdat.md) 갱신

15. **🌟 OBJ/{000,001,002}/ 그룹 분포 측정**
    - `OBJ/000/`: 100 파일, **모두 16×16 균일** (small icon / UI)
    - `OBJ/001/`: 100 파일, variable 12~60×13~92 (캐릭터/큰 객체)
    - `OBJ/002/`: 47 파일, variable 8~36×11~35 (아이템/중형)
    - 247 single-frame BM, 게임 내 정확한 매핑은 `_MAP_M_` extras `sub[3]` field 와 cross-reference 후 확정
    - [bm-tile-obj.md](formats/bm-tile-obj.md) §"OBJ 그룹 분포" 추가

16. **e0185 body 통계 (5545B catalog 이전 영역)** — 555개 0xff separator, top byte 분포 `0x00`(1786) / `0x01`(1193) / `0xff`(560) / `0x2e`(498) / `0x07`(485). 복잡한 nested bytecode 구조. opcode 0x2e (= '.') 와 0x07 의 의미는 Ghidra 후 확정.

이번 누적 발견 (총 16 항목): 1~12 + **HDAT Group A 키 공유 확인 + Group D 풀림 + OBJ 그룹 분포 + e0185 body 통계**.

자동 영역에서 남은 미해결 (모두 Phase B Ghidra 의존): _MAP_M_ section 별 명명 (NPC vs exit vs event), _EXD count>1 entry 2+ 구조, e0184/e0185 byte 12+ opcode 정확한 의미, HDAT Group A 의 평문 구조 (DES key 후), OBJ id ↔ 게임 객체 매핑.
