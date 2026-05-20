"""Hero4 Round 114 — 환수 stat block × effect_id namespace 통합 (R87+R89+R113 후속).

R89 정정: 환수 STATUS_PROC byte[7] 와 AURA byte[7] 가 'strength' 가 아닌
**OPTION/class skill 과 동일 effect_id namespace** 임을 검증.

3-system unified effect engine:
  OPTION    : byte[0] = effect_id
  class skill: byte[20] = effect_id (R113)
  환수 STATUS_PROC (byte[5]=7) : byte[7] = effect_id
  환수 AURA          (byte[5]=11): byte[7] = effect_id, byte[11] = secondary effect_id
  환수 SHIELD        (byte[5]=6) : byte[7] = literal strength, byte[11] = secondary effect_id
  환수 PASSIVE       (byte[5]=12): byte[7] = skill_id (별도 namespace, 91-94)
  환수 ACTIVE_ATTACK (byte[0]=20): byte[5]=2 element const
"""
from __future__ import annotations
import json
import pathlib
from collections import defaultdict, Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SB_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_statblock_schema.json'
OPT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_itm_option_struct.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def load_effect_names_from_option() -> dict[int, str]:
    opt = json.loads(OPT_JSON.read_text(encoding='utf-8'))
    by_id: dict[int, list[str]] = defaultdict(list)
    for e in opt['entries']:
        eid = e['payload'][0]
        name = e['name'].rsplit(' L', 1)[0] if ' L' in e['name'] else e['name']
        by_id[eid].append(name)
    return {eid: Counter(n).most_common(1)[0][0] for eid, n in by_id.items()}


def main() -> int:
    sb = json.loads(SB_JSON.read_text(encoding='utf-8'))
    effect_names = load_effect_names_from_option()

    # Per template/subtype, extract effect_id field
    rows = []
    for b in sb['blocks']:
        owner = b.get('owner') or '(boss)'
        name = b['name']
        raw = b['raw']
        template = b.get('template', '?')
        subtype = b.get('subtype', '')
        # default
        primary_eid = None
        primary_field = None
        secondary_eid = None
        secondary_field = None

        if template == 'ACTIVE_ATTACK':
            # byte[5] = element const (2), not effect_id
            primary_eid = None
            primary_field = 'byte[5]=element(const 2)'
        elif subtype == 'STATUS_PROC':
            primary_eid = raw[7]
            primary_field = 'byte[7]'
        elif subtype == 'AURA':
            primary_eid = raw[7]
            primary_field = 'byte[7]'
            if raw[11] != 0:
                secondary_eid = raw[11]
                secondary_field = 'byte[11]'
        elif subtype == 'SHIELD':
            # byte[7] = literal shield strength (63), not effect_id
            primary_eid = None
            primary_field = 'byte[7]=literal'
            if raw[11] != 0:
                secondary_eid = raw[11]
                secondary_field = 'byte[11]'
        elif subtype == 'PASSIVE':
            # byte[7] = skill_id (91-94), separate namespace
            primary_eid = None
            primary_field = f'byte[7]=skill_id({raw[7]})'

        rows.append({
            'owner': owner,
            'name': name,
            'template': template,
            'subtype': subtype or '-',
            'primary_eid': primary_eid,
            'primary_field': primary_field,
            'primary_meaning': effect_names.get(primary_eid) if primary_eid else None,
            'secondary_eid': secondary_eid,
            'secondary_field': secondary_field,
            'secondary_meaning': effect_names.get(secondary_eid) if secondary_eid else None,
            'raw_5_14': raw[5:15],
        })

    # Cross-validation
    proc_match = sum(1 for r in rows
                     if r['subtype'] == 'STATUS_PROC'
                     and r['primary_meaning'] is not None)
    aura_match = sum(1 for r in rows
                     if r['subtype'] == 'AURA'
                     and r['primary_meaning'] is not None)
    proc_total = sum(1 for r in rows if r['subtype'] == 'STATUS_PROC')
    aura_total = sum(1 for r in rows if r['subtype'] == 'AURA')

    secondary_total = sum(1 for r in rows if r['secondary_eid'] is not None)
    secondary_match = sum(1 for r in rows if r['secondary_meaning'] is not None)

    # Newly discovered effect_id meanings (for 환수 entries)
    new_in_summon = set()
    for r in rows:
        if r['primary_eid'] is not None and r['primary_meaning'] is None:
            new_in_summon.add(r['primary_eid'])

    out = {
        'round': 114,
        'r87_r89_r113_followup': '환수 stat block × effect_id namespace 통합 (3-system unified)',
        'system_count': 3,
        'systems': {
            '1_option': 'item enchantment (R106), byte[0] = effect_id',
            '2_class_skill': 'character skill (R113), byte[20] = effect_id',
            '3_summon_status_proc_aura': 'summon STATUS_PROC + AURA (R114), byte[7] = effect_id',
        },
        'cross_validation': {
            'STATUS_PROC': {
                'total': proc_total,
                'effect_id_in_shared_namespace': proc_match,
                'rate': f'{proc_match}/{proc_total}',
            },
            'AURA': {
                'total': aura_total,
                'effect_id_in_shared_namespace': aura_match,
                'rate': f'{aura_match}/{aura_total}',
            },
            'AURA_secondary_byte11': {
                'nonzero': secondary_total,
                'effect_id_in_shared_namespace': secondary_match,
                'rate': f'{secondary_match}/{secondary_total}',
            },
        },
        'unique_summon_effect_ids': sorted(new_in_summon),
        'r89_correction': (
            'R89 의 STATUS_PROC byte[7]="strength" / AURA byte[7]="strength" 는 부정확. '
            '실제로는 effect_id (OPTION namespace 와 공유). R114 정정.'
        ),
        'blocks': rows,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_summon_effect_id_xref.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print('=== R114 환수 stat block × effect_id namespace 통합 ===\n')
    print('=== 환수 STATUS_PROC (byte[5]=7) 검증 ===')
    print(f'  {proc_match}/{proc_total} 가 effect_id namespace 매칭')
    for r in rows:
        if r['subtype'] == 'STATUS_PROC':
            eid = r['primary_eid']
            meaning = r['primary_meaning'] or '(환수 단독)'
            print(f"  {r['owner']:10s} {r['name']:14s} byte[7]={eid:3d} = {meaning}")

    print('\n=== 환수 AURA (byte[5]=11) 검증 ===')
    print(f'  {aura_match}/{aura_total} 가 effect_id namespace 매칭')
    for r in rows:
        if r['subtype'] == 'AURA':
            eid = r['primary_eid']
            meaning = r['primary_meaning'] or '(미매칭)'
            sec_eid = r['secondary_eid']
            sec_m = r['secondary_meaning'] or '(없음)'
            sec_str = f' / 2nd byte[11]={sec_eid}={sec_m}' if sec_eid else ''
            print(f"  {r['owner']:10s} {r['name']:14s} byte[7]={eid:3d} = {meaning}{sec_str}")

    print('\n=== 환수 SHIELD (byte[5]=6) 검증 ===')
    for r in rows:
        if r['subtype'] == 'SHIELD':
            sec_eid = r['secondary_eid']
            sec_m = r['secondary_meaning'] or '(없음)'
            print(f"  {r['owner']:10s} {r['name']:14s} byte[7]={r['raw_5_14'][2]}(literal) "
                  f"2nd byte[11]={sec_eid}={sec_m}")

    print('\n=== 환수 PASSIVE (byte[5]=12) — skill_id (별도 namespace) ===')
    for r in rows:
        if r['subtype'] == 'PASSIVE':
            print(f"  {r['name']:14s} byte[7]=skill_id({r['raw_5_14'][2]})")

    print('\n=== 환수 ACTIVE_ATTACK — byte[5]=2 element const ===')
    for r in rows:
        if r['template'] == 'ACTIVE_ATTACK':
            print(f"  {r['owner']:10s} {r['name']:14s} byte[5]={r['raw_5_14'][0]} (element)")

    print(f'\n=== 환수 단독 effect_id ({len(new_in_summon)}): {sorted(new_in_summon)} ===')
    print('  (66 = 망각의저주 boss-only)')

    print(f'\n[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
