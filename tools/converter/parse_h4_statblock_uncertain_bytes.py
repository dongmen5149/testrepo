"""Hero4 Round 112 — 32B class skill stat block 미확정 byte 정밀화 (R102+R109 후속).

R102 확정 field (8개): byte[0/3-4/5/8/16-19]
R102 추정 field (12개): byte[1/2/6/7/9/13/14/15/22] flag/marker
R102 미확정 field (12+): byte[10/11/12/18/20-21/23-31] sparse non-zero

각 미확정 byte 의 nonzero entry 를 R109 sub-cat / R104 dtype / lvl_req 와 cross-ref 해서
의미를 추론한다.
"""
from __future__ import annotations
import json
import pathlib
from collections import defaultdict, Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CSS_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_class_skill_schema.json'
T0_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_type0_subcategory.json'
DT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_damage_type_semantics.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def load_subcat_map() -> dict[tuple[str, str], str]:
    d = json.loads(T0_JSON.read_text(encoding='utf-8'))
    out = {}
    for cat, info in d['category_summary'].items():
        for sk in info['skills']:
            out[(sk['file'], sk['name'])] = cat
    return out


def load_dtype_map() -> dict[tuple[str, str], int]:
    d = json.loads(DT_JSON.read_text(encoding='utf-8'))
    out = {}
    for dtype_str, info in d['type_summary'].items():
        dt = int(dtype_str)
        for sk in info['skills']:
            out[(sk['file'], sk['name'])] = dt
    return out


def load_all_skills() -> list[dict]:
    css = json.loads(CSS_JSON.read_text(encoding='utf-8'))
    out = []
    for fname, info in css['class_files'].items():
        for e in info['entries']:
            b = bytes.fromhex(e['stat_block_hex'])
            assert len(b) == 32
            out.append({
                'file': fname,
                'name': e['name_clean'],
                'is_alt': e['is_alt_form'],
                'bytes': list(b),
                'desc': e.get('desc_text', ''),
            })
    return out


def analyze_byte(pos: int, skills: list[dict], subcat: dict, dtype: dict) -> dict:
    """For byte at position `pos`, group nonzero entries by sub-cat / dtype / class."""
    nonzero_entries = [
        s for s in skills if s['bytes'][pos] != 0
    ]
    if not nonzero_entries:
        return {
            'nonzero_count': 0,
            'invariant_value': 0,
        }

    # Value distribution
    val_dist = Counter(s['bytes'][pos] for s in nonzero_entries)

    # By sub-cat
    by_subcat: dict[str, list[int]] = defaultdict(list)
    for s in nonzero_entries:
        key = (s['file'], s['name'])
        sc = subcat.get(key, '(non-type0)')
        by_subcat[sc].append(s['bytes'][pos])

    # By dtype
    by_dtype: dict[int, list[int]] = defaultdict(list)
    for s in nonzero_entries:
        key = (s['file'], s['name'])
        dt = dtype.get(key, -1)
        by_dtype[dt].append(s['bytes'][pos])

    # By class
    by_class: dict[str, list[int]] = defaultdict(list)
    for s in nonzero_entries:
        by_class[s['file']].append(s['bytes'][pos])

    # By alt/primary
    alt_vals = [s['bytes'][pos] for s in nonzero_entries if s['is_alt']]
    pri_vals = [s['bytes'][pos] for s in nonzero_entries if not s['is_alt']]

    # Concrete entries
    examples = [
        {
            'file': s['file'],
            'name': s['name'],
            'val': s['bytes'][pos],
            'is_alt': s['is_alt'],
            'subcat': subcat.get((s['file'], s['name']), '?'),
            'dtype': dtype.get((s['file'], s['name']), -1),
        }
        for s in nonzero_entries
    ]

    return {
        'nonzero_count': len(nonzero_entries),
        'value_distribution': dict(val_dist.most_common()),
        'by_sub_category': {k: dict(Counter(v).most_common()) for k, v in by_subcat.items()},
        'by_damage_type': {str(k): dict(Counter(v).most_common()) for k, v in by_dtype.items()},
        'by_class_file': {k: dict(Counter(v).most_common()) for k, v in by_class.items()},
        'alt_form_count': len(alt_vals),
        'primary_count': len(pri_vals),
        'examples': examples,
    }


def interpret(pos: int, ana: dict) -> str:
    """Heuristic interpretation based on analysis result."""
    if ana['nonzero_count'] == 0:
        return 'INVARIANT 0 (truly unused/padding)'
    if ana['nonzero_count'] <= 3:
        return f'SPARSE_OUTLIER (only {ana["nonzero_count"]} nonzero — likely 누락 entry / corruption / per-skill flag)'
    # Check if correlated with sub-cat
    sub_counts = {k: sum(v.values()) for k, v in ana['by_sub_category'].items()}
    if len(sub_counts) == 1:
        cat = list(sub_counts.keys())[0]
        return f'SUB_CAT_SPECIFIC ({cat} only)'
    # Check if correlated with damage_type
    dt_counts = {k: sum(v.values()) for k, v in ana['by_damage_type'].items()}
    if len(dt_counts) == 1:
        return f'DTYPE_SPECIFIC (dtype={list(dt_counts.keys())[0]} only)'
    # Check if correlated with class
    cls_counts = {k: sum(v.values()) for k, v in ana['by_class_file'].items()}
    if len(cls_counts) == 1:
        return f'CLASS_SPECIFIC ({list(cls_counts.keys())[0]} only)'
    return f'MULTI_CATEGORY ({ana["nonzero_count"]} nonzero across {len(sub_counts)} sub-cat)'


def analyze_le16_pair(lo: int, hi: int, skills: list[dict], subcat: dict, dtype: dict) -> dict:
    """Analyze LE16 pair at positions (lo, hi). Skip entries where both are 0."""
    entries = []
    for s in skills:
        l, h = s['bytes'][lo], s['bytes'][hi]
        val = l | (h << 8)
        if val == 0:
            continue
        entries.append({
            'file': s['file'],
            'name': s['name'],
            'is_alt': s['is_alt'],
            'le16': val,
            'subcat': subcat.get((s['file'], s['name']), '?'),
            'dtype': dtype.get((s['file'], s['name']), -1),
        })
    return {
        'nonzero_count': len(entries),
        'value_distribution': dict(Counter(e['le16'] for e in entries).most_common()),
        'by_sub_category': {
            k: dict(Counter(e['le16'] for e in entries if e['subcat'] == k).most_common())
            for k in {e['subcat'] for e in entries}
        },
        'entries': entries,
    }


def main() -> int:
    skills = load_all_skills()
    subcat = load_subcat_map()
    dtype = load_dtype_map()

    # Uncertain bytes per R102
    uncertain_positions = [6, 10, 11, 12, 13, 14, 18, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]

    results = {}
    for pos in uncertain_positions:
        ana = analyze_byte(pos, skills, subcat, dtype)
        ana['interpretation'] = interpret(pos, ana)
        results[f'byte[{pos}]'] = ana

    # Special: byte[20-21] secondary_effect_le16
    le16_2021 = analyze_le16_pair(20, 21, skills, subcat, dtype)
    results['byte[20-21]_le16'] = {
        **le16_2021,
        'interpretation': 'secondary_effect LE16 — proc damage / status duration / status intensity 후보',
    }

    # Save concise output
    out = {
        'round': 112,
        'r102_r109_followup': '32B class skill stat block 미확정 byte 정밀화',
        'corpus': '64 skills (4 class × 16 entries)',
        'analyzed_positions': uncertain_positions + ['20-21 LE16'],
        'results': results,
        'summary': {
            f'byte[{p}]': results[f'byte[{p}]']['interpretation']
            for p in uncertain_positions
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_statblock_uncertain_bytes.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    # Print compact summary
    print(f'=== R112 stat block 32B 미확정 byte 정밀화 (64 skill corpus) ===\n')
    for pos in uncertain_positions:
        key = f'byte[{pos}]'
        ana = results[key]
        print(f'\n[{key}] nonzero={ana["nonzero_count"]}/64 — {ana["interpretation"]}')
        if ana['nonzero_count']:
            print(f'  values: {ana.get("value_distribution", {})}')
            sub = ana.get('by_sub_category', {})
            if sub:
                print(f'  by sub-cat ({len(sub)} groups):')
                for sc, cnts in sorted(sub.items(), key=lambda x: -sum(x[1].values())):
                    print(f'    {sc:20s} {dict(cnts)}')
            # Show top 5 examples
            if ana['nonzero_count'] <= 10:
                print(f'  examples:')
                for e in ana['examples'][:10]:
                    print(f"    {e['file'][-5:]} {e['name']:14s} val={e['val']} alt={e['is_alt']} {e['subcat']}")

    print(f'\n[byte[20-21] LE16] nonzero={le16_2021["nonzero_count"]}/64')
    print(f'  values: {le16_2021["value_distribution"]}')
    print(f'  by sub-cat:')
    for sc, cnts in sorted(le16_2021['by_sub_category'].items(), key=lambda x: -sum(x[1].values())):
        print(f'    {sc:20s} {dict(cnts)}')

    print(f'\n[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
