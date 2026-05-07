"""Batch wrapper for convert_h5_sprite.py / convert_h5_pa.py.

asset_names.tsv 에서 .mgr/.cif/.ext (sprite) 와 .pal (palette) 항목을
찾아 vfs_entries 에서 디코딩.
"""
from __future__ import annotations
import csv, pathlib, sys, json, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.converter.convert_h5_sprite import decode_file as dec_sprite
from tools.converter.convert_h5_pa import parse_h5_palette


def main() -> int:
    names_file = ROOT / "work/h5/analysis/asset_names.tsv"
    vfs_dir = ROOT / "work/h5/vfs_entries"
    spr_root = ROOT / "work/h5/converted/sprites"
    pal_root = ROOT / "work/h5/converted/palettes"
    spr_root.mkdir(parents=True, exist_ok=True)
    pal_root.mkdir(parents=True, exist_ok=True)

    spr_ok = spr_skip = spr_err = 0
    pal_ok = pal_err = 0

    with open(names_file, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            name = row.get('recovered_name', '')
            if not name: continue
            idx = int(row['index']); h = int(row['hash'], 16)
            src = vfs_dir / f'{idx:05d}_{h:08x}.bin'
            if not src.exists(): continue
            if name.endswith(('.mgr', '.cif', '.ext')):
                dst = spr_root / f'{idx:05d}_{h:08x}'
                try:
                    stats = dec_sprite(src, dst)
                    if stats.get('rendered', 0) > 0: spr_ok += 1
                    else: spr_skip += 1
                except Exception as e:
                    spr_err += 1
            elif name.endswith('.pal'):
                try:
                    pal = parse_h5_palette(src.read_bytes())
                    out = pal_root / f'{idx:05d}_{h:08x}.json'
                    out.write_text(json.dumps(pal, ensure_ascii=False), encoding='utf-8')
                    pal_ok += 1
                except Exception:
                    pal_err += 1

    print(f'sprites: ok={spr_ok} skipped={spr_skip} errors={spr_err}')
    print(f'palettes: ok={pal_ok} errors={pal_err}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
