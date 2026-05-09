# Hero3 자산 포맷 분석

원본 JAR: `Hero3/0103EFD4.jar` → `client.bin64000` (ARM Thumb 네이티브, 735KB) + 약 1,471개 자산 파일.

플랫폼: SK Telecom **GVM/Clet** (한국 피처폰 전용, ≠ J2ME/MIDP).

## 자산 인벤토리

| 확장자 | 개수 | 크기 범위 | 정체 | 분석 상태 |
|---|---:|---|---|---|
| `_bm` | 479 | 88B – 139KB | 비트맵/스프라이트 (4-bit 인덱스 추정) | ⚠️ 헤더 OK, 픽셀 레이아웃 미확정 |
| `_cif` | 103 | 5B – 52KB | 캐릭터/애니메이션 정보 | ⚠️ 헤더 OK, 페이로드 미해독 |
| `_dat` | 45 | 72B – 7KB | 게임 데이터 테이블 | ✅ 레코드 구조 확정 |
| `_mf` | 33 | 931B – 15KB | 사운드 (Yamaha SMAF/MMF) | ✅ 표준 포맷 |
| `_mp` | 135 | 544B – 5KB | 맵/타일맵 | ✅ 헤더 OK |
| `_pa` | 216 | 13 – 133B | 팔레트 (RGBA8888) | ✅ 완전 해독 |
| `_scn` | 244 | 69B – 14KB | 이벤트 스크립트 (바이트코드) | ❌ 디스어셈블러 필요 |
| `_txt` | 9 | 32 – 4KB | 문자열 테이블 (EUC-KR) | ✅ 완전 해독 |
| (기타) | 7 | – | client.bin64000 등 바이너리 | – |

## 포맷 상세

### `_txt` (문자열 테이블) — ✅ 완전 해독

```
struct TextTable {
    uint16_t  file_size;           // LE, 자체 크기
    uint16_t  string_count;
    uint16_t  offsets[count];      // LE, 파일 시작 기준 오프셋
    char      strings[];           // EUC-KR, NUL-terminated 또는 다음 오프셋까지
};
```

`dat/InGame_txt`의 처음 196개 문자열:
```
[ 0] MENU       [ 7] 상태보기
[ 1] STATUS     [ 8] 가방
[ 2] INVENTORY  [ 9] 장비
[ 3] EQUIPMENT  [10] 스킬
[ 4] SKILL      [11] 퀘스트
[ 5] QUEST      [12] 시스템
[ 6] SYSTEM     [13] 세이브
```

> **i18n 보너스**: 영어/한국어 병행 데이터가 이미 들어있음. 인덱스 패턴(0–6 ENG, 7–13 KOR)을 분석하면 추가 언어 확장이 단순 string resource 추가로 끝남.

### `_pa` (팔레트) — ✅ 완전 해독

```
struct Palette {
    uint8_t  count;                // 11–33 (관측치)
    uint32_t colors[count];        // 추정 RGBA8888 또는 BGRA8888
};
```

검증: `len(file) == count * 4 + 1` 모든 샘플에서 성립.

### `_dat` (데이터 테이블) — ✅ 구조 확정

가변 길이 레코드. 일부 파일은 8/12-byte 고정, 다른 파일은 가변. 일반 패턴:

```
struct Record {
    uint8_t  rec_size;             // 본 레코드 데이터 크기
    uint8_t  flags;                // 0x00 또는 type marker
    uint8_t  name_len;             // EUC-KR 바이트 수
    uint8_t  name[name_len];
    uint8_t  payload[rec_size - 2 - name_len];
    // 다음 레코드는 offset += rec_size + 1
};
```

`enemy_dat`에서 추출한 적 이름 일부: `아스크란가드`, `코르버스로그`, `솔티안로그`, `도적`, `리츠`, `케이`, `멜페토`, `아스크란템플러`, `아스크란체이서`.

### `_mf` (사운드) — ✅ Yamaha SMAF (MMF) 표준

매직 `MMMD`로 시작. 청크 구조: `CNTI`, `OPDA`, `MTR`, `ATR` 등.

**Android 변환 전략**: 빌드 타임에 OGG/MP3로 변환 (FOSS 도구: `libsmaf`, `smaf2midi` 등) 후 `MediaPlayer`로 재생. 런타임 SMAF 디코딩은 라이브러리 가용성 문제로 비추천.

### `_mp` (맵) — ✅ 구조 해독 (134/135 파싱 성공)

```
struct MapFile {
    uint8  version;                // 0x02 또는 0x03
    bytes  meta[hdr_size - 1];     // version 0x02 → 4바이트, 0x03 → 5바이트 추가 (의미 미확정 — tile sheet ID 추정)
    uint8  name_length;
    char   name[name_length];      // ASCII (예: "NEOSOLTIA", "RUINED_DESERT_1", "BOSS_TOWN")
    uint8  nul;                    // 0x00
    uint8  width;                  // 1..70 (관측)
    uint8  height;                 // 1..47
    uint8  palette_count;          // 1..16
    uint8  meta4;                  // 의미 미확정
    uint8  palette[palette_count]; // 사용된 tile ID 목록 (전역 tile sheet 인덱스)
    uint8  layer_0[width * height];   // terrain (지형)
    uint8  layer_1[width * height];   // objects/collision
    bytes  extras[];               // events / exits / NPCs (포맷 미확정)
};
```

**확정 사항**:
- 134개 맵 모두 헤더·이름·치수·팔레트 정상 파싱
- 2개의 layer × 1 byte/tile 구조 확인 — Layer 0은 terrain, Layer 1은 collision/objects
- 시각 검증: SECRET_ROOM·BOSS_TOWN·NEOSOLTIA 등에서 명확한 공간 구조(방·통로·벽) 인식됨

**미확정**:
- 헤더 meta 바이트의 의미 (어떤 tile sheet 사용 등)
- `extras` 영역의 NPC/exit/event 데이터 포맷

**관측된 맵 이름 예시**: NEOSOLTIA, SMALL_FACTORY_4, SECRET_ROOM, RUINED_DESERT_1~3, GULBEIG_RUIN_5~7, GULBEIG_ROOM, WAR_OF_RUIN_1~2, NEMESIS_FOREST_5, SMALL_CAVE_1, BEAST_FOREST_1~3, UNDER_CAVE_1~3, GUARDIAN_CAVE_1~7, CORE_OF_RUIN, BOSS_TOWN, RETIREMENT.

### `_bm` (비트맵/스프라이트) — ✅ 다중 프레임 완전 해독

**파일은 N개의 독립 프레임을 담은 컨테이너이며, 각 프레임은 자체 mini-header + 팔레트 + 픽셀을 가짐.**

```
struct BitmapFile {
    // ─── 6-byte file header ───
    uint16_t frame_count;          // 1–43 (관측)
    uint16_t flag1;                // 첫 프레임 데이터 크기 힌트 (정밀하지 않음)
    uint16_t reserved;             // 항상 0x0000

    // ─── frame_count 개의 Frame 연속 배치 ───
    Frame    frames[frame_count];
};

struct Frame {
    // ─── 9-byte mini-header ───
    uint8_t  type;                 // 0x0b (uncompressed), 0x0c (변형 - 압축 추정)
    uint16_t w;                    // LE
    uint16_t h;                    // LE
    uint16_t cw;                   // 의미 미확정 (대부분 ≤ w)
    uint16_t ch;                   // 의미 미확정 (대부분 ≤ h)

    // ─── 2-byte palette marker ───
    uint16_t marker;               // 0xf81f LE — 매 프레임의 경계 시그널

    // ─── 32-byte palette ───
    uint16_t palette[16];          // RGB565 LE, palette[0] = 0xf81f (마젠타 = 투명)

    // ─── pixel data ───
    uint4_t  pixels[w * h];        // 4-bit 인덱스 packed, big-nibble-first
                                    // byte b → pixel(b>>4), pixel(b & 0xf)
};
```

**파싱 전략 (검증됨)**:
파일 전체에서 `0x1f 0xf8` 바이트 시퀀스를 찾고, 각 마커마다 9바이트 앞 바이트가 0x0b/0x0c인지 검증. 통과한 위치가 프레임 mini-header 시작점.

**관찰된 에지 케이스**:
- 일부 프레임에서 직전/직후 alignment로 2~6 byte underrun (시각 영향 미미, 마지막 픽셀 행 일부만 누락)
- `type=0x0c` 프레임은 type=0x0b와 다른 픽셀 인코딩 가능 (압축 추정). 1차 베이스라인은 동일 처리, 향후 Ghidra에서 디코더 확인 필요
- 픽셀 데이터 안에서 우연히 `1f f8 + 9바이트 앞 0b` 패턴이 발생할 수 있음 → false positive. dimensions 1..512 sanity check 로 대부분 제거
- master `flag1` 값은 frame 0 데이터 크기와 일치하지 않는 경우가 있음 (정밀하지 않은 힌트)

**렌더링 검증 결과** (2026-05-01):
- 479개 `_bm` 파일 → **3,131개 프레임 PNG 추출 성공** (단일 프레임 솔루션 대비 6배 증가)
- 시각 검증: boss/hero/enemy/menu/comm/logo 모든 카테고리에서 정상 스프라이트 확인
- `comm/number_bm` 디지트 시트 명확
- `boss/boss9000_bm` 23 프레임 중 21개 정상 (false positive 2개 제외)

**Android 매핑 전략**: 빌드 타임에 모든 프레임을 PNG로 export. 각 프레임은 별도 파일 또는 sprite atlas로 packing. 런타임은 표준 `Bitmap`/`Canvas` API.

### `_cif` (캐릭터 정보/애니메이션) — ⚠️ 부분 해독

```
struct CifFile {
    uint8  slot_count;                  // 0..8
    uint8  category;                    // 0=hero/boss, 1=enemy 추정, 2=일부 보스
    uint8  sprite_indices[slot_count];  // 2..2+count
    bytes  animation_data[];            // 나머지 (frame/cell 데이터, 디코더 종류 별)
};
```

**확정 부분 (검증됨)**:
- `slot_count` = 캐릭터의 키 슬롯 수 (영웅 8, 적 1~5, 보스 1, 맵 스프라이트 1)
- `sprite_indices` = 각 슬롯이 가리키는 BM 프레임 인덱스
- enemy/map: 인덱스 = `_bm` 파일 번호 (예: `e100_cif` indices [1,2,3,4] → `e1001_bm`, `e1002_bm`, `e1003_bm`, `e1004_bm`)
- hero/boss: 인덱스가 파일 번호와 직접 매핑되지 않음 — 멀티프레임 BM의 글로벌 프레임 인덱스로 추정

**Hero (h0_cif) frame 인코딩 (2026-05-07 해독)**:
- 41 byte fixed-stride 레코드, 헤더 3 byte (`0a XX YY` = duration, type, count) + 9 cells × 4 byte + 2 byte 트레일러
- Cell 4 byte: `[x_s8, y_s8, bm_ref_u8, flag_u8]`
- 4 그룹 × 8 frame = 32 walk-cycle frame (h0 만 이 구조, h4-h11 은 다른 인코딩)

**Boss/enemy frame 인코딩 (2026-05-09 해독, FUN_00098ef8 @ 0x98ef8)**:
- 헤더 직후부터 4-byte stride 셀 스트림 (별도 frame 헤더 없음)
- Cell byte 0 분해:
  - `bit 7` = special flag (특수 셀)
  - `bits 5..6` = orientation (0/1/2; sentinel 시 3)
  - `bits 0..4` = cell ref / type (5-bit)
- Sentinel cell = `byte 0 == 0x7f` (전체로는 `7f 00 ff ff` 4-byte 패턴 일반적). 디코더가 skip
- bytes 1..3 = `(x_s8, y_s8, extra_u8)` 추정 (BM 매핑까지 확정 후 검증 가능)
- 통계 (39 cif): boss0 sentinel 46개, boss3 86개, boss4 147개. 대부분 enemy 는 sentinel 0개 → 단일 frame
- 라이브러리: `tools/recon/analyze_cif.py` 의 `decode_cell_byte / parse_boss_header / parse_boss_cells / split_frames_by_sentinel / boss_cif_summary`
- 일괄 통계 도구: `tools/recon/dump_boss_cif.py` → `work/h3/boss_cif_summary.json`

**미확정**:
- Boss/enemy cell 의 bytes 1..3 정확한 의미 (좌표/플래그 가설) — BM 매핑까지 검증되면 확정 가능
- h4-h11 walk-cycle 인코딩 (h0 의 4×8 그룹 구조와 다름; 4-5 frame 짧은 그룹 흩어짐)
- 슬롯과 게임 로직 간 매핑 (예: 슬롯 0 = idle, 1 = walk-up 등 표준화 여부)
- Animation tick handler `UndefinedFunction_00041172` 이 frame_idx++ + frame_count wrap 으로 동작 — `frame_count` 위치 미확정

→ 향후 보강 분석 가능. 현재는 슬롯 인덱스 정보 + boss/enemy decoder 라이브러리로 cell 단위 해석 가능.

### `_scn` (이벤트 스크립트) — ⚠️ 부분 분석, 대사 코퍼스 추출 완료

```
struct ScnFile {
    bytes  header[4];                  // 가변 (예: "80 00 02 ff")
    bytes  bytecode_and_text[];        // byte-code 명령 + 임베디드 EUC-KR 대사
};
```

**확정**:
- 244개 `_scn` 모두에서 **26,415개 EUC-KR 대사 추출** (9,741 unique)
- 0xff 가 빈번한 separator/opcode 종결자
- 대사는 byte-code 명령 사이에 연속 EUC-KR 시퀀스로 임베디드

**미확정**:
- Byte-code opcode 매핑 (이동·분기·NPC 호출·상품·플래그 등) — 향후 Ghidra 분석으로 보강 가능

**i18n 베이스**:
- `work/converted/dialogue_corpus.json` — 전체 코퍼스
- `work/converted/dialogue_top_texts.json` — 빈도 상위 200
- 캐릭터 이름 추출: 케이(847×), 리츠(811×), 일레느(454×), 시엔(201×), 레아(113×), 엘지스(108×), 케네스(95×), 이안(77×), 멜페토(76×)
- 지명: 솔티아 (Soltia), 스토리 키워드: 가디언, 가면의검사 등

## 세이브 파일 (`P/`)

| 파일 | 크기 | 비고 |
|---|---:|---|
| `Hero3GameSave_0` | 1472B | 게임 진행 데이터 |
| `Hero3OptionSave` | 32B | XOR/암호화된 옵션 (분석 보류, 호환 불필요) |
| `Hero3SlotSave_0` | 32B | 슬롯 메타데이터 |

> 사용자 결정: **세이브 호환 불필요** → 이 파일들은 자료로만 보존.

## 변환 파이프라인 우선순위

| 우선 | 포맷 | 작업 | 즉시 가능? |
|---:|---|---|---|
| 1 | `_txt` | EUC-KR → UTF-8 JSON, ENG/KOR 분리 → Android string resources | ✅ |
| 2 | `_pa` | 81-byte 등 → 표준 PAL/JSON | ✅ |
| 3 | `_mf` | 빌드 타임 SMAF → OGG | ✅ (외부 도구) |
| 4 | `_dat` | 레코드 → JSON | ✅ |
| 5 | `_bm` | 4-bit 인덱스 + 팔레트 → PNG (모든 프레임) | ✅ |
| 6 | `_cif` | 애니메이션 메타 → JSON | ⚠️ Ghidra 후 |
| 7 | `_mp` | 타일맵 → Tiled TMX 또는 JSON | ⚠️ Ghidra 후 |
| 8 | `_scn` | 이벤트 → 사람 읽기 가능 스크립트 | ❌ 큰 작업 |

## Ghidra 분석 우선순위

`client.bin64000`에서 찾아야 할 함수들:

1. **비트맵 로더** — `_bm` 픽셀 디코딩 함수 (가장 critical)
2. **CIF 파서** — 애니메이션 프레임 시스템
3. **맵 로더** — 타일맵 렌더링
4. **이벤트 인터프리터** — `_scn` 명령어 디스패치 테이블
5. **세이브 직렬화** — 게임 상태 구조 (호환 불필요지만 데이터 모델 참조용)

## HD 리마스터 노트

원본 240×320, 4-bit 인덱스 비트맵 → 모던 1080p+. 두 경로:

- **AI 업스케일** (waifu2x, Real-ESRGAN): 빠르고 자동, 픽셀아트 스타일에 호불호. 권장 — 1차 베이스라인.
- **수동 리드로우**: 핵심 캐릭터/UI만. AI 결과를 바탕으로 점진 교체.

해상도와 별도로 **렌더링은 가상 240×320 캔버스 + 정수 스케일** 방식으로 시작하면 원본 게임플레이 보존 + HD 자산 슬롯인이 가능.
