"""Hero4 Round 69 — 모든 평문 데이터 → 통합 Hero4 catalog.

Round 68+69 누적 결과:
    - SCN 350 (35,752 dialogue)
    - HDAT-A 8 (heroes + skills + shop)
    - ITM/DAT 26 (items, character starting gear)
    - NPC scripts 9 (quests, UI, probability)
    - E/BSDAT, E/ESDAT 6 (boss/event scripts)
    - FR/ 3 (battle frames)

산출: work/h4/converted/h4_catalog.json — Android remake 가 직접 import.
"""
from __future__ import annotations
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXTRACTED = ROOT / 'work' / 'h4' / 'extracted'
DECRYPTED = ROOT / 'work' / 'h4' / 'decrypted'
CONVERTED = ROOT / 'work' / 'h4' / 'converted'


def find_korean_runs(data: bytes, min_len: int = 4) -> list[tuple[int, int, str]]:
    """모든 EUC-KR Korean run 의 (offset, length, text)."""
    runs = []
    i = 0
    while i < len(data) - 1:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
            start = i
            while i < len(data) - 1 and 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
                i += 2
            if i - start >= min_len:
                try:
                    s = data[start:i].decode('euc-kr', errors='replace')
                    runs.append((start, i - start, s))
                except Exception:
                    pass
        else:
            i += 1
    return runs


def extract_skill_names(data: bytes) -> list[dict]:
    """skill set 파일 — `name + 0x3d 0x20 (= )` 형태로 첫 단어 추출."""
    skills = []
    # Find all '= ' (0x3d 0x20) anchor points
    for m in re.finditer(b'\x3d\x20', data):
        end = m.start()
        # Walk backwards while EUC-KR pair
        i = end
        while i >= 2 and 0xa1 <= data[i-2] <= 0xfe and 0xa1 <= data[i-1] <= 0xfe:
            i -= 2
        if end - i >= 4:
            try:
                name = data[i:end].decode('euc-kr', errors='replace')
                skills.append({'offset': hex(i), 'name': name})
            except Exception:
                pass
    return skills


def parse_skill_set(file_path: pathlib.Path) -> dict:
    data = file_path.read_bytes()
    skills = extract_skill_names(data)
    # Dedup
    seen = set()
    unique = []
    for s in skills:
        if s['name'] not in seen:
            unique.append(s)
            seen.add(s['name'])
    return {
        'file': file_path.name,
        'size': len(data),
        'skill_count': len(unique),
        'skills': unique,
    }


def parse_item_dat(file_path: pathlib.Path) -> dict:
    """ITM/DAT/_ITM_*_DAT — 첫 byte = count, 이후 length-prefix 한국어 텍스트."""
    data = file_path.read_bytes()
    if not data:
        return {'file': file_path.name, 'size': 0, 'items': []}
    runs = find_korean_runs(data)
    return {
        'file': file_path.name,
        'size': len(data),
        'first_byte': data[0],
        'korean_count': len(runs),
        'unique_names': list(dict.fromkeys(r[2] for r in runs))[:40],
    }


def parse_npc_data(file_path: pathlib.Path) -> dict:
    data = file_path.read_bytes()
    runs = find_korean_runs(data)
    return {
        'file': file_path.name,
        'size': len(data),
        'korean_count': len(runs),
        'samples': [r[2] for r in runs[:25]],
    }


def main():
    catalog: dict = {
        'meta': {
            'game': 'Hero4 (영웅서기4 - 환영의검)',
            'round': 'R68 + R69 + R70 + R71 + R72 + R73 + R74 + R75 + R86 + R87',
            'date': '2026-05-19',
            'key': 'J@IWO8N7',
            'cipher': 'Hero5 mx_des_decrypt (S1[58]=2 + swap + reversed subkey)',
            'total_files_decrypted': 407,
        },
        'heroes': {
            'count': 2,
            'list': [
                {'name': '티르', 'class_suggested': '양손검 (Two-handed sword)',
                 'skill_set': '_H_S000 / _H_S002 (variants)',
                 'note': 'Round 68 dialogue corpus 의 가장 많이 등장하는 캐릭터 (x94)'},
                {'name': '루레인', 'class_suggested': '사격 더블건 (Dual Gun)',
                 'skill_set': '_H_S001',
                 'note': '_H_BH 에서 티르와 함께 등장'},
            ],
            'source': '_H_BH (168B = 4 entries × 40B stride)',
        },
        'skill_sets': [],
        'shop': {},
        'items': [],
        'npc': [],
        'quests': [],
    }

    # Skill sets
    for fn in ['_H_S000', '_H_S001', '_H_S002', '_H_S003']:
        r = parse_skill_set(DECRYPTED / 'HDAT' / fn)
        catalog['skill_sets'].append(r)
        print(f'{fn}: {r["skill_count"]} skills')
        for s in r['skills'][:12]:
            print(f"  - {s['name']}")
        print()

    # Shop Skills
    ss = parse_skill_set(DECRYPTED / 'HDAT' / '_H_SS')
    catalog['shop']['skill_shop'] = ss
    print(f'_H_SS (Shop Skills): {ss["skill_count"]} skills')

    # Items
    itm_dir = DECRYPTED / 'ITM' / 'DAT'
    if itm_dir.exists():
        for itm_file in sorted(itm_dir.glob('_ITM_*')):
            r = parse_item_dat(itm_file)
            catalog['items'].append(r)
    else:
        # Use original ITM/DAT (some may not be encrypted)
        for itm_file in sorted((EXTRACTED / 'ITM' / 'DAT').glob('_ITM_*')):
            # Try decrypted first
            dec = DECRYPTED / 'ITM' / 'DAT' / itm_file.name
            f = dec if dec.exists() else itm_file
            r = parse_item_dat(f)
            catalog['items'].append(r)
    print(f'\nItems: {len(catalog["items"])} ITM/DAT files')

    # NPC scripts
    npc_dir = DECRYPTED / 'NPC'
    if npc_dir.exists():
        for f in sorted(npc_dir.glob('*')):
            if f.is_file():
                r = parse_npc_data(f)
                catalog['npc'].append(r)
        print(f'NPC: {len(catalog["npc"])} files')

    # Items detailed (R73) — separately parsed in h4_items_detailed.json
    items_detailed_path = CONVERTED / 'h4_items_detailed.json'
    if items_detailed_path.exists():
        try:
            idata = json.loads(items_detailed_path.read_text(encoding='utf-8'))
            sd_summary = [{'file': r['file'], 'count': r['count']}
                          for r in idata.get('sd_files', [])]
            dat_summary = [{'file': r['file'], 'count': r['count']}
                           for r in idata.get('dat_files', [])]
            catalog['items_detailed'] = {
                'sd_files': sd_summary,
                'dat_files': dat_summary,
                'total_entries': idata.get('meta', {}).get('total_entries', 0),
                'note': 'LE16[0] = price (gold) confirmed for _DAT files',
            }
            print(f'\nItems detailed: {catalog["items_detailed"]["total_entries"]} entries (R73)')
        except Exception as e:
            print(f'  WARN: failed to load items_detailed: {e}', file=sys.stderr)

    # Event scripts (R72) — separately parsed in h4_event_scripts.json
    scripts_path = CONVERTED / 'h4_event_scripts.json'
    if scripts_path.exists():
        try:
            sdata = json.loads(scripts_path.read_text(encoding='utf-8'))
            # 압축: bsdat/esdat 각 파일별 entry name + count
            bsdat_summary = [
                {'file': r['file'], 'count': r['count'],
                 'unique_names': sorted({e['name'] for e in r.get('entries', []) if e.get('name')})}
                for r in sdata.get('bsdat', [])
            ]
            esdat_summary = [
                {'file': r['file'], 'count': r['count'],
                 'unique_names': sorted({e['name'] for e in r.get('entries', []) if e.get('name')})[:30]}
                for r in sdata.get('esdat', [])
            ]
            catalog['event_scripts'] = {
                'bsdat': bsdat_summary,
                'esdat': esdat_summary,
                'total_entries': sdata.get('meta', {}).get('total_entries', 0),
            }
            print(f'\nEvent scripts: {catalog["event_scripts"]["total_entries"]} entries (R72)')
        except Exception as e:
            print(f'  WARN: failed to load event_scripts: {e}', file=sys.stderr)

    # Hero stat blocks (R71) — separately parsed in h4_hero_stats.json
    hero_stats_path = CONVERTED / 'h4_hero_stats.json'
    if hero_stats_path.exists():
        try:
            hsdata = json.loads(hero_stats_path.read_text(encoding='utf-8'))
            catalog['hero_stats'] = {
                'entries': hsdata.get('entries', []),
                'observations': hsdata.get('observations', {}),
            }
            print(f'\nHero stats: {len(hsdata.get("entries", []))} entries (R71)')
        except Exception as e:
            print(f'  WARN: failed to load hero_stats: {e}', file=sys.stderr)

    # Summon system (R87) — separately parsed in h4_summon_system.json
    summon_path = CONVERTED / 'h4_summon_system.json'
    if summon_path.exists():
        try:
            sdata = json.loads(summon_path.read_text(encoding='utf-8'))
            catalog['summon_system'] = {
                'summon_count': sdata['meta']['summon_count'],
                'logical_skills_per_summon': sdata['meta']['logical_skills_per_summon'],
                'global_passive_count': sdata['meta']['global_passive_count'],
                'global_passive_skill_ids': sdata['meta']['global_passive_skill_ids'],
                'summons': [
                    {
                        'id': s['id'],
                        'name': s['name'],
                        'summon_id_byte': s['summary']['summon_id'] if s.get('summary') else None,
                        'skills': [
                            {
                                'kind': sk['kind'],
                                'descriptor_name': sk['descriptor']['name'] if sk.get('descriptor') else None,
                                'active_name': sk['active']['name'] if sk.get('active') else None,
                                'stat_block_hex': (sk['active']['data_hex'] if sk.get('active')
                                                    else sk['descriptor']['data_hex'] if sk.get('descriptor') else None),
                            } for sk in s['skills']
                        ],
                    } for s in sdata['summons']
                ],
                'global_passives': [
                    {
                        'short_name': p['short_name'],
                        'long_name': p['long_name'],
                        'skill_id': p['short_entry']['data_hex'][14:16] if p.get('short_entry') else None,
                    } for p in sdata['global_passives']
                ],
                'special_entries': {
                    'boss_like_name': sdata['boss_entry']['name'],
                    'section_a_divider_name': sdata['section_a_divider']['name'],
                },
            }
            print(f'\nSummon system: {len(sdata["summons"])} 환수 + {len(sdata["global_passives"])} global passives (R87)')
        except Exception as e:
            print(f'  WARN: failed to load summon_system: {e}', file=sys.stderr)

    # Summon progression (R88) — _H_BS stat + _H_SA ability / tier
    prog_path = CONVERTED / 'h4_summon_progression.json'
    if prog_path.exists():
        try:
            pdata = json.loads(prog_path.read_text(encoding='utf-8'))
            catalog['summon_progression'] = {
                'h_bs': {
                    'record_count': pdata['h_bs']['record_count'],
                    'record_stride': pdata['h_bs']['record_stride'],
                    'summons': [
                        {
                            'summon_id': s['summon_id'],
                            'name': s['name'],
                            'stats': s['stats'],
                            'learn_skill_ids': s['learn_skill_ids'],
                            'cost_marker': s['cost_marker'],
                        } for s in pdata['h_bs']['summons']
                    ],
                },
                'h_sa': {
                    'record_count': pdata['h_sa']['record_count'],
                    'ability_slot_count': len(pdata['h_sa']['ability_slots']),
                    'summon_tier_count': len(pdata['h_sa']['summon_tier_growth']),
                },
            }
            print(f'\nSummon progression: 5 환수 stat + 24 ability + 15 tier (R88)')
        except Exception as e:
            print(f'  WARN: failed to load summon_progression: {e}', file=sys.stderr)

    # Quest reward map (R90) — idx ↔ quest 1:1 매핑
    qrm_path = CONVERTED / 'h4_quest_reward_map.json'
    if qrm_path.exists():
        try:
            qrm = json.loads(qrm_path.read_text(encoding='utf-8'))
            catalog['quest_reward_map'] = {
                'meta': qrm['meta'],
                'extra_categorization': qrm['extra_categorization'],
                'verification': qrm['verification'],
            }
            print(f'\nQuest reward map: 128 quest 1:1 + 72 extras (R90)')
        except Exception as e:
            print(f'  WARN: failed to load quest_reward_map: {e}', file=sys.stderr)

    # Stat block schema (R89) — 23B block 통합 schema
    schema_path = CONVERTED / 'h4_statblock_schema.json'
    if schema_path.exists():
        try:
            sch = json.loads(schema_path.read_text(encoding='utf-8'))
            catalog['statblock_schema'] = {
                'template_catalog': sch['template_catalog'],
                'passive_subtype_catalog': sch['passive_subtype_catalog'],
                'block_count': sch['block_count'],
                'by_template': sch['by_template'],
            }
            print(f'\nStat block schema: 3 templates + 4 passive subtypes ({sch["block_count"]} blocks) (R89)')
        except Exception as e:
            print(f'  WARN: failed to load statblock_schema: {e}', file=sys.stderr)

    # Quests (R70) — separately parsed in h4_quests.json
    quests_path = CONVERTED / 'h4_quests.json'
    if quests_path.exists():
        try:
            qdata = json.loads(quests_path.read_text(encoding='utf-8'))
            for fn, qfile in qdata.get('files', {}).items():
                for q in qfile.get('quests', []):
                    catalog['quests'].append({
                        'source_file': fn,
                        'name': q.get('name', ''),
                        'description': q.get('description', ''),
                        'category': q.get('category', ''),
                    })
            print(f'\nQuests: {len(catalog["quests"])} entries (R70)')
        except Exception as e:
            print(f'  WARN: failed to load quests: {e}', file=sys.stderr)

    # Save
    out = CONVERTED / 'h4_catalog.json'
    out.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nSaved: {out}')

    # Summary stats
    total_skills = sum(s['skill_count'] for s in catalog['skill_sets'])
    total_items_kor = sum(i.get('korean_count', 0) for i in catalog['items'])
    total_npc_kor = sum(n.get('korean_count', 0) for n in catalog['npc'])
    print(f'\nTotal skill names: {total_skills}')
    print(f'Total item Korean entries: {total_items_kor}')
    print(f'Total NPC Korean entries: {total_npc_kor}')


if __name__ == '__main__':
    main()
