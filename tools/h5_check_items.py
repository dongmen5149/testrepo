"""items.json cat 12+ extra 길이 + sb_start 분석."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
with open(ROOT / 'apps/hero5-godot/assets/gamedata/items.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("== extra 길이 vs sb_start ==")
for slot in range(19):
    key = f'slot_{slot}'
    if key not in data: continue
    recs = data[key]
    if not recs: continue
    r = recs[0]
    eh = r.get('extra_hex', '')
    extra_len = len(eh) // 2
    sblen = r.get('sub_record_len', 0)
    sb_start = 5 + (sblen or 0)
    rem = extra_len - sb_start
    cat = data.get('_meta', {}).get('category_dispatch', {}).get(str(slot), {}).get('category', '?')
    print(f"  slot_{slot:>2}  cat={cat:<10s}  extra_len={extra_len:>3}  sblen={sblen:>3}  sb_start={sb_start:>3}  rem={rem}  {r['name'][:14]}")
