"""
Hero3 _cif → JSON 메타데이터.

헤더:
    uint8  slot_count          // 0..8 (hero=8, enemy=1~5, boss=1)
    uint8  category            // 0=hero/boss, 1=enemy, 2=일부 보스
    uint8  sprite_indices[slot_count]
    bytes  animation_data[]    // hero=41B fixed stride, boss/enemy=4B cell stream

사용:
    python convert_cif.py <input.cif> <output.json>           # header only
    python convert_cif.py <input.cif> <output.json> --boss    # FUN_00098ef8 디코더로 cell 까지 dump
"""
from __future__ import annotations
import sys, json, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'recon'))
from analyze_cif import boss_cif_summary, parse_boss_header, parse_boss_cells, split_frames_by_sentinel


def parse_cif(data: bytes) -> dict:
    if len(data) < 2:
        return {'slot_count': 0, 'category': 0, 'indices': [], 'raw_size': len(data)}
    slot_count = data[0]
    category = data[1]
    end = 2 + slot_count
    indices_bytes = data[2:end] if end <= len(data) else data[2:]
    indices = list(indices_bytes)
    rest = data[end:] if end <= len(data) else b''
    return {
        'slot_count': slot_count,
        'category': category,
        'indices': indices,
        'animation_data_size': len(rest),
        'animation_data_hex_preview': rest[:32].hex() if rest else '',
    }


def parse_cif_boss(data: bytes) -> dict:
    """Boss/enemy cif 를 FUN_00098ef8 디코더로 풀어 cell 까지 dump."""
    h = parse_boss_header(data)
    body = data[h['body_offset']:]
    cells = parse_boss_cells(body)
    frames = split_frames_by_sentinel(cells)
    summary = boss_cif_summary(data)
    return {
        'slot_count': h['slot_count'],
        'category': h['category'],
        'indices': h['indices'],
        'body_bytes': summary['body_bytes'],
        'cells_total': summary['cells_total'],
        'sentinels': summary['sentinels'],
        'specials': summary['specials'],
        'frames': summary['frames'],
        'frame_len_min': summary['frame_len_min'],
        'frame_len_max': summary['frame_len_max'],
        'top_refs': summary['top_refs'],
        'frame_summaries': [
            {
                'idx': i,
                'cells': len(f),
                'orient_dist': _count_field(f, 'orient'),
                'ref_dist': _count_field(f, 'ref'),
            }
            for i, f in enumerate(frames[:64])  # 첫 64 frame 만 dump (boss4 같은 큰 파일 제한)
        ],
    }


def _count_field(cells: list[dict], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for c in cells:
        k = str(c.get(key, ''))
        out[k] = out.get(k, 0) + 1
    return out


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith('-')]
    boss_mode = '--boss' in argv
    if len(args) != 2:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(args[0]), pathlib.Path(args[1])
    data = src.read_bytes()
    out = parse_cif_boss(data) if boss_mode else parse_cif(data)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out, indent=2), encoding='utf-8')
    tag = ' [boss]' if boss_mode else ''
    print(f'  {src.name} -> {dst.name}{tag} (slots={out["slot_count"]}, indices={out["indices"]})')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
