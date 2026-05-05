# Hero4 자산 포맷 분석

원본: `Hero4/010100D4.jar` (한빛소프트 2009, SKT GVM/Clet, 240×320).

이 폴더의 각 문서는 `tools/converter/` 의 파서 모듈과 짝을 이룹니다.

| 문서 | 포맷 | 변환기 | 결과 (errors=0) |
|---|---|---|---|
| [pal.md](pal.md) | `_PAL` 8byte/color | [`tools/converter/convert_palette.py`](../../../tools/converter/convert_palette.py) | 196/196 |
| [map.md](map.md) | `_MAP_M_NNN` 헤더 v1/v2/v3 + body | [`tools/converter/convert_h4_map.py`](../../../tools/converter/convert_h4_map.py) | 97/97 |
| [exd.md](exd.md) | `_EXD` 캐릭터 확장 데이터 | [`tools/converter/convert_exd.py`](../../../tools/converter/convert_exd.py) | 117/117 (헤더만) |
| [bm-tile-obj.md](bm-tile-obj.md) | `_BM` (멀티/싱글), `TILE`, `OBJ` 0x0b/0x0c | [`tools/converter/convert_bm_v2.py`](../../../tools/converter/convert_bm_v2.py), [`convert_h4_tile.py`](../../../tools/converter/convert_h4_tile.py) | 200 + 30 + 246 frames |
| [hdat.md](hdat.md) | `HDAT/` 25개 그룹 | (정찰만, 파서 없음) | 분류 완료 |

## Hero3 와 공유

다음 포맷은 Hero3 와 100% 호환이라 별도 분석 문서 없음 (기존 `docs/asset-formats.md` 참조):

| 포맷 | 결과 |
|---|---|
| `_TXT` | 5/5 |
| `_CIF` (single-frame) | 148/148 |
| `_DAT` | 26/26 |
| `_SCN` (이벤트 스크립트) | 350 → 4,078 대사 추출 |
| `_MMF` (Yamaha SMAF/MMF 사운드) | 41 (그대로 사용 가능) |

## 미해독 / 부분 해독 (Ghidra 후 확정)

- **`_PAL` secondary RGB 의미** — alpha mask vs 그림자 vs 두번째 색
- **`_EXD` payload entry layout** — 8byte header 뒤의 데이터 구조
- **`_MAP_M_` extras 영역** — NPC/exit/event 배치 (Hero3 의 `_mp` extras 와 같이 미해독)
- **HDAT entry layout** — 그룹 분류만 됐고 entry struct 미해독
- **`OBJ/{000,001,002}/` 인덱스 의미** — 247 single-frame BM 이지만 무엇의 인덱스인지 불명
- **`_TILE_030`** — 다른 헤더 prefix (file header 추가) — 해독 보류
