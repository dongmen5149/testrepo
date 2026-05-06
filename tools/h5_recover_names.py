"""
Hero5 자산 이름 복원.

전략:
  1. classes.dex 의 string pool 파싱 (DEX 포맷)
  2. 각 문자열에 Hero5 hash (DJB2-like, init=0x1505, mul=0x21) 적용
  3. vfs_catalog 의 2,189 hash 와 매칭

산출:
  work/h5/analysis/asset_names.tsv  (index, hash, recovered_name)
"""
from __future__ import annotations
import struct, pathlib, csv

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEX = ROOT / 'work' / 'h5' / 'extracted' / 'classes.dex'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'


def djb2_hero5(name: str) -> int:
    h = 0x1505
    for ch in name.encode('utf-8'):
        h = (ch + h * 0x21) & 0xFFFFFFFF
    return h


def read_uleb128(buf: bytes, pos: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        b = buf[pos]; pos += 1
        result |= (b & 0x7f) << shift
        if not (b & 0x80): break
        shift += 7
    return result, pos


def parse_dex_strings(path: pathlib.Path) -> list[str]:
    data = path.read_bytes()
    if data[:4] != b'dex\n':
        raise ValueError('not a DEX file')
    string_ids_size = struct.unpack_from('<I', data, 0x38)[0]
    string_ids_off = struct.unpack_from('<I', data, 0x3c)[0]
    strings = []
    for i in range(string_ids_size):
        string_data_off = struct.unpack_from('<I', data, string_ids_off + i*4)[0]
        # string_data_item: uleb128 utf16_size + MUTF-8 bytes + 0x00
        utf16_size, pos = read_uleb128(data, string_data_off)
        # find terminating null
        end = data.index(b'\x00', pos)
        try:
            s = data[pos:end].decode('utf-8', errors='strict')
            strings.append(s)
        except UnicodeDecodeError:
            pass
    return strings


def load_catalog() -> dict[int, list[int]]:
    """hash -> [indices]"""
    h2idx: dict[int, list[int]] = {}
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            idx = int(row['index'])
            h = int(row['hash'], 16)
            h2idx.setdefault(h, []).append(idx)
    return h2idx


def main() -> int:
    print(f'parsing {DEX}...')
    strings = parse_dex_strings(DEX)
    print(f'  {len(strings)} strings extracted')

    h2idx = load_catalog()
    print(f'catalog: {sum(len(v) for v in h2idx.values())} entries / {len(h2idx)} unique hashes')

    # also generate variations: try common asset name patterns
    candidates: dict[int, str] = {}
    seen = set()
    def try_name(name: str):
        if name in seen: return
        seen.add(name)
        h = djb2_hero5(name)
        if h in h2idx and h not in candidates:
            candidates[h] = name

    for s in strings:
        try_name(s)
        # also try common prefixes/suffixes
        for variant in (s.upper(), s.lower(), s + '.bin', s + '.png', s + '.dat',
                        s.replace('/', '\\'), s.replace('\\', '/')):
            try_name(variant)

    # generate numbered patterns from any base names
    for s in strings:
        if len(s) < 3 or len(s) > 50: continue
        if not all(c.isalnum() or c in '_-./' for c in s): continue
        for n in range(0, 200):
            for fmt in (f'{s}{n}', f'{s}{n:02d}', f'{s}{n:03d}', f'{s}_{n}', f'{s}_{n:02d}', f'{s}_{n:03d}'):
                try_name(fmt)

    # write results
    OUT.parent.mkdir(parents=True, exist_ok=True)
    matched_indices = set()
    rows = []
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            idx = int(row['index'])
            h = int(row['hash'], 16)
            name = candidates.get(h, '')
            if name:
                matched_indices.add(idx)
            rows.append((idx, f'0x{h:08x}', row['type'], row['length'], name))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('index\thash\ttype\tlength\trecovered_name\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')

    print(f'\nrecovered {len(matched_indices)} / {len(rows)} asset names ({100*len(matched_indices)/len(rows):.1f}%)')
    print(f'unique hashes recovered: {len(candidates)}')
    print(f'wrote {OUT}')

    # show first 30 hits
    print('\nfirst 30 recoveries:')
    n = 0
    for r in rows:
        if r[4]:
            print(f'  {r[0]:5d}  {r[1]}  type={r[2]}  len={r[3]:>7}  → {r[4]}')
            n += 1
            if n >= 30: break
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
