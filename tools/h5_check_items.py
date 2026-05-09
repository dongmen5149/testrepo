"""items.json 의 class_mask / class_label 검증."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
with open(ROOT / 'apps/hero5-godot/assets/gamedata/items.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for slot in (0, 5, 9, 10):
    key = f'slot_{slot}'
    if key not in data: continue
    print(f"=== {key} samples ===")
    for r in data[key][:5]:
        print(f"  {r['name'][:14]:>14}  subtype={r.get('subtype')}  cls_mask={r.get('class_mask'):>3}  cls_label={r.get('class_label'):<6}  lv={r.get('level_limit')}")
