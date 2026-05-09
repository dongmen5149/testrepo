"""items.json 의 record 의 extra_hex 길이 확인."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
with open(ROOT / 'apps/hero5-godot/assets/gamedata/items.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for slot in ('slot_0', 'slot_5', 'slot_12', 'slot_17'):
    if slot not in data: continue
    r = data[slot][0]
    eh = r.get('extra_hex', '')
    print(f"{slot}: name={r['name']!r}  extra_len_bytes={len(eh)//2}  first_5={eh[:10]}")
