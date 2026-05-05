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

## 미해독: extras 영역

Hero3 `_mp` 와 같이 NPC/exit/event placement 추정. 7-byte record + flag bytes (0x00/0x40/0x80/0xc0) 패턴 관찰됨. 정확한 포맷은 Ghidra 의 `/MAP/M/_MAP_M_%03d` 로더 함수 추적 후 확정.

## Layer0/Layer1 의미

- **Layer 0**: terrain tile index (TILE/_TILE_NNN 또는 OBJ/ 인덱스 매핑)
- **Layer 1**: collision / overlay (Hero3 와 동일 — 0 = 통과, 비-0 = 차단 또는 오브젝트)

타일 PNG 매핑은 Hero3 와 비슷하게 palette 안의 tile id 와 TILE/ 폴더의 PNG 인덱스를 연결해야 함 (게임 wiring 단계).
