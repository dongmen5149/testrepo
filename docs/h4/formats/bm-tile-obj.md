# BM / TILE / OBJ 비트맵 디코더 (Hero3+Hero4 공통)

Hero3 와 Hero4 모두 같은 BM 디코더 (`FUN_00010fe4` Ghidra 분석 결과). 두 게임이 같은 한빛 내부 엔진의 진화형이라 알고리즘이 100% 호환.

## 컨테이너 종류

| 위치 | 컨테이너 | 설명 |
|---|---|---|
| Hero3 `_bm` | 멀티프레임 BM | 6-byte file header + N × frame |
| Hero3 `boss/_bm`, `enemy/_bm`, `hero/_bm` | 멀티프레임 BM | 동일 |
| Hero4 `_BM` | 멀티프레임 BM | 동일 |
| Hero4 `OBJ/SPR/_OBJ_SPR_NNN_BM` | 멀티프레임 BM | 동일 |
| **Hero4 `TILE/_TILE_NNN`** | **single-frame** | file header 없이 frame mini-header 부터 시작 |
| **Hero4 `OBJ/{000,001,002}/_OBJ_NNN`** | **single-frame** | 동일 |

## 멀티프레임 BM layout

```
file_header (6 bytes): count_LE16 + flag1 + reserved
frames[count]: 각 프레임 자체 mini-header + palette + pixels
  mini_header (9 bytes): type + w_LE16 + h_LE16 + cw_LE16 + ch_LE16
  marker     (2 bytes): 0x1ff8
  palette   (32 bytes): 16 × RGB565 LE
  pixels:
    type 0x0b: 4-bit big-nibble-first dense, palette[0]=0xf81f 투명
    type 0x0c: 8-bit dense palette indexed, byte=0 → 투명 skip
```

프레임 경계 식별: `0x1ff8` 마커 위치 + 9 bytes 앞 type byte (0x0b 또는 0x0c) sanity 검증.

## Single-frame BM layout (TILE/, OBJ/{000,001,002}/)

```
[type=0x0b 또는 0x0c]
[w_LE16][h_LE16][cw_LE16][ch_LE16]
[marker=0x1ff8]
[palette: 16 × RGB565 LE]
[pixels: type 별 위와 동일]
```

= 멀티프레임 BM 의 frame 1개 부분만 단독으로 떼어낸 형태. file header (6 bytes) 가 없는 차이.

## Type 0x0c 디코더 (Ghidra 확정)

```python
# FUN_00010fe4 line 4847-4851 분석 결과
for i in range(width * height):
    idx = pixels_data[i]
    if idx == 0:
        continue  # transparent
    if idx < 16:  # palette has 16 entries
        canvas[x=i%w, y=i//w] = palette[idx]
```

**1 byte = 1 pixel**, palette index. **index 0 = 투명 skip**. 매우 단순한 indexed bitmap.

이전에 시도했던 **sparse encoding 가설** (records ÷ cells ≈ 0.51 → RLE 추정) 은 **모두 오답**. byte 0 이 transparent skip 되는 비율이 우연히 그 수치와 비슷했던 것.

## 시각 검증 (Hero3+Hero4)

| 샘플 | 결과 |
|---|---|
| Hero3 `theme_0_bm` (16×480 strip) | 9% nonempty, 16 unique colors — 타일셋 strip |
| Hero3 `obj_0_bm` frame 0 (32×16) | 자연스러운 작은 오브젝트 |
| Hero4 `_TILE_000` (16×432) | 43% nonempty, 16 colors — 배경/UI |
| Hero4 `_OBJ_000` (16×16) | 90.6% nonempty, 12 colors — 작은 오브젝트 |

## Hero3 91 BM unblocking

이번 Hero4 분석으로 Hero3 의 미해독 0x0c 프레임들 (`map/theme_*_bm` 47 + `map/obj_*_bm` 44 = **91 파일**) 도 자동으로 디코딩 됨. `tools/converter/convert_bm_v2.py` 한 번의 패치로 양쪽 게임 unblocking.

## 변환 결과 (errors=0)

| 게임 | 멀티프레임 BM | Single-frame BM | 합계 |
|---|---|---|---|
| Hero3 | 479 files → 3,131 frames | — | 3,131 PNG |
| Hero4 | 30 files → 200 frames | TILE 30 + OBJ 246 = 276 | 476 PNG |

## 변환 명령

```bash
HERO_GAME=h3 python tools/converter/convert_all.py work/h3/extracted work/h3/converted
HERO_GAME=h4 python tools/converter/convert_all.py work/h4/extracted work/h4/converted
```

`convert_all.py` 가 자동 분기:
- `_BM`/`_bm` 접미사 → 멀티프레임
- `_TILE_*` / `_OBJ_*` (단, `_OBJ_SPR_*_BM` 는 멀티) → single-frame

## 미해독 / TODO

- **`_TILE_030`** — 다른 헤더 prefix (8-byte file header `01 00 00 00 8d 00 00 00` + 일반 frame header). 컨테이너 변형으로 추정 — 향후 분석 보류
- **palette[0] 의미** — 0x0b 는 magenta=투명 보장, 0x0c 는 byte=0 이 투명. 두 정의가 다름. Ghidra 에서 palette[0] 처리 함수 한번 더 확인 가치 있음
