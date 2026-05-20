"""Hero4 Round 109 — type=0 magic skill sub-categorization (R104 후속).

R104 에서 type=0 (MAGIC_OR_SKILL) 이 64 skill 중 54 skill (84.4%) 로 dominate.
description text + dmg + alt_form + 환수 cross-ref 기반으로 세분 카테고리화.

Sub-categories (8):
  PASSIVE_DEEP      — name "|" prefix, dmg=0, 패시브 (16)
  ACTIVE_BUFF_SELF  — dmg=0 active, self enhancement (회복/극대/SP 충전)
  ACTIVE_DEBUFF     — 적 약화 (저주/암흑 magic)
  ACTIVE_AOE        — 범위 공격 (연속/대지/범위)
  ACTIVE_ELEMENT    — element 마법 (화염/빙결/얼음/암흑)
  ACTIVE_DASH       — 돌격/텔레포트
  ACTIVE_TRAP       — 설치 (트랩/장벽)
  ACTIVE_COMBO      — 환수 융합 combo
  ACTIVE_BASIC      — 기본 단발 공격 (default)

Class 별 layer 구조 검증:
  S000 양손검: passive 4 + buff 2 + AoE 1 + dash 1 + basic 2
  S001 사격:   passive 4 + buff 4 + basic 1 + dash 0 + multi 1 + trap 1 + status 1
  S002 마검:   passive 4 + buff 2 + element 4 + combo 2 + AoE 1 + dash 1 + basic 2
  S003 마법:   passive 4 + buff 1 + element 4 + AoE 2 + trap 1 + combo 2 + debuff 2
"""
from __future__ import annotations
import json
import pathlib
import re
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_damage_type_semantics.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def _match(keys: list[str], hay: str, prefix: str) -> list[str]:
    out = []
    for k in keys:
        if k in hay:
            out.append(f'{prefix}:{k}')
    return out


def classify(skill: dict) -> tuple[str, list[str]]:
    """Return (category, matched_keywords) for a type=0 skill.

    Priority order = most specific first. Each layer uses ITS OWN match list
    (no leak between layers).
    """
    name = skill['name']
    desc = skill['desc']
    haystack = name + ' ' + desc
    dmg = skill['dmg']

    # Layer 1: PASSIVE — name starts with '|' marker (확정)
    if name.startswith('|'):
        return ('PASSIVE_DEEP', ['name_pipe_prefix'])

    # Layer 2: ACTIVE_COMBO — 환수 + 융합/합신/특공/증폭/소울웨이브
    m = _match(['환수와', '환수 합신', '환수특공', '환수증폭', '소울웨이브', '융합'],
               haystack, 'combo')
    if m:
        return ('ACTIVE_COMBO', m)

    # Layer 3: ACTIVE_DEBUFF — 저주/적 약화/암흑의 구 (마법 debuff, S003 전용)
    m = _match(['저주', '암흑의 구', '역대미지', '공격력을'], haystack, 'debuff')
    if m:
        return ('ACTIVE_DEBUFF', m)

    # Layer 4: ACTIVE_TRAP — 설치/장벽/영역/폭탄 (semicolon-tolerant)
    desc_nosemi = desc.replace(';', ' ')
    m = _match(['설치', '장벽', '영역을 생성', '폭탄', '영역을  생성'], desc_nosemi, 'trap')
    if m:
        return ('ACTIVE_TRAP', m)

    # Layer 5: ACTIVE_DASH — 돌격/텔레포트/추적 (gap-closer)
    m = _match(['돌격', '텔레포트', '추적'], haystack, 'dash')
    if m:
        return ('ACTIVE_DASH', m)

    # Layer 6: ACTIVE_AOE — 범위/대지/연속/낙하 (dmg > 0 만)
    m = _match(['범위공격', '범위 공격', '대지를 흔들어', '연속하여', '넓은 범위', '낙하'],
               desc_nosemi, 'aoe')
    if m and dmg > 0:
        return ('ACTIVE_AOE', m)

    # Layer 7: ACTIVE_BUFF_SELF — self enhancement (dmg 무관: 찰라의영검 charge,
    # 기합 HP회복 + dmg=90, 헤이스트 cooldown + dmg=90 도 buff)
    m = _match(['SP 자동', 'SP를 모아', '극대', '몸을 숨긴', 'HP와 SP회복', 'SP의 소모량',
                '쿨타임과', '쿨타임', '육체강화', 'HP와 SP 회복', '회복', '강화 SP'],
               desc_nosemi, 'buff')
    if m:
        return ('ACTIVE_BUFF_SELF', m)

    # Layer 8: ACTIVE_ELEMENT — 화염/빙결/얼음 element (dmg > 0)
    m = _match(['화염', '빙결', '얼음'], haystack, 'element')
    if m and dmg > 0:
        return ('ACTIVE_ELEMENT', m)

    # Layer 9: ACTIVE_STATUS_HIT — 스턴/출혈/유도 (dmg > 0)
    m = _match(['스턴', '출혈', '유도'], desc_nosemi, 'status')
    if m and dmg > 0:
        return ('ACTIVE_STATUS_HIT', m)

    # Layer 10: ACTIVE_MULTI_HIT — 연속/추가타/2개 (dmg > 0)
    m = _match(['2개', '연속 사격', '추가타', '2콤보', '연타'], desc_nosemi, 'multi')
    if m and dmg > 0:
        return ('ACTIVE_MULTI_HIT', m)

    # Default: basic damage if dmg > 0, else basic combo (대검공격 dmg=0 fallback)
    if dmg > 0:
        return ('ACTIVE_BASIC', ['default_damage'])
    return ('ACTIVE_BASIC', ['default_basic_combo_dmg0'])


CATEGORY_ORDER = [
    'PASSIVE_DEEP',
    'ACTIVE_BUFF_SELF',
    'ACTIVE_BASIC',
    'ACTIVE_MULTI_HIT',
    'ACTIVE_STATUS_HIT',
    'ACTIVE_AOE',
    'ACTIVE_DASH',
    'ACTIVE_TRAP',
    'ACTIVE_ELEMENT',
    'ACTIVE_DEBUFF',
    'ACTIVE_COMBO',
]

CATEGORY_SEMANTIC = {
    'PASSIVE_DEEP':      '"|" prefix 패시브 — passive layer (lvl_req=11 deep tree)',
    'ACTIVE_BUFF_SELF':  'dmg=0 active — self enhancement (회복/극대/SP 충전/은신)',
    'ACTIVE_BASIC':      '기본 단발 공격 — dmg>0 default damage',
    'ACTIVE_MULTI_HIT':  '연속/2연속 타격 — multi-instance damage',
    'ACTIVE_STATUS_HIT': '공격 + status 유도 (스턴/출혈)',
    'ACTIVE_AOE':        '범위 공격 — area-of-effect',
    'ACTIVE_DASH':       '돌격/텔레포트 — gap-closer / displacement',
    'ACTIVE_TRAP':       '설치형 — trap / barrier / persistent area',
    'ACTIVE_ELEMENT':    'element 마법 — 화염/빙결/얼음 elemental',
    'ACTIVE_DEBUFF':     '적 약화 — 저주/공격력 감소/역대미지',
    'ACTIVE_COMBO':      '환수 융합 combo — summon-character synergy',
}


def main() -> int:
    dt = json.loads(DT_JSON.read_text(encoding='utf-8'))
    type0_skills = dt['type_summary']['0']['skills']
    assert len(type0_skills) == 54, f'expected 54 type=0 skills, got {len(type0_skills)}'

    classified = []
    by_cat: dict[str, list] = defaultdict(list)
    by_class_cat: dict[str, Counter] = defaultdict(Counter)

    for sk in type0_skills:
        cat, matched = classify(sk)
        rec = {**sk, 'category': cat, 'matched_keywords': matched}
        classified.append(rec)
        by_cat[cat].append(rec)
        by_class_cat[sk['file']][cat] += 1

    # Build summary
    category_summary = {}
    for cat in CATEGORY_ORDER:
        entries = by_cat.get(cat, [])
        category_summary[cat] = {
            'semantic': CATEGORY_SEMANTIC[cat],
            'count': len(entries),
            'skills': [
                {
                    'file': e['file'],
                    'name': e['name'],
                    'mp': e['mp'],
                    'dmg': e['dmg'],
                    'desc': e['desc'],
                    'matched': e['matched_keywords'],
                }
                for e in entries
            ],
        }

    class_layered = {
        cls: dict(cnt) for cls, cnt in by_class_cat.items()
    }

    # design observations
    obs = []
    pcount = category_summary['PASSIVE_DEEP']['count']
    if pcount == 16:
        obs.append(
            f'PASSIVE_DEEP = {pcount}/54 = 정확히 4 class × 4 passive — R101 schema (16 entry × 4 class) 의 passive layer 와 일치'
        )
    combo_classes = sorted(set(s['file'] for s in by_cat['ACTIVE_COMBO']))
    obs.append(
        f'ACTIVE_COMBO ({len(by_cat["ACTIVE_COMBO"])}) class = {combo_classes} — 환수 cross-link 은 마검+마법 (S002/S003) 만 보유'
    )
    debuff_classes = sorted(set(s['file'] for s in by_cat['ACTIVE_DEBUFF']))
    obs.append(
        f'ACTIVE_DEBUFF ({len(by_cat["ACTIVE_DEBUFF"])}) class = {debuff_classes} — magic-based debuff 은 S003 전용 (R104 의 type=20 S000-only debuff 과 분리)'
    )
    element_classes = sorted(set(s['file'] for s in by_cat['ACTIVE_ELEMENT']))
    obs.append(
        f'ACTIVE_ELEMENT ({len(by_cat["ACTIVE_ELEMENT"])}) class = {element_classes} — elemental 은 S002/S003 만'
    )

    out = {
        'round': 109,
        'r104_followup': 'type=0 (MAGIC_OR_SKILL) 54 skill 세분화',
        'category_count': len(CATEGORY_ORDER),
        'category_summary': category_summary,
        'class_layered_distribution': class_layered,
        'design_observations': obs,
        'mode_layer_model': {
            'passive_layer': 'lvl_req=11 deep tree, 4×4 = 16 (모든 class 균등)',
            'mode_0_active_layer': '기본 weapon/magic 공격 (BASIC/MULTI/STATUS) + element/AoE',
            'mode_1_advanced_layer': 'DASH / TRAP / DEBUFF / COMBO (mid-tier unlock, R103 alt-form 의 mode-2)',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_type0_subcategory.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    # Print summary
    print(f'=== R109 type=0 sub-categorization (54 skill) ===\n')
    for cat in CATEGORY_ORDER:
        info = category_summary[cat]
        print(f'\n[{cat}] {info["count"]} skill — {info["semantic"]}')
        for sk in info['skills']:
            print(f'  {sk["file"][-5:]} {sk["name"]:14s} MP={sk["mp"]:3d} dmg={sk["dmg"]:4d} | {sk["desc"][:55]}')

    print('\n=== Class layered distribution ===')
    for cls in ['_H_S000', '_H_S001', '_H_S002', '_H_S003']:
        dist = class_layered.get(cls, {})
        total = sum(dist.values())
        print(f'  {cls} (total {total}):')
        for cat in CATEGORY_ORDER:
            if cat in dist:
                print(f'    {cat:18s} {dist[cat]}')

    print('\n=== Design observations ===')
    for o in obs:
        print(f'  - {o}')

    print(f'\n[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
