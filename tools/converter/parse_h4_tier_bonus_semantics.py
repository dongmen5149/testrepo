"""Hero4 Round 100 — bonus_id=0 + tier_value semantic analysis (R94 후속).

R94 의 `_H_SA` ability slot 의 tier_value 와 bonus_id 의미 확정.

R99 tutorial 단서: "고레벨로 올라갈 수록 소모되는 포인트의 양이 많아짐"
→ tier_value = **진화포인트 소모량** (consumption cost per tier)

bonus_id=0 vs bonus_id>0:
- bonus_id=0 (5 skills: 13, 18, 21, 22, 37): self-only upgrade (no cross-tree bonus)
- bonus_id>0 (3 skills: 12→18, 15→19, 16→17): cross-tree bonus to linked passive

S001 사격 skill tree 구조:
    active (cost tier 10/20/30) → linked passive (bonus +5/10/15 or +10/20/30):
        12 동시사격 → 18 암즈강화 (+5/10/15)
        15 에이밍샷 → 19 속사 (+5/10/15)
        16 암즈트랩 → 17 회피증가 (+10/20/30)
    passive (cost tier 10/20/30, no side bonus):
        18 암즈강화 (자체 강화 가능 OR 12 동시사격 통해 간접 강화)

Tier_value progression 패턴 (8 skills):
    diff +5  : skill 21 (마검공격) — cheapest
    diff +10 : skill 12-18 (S001 5 skills) — standard
    diff +15 : skill 22 (텔레포트소드)
    diff +20 : skill 37 (마법강화) — most expensive
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SAS_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_sa_ability_skill_map.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def analyze() -> dict:
    sas = json.loads(SAS_JSON.read_text(encoding='utf-8'))
    abilities = sas['ability_skill_summary']

    enhanced = []
    for a in abilities:
        tv = a['tier_values']
        diffs = [tv[i+1] - tv[i] for i in range(len(tv)-1)]
        is_arithmetic = len(set(diffs)) == 1
        diff = diffs[0] if is_arithmetic else None
        bonus = a.get('bonus')
        enhanced.append({
            'skill_id': a['skill_id'],
            'class_name': a['class_name'],
            'skill_name': a['skill_name'],
            'tier_values': tv,
            'tier_diffs': diffs,
            'is_arithmetic_progression': is_arithmetic,
            'arithmetic_step': diff,
            'has_bonus_chain': bonus is not None,
            'bonus_target_id': bonus['bonus_skill_id'] if bonus else 0,
            'bonus_target_name': bonus['bonus_name'] if bonus else None,
            'bonus_values': bonus['bonus_values'] if bonus else None,
        })

    # Group by has_bonus
    with_bonus = [e for e in enhanced if e['has_bonus_chain']]
    no_bonus = [e for e in enhanced if not e['has_bonus_chain']]

    return {
        'all_abilities': enhanced,
        'with_bonus_chain': with_bonus,
        'no_bonus_self_only': no_bonus,
        'arithmetic_count': sum(1 for e in enhanced if e['is_arithmetic_progression']),
        'tier_value_diff_groups': {
            5:  [e['skill_name'] for e in enhanced if e['arithmetic_step'] == 5],
            10: [e['skill_name'] for e in enhanced if e['arithmetic_step'] == 10],
            15: [e['skill_name'] for e in enhanced if e['arithmetic_step'] == 15],
            20: [e['skill_name'] for e in enhanced if e['arithmetic_step'] == 20],
        },
    }


def main() -> int:
    a = analyze()

    out = {
        'round': 100,
        'milestone': 'Hero4 자동 분석 100 round 마일스톤',
        'r94_followup': {
            'tier_value_semantic': '진화포인트 소모량 (R99 tutorial: "고레벨일수록 소모 포인트 증가")',
            'bonus_id_semantic': '0 = self-only upgrade, >0 = cross-tree bonus to linked passive',
        },
        'arithmetic_progression_verification': {
            'count_arithmetic': a['arithmetic_count'],
            'total_abilities': len(a['all_abilities']),
            'all_arithmetic': a['arithmetic_count'] == len(a['all_abilities']),
        },
        'tier_value_cost_classes': a['tier_value_diff_groups'],
        'bonus_chain_summary': {
            'with_bonus_count': len(a['with_bonus_chain']),
            'no_bonus_count': len(a['no_bonus_self_only']),
            'cross_tree_links': [
                f'{e["skill_name"]} (id {e["skill_id"]}) → {e["bonus_target_name"]} (id {e["bonus_target_id"]})'
                for e in a['with_bonus_chain']
            ],
        },
        'all_abilities': a['all_abilities'],
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_tier_bonus_semantics.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print('=== Tier_value semantic ===')
    print(f'  All 8/8 abilities show arithmetic progression: {out["arithmetic_progression_verification"]["all_arithmetic"]}')
    print(f'  Cost-class groups (step size):')
    for step, names in a['tier_value_diff_groups'].items():
        if names:
            print(f'    +{step:2d}: {names}')
    print()
    print('=== Bonus chain summary ===')
    print(f'  with bonus: {len(a["with_bonus_chain"])}/8  (all in S001 사격 self-tree)')
    print(f'  no  bonus: {len(a["no_bonus_self_only"])}/8')
    for link in out['bonus_chain_summary']['cross_tree_links']:
        print(f'    {link}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
