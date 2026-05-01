"""
Hero3 자산 일괄 변환기 — 현재 지원: _txt, _pa.

사용:
    python convert_all.py <extracted_dir> <output_dir>

추후 추가: _bm, _cif, _mp, _scn, _mf (각각 Ghidra 분석 후).
"""
from __future__ import annotations
import sys, pathlib, traceback
from convert_text import parse_text_table
from convert_palette import parse_palette
from convert_bm_v2 import decode_file as decode_bm_file
from convert_cif import parse_cif
from convert_mp import parse_mp
from convert_scn import parse_scn
from convert_dat import parse_dat
import json


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2

    src_root = pathlib.Path(argv[1])
    out_root = pathlib.Path(argv[2])
    out_root.mkdir(parents=True, exist_ok=True)

    counts = {'txt': 0, 'pa': 0, 'bm_files': 0, 'bm_frames': 0, 'cif': 0, 'mp': 0, 'scn': 0, 'scn_dialogues': 0, 'skipped': 0, 'errors': 0}

    for path in src_root.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(src_root)
        try:
            if path.name.endswith('_txt'):
                strings = parse_text_table(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(strings, ensure_ascii=False, indent=2), encoding='utf-8')
                counts['txt'] += 1
            elif path.name.endswith('_pa'):
                colors = parse_palette(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps({'count': len(colors), 'colors': colors}, indent=2), encoding='utf-8')
                counts['pa'] += 1
            elif path.name.endswith('_bm'):
                # 멀티프레임: rel-without-suffix 디렉토리 안에 frame_NN_*.png 들 생성
                bm_out_dir = (out_root / rel.with_suffix(''))
                info = decode_bm_file(path, bm_out_dir)
                counts['bm_files'] += 1
                counts['bm_frames'] += info.get('rendered', 0)
            elif path.name.endswith('_cif'):
                cif_meta = parse_cif(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(cif_meta, indent=2), encoding='utf-8')
                counts['cif'] += 1
            elif path.name.endswith('_mp'):
                mp_data = parse_mp(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(mp_data, indent=2), encoding='utf-8')
                counts['mp'] += 1
            elif path.name.endswith('_scn'):
                scn_data = parse_scn(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(scn_data, ensure_ascii=False, indent=2), encoding='utf-8')
                counts['scn'] += 1
                counts['scn_dialogues'] += len(scn_data.get('dialogue', []))
            elif path.name.endswith('_dat'):
                dat_data = parse_dat(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(dat_data, ensure_ascii=False, indent=2), encoding='utf-8')
                counts.setdefault('dat', 0)
                counts['dat'] += 1
            else:
                counts['skipped'] += 1
        except Exception as e:
            counts['errors'] += 1
            print(f'  ERROR {rel}: {e}', file=sys.stderr)

    print(f'\nDone. txt={counts["txt"]} pa={counts["pa"]} bm_files={counts["bm_files"]} bm_frames={counts["bm_frames"]} cif={counts["cif"]} mp={counts["mp"]} scn={counts["scn"]} scn_dialogues={counts["scn_dialogues"]} skipped={counts["skipped"]} errors={counts["errors"]}')
    return 0 if counts['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
