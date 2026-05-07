"""
drop/shop/smith/quest/rewards 디코더.

테이블별 포맷:
  droptable.dat (252×11B): u8 item_id, u8 ?, u8 type1, u8 type2, u8 ?,
                            u8 rate, u8 mp_cost, u8 ?, u8 ?, u16 0xFFFF
                            → enemy 의 drop list 추정
  shop_NN.dat (9×10B):     상점 판매 아이템 entry
  smith_NN.dat (96 entries): 가변사이즈 (대장간 레시피)
  quest_NN.dat (151 entries): 가변사이즈 + Korean 설명 (퀘스트 진행 텍스트)
  rewards_NN.dat (95 entries): 가변사이즈 (보상 entry)
  N_rewards_M.dat (194B 고정): per-game per-act rewards

산출:
  apps/hero5-godot/assets/gamedata/drops.json
  apps/hero5-godot/assets/gamedata/shops.json
  apps/hero5-godot/assets/gamedata/smiths.json
  apps/hero5-godot/assets/gamedata/quests_text.json
  apps/hero5-godot/assets/gamedata/rewards.json
"""
from __future__ import annotations
import csv, pathlib, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'
OUT_DIR = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata'


def djb2(s: bytes) -> int:
    h = 0x1505
    for c in s: h = (c + h * 0x21) & 0xFFFFFFFF
    return h


def find(name: str) -> pathlib.Path | None:
    target = djb2(name.encode())
    for r in csv.DictReader(open(CATALOG, encoding='utf-8'), delimiter='\t'):
        if int(r['hash'], 16) == target:
            return ENTRIES / f'{int(r["index"]):05d}_{target:08x}.bin'
    return None


def parse_var_records(d: bytes) -> list[dict]:
    """표준 가변 csv: u16 count + records[u16 size, body]."""
    if len(d) < 2: return []
    count = struct.unpack_from('<H', d, 0)[0]
    pos = 2
    out = []
    for i in range(count):
        if pos + 2 > len(d): break
        sz = struct.unpack_from('<H', d, pos)[0]; pos += 2
        if pos + sz > len(d): break
        body = d[pos:pos + sz]; pos += sz
        # body[0] = strlen if record has name
        if body and body[0] < sz:
            strlen = body[0]
            try:
                name = body[1:1+strlen].decode('euc-kr', errors='replace')
            except: name = ''
            extra = body[1+strlen:]
        else:
            name = ''
            extra = body
        # also try EUC-KR decode of full extra (some tables embed text without strlen)
        try:
            korean_in_extra = []
            i = 0
            while i < len(extra) - 1:
                if 0xb0 <= extra[i] <= 0xc8 and 0xa1 <= extra[i+1] <= 0xfe:
                    j = i
                    while j < len(extra) - 1 and (
                            (0xb0 <= extra[j] <= 0xc8 and 0xa1 <= extra[j+1] <= 0xfe) or
                            extra[j] in (0x20, 0x3b)):
                        j += 2
                    if j - i >= 4:
                        try:
                            korean_in_extra.append(extra[i:j].decode('euc-kr', errors='replace'))
                        except: pass
                    i = j
                else:
                    i += 1
        except: korean_in_extra = []
        out.append({
            'idx': i,
            'name': name,
            'korean': korean_in_extra,
            'extra_hex': extra.hex(),
        })
    return out


def parse_fixed(d: bytes, rec_size: int) -> list[dict]:
    if len(d) < 2: return []
    count = struct.unpack_from('<H', d, 0)[0]
    out = []
    for i in range(count):
        off = 2 + i * rec_size
        if off + rec_size > len(d): break
        rec = d[off:off + rec_size]
        n_u16 = rec_size // 2
        u16 = list(struct.unpack(f'<{n_u16}H', rec[:n_u16*2]))
        out.append({'idx': i, 'hex': rec.hex(), 'u8': list(rec), 'u16_le': u16})
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # droptable.dat - 252 × 11B
    p = find('c/csv/droptable.dat')
    if p:
        d = p.read_bytes()
        # custom: 2B count + 252 × 11B... but wait, total = 2+252*13 = 3278 ✓
        # so it's u16 count + per-record 13B (with size header 2B per record?)
        # Let me just use parse_var_records first to check
        items = parse_fixed(d, 13)  # try 13 (including size header)
        # if first record sz looks weird try 11
        out = parse_var_records(d)
        (OUT_DIR / 'drops.json').write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'drops: {len(out)} records')

    # shops
    shops = []
    for n in range(3):
        p = find(f'c/csv/shop_{n}.dat')
        if not p: continue
        recs = parse_var_records(p.read_bytes())
        shops.append({'shop_id': n, 'records': recs})
    (OUT_DIR / 'shops.json').write_text(
        json.dumps(shops, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'shops: {len(shops)} shops')

    # smiths
    smiths = []
    for n in range(3):
        p = find(f'c/csv/smith_{n}.dat')
        if not p: continue
        recs = parse_var_records(p.read_bytes())
        smiths.append({'smith_id': n, 'records': recs})
    (OUT_DIR / 'smiths.json').write_text(
        json.dumps(smiths, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'smiths: {len(smiths)} smiths')

    # quests_text — quest_0.dat 의 한글 (퀘스트 진행 / NPC 대사)
    quests_text = []
    for n in range(3):
        p = find(f'c/csv/quest_{n}.dat')
        if not p: continue
        recs = parse_var_records(p.read_bytes())
        quests_text.append({'episode': n, 'records': recs})
    (OUT_DIR / 'quests_text.json').write_text(
        json.dumps(quests_text, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'quests_text: {sum(len(q["records"]) for q in quests_text)} records')

    # rewards
    rewards = []
    for n in range(3):
        p = find(f'c/csv/rewards_{n}.dat')
        if not p: continue
        recs = parse_var_records(p.read_bytes())
        rewards.append({'tier': n, 'records': recs})
    (OUT_DIR / 'rewards.json').write_text(
        json.dumps(rewards, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'rewards: {sum(len(r["records"]) for r in rewards)} records')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
