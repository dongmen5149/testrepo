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

slot_N → ItemTable category (분석 결과, ITEM_STRUCT.md 참조):
  slot_0..slot_10 = EquipItemInfo (weapon/armor/etc, 376B runtime record)
  slot_11        = (unused / reserved)
  slot_12        = BattleUseItemInfo (potion/scroll, 312B)
  slot_13        = OrbItemInfo (gem/orb, 312B)
  slot_14, 15    = MixItemInfo (alchemy material, 308B)
  slot_16        = MixBookItemInfo (recipe book, 324B)
  slot_17, 18    = SkillBookItemInfo (skill book, 312B)
  slot_19        = CashItemInfo (premium item, 312B)

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

# slot_N → 카테고리 메타데이터 (ItemTable::GetItemTableInfo dispatch 참조)
SLOT_META = {
    0:  {"category": "equip", "kind": "weapon",       "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    1:  {"category": "equip", "kind": "weapon_2",     "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    2:  {"category": "equip", "kind": "weapon_3",     "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    3:  {"category": "equip", "kind": "weapon_4",     "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    4:  {"category": "equip", "kind": "armor",        "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    5:  {"category": "equip", "kind": "helmet",       "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    6:  {"category": "equip", "kind": "boots",        "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    7:  {"category": "equip", "kind": "accessory",    "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    8:  {"category": "equip", "kind": "accessory_2",  "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    9:  {"category": "equip", "kind": "shield",       "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    10: {"category": "equip", "kind": "spirit",       "runtime_struct": "EquipItemInfo",      "runtime_size": 376},
    11: {"category": "battle_use", "kind": "potion",  "runtime_struct": "BattleUseItemInfo",  "runtime_size": 312},
    12: {"category": "battle_use", "kind": "scroll",  "runtime_struct": "BattleUseItemInfo",  "runtime_size": 312},
    13: {"category": "orb",       "kind": "orb",      "runtime_struct": "OrbItemInfo",        "runtime_size": 312},
    14: {"category": "mix",       "kind": "material", "runtime_struct": "MixItemInfo",        "runtime_size": 308},
    15: {"category": "mix",       "kind": "material_2", "runtime_struct": "MixItemInfo",      "runtime_size": 308},
    16: {"category": "mix_book",  "kind": "recipe",   "runtime_struct": "MixBookItemInfo",    "runtime_size": 324},
    17: {"category": "skill_book", "kind": "skill_book", "runtime_struct": "SkillBookItemInfo", "runtime_size": 312},
    18: {"category": "skill_book", "kind": "skill_book_2", "runtime_struct": "SkillBookItemInfo", "runtime_size": 312},
}


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
        # 주의 (Round 13): csv extra 는 압축된 stat data (33..80 byte) — in-memory
        # EquipItemInfo struct (376B) 와 layout 다름. ItemTable::GetItemTableInfo 가
        # csv stat 들을 EquipItemInfo offset 에 store 하는 매핑은 다음 라운드 RE 필요.
        # 현재 stats_u16 순서:
        #   stats_u16[0] = 가격 (gold)
        #   stats_u16[1] = pad/flags
        #   stats_u16[2..] = stat 들 (정확한 의미 = csv→struct 매핑 후 결정)
        out.append({
            'idx': i,
            'name': name,
            'prefix': prefix,    # icon_id 또는 category
            'price': u16[0] if u16 else 0,
            'stats_u16': u16,
            'extra_hex': extra.hex(),
        })
    return out


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    # 호환성: 기존 GameData loader 가 data["slot_N"] 직접 접근. 평면 구조 유지하고
    # 메타데이터는 별도 key 로.
    all_items: dict = {"_meta": {"category_dispatch": SLOT_META}}
    total = 0
    for slot in range(19):  # item_00..item_18
        p = find(f'c/csv/item_{slot:02d}.dat')
        if not p: continue
        items = parse_items(p.read_bytes())
        all_items[f'slot_{slot}'] = items
        meta = SLOT_META.get(slot, {})
        named = sum(1 for x in items if x.get('name', '').strip() and x['name'] != '?')
        total += named
        print(f'item_{slot:02d} ({meta.get("kind", "?"):<14}): {len(items)} records, {named} named')
        for x in items[:5]:
            print(f'  prefix=0x{x.get("prefix",0):04x}  price={x.get("price", 0):>4}  {x.get("name","?")!r}  stats={x.get("stats_u16",[])[:6]}')

    OUT.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT} (total {total} named items)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
