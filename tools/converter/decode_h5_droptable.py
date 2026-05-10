"""
droptable.dat 디코더.

Round 27 → Round 30 분석 종합:
  ItemTable::LoadItemDropTable (0xa0b54) → LoadRes("/c/csv/droptable.dat")
  → ItemTable+0x214 = drop_table_ptr
  Monster::SetDropItem (0xbc910) 안에서 random drop_tier 선택 후 NewDropItem 호출.

VFS index 18, hash 0xe58e8176, 3278 byte.

Layout (u16 count + 252 × 13 byte = 63 monsters × 4 drop tiers):
  byte 0  = 0x0b (constant marker — 모든 252 entries 일관, 의미 미상 — format version 추정)
  byte 1  = 0x00 (sub-flag — 모든 252 일관)
  byte 2  = monster_idx (0..62, 4 entries 단위)
  byte 3  = drop_tier (0x0e/0x0f/0x10/0x11, 4 unique = 4 tier per monster)
  byte 4  = 12 unique values, byte 6 와 동일 분포 (paired field, val_15c?)
  byte 5  = 20 unique values (val_15f tier_flags 또는 idx?)
  byte 6  = 12 unique values, byte 4 와 동일 분포 (paired)
  byte 7  = 10 unique (idx 또는 val_162)
  byte 8  = 25 unique (val_160 또는 stat)
  byte 9  = 7 unique, 0xff=108 (sentinel = NewDropItem strb skip)
  byte 10 = 30 unique, 0x00=112 (val_163 또는 zero default)
  byte 11 = **NewDropItem cat arg (signed s8)**:
              0x05 (helmet) 27 / 0x06 (boots) 14 / 0x07 (accessory) 61 /
              0x08 (accessory_2) 46 / 0xff (-1=default→EquipItemInfo) 104
            ✅ Round 30 발견: byte 0 가 cat 이 아닌 byte 11 가 cat.
            droptable.dat = **EquipItem drop pool** (potion 아님)
  byte 12 = 13 unique, 0xff=104 (sentinel = strb skip)

NewDropItem args 매핑 (Round 30 register propagation 추적):
  r3 (cat) = signed s8 of byte 11
  arg5..arg12 (sp+0..sp+0x1c) = stack args (idx, val_15c, val_15f, val_162, val_160,
    val_163, val_161, val_164) — 정확한 byte→arg 매핑은 추가 검증 필요 (Round 31).

각 entry = monster 의 한 drop_tier 의 EquipItem (helmet/boots/accessory + sentinel default).
무기 (cat 0..3) drop 이 droptable.dat 에 없는 이유: 무기 drop 은 별도 메커니즘 (Quest reward,
Treasure chest, 또는 default tier의 generic drop).

산출:
  apps/hero5-godot/assets/gamedata/droptable.json
"""
from __future__ import annotations
import csv, json, pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'droptable.json'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'


def djb2(s: bytes) -> int:
    h = 0x1505
    for c in s: h = (c + h * 0x21) & 0xFFFFFFFF
    return h


def find_droptable() -> pathlib.Path | None:
    target = djb2(b'c/csv/droptable.dat')
    with open(CATALOG, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if int(r['hash'], 16) == target:
                idx = int(r['index'])
                return ENTRIES / f'{idx:05d}_{target:08x}.bin'
    return None


def parse(data: bytes) -> dict:
    count = struct.unpack_from('<H', data, 0)[0]
    expected = 2 + count * 13
    if expected != len(data):
        return {'error': f'size mismatch: got {len(data)}, expected {expected}'}

    # Round 30: byte 11 = cat (NewDropItem r3 arg, signed s8)
    CAT_LABELS = {
        5: 'helmet', 6: 'boots', 7: 'accessory', 8: 'accessory_2',
        0xff: 'default',  # NewDropItem default branch → EquipItemInfo (376B)
    }
    entries = []
    monsters: dict[int, list[dict]] = {}
    for i in range(count):
        e = data[2 + i * 13: 2 + (i + 1) * 13]
        cat = e[11]
        cat_signed = cat - 256 if cat >= 0x80 else cat  # signed s8
        rec = {
            'idx': i,
            'marker':      e[0],   # 항상 0x0b (constant marker)
            'sub_flag':    e[1],   # 항상 0x00
            'monster_idx': e[2],   # 0..62
            'drop_tier':   e[3],   # 4 unique (0x0e..0x11)
            'cat': cat_signed,     # NewDropItem r3 arg ← Round 30 핵심
            'cat_label': CAT_LABELS.get(cat, f'cat_{cat}'),
            'b4': e[4], 'b5': e[5], 'b6': e[6], 'b7': e[7], 'b8': e[8],
            'b9': e[9],            # 0xff = sentinel (NewDropItem arg strb skip)
            'b10': e[10],
            'b12': e[12],          # 0xff = sentinel
            'hex': e.hex(),
        }
        entries.append(rec)
        monsters.setdefault(e[2], []).append(rec)

    return {
        'meta': {
            'source': 'c/csv/droptable.dat',
            'vfs_index': 18,
            'count': count,
            'monsters': len(monsters),
            'entries_per_monster': max(len(v) for v in monsters.values()),
            'note': 'See decode_h5_droptable.py docstring for byte layout details.',
        },
        'entries': entries,
        'by_monster': {str(k): v for k, v in sorted(monsters.items())},
    }


def main() -> int:
    p = find_droptable()
    if not p:
        print('droptable.dat not found in VFS catalog')
        return 1
    if not p.exists():
        print(f'{p} missing — run h5_vfs_unpack.py first')
        return 1
    data = p.read_bytes()
    result = parse(data)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    meta = result.get('meta', {})
    print(f'wrote {OUT}')
    print(f'  count={meta.get("count")}, monsters={meta.get("monsters")}, entries/monster={meta.get("entries_per_monster")}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
