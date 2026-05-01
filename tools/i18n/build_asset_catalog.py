"""
변환된 자산을 검색·식별하기 쉽게 카탈로그 JSON 으로 정리.

출력: work/converted/asset_catalog.json
{
  "characters": {
    "h0": {"name_ko": "리츠?", "name_en": "Ritz?", "type": "hero", "bm_dirs": ["h00000_bm", ...], "cif": "h0_cif", "frame_count": ...},
    ...
  },
  "bosses": {...},
  "enemies": {...},
  "npcs": {...},
  "maps": {map0: {name: "NEOSOLTIA", name_en: "Neo Soltia", ...}},
  "ui_sprites": {...},
}

이 카탈로그는 Android 갤러리/디버그 UI 에서 의미 있는 라벨 표시,
나중에 시나리오 스크립트와 자산을 연결할 때 매핑 키로 사용.
"""
from __future__ import annotations
import json, pathlib, sys
import collections

ROOT = pathlib.Path(__file__).parent.parent.parent
CONVERTED = ROOT / 'work' / 'converted'

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from translation_dict import CHARACTERS, PLACES


def categorize_sprites():
    """sprites/<cat>/<bm_dir>/ 들을 카테고리별로 정리."""
    by_cat: dict[str, list[dict]] = collections.defaultdict(list)
    for cat_dir in CONVERTED.iterdir():
        if not cat_dir.is_dir():
            continue
        cat = cat_dir.name
        if cat in ('event', 'dat', 'snd', 'fgi', 'logo', 'map', 'menu', 'comm', 'skill', 'hero', 'boss', 'enemy', 'npc', 'font'):
            for bm_dir in cat_dir.iterdir():
                if not bm_dir.is_dir():
                    continue
                pngs = sorted(p.name for p in bm_dir.glob('*.png'))
                if not pngs:
                    continue
                # 첫 프레임 dimensions
                first = pngs[0]
                # frame_NN_WxH_tT.png
                parts = first.rsplit('.', 1)[0].split('_')
                dim = parts[2] if len(parts) >= 3 else '?'
                by_cat[cat].append({
                    'name': bm_dir.name,
                    'frame_count': len(pngs),
                    'first_frame': first,
                    'first_dim': dim,
                })
    return by_cat


def load_maps() -> list[dict]:
    map_dir = CONVERTED / 'map'
    out = []
    if not map_dir.exists():
        return out
    for jpath in sorted(map_dir.glob('map*_mp.json'), key=lambda p: int(''.join(c for c in p.stem.split('_')[0] if c.isdigit()) or 0)):
        info = json.loads(jpath.read_text(encoding='utf-8'))
        ko_name = info.get('name', '')
        en_name = PLACES.get(ko_name, ko_name)
        out.append({
            'file': jpath.stem,
            'name_ko': ko_name,
            'name_en': en_name,
            'width': info.get('width'),
            'height': info.get('height'),
            'palette_count': info.get('palette_count'),
        })
    return out


def main():
    by_cat = categorize_sprites()
    maps = load_maps()

    catalog = {
        'meta': {
            'generated_at': '2026-05-01',
            'source': 'work/converted',
        },
        'sprites_by_category': {cat: items for cat, items in sorted(by_cat.items())},
        'maps': maps,
        'translations': {
            'characters': CHARACTERS,
            'places': PLACES,
        },
    }

    out_path = CONVERTED / 'asset_catalog.json'
    out_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')

    # 요약 출력
    total_sprites = sum(len(v) for v in by_cat.values())
    total_frames = sum(item['frame_count'] for items in by_cat.values() for item in items)
    print(f'Catalog written: {out_path}')
    print(f'  total sprite directories: {total_sprites}')
    print(f'  total frames: {total_frames}')
    print(f'  maps: {len(maps)}')
    for cat, items in sorted(by_cat.items()):
        print(f'    {cat}: {len(items)} dirs, {sum(i["frame_count"] for i in items)} frames')


if __name__ == '__main__':
    sys.exit(main() or 0)
