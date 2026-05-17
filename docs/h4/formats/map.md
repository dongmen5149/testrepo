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

### Section 별 의미 추정 (Ghidra 후 확정 필요)

| section | typical count | 추정 |
|---|---|---|
| 0 | 50~200 | tile decoration / NPC spawn 위치 |
| 1 | 20~50 | exit / zone transition (sub data 가 다른 zone id) |
| 2 | 10~30 | event trigger / interactive object |
| 3+ | 0~20 | item/treasure / quest marker |

### 샘플 (`_MAP_M_000`, 수레바퀴섬/선착장, 20×20)

```
extras = 850B, 4 sections, tail=6B
  sec[0]: 55 records → e.g. type=0 sub=[40,255,47] pos=(232,224)
  sec[1]: 26 records → e.g. type=0 sub=[0,255,58]  pos=(200,224)
  sec[2]: 24 records → e.g. type=0 sub=[0,255,53]  pos=(40,32)
  sec[3]: 0 records  (마커 / 종료자)
```

### 파서 + JSON

[tools/converter/parse_h4_map_extras.py](../../tools/converter/parse_h4_map_extras.py) 97 파일 모두 파싱. `work/h4/converted/map_extras_parsed.json` 출력. 각 record 의 `type` / `sub` / `x` / `y` 포함.

정확한 각 section 의 명명 (NPC vs exit vs event) + sub[3] 의 의미 (특히 type 의 상위 2비트가 무엇을 표시하는지) 는 Phase B Ghidra 분석으로 확정.

## Layer0/Layer1 의미

- **Layer 0**: terrain tile index (TILE/_TILE_NNN 또는 OBJ/ 인덱스 매핑)
- **Layer 1**: collision / overlay (Hero3 와 동일 — 0 = 통과, 비-0 = 차단 또는 오브젝트)

타일 PNG 매핑은 Hero3 와 비슷하게 palette 안의 tile id 와 TILE/ 폴더의 PNG 인덱스를 연결해야 함 (게임 wiring 단계).
