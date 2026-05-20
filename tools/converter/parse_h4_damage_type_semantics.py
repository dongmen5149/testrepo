"""Hero4 Round 104 — damage_type byte[5] enum 별 특성 식별 (R102 후속).

R102 발견 damage_type enum (0/5/20/25) 의 in-game 의미를 description text 와 cross-ref.

확정 enum:
    type=0   (54 skills): MAGIC_OR_SKILL — skill 자체 damage 값 사용 (mp 소비 + 효과)
    type=5   ( 7 skills): WEAPON_BASIC  — weapon stat 기반 (skill damage = 0,
                                            character ATK 사용)
    type=20  ( 2 skills): DEBUFF        — 적 stat 감소 (방어도 감소, 둔화)
    type=25  ( 1 skill):  WEAPON_SPECIAL — 특수 무기 콤보 (철의주먹 = 암즈 2콤보)

Class 별 분포:
    S000 (양손검): 5×3 + 0×10 + 20×2 + 25×1 (가장 다양 — 4 type 모두 보유)
    S001 (사격):   5×4 + 0×12 (basic weapon 4 + magic 12)
    S002 (마검):   0×16 (모두 magic-based)
    S003 (마법):   0×16 (모두 magic-based)

→ S000/S001 만 WEAPON_BASIC (type=5) 보유 — 둘 다 무기 클래스 (양손검/사격).
  S002/S003 (마검/마법) 은 모두 skill-based damage = 0 만 사용.
  type=20/25 는 S000 전용 (양손검 의 debuff/special 특화).
"""
from __future__ import annotations
import json
import pathlib
import re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CSS_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_class_skill_schema.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

TYPE_LABEL = {
    0:  ('MAGIC_OR_SKILL',  'skill 자체 damage 값 사용 + MP 소비'),
    5:  ('WEAPON_BASIC',    'weapon stat 기반 (skill damage = 0, character ATK 사용)'),
    20: ('DEBUFF',          '적 stat 감소 (방어도 감소, 둔화)'),
    25: ('WEAPON_SPECIAL',  '특수 무기 콤보 (단발)'),
}


def clean(s: str) -> str:
    s = re.sub(r'[^가-힣 .,;0-9!?A-Za-z]', ' ', s)
    s = re.sub(r' +', ' ', s)
    return s.strip()


def main() -> int:
    css = json.loads(CSS_JSON.read_text(encoding='utf-8'))
    skills = []
    for fname, info in css['class_files'].items():
        for e in info['entries']:
            b = bytes.fromhex(e['stat_block_hex'])
            skills.append({
                'file': fname,
                'name': e['name_clean'],
                'is_alt': e['is_alt_form'],
                'mp_cost': b[0],
                'damage_le16': b[3] | (b[4] << 8),
                'damage_type': b[5],
                'desc_short': clean(e['desc_text'])[:80],
            })

    # Group by dtype
    by_type = {}
    for s in skills:
        by_type.setdefault(s['damage_type'], []).append(s)

    # Per-class breakdown
    class_dist = {}
    for fname in ['_H_S000', '_H_S001', '_H_S002', '_H_S003']:
        cnt = Counter(s['damage_type'] for s in skills if s['file'] == fname)
        class_dist[fname] = dict(cnt)

    # build result
    type_summary = {}
    for dtype, label_pair in TYPE_LABEL.items():
        recs = by_type.get(dtype, [])
        label, semantic = label_pair
        type_summary[dtype] = {
            'label': label,
            'semantic': semantic,
            'count': len(recs),
            'skills': [{'file': r['file'], 'name': r['name'], 'mp': r['mp_cost'], 'dmg': r['damage_le16'], 'desc': r['desc_short']} for r in recs],
        }

    out = {
        'round': 104,
        'r102_followup': 'damage_type byte[5] enum 별 특성 식별',
        'type_enum_definitions': {str(k): v[0] for k, v in TYPE_LABEL.items()},
        'type_summary': type_summary,
        'class_distribution': class_dist,
        'design_observations': {
            'weapon_class_split': 'S000/S001 (무기 class) 만 WEAPON_BASIC (type=5) 보유, S002/S003 (마검/마법) 은 모두 magic-based',
            's000_unique_types': 'S000 양손검 만이 DEBUFF (20) + WEAPON_SPECIAL (25) 보유 — 가장 다양한 dtype',
            'type_0_dominance': 'type=0 (skill-based damage) 가 54/64 = 84.4% — 대다수 skill 이 자체 damage 값 보유',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_damage_type_semantics.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    for dtype in [0, 5, 20, 25]:
        s = type_summary[dtype]
        print(f'\n=== type={dtype} {s["label"]}: {s["count"]} skills ===')
        print(f'  semantic: {s["semantic"]}')
        if dtype != 0:  # show all examples for non-default
            for sk in s['skills']:
                print(f'    {sk["file"][-5:]} {sk["name"]:12s} MP={sk["mp"]:2d} dmg={sk["dmg"]:3d}  | {sk["desc"][:50]}')
        else:
            for sk in s['skills'][:3]:
                print(f'    {sk["file"][-5:]} {sk["name"]:12s} MP={sk["mp"]:2d} dmg={sk["dmg"]:3d}  | {sk["desc"][:50]}')
            print(f'    ... ({s["count"]} total)')

    print(f'\n=== Class distribution ===')
    for fname, dist in class_dist.items():
        print(f'  {fname}: {dist}')

    print(f'\n[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
