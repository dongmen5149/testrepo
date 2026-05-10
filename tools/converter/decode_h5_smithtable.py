"""
smith_NN.dat 디코더 (Round 32 — 2026-05-10).

Round 28 에서 ApplyNormalMix 의 MixSmithTableInfo* 사용 발견 — csv slot_15 와 별개.
Round 32 에서 출처 식별:
  HERO::LoadMixSmithTableInfo (0x8b958, 588B) → LoadRes("/c/csv/smith_%d.dat", arg)
  → HERO+0x1d00 = MixSmithTable_ptr (alloc count*0x12c bytes)
  arg = smith table index. 발견된 파일: smith_0/1/2.dat (각 96 entries × 300B/entry).

VFS:
  smith_0.dat: index=70, hash 0x70fbe64d, 5567B, 96 entries
  smith_1.dat: index=71, hash 0x710dfece, 6302B, 96 entries
  smith_2.dat: index=72, hash 0x7120174f, 6287B, 96 entries

File layout (per entry, after u16 count):
  u16 record_size
  u16 prefix (icon_id 또는 sub-id)
  u8 strlen
  bytes[strlen] name (EUC-KR)
  u32 item_id → struct +0x18
  u8 sub_record_len
  bytes[sub_record_len] sub_record → struct +0x1c..+0x11c (256B padded memset+memcpy)
  13-byte smith data → struct +0x11c..+0x128:
    byte 0  = option_grade → struct +0x11c
    bytes 1-3 = ingredient 1 (cat, idx, count) → struct +0x11d/+0x120/+0x123 (column-major!)
    bytes 4-6 = ingredient 2 → struct +0x11e/+0x121/+0x124
    bytes 7-9 = ingredient 3 → struct +0x11f/+0x122/+0x125
    byte 10 = result_cat → struct +0x126
    byte 11 = result_idx → struct +0x127
    byte 12 = success_rate → struct +0x128

→ smith data 13-byte = mix_book recipe (slot_15) 와 동일 layout. csv 가 row-major,
  struct memory 가 column-major (LoadMixSmithTableInfo 가 transpose).

산출:
  apps/hero5-godot/assets/gamedata/smithtable.json
"""
from __future__ import annotations
import csv, json, pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'smithtable.json'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'


def djb2(s: bytes) -> int:
    h = 0x1505
    for c in s: h = (c + h * 0x21) & 0xFFFFFFFF
    return h


def find_smith(idx: int) -> pathlib.Path | None:
    target = djb2(f'c/csv/smith_{idx}.dat'.encode())
    with open(CATALOG, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if int(r['hash'], 16) == target:
                vidx = int(r['index'])
                return ENTRIES / f'{vidx:05d}_{target:08x}.bin'
    return None


def parse_ingredient(c: int, i: int, ct: int) -> dict | None:
    if c == 0xff:
        return None
    return {'cat': c, 'idx': i, 'count': ct}


def parse_smith(data: bytes) -> dict:
    if len(data) < 2:
        return {'error': 'too small'}
    count = struct.unpack_from('<H', data, 0)[0]
    pos = 2
    entries = []
    for i in range(count):
        if pos + 5 > len(data):
            break
        rec_sz = struct.unpack_from('<H', data, pos)[0]; pos += 2
        body_start = pos
        if pos + rec_sz > len(data):
            break
        prefix = struct.unpack_from('<H', data, pos)[0]; pos += 2
        strlen = data[pos]; pos += 1
        if strlen > rec_sz - 3:
            pos = body_start + rec_sz
            entries.append({'idx': i, 'name': '?', 'prefix': prefix})
            continue
        try:
            name = data[pos:pos + strlen].decode('euc-kr', errors='replace')
        except Exception:
            name = ''
        pos += strlen
        extra_len = rec_sz - 3 - strlen
        extra = data[pos:pos + extra_len]
        pos += extra_len

        rec = {
            'idx': i,
            'name': name,
            'prefix': prefix,
        }

        # extra: u32 item_id + u8 sub_record_len + sub_record + 13 byte smith data
        if len(extra) >= 5:
            item_id = struct.unpack_from('<I', extra, 0)[0]
            sblen = extra[4]
            rec['item_id'] = item_id
            rec['sub_record_len'] = sblen
            sb_start = 5 + sblen
            if sb_start + 13 <= len(extra):
                sb = extra[sb_start:sb_start + 13]
                rec['option_grade'] = sb[0]
                rec['recipe'] = {
                    'ing1': parse_ingredient(sb[1], sb[2], sb[3]),
                    'ing2': parse_ingredient(sb[4], sb[5], sb[6]),
                    'ing3': parse_ingredient(sb[7], sb[8], sb[9]),
                    'result_cat': sb[10],
                    'result_idx': sb[11],
                    'success_rate': sb[12],
                }
                rec['smith_hex'] = sb.hex()

        entries.append(rec)
    return {
        'count': count,
        'entries': entries,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    all_tables: dict = {'_meta': {'note': 'See decode_h5_smithtable.py docstring.'}}
    total = 0
    for n in range(5):
        p = find_smith(n)
        if not p:
            continue
        if not p.exists():
            print(f'  smith_{n}: file missing ({p})')
            continue
        result = parse_smith(p.read_bytes())
        all_tables[f'smith_{n}'] = result
        named = sum(1 for e in result.get('entries', []) if e.get('name', '?') != '?' and e.get('name'))
        total += named
        print(f'  smith_{n}.dat: {result.get("count")} entries, {named} named')
        # 첫 3 sample
        for e in result.get('entries', [])[:3]:
            r = e.get('recipe', {})
            ings = [e.get('recipe', {}).get(f'ing{i}') for i in (1, 2, 3)]
            ings_str = ' + '.join(f'(cat={i["cat"]},idx={i["idx"]},×{i["count"]})' if i else '-' for i in ings)
            print(f"    [{e.get('idx'):3d}] {e.get('name','?'):>15s}  {ings_str} → ({r.get('result_cat','?')},{r.get('result_idx','?')}) sr={r.get('success_rate','?')}")

    OUT.write_text(json.dumps(all_tables, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT} (total {total} named smith recipes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
