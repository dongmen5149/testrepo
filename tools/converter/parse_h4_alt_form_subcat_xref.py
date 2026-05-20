"""Hero4 Round 111 — alt-form 24 × type=0 sub-category cross-check (R103+R109 후속).

R103 의 4 alt-form 카테고리 (enhanced_primary/state_transform/variant/summon_combo)
와 R109 의 11 type=0 sub-category 의 대응 관계 검증.

핵심 질문:
1. R103 의 mode-2 advanced layer 가설이 R109 sub-cat 으로 어떻게 분포?
2. 24 alt-form 중 type=0 이 몇 개? (나머지 5/20/25 damage_type 은?)
3. R110 milestone 의 mode_1 advanced layer 12 = DASH+TRAP+DEBUFF+COMBO 가설 검증
"""
from __future__ import annotations
import json
import pathlib
from collections import defaultdict, Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ALT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_alt_form_mode.json'
T0_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_type0_subcategory.json'
DT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_damage_type_semantics.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def load_subcat_map() -> dict[tuple[str, str], str]:
    """name (file, name) → R109 sub-category."""
    d = json.loads(T0_JSON.read_text(encoding='utf-8'))
    out = {}
    for cat, info in d['category_summary'].items():
        for sk in info['skills']:
            out[(sk['file'], sk['name'])] = cat
    return out


def load_dtype_map() -> dict[tuple[str, str], int]:
    """name (file, name) → R104 damage_type byte[5] enum."""
    d = json.loads(DT_JSON.read_text(encoding='utf-8'))
    out = {}
    for dtype_str, info in d['type_summary'].items():
        dtype = int(dtype_str)
        for sk in info['skills']:
            out[(sk['file'], sk['name'])] = dtype
    return out


def main() -> int:
    alt = json.loads(ALT_JSON.read_text(encoding='utf-8'))
    subcat = load_subcat_map()
    dtype = load_dtype_map()

    alt_forms = alt['alt_skill_analysis']
    assert len(alt_forms) == 24, f'expected 24 alt-forms, got {len(alt_forms)}'

    # Cross-check each alt-form
    xref_rows = []
    for af in alt_forms:
        key = (af['file'], af['name'])
        sub = subcat.get(key, '(non-type0)')
        dt = dtype.get(key, '?')
        xref_rows.append({
            'file': af['file'],
            'name': af['name'],
            'r103_category': af['category'],
            'r109_sub_category': sub,
            'damage_type_byte5': dt,
            'mp': af['mp_cost'],
            'dmg': af['damage_le16'],
            'lvl': af['skill_lvl_req'],
        })

    # 1. damage_type distribution
    dt_dist = Counter(r['damage_type_byte5'] for r in xref_rows)

    # 2. R103 cat × R109 sub-cat matrix
    matrix: dict[str, Counter] = defaultdict(Counter)
    for r in xref_rows:
        matrix[r['r103_category']][r['r109_sub_category']] += 1

    # 3. R110 mode_1 advanced layer hypothesis test
    advanced_subcats = {'ACTIVE_DASH', 'ACTIVE_TRAP', 'ACTIVE_DEBUFF', 'ACTIVE_COMBO'}
    advanced_count = sum(1 for r in xref_rows if r['r109_sub_category'] in advanced_subcats)

    # 4. Per-class breakdown
    per_class: dict[str, list] = defaultdict(list)
    for r in xref_rows:
        per_class[r['file']].append(r)

    # 5. R103 vs R109 alignment
    alignments = {
        'enhanced_primary -> ACTIVE_AOE/ELEMENT': 0,
        'state_transform -> ACTIVE_BUFF_SELF/PASSIVE': 0,
        'variant -> ACTIVE_ELEMENT/MULTI/AOE/DEBUFF': 0,
        'summon_combo -> ACTIVE_COMBO': 0,
    }
    for r in xref_rows:
        c103, c109 = r['r103_category'], r['r109_sub_category']
        if c103 == 'enhanced_primary' and c109 in ('ACTIVE_AOE', 'ACTIVE_ELEMENT', 'PASSIVE_DEEP'):
            alignments['enhanced_primary -> ACTIVE_AOE/ELEMENT'] += 1
        if c103 == 'state_transform' and c109 in ('ACTIVE_BUFF_SELF', 'PASSIVE_DEEP'):
            alignments['state_transform -> ACTIVE_BUFF_SELF/PASSIVE'] += 1
        if c103 == 'variant' and c109 in ('ACTIVE_ELEMENT', 'ACTIVE_MULTI_HIT', 'ACTIVE_AOE',
                                          'ACTIVE_DEBUFF', 'ACTIVE_DASH', 'ACTIVE_BUFF_SELF'):
            alignments['variant -> ACTIVE_ELEMENT/MULTI/AOE/DEBUFF'] += 1
        if c103 == 'summon_combo' and c109 == 'ACTIVE_COMBO':
            alignments['summon_combo -> ACTIVE_COMBO'] += 1

    out = {
        'round': 111,
        'r103_r109_followup': 'alt-form 24 × type=0 sub-category cross-check',
        'alt_form_xref': xref_rows,
        'damage_type_distribution': dict(dt_dist),
        'r103_vs_r109_matrix': {
            r103: dict(c) for r103, c in matrix.items()
        },
        'r110_advanced_layer_test': {
            'hypothesis': 'mode_1 advanced layer = ACTIVE_{DASH,TRAP,DEBUFF,COMBO} (12 type=0 skills total)',
            'alt_form_in_advanced': advanced_count,
            'total_type0_advanced': 12,
            'advanced_in_alt_form_ratio': f'{advanced_count}/12 ({advanced_count*100//12}%)',
            'interpretation': (
                'alt-form 중 advanced layer 비율 = {pc:.1%}'
                .format(pc=advanced_count / 12 if advanced_count else 0)
            ),
        },
        'r103_r109_alignment': alignments,
        'per_class_breakdown': {
            cls: [{
                'name': r['name'],
                'r103': r['r103_category'],
                'r109': r['r109_sub_category'],
                'dt': r['damage_type_byte5'],
            } for r in rows]
            for cls, rows in per_class.items()
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_alt_form_subcat_xref.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    # Print
    print('=== R111 alt-form 24 × type=0 sub-category cross-check ===\n')
    print(f'damage_type distribution across 24 alt-forms: {dict(dt_dist)}')
    print()
    print('=== Per alt-form xref ===')
    for r in xref_rows:
        print(f"  {r['file'][-5:]} {r['name']:14s} R103={r['r103_category']:18s} "
              f"R109={r['r109_sub_category']:18s} dt={r['damage_type_byte5']} "
              f"MP={r['mp']:3d} dmg={r['dmg']:4d} lvl={r['lvl']}")
    print()
    print('=== R103 cat × R109 sub-cat matrix ===')
    all_r109 = sorted({c for cnts in matrix.values() for c in cnts})
    header = '  R103↓ \\ R109→ | ' + ' | '.join(c[:7] for c in all_r109)
    print(header)
    for r103, cnts in matrix.items():
        row = f'  {r103:20s}'
        for c in all_r109:
            row += f' | {cnts.get(c, 0):7d}'
        print(row)
    print()
    print('=== R110 advanced-layer hypothesis test ===')
    print(f"  alt-form 중 ACTIVE_{{DASH,TRAP,DEBUFF,COMBO}} sub-cat = {advanced_count}/12 "
          f"= {advanced_count*100//12 if advanced_count else 0}%")
    print()
    print('=== R103 → R109 alignment ===')
    for k, v in alignments.items():
        print(f'  {k:50s} {v}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
