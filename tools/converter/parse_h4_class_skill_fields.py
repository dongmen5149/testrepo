"""Hero4 Round 102 — 32B class skill stat block field 정밀 (R101 후속).

64 skill 전수 byte 분포 분석으로 32B stat block 의 각 field 의미 식별.

확정 field (high-evidence):
    byte[0]    MP cost (29 unique, 60/64 nonzero)
    byte[1]    flag (16 unique, 0xff dominant 23×)
    byte[2]    section marker (6 unique, 0xff dominant 55/64)
    byte[3-4]  damage LE16 (29 nonzero, 8/64 LE16>255)
    byte[5]    damage type enum (4 unique: 0/5/20/25)
    byte[7]    pre-cast flag (3 unique)
    byte[8]    skill level requirement (8 unique: 3/11/6/0/5)
    byte[9]    secondary flag (5 unique, 2=24 dominant)
    byte[13]   binary flag (0/1)
    byte[14]   const marker (0 또는 120=0x78)
    byte[15]   항상 0
    byte[16]   speed (37 unique, 51-63 dominant — 환수 stat block speed 53 와 유사)
    byte[17]   range/duration (23 unique, 4/150/44 common)
    byte[18]   flag (binary)
    byte[19]   animation_id (21 unique, 15/4 common — 환수 stat block anim 와 유사 layer)
    byte[20-21] secondary effect LE16 (proc/status power)
    byte[22]   const 0 (sub-boundary)
    byte[23]   bonus value
    byte[24-31] mostly zero (reserved/extension)

R101 32B field 후보 4개 (byte[0]/[3-4]/[5]/[8]) 검증 + byte[16-19] cluster 식별 완료.
"""
from __future__ import annotations
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CSS_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_class_skill_schema.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

FIELD_LABELS = {
    0:  ('MP cost', 'mp_cost'),
    1:  ('flag1 (0xff marker)', 'flag1'),
    2:  ('section marker (0xff)', 'sec_marker'),
    3:  ('damage_lo', 'damage_lo'),
    4:  ('damage_hi', 'damage_hi'),
    5:  ('damage type', 'damage_type'),
    6:  ('animation cluster A', 'anim_a'),
    7:  ('pre-cast flag', 'precast_flag'),
    8:  ('skill level requirement', 'skill_lvl_req'),
    9:  ('secondary flag', 'sec_flag'),
    10: ('aux byte', 'aux_a'),
    11: ('aux flag', 'aux_b'),
    12: ('special', 'special'),
    13: ('binary flag 13', 'flag13'),
    14: ('const marker (0 또는 0x78)', 'const14'),
    15: ('always 0', 'zero15'),
    16: ('speed', 'speed'),
    17: ('range/duration', 'range_or_duration'),
    18: ('flag18', 'flag18'),
    19: ('animation_id', 'animation_id'),
    20: ('secondary_effect_lo', 'sec_effect_lo'),
    21: ('secondary_effect_hi', 'sec_effect_hi'),
    22: ('sub_boundary (=0)', 'sub_boundary'),
    23: ('bonus value', 'bonus_value'),
}


def field_distribution(blocks: list[bytes]) -> dict:
    dist = {}
    for pos in range(32):
        vals = [b[pos] for b in blocks]
        cnt = Counter(vals)
        dist[pos] = {
            'unique_count': len(cnt),
            'nonzero_count': sum(1 for v in vals if v != 0),
            'top5': cnt.most_common(5),
            'label': FIELD_LABELS.get(pos, ('unknown', f'pos_{pos}'))[0],
        }
    return dist


def decode_skill(b: bytes) -> dict:
    return {
        'mp_cost': b[0],
        'damage_le16': b[3] | (b[4] << 8),
        'damage_type': b[5],
        'precast_flag': b[7],
        'skill_lvl_req': b[8],
        'sec_flag': b[9],
        'speed': b[16],
        'range_or_duration': b[17],
        'animation_id': b[19],
        'secondary_effect_le16': b[20] | (b[21] << 8),
        'bonus_value': b[23],
    }


def main() -> int:
    data = json.loads(CSS_JSON.read_text(encoding='utf-8'))
    blocks = []
    decoded = []
    for fname, info in data['class_files'].items():
        for e in info['entries']:
            b = bytes.fromhex(e['stat_block_hex'])
            blocks.append(b)
            d = decode_skill(b)
            d['file'] = fname
            d['name'] = e['name_clean']
            d['is_alt'] = e['is_alt_form']
            decoded.append(d)

    dist = field_distribution(blocks)

    # group by damage_type
    by_dtype = Counter(d['damage_type'] for d in decoded)
    # group by skill_lvl_req
    by_lvl = Counter(d['skill_lvl_req'] for d in decoded)
    # MP cost stats
    mp_costs = [d['mp_cost'] for d in decoded if d['mp_cost'] > 0]
    damage_values = [d['damage_le16'] for d in decoded if d['damage_le16'] > 0]

    out = {
        'round': 102,
        'r101_followup': '32B stat block field 정밀 식별',
        'field_distribution': {f'pos[{p}]': v for p, v in dist.items()},
        'damage_type_enum': dict(by_dtype),
        'skill_level_req_distribution': dict(by_lvl),
        'mp_cost_stats': {
            'nonzero_count': len(mp_costs),
            'min': min(mp_costs) if mp_costs else 0,
            'max': max(mp_costs) if mp_costs else 0,
            'mean': round(sum(mp_costs) / len(mp_costs), 1) if mp_costs else 0,
        },
        'damage_stats': {
            'nonzero_count': len(damage_values),
            'min': min(damage_values) if damage_values else 0,
            'max': max(damage_values) if damage_values else 0,
        },
        'decoded_64_skills': decoded,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_class_skill_fields.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'=== Damage type enum (byte[5]) ===')
    for k, v in by_dtype.items():
        print(f'  type={k}: {v} skills')
    print()
    print(f'=== Skill level requirement distribution ===')
    for k, v in sorted(by_lvl.items()):
        print(f'  lvl_req={k}: {v} skills')
    print()
    print(f'=== MP cost: min={min(mp_costs)} max={max(mp_costs)} mean={round(sum(mp_costs)/len(mp_costs), 1)} ({len(mp_costs)}/64 nonzero)')
    print(f'=== Damage: min={min(damage_values)} max={max(damage_values)} ({len(damage_values)}/64 nonzero)')
    print()
    print('=== Sample decoded skills (S001 사격 first 3) ===')
    for d in [x for x in decoded if x['file'] == '_H_S001'][:3]:
        print(f'  {d["name"]:10s} MP={d["mp_cost"]:3d} dmg={d["damage_le16"]:4d} dtype={d["damage_type"]} '
              f'lvl={d["skill_lvl_req"]} speed={d["speed"]} range={d["range_or_duration"]} anim={d["animation_id"]}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
