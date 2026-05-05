"""
Hero4 _MAP_M_NNN 맵 파서.

전체 layout:
    [v] [b1] [ff] [b3] [ff] ... [b_{2v-1}] [ff] [nlen1] [name1_eucKR×nlen1]
        [nlen2] [name2_eucKR×nlen2] [NUL]
        [width][height][palette_count][meta]
        [palette: palette_count bytes]
        [layer0: width*height bytes]   # terrain
        [layer1: width*height bytes]   # collision/objects
        [extras: 나머지]                # NPC/exit/event placement (포맷 미해독)

v ∈ {1, 2, 3} — 0xff separator 의 개수. nlen1 offset = 2v+1.
post-NUL body 는 Hero3 _mp 와 동일 layout.
"""
from __future__ import annotations
import json, sys, pathlib


def parse_h4_map(data: bytes) -> dict:
    if len(data) < 8:
        raise ValueError('file too short')
    v = data[0]
    if v not in (1, 2, 3):
        raise ValueError(f'unknown version byte 0x{v:02x}')
    for k in range(v):
        ff_off = 2 + 2 * k
        if data[ff_off] != 0xff:
            raise ValueError(f'v={v}: expected 0xff at offset {ff_off}, got 0x{data[ff_off]:02x}')
    meta = [data[1 + 2 * k] for k in range(v)]
    i = 2 * v + 1
    nlen1 = data[i]; i += 1
    name1 = data[i : i + nlen1].decode('euc-kr', errors='replace'); i += nlen1
    nlen2 = data[i]; i += 1
    name2 = data[i : i + nlen2].decode('euc-kr', errors='replace'); i += nlen2
    if data[i] != 0x00:
        raise ValueError(f'expected NUL at offset {i}, got 0x{data[i]:02x}')
    i += 1  # body 시작

    # === post-NUL body (Hero3 _mp 와 동일 layout) ===
    width = data[i]; i += 1
    height = data[i]; i += 1
    palette_count = data[i]; i += 1
    body_meta = data[i]; i += 1
    palette = list(data[i : i + palette_count]); i += palette_count

    layer_size = width * height
    layer0 = list(data[i : i + layer_size]); i += layer_size
    layer1 = list(data[i : i + layer_size]); i += layer_size
    extras_raw = data[i:]

    return {
        'version': v,
        'meta_bytes': meta,
        'name': name1,
        'place': name2,
        'width': width,
        'height': height,
        'palette_count': palette_count,
        'body_meta': body_meta,
        'palette': palette,
        'layer0': layer0,
        'layer1': layer1,
        'extras_size': len(extras_raw),
        'extras_first_64': extras_raw[:64].hex() if extras_raw else '',
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    info = parse_h4_map(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({info["width"]}x{info["height"]} pc={info["palette_count"]})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
