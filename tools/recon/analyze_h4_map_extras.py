"""Hero4 _MAP_M_ extras 영역 의미론 분석기 (2026-05-18 후속4).

검증된 layout (sec[0..3]):
    8B record = type(1) + sub_a(1) + 0xff(1) + obj_id(1) + x(2 LE) + y(2 LE)

검증 결과 (97 map × 16,358 sec[0..3] records):
    - sub[1] = 0xff 100%      → 고정 marker / category separator
    - x, y   = pixel coords (16px tile)
                max_x/16+1 = map width tiles, max_y/16+1 = map height tiles
                map size = tile_w × tile_h 와 정확히 일치
    - sub[2] (obj_id) ∈ [0, 246] 100%  → global OBJ id, 0 out-of-bounds
                0..99  = OBJ/000/_OBJ_NNN  (small 16×16 icons)
                100..199 = OBJ/001/_OBJ_(NNN-100)  (variable characters)
                200..246 = OBJ/002/_OBJ_(NNN-200)  (variable items)
    - type   = bit flags, 99% 가 0 or 0x40 (orientation/flip 추정)
    - sub[0] (sub_a) = state/variant byte (특히 sec[3] 에서 (40, obj_id) 페어)

Section 의미 추정 (resource pool 크기 + group 비율):
    sec[0] (8022 rec, 135 unique): 47% g000 + 18% g001 + 34% g002
        → terrain decoration / props (가장 큰 layer, 작은 icon + 아이템 위주)
    sec[1] (6010 rec, 164 unique): 47% g000 + 23% g001 + 28% g002
        → secondary decoration / interactive objects
    sec[2] (1956 rec, 113 unique): 52% g000 + 45% g001 + 2% g002
        → NPC/character mix (g002 사실상 제외 — 캐릭터 위주)
    sec[3] (370 rec, 19 unique): 32% g000 + 60% g001 + 6% g002
        → 특수 캐릭터/이벤트 객체 (좁은 자원 풀 = 보스/포털/이벤트 NPC)

sec[4+] schema 다름 (96/97 파일에서 mis-parsing 의심). 1B count + variable-length
records 또는 별도 event/dialog 블록. Ghidra 후 확정.
"""
from __future__ import annotations
import argparse, json, pathlib, sys
from collections import Counter, defaultdict


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DEFAULT_IN = ROOT / 'work' / 'h4' / 'converted' / 'map_extras_parsed.json'
DEFAULT_OUT = ROOT / 'work' / 'h4' / 'converted' / 'map_extras_semantics.json'

OBJ_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'OBJ'


def obj_id_to_path(obj_id: int) -> str:
    """Map global OBJ id to filesystem path.
    NB: OBJ filenames preserve the global id (000..246), grouped only by directory.
        e.g. obj_id=199 -> OBJ/001/_OBJ_199 (NOT _OBJ_099).
    """
    if obj_id < 100:
        return f'OBJ/000/_OBJ_{obj_id:03d}'
    if obj_id < 200:
        return f'OBJ/001/_OBJ_{obj_id:03d}'
    if obj_id < 247:
        return f'OBJ/002/_OBJ_{obj_id:03d}'
    return f'OBJ/?/_OBJ_{obj_id:03d}'


def obj_id_to_group(obj_id: int) -> str:
    if obj_id < 100: return '000'
    if obj_id < 200: return '001'
    if obj_id < 247: return '002'
    return '???'


def annotate_records(parsed_data: dict) -> dict:
    """parsed_data = output of parse_h4_map_extras.py"""
    annotated = []
    for entry in parsed_data['parsed']:
        new_secs = []
        for sec_idx, sec in enumerate(entry['sections']):
            new_recs = []
            for rec in sec['records']:
                obj_id = rec['sub'][2]
                new_recs.append({
                    **rec,
                    'obj_id': obj_id,
                    'obj_group': obj_id_to_group(obj_id),
                    'obj_path': obj_id_to_path(obj_id),
                    'state': rec['sub'][0],
                    'tile_x': rec['x'] // 16,
                    'tile_y': rec['y'] // 16,
                    'flip_x': bool(rec['type'] & 0x40),
                })
            new_secs.append({
                'section_index': sec_idx,
                'count': sec['count'],
                'records': new_recs,
            })
        annotated.append({
            **{k: v for k, v in entry.items() if k != 'sections'},
            'sections': new_secs,
        })
    return {
        **{k: v for k, v in parsed_data.items() if k != 'parsed'},
        'parsed': annotated,
        'schema_note': 'sub[2] = global OBJ id (0..99=g000, 100..199=g001, 200..246=g002)',
    }


def summary_stats(parsed: list) -> dict:
    """Aggregate stats across all maps."""
    out = {
        'per_section': {},
        'top_objects_overall': [],
    }
    obj_counter = Counter()
    for entry in parsed:
        for sec_idx, sec in enumerate(entry['sections']):
            for rec in sec['records']:
                obj_counter[rec['obj_id']] += 1
    out['top_objects_overall'] = [
        {'obj_id': i, 'obj_path': obj_id_to_path(i), 'count': c}
        for i, c in obj_counter.most_common(20)
    ]
    for sec_idx in range(5):
        sec_objs = Counter()
        sec_states = Counter()
        for entry in parsed:
            if sec_idx < len(entry['sections']):
                for rec in entry['sections'][sec_idx]['records']:
                    sec_objs[rec['obj_id']] += 1
                    sec_states[rec['state']] += 1
        if sec_objs:
            out['per_section'][f'sec[{sec_idx}]'] = {
                'total_records': sum(sec_objs.values()),
                'unique_objects': len(sec_objs),
                'top10_objects': [
                    {'obj_id': i, 'obj_path': obj_id_to_path(i), 'count': c}
                    for i, c in sec_objs.most_common(10)
                ],
                'top10_states': [
                    {'state': s, 'count': c} for s, c in sec_states.most_common(10)
                ],
            }
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--in_', '-i', default=str(DEFAULT_IN),
                    help='Input map_extras_parsed.json')
    ap.add_argument('--out', '-o', default=str(DEFAULT_OUT),
                    help='Output map_extras_semantics.json')
    args = ap.parse_args()

    with open(args.in_, encoding='utf-8') as fp:
        data = json.load(fp)

    annotated = annotate_records(data)
    stats = summary_stats(annotated['parsed'])
    annotated['stats'] = stats

    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fp:
        json.dump(annotated, fp, ensure_ascii=False, indent=2)

    print(f'Annotated {len(annotated["parsed"])} maps -> {args.out}')
    print()
    print('=== Top 20 most-placed objects across all maps ===')
    for item in stats['top_objects_overall']:
        print(f'  {item["obj_path"]:30}  x{item["count"]}')
    print()
    for k, v in stats['per_section'].items():
        print(f'=== {k}: total={v["total_records"]}, unique={v["unique_objects"]} ===')
        print(f'  Top10 objects:')
        for item in v['top10_objects']:
            print(f'    {item["obj_path"]:30}  x{item["count"]}')
        print(f'  Top5 states: {[(s["state"], s["count"]) for s in v["top10_states"][:5]]}')
        print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
