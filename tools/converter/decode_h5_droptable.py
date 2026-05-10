"""
droptable.dat 디코더.

Round 27 → Round 31 분석 종합:
  ItemTable::LoadItemDropTable (0xa0b54) → LoadRes("/c/csv/droptable.dat")
  → ItemTable+0x214 = drop_table_ptr
  Monster::SetDropItem (0xbc910) 안에서 random drop_tier 선택 후 NewDropItem 호출.

VFS index 18, hash 0xe58e8176, 3278 byte.

Layout (u16 count + 252 × 13 byte = 63 monsters × 4 drop tiers):
  byte 0  = 0x0b (constant marker — 모든 252 entries 일관)
  byte 1  = 0x00 (sub-flag — 모든 252 일관)
  byte 2  = monster_idx (0..62, 4 entries 단위)
  byte 3  = drop_tier (0x0e/0x0f/0x10/0x11, 4 unique = 4 tier per monster)
  byte 4  = 12 unique values, byte 6 와 동일 분포 (paired)
  byte 5  = 20 unique values (idx 또는 stat 후보)
  byte 6  = 12 unique values, byte 4 와 paired
  byte 7  = **default path cat (NewDropItem r3 arg)** ✅ Round 31 발견:
              cat 0..9 EquipItem cats (cat 4=armor 제외, 12 sentinel)
              0=weapon(28) / 1=weapon_2(28) / 2=weapon_3(27) / 3=weapon_4(28) /
              5=helmet(25) / 6=boots(26) / 7=accessory(26) / 8=accessory_2(24) /
              9=shield(28) / 0xff(=-1, default branch)(12)
              **cat 4 누락 = Round 22 Sorcerer 미구현 stub cross-confirm**
  byte 8  = 25 unique (idx 또는 stat)
  byte 9  = 7 unique, 0xff=108 (sentinel)
  byte 10 = 30 unique, 0x00=112 (val_163 또는 zero default)
  byte 11 = **highest-tier path cat (NewDropItem r3 arg, 별도 path)** ✅ Round 30:
              0x05 (helmet) 27 / 0x06 (boots) 14 / 0x07 (accessory) 61 /
              0x08 (accessory_2) 46 / 0xff (default) 104
              → 보스급 monster 의 specific accessory drop tier
  byte 12 = 13 unique, 0xff=104 (sentinel)

Monster::SetDropItem 의 드롭 결정 로직 (Round 31 정밀 추적):
  - Rand(0,0xffff) → r0
  - if r0 < Monster.+0x254: skip (no drop)
  - elif r0 < Monster.+0x258 (0xbcca8 path): cat = Rand(0,9) (random EquipItem cat)
  - elif r0 < Monster.+0x25c (0xbccf8 path): cat = Rand(0,9) variant
  - elif r0 < Monster.+0x260 (0xbcda0 path): cat = Rand(0,9) variant
  - elif r0 < Monster.+0x264 (0xbcb54 default fall-through): **cat = byte 7** (specific)
  - elif r0 < Monster.+0x268 (0xbcd60 path): high-tier mix
  - elif r0 < Monster.+0x26c (0xbce24 path): **cat = byte 11** (highest tier)
  - else: skip
  - Each path sets various sp slots that NewDropItem reads as args (idx, val_15c, etc).
  - Final NewDropItem call at 0xbcc74 (caller 1) reached if Monster +0x271 != -1.
  - Caller 2 (0xbcf30) at function end: cat=0xe (mix material) drop, prob ~40%.

cat 매핑 의미:
  - byte 7 = "common drop cat" — random pick from monster's 4 entries × 4 tiers
  - byte 11 = "rare drop cat" — specific accessory drop in highest tier
  - 0xff = NewDropItem default branch = generic EquipItem (376B alloc, no specific cat)

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

    # Round 30/31: byte 7 = default path cat, byte 11 = highest tier path cat
    CAT_LABELS = {
        0: 'weapon', 1: 'weapon_2', 2: 'weapon_3', 3: 'weapon_4',
        4: 'armor',  # Sorcerer 미구현 (Round 22) — droptable 에는 없음
        5: 'helmet', 6: 'boots', 7: 'accessory', 8: 'accessory_2',
        9: 'shield', 10: 'spirit',
        0xff: 'default',  # NewDropItem default branch → EquipItemInfo (376B)
    }
    def label(b: int) -> str:
        if b >= 0x80:
            return CAT_LABELS.get(b, f'sentinel_{b}')
        return CAT_LABELS.get(b, f'cat_{b}')

    entries = []
    monsters: dict[int, list[dict]] = {}
    for i in range(count):
        e = data[2 + i * 13: 2 + (i + 1) * 13]
        cat_default = e[7] - 256 if e[7] >= 0x80 else e[7]
        cat_rare = e[11] - 256 if e[11] >= 0x80 else e[11]
        rec = {
            'idx': i,
            'marker':      e[0],   # 항상 0x0b (constant marker)
            'sub_flag':    e[1],   # 항상 0x00
            'monster_idx': e[2],   # 0..62
            'drop_tier':   e[3],   # 4 unique (0x0e..0x11)
            'cat_default': cat_default,        # byte 7 — common drop cat (Round 31)
            'cat_default_label': label(e[7]),
            'cat_rare':    cat_rare,           # byte 11 — highest-tier drop cat (Round 30)
            'cat_rare_label':   label(e[11]),
            'b4': e[4], 'b5': e[5], 'b6': e[6], 'b8': e[8],
            'b9': e[9],            # 0xff = sentinel
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
