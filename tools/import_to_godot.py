"""
Hero5 Godot 임포트 파이프라인.

이미 변환된 산출물들을 Godot 프로젝트의 `assets/` 디렉토리로 복사/변환한다.

소스 → 타겟:
  work/h5/converted/sprites/<file>/frame_*.png  → apps/hero5-godot/assets/sprites/<file>/
  work/h5/converted/gbm/<sub>/<name>.png        → apps/hero5-godot/assets/gbm/<sub>/<name>.png
  work/h5/converted/text/_corpus.txt + *.json   → apps/hero5-godot/assets/text/
  work/h5/vfs_entries/*.ogg                     → apps/hero5-godot/assets/sounds/
  work/h5/analysis/scn_headers.tsv              → apps/hero5-godot/assets/scenes/index.json

선택적: 팔레트 _pa 파일을 RGB565 → JSON RGBA 로 변환.
"""
from __future__ import annotations
import shutil, pathlib, csv, json, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC_SPR  = ROOT / 'work' / 'h5' / 'converted' / 'sprites'
SRC_GBM  = ROOT / 'work' / 'h5' / 'converted' / 'gbm'
SRC_TEXT = ROOT / 'work' / 'h5' / 'converted' / 'text'
SRC_VFS  = ROOT / 'work' / 'h5' / 'vfs_entries'
SRC_NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
SRC_SCN   = ROOT / 'work' / 'h5' / 'analysis' / 'scn_headers.tsv'

DST = ROOT / 'apps' / 'hero5-godot' / 'assets'


def copy_tree(src: pathlib.Path, dst: pathlib.Path, label: str = '') -> int:
    if not src.exists():
        print(f'  [skip] {label}: {src} not found')
        return 0
    n = 0
    for f in src.rglob('*'):
        if not f.is_file(): continue
        rel = f.relative_to(src)
        out = dst / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
        n += 1
    print(f'  copied {n} files: {src.name} -> {dst.relative_to(ROOT)}')
    return n


def import_sounds() -> int:
    if not SRC_NAMES.exists():
        print('  [skip] sounds: asset_names.tsv missing'); return 0
    out_dir = DST / 'sounds'; out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(SRC_NAMES, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            name = row['recovered_name']
            if not name: continue
            if not (name.endswith('.ogg') or name.endswith('.mmf') or
                    name.endswith('.smaf')): continue
            idx = int(row['index']); h = int(row['hash'], 16)
            ext = row['type']  # 'ogg' or 'smaf'
            if ext != 'ogg': continue  # skip SMAF (need conversion)
            src = SRC_VFS / f'{idx:05d}_{h:08x}.{ext}'
            if not src.exists(): continue
            stem = pathlib.PurePosixPath(name).stem
            dst = out_dir / f'{stem}.ogg'
            shutil.copy2(src, dst)
            n += 1
    print(f'  copied {n} OGG sounds -> assets/sounds/')
    return n


def import_palettes() -> int:
    """Read .pa indexed RGB565 files → JSON RGBA arrays."""
    out_dir = DST / 'palettes'; out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(SRC_NAMES, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            name = row['recovered_name']
            if not name.endswith('.pal'): continue
            idx = int(row['index']); h = int(row['hash'], 16)
            src = SRC_VFS / f'{idx:05d}_{h:08x}.bin'
            if not src.exists(): continue
            data = src.read_bytes()
            if len(data) < 1: continue
            count = data[0]
            if 1 + count * 2 > len(data): continue
            colors = []
            for i in range(count):
                v = struct.unpack_from('<H', data, 1 + i*2)[0]
                r5, g6, b5 = (v >> 11) & 0x1F, (v >> 5) & 0x3F, v & 0x1F
                r = (r5 * 255 + 15) // 31
                g = (g6 * 255 + 31) // 63
                b = (b5 * 255 + 15) // 31
                a = 0 if i == 0 else 255  # idx 0 = transparent
                colors.append([r, g, b, a])
            stem = pathlib.PurePosixPath(name).stem
            (out_dir / f'{stem}.json').write_text(json.dumps(colors), encoding='utf-8')
            n += 1
    print(f'  converted {n} palettes -> assets/palettes/')
    return n


def import_text() -> int:
    """Copy text JSON corpus."""
    if not SRC_TEXT.exists(): return 0
    out_dir = DST / 'text'; out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in SRC_TEXT.rglob('*.json'):
        shutil.copy2(f, out_dir / f.name); n += 1
    # also copy corpus
    corpus = SRC_TEXT / '_corpus.txt'
    if corpus.exists():
        shutil.copy2(corpus, out_dir / '_corpus.txt')
    print(f'  copied {n} text JSONs -> assets/text/')
    return n


def import_scn_index() -> int:
    """Build assets/scenes/index.json from scn_headers.tsv."""
    if not SRC_SCN.exists(): return 0
    out_dir = DST / 'scenes'; out_dir.mkdir(parents=True, exist_ok=True)
    scenes = []
    with open(SRC_SCN, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            scenes.append({
                'index': int(row['index']),
                'name': row['name'],
                'mapID': int(row['mapID']),
                'startX': int(row['startX']),
                'startY': int(row['startY']),
                'startDir': int(row['startDir']),
                'body_len': int(row['body_len']),
            })
    (out_dir / 'index.json').write_text(json.dumps(scenes, indent=2), encoding='utf-8')
    print(f'  wrote scene index ({len(scenes)} entries) -> assets/scenes/index.json')
    return len(scenes)


def main() -> int:
    DST.mkdir(parents=True, exist_ok=True)
    print(f'importing to {DST.relative_to(ROOT)}/')
    copy_tree(SRC_SPR,  DST / 'sprites', 'sprites')
    copy_tree(SRC_GBM,  DST / 'gbm', 'gbm')
    import_palettes()
    import_text()
    import_sounds()
    import_scn_index()
    print('\ndone.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
