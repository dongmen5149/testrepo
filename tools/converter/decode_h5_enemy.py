"""
enemy_g.dat 121B record 디코더.

근거 (.so disasm 검증 — Map::MapEnemyG_set @ 0x000ae394 + ByteToInt16):
  - record stride = 121 (header 4B + 121*166 records)
  - record byte 0x00..0x0b → struct[0x00..0x0b]: 12 × u8 (sprite/anim/AI flags)
  - record byte 0x0c..0x17 → struct[0x0c..0x17]: 6 × u16 LE (StaticUtil::ByteToInt16)
      0x0c..0x0d: HP    0x0e..0x0f: MP
      0x10..0x11: ATK   0x12..0x13: DEF
      0x14..0x15: stat5 (EXP 후보)   0x16..0x17: stat6 (Gold 후보)
  - record byte 0x18..0x23 → struct[0x18..0x23]: 12 × u8 (flags_b — element/resist)
  - record byte 0x24..0x77 → 5 × 16B 스킬 슬롯 (8 × u16 each)
  - StaticUtil::ByteToInt16 = `buf[off] | (buf[off+1]<<8)` = LE u16

검증: 65535 sentinel 빈도 = enemy_g 가 sparse (게임이 일부 record 만 사용).

산출:
  apps/hero5-godot/assets/gamedata/enemy_table.json
"""
from __future__ import annotations
import pathlib, csv, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'enemy_table.json'


def find_path(target: str) -> pathlib.Path:
    with open(NAMES, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['recovered_name'] == target:
                return ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"],16):08x}.bin'
    raise FileNotFoundError(target)


def decode_record(r: bytes) -> dict:
    if len(r) < 0x24: return {}
    # .so disasm 검증된 layout (record-relative byte offsets):
    return {
        'flags_a': list(r[0:12]),                              # u8 × 12
        'hp':      struct.unpack_from('<H', r, 0x0c)[0],
        'mp':      struct.unpack_from('<H', r, 0x0e)[0],
        'atk':     struct.unpack_from('<H', r, 0x10)[0],
        'def':     struct.unpack_from('<H', r, 0x12)[0],
        'exp':     struct.unpack_from('<H', r, 0x14)[0],       # stat5 후보
        'gold':    struct.unpack_from('<H', r, 0x16)[0],       # stat6 후보
        'flags_b': list(r[0x18:0x24]),                         # u8 × 12 (resist/element)
        'skills':  [
            list(struct.unpack_from('<8H', r, 0x24 + i * 16))
            for i in range(5) if 0x24 + (i + 1) * 16 <= len(r)
        ],
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    p = find_path('c/csv/enemy_g.dat')
    d = p.read_bytes()
    count = struct.unpack_from('<H', d, 0)[0]
    payload_sz = struct.unpack_from('<H', d, 2)[0]
    rec_size = payload_sz + 2  # stride includes the 2B size field per Map::MapEnemyG_set
    # Actually the sz_field is for ALL records (single global size at offset 2), records START at 4.
    # Stride per record = payload_sz + 2 = 121.
    print(f'enemy_g.dat: {count} records × stride={rec_size}B (payload_sz={payload_sz})')

    out = []
    for i in range(count):
        off = 4 + i * rec_size
        rec = d[off:off + rec_size]
        info = decode_record(rec)
        info['idx'] = i
        info['hex'] = rec.hex()
        out.append(info)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'wrote {OUT}')

    # show stats summary
    valid = [r for r in out if 0 < r['hp'] < 65535]
    valid_atk = [r for r in valid if 0 < r['atk'] < 65535]
    valid_def = [r for r in valid if 0 < r['def'] < 65535]
    print(f'\nvalid: HP {len(valid)}/{len(out)}  '
          f'ATK {len(valid_atk)}  DEF {len(valid_def)}')
    if valid_atk:
        a = sorted(r['atk'] for r in valid_atk)
        print(f'  ATK range: {a[0]} .. {a[-1]}  median={a[len(a)//2]}')
    if valid_def:
        d_ = sorted(r['def'] for r in valid_def)
        print(f'  DEF range: {d_[0]} .. {d_[-1]}  median={d_[len(d_)//2]}')
    print('\nfirst 12 valid enemies:')
    for r in valid[:12]:
        print(f'  #{r["idx"]:3d}  HP={r["hp"]:5d} MP={r["mp"]:5d} '
              f'ATK={r["atk"]:5d} DEF={r["def"]:5d} EXP={r["exp"]:5d} Gold={r["gold"]:5d}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
