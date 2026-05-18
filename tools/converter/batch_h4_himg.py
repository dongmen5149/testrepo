"""Hero4 H4/000~007 디렉토리의 _HIMG_NNN_MMM 파일 일괄 BM 디코드.

검증: 모든 368 파일이 BM v2 0x0b magic (Hero3 디코더 100% 호환).
파일명 패턴: _HIMG_NNN_MMM (NNN = group 000-007, MMM = within-group index).

출력:
    work/h4/converted/HIMG/<NNN>/_HIMG_NNN_MMM/frame_XX_WxH_tb.png

요약 통계:
    - 총 368 파일, 평균 ~7 frames/file → ~2,500 PNG 추정
    - H4/000 (102 files, 메인 sprite), H4/005 (15 files, 보스급 큰 sprite) 등
"""
from __future__ import annotations
import argparse, json, pathlib, sys, time
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
H4_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'H4'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted' / 'HIMG'

sys.path.insert(0, str(ROOT / 'tools' / 'converter'))
from convert_bm_v2 import decode_file


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--groups', nargs='+', default=['000','001','002','003','004','005','006','007'])
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {'groups': {}, 'errors': []}
    total_frames = 0
    total_files = 0
    t0 = time.time()

    for group in args.groups:
        src = H4_DIR / group
        if not src.exists():
            continue
        out_grp = OUT_DIR / group
        out_grp.mkdir(parents=True, exist_ok=True)

        g_frames = 0
        g_files = 0
        g_errors = []
        for f in sorted(src.iterdir()):
            if not f.is_file():
                continue
            file_out = out_grp / f.name
            file_out.mkdir(parents=True, exist_ok=True)
            try:
                r = decode_file(f, file_out)
                g_frames += r.get('rendered', 0)
                g_files += 1
            except Exception as e:
                g_errors.append({'file': f.name, 'error': str(e)})

        summary['groups'][group] = {
            'files': g_files,
            'frames_rendered': g_frames,
            'errors': len(g_errors),
            'error_details': g_errors,
        }
        total_frames += g_frames
        total_files += g_files
        summary['errors'].extend(g_errors)
        print(f'  H4/{group}/: {g_files} files -> {g_frames} frames, {len(g_errors)} errors')

    summary['total_files'] = total_files
    summary['total_frames'] = total_frames
    summary['elapsed_sec'] = round(time.time() - t0, 1)

    out_json = OUT_DIR / '_himg_decode_summary.json'
    out_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'\nTotal: {total_files} files, {total_frames} frames decoded')
    print(f'Errors: {len(summary["errors"])}')
    print(f'Elapsed: {summary["elapsed_sec"]}s')
    print(f'-> {out_json}')


if __name__ == '__main__':
    sys.exit(main())
