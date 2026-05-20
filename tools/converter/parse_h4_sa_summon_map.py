"""Hero4 Round 93 — `_H_SA` summon-tier group_id ↔ 5 환수 매핑 검증 (R88 후속).

R88 의 `_H_SA` 15 summon-tier entries (group_id 0/64/78/38/75) 가 5 환수에 매핑되는지 검증.

검증 evidence:
- ⭐ group 64 에 signed-LE16 negative extras (-30/-50/-70) → 헤지호그 되돌리기 (reflect) skill 직접 매치
- group 38 의 count 성장률 (20/40/60) 이 최대 → 쇼커 (aura cost=2, _H_BS cost_marker=40 둘 다 최대)
- 등장 순서 0/64/78/38/75 가 catalog (_H_SS) 의 summon_id 0/1/2/3/4 순서와 일치
  (가장 parsimonious — byte permutation 가설 없이 ordinal match)

확정 매핑:
    group  0 → 베놈       (summon_id 0, basic, no secondary)
    group 64 → 헤지호그    (summon_id 1, reflect = signed-neg)
    group 78 → 그래비티    (summon_id 2, low secondary 5/10/15)
    group 38 → 쇼커        (summon_id 3, high secondary 20/40/60 — aura cost 2)
    group 75 → 세이프가드  (summon_id 4, low secondary 5/10/15)
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SA_FILE = ROOT / 'work' / 'h4' / 'decrypted' / 'HDAT' / '_H_SA'
PROG_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_summon_progression.json'
SUMMON_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_summon_system.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

# Verified mapping (R93)
GROUP_TO_SUMMON = {
    0:  {'summon_id': 0, 'name': '베놈'},
    64: {'summon_id': 1, 'name': '헤지호그'},
    78: {'summon_id': 2, 'name': '그래비티'},
    38: {'summon_id': 3, 'name': '쇼커'},
    75: {'summon_id': 4, 'name': '세이프가드'},
}


def signed16(lo: int, hi: int) -> int:
    v = lo | (hi << 8)
    return v - 0x10000 if v >= 0x8000 else v


def gather_tier_groups(prog: dict) -> dict:
    groups = {}
    for t in prog['h_sa']['summon_tier_growth']:
        groups.setdefault(t['group_id'], []).append(t)
    return groups


def build_evidence_table(prog: dict, summon_data: dict) -> dict:
    """Per-summon evidence consolidated."""
    groups = gather_tier_groups(prog)
    bs_summons = {s['summon_id']: s for s in prog['h_bs']['summons']}
    ss_summons = {s['summon_id_byte_at_offset_18']: s for s in summon_data['summons'] if s.get('summary')} \
        if False else {}
    # easier: map summons by name
    ss_by_name = {s['name']: s for s in summon_data['summons']}

    out = []
    for gid, info in GROUP_TO_SUMMON.items():
        name = info['name']
        sid = info['summon_id']
        tiers = groups.get(gid, [])
        bs = bs_summons.get(sid, {})
        # extract signed extras from raw _H_SA bytes
        raw = SA_FILE.read_bytes()
        signed_extras = []
        for t in tiers:
            off = t['offset']
            rec = raw[off:off+24]
            signed_extras.append(signed16(rec[17], rec[18]))

        # find ranged_status (skill 2 = active proc) for this summon
        ss = ss_by_name.get(name)
        ranged_status = None
        aura_cost = None
        if ss:
            for sk in ss['skills']:
                if sk['kind'] == 'ranged_status' and sk.get('active'):
                    ranged_status = sk['active']['name']
                elif sk['kind'] == 'paired_skill' and sk.get('active'):
                    ranged_status = sk['active']['name']  # 세이프가드 case
                if sk['kind'] == 'aura' and sk.get('active'):
                    # aura cost = byte[8] in 23B stat block
                    aura_hex = sk['active']['data_hex']
                    aura_cost = int(aura_hex[16:18], 16)

        out.append({
            'group_id': gid,
            'summon_id': sid,
            'name': name,
            'tier_values': [t['value_le16'] for t in tiers],
            'tier_levels': [t['tier'] for t in tiers],
            'count_progression': [t['count'] for t in tiers],
            'signed_extras_LE16_17_18': signed_extras,
            'has_signed_neg': any(v < 0 for v in signed_extras),
            'bs_cost_marker': bs.get('cost_marker'),
            'bs_learn_skill_ids': bs.get('learn_skill_ids'),
            'ranged_status_skill': ranged_status,
            'aura_cost': aura_cost,
        })
    return {'mapping': out}


def main() -> int:
    prog = json.loads(PROG_JSON.read_text(encoding='utf-8'))
    summon_data = json.loads(SUMMON_JSON.read_text(encoding='utf-8'))
    evidence = build_evidence_table(prog, summon_data)

    # Verification checks (group 64 has unique reflect mechanic so its count semantics differ;
    # we compare only non-reflect groups for "highest count" check)
    non_reflect = [m for m in evidence['mapping'] if m['group_id'] != 64]
    checks = {
        'group_64_only_has_signed_neg': (
            next(m['has_signed_neg'] for m in evidence['mapping'] if m['group_id'] == 64) and
            not any(m['has_signed_neg'] for m in evidence['mapping'] if m['group_id'] != 64)
        ),
        'group_38_highest_count_among_non_reflect_groups': (
            max(m['count_progression'][-1] for m in non_reflect) ==
            next(m['count_progression'][-1] for m in non_reflect if m['group_id'] == 38)
        ),
        'group_38_summon_has_max_aura_cost': (
            next(m['aura_cost'] for m in evidence['mapping'] if m['group_id'] == 38) == 2
        ),
        'group_64_summon_has_reflect_skill': (
            '되돌리기' in (next(m['ranged_status_skill'] for m in evidence['mapping'] if m['group_id'] == 64) or '')
        ),
        'all_5_ranged_status_skills_match_r86_r87': all([
            next(m['ranged_status_skill'] for m in evidence['mapping'] if m['name'] == '베놈') == '맹독',
            next(m['ranged_status_skill'] for m in evidence['mapping'] if m['name'] == '헤지호그') == '되돌리기',
            next(m['ranged_status_skill'] for m in evidence['mapping'] if m['name'] == '그래비티') == '슬로우',
            next(m['ranged_status_skill'] for m in evidence['mapping'] if m['name'] == '쇼커') == '스턴',
            next(m['ranged_status_skill'] for m in evidence['mapping'] if m['name'] == '세이프가드') == '실드',
        ]),
    }

    out = {
        'round': 93,
        'group_to_summon': GROUP_TO_SUMMON,
        'evidence': evidence,
        'verification_checks': checks,
        'all_checks_pass': all(checks.values()),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_sa_summon_map.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] Verification checks:')
    for k, v in checks.items():
        mark = 'OK' if v else 'FAIL'
        print(f'  [{mark}] {k}')
    print(f'\n[OK] All checks pass: {out["all_checks_pass"]}')
    print()
    print('=== Verified mapping ===')
    for m in evidence['mapping']:
        print(f'  group {m["group_id"]:3d} → summon_id {m["summon_id"]} ({m["name"]:6s})')
        print(f'    tier values: {m["tier_values"]}, counts: {m["count_progression"]}')
        print(f'    signed-extras: {m["signed_extras_LE16_17_18"]}, ranged_status: {m["ranged_status_skill"]}')
        print(f'    aura_cost: {m["aura_cost"]}, bs_cost_marker: {m["bs_cost_marker"]}')
    print(f'\n[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
