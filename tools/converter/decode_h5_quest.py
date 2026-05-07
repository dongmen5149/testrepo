"""
mission_list.dat (퀘스트 이름 + 메타) + questTree.dat (트리 구조) 파서.

mission_list.dat: 표준 csv 포맷 (u16 count + records[u16 size, u8 strlen,
str, stats]). 105 records.

questTree.dat: 72 × 7B 고정 record. 각 record 의미:
  u16 questID (또는 prereq), u16 next, u16 condition_or_flag, u8 type
  (정확한 layout 은 후속)

산출:
  apps/hero5-godot/assets/gamedata/quests.json
"""
from __future__ import annotations
import pathlib, csv, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'quests.json'


def find(target: str) -> pathlib.Path:
    for r in csv.DictReader(open(NAMES, encoding='utf-8'), delimiter='\t'):
        if r['recovered_name'] == target:
            return ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"], 16):08x}.bin'
    raise FileNotFoundError(target)


def parse_var_dat(d: bytes) -> list[dict]:
    """표준 csv: u16 count + records[u16 size, u8 strlen, str, extra]."""
    count = struct.unpack_from('<H', d, 0)[0]
    pos = 2
    out = []
    for _ in range(count):
        if pos + 3 > len(d): break
        sz = struct.unpack_from('<H', d, pos)[0]; pos += 2
        if pos + sz > len(d): break
        body = d[pos:pos + sz]
        pos += sz
        strlen = body[0]
        try:
            name = body[1:1 + strlen].decode('euc-kr', errors='replace')
        except Exception:
            name = ''
        extra = body[1 + strlen:]
        out.append({'name': name, 'extra_hex': extra.hex()})
    return out


def parse_fixed(d: bytes, rec_size: int) -> list[dict]:
    count = struct.unpack_from('<H', d, 0)[0]
    out = []
    for i in range(count):
        off = 2 + i * rec_size
        if off + rec_size > len(d): break
        rec = d[off:off + rec_size]
        out.append({'idx': i, 'hex': rec.hex()})
    return out


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    quests = parse_var_dat(find('c/csv/mission_list.dat').read_bytes())
    tree = parse_fixed(find('c/csv/questTree.dat').read_bytes(), 7)

    OUT.write_text(json.dumps({
        'quests': quests,
        'tree': tree,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'parsed {len(quests)} quests, {len(tree)} tree nodes → {OUT}')
    print('\nfirst 10 quest names:')
    for i, q in enumerate(quests[:10]):
        print(f'  #{i:3d}  {q["name"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
