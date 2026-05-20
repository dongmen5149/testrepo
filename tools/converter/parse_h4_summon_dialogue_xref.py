"""Hero4 Round 92 — Summon dialogue corpus cross-reference (R87 후속).

5 환수 (베놈/헤지호그/그래비티/쇼커/세이프가드) 와 generic summon 용어
(소환수/환수/소환사/소환술) 의 전체 decrypted 코퍼스 출현 빈도 분석.

핵심 발견:
- 5 환수 개별 이름은 catalog 4 파일 외 거의 부재:
    `_H_SS` (catalog source), `_ITM_15_DAT` (item catalog 사본),
    `NPCUI_GUARDIANSHOP_DAT` (수호자 상점 NPC), `n0124_scn` (베놈 tutorial scene)
- generic "환수"(147 hits) / "소환수"(130 hits) 는 35 파일에 산재
- "소환사" 는 9 hits / 3 파일 — class name 으로의 명시적 dialogue 거의 없음
- "소환술" 0 hits — 명시적 skill 이름으로 dialogue 부재
- boss "망각의 저주" 는 catalog 외 0 hits — story 노출 없음

해석:
- 환수 시스템은 **상점 NPC + tutorial scene** 통해 도입되며 메인 story 에 영향 최소
- n0124_scn = 환수 시스템 tutorial (베놈을 예시로 설명)
- NPCUI_GUARDIANSHOP_DAT = "수호자 상점" 환수 획득 UI
"""
from __future__ import annotations
import json
import os
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DECRYPTED = ROOT / 'work' / 'h4' / 'decrypted'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

SUMMON_NAMES = ['베놈', '헤지호그', '그래비티', '쇼커', '세이프가드']
GENERIC = ['소환수', '소환사', '환수', '소환술', '망각', '망각의 저주']
SKILL_NAMES = ['뇌격', '맹독', '되돌리기', '슬로우', '스턴', '실드']
AURA = ['저주의 오러', '강화의 오러', '마법의 오러', '마력의 오러', '보호의 오러']
PASSIVE = ['마법력강화', '교감도강화', '체력강화', '정신강화']


def scan_corpus() -> dict:
    keywords = SUMMON_NAMES + GENERIC + SKILL_NAMES + AURA + PASSIVE
    counts: dict[str, dict] = {k: {'hits': 0, 'files': []} for k in keywords}
    files_scanned = 0
    bytes_scanned = 0
    for root, _, files in os.walk(DECRYPTED):
        for fn in files:
            p = pathlib.Path(root) / fn
            try:
                data = p.read_bytes()
            except OSError:
                continue
            txt = data.decode('euc-kr', errors='replace')
            files_scanned += 1
            bytes_scanned += len(data)
            relp = str(p.relative_to(DECRYPTED)).replace('\\', '/')
            for k in keywords:
                c = txt.count(k)
                if c:
                    counts[k]['hits'] += c
                    counts[k]['files'].append({'path': relp, 'count': c})
    return {
        'files_scanned': files_scanned,
        'bytes_scanned': bytes_scanned,
        'keyword_counts': counts,
    }


def categorize_sources(counts: dict) -> dict:
    """5 환수 이름이 출현하는 파일을 source type 별로 분류."""
    file_role = {}
    for name in SUMMON_NAMES:
        for entry in counts[name]['files']:
            p = entry['path']
            role = file_role.setdefault(p, {'roles': set(), 'summons_found': set()})
            role['summons_found'].add(name)
            if p.endswith('_H_SS'):
                role['roles'].add('catalog_primary')
            elif p.startswith('ITM/') or '_ITM_' in p:
                role['roles'].add('item_catalog_sub')
            elif p.startswith('NPC/'):
                role['roles'].add('shop_npc')
            elif p.startswith('MAP/SC/') or p.endswith('_scn'):
                role['roles'].add('scene_dialogue')
            else:
                role['roles'].add('unknown')
    out = []
    for p, info in file_role.items():
        out.append({
            'path': p,
            'roles': sorted(info['roles']),
            'summons_found': sorted(info['summons_found']),
            'summon_count': len(info['summons_found']),
        })
    out.sort(key=lambda x: (-x['summon_count'], x['path']))
    return out


def find_tutorial_excerpts(counts: dict) -> list[dict]:
    """베놈 가 등장하는 scene 파일에서 tutorial 인용 추출."""
    out = []
    for entry in counts['베놈']['files']:
        p = entry['path']
        if not (p.endswith('_scn') or p.startswith('MAP/SC/')):
            continue
        full = (DECRYPTED / p).read_bytes()
        txt = full.decode('euc-kr', errors='replace')
        idx = txt.find('베놈')
        if idx >= 0:
            start = max(0, idx - 80)
            end = min(len(txt), idx + 120)
            excerpt = txt[start:end]
            # filter to readable Korean
            excerpt = re.sub(r'[^\x20-\x7e가-힣ㅏ-ㅣ.,!?·<>{}()\[\] ]', '·', excerpt)
            out.append({
                'path': p,
                'excerpt_around_first_mention': excerpt,
            })
    return out


def main() -> int:
    scan = scan_corpus()
    counts = scan['keyword_counts']

    # Simplify file entries for output
    summary = {}
    for k, info in counts.items():
        summary[k] = {
            'hits': info['hits'],
            'file_count': len(info['files']),
            'top_files': info['files'][:5],
        }

    source_files = categorize_sources(counts)
    tutorial_excerpts = find_tutorial_excerpts(counts)

    out = {
        'round': 92,
        'corpus_meta': {
            'files_scanned': scan['files_scanned'],
            'bytes_scanned': scan['bytes_scanned'],
        },
        'keyword_summary': summary,
        'summon_source_files': source_files,
        'tutorial_excerpts': tutorial_excerpts,
        'r87_followup_findings': {
            'individual_names_localized': '5 환수 이름은 catalog + 상점 NPC + tutorial 1 scene 외 dialogue 부재',
            'generic_terms_widespread': '"환수"/"소환수" 147+130 hits across 35 files',
            'class_name_absent': '"소환사" 9 hits, "소환술" 0 hits — class name 으로 dialogue 거의 없음',
            'boss_curse_catalog_only': '"망각의 저주" 1 hit (catalog 외 0)',
            'shop_npc_role': 'NPCUI_GUARDIANSHOP_DAT = 수호자 상점 = 환수 획득 UI',
            'tutorial_scene': 'n0124_scn 이 베놈 을 예시로 환수 시스템 설명',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_summon_dialogue_xref.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] scanned {scan["files_scanned"]} files / {scan["bytes_scanned"]:,} bytes')
    print()
    print('=== Individual summon names ===')
    for n in SUMMON_NAMES:
        info = counts[n]
        print(f'  {n:10s}: hits={info["hits"]:4d}  files={len(info["files"]):3d}')
    print()
    print('=== Generic terms ===')
    for n in GENERIC:
        info = counts[n]
        print(f'  {n:14s}: hits={info["hits"]:4d}  files={len(info["files"]):3d}')
    print()
    print('=== Summon source files (where 환수 이름이 출현) ===')
    for f in source_files:
        print(f'  [{",".join(f["roles"]):20s}] {f["path"]} ({f["summon_count"]}/5 환수)')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
