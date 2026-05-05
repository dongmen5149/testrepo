# `_PAL` 팔레트 포맷 (Hero4)

196개 파일 (`H4/PAL/_H_NNN_PAL`, `MAP/_M_NNN_PAL` 등). Hero3 `_pa` 의 8byte/color 변형.

## 검증된 구조

```
[count: uint8] [entries: count × 8 byte]
```

각 entry (8 byte):
```
byte 0: r1   (primary R)
byte 1: g1   (primary G)
byte 2: b1   (primary B)
byte 3: a1   (primary alpha?  대부분 0)
byte 4: r2   (secondary R)
byte 5: g2   (secondary G)
byte 6: b2   (secondary B)
byte 7: a2   (secondary alpha? 대부분 0)
```

검증: `len(file) == count * 8 + 1` — 196/196 모두 통과.

## Hero3 vs Hero4 비교

| | Hero3 `_pa` | Hero4 `_PAL` |
|---|---|---|
| Bytes per color | 4 | **8** (2배) |
| Layout | RGBA 단일 | primary RGB + secondary RGB 페어 |
| 카운트 byte | byte 0 | byte 0 |

`tools/converter/convert_palette.py` 가 두 포맷 자동 감지 (size 검증).

## Secondary RGB 의 의미 (미해독)

Ghidra 분석 단서: `client.bin387872` 의 string `"====> Alpha Palette Index Not Found"` 발견.

가능한 가설:
1. **Alpha mask 슬롯** — secondary RGB 는 픽셀별 alpha (투명도) 매핑용
2. **그림자 색** — 캐릭터 윤곽선 / 그림자에 사용되는 두번째 색
3. **다른 광원/조명 변형** — 낮/밤 / 인도어/아웃도어 변형

확정에 필요: Ghidra 에서 `_PAL` 로더 함수 (`/H4/PAL/_H_%03d_PAL` string xref) 추적.

## 샘플 데이터

`H4/PAL/_H_000_PAL` (캐릭터 0의 첫 팔레트):
```
size: 145 bytes
count: 0x12 = 18
entry 0 bytes: 2a 45 e5 00  72 38 9a 00
  = primary  RGB(0x2a, 0x45, 0xe5) = 분홍빛 빨강
  + secondary RGB(0x72, 0x38, 0x9a) = 진한 자주
```

Primary 와 secondary 의 색이 의미적으로 연관 (둘 다 빨강 계열) → 그림자/하이라이트 가설 유력.

## 변환

`tools/converter/convert_all.py` 가 자동 처리 (case-insensitive `_PAL` 매칭). 출력 JSON 예:
```json
{
  "count": 18,
  "colors": [
    {"primary": "#2a45e5", "secondary": "#72389a", "primary_alpha": 0, "secondary_alpha": 0, "bytes": [...]},
    ...
  ]
}
```
