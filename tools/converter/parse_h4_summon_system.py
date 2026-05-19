"""Hero4 Round 87 — `_H_SS` 환수(소환수) 시스템 정밀 파서.

R86 에서 발견된 _H_SS (1624B) 구조를 entry 별로 분해.

레이아웃 (R87 발견):

    [0x0000-0x0001] FILE HEADER 2B: 0x25 (count/marker) + 0x00
    [0x0002-0x0024] Entry 0 (boss-like): 망각의 저주
        [nlen=0x0b:1B] [name:11B "망각의 저주"] [data:23B]
    [0x0025-0x00c4] SUMMARY 5 환수 × 32B each (fixed size):
        [01][cost=2d][size_marker:1B][00][nlen:1B][name:nlen B][padding][stats][id:1B at +18][padding]
        환수 ID at offset +18: 0=베놈, 1=헤지호그, 2=그래비티, 3=쇼커, 4=세이프가드
    [0x00c5-0x00d6] 18B zero padding
    [0x00d7-0x00f7] 환수A공격 divider:
        [nlen=0x09] [name:9B "환수A공격"] [data:23B]
    [0x00f8-0x056b] 5 환수 × 7 skill entries each:
        Pattern per entry: [nlen:1B] [name:nlen B] [data_block]
        - Long descriptor (~20-28B name): 2B data = [cost:1B][00]
        - Short active/aura (~4-11B name): 23B stat block
        Between 환수 groups: 환수[B-E]공격 dividers (nlen=9, 23B data)
    [0x056c-...0x065f] 4 global summoner passives:
        Pattern: short(nlen~8-10, 23B stats) + long(nlen~18-20, 2B desc)
        마법력/교감도/체력/정신 강화

5 환수: 베놈/헤지호그/그래비티/쇼커/세이프가드 (R86 확인)
4 글로벌 passive: 소환사 본인 강화 (마법력/방어력/체력/교감도)
"""
from __future__ import annotations
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SS_FILE = ROOT / 'work' / 'h4' / 'decrypted' / 'HDAT' / '_H_SS'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

SUMMON_NAMES = ['베놈', '헤지호그', '그래비티', '쇼커', '세이프가드']
DIVIDER_NAMES = ['환수B공격', '환수C공격', '환수D공격', '환수E공격']
GLOBAL_NAMES_SHORT = ['마법력강화', '교감도강화', '체력강화', '정신강화']


def is_korean_pair(b1: int, b2: int) -> bool:
    return 0xa1 <= b1 <= 0xfe and 0xa1 <= b2 <= 0xfe


def find_skill_entries(data: bytes, start: int, end: int) -> list[dict]:
    """[nlen:1B][name:nlen B][data:variable until next nlen] 스캔."""
    entries = []
    i = start
    while i < end - 4:
        nlen = data[i]
        if 1 <= nlen <= 60 and i + 1 + nlen <= end:
            nm = data[i+1:i+1+nlen]
            if len(nm) < 2:
                i += 1
                continue
            # First 2B must be EUC-KR Korean or contain literal char (e.g., '환수A공격' has 'A')
            first_pair_korean = is_korean_pair(nm[0], nm[1])
            if first_pair_korean and 0 not in nm[:max(nlen-1, 1)]:
                try:
                    txt = nm.decode('euc-kr', errors='strict')
                except UnicodeDecodeError:
                    i += 1
                    continue
                entries.append({'offset': i, 'nlen': nlen, 'name': txt})
                i = i + 1 + nlen
                continue
        i += 1
    # Now fill data blocks
    for j in range(len(entries)):
        nxt = entries[j+1]['offset'] if j+1 < len(entries) else end
        ds = entries[j]['offset'] + 1 + entries[j]['nlen']
        block = data[ds:nxt]
        entries[j]['data_offset'] = ds
        entries[j]['data_size'] = len(block)
        entries[j]['data_hex'] = block.hex()
    return entries


def parse_boss_entry(data: bytes) -> dict:
    """Entry 0: boss-like '망각의 저주' (offset 2, nlen=11, 23B data)."""
    nlen = data[2]
    name = data[3:3+nlen].decode('euc-kr', errors='replace')
    data_block = data[3+nlen:0x025]
    return {
        'offset': 2,
        'file_header_2b': data[0:2].hex(),
        'nlen': nlen,
        'name': name,
        'data_offset': 3 + nlen,
        'data_size': len(data_block),
        'data_hex': data_block.hex(),
    }


def find_summary_entries(data: bytes, start: int, end: int) -> list[dict]:
    """[01][2d][size_marker:1B][00][nlen:1B][name] 패턴을 스캔하여 5 환수 summary 추출.

    Variable stride (32B 또는 36B) — 4B 추가 padding 발생.
    """
    entries = []
    i = start
    while i < end - 6:
        if data[i] == 0x01 and data[i+1] == 0x2d and data[i+3] == 0x00:
            size_marker = data[i+2]
            nlen = data[i+4]
            if 1 <= nlen <= 14 and i + 5 + nlen <= end:
                nm = data[i+5:i+5+nlen]
                if is_korean_pair(nm[0], nm[1]):
                    try:
                        name = nm.decode('euc-kr', errors='strict')
                    except UnicodeDecodeError:
                        i += 1
                        continue
                    entries.append({
                        'offset': i,
                        'flag': data[i],
                        'cost': data[i+1],
                        'size_marker': size_marker,
                        'sep': data[i+3],
                        'nlen': nlen,
                        'name': name,
                    })
                    i += 5 + nlen
                    continue
        i += 1
    # Fill tail/stride
    for j in range(len(entries)):
        nxt = entries[j+1]['offset'] if j+1 < len(entries) else end
        tail_start = entries[j]['offset'] + 5 + entries[j]['nlen']
        tail = data[tail_start:nxt]
        entries[j]['tail_offset'] = tail_start
        entries[j]['tail_len'] = len(tail)
        entries[j]['tail_hex'] = tail.hex()
        # summon_id 는 tail 내 signature `09 03 29` 다음 byte
        sig_pos = tail.find(b'\x09\x03\x29')
        if sig_pos >= 0 and sig_pos + 3 < len(tail):
            entries[j]['summon_id'] = tail[sig_pos + 3]
            entries[j]['summon_id_offset'] = tail_start + sig_pos + 3
        else:
            entries[j]['summon_id'] = None
            entries[j]['summon_id_offset'] = None
        entries[j]['entry_total'] = len(tail) + 5 + entries[j]['nlen']
    return entries


def main():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    data = SS_FILE.read_bytes()
    print(f'_H_SS size = {len(data)}B')

    # Section 0: boss entry
    boss = parse_boss_entry(data)
    print(f'\n=== Section 0: Boss-like entry (0x000-0x024) ===')
    print(f'  file_header: {boss["file_header_2b"]}')
    print(f'  nlen={boss["nlen"]} name={boss["name"]!r}')
    print(f'  data({boss["data_size"]}B): {boss["data_hex"]}')

    # Section 1: 5 환수 summary (variable stride 32-36B)
    summary_entries = find_summary_entries(data, 0x025, 0x0d7)
    print(f'\n=== Section 1: {len(summary_entries)} 환수 Summary entries (0x025-0x0c4) ===')
    for e in summary_entries:
        print(f'  @0x{e["offset"]:04x} flag={e["flag"]} cost={e["cost"]} '
              f'size_marker={e["size_marker"]} nlen={e["nlen"]} '
              f'summon_id={e["summon_id"]} total={e["entry_total"]}B name={e["name"]!r}')
        print(f'    tail({e["tail_len"]}B): {e["tail_hex"]}')

    # Section 2: 환수A공격 divider at 0x0d7
    a_nlen = data[0x0d7]
    a_name = data[0x0d8:0x0d8+a_nlen].decode('euc-kr', errors='replace')
    a_data = data[0x0d8+a_nlen:0x0f8]
    a_divider = {
        'offset': 0x0d7,
        'nlen': a_nlen,
        'name': a_name,
        'data_offset': 0x0d8 + a_nlen,
        'data_size': len(a_data),
        'data_hex': a_data.hex(),
        'pre_padding_hex': data[0x0c5:0x0d7].hex(),
    }
    print(f'\n=== Section 2: 환수A공격 Divider (0x0c5-0x0f7) ===')
    print(f'  pre_padding({len(data[0x0c5:0x0d7])}B): {a_divider["pre_padding_hex"]}')
    print(f'  @0x{a_divider["offset"]:04x} nlen={a_nlen} name={a_name!r}')
    print(f'  data({a_divider["data_size"]}B): {a_divider["data_hex"]}')

    # Section 3: skill entries from 0x0f8 to end
    skill_entries = find_skill_entries(data, 0x0f8, len(data))
    print(f'\n=== Section 3: Skill Entries from 0x0f8 ({len(skill_entries)} entries) ===')

    # Group into 환수 sections
    summon_groups = {sn: [] for sn in SUMMON_NAMES}
    current_summon_idx = 0  # 베놈 (after 환수A공격)
    globals_list = []
    in_globals = False

    for e in skill_entries:
        nm = e['name']
        if nm in DIVIDER_NAMES:
            current_summon_idx += 1
            continue
        if nm in GLOBAL_NAMES_SHORT:
            in_globals = True
        if in_globals:
            globals_list.append(e)
        else:
            summon_groups[SUMMON_NAMES[current_summon_idx]].append(e)

    for sn, ents in summon_groups.items():
        print(f'\n  -- {sn} ({len(ents)} entries) --')
        for e in ents:
            kind = 'desc' if e['data_size'] <= 5 else 'stat'
            print(f'    @0x{e["offset"]:04x} nlen={e["nlen"]:2d} data={e["data_size"]:2d}B [{kind}] {e["name"]!r}')

    print(f'\n  -- 4 Global Passives ({len(globals_list)} entries) --')
    for e in globals_list:
        kind = 'desc' if e['data_size'] <= 5 else 'stat'
        print(f'    @0x{e["offset"]:04x} nlen={e["nlen"]:2d} data={e["data_size"]:2d}B [{kind}] {e["name"]!r}')

    # Build structured JSON — 5 skills per 환수 (R86 모델)
    summons = []
    for idx, sn in enumerate(SUMMON_NAMES):
        ents = summon_groups.get(sn, [])
        skills = []
        i = 0
        # Pattern (per R87): D-A-D-A-D-S-D
        # D = descriptor (long name, 2B data)
        # A = active (short name 4-8B, 23B stat block)
        # S = aura (medium name 11B, 23B stat block, standalone)
        while i < len(ents):
            e = ents[i]
            is_desc = e['data_size'] <= 5
            is_stat = e['data_size'] >= 20
            # Skill 1, 2: long descriptor + short active
            if is_desc and i+1 < len(ents) and ents[i+1]['data_size'] >= 20 and ents[i+1]['nlen'] <= 8:
                skill_kind = 'basic_attack' if '기본공격력' in e['name'] else (
                    'ranged_status' if '원거리' in e['name'] else 'paired_skill')
                skills.append({
                    'kind': skill_kind,
                    'descriptor': e,
                    'active': ents[i+1],
                })
                i += 2
                continue
            # Skill 3, 5: descriptor only (no active form)
            if is_desc and (i+1 >= len(ents) or ents[i+1]['nlen'] >= 10):
                # name may use ';' as separator (e.g., "뇌격의;중독 효과;강화")
                nm_flat = e['name'].replace(';', ' ')
                skill_kind = 'effect_boost' if '효과' in nm_flat and '강화' in nm_flat else (
                    'on_summon_buff' if '소환시' in nm_flat or '회복시' in nm_flat else 'passive_desc')
                skills.append({
                    'kind': skill_kind,
                    'descriptor': e,
                    'active': None,
                })
                i += 1
                continue
            # Skill 4: aura (medium name 11B, 23B stats, standalone)
            if is_stat and 'aura' not in [s.get('kind') for s in skills]:
                if e['nlen'] >= 10 and '오러' in e['name']:
                    skills.append({
                        'kind': 'aura',
                        'descriptor': None,
                        'active': e,
                    })
                    i += 1
                    continue
            # Fallback: unknown
            skills.append({
                'kind': 'unknown',
                'descriptor': e if is_desc else None,
                'active': e if is_stat else None,
            })
            i += 1
        summons.append({
            'id': idx,
            'name': sn,
            'summary': next((s for s in summary_entries if s['name'] == sn), None),
            'skill_count': len(skills),
            'skills_raw': ents,
            'skills': skills,
        })

    global_passives = []
    i = 0
    while i < len(globals_list):
        e = globals_list[i]
        if e['data_size'] >= 20 and i+1 < len(globals_list) and globals_list[i+1]['data_size'] <= 5:
            global_passives.append({
                'short_name': e['name'],
                'long_name': globals_list[i+1]['name'],
                'short_entry': e,
                'long_entry': globals_list[i+1],
            })
            i += 2
        else:
            global_passives.append({
                'short_name': e['name'],
                'long_name': None,
                'short_entry': e,
                'long_entry': None,
            })
            i += 1

    out = {
        'file': '_H_SS',
        'size': len(data),
        'boss_entry': boss,
        'summary_entries': summary_entries,
        'section_a_divider': a_divider,
        'summons': summons,
        'global_passives': global_passives,
        'meta': {
            'summon_count': len(SUMMON_NAMES),
            'raw_entries_per_summon': [len(summon_groups[sn]) for sn in SUMMON_NAMES],
            'logical_skills_per_summon': [sd['skill_count'] for sd in summons],
            'skill_kinds': sorted(set(s.get('kind', '?') for sd in summons for s in sd['skills'])),
            'global_passive_count': len(global_passives),
            'global_passive_skill_ids': [p['short_entry'].get('data_hex', '')[14:16] for p in global_passives],
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_summon_system.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nSaved: {out_path}')
    print(f'Meta: {json.dumps(out["meta"], ensure_ascii=False)}')


if __name__ == '__main__':
    main()
