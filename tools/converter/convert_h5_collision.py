"""
Hero5 (md)NN 맵 데이터에서 collision + tile attribute 배열 추출.

근거:
  Map::Initialize 가 malloc(tileCount) 와 malloc(tileCount*2) 두 버퍼 할당.
  → collision = 1B/tile, tile_attr = 2B/tile.
  (md) 파일 분석 결과 모든 67 파일이 (S, 2S) section 쌍 보유 (100%).

전략:
  1. (md) 파일의 section table 에서 (S, 2S) 쌍 찾기 (가장 큰 쌍 = main map)
  2. 동일 사이즈 section 쌍 (mini-map / 다른 layer) 도 추출
  3. 폭 추정: section_size 가 정수 인수분해 가능한 폭/높이 후보 중
     phone 게임에 적합한 (W ≤ 64, H ≤ 256) 우선

산출:
  apps/hero5-godot/assets/maps/<id>.json — {width, height, collision[], tile[]}
"""
from __future__ import annotations
import pathlib, csv, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT_DIR = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'maps'


def parse_md(d: bytes) -> dict:
    n_off = (0x60 - 0x1c) // 4
    offs = list(struct.unpack_from(f'<{n_off}I', d, 0x1c))
    valid_sorted = sorted(set(o for o in offs if 96 <= o <= len(d)))
    sections = []
    for i, s in enumerate(valid_sorted):
        e = valid_sorted[i+1] if i+1 < len(valid_sorted) else len(d)
        sections.append((s, e, e - s))
    return {'sections': sections}


def best_dimensions(area: int) -> tuple[int, int]:
    """area 를 (width, height) 로 분해 — phone-friendly (작은 W, 큰 H 우선)."""
    best: tuple[int, int] = (1, area)
    best_score = abs(1 - area)
    for w in range(8, min(257, area + 1)):
        if area % w == 0:
            h = area // w
            if h > 256 or h < 8: continue
            # prefer ratios where 1.5 < h/w < 6 (vertical phone screens)
            ratio = h / w
            score = abs(ratio - 3.0)  # target H/W ≈ 3
            if score < best_score:
                best_score = score
                best = (w, h)
    return best


def extract(d: bytes, info: dict) -> dict | None:
    sections = info['sections']
    sizes = [s[2] for s in sections]
    # find largest (S, 2S) pair
    main_pair = None
    for i, sz in enumerate(sizes):
        if sz < 100: continue
        if 2 * sz in sizes:
            j = sizes.index(2 * sz)
            if main_pair is None or sz > main_pair[2]:
                main_pair = (i, j, sz)
    if not main_pair:
        return None
    i, j, area = main_pair
    w, h = best_dimensions(area)
    col_off = sections[i][0]; col_end = sections[i][1]
    til_off = sections[j][0]; til_end = sections[j][1]
    return {
        'width': w, 'height': h,
        'tile_count': area,
        'collision_section': i,
        'tile_section': j,
        'collision': list(d[col_off:col_end]),
        'tile': [struct.unpack_from('<H', d, til_off + k * 2)[0]
                 for k in range(area)],
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md_files = []
    with open(NAMES, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if '(md)' in r['recovered_name']:
                md_files.append(r)

    ok = 0
    for r in md_files:
        p = ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"], 16):08x}.bin'
        d = p.read_bytes()
        info = parse_md(d)
        ext = extract(d, info)
        if ext is None: continue
        # save as JSON (collision array as base64 might be smaller for big maps,
        # but JSON is fine for 67 files)
        # extract id from name (e.g., (md)00 → 0)
        name = r['recovered_name']
        idx = int(name.replace('c/map/(md)', ''))
        # write compact JSON: collision/tile as comma-separated strings to keep size down
        out = {
            'id': idx,
            'width': ext['width'],
            'height': ext['height'],
            'tile_count': ext['tile_count'],
            'collision_b64': bytes(ext['collision']).hex(),
            'tile_count_words': len(ext['tile']),
        }
        # save tile attributes separately as binary file (smaller than JSON)
        tile_bytes = b''.join(struct.pack('<H', v) for v in ext['tile'])
        (OUT_DIR / f'{idx:02d}.tile.bin').write_bytes(tile_bytes)
        col_bytes = bytes(ext['collision'])
        (OUT_DIR / f'{idx:02d}.col.bin').write_bytes(col_bytes)
        # JSON metadata
        (OUT_DIR / f'{idx:02d}.json').write_text(json.dumps({
            'id': idx,
            'width': ext['width'],
            'height': ext['height'],
            'tile_count': ext['tile_count'],
            'collision_section': ext['collision_section'],
            'tile_section': ext['tile_section'],
        }, indent=2), encoding='utf-8')
        ok += 1

    print(f'extracted {ok}/{len(md_files)} maps -> {OUT_DIR}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
