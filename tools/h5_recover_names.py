"""
Hero5 자산 이름 복원 v4 — 발견된 모든 .so 'c/' 경로 + 패턴.

발견된 카테고리:
  c/calc/calc_<region>.dat
  c/csv/<table>.dat (+ enemy_, item_, quest_, rewards_, shop_, skill_, smith_, zonemap_, smith_, etc)
  c/csv2/help_<region>.dat
  c/font/{eng,kor}.fnt + table.dat + type.dat
  c/img/<ui>.mgr (gmenu, icon, menu, shadow, touch, ui, worldmap)
  c/sp/img0..6/NNN.mgr
  c/sp/cif/{NNN.cif, named.cif}
  c/sp/ext/{NNN.ext, named.ext}
  c/sp/imgcom/named.mgr
  c/sp/empty/empty.mgr
  c/sp/pal/  (557 entries)
  c/map/{face,obj,fgi,seaani,tile}_NNN.<ext>
  c/map_sp/{fgi,ms,ms_img}_NNN.mgr
  c/mon/...
  c/par/{p,pimg,pinfo,ps}NN
  c/snd/bgm_*  c/snd/eff_*
  c/iconpal/NNN_*
  c/ep/ep_N/...
"""
from __future__ import annotations
import re, pathlib, csv, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO   = ROOT / 'work' / 'h5' / 'extracted' / 'lib' / 'armeabi' / 'libHeroesLore5.so'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'


def djb2(s: bytes) -> int:
    h = 0x1505
    for c in s:
        h = (c + h * 0x21) & 0xFFFFFFFF
    return h


def main() -> int:
    h2info: dict[int, tuple] = {}
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            h2info[int(row['hash'],16)] = (int(row['index']), row['type'], int(row['length']))

    so = SO.read_bytes()
    strs = set(re.findall(rb'[\x20-\x7e]{3,200}', so))

    candidates: dict[int, bytes] = {}
    def add(name: bytes):
        h = djb2(name)
        if h in h2info and h not in candidates:
            candidates[h] = name

    # Pass 0 — explicit known names that may not appear standalone in .so
    for nm in (b'version.txt', b'c/font/eng.fnt', b'c/font/kor.fnt',
               b'c/font/table.dat', b'c/font/type.dat'):
        add(nm)
    # Pass 1 — raw + path-suffix slices
    for s in strs:
        add(s)
        for sep in (ord('/'), 0x5c):
            for p, b in enumerate(s):
                if b == sep and p + 1 < len(s):
                    add(s[p+1:])
    print(f'[1] raw+suffix: {len(candidates)}')

    # Pass 2 — sprite/cif/ext numeric ranges
    for n in range(0, 1000):
        for cat in range(0, 10):
            for d in (2, 3, 4):
                add(f'c/sp/img{cat}/{n:0{d}d}.mgr'.encode())
        for tpl in (
            f'c/sp/cif/{n:03d}.cif',
            f'c/sp/ext/{n:03d}.ext',
            f'c/sp/imgcom/{n:03d}.mgr',
            f'c/sp/empty/{n:03d}.mgr',
            f'c/sp/pal/{n:03d}.pal',
            f'c/sp/pal/{n:03d}.dat',
            f'c/sp/pal/{n:03d}',
            f'c/sp/pal/{n:03d}.mgr',
            f'c/sp/pal/{n:04d}.pal',
            f'c/img/{n:03d}.mgr',
            f'c/font/{n:03d}.dat',
        ):
            add(tpl.encode())
    print(f'[2] numeric sprite/pal: {len(candidates)}')

    # Pass 3 — map/, map_sp/, mon/, par/, snd/, ep/, iconpal/
    # Format strings discovered in .so:
    #   c/map/face_%02d.gbm  c/map/obj_%03d.gbm  c/map/fgi_%03d.gbm
    #   c/map/tile_%03d.gbm  c/map/seaani_%03d.pal
    #   c/mon/%d_ai
    #   c/ep/ep_%d/s%d_%03d.scn
    #   c/iconpal/NNN_%03d.pal  (NNN = 226..232)
    for n in range(0, 500):
        for tpl in (
            f'c/map/face_{n:02d}.gbm', f'c/map/face_{n:03d}.gbm',
            f'c/map/obj_{n:03d}.gbm',  f'c/map/obj_{n:02d}.gbm',
            f'c/map/fgi_{n:03d}.gbm',  f'c/map/fgi_{n:02d}.gbm',
            f'c/map/tile_{n:03d}.gbm', f'c/map/tile_{n:02d}.gbm',
            f'c/map/seaani_{n:03d}.pal', f'c/map/seaani_{n:02d}.pal',
            f'c/mon/{n}_ai',
            f'c/mon/{n}_ai.dat', f'c/mon/{n:02d}_ai', f'c/mon/{n:03d}_ai',
        ):
            add(tpl.encode())
    # ep/ep_E/sS_NNN.scn
    for ep in range(0, 10):
        for s in range(0, 20):
            for n in range(0, 300):
                add(f'c/ep/ep_{ep}/s{s}_{n:03d}.scn'.encode())
    # c/map/%05d.scn — main map scenes (5-digit numeric)
    for n in range(0, 100000):
        add(f'c/map/{n:05d}.scn'.encode())
    # c/map/(md)NN — weird parens-prefix pattern
    for n in range(0, 200):
        add(f'c/map/(md){n:02d}'.encode())
        add(f'c/map/(md){n:03d}'.encode())
        add(f'c/map/(md){n:02d}.scn'.encode())
        add(f'c/map/(md){n:02d}.dat'.encode())
    # c/map_sp/NNN.ext + extensionless fgi/ms
    for n in range(0, 1000):
        add(f'c/map_sp/{n:03d}.ext'.encode())
        add(f'c/map_sp/{n:03d}.mgr'.encode())
        add(f'c/map_sp/fgi{n:03d}'.encode())
        add(f'c/map_sp/ms{n:03d}'.encode())
        add(f'c/map_sp/fgi{n:02d}'.encode())
        add(f'c/map_sp/ms{n:02d}'.encode())
    # c/par/pNNN, psNNN (extensionless)
    for n in range(0, 1000):
        add(f'c/par/p{n:03d}'.encode())
        add(f'c/par/ps{n:03d}'.encode())
        add(f'c/par/p{n:02d}'.encode())
        add(f'c/par/ps{n:02d}'.encode())
    # c/csv refined: enemy_%d, item_%02d, quest_%d, etc.
    for n in range(0, 200):
        add(f'c/csv/enemy_{n}.dat'.encode())
        add(f'c/csv/enemy_expert_{n}.dat'.encode())
        add(f'c/csv/item_{n:02d}.dat'.encode())
        add(f'c/csv/item_{n}.dat'.encode())
        add(f'c/csv/quest_{n}.dat'.encode())
        add(f'c/csv/rewards_{n}.dat'.encode())
        add(f'c/csv/shop_{n}.dat'.encode())
        add(f'c/csv/skill_{n:02d}.dat'.encode())
        add(f'c/csv/skill_{n}.dat'.encode())
        add(f'c/csv/smith_{n}.dat'.encode())
        add(f'c/csv/zonemap_{n}.dat'.encode())
        for m in range(0, 50):
            add(f'c/csv/{n}_rewards_{m}.dat'.encode())
    # iconpal NNN_MM.pal
    for n in range(220, 350):
        for m in range(0, 100):
            add(f'c/iconpal/{n}_{m:03d}.pal'.encode())
            add(f'c/iconpal/{n}_{m:02d}.pal'.encode())
    # Old defaults (kept for compatibility)
    for n in range(0, 200):
        for tpl in (
            f'c/map/face_{n:02d}.mgr', f'c/map/face_{n:03d}.mgr',
            f'c/map/obj_{n:02d}.mgr',  f'c/map/obj_{n:03d}.mgr',
            f'c/map/fgi_{n:02d}.mgr',  f'c/map/fgi_{n:03d}.mgr',
            f'c/map/seaani_{n:02d}.mgr', f'c/map/seaani_{n:03d}.mgr',
            f'c/map/tile_{n:02d}.mgr', f'c/map/tile_{n:03d}.mgr',
            f'c/map/face_{n}.dat', f'c/map/obj_{n}.dat',
            f'c/map/fgi_{n}.dat', f'c/map/tile_{n}.dat',
            f'c/map_sp/fgi_img{n:02d}.mgr', f'c/map_sp/fgi_img{n:03d}.mgr',
            f'c/map_sp/ms_img{n:02d}.mgr', f'c/map_sp/ms_img{n:03d}.mgr',
            f'c/map_sp/ms{n:02d}.mgr', f'c/map_sp/ms{n:03d}.mgr',
            f'c/mon/{n:02d}.mgr', f'c/mon/{n:03d}.mgr',
            f'c/mon/{n:02d}.dat', f'c/mon/{n:03d}.dat',
            f'c/mon/mon_{n:03d}.mgr', f'c/mon/mon{n:03d}.mgr',
            f'c/par/p{n:02d}.dat', f'c/par/p{n:03d}.dat',
            f'c/par/pimg{n:02d}.mgr', f'c/par/pimg{n:03d}.mgr',
            f'c/par/ps{n:02d}.dat', f'c/par/ps{n:03d}.dat',
            f'c/par/pinfo{n:02d}.dat', f'c/par/pinfo{n:03d}.dat',
            f'c/snd/bgm_{n:02d}.mid', f'c/snd/bgm_{n:03d}.mid',
            f'c/snd/bgm_{n:02d}.mmf', f'c/snd/bgm_{n:03d}.mmf',
            f'c/snd/bgm_{n:02d}.smaf', f'c/snd/bgm_{n:03d}.smaf',
            f'c/snd/bgm_{n:02d}.ogg', f'c/snd/bgm_{n:03d}.ogg',
            f'c/snd/eff_{n:02d}.mid', f'c/snd/eff_{n:03d}.mid',
            f'c/snd/eff_{n:02d}.mmf', f'c/snd/eff_{n:03d}.mmf',
            f'c/snd/eff_{n:02d}.smaf', f'c/snd/eff_{n:03d}.smaf',
            f'c/snd/eff_{n:02d}.ogg', f'c/snd/eff_{n:03d}.ogg',
            f'c/ep/ep_0/{n:03d}.dat', f'c/ep/ep_1/{n:03d}.dat',
            f'c/ep/ep_2/{n:03d}.dat', f'c/ep/ep_3/{n:03d}.dat',
            f'c/ep/ep_{n:02d}.dat',  f'c/ep/ep_{n:03d}.dat',
            f'c/ep/ep_{n}.dat', f'c/ep/ep_{n}',
        ):
            add(tpl.encode())
    print(f'[3] map/snd/par/mon/ep: {len(candidates)}')

    # Pass 4 — iconpal NNN_M / NNN_MM patterns
    for n in range(200, 350):
        for m in range(0, 100):
            for tpl in (
                f'c/iconpal/{n}_{m:02d}.pal',
                f'c/iconpal/{n}_{m:02d}.dat',
                f'c/iconpal/{n}_{m:02d}.mgr',
                f'c/iconpal/{n}_{m}.pal',
                f'c/iconpal/{n}_{m}.dat',
                f'c/iconpal/{n}_{m}',
            ):
                add(tpl.encode())
    print(f'[4] iconpal: {len(candidates)}')

    # Pass 5 — csv extensions: enemy_, item_, quest_, etc with named/numbered suffix
    csv_prefixes = ['enemy_', 'enemy_expert_', 'item_', 'quest_', 'rewards_',
                    'shop_', 'skill_', 'smith_', 'zonemap_']
    csv_regions  = ['', 'expert', 'normal', 'sk', 'skt', 'ktf', 'lg',
                    'android', 'android_skt', 'android_ktf']
    for prefix in csv_prefixes:
        for region in csv_regions:
            base = f'c/csv/{prefix}{region}'
            add((base + '.dat').encode())
            for n in range(0, 100):
                add(f'{base}{n:02d}.dat'.encode())
                add(f'{base}{n}.dat'.encode())
    # csv2 help
    for region in ['', 'sk', 'skt', 'ktf', 'lg', 'android', 'android_sk',
                   'android_skt', 'android_ktf']:
        add(f'c/csv2/help_{region}.dat'.encode())
        add(f'c/csv2/help{region}.dat'.encode())
    print(f'[5] csv variants: {len(candidates)}')

    # Pass 6 — combine .so basename tokens with all 'c/' prefixes
    PREFIXES = [b'c/calc/', b'c/csv/', b'c/csv2/', b'c/font/', b'c/img/',
                b'c/sp/imgcom/', b'c/sp/empty/', b'c/sp/cif/', b'c/sp/ext/',
                b'c/sp/pal/', b'c/map/', b'c/map_sp/', b'c/mon/', b'c/par/',
                b'c/snd/', b'c/iconpal/', b'c/ep/']
    EXTS = (b'.dat', b'.mgr', b'.cif', b'.ext', b'.pal', b'.fnt',
            b'.mid', b'.mmf', b'.smaf', b'.ogg', b'.bin', b'.txt')
    bases = set()
    for s in strs:
        for tok in re.split(rb'[/\\\s,():"\']', s):
            if 1 <= len(tok) <= 40 and re.match(rb'^[A-Za-z0-9_.\-]+$', tok):
                bases.add(tok)
                # also stem (without extension)
                if b'.' in tok:
                    bases.add(tok.rsplit(b'.', 1)[0])
    print(f'  bases: {len(bases)}')
    for prefix in PREFIXES:
        for base in bases:
            add(prefix + base)
            if b'.' not in base:
                for ext in EXTS:
                    add(prefix + base + ext)
    print(f'[6] base+prefix combo: {len(candidates)}')

    # Pass 7 — special: .so contains tokens like '828_sk', 'ealogo', 'imo', 'pointer', 'title', 'eff'
    NAMED = [b'828_sk', b'ealogo', b'eff', b'imo', b'pointer', b'title',
             b'gmenu', b'icon', b'menu', b'shadow', b'touch', b'ui',
             b'worldmap', b'empty']
    for prefix in PREFIXES:
        for nm in NAMED:
            for ext in EXTS:
                add(prefix + nm + ext)
    print(f'[7] named: {len(candidates)}')

    # Write results
    OUT.parent.mkdir(parents=True, exist_ok=True)
    matched = 0
    rows = []
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            h = int(row['hash'],16)
            name = candidates.get(h, b'')
            if name: matched += 1
            rows.append((row['index'], f'0x{h:08x}', row['type'], row['length'],
                         name.decode('utf-8','replace') if name else ''))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('index\thash\ttype\tlength\trecovered_name\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')

    print(f'\nrecovered {matched} / {len(rows)} ({100*matched/len(rows):.1f}%)')

    from collections import Counter
    cats = Counter()
    for _, _, _, _, name in rows:
        if name:
            parts = name.split('/')
            key = '/'.join(parts[:3]) if len(parts) >= 3 else '/'.join(parts[:2])
            cats[key] += 1
    print('\ncategory distribution:')
    for k,v in cats.most_common():
        print(f'  {k:35} {v}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
