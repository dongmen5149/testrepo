"""val_15f upper 3 bit 분석."""
import json, pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
with open(ROOT / 'apps/hero5-godot/assets/gamedata/items.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# val_15f upper 3 bit = (val_15f >> 5) & 0x7
# bit 5 = 32, bit 6 = 64, bit 7 = 128
all_recs = []
for slot in range(11):
    key = f'slot_{slot}'
    if key not in data: continue
    for r in data[key]:
        v = r.get('val_15f')
        if v is not None:
            all_recs.append((slot, v, r['name']))

print("== val_15f upper 3 bit (>>5) 분포 ==")
upper = Counter((v >> 5) & 0x7 for _, v, _ in all_recs)
for u, c in sorted(upper.items()):
    bits = bin(u)[2:].rjust(3, '0')
    print(f"  upper={u} (0b{bits})  count={c}")

# 각 upper 별 sample items
print("\n== upper bits 별 sample items ==")
upper_examples = {}
for slot, v, name in all_recs:
    u = (v >> 5) & 0x7
    upper_examples.setdefault(u, []).append((slot, v, name))
for u in sorted(upper_examples):
    print(f"\n  upper={u} ({len(upper_examples[u])} items):")
    for slot, v, name in upper_examples[u][:8]:
        low5 = v & 0x1f
        print(f"    slot_{slot}  v={v:>3}  low5={low5:>2}  upper={u}  name={name}")

# 슬롯 X upper 매트릭스
print("\n== slot × upper 매트릭스 ==")
matrix = {}
for slot, v, _ in all_recs:
    u = (v >> 5) & 0x7
    matrix.setdefault(slot, Counter())[u] += 1
print(f"  {'slot':>4s}  | upper=0  upper=1  upper=2  upper=3  upper=4  upper=5  upper=6  upper=7")
for slot in sorted(matrix):
    row = matrix[slot]
    cells = [f"{row.get(u, 0):>7d}" for u in range(8)]
    print(f"  {slot:>4d}  | {'  '.join(cells)}")
