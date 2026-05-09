"""
Hero3 boss/enemy cif 일괄 분석.

FUN_00098ef8 알고리즘을 모든 boss/enemy cif 에 적용해 통계 요약을 JSON 으로 저장.
이후 BM 매핑/베이킹 도구가 이 통계를 입력으로 쓸 수 있다.

사용:
    python tools/recon/dump_boss_cif.py [work/h3/extracted] [out.json]
"""
from __future__ import annotations
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from analyze_cif import boss_cif_summary


def collect(extracted_root: pathlib.Path) -> dict:
    out: dict[str, dict] = {}
    for subdir in ('enemy', 'boss'):
        d = extracted_root / subdir
        if not d.is_dir():
            continue
        for cif in sorted(d.glob('*_cif')):
            data = cif.read_bytes()
            s = boss_cif_summary(data)
            out[f'{subdir}/{cif.name}'] = {
                'size': len(data),
                'header': s['header'],
                'body_bytes': s['body_bytes'],
                'cells_total': s['cells_total'],
                'sentinels': s['sentinels'],
                'specials': s['specials'],
                'frames': s['frames'],
                'frame_len_min': s['frame_len_min'],
                'frame_len_avg': round(s['frame_len_avg'], 2),
                'frame_len_max': s['frame_len_max'],
                'top_refs': s['top_refs'],
            }
    return out


def main(argv: list[str]) -> int:
    root = pathlib.Path(argv[1] if len(argv) > 1 else 'work/h3/extracted')
    out_path = pathlib.Path(argv[2] if len(argv) > 2 else 'work/h3/boss_cif_summary.json')
    if not root.is_dir():
        print(f'! {root} not found', file=sys.stderr)
        return 1
    data = collect(root)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    n_sent = sum(1 for v in data.values() if v['sentinels'] > 0)
    print(f'wrote {out_path} ({len(data)} cif, {n_sent} with sentinels)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
