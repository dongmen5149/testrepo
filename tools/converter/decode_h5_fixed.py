"""
고정 사이즈 record 테이블 (.dat) 디코더.

대상:
  c/csv/enemy_g.dat    166 records × 121 bytes
  c/csv/npc_g.dat       81 records ×  27 bytes
  (이름 없음, 순수 stat 데이터)

DES key "0EP@KO91" 발견됐지만 이 두 파일은 평문임을 검증
(MX_desInit caller 추적: 0x001688b0 = "0EP@KO91" 8B ASCII).
세이브 파일 / 일부 보호 리소스만 DES 사용.

산출:
  apps/hero5-godot/assets/gamedata/enemy_stats.json
  apps/hero5-godot/assets/gamedata/npc_stats.json
"""
from __future__ import annotations
import pathlib, csv, struct, json

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT_DIR = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata'


def find_file(name: str) -> pathlib.Path:
    with open(NAMES, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['recovered_name'] == name:
                return ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"],16):08x}.bin'
    raise FileNotFoundError(name)


def decode_fixed(path: pathlib.Path) -> dict:
    d = path.read_bytes()
    count = struct.unpack_from('<H', d, 0)[0]
    rest = d[2:]
    if count == 0 or len(rest) % count != 0:
        return {'count': count, 'rec_size': 0, 'records': []}
    rec_size = len(rest) // count
    records = []
    for i in range(count):
        r = rest[i * rec_size: (i + 1) * rec_size]
        # decode as u16 LE array (most stat fields appear u16-aligned)
        u16s = list(struct.unpack(f'<{rec_size//2}H', r[:(rec_size//2)*2]))
        records.append({
            'idx': i,
            'hex': r.hex(),
            'u16_le': u16s,
        })
    return {'count': count, 'rec_size': rec_size, 'records': records}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for src_name, out_name in [
        ('c/csv/enemy_g.dat', 'enemy_stats.json'),
        ('c/csv/npc_g.dat', 'npc_stats.json'),
    ]:
        d = decode_fixed(find_file(src_name))
        (OUT_DIR / out_name).write_text(
            json.dumps(d, indent=2), encoding='utf-8')
        print(f'{src_name}: {d["count"]} records × {d["rec_size"]}B → {out_name}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
