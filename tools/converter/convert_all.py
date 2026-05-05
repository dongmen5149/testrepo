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
from convert_h4_map import parse_h4_map
from convert_exd import parse_exd
from convert_h4_tile import decode_h4_tile
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
        # Hero4 같은 게임은 대문자 접미사(_BM, _CIF, _DAT, _PAL 등)를 쓰므로 case-insensitive 분기
        name_lower = path.name.lower()
        try:
            if name_lower.endswith('_txt'):
                strings = parse_text_table(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(strings, ensure_ascii=False, indent=2), encoding='utf-8')
                counts['txt'] += 1
            elif name_lower.endswith('_pa') or name_lower.endswith('_pal'):
                colors = parse_palette(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps({'count': len(colors), 'colors': colors}, indent=2), encoding='utf-8')
                counts['pa'] += 1
            elif name_lower.endswith('_bm'):
                # 멀티프레임: rel-without-suffix 디렉토리 안에 frame_NN_*.png 들 생성
                bm_out_dir = (out_root / rel.with_suffix(''))
                info = decode_bm_file(path, bm_out_dir)
                counts['bm_files'] += 1
                counts['bm_frames'] += info.get('rendered', 0)
            elif name_lower.endswith('_cif'):
                cif_meta = parse_cif(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(cif_meta, indent=2), encoding='utf-8')
                counts['cif'] += 1
            elif name_lower.endswith('_mp'):
                mp_data = parse_mp(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(mp_data, indent=2), encoding='utf-8')
                counts['mp'] += 1
            elif name_lower.endswith('_scn'):
                scn_data = parse_scn(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(scn_data, ensure_ascii=False, indent=2), encoding='utf-8')
                counts['scn'] += 1
                counts['scn_dialogues'] += len(scn_data.get('dialogue', []))
            elif name_lower.endswith('_dat'):
                dat_data = parse_dat(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(dat_data, ensure_ascii=False, indent=2), encoding='utf-8')
                counts.setdefault('dat', 0)
                counts['dat'] += 1
            elif name_lower.startswith('_map_m_'):
                # Hero4 맵 (suffix 없음, _MAP_M_NNN 명명)
                map_info = parse_h4_map(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(map_info, ensure_ascii=False, indent=2), encoding='utf-8')
                counts.setdefault('h4_map', 0)
                counts['h4_map'] += 1
            elif name_lower.endswith('_exd'):
                exd_info = parse_exd(path.read_bytes())
                out = (out_root / rel).with_suffix('.json')
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(json.dumps(exd_info, indent=2), encoding='utf-8')
                counts.setdefault('exd', 0)
                counts['exd'] += 1
            elif name_lower.startswith('_tile_') or (
                name_lower.startswith('_obj_')
                and not name_lower.endswith('_bm')
                and not name_lower.endswith('_cif')
            ):
                # Hero4 single-frame BM (TILE/_TILE_NNN, OBJ/{000,001,002}/_OBJ_NNN)
                # _OBJ_SPR_NNN_BM/_CIF 는 위 _bm/_cif 분기에서 처리
                img = decode_h4_tile(path.read_bytes())
                if img is not None:
                    out = (out_root / rel).with_suffix('.png')
                    out.parent.mkdir(parents=True, exist_ok=True)
                    img.save(out)
                    counts.setdefault('h4_tile', 0)
                    counts['h4_tile'] += 1
                else:
                    counts['skipped'] += 1
            else:
                counts['skipped'] += 1
        except Exception as e:
            counts['errors'] += 1
            print(f'  ERROR {rel}: {e}', file=sys.stderr)

    h4_map = counts.get('h4_map', 0)
    dat_n = counts.get('dat', 0)
    exd_n = counts.get('exd', 0)
    tile_n = counts.get('h4_tile', 0)
    print(f'\nDone. txt={counts["txt"]} pa={counts["pa"]} bm_files={counts["bm_files"]} bm_frames={counts["bm_frames"]} '
          f'cif={counts["cif"]} mp={counts["mp"]} scn={counts["scn"]} scn_dialogues={counts["scn_dialogues"]} '
          f'dat={dat_n} h4_map={h4_map} exd={exd_n} h4_tile={tile_n} skipped={counts["skipped"]} errors={counts["errors"]}')
    return 0 if counts['errors'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
