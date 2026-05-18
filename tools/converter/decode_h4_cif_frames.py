"""Hero4 CIF 117 파일 animation frame 완전 디코더.

검증된 schema (Hero3 decoder 그대로 작동):

Hero CIF (slot_count=8, 4 files):
    0x0a marker 기반 가변 길이 frame entries
    각 frame entry = 41 bytes
        byte 0   : 0x0a marker
        byte 1   : ? (보통 0)
        byte 2   : frame meta (보통 0x0f = 15)
        byte 3+  : 9 cells × 4 bytes = 36 byte cell stream
            cell = [x_s8, y_s8, sprite_ref_u8, flag_u8]
        총: 1 + 1 + 1 + 36 = 39B + 2B trailer/padding = 41B
    Hero3 의 `find_frames()` 가 그대로 동작.

Enemy/NPC CIF (slot_count=1~6, 113 files):
    4-byte cell stream (frame 헤더 없음)
    각 cell = 4 byte:
        byte 0   : packed flags
            bit 7      = special (decoder 가 별도 처리)
            bits 5..6  = orientation (0/1/2/3=sentinel)
            bits 0..4  = sprite ref (5-bit, 0..31)
        byte 1   : x (signed s8)
        byte 2   : y (signed s8)
        byte 3   : extra/flag
    Sentinel cell (byte 0 == 0x7f) = frame separator
    Hero3 의 `parse_boss_cells()` + `split_frames_by_sentinel()` 그대로 동작.

검증 결과:
    - hero CIFs (_H_001~004): 973~1879 frames per character
    - enemy CIFs: top sprite refs 일관되게 0..31 범위 (0, 1, 2, 10, 31)
    - 51-slot sprite pool 중 ref 1..31 (5-bit) 만 enemy 가 사용 → 32..51 슬롯은 hero 전용
"""
from __future__ import annotations
import argparse, json, pathlib, sys
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CIF_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'H4' / 'CIF'
OUT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'cif_frames_decoded.json'

sys.path.insert(0, str(ROOT / 'tools' / 'recon'))
from analyze_cif import (  # noqa: E402
    find_frames, parse_boss_cells, split_frames_by_sentinel,
    boss_cif_summary, s8,
)


def parse_hero_frames(data: bytes) -> list[dict]:
    """Hero CIF (slot=8): 0x0a marker frames with 9-cell payload."""
    frames = []
    offsets = find_frames(data, start=10)
    for f_idx, off in enumerate(offsets):
        if off + 41 > len(data):
            break
        rec = data[off:off + 41]
        cells = []
        for k in range(9):
            o = 3 + k * 4
            if o + 4 > len(rec):
                break
            cells.append({
                'idx': k,
                'x': s8(rec[o]),
                'y': s8(rec[o + 1]),
                'sprite_ref': rec[o + 2],
                'flag': rec[o + 3],
            })
        frames.append({
            'frame_idx': f_idx,
            'offset': off,
            'meta_byte1': rec[1],
            'meta_byte2': rec[2],
            'cells': cells,
        })
    return frames


def decode_cif_file(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    if len(data) < 2:
        return {'file': path.name, 'error': 'too_short'}
    slot_count = data[0]
    category = data[1]
    indices = list(data[2:2 + slot_count])
    body_offset = 2 + slot_count

    result = {
        'file': path.name,
        'size': len(data),
        'slot_count': slot_count,
        'category': category,
        'indices': indices,
        'body_offset': body_offset,
    }

    if slot_count == 8:
        # Hero CIF
        frames = parse_hero_frames(data)
        result['mode'] = 'hero_41B'
        result['frame_count'] = len(frames)
        # Stat: unique sprite_refs across all cells
        all_refs = []
        for f in frames:
            for c in f['cells']:
                all_refs.append(c['sprite_ref'])
        result['ref_stats'] = {
            'total_cells': len(all_refs),
            'unique_refs': len(set(all_refs)),
            'top10_refs': Counter(all_refs).most_common(10),
            'ref_range': [min(all_refs), max(all_refs)] if all_refs else [0, 0],
        }
        result['frames_sample'] = frames[:3]
        result['frames'] = frames  # full data
    else:
        # Enemy/NPC CIF — 4-byte cell stream
        body = data[body_offset:]
        cells = parse_boss_cells(body)
        seg_frames = split_frames_by_sentinel(cells)
        result['mode'] = 'enemy_4B'
        result['cells_total'] = len(cells)
        result['sentinel_count'] = sum(1 for c in cells if c['is_sentinel'])
        result['special_count'] = sum(1 for c in cells if c['special'])
        result['frame_count'] = len(seg_frames)
        refs = [c['ref'] for c in cells if not c['is_sentinel']]
        result['ref_stats'] = {
            'total_cells': len(cells),
            'unique_refs': len(set(refs)),
            'top10_refs': Counter(refs).most_common(10),
            'ref_range': [min(refs), max(refs)] if refs else [0, 0],
        }
        # First 3 frames
        result['frames_sample'] = [
            {
                'frame_idx': i,
                'cell_count': len(f),
                'cells': f[:6],  # first 6 cells per frame
            }
            for i, f in enumerate(seg_frames[:3])
        ]

    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=str(OUT_JSON))
    ap.add_argument('--full_frames', action='store_true',
                    help='Include full frame data (large output, default sample only)')
    args = ap.parse_args()

    files = sorted(CIF_DIR.glob('_H_*_CIF'))
    decoded = []
    mode_counter = Counter()
    err_count = 0

    for f in files:
        try:
            r = decode_cif_file(f)
            if not args.full_frames and 'frames' in r:
                del r['frames']  # keep only frames_sample
            decoded.append(r)
            mode_counter[r.get('mode', 'error')] += 1
            if 'error' in r:
                err_count += 1
        except Exception as e:
            decoded.append({'file': f.name, 'error': str(e)})
            err_count += 1

    out = {
        'files': len(decoded),
        'modes': dict(mode_counter),
        'errors': err_count,
        'decoded': decoded,
    }
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    print(f'Decoded {len(decoded)} CIF files -> {args.out}')
    print(f'Modes: {dict(mode_counter)}')
    print(f'Errors: {err_count}')

    print(f'\n=== Hero CIFs (slot=8) frame counts ===')
    for r in decoded:
        if r.get('mode') == 'hero_41B':
            rs = r.get('ref_stats', {})
            print(f'  {r["file"]:18}: {r["frame_count"]:5} frames, '
                  f'{rs.get("total_cells", 0):6} cells, '
                  f'ref range={rs.get("ref_range")} unique={rs.get("unique_refs")}')
            print(f'    top refs: {rs.get("top10_refs", [])[:5]}')

    print(f'\n=== Enemy CIFs (slot=1~6) sample ===')
    enemy_samples = [r for r in decoded if r.get('mode') == 'enemy_4B'][:5]
    for r in enemy_samples:
        rs = r.get('ref_stats', {})
        print(f'  {r["file"]:18} (slot={r["slot_count"]} cat={r["category"]}): '
              f'{r["frame_count"]} frames, {r["cells_total"]} cells, '
              f'sentinels={r["sentinel_count"]}, specials={r["special_count"]}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
