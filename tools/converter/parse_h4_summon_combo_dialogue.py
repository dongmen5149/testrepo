"""Hero4 Round 108 — 환수 combo skill dialogue 검색 (R103 후속).

R103 에서 발견한 3 환수 combo alt-form skill 의 dialogue 등장 여부 확인:
- 환수 합신 (S002, lvl 6, MP 27)
- 환수특공 (S003, lvl 10, MP 24)
- 환수증폭 (S003, lvl 10, MP 28)

+ R103 primary 의 환수 관련 skill:
- 환수흡수 (S003 primary, lvl 10)
- 흡혈환수 (S003 primary, lvl 11)

전체 decrypted corpus (252 파일/484KB) EUC-KR 디코딩 후 keyword 검색.
HDAT catalog (skill 이름 자체) 와 SCN/NPC dialogue 를 분리해서 표시.
"""
from __future__ import annotations
import json
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DECRYPTED = ROOT / 'work' / 'h4' / 'decrypted'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

COMBO_KEYWORDS = [
    '환수 합신', '환수합신',
    '환수특공', '환수 특공',
    '환수증폭', '환수 증폭',
    '환수흡수', '환수 흡수',
    '흡혈환수', '흡혈 환수',
]


def classify(path: str) -> str:
    if path.startswith('HDAT/'):
        return 'catalog_hdat'
    if path.startswith('ITM/'):
        return 'catalog_item'
    if path.startswith('NPC/'):
        return 'npc_shop_or_quest'
    if path.startswith('MAP/') or path.endswith('_scn'):
        return 'scene_dialogue'
    if path.startswith('E/'):
        return 'event_script'
    if path.startswith('FR/'):
        return 'battle_frame'
    return 'other'


def scan() -> dict:
    results = {k: [] for k in COMBO_KEYWORDS}
    files_scanned = 0
    bytes_scanned = 0
    for root, _, files in os.walk(DECRYPTED):
        for fn in files:
            p = pathlib.Path(root) / fn
            try:
                data = p.read_bytes()
            except OSError:
                continue
            files_scanned += 1
            bytes_scanned += len(data)
            txt = data.decode('euc-kr', errors='replace')
            relp = str(p.relative_to(DECRYPTED)).replace('\\', '/')
            for k in COMBO_KEYWORDS:
                start = 0
                while True:
                    idx = txt.find(k, start)
                    if idx < 0:
                        break
                    s = max(0, idx - 60)
                    e = min(len(txt), idx + 60 + len(k))
                    excerpt = txt[s:e]
                    excerpt = re.sub(
                        r'[^\x20-\x7e가-힣ㅏ-ㅣ.,!?·<>{}()\[\] ]', '·', excerpt
                    )
                    results[k].append({
                        'path': relp,
                        'role': classify(relp),
                        'offset': idx,
                        'excerpt': excerpt,
                    })
                    start = idx + len(k)
    return {
        'files_scanned': files_scanned,
        'bytes_scanned': bytes_scanned,
        'hits': results,
    }


def main() -> int:
    scan_result = scan()
    hits = scan_result['hits']

    # Merge variants (with/without space)
    canonical = {
        '환수 합신': ['환수 합신', '환수합신'],
        '환수특공': ['환수특공', '환수 특공'],
        '환수증폭': ['환수증폭', '환수 증폭'],
        '환수흡수': ['환수흡수', '환수 흡수'],
        '흡혈환수': ['흡혈환수', '흡혈 환수'],
    }

    merged = {}
    for canon, variants in canonical.items():
        all_hits = []
        for v in variants:
            all_hits.extend(hits.get(v, []))
        # Per-role breakdown
        by_role: dict[str, int] = {}
        scene_or_npc_hits = []
        for h in all_hits:
            by_role[h['role']] = by_role.get(h['role'], 0) + 1
            if h['role'] in ('scene_dialogue', 'npc_shop_or_quest', 'event_script'):
                scene_or_npc_hits.append(h)
        merged[canon] = {
            'total_hits': len(all_hits),
            'file_count': len({h['path'] for h in all_hits}),
            'by_role': by_role,
            'dialogue_hits': scene_or_npc_hits,  # non-catalog only
            'all_hits_sample': all_hits[:5],
        }

    out = {
        'round': 108,
        'topic': 'summon combo skill dialogue search (R103 follow-up)',
        'corpus_meta': {
            'files_scanned': scan_result['files_scanned'],
            'bytes_scanned': scan_result['bytes_scanned'],
        },
        'keywords_searched': list(canonical.keys()),
        'results': merged,
        'interpretation': {
            'catalog_only': [k for k, v in merged.items()
                             if v['total_hits'] > 0
                             and not any(r in v['by_role'] for r in
                                         ('scene_dialogue', 'npc_shop_or_quest', 'event_script'))],
            'has_dialogue': [k for k, v in merged.items() if v['dialogue_hits']],
            'absent': [k for k, v in merged.items() if v['total_hits'] == 0],
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_summon_combo_dialogue.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] scanned {scan_result["files_scanned"]} files / {scan_result["bytes_scanned"]:,} bytes')
    print()
    print('=== R108 환수 combo skill dialogue 검색 ===')
    for canon, info in merged.items():
        print(f'\n  {canon}:')
        print(f'    total_hits={info["total_hits"]}  files={info["file_count"]}')
        print(f'    by_role={info["by_role"]}')
        if info['dialogue_hits']:
            print(f'    [!] scene/npc/event dialogue hits = {len(info["dialogue_hits"])}')
            for h in info['dialogue_hits'][:3]:
                print(f'      - [{h["role"]}] {h["path"]} @ {h["offset"]}')
                print(f'        > {h["excerpt"]!r}')
    print()
    print('=== 분류 요약 ===')
    print(f'  catalog_only (skill 정의만): {out["interpretation"]["catalog_only"]}')
    print(f'  has_dialogue (story 노출):   {out["interpretation"]["has_dialogue"]}')
    print(f'  absent (전혀 없음):           {out["interpretation"]["absent"]}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
