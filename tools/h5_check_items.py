"""items.json 모든 카테고리에 item_id + sub_record_hex 부여 검증."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
with open(ROOT / 'apps/hero5-godot/assets/gamedata/items.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("== 모든 슬롯의 첫 record (Round 18 common fields) ==")
for slot in range(19):
    key = f'slot_{slot}'
    if key not in data: continue
    recs = data[key]
    if not recs: continue
    r = recs[0]
    iid = r.get('item_id', '?')
    sblen = r.get('sub_record_len', '?')
    sbhex = r.get('sub_record_hex', '')[:20] + ('...' if len(r.get('sub_record_hex', '')) > 20 else '')
    print(f"  {key:>8s}  {r['name'][:14]:>14s}  item_id={iid:>5}  sblen={sblen:>3}  sub_record={sbhex}")
