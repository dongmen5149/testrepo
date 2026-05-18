# `_MAP_M_NNN` 맵 포맷 (Hero4)

97개 파일 (`MAP/M/_MAP_M_000` ~ `_MAP_M_096`). 헤더는 새 포맷이지만 body 는 Hero3 `_mp` 와 동일.

## 전체 layout

```
[v: uint8]                               # 버전 (1, 2, 또는 3)
[meta_byte_1] [0xff]
[meta_byte_3] [0xff]                     # v ≥ 2 일 때
[meta_byte_5] [0xff]                     # v == 3 일 때
[nlen1: uint8] [name1: nlen1 byte EUC-KR]   # zone 이름 (예: "수레바퀴섬")
[nlen2: uint8] [name2: nlen2 byte EUC-KR]   # place 이름 (예: "선착장")
[NUL: 0x00]                              # 헤더 종료
─────────── (이 아래는 Hero3 _mp 와 동일 layout) ───────────
[width: uint8]
[height: uint8]
[palette_count: uint8]
[meta: uint8]
[palette: palette_count byte]
[layer0: width × height byte]            # terrain
[layer1: width × height byte]            # collision / objects
[extras: 나머지 byte]                    # NPC / exit / event 배치 (미해독)
```

## 헤더 버전 일반화 패턴

`v` (첫 byte) 가 그대로 의미: **`0xff` separator 의 개수**. 그 사이에 `v-1` 개의 메타바이트 (b1, b3, ...). `nlen1` 의 offset 은 항상 `2v + 1`.

| v | 헤더 byte 위치 |
|---|---|
| 1 | `[01][b1][ff][nlen1]...` |
| 2 | `[02][b1][ff][b3][ff][nlen1]...` |
| 3 | `[03][b1][ff][b3][ff][b5][ff][nlen1]...` |

`tools/converter/convert_h4_map.py:parse_h4_map()` 가 자동 인식.

## 변환 결과 (97/97)

- 총 cell 수: 96,655 (모든 layer0 합산)
- 맵 크기: 20×20 ~ 60×50, 평균 33×28
- extras 영역 평균 1,386 byte (정확한 포맷 미해독)

## Zone 분포 (20개 unique)

켈트 신화 Tuatha Dé Danann 4도시의 패러디:
- **뮤리아스** (Murias), **핀디아스** (Findias), **팔리아스** (Falias)
- 추가: **매도우힐**, **이름없는섬**, **수레바퀴섬**, **아눈섬**, **검은바위섬**, **은바위섬**, **해적소굴**, **보스룸**, **보스이벤트룸**, **선박 내부**, **성지**, **최종**

## 샘플 디코드

`_MAP_M_000` (size=1689):
```
v=2, meta_bytes=[0x02, 0x04]
zone="수레바퀴섬", place="선착장"
NUL @ offset 23
width=20, height=20, palette_count=11
layer0/layer1: 400 cells each
extras: 1,261 byte (NPC/exit/event 미해독)
```

## extras 영역 — multi-section 구조 풀림 (2026-05-18)

```
section 0: [count: uint8] [N₀ × 8-byte records]
section 1: [count: uint8] [N₁ × 8-byte records]
...
section K-1: [variable-length tail]   # 84/97 파일에서 1~40B trailing
```

각 8-byte record:
```
type    : uint8       (0x00 / 0x40 / 0x80 / 0xc0 — 상위 2비트 grouping)
sub[3]  : 3 byte      (sub-type / id / flags — 정확한 의미 미정)
x       : uint16 LE   (맵 픽셀 좌표, 보통 0~640)
y       : uint16 LE   (맵 픽셀 좌표, 보통 0~960)
```

### 검증 통계 (97 파일)

| section 수 | 파일 수 |
|---|---|
| 4 sections | 28 |
| 5 sections | 48 |
| 6 sections | 15 |
| 7 sections | 4 |
| 8 sections | 2 |

- **13 / 97** 파일은 모든 section 이 깔끔히 소비 (tail = 0B)
- **84 / 97** 파일은 1~40B trailing (variable-length 마지막 section 또는 padding)
- 모든 파일에서 적어도 첫 4 sections 정상 파싱 → 핵심 구조 확정

### 8B record 필드 의미 (2026-05-18 후속4 확정)

```
struct ExtrasRecord {
    uint8  type;       // bit flags. 99% 가 0x00 또는 0x40 (bit 0x40 = flip-x 추정)
    uint8  state;      // sub[0]. variant / animation state / facing
    uint8  marker;     // sub[1] = 0xff 100% (16,358/16,358 records). category separator
    uint8  obj_id;     // sub[2] = global OBJ id (0..246)
    uint16 x_le;       // pixel coord, /16 = tile_x
    uint16 y_le;       // pixel coord, /16 = tile_y
}
```

**global OBJ id 매핑** (sub[2]):

| 범위 | OBJ 경로 | 파일 수 |
|---|---|---|
| `0..99`     | `OBJ/000/_OBJ_NNN`  | 100 (16×16 icons) |
| `100..199`  | `OBJ/001/_OBJ_NNN`  | 100 (variable characters) |
| `200..246`  | `OBJ/002/_OBJ_NNN`  | 47 (variable items) |

**filename = global id 그대로** (offset 빼지 않음). 예: `obj_id=199 → OBJ/001/_OBJ_199`, `obj_id=228 → OBJ/002/_OBJ_228`. group 디렉토리는 100 단위 분류용.

**검증**: 16,358 sec[0..3] records 중 0 out-of-bounds (max=246). x/y 좌표는 16-pixel 정렬, max_x / max_y / 16 = map tile dimensions 정확히 일치 (`_MAP_M_001` size=2500 → 50×50 → 800×800px, max_x=776, max_y=805 ✓).

### Section 별 의미 (resource pool 분포 기반)

| section | total | unique obj_id | g000 / g001 / g002 비율 | 추정 |
|---|---|---|---|---|
| 0 | 8022 | 135 | 47% / 18% / 34% | terrain decoration / props (가장 큰 layer) |
| 1 | 6010 | 164 | 47% / 23% / 28% | secondary decoration / interactive objects |
| 2 | 1956 | 113 | 52% / 45% / 2% | NPC / character mix (g002 거의 제외) |
| 3 | 370 | **19** | 32% / 60% / 6% | 특수 NPC / portal / 이벤트 객체 (좁은 자원 풀) |

sec[3] 의 `(state=40, obj_id=10)` 페어가 105회 반복 — `OBJ/000/_OBJ_010` 의 표준 instance.

sec[4+] 는 schema 가 다름 (sub[1] 가 0xff 아니고, x/y 가 픽셀 좌표 범위 벗어남). 실제로는 single event/script block 으로 추정.

### sec[3] 뒤 event block schema (2026-05-18 후속5 발견)

97/97 maps 가 sec[3] 뒤에 byte sequence 존재. 그 중 **77/97** 이 다음 4-byte header 매칭:

```
[count: 1B] [00 01: 2B fixed magic] [type: 1B] [count × variable-length records]
```

| count | maps | 추정 |
|---|---|---|
| 3 | 51 | 표준 이벤트 블록 (3 events) |
| 4 | 26 | 확장 이벤트 블록 (4 events) |

type byte:
- `0x03`: 52 maps
- `0x02`: 34 maps
- `0x06`: 1 map

Records 는 variable-length (count=3 평균 12B/rec, range 3-20B). 정확한 record schema 는 Ghidra 후 확정. payload bytes 가 script opcode 같이 보이며 (0x00..0x30 범위 작은 값 위주), 0xff separator 없음.

남은 20 maps:
- 10 maps: 첫 2 byte `00 00` (no events?)
- 8 maps: `01 03 01 03` header (subtype variant)
- 1 map 각: `01 03 02 03`, `02 00 03 06`

### 샘플 (`_MAP_M_000`, 수레바퀴섬/선착장, 20×20)

```
extras = 850B, 4 sections, tail=6B
  sec[0]: 55 records → e.g. obj=OBJ/000/_OBJ_047 state=40 flip_x=False pos=(232,224)
  sec[1]: 26 records → e.g. obj=OBJ/000/_OBJ_058 state=0  flip_x=False pos=(200,224)
  sec[2]: 24 records → e.g. obj=OBJ/000/_OBJ_053 state=0  flip_x=False pos=(40,32)
  sec[3]: 0 records  (마커 / 종료자)
```

### 파서 + 분석기 + JSON

- [tools/converter/parse_h4_map_extras.py](../../tools/converter/parse_h4_map_extras.py) — raw 8B record 파싱 → `work/h4/converted/map_extras_parsed.json`
- [tools/recon/analyze_h4_map_extras.py](../../tools/recon/analyze_h4_map_extras.py) — global OBJ id 매핑 + 통계 → `work/h4/converted/map_extras_semantics.json`

Top 5 most-placed objects across 97 maps:

| OBJ | count |
|---|---|
| `OBJ/000/_OBJ_098` | 1273 |
| `OBJ/001/_OBJ_199` | 949 |
| `OBJ/002/_OBJ_228` | 622 |
| `OBJ/002/_OBJ_229` | 614 |
| `OBJ/000/_OBJ_048` | 547 |

남은 미해결 (Phase B Ghidra 필요):
- sec[3] 의 `state=40` 의미 (frame/anim/dir?)
- sec[4+] 의 정확한 schema
- `state` 바이트가 OBJ 별로 다른 의미를 갖는지 (frame index? facing direction? animation state?)
- 각 section 의 실제 게임 내 역할 (NPC spawn vs decoration vs trigger 등)

## Layer0/Layer1 의미

- **Layer 0**: terrain tile index (TILE/_TILE_NNN 또는 OBJ/ 인덱스 매핑)
- **Layer 1**: collision / overlay (Hero3 와 동일 — 0 = 통과, 비-0 = 차단 또는 오브젝트)

타일 PNG 매핑은 Hero3 와 비슷하게 palette 안의 tile id 와 TILE/ 폴더의 PNG 인덱스를 연결해야 함 (게임 wiring 단계).
