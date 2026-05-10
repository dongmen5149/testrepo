"""
droptable.dat 디코더 (Round 29 — 2026-05-10).

Round 27 에서 Monster::SetDropItem 분석으로 drop_table 의 13-byte entry 구조
가설 발견. Round 29 에서 LoadItemDropTable 분석으로 데이터 위치 확정:
  ItemTable::LoadItemDropTable (0xa0b54) → LoadRes("/c/csv/droptable.dat")
  → ItemTable+0x214 = drop_table_ptr

VFS index 18, hash 0xe58e8176, 3278 byte.

Layout:
  u16 count = 252
  records 252 × 13 byte:
    byte 0 = 0x0b (cat=11, potion drop pool — all 252 entries 일관)
    byte 1 = 0x00 (sub-flag, all 252 entries 일관)
    byte 2 = monster_idx (0..62, 4 entries per monster)
    byte 3 = drop_type (0x0e/0x0f/0x10/0x11, 4 distinct = 4 drop tiers per monster)
    byte 4..12 = NewDropItem args 후보 (cat, idx, val_15c, val_15f, val_162, val_160, val_163, val_161, val_164)
      정확한 매핑은 SetDropItem caller 1 (0xbcc74) 의 register propagation 추적 필요.
      - byte 9 = 절반 0xff (sentinel = NewDropItem strb skip — value < 0)
      - byte 11 = 절반 0xff (같은 sentinel)
      - byte 4 ≈ byte 6 (값 빈도 동일 — paired drop?)

→ 252 entries = **63 monsters × 4 drop entries** (potion drop pool).
→ Monster 의 다른 cat drop (EquipItem 등) 은 droptable.dat 와 별개 메커니즘 일 가능성
  (caller 2 의 cat=0xe mix material drop 은 별도 path — Round 27).

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

    entries = []
    monsters: dict[int, list[dict]] = {}
    for i in range(count):
        e = data[2 + i * 13: 2 + (i + 1) * 13]
        rec = {
            'idx': i,
            'cat':         e[0],   # 항상 0x0b (potion)
            'sub_idx':     e[1],   # 항상 0x00
            'monster_idx': e[2],   # 0..62
            'drop_tier':   e[3],   # 4 unique (0x0e..0x11)
            'b4': e[4],
            'b5': e[5],
            'b6': e[6],
            'b7': e[7],
            'b8': e[8],
            'b9': e[9],            # 0xff = sentinel (NewDropItem strb skip)
            'b10': e[10],
            'b11': e[11],          # 0xff = sentinel
            'b12': e[12],
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
