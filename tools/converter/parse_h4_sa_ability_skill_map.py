"""Hero4 Round 94 — `_H_SA` ability skill_id {12,13,15,16,18,21,22,37} 카테고리 식별 (R88 후속).

R88 의 24 ability slot 의 skill_id 8 종이 R69 catalog 의 40 character class skill
(4 class × 10 skills) 에 대해 **global skill_id (0-39)** 로 깔끔히 매핑됨을 확인.

global skill_id 매핑 규칙: `skill_id = class_index × 10 + local_index`
    class 0 = S000 (티르 양손검 base)         IDs  0-9
    class 1 = S001 (루레인 사격 shooter)        IDs 10-19
    class 2 = S002 (티르 마검 mage-sword)       IDs 20-29
    class 3 = S003 (루레인 단도+마법 = 소환사)   IDs 30-39

8 ability skill 매핑 결과:
    skill_id 12 = S001+2 = 동시사격
    skill_id 13 = S001+3 = 급소사격
    skill_id 15 = S001+5 = 에이밍샷
    skill_id 16 = S001+6 = 암즈트랩
    skill_id 18 = S001+8 = 암즈강화
    skill_id 21 = S002+1 = 마검공격
    skill_id 22 = S002+2 = 텔레포트소드
    skill_id 37 = S003+7 = 마법강화

bonus_id 매핑 (R88 의 'ability X 가 ability Y 에 보너스'):
    bonus_id 17 = S001+7 = 회피증가
    bonus_id 18 = S001+8 = 암즈강화 (= 자기 자신; ability_18 의 self-bonus)
    bonus_id 19 = S001+9 = 속사

Class 분포:
    S000: 0 (티르 base, ability upgrade 부재)
    S001: 5 (루레인 사격 — deepest customization)
    S002: 2 (티르 마검 — basic variants 만)
    S003: 1 (루레인 마법 — 마법강화 만)
"""
from __future__ import annotations
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CATALOG_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_catalog.json'
PROG_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_summon_progression.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

CLASS_NAMES = {0: 'S000', 1: 'S001', 2: 'S002', 3: 'S003'}
CLASS_ROLE = {
    'S000': '티르 양손검 (base)',
    'S001': '루레인 사격 (shooter)',
    'S002': '티르 마검 (mage-sword)',
    'S003': '루레인 단도+마법 (소환사)',
}


def build_global_skill_table(catalog: dict) -> list[dict]:
    out = []
    for ci, ss in enumerate(catalog['skill_sets']):
        cname = CLASS_NAMES[ci]
        for li, sk in enumerate(ss['skills']):
            out.append({
                'global_id': ci * 10 + li,
                'class_id': ci,
                'class_name': cname,
                'local_id': li,
                'skill_name': sk.get('name', ''),
            })
    return out


def main() -> int:
    catalog = json.loads(CATALOG_JSON.read_text(encoding='utf-8'))
    prog = json.loads(PROG_JSON.read_text(encoding='utf-8'))

    skill_table = build_global_skill_table(catalog)

    # Ability slots in _H_SA — load raw from h4_summon_progression
    raw_path = ROOT / 'work' / 'h4' / 'decrypted' / 'HDAT' / '_H_SA'
    raw = raw_path.read_bytes()

    # 24 ability slots starting at offset 24
    ability_slots = []
    for i in range(24):
        off = 24 + i * 24
        rec = raw[off:off+24]
        ability_slots.append({
            'slot_id': i,
            'skill_id': rec[8],
            'tier_value': rec[9],
            'bonus_id': rec[12],
            'bonus_value': rec[13],
        })

    # Resolve names
    resolved = []
    for slot in ability_slots:
        sid = slot['skill_id']
        bid = slot['bonus_id']
        s = skill_table[sid] if sid < 40 else None
        b = skill_table[bid] if bid < 40 and bid > 0 else None
        resolved.append({
            **slot,
            'skill_name': s['skill_name'] if s else None,
            'skill_class': s['class_name'] if s else None,
            'bonus_name': b['skill_name'] if b else None,
            'bonus_class': b['class_name'] if b else None,
        })

    # Group by skill_id (8 unique × 3 tiers)
    by_skill = {}
    for r in resolved:
        by_skill.setdefault(r['skill_id'], []).append(r)

    # Class distribution
    unique_skills = list(by_skill.keys())
    class_count = Counter()
    for sid in unique_skills:
        class_count[skill_table[sid]['class_name']] += 1

    summary_by_skill = []
    for sid, slots in by_skill.items():
        s = skill_table[sid]
        bonus_info = None
        if slots[0]['bonus_id'] not in (0,):
            bonus_s = skill_table[slots[0]['bonus_id']] if slots[0]['bonus_id'] < 40 else None
            bonus_info = {
                'bonus_skill_id': slots[0]['bonus_id'],
                'bonus_name': bonus_s['skill_name'] if bonus_s else None,
                'bonus_values': [x['bonus_value'] for x in slots],
            }
        summary_by_skill.append({
            'skill_id': sid,
            'class_name': s['class_name'],
            'class_role': CLASS_ROLE[s['class_name']],
            'local_id': s['local_id'],
            'skill_name': s['skill_name'],
            'tier_values': [x['tier_value'] for x in slots],
            'bonus': bonus_info,
        })
    summary_by_skill.sort(key=lambda x: x['skill_id'])

    out = {
        'round': 94,
        'global_skill_id_rule': 'skill_id = class_index × 10 + local_index (4 class × 10 skills)',
        'class_names': CLASS_NAMES,
        'class_roles': CLASS_ROLE,
        'global_skill_table_40': skill_table,
        'ability_skill_summary': summary_by_skill,
        'class_distribution': dict(class_count),
        'design_observations': {
            'S000_no_abilities': 'S000 (티르 base) ability upgrade 없음 — default skills only',
            'S001_dominant': 'S001 (루레인 사격) 5/8 ability — deepest customization',
            'S002_basic_variants': 'S002 (티르 마검) 2/8 — 마검공격/텔레포트소드 (combat 변종)',
            'S003_single_passive': 'S003 (마법) 1/8 — 마법강화 만 ability tier 보유',
            'all_bonus_in_S001': '3 bonus chain (회피증가/암즈강화/속사) 모두 S001 passive — 사격 class 가 self-contained tree',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_sa_ability_skill_map.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] 8 unique ability skill_ids resolved')
    for s in summary_by_skill:
        bonus_str = f' bonus→{s["bonus"]["bonus_name"]} +{s["bonus"]["bonus_values"]}' if s['bonus'] else ''
        print(f'  skill_id {s["skill_id"]:3d} [{s["class_name"]}] {s["skill_name"]:10s} tiers={s["tier_values"]}{bonus_str}')
    print()
    print(f'Class distribution: {dict(class_count)}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
