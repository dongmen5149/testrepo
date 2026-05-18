"""Hero4 전체 트리에서 SCN-키로 복호화 가능한 파일 발굴 스캔.

검증된 SCN cipher block sentinels (ECB DES 패턴 = 같은 키 강력 시사):
    3b7af9a427907dac  : SCN last (×38), HDAT-A (×92) — 가장 강한 marker
    1b7559e5bcf49488  : SCN last (×13)
    ef9c94a1d8247276  : SCN last (×12)
    c0f2daf72c2210e1  : SCN last (×11)
    f7740f758b9a6ae4  : SCN second (×17)

발견:
    1. CONFIRMED (sentinel match): 94 files Hero4-wide
       - SCN/MAP: 다수 (348개 SCN 일부 중복 카운트됨)
       - HDAT Group A: 7/8 (sentinel @offset 16~344)
       - E/: BSDAT_0/1/2 + ESDAT_0/1/2 = 6 dialog scripts
       - ITM/: ITM_08/13/OPTION/Q_REPAY_1/REPAY_0 = 5
       - NPC/: PROBABILITY_DAT = 1

    2. LIKELY (no sentinel but high entropy + 8B aligned): 150 files
       - 대부분 SCN/SC 의 다른 348 encrypted files
       - ITM/DAT/ 21 more (전체 26 ITM/DAT 중 5 confirmed + 21 likely = ~26)
       - NPC/ 6 (QUEST_0/1_DAT, NPCUI_COMBINE_DAT_0/1/2, NPCUI_GUARDIANSHOP_DAT)
       - FR/ 3 (_FR_BA, _FR_PL, _FR_SK — _FR_EN/SU 작아서 sentinel 못 찾음)

Total unblocking set (sentinel + size/entropy heuristic):
    - SCN: 350 (348 encrypted + 2 plaintext)
    - HDAT Group A: 8
    - E/ scripts: 6
    - ITM/DAT: ~26
    - NPC scripts: ~7
    - FR/: ~5
    → ~400 파일 동시 복호화 (DES key 1개 발견 시).
"""
from __future__ import annotations
import argparse, json, math, pathlib, sys
from collections import Counter, defaultdict


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXTRACTED = ROOT / 'work' / 'h4' / 'extracted'
OUT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'des_encrypted_files_scan.json'

SENTINELS = [
    bytes.fromhex('3b7af9a427907dac'),
    bytes.fromhex('1b7559e5bcf49488'),
    bytes.fromhex('ef9c94a1d8247276'),
    bytes.fromhex('c0f2daf72c2210e1'),
    bytes.fromhex('f7740f758b9a6ae4'),
    bytes.fromhex('4655b8f39c0fe0b2'),  # SCN first
    bytes.fromhex('38d18f6ac1c49c07'),  # SCN first
]


def entropy(d: bytes) -> float:
    if not d: return 0
    freq = Counter(d)
    total = len(d)
    return -sum((c/total) * math.log2(c/total) for c in freq.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=str(OUT_JSON))
    ap.add_argument('--entropy_threshold', type=float, default=7.5)
    args = ap.parse_args()

    all_files = [f for f in EXTRACTED.rglob('*') if f.is_file()]
    print(f'Scanning {len(all_files)} files under {EXTRACTED}')

    confirmed = []
    likely = []
    plaintext = []  # files with low entropy (NOT encrypted)

    for f in all_files:
        d = f.read_bytes()
        if len(d) < 8: continue
        aligned = len(d) % 8 == 0
        ent = entropy(d)

        hits = []
        for s in SENTINELS:
            pos = d.find(s)
            if pos >= 0:
                hits.append({'sentinel': s.hex(), 'offset': pos})

        rec = {
            'file': str(f.relative_to(EXTRACTED)).replace('\\', '/'),
            'size': len(d),
            'entropy': round(ent, 3),
            'aligned8': aligned,
            'sentinel_hits': hits,
        }
        if hits:
            confirmed.append(rec)
        elif aligned and ent > args.entropy_threshold:
            likely.append(rec)

    # Group by parent dir
    def group(recs):
        by_dir = defaultdict(list)
        for r in recs:
            parent = str(pathlib.Path(r['file']).parent)
            by_dir[parent].append(r)
        return {k: len(v) for k, v in sorted(by_dir.items())}

    out = {
        'sentinels': [s.hex() for s in SENTINELS],
        'confirmed_count': len(confirmed),
        'likely_count': len(likely),
        'confirmed_by_dir': group(confirmed),
        'likely_by_dir': group(likely),
        'confirmed': confirmed,
        'likely': likely,
    }
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    print(f'\nConfirmed (sentinel match): {len(confirmed)}')
    print('  Distribution by dir:')
    for d, c in out['confirmed_by_dir'].items():
        print(f'    {d:25}: {c}')
    print(f'\nLikely (high entropy aligned, no sentinel): {len(likely)}')
    print('  Distribution by dir:')
    for d, c in out['likely_by_dir'].items():
        print(f'    {d:25}: {c}')

    # Total unique non-SCN unblocking files
    non_scn_conf = [r for r in confirmed if not r['file'].startswith('MAP/SC/')]
    non_scn_likely = [r for r in likely if not r['file'].startswith('MAP/SC/')]
    print(f'\n=== NEW non-SCN unblocking files (excluding 348 SCN already known) ===')
    print(f'  Confirmed: {len(non_scn_conf)}')
    print(f'  Likely:    {len(non_scn_likely)}')
    print(f'\n  -> Total decryption pool when DES key found:')
    print(f'     350 (SCN incl 2 plaintext) + 8 (HDAT Group A) + {len(non_scn_conf) - 7}  NEW confirmed + {len(non_scn_likely)} likely')
    print(f'     ~{350 + 8 + (len(non_scn_conf) - 7) + len(non_scn_likely)} files total')

    print(f'\n-> {args.out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
