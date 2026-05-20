"""Hero4 Round 101 — character class skill (S000-S003) stat block schema 정밀 (R95 후속).

R95 의 미해결: character skill 파일이 _H_SS ACTIVE_ATTACK template 미사용, 별개 schema.

발견된 entry layout:
    [size:1B][00][nlen:1B][name:EUC-KR='][stat_block:32B][desc_len:1B][desc:'{'+EUC-KR]

검증: body[32] (desc_len field) == len(body) - 32 → 4 파일 모두 16/16 entries 모두 부합.

R69 정정: R69 catalog 가 10 skill/class 로 보고했으나 R101 검증 결과
**4 파일 × 16 entries = 64 skill** (24 entry 추가 발견).
추가 entry 는 "= XX" prefix 패턴 (mode-2 alt skill 가설 — R81 의 2 영웅 × 2 mode 구조 부합).

32B stat block field 후보 (R101 분석):
    byte[0]      MP cost (varies 0-23)
    byte[1-2]    flags / marker (0xff common)
    byte[3-4]    LE16 damage
    byte[5]      damage type
    byte[6]      ?
    byte[8]      skill level requirement (0/3/4/5)
    byte[16-19]  speed/range/anim 후보
    byte[20-31]  zero padding (대부분)
"""
from __future__ import annotations
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
HDAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'HDAT'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

CLASS_FILES = ['_H_S000', '_H_S001', '_H_S002', '_H_S003']
CLASS_ROLE = {
    '_H_S000': '티르 양손검 (base)',
    '_H_S001': '루레인 사격 (shooter)',
    '_H_S002': '티르 마검 (mage-sword)',
    '_H_S003': '루레인 단도+마법 (소환사)',
}


def parse_class_file(path: pathlib.Path) -> list[dict]:
    data = path.read_bytes()
    entries = []
    i = 0
    while i < len(data) - 4:
        sz = data[i]
        if sz < 30 or sz > 250 or data[i+1] != 0:
            i += 1
            continue
        nlen = data[i+2]
        if nlen < 2 or nlen > 30:
            i += 1
            continue
        try:
            name = data[i+3:i+3+nlen].decode('euc-kr', errors='strict')
        except UnicodeDecodeError:
            i += 1
            continue
        if not re.search(r'[가-힣]', name):
            i += 1
            continue
        body_end = i + 1 + sz
        if body_end > len(data):
            i += 1
            continue
        body_start = i + 3 + nlen
        body = data[body_start:body_end]
        # validate desc_len at body[32]
        if len(body) < 33 or body[32] != len(body) - 32:
            i += 1
            continue
        stat_block = body[:32]
        desc_bytes = body[33:]  # skip '{'
        try:
            desc_text = desc_bytes.decode('euc-kr', errors='replace')
        except:
            desc_text = ''
        entries.append({
            'offset': i,
            'name_raw': name,
            'name_clean': name.replace('= ', '').strip(),
            'is_alt_form': name.startswith('= '),
            'size_field': sz,
            'body_size': len(body),
            'stat_block_hex': stat_block.hex(),
            'stat_byte_0_mp_cost': stat_block[0],
            'stat_damage_le16': stat_block[3] | (stat_block[4] << 8),
            'stat_byte_5_dmg_type': stat_block[5],
            'stat_byte_8_skill_level_req': stat_block[8],
            'stat_byte_16_17': (stat_block[16], stat_block[17]),
            'stat_byte_18_19': (stat_block[18], stat_block[19]),
            'desc_text': desc_text,
        })
        i = body_end
    return entries


def main() -> int:
    results = {}
    total = 0
    alt_count = 0
    for fname in CLASS_FILES:
        entries = parse_class_file(HDAT_DIR / fname)
        results[fname] = {
            'role': CLASS_ROLE[fname],
            'entry_count': len(entries),
            'alt_form_count': sum(1 for e in entries if e['is_alt_form']),
            'entries': entries,
        }
        total += len(entries)
        alt_count += results[fname]['alt_form_count']

    out = {
        'round': 101,
        'r95_followup': '32B stat block + variable description 형태 schema 확정',
        'r69_correction': f'R69 catalog 가 4 class × 10 = 40 skill 으로 보고했으나 실제 {total} skill 발견',
        'entry_layout': '[size:1B][00][nlen:1B][name:EUC-KR][stat_block:32B][desc_len:1B][desc:1B="{" + EUC-KR text]',
        'validation': 'body[32] == len(body) - 32 로 entry 경계 자가검증',
        'total_skills': total,
        'alt_form_count': alt_count,
        'class_files': results,
        'stat_block_field_candidates': {
            'byte_0': 'MP cost (0-23 varies)',
            'byte_1_2': 'flags / 0xff marker',
            'byte_3_4_LE16': 'damage',
            'byte_5': 'damage type',
            'byte_8': 'skill level requirement (0/3/4/5)',
            'byte_16_19': 'speed/range/anim cluster',
            'byte_20_31': 'mostly zero (reserved)',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_class_skill_schema.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'=== Class skill schema 분석 ===')
    for fname, info in results.items():
        print(f'  {fname} ({info["role"]}): {info["entry_count"]} entries ({info["alt_form_count"]} alt-form)')
    print(f'\nTotal: {total} skills (R69: 40 → R101: {total}, +{total - 40} 추가 발견)')
    print(f'Alt-form (=  prefix): {alt_count}')
    print()
    print('=== Sample entry decoding (first 3 of S000) ===')
    for e in results['_H_S000']['entries'][:3]:
        print(f'  {e["name_clean"]:12s} (alt={e["is_alt_form"]}) MP={e["stat_byte_0_mp_cost"]:3d} dmg={e["stat_damage_le16"]:4d} dtype={e["stat_byte_5_dmg_type"]} lvl={e["stat_byte_8_skill_level_req"]} desc={e["desc_text"][:30]!r}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
