"""
enemy_g.dat 121B record 디코더.

근거: Map::MapEnemyG_set @ 000be394 디컴파일 (work/h5/analysis/monster_load.c).

레코드 구조 (121B per record):
  offset 0x00..0x03: 헤더/패딩 (size 정보, ByteToInt16 가 처음 2B 읽음)
  offset 0x04..0x0f: 12개 u8 필드 (sprite/anim/AI flags 추정)
  offset 0x10..0x11: u16 LE — HP
  offset 0x12..0x13: u16 LE — MP/SP
  offset 0x14..0x15: u16 LE — Attack
  offset 0x16..0x17: u16 LE — Defense
  offset 0x18..0x19: u16 LE — EXP reward
  offset 0x1a..0x1b: u16 LE — Gold reward
  offset 0x1c..0x2a: 15개 u8 (resistance/element flags)
  offset 0x2b..0x7a: 5 × 16B 서브레코드 (스킬 슬롯 5개; 각 = 8 u16)

(필드 의미 정확한 확정은 BATTLER 의 setHP/setAtk 등 추가 분석 필요)

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
    if len(r) < 39: return {}
    # Field offsets within record (record starts at file offset 4 after count+sz header):
    return {
        'flags_a': list(r[0:12]),           # 12 u8 (sprite/anim/AI)
        'hp':      struct.unpack_from('<H', r, 12)[0],
        'mp':      struct.unpack_from('<H', r, 14)[0],
        'stat3':   struct.unpack_from('<H', r, 16)[0],   # ATK 추정
        'stat4':   struct.unpack_from('<H', r, 18)[0],   # DEF 추정
        'stat5':   struct.unpack_from('<H', r, 20)[0],   # EXP/lvl 추정
        'stat6':   struct.unpack_from('<H', r, 22)[0],   # GOLD/AI type 추정
        'flags_b': list(r[24:39]),          # 15 u8
        'skills':  [
            list(struct.unpack_from('<8h', r, 39 + i * 16))
            for i in range(5) if 39 + (i + 1) * 16 <= len(r)
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
    print(f'\nfirst 8 enemies:')
    for r in out[:8]:
        print(f'  #{r["idx"]:3d}  HP={r["hp"]:5d} MP={r["mp"]:4d} '
              f'stat3={r["stat3"]:5d} stat4={r["stat4"]:5d} '
              f'stat5={r["stat5"]:5d} stat6={r["stat6"]:5d}')
    print('\nstrongest enemies (by HP, valid only):')
    valid = [r for r in out if r['hp'] != 0xFFFF and r['hp'] > 0]
    print(f'  valid: {len(valid)}/{len(out)}')
    for r in sorted(valid, key=lambda x: -x['hp'])[:8]:
        print(f'  #{r["idx"]:3d}  HP={r["hp"]:5d} MP={r["mp"]:5d} flags_a[:5]={r["flags_a"][:5]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
