"""
팔레트 파일 → JSON.

지원 포맷:
- Hero3 `_pa`  : uint8 count + count × 4 byte (RGBA, 4번째 byte는 거의 항상 0)
- Hero4 `_PAL` : uint8 count + count × 8 byte (RGB triplet 페어, 4·8번째 byte=alpha=0)
                 → 두 색을 main_color / shadow_color 로 추정 (BM 변환기 연결 후 확정)

검증: len(file) == count * 4 + 1 (h3)  또는  count * 8 + 1 (h4).
"""
from __future__ import annotations
import sys, json, pathlib


def parse_palette(data: bytes) -> list[dict]:
    if len(data) < 1:
        raise ValueError('empty file')
    count = data[0]
    expected_4 = count * 4 + 1
    expected_8 = count * 8 + 1
    if len(data) == expected_4:
        bpe = 4
    elif len(data) == expected_8:
        bpe = 8
    else:
        raise ValueError(
            f'size mismatch: count={count} expected={expected_4} (h3) or {expected_8} (h4), actual={len(data)}'
        )

    colors: list[dict] = []
    for i in range(count):
        off = 1 + i * bpe
        entry = data[off : off + bpe]
        if bpe == 4:
            b0, b1, b2, b3 = entry
            # b0=B, b1=G, b2=R, b3=A 또는 그 반대 — _bm 변환기가 BGRA 라고 가정하던 기존 동작 유지
            colors.append({
                'rgba_be': f'#{b0:02x}{b1:02x}{b2:02x}{b3:02x}',
                'argb_le': f'#{b3:02x}{b2:02x}{b1:02x}{b0:02x}',
                'bytes': [b0, b1, b2, b3],
            })
        else:  # bpe == 8 (Hero4 _PAL)
            r1, g1, b1, a1, r2, g2, b2, a2 = entry
            colors.append({
                # 첫 4byte = primary color, 둘째 4byte = secondary (그림자/하이라이트 추정)
                'primary': f'#{r1:02x}{g1:02x}{b1:02x}',
                'secondary': f'#{r2:02x}{g2:02x}{b2:02x}',
                'primary_alpha': a1,
                'secondary_alpha': a2,
                'bytes': list(entry),
            })
    return colors


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    colors = parse_palette(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps({'count': len(colors), 'colors': colors}, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({len(colors)} colors)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
