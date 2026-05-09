"""items.json 의 EquipItem 새 fields 확인 + cross-check."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
with open(ROOT / 'apps/hero5-godot/assets/gamedata/items.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print("== EquipItem 슬롯 (cat 1-11) 새 fields ==")
for slot in ('slot_0', 'slot_4', 'slot_5', 'slot_9', 'slot_10'):
    if slot not in data: continue
    recs = data[slot]
    print(f"\n[{slot}] ({len(recs)} items)")
    for r in recs[:3]:
        cls = r.get('class_restriction', '?')
        lv = r.get('level_limit', '?')
        item_id = r.get('item_id', '?')
        print(f"  {r['name'][:14]:>14s}  price={r.get('price','?'):>5}  cls={cls}  lv={lv}  item_id={item_id}")

print("\n== 비-EquipItem 슬롯 (cat 12+) 검증 - named fields 없어야 ==")
for slot in ('slot_11', 'slot_13', 'slot_17'):
    if slot not in data: continue
    r = data[slot][0] if data[slot] else None
    if r:
        has_cls = 'class_restriction' in r
        print(f"  {slot}: name={r['name'][:14]}, has class_restriction={has_cls}")
