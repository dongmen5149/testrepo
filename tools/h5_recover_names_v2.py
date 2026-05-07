"""
Hero5 자산 이름 복원 v2.

v1 대비 변경:
  - DEX strings 외에 libHeroesLore5.so 의 ASCII identifier 풀(6,529개) 추가
  - 확장자/대소문자/접두사 변형 확장 (.cif/.dat/.sav 등 .so 에서 발견된 것 추가)
  - 공통 게임 자산 prefix (anim/spr/img/snd/map/ui/font + 0..999) 합성
"""
from __future__ import annotations
import pathlib, csv, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEX = ROOT / 'work' / 'h5' / 'extracted' / 'classes.dex'
SO_STRS = ROOT / 'work' / 'h5' / 'analysis' / 'so_strings.txt'
DEX_CAND = ROOT / 'work' / 'h5' / 'analysis' / 'asset_name_candidates.txt'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'

EXTS = ['', '.bin', '.png', '.dat', '.cif', '.sav', '.pa', '.bm', '.mp', '.txt',
        '.spr', '.anim', '.img', '.snd', '.smaf', '.ogg', '.mmf']


def djb2(name: str) -> int:
    h = 0x1505
    for ch in name.encode('utf-8'):
        h = (ch + h * 0x21) & 0xFFFFFFFF
    return h


def load_catalog() -> dict[int, list[int]]:
    h2idx: dict[int, list[int]] = {}
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            h2idx.setdefault(int(row['hash'], 16), []).append(int(row['index']))
    return h2idx


def load_pool() -> set[str]:
    pool: set[str] = set()
    if SO_STRS.exists():
        pool.update(SO_STRS.read_text(encoding='utf-8').splitlines())
    if DEX_CAND.exists():
        pool.update(DEX_CAND.read_text(encoding='utf-8').splitlines())
    return {s.strip() for s in pool if s.strip()}


def main() -> int:
    pool = load_pool()
    h2idx = load_catalog()
    total_entries = sum(len(v) for v in h2idx.values())
    print(f'pool: {len(pool)} base strings')
    print(f'catalog: {total_entries} entries / {len(h2idx)} unique hashes')

    candidates: dict[int, str] = {}
    seen: set[str] = set()

    # Sanity: only accept a name if its inferred extension matches the entry type.
    EXT_TO_TYPE = {
        '.txt': 'txt', '.ogg': 'ogg', '.smaf': 'smaf', '.mmf': 'smaf',
    }
    # Anything else falls under 'bin' bucket.
    h2type = {}
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            h2type[int(row['hash'], 16)] = row['type']

    def add(name: str):
        if not name or name in seen: return
        seen.add(name)
        h = djb2(name)
        if h not in h2idx or h in candidates: return
        # type sanity check
        actual = h2type.get(h)
        for ext, expected in EXT_TO_TYPE.items():
            if name.lower().endswith(ext) and actual != expected:
                return
        # bin entries should not have an obvious non-bin extension
        if actual == 'bin' and any(name.lower().endswith(e) for e in EXT_TO_TYPE):
            return
        candidates[h] = name

    # Pass 1: pool strings + extension/case variations
    for s in pool:
        if not (1 <= len(s) <= 80): continue
        for ext in EXTS:
            for n in (s, s.lower(), s.upper()):
                add(n + ext)
                # path normalization
                for sep_swap in (n.replace('/', '\\'), n.replace('\\', '/')):
                    add(sep_swap + ext)

    print(f'after pass 1: {len(candidates)} hash matches')

    # Pass 2: numbered patterns from short pool strings
    short_bases = [s for s in pool if 2 <= len(s) <= 30 and all(
        c.isalnum() or c in '_-' for c in s)]
    print(f'short bases for numbering: {len(short_bases)}')
    for s in short_bases:
        for n in range(0, 300):
            for fmt in (f'{s}{n}', f'{s}{n:02d}', f'{s}{n:03d}', f'{s}{n:04d}',
                        f'{s}_{n}', f'{s}_{n:02d}', f'{s}_{n:03d}'):
                for ext in ('', '.bin', '.png', '.dat'):
                    add(fmt + ext)

    print(f'after pass 2: {len(candidates)} hash matches')

    # Pass 3: synthetic prefixes
    PREFIX = ['anim', 'spr', 'sprite', 'img', 'image', 'snd', 'sound', 'mus', 'music',
              'map', 'stage', 'ui', 'font', 'effect', 'fx', 'char', 'monster', 'item',
              'icon', 'bg', 'tile', 'frame', 'data', 'res', 'tbl', 'table',
              'h5_', 'hero_', 'data_', 'res_', 'asset_']
    for p in PREFIX:
        for n in range(0, 1000):
            for fmt in (f'{p}{n}', f'{p}{n:02d}', f'{p}{n:03d}', f'{p}{n:04d}',
                        f'{p}_{n}', f'{p}_{n:02d}', f'{p}_{n:03d}', f'{p}_{n:04d}'):
                for ext in ('', '.bin', '.dat', '.png'):
                    add(fmt + ext)

    print(f'after pass 3: {len(candidates)} hash matches')

    # Write results
    OUT.parent.mkdir(parents=True, exist_ok=True)
    matched = 0
    rows = []
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            h = int(row['hash'], 16)
            name = candidates.get(h, '')
            if name: matched += 1
            rows.append((row['index'], f'0x{h:08x}', row['type'], row['length'], name))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('index\thash\ttype\tlength\trecovered_name\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')

    print(f'\nrecovered {matched} / {len(rows)} ({100*matched/len(rows):.1f}%)')
    print(f'wrote {OUT}')

    print('\nfirst 40 hits:')
    n = 0
    for r in rows:
        if r[4]:
            print(f'  {r[0]:>5}  {r[1]}  {r[2]:6} len={r[3]:>7}  -> {r[4]}')
            n += 1
            if n >= 40: break
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
