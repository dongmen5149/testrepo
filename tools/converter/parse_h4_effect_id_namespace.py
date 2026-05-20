"""Hero4 Round 113 — OPTION × class skill effect_id namespace 통합 (R106+R112 후속).

R106: `_ITM_OPTION` 122 entries × 3B `[effect_id][cat 0/15/100][mag]`
R112: class skill 32B byte[20]=effect_id, byte[21-23]=cat/mag triplet

Cross-system 검증: 12 effect_id 가 양 시스템에서 공유 → effect_id namespace 공통화 가능.

핵심: OPTION 의 named entry ("화염발동 L1", "스턴발동 L2") 로부터 effect_id 의미를
직접 추론 → class skill 의 효과 의미 확정.
"""
from __future__ import annotations
import json
import pathlib
from collections import defaultdict, Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CSS_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_class_skill_schema.json'
OPT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_itm_option_struct.json'
T0_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_type0_subcategory.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def load_subcat() -> dict[tuple[str, str], str]:
    d = json.loads(T0_JSON.read_text(encoding='utf-8'))
    out = {}
    for cat, info in d['category_summary'].items():
        for sk in info['skills']:
            out[(sk['file'], sk['name'])] = cat
    return out


def derive_effect_names(opt_entries: list[dict]) -> dict[int, list[str]]:
    """For each effect_id (byte0), collect distinct base names from OPTION entry names.

    Entry names follow pattern "<base> L<tier>" e.g. "HP회복 L1", "화염발동 L2".
    """
    by_id: dict[int, list[str]] = defaultdict(list)
    for e in opt_entries:
        eid = e['payload'][0]
        name = e['name']
        # Strip "L<tier>" suffix
        base = name.rsplit(' L', 1)[0] if ' L' in name else name
        by_id[eid].append(base)
    out = {}
    for eid, names in by_id.items():
        # take most common base name
        c = Counter(names)
        most, _ = c.most_common(1)[0]
        out[eid] = most
    return out


def main() -> int:
    css = json.loads(CSS_JSON.read_text(encoding='utf-8'))
    opt = json.loads(OPT_JSON.read_text(encoding='utf-8'))
    subcat = load_subcat()

    # Build effect_id → name mapping from OPTION
    effect_names = derive_effect_names(opt['entries'])

    # Class skill entries with byte[20] != 0
    cls_entries = []
    for fname, info in css['class_files'].items():
        for e in info['entries']:
            b = bytes.fromhex(e['stat_block_hex'])
            if b[20] == 0:
                continue
            cls_entries.append({
                'file': fname,
                'name': e['name_clean'],
                'is_alt': e['is_alt_form'],
                'effect_id': b[20],
                'b21': b[21],
                'b22': b[22],
                'b23': b[23],
                'desc': (e.get('desc_text', '') or '')[:50],
            })

    # Cross-reference: for each class skill, look up effect_id in OPTION names
    cross = []
    for c in cls_entries:
        eid = c['effect_id']
        opt_name = effect_names.get(eid)
        cross.append({
            **c,
            'option_effect_name': opt_name or '(not in OPTION)',
            'in_option': opt_name is not None,
            'sub_cat': subcat.get((c['file'], c['name']), '(non-type0)'),
        })

    # Stats
    common_ids = sorted({c['effect_id'] for c in cross if c['in_option']})
    only_in_cls = sorted({c['effect_id'] for c in cross if not c['in_option']})

    # Validation table: does the OPTION effect name match the class skill desc?
    # Define semantic match keywords for each common effect_id
    semantic_match = {
        4: ['HP회복', 'HP', '회복력'],
        7: ['SP소모', 'SP의 소모', 'SP소모량'],
        8: ['SP', '최대 SP', 'SP회복', 'SP의'],
        12: ['공격', '공격력', '근접'],
        15: ['공격력', '마법', '암즈사격', '마법공격', '마력'],
        27: ['쿨타임', '쿨'],
        68: ['넉백', '돌격', '띄우기'],  # 관통의영검 has 추가타 띄우기 = 넉백
        75: ['슬로우', '둔화'],
        76: ['스턴', '기절'],
        78: ['화염', '불꽃'],
        79: ['빙결', '얼음', '냉기'],
        80: ['물약', '회복량', '물약의'],
    }
    validation = []
    matches = 0
    for c in cross:
        if not c['in_option']:
            continue
        keys = semantic_match.get(c['effect_id'], [])
        hit_key = next((k for k in keys if k in c['desc']), None)
        if hit_key:
            matches += 1
        validation.append({
            'class_skill': f"{c['file'][-5:]} {c['name']}",
            'effect_id': c['effect_id'],
            'option_effect': c['option_effect_name'],
            'class_skill_desc': c['desc'],
            'semantic_match_key': hit_key,
            'matched': hit_key is not None,
        })

    total_cross = sum(1 for c in cross if c['in_option'])
    match_rate = f'{matches}/{total_cross}'

    out = {
        'round': 113,
        'r106_r112_followup': 'OPTION × class skill effect_id namespace 통합',
        'option_meta': {
            'entries': len(opt['entries']),
            'unique_effect_ids': len(set(e['payload'][0] for e in opt['entries'])),
        },
        'class_skill_meta': {
            'entries_with_b20': len(cls_entries),
            'unique_b20': len({c['effect_id'] for c in cls_entries}),
        },
        'effect_id_namespace': {
            'shared_ids': common_ids,
            'shared_count': len(common_ids),
            'class_skill_only': only_in_cls,
            'option_only': sorted(set(effect_names.keys()) - {c['effect_id'] for c in cls_entries}),
        },
        'effect_id_meanings': {
            str(eid): effect_names[eid] for eid in common_ids
        },
        'cross_validation': {
            'total_shared_class_skill_entries': total_cross,
            'semantic_match_count': matches,
            'match_rate': match_rate,
            'validation_table': validation,
        },
        'all_class_skill_xref': cross,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_effect_id_namespace.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    # Print
    print('=== R113 OPTION × class skill effect_id namespace 통합 ===\n')
    print(f"OPTION: {len(opt['entries'])} entries / "
          f"{len(set(e['payload'][0] for e in opt['entries']))} unique effect_ids")
    print(f"Class skill (byte[20]!=0): {len(cls_entries)} entries / "
          f"{len({c['effect_id'] for c in cls_entries})} unique effect_ids")
    print()
    print(f'SHARED effect_id namespace ({len(common_ids)}): {common_ids}')
    print()
    print('=== Effect ID 의미 (OPTION 의 명명된 entry 기반) ===')
    for eid in common_ids:
        print(f'  {eid:3d}: {effect_names[eid]}')
    print()
    print(f'=== Cross-validation: {match_rate} class skill 가 OPTION 의 effect 의미와 desc 일치 ===')
    for v in validation:
        mark = '✓' if v['matched'] else '✗'
        print(f"  {mark} {v['class_skill']:18s} eid={v['effect_id']:3d} "
              f"OPT={v['option_effect']:14s} | desc={v['class_skill_desc']!r}")
    print()
    print(f'class skill 단독 effect_id ({len(only_in_cls)}): {only_in_cls}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
