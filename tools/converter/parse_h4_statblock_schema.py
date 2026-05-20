"""Hero4 Round 89 — 23B stat block 통합 schema 식별 + 카탈로그 출력.

R87 의 stat block field 표를 정정 + 확장. 21 개 23B block (boss 1 + active 5 + status 5
+ aura 5 + paired 1 + passive 4 + divider 1) 을 전수 비교해 **3 template** 식별.

Template = byte[0] 가 결정:
    byte[0] = 0x14 (20)   → ACTIVE_ATTACK (basic_attack / paired_attack)
    byte[0] = 0x0a (10)   → DIVIDER       (환수A공격 등 그룹 구분자, attack 와 동일 schema)
    byte[0] = 0x00        → STATUS/AURA/PASSIVE (byte[5] 가 subtype 결정)

ACTIVE_ATTACK schema (byte[0]=20 or 10):
    byte[3-4] = damage_le16            (200, 300, 400, 500)
    byte[5]   = element/damage_type    (const 2)
    byte[6]   = heal_flag              (0=damage, 2=heal)
    byte[7]   = speed/cooldown         (53 standard, 61 heal)
    byte[8]   = range                  (100-160)
    byte[10]  = animation_id           (3-20)

PASSIVE template schema (byte[0]=0, byte[5] determines subtype):

    byte[5]=6  SHIELD                  paired_skill 실드
        byte[7]=strength, byte[8]=cost, byte[10]=anim,
        byte[11-14] secondary HP/SP buff

    byte[5]=7  STATUS_PROC              맹독/되돌리기/슬로우/스턴/(boss)망각의저주
        byte[6] = reflect_flag (0 standard, 3 reflect)
        byte[7] = strength/duration
        byte[8] = cost (1 standard; boss=0)
        byte[10]= animation_id

    byte[5]=11 AURA                     저주/강화/마법/마력/보호의 오러
        byte[6] = const 2 (aura marker)
        byte[7] = aura strength
        byte[8] = cost
        byte[10]= animation
        byte[11]= secondary buff value (0/6/17/30 = HP/SP 추가 보너스)
        byte[12]= secondary subtype
        byte[14]= secondary anim

    byte[5]=12 PASSIVE                  4 글로벌 소환사 패시브
        byte[6] = const 3 (passive marker)
        byte[7] = skill_id (91-94)
        byte[8] = level (const 2)
        byte[10]= 0

Boss 특수 (byte[2]=5): 망각의저주 만 가지는 subtype marker — "incurable curse" 추정.

R87 정정사항:
- "damage" 가 byte[3] 단일 (44/200/144/44/244) → byte[3-4] LE16 (300/200/400/300/500)
- "type position 0" 만이 type 이라고 했으나, 실제로 byte[0] 는 template marker 이며
  byte[5] 가 PASSIVE template 의 subtype 결정자
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SS_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_summon_system.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

# byte[5] → subtype name (PASSIVE template only)
PASSIVE_SUBTYPE = {
    6: 'SHIELD',
    7: 'STATUS_PROC',
    11: 'AURA',
    12: 'PASSIVE',
}

# byte[0] → template
TEMPLATE = {
    0x14: 'ACTIVE_ATTACK',
    0x0a: 'DIVIDER',
    0x00: 'PASSIVE_TEMPLATE',
}


def collect_blocks(data: dict) -> list[dict]:
    blocks = []
    # boss
    be = data['boss_entry']
    blocks.append({
        'category': 'boss',
        'owner': None,
        'kind': 'boss_status',
        'name': be['name'],
        'data_hex': be['data_hex'],
    })
    # summon skills
    for s in data['summons']:
        for sk in s['skills']:
            if sk.get('active') and sk['active'].get('data_size') == 23:
                blocks.append({
                    'category': 'summon_active',
                    'owner': s['name'],
                    'kind': sk['kind'],
                    'name': sk['active']['name'],
                    'data_hex': sk['active']['data_hex'],
                })
    # global passives
    for p in data['global_passives']:
        if p.get('short_entry') and p['short_entry'].get('data_size') == 23:
            blocks.append({
                'category': 'global_passive',
                'owner': None,
                'kind': 'passive',
                'name': p['short_name'],
                'data_hex': p['short_entry']['data_hex'],
            })
    # divider
    if 'section_a_divider' in data and data['section_a_divider'].get('data_size') == 23:
        blocks.append({
            'category': 'divider',
            'owner': None,
            'kind': 'divider',
            'name': data['section_a_divider']['name'],
            'data_hex': data['section_a_divider']['data_hex'],
        })
    return blocks


def decode_block(hx: str) -> dict:
    b = bytes.fromhex(hx[:46])
    assert len(b) == 23
    template_id = b[0]
    template = TEMPLATE.get(template_id, f'UNKNOWN_{template_id:02x}')
    out = {
        'raw': list(b),
        'template_id': template_id,
        'template': template,
    }
    if template in ('ACTIVE_ATTACK', 'DIVIDER'):
        out.update({
            'damage': b[3] | (b[4] << 8),
            'element': b[5],
            'heal_flag': b[6],
            'speed': b[7],
            'range': b[8],
            'animation_id': b[10],
        })
    else:  # PASSIVE_TEMPLATE
        subtype_id = b[5]
        subtype = PASSIVE_SUBTYPE.get(subtype_id, f'UNKNOWN_{subtype_id:02x}')
        out.update({
            'subtype_id': subtype_id,
            'subtype': subtype,
            'flag6': b[6],
            'strength_or_skillid': b[7],
            'cost_or_level': b[8],
            'animation_id': b[10],
            'secondary': {
                'value': b[11],
                'subtype': b[12],
                'animation': b[14],
            },
        })
        if b[2] != 0:
            out['boss_marker'] = b[2]
    return out


def main() -> int:
    data = json.loads(SS_JSON.read_text(encoding='utf-8'))
    blocks = collect_blocks(data)

    decoded = []
    for blk in blocks:
        info = decode_block(blk['data_hex'])
        decoded.append({**blk, **info})

    # Summary by template
    summary = {}
    for d in decoded:
        key = d['template']
        if key == 'PASSIVE_TEMPLATE':
            key = f'PASSIVE_TEMPLATE/{d["subtype"]}'
        summary.setdefault(key, []).append({
            'owner': d['owner'],
            'kind': d['kind'],
            'name': d['name'],
        })

    out = {
        'round': 89,
        'template_catalog': TEMPLATE,
        'passive_subtype_catalog': PASSIVE_SUBTYPE,
        'block_count': len(decoded),
        'by_template': {k: len(v) for k, v in summary.items()},
        'blocks': decoded,
        'r87_corrections': {
            'damage_field_was': 'byte[3] single (44,200,144,44,244)',
            'damage_field_is':  'byte[3..4] LE16 (300,200,400,300,500)',
            'type_field_was':   'pos 0 unified type marker',
            'type_field_is':    'byte[0]=template, byte[5]=subtype (for PASSIVE template)',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_statblock_schema.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] {len(decoded)} 23B blocks decoded')
    for k, v in summary.items():
        print(f'  {k:35s} {len(v)} entries')
    print()
    print('=== ACTIVE_ATTACK (5 basic_attack + 1 divider) ===')
    for d in decoded:
        if d['template'] in ('ACTIVE_ATTACK', 'DIVIDER'):
            print(f'  {d["owner"] or "(divider)":12s} {d["name"][:10]:10s} damage={d["damage"]:4d} '
                  f'element={d["element"]} heal={d["heal_flag"]} speed={d["speed"]} range={d["range"]} anim={d["animation_id"]}')
    print()
    print('=== PASSIVE_TEMPLATE by subtype ===')
    for d in decoded:
        if d['template'] == 'PASSIVE_TEMPLATE':
            sec = d['secondary']
            print(f'  [{d["subtype"]:11s}] {d["owner"] or "(global)":12s} {d["name"][:10]:10s} '
                  f'flag6={d["flag6"]} val[7]={d["strength_or_skillid"]:3d} cost[8]={d["cost_or_level"]:3d} '
                  f'anim={d["animation_id"]} secondary={sec}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
