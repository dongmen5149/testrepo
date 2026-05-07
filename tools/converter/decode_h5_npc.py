"""
npc_g.dat 27B record 디코더.

근거: Map::MapNpcG_set @ 000be6c8.

레코드 구조 (27B per record):
  offset 0..1: payload size header (= 25, 즉 stride=27)
  offset 2..12: 11 u8 (sprite/dir/anim params)
  offset 13..14: u16 LE — stat 1 (대화ID 추정)
  offset 15..16: u16 LE — stat 2 (action ID)
  offset 17..18: u16 LE — stat 3
  offset 19..20: u16 LE — stat 4
  offset 21..22: u16 LE — stat 5
  offset 23..24: u16 LE — stat 6
  offset 25..26: u16 LE — stat 7

산출:
  apps/hero5-godot/assets/gamedata/npc_table.json
"""
from __future__ import annotations
import pathlib, csv, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'npc_table.json'


def main() -> int:
    p = None
    with open(NAMES, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['recovered_name'] == 'c/csv/npc_g.dat':
                p = ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"], 16):08x}.bin'
    if p is None: return 1
    d = p.read_bytes()
    count = struct.unpack_from('<H', d, 0)[0]
    payload_sz = struct.unpack_from('<H', d, 2)[0]
    stride = payload_sz + 2
    print(f'npc_g.dat: {count} × {stride}B (payload {payload_sz})')

    out = []
    for i in range(count):
        off = 4 + i * stride
        rec = d[off:off + stride]
        if len(rec) < 25: continue
        info = {
            'idx': i,
            'flags': list(rec[0:11]),
            'stat1': struct.unpack_from('<H', rec, 11)[0],
            'stat2': struct.unpack_from('<H', rec, 13)[0],
            'stat3': struct.unpack_from('<H', rec, 15)[0],
            'stat4': struct.unpack_from('<H', rec, 17)[0],
            'stat5': struct.unpack_from('<H', rec, 19)[0],
            'stat6': struct.unpack_from('<H', rec, 21)[0],
            'stat7': struct.unpack_from('<H', rec, 23)[0],
            'hex':   rec.hex(),
        }
        out.append(info)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {OUT}')

    valid = [r for r in out if r['stat1'] != 0xFFFF or r['flags'][0] != 0xFF]
    print(f'valid records: {len(valid)}/{len(out)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
