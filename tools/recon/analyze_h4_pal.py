"""Hero4 _PAL secondary RGB 의미 통계 분석.

_PAL 포맷 (2026-05-18 재확정):
    byte 0       : u8 count N
    byte 1..1+8N : N × 8-byte entries
    8-byte entry : R1 G1 B1 A1 R2 G2 B2 A2

A1/A2 (byte 3/7) 의 의미 + secondary RGB(R2,G2,B2) 가 primary 대비
어떤 관계인지 통계로 추론. 가설:
    (a) alpha mask — A1/A2 가 0/255 같은 mask 값
    (b) shadow color — 항상 더 어두운 톤
    (c) animation frame — 무관한 두 색
    (d) palette swap — primary 와 같음 (변형 안 됨)
"""
from __future__ import annotations
import os, pathlib, sys, json
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
PAL_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'H4' / 'PAL'


def analyze():
    files = sorted(PAL_DIR.glob('*_PAL'))
    total = 0
    a1_dist, a2_dist = Counter(), Counter()
    cat = Counter()
    samples_diff = []
    samples_same = []

    for fp in files:
        d = fp.read_bytes()
        if len(d) < 1:
            continue
        cnt = d[0]
        if 1 + cnt * 8 != len(d):
            continue
        for i in range(cnt):
            off = 1 + i*8
            if off + 8 > len(d):
                break
            r1, g1, b1, a1, r2, g2, b2, a2 = d[off:off+8]
            total += 1
            a1_dist[a1] += 1
            a2_dist[a2] += 1
            same = (r1, g1, b1) == (r2, g2, b2)

            if same:
                cat['identical'] += 1
                if len(samples_same) < 5:
                    samples_same.append((fp.name, i, (r1,g1,b1), (r2,g2,b2)))
                continue

            # Scaled?
            ratios = []
            for p, s in [(r1, r2), (g1, g2), (b1, b2)]:
                if p > 0:
                    ratios.append(s / p)
                elif s == 0:
                    ratios.append(1.0)
                else:
                    ratios.append(None)
            valid = [r for r in ratios if r is not None]
            avg1 = (r1 + g1 + b1) / 3
            avg2 = (r2 + g2 + b2) / 3
            d_avg = avg2 - avg1

            if valid and (max(valid) - min(valid)) < 0.15 and len(valid) >= 2:
                k = sum(valid) / len(valid)
                if k < 0.85:
                    cat['scaled_darker'] += 1
                elif k > 1.15:
                    cat['scaled_lighter'] += 1
                else:
                    cat['scaled_near1'] += 1
            elif d_avg < -10:
                cat['darker_no_scale'] += 1
            elif d_avg > 10:
                cat['lighter_no_scale'] += 1
            else:
                cat['independent'] += 1

            if len(samples_diff) < 12:
                rdiff = r2 - r1
                gdiff = g2 - g1
                bdiff = b2 - b1
                samples_diff.append((fp.name, i, (r1,g1,b1), (r2,g2,b2), rdiff, gdiff, bdiff))

    print(f'Total entries: {total}')
    print(f'\nA1 (byte 3) top-5: {dict(a1_dist.most_common(5))}')
    print(f'A2 (byte 7) top-5: {dict(a2_dist.most_common(5))}')

    print(f'\n=== Primary vs Secondary RGB relationship ===')
    for name, count in cat.most_common():
        pct = count * 100 / total
        print(f'  {name:24} {count:6} ({pct:5.1f}%)')

    print(f'\n=== Identical samples (primary == secondary) ===')
    for fname, i, p, s in samples_same:
        print(f'  {fname} ent[{i}]: RGB{p}')

    print(f'\n=== Different samples ===')
    for fname, i, p, s, dr, dg, db in samples_diff:
        sign = 'DARKER ' if (dr+dg+db) < 0 else 'LIGHTER'
        print(f'  {fname} ent[{i}]: P=RGB{p} S=RGB{s} Δ=({dr:+4d},{dg:+4d},{db:+4d}) {sign}')

    # Write summary JSON
    out = ROOT / 'work' / 'h4' / 'converted' / 'pal_secondary_stats.json'
    summary = {
        'total_entries': total,
        'alpha1_top10': dict(a1_dist.most_common(10)),
        'alpha2_top10': dict(a2_dist.most_common(10)),
        'relationship': dict(cat),
        'relationship_percent': {k: round(v*100/total, 2) for k, v in cat.items()},
    }
    out.write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(f'\nWrote summary: {out}')


if __name__ == '__main__':
    analyze()
