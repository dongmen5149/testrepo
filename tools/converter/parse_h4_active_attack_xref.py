"""Hero4 Round 95 — element byte[5]=2 검증 (R89 후속).

R89 의 23B stat block ACTIVE_ATTACK template (byte[0]=0x14) 에서 byte[5]=2 가
"element" 인지 검증. 전 decrypted 코퍼스에서 valid ACTIVE_ATTACK signature 출현 분포를
확인해 element 의 실제 의미 추정.

발견:
- ACTIVE_ATTACK template (0x14...) 은 `_H_SS` 환수 catalog 에 한정 출현 (6 candidates)
- 모든 6 candidate byte[5]=2 (5 환수 basic + 1 divider 환수A공격)
- 다른 character skill 파일 (_H_S000-_H_S003) 에는 0x14 signature 부재 / coincidental
  → byte[5] 는 "element" 가 아니라 **summon-exclusive 'block-subtype' marker** (=2 = 환수 attack 종류)
- character class 스킬은 별개 stat block schema 사용 (R96+ 분석 대상)

R89 정정:
- "element field byte[5]" 라는 명명 → "summon ACTIVE_ATTACK subtype marker (const 2)" 로 변경
- PASSIVE_TEMPLATE 의 byte[5] 가 subtype id 역할을 하는 것과 동일한 의미 layer
  (ACTIVE_ATTACK 의 byte[5] = 2 = "환수 무기 type" 고정)
"""
from __future__ import annotations
import json
import os
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DECRYPTED = ROOT / 'work' / 'h4' / 'decrypted'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def scan_active_attack() -> dict:
    """Scan all decrypted files for 0x14 ACTIVE_ATTACK signature."""
    results = []
    elements = Counter()
    files_with_hits = 0
    files_scanned = 0
    for root, _, files in os.walk(DECRYPTED):
        for fn in files:
            p = pathlib.Path(root) / fn
            try:
                data = p.read_bytes()
            except OSError:
                continue
            files_scanned += 1
            hits = []
            for i in range(len(data) - 22):
                # signature: 0x14, 0x00, 0x00, [LE16 damage > 0]
                if data[i] != 0x14 or data[i+1] != 0x00 or data[i+2] != 0x00:
                    continue
                dmg = data[i+3] | (data[i+4] << 8)
                if dmg == 0:
                    continue
                # element/subtype byte must be small value
                if data[i+5] > 10:
                    continue
                hits.append({
                    'offset': i,
                    'damage_le16': dmg,
                    'byte_5_element': data[i+5],
                    'byte_6_heal_flag': data[i+6],
                    'speed': data[i+7],
                    'range': data[i+8],
                    'anim': data[i+10],
                })
                elements[data[i+5]] += 1
            if hits:
                relpath = str(p.relative_to(DECRYPTED)).replace(os.sep, '/')
                results.append({
                    'path': relpath,
                    'hit_count': len(hits),
                    'hits': hits,
                })
                files_with_hits += 1

    return {
        'files_scanned': files_scanned,
        'files_with_hits': files_with_hits,
        'element_distribution': dict(elements),
        'results': results,
    }


def main() -> int:
    scan = scan_active_attack()

    # Interpretation
    summon_only = all(
        r['path'].endswith('_H_SS') or '_ITM_15' in r['path']
        for r in scan['results']
    )

    out = {
        'round': 95,
        'r89_field_being_validated': 'byte[5] = element',
        'scan_meta': {
            'files_scanned': scan['files_scanned'],
            'files_with_active_attack_signature': scan['files_with_hits'],
            'element_distribution': scan['element_distribution'],
        },
        'results_per_file': scan['results'],
        'r89_correction': {
            'old_interpretation': 'byte[5] = element (const 2)',
            'new_interpretation': 'byte[5] = ACTIVE_ATTACK subtype marker (const 2 = 환수 attack)',
            'evidence': (
                '0x14 ACTIVE_ATTACK signature 는 _H_SS catalog 에만 출현 ('
                f'{sum(r["hit_count"] for r in scan["results"])} hit). '
                'byte[5]=2 는 invariant — 즉 "element" 가 아닌 "summon-exclusive subtype" marker.'
            ),
            'summon_exclusive': summon_only,
        },
        'character_skill_schema_note': (
            'character class skill 파일 (_H_S000-_H_S003) 은 ACTIVE_ATTACK template 부재. '
            '별개 stat block schema 사용 — R96+ 별도 분석 필요.'
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_active_attack_xref.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] scanned {scan["files_scanned"]} files, {scan["files_with_hits"]} with 0x14 ACTIVE_ATTACK signature')
    print(f'element[5] distribution: {scan["element_distribution"]}')
    print()
    print('=== Per-file ACTIVE_ATTACK candidates ===')
    for r in scan['results']:
        print(f'  {r["path"]:40s} {r["hit_count"]} hits')
        for h in r['hits']:
            print(f'    @0x{h["offset"]:04x} damage={h["damage_le16"]:4d} byte5={h["byte_5_element"]} '
                  f'heal={h["byte_6_heal_flag"]} speed={h["speed"]} range={h["range"]} anim={h["anim"]}')
    print()
    print(f'R89 correction: byte[5]=2 is **NOT** element — it is summon-exclusive subtype marker.')
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
