"""Hero4 Round 103 — 24 alt-form mode 매핑 (R101 후속).

R101 발견된 24 alt-form (`= 이름` prefix) 의 활성화 mode/condition 분석.

분석 방법:
1. alt-form 의 이름 패턴 분석 (primary 와의 어근 공유)
2. lvl_req 분포 비교
3. stat 차이 (MP cost, damage, range)
4. 환수 시스템 cross-link 식별 (특히 S002/S003)

핵심 발견:
- alt-form 은 **primary skill 의 확장/변종** — 같은 어근 공유
  S000: 영검 series, 인첸트 series 등
  S001: 암즈샷 series, 상태변환 (은신/광폭/지축)
  S002: 환수 합신 ← 환수 시스템 cross-link
  S003: 환수특공/환수증폭/환수흡수 (환수 합체 skill set)
- alt-form lvl_req: 3 (10), 5 (3), 6 (8), 10 (3) — 11 부재 (= primary passive 11 과 다른 unlock layer)
- MP cost: alt-form 평균 18.1 (primary 11.7 보다 1.5×) — 고급 skill
- 환수 연동 skill 7개 (S002 "환수 합신" + S003 의 환수 4종)
"""
from __future__ import annotations
import json
import pathlib
import re
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CSF_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_class_skill_fields.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def find_alt_primary_link(name: str, primaries: list[dict]) -> dict | None:
    """alt-form 이름과 가장 유사한 primary skill (어근 공유) 찾기."""
    for p in primaries:
        pname = p['name']
        # 직접 substring match
        if len(name) >= 2 and (name[-2:] in pname or pname[-2:] in name):
            return p
        # 같은 한자/어근 (2글자 공유)
        for i in range(len(name) - 1):
            if name[i:i+2] in pname:
                return p
    return None


def categorize_alt(name: str) -> str:
    """alt-form 카테고리 추정."""
    if '환수' in name:
        return 'summon_combo'
    if any(k in name for k in ['은신', '광폭', '지축', '격노', '금강', '집중', '체질', '강타']):
        return 'state_transform'
    if any(k in name for k in ['영검', '대지', '심판', '단련']):
        return 'enhanced_primary'
    return 'variant'


def main() -> int:
    csf = json.loads(CSF_JSON.read_text(encoding='utf-8'))
    skills = csf['decoded_64_skills']

    primary = [s for s in skills if not s['is_alt']]
    alt = [s for s in skills if s['is_alt']]

    # Stats
    p_mp = [s['mp_cost'] for s in primary if s['mp_cost'] > 0]
    a_mp = [s['mp_cost'] for s in alt if s['mp_cost'] > 0]
    p_lvls = Counter(s['skill_lvl_req'] for s in primary)
    a_lvls = Counter(s['skill_lvl_req'] for s in alt)

    # Alt categorization + primary linking
    alt_analysis = []
    for a in alt:
        same_class_primaries = [p for p in primary if p['file'] == a['file']]
        linked = find_alt_primary_link(a['name'], same_class_primaries)
        cat = categorize_alt(a['name'])
        alt_analysis.append({
            'file': a['file'],
            'name': a['name'],
            'category': cat,
            'mp_cost': a['mp_cost'],
            'damage_le16': a['damage_le16'],
            'skill_lvl_req': a['skill_lvl_req'],
            'speed': a['speed'],
            'range_or_duration': a['range_or_duration'],
            'animation_id': a['animation_id'],
            'linked_primary_name': linked['name'] if linked else None,
        })

    # Summon-linked alt-forms
    summon_alts = [a for a in alt_analysis if a['category'] == 'summon_combo']

    out = {
        'round': 103,
        'r101_followup': '24 alt-form mode/condition 분석',
        'stats_comparison': {
            'primary_count': len(primary),
            'alt_count': len(alt),
            'primary_mp_mean': round(sum(p_mp) / len(p_mp), 1) if p_mp else 0,
            'alt_mp_mean': round(sum(a_mp) / len(a_mp), 1) if a_mp else 0,
            'primary_lvl_req_distribution': dict(p_lvls),
            'alt_lvl_req_distribution': dict(a_lvls),
        },
        'category_distribution': dict(Counter(a['category'] for a in alt_analysis)),
        'summon_linked_alts': summon_alts,
        'alt_skill_analysis': alt_analysis,
        'mode_hypothesis': {
            'r81_context': '2 영웅 × 2 mode = 4 character slot. mode 0 = primary, mode 1 = alt-form 가능성',
            'observation_1': 'alt-form lvl_req 에 11 부재 (primary passive 11 과 다른 unlock layer)',
            'observation_2': 'alt-form 평균 MP cost 가 primary 보다 약 1.5× 높음 → 고급 skill',
            'observation_3': 'S002 (티르 마검) 의 "환수 합신" + S003 (루레인 마법) 의 환수 4종 alt 가 환수 시스템 cross-link',
            'observation_4': 'alt-form 어근 공유: 영검 series, 인첸트 series, 암즈샷 series 등 → 같은 skill family 의 advanced variant',
            'conclusion': (
                'alt-form 은 mode-2 skill 으로 추정 (R81 mode 구조와 부합). '
                '특히 S002/S003 의 환수 관련 alt 는 환수+character mode 의 조합 skill. '
                '게임 진행 (mode switch / quest unlock / 특정 장비) 으로 활성화'
            ),
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_alt_form_mode.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'=== Primary vs Alt-form stats ===')
    print(f'  primary count: {len(primary)}, alt count: {len(alt)}')
    print(f'  primary MP mean: {out["stats_comparison"]["primary_mp_mean"]}')
    print(f'  alt MP mean: {out["stats_comparison"]["alt_mp_mean"]}')
    print(f'  primary lvl_req: {dict(p_lvls)}')
    print(f'  alt lvl_req: {dict(a_lvls)}')
    print()
    print(f'=== Alt-form categories ===')
    for cat, n in out['category_distribution'].items():
        print(f'  {cat}: {n}')
    print()
    print(f'=== Summon-linked alt-forms ({len(summon_alts)}) ===')
    for a in summon_alts:
        print(f'  {a["file"]} {a["name"]:10s} (lvl={a["skill_lvl_req"]}, MP={a["mp_cost"]}, dmg={a["damage_le16"]})')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
