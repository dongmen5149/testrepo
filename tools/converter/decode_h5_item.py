"""
item_NN.dat 디코더.

표준 csv 와 다른 포맷:
  u16 count
  records:
    u16 record_size
    u16 prefix (icon_id 또는 item_category 추정)
    u8 strlen
    bytes[strlen] (EUC-KR 이름)
    bytes[record_size - 3 - strlen] (stats)

검증 (item_00.dat 첫 record):
  count=86, size=0x2a (42), prefix=0xc7 (199), strlen=6, "롱소드", extra=33B

산출:
  apps/hero5-godot/assets/gamedata/items.json
"""
from __future__ import annotations
import csv, pathlib, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'items.json'


CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'


def djb2(s: bytes) -> int:
    h = 0x1505
    for c in s: h = (c + h * 0x21) & 0xFFFFFFFF
    return h


def find_by_hash(name: str) -> pathlib.Path | None:
    """asset_names.tsv 가 false-positive 인 경우 (item_NN 등) catalog 에서
    hash 직접 매칭."""
    target_h = djb2(name.encode())
    with open(CATALOG, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if int(r['hash'], 16) == target_h:
                idx = int(r['index'])
                return ENTRIES / f'{idx:05d}_{target_h:08x}.bin'
    return None


def find(target: str) -> pathlib.Path | None:
    return find_by_hash(target)


def parse_items(d: bytes) -> list[dict]:
    if len(d) < 2: return []
    count = struct.unpack_from('<H', d, 0)[0]
    pos = 2
    out = []
    for i in range(count):
        if pos + 5 > len(d): break
        rec_sz = struct.unpack_from('<H', d, pos)[0]; pos += 2
        if pos + rec_sz > len(d): break
        body_start = pos
        prefix = struct.unpack_from('<H', d, pos)[0]; pos += 2
        strlen = d[pos]; pos += 1
        if strlen > rec_sz - 3:
            pos = body_start + rec_sz
            out.append({'idx': i, 'name': '?', 'prefix': prefix, 'extra_hex': ''})
            continue
        try:
            name = d[pos:pos + strlen].decode('euc-kr', errors='replace')
        except Exception:
            name = ''
        pos += strlen
        extra_len = rec_sz - 3 - strlen
        extra = d[pos:pos + extra_len]
        pos += extra_len
        # extra 는 stat fields (u16 LE 배열)
        n_u16 = len(extra) // 2
        u16 = list(struct.unpack(f'<{n_u16}H', extra[:n_u16*2])) if n_u16 else []
        out.append({
            'idx': i,
            'name': name,
            'prefix': prefix,    # icon_id 또는 category
            'stats_u16': u16,
            'extra_hex': extra.hex(),
        })
    return out


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    all_items: dict[str, list] = {}
    total = 0
    for slot in range(19):  # item_00..item_18
        p = find(f'c/csv/item_{slot:02d}.dat')
        if not p: continue
        items = parse_items(p.read_bytes())
        all_items[f'slot_{slot}'] = items
        named = sum(1 for x in items if x.get('name', '').strip() and x['name'] != '?')
        total += named
        print(f'item_{slot:02d}: {len(items)} records, {named} named')
        for x in items[:5]:
            print(f'  prefix=0x{x.get("prefix",0):04x}  {x.get("name","?")!r}  stats={x.get("stats_u16",[])[:6]}')

    OUT.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT} (total {total} named items)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
