"""_mp extras 영역 통계 분석 — Ghidra 없이 record 구조 추정.

전 134 맵의 extras 를 모아:
  1) 첫 1~2 바이트 (entity count?) 분포
  2) 짝수/홀수 record size 후보 (2..16) 별 정합 점수
  3) 짝지어진 byte 들 중 width/height 범위 안에 들어오는 candidate
     → x, y 위치 추정

출력: work/extras_summary.json + 사람이 읽을 수 있는 stdout 리포트.

사용:
    python analyze_mp_extras.py
"""
from __future__ import annotations
import json, pathlib, collections, statistics

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAPS = ROOT / 'work' / 'extracted' / 'map'
OUT  = ROOT / 'work' / 'extras_summary.json'


def parse_mp(data: bytes):
    if len(data) < 10:
        return None
    version = data[0]
    if version not in (0x02, 0x03): return None
    hdr_size = 5 if version == 0x02 else 6
    name_len = data[hdr_size]
    name_start = hdr_size + 1
    name_end = name_start + name_len
    if name_end >= len(data): return None
    name = data[name_start:name_end].decode('ascii', errors='replace')
    if data[name_end] != 0:
        return None
    pos = name_end + 1
    if pos + 4 > len(data): return None
    width = data[pos]; pos += 1
    height = data[pos]; pos += 1
    pal_count = data[pos]; pos += 1
    pos += 1   # meta4
    pos += pal_count
    grid_size = width * height
    extras_start = pos + 2 * grid_size
    if extras_start > len(data): return None
    extras = data[extras_start:]
    return {'name': name, 'w': width, 'h': height, 'extras': extras}


def score_record_size(extras: bytes, w: int, h: int, rec_size: int) -> tuple[float, int]:
    """추정 record size 가 얼마나 잘 맞는지.

    가설: 첫 byte = entity count, 그 다음 count*rec_size bytes 가 record.
    각 record 의 어떤 byte 두 개가 (x in [0,w), y in [0,h)) 좌표일 것이라고 본다.
    score = (#valid records) / (count) 와 길이 매칭 함께 평가.
    """
    if len(extras) < 1: return (0.0, 0)
    count = extras[0]
    if count == 0: return (0.0, 0)
    needed = 1 + count * rec_size
    if needed > len(extras): return (0.0, count)
    body = extras[1:needed]
    valid = 0
    for i in range(count):
        rec = body[i*rec_size:(i+1)*rec_size]
        # 어느 두 byte 든 (x,y) 후보가 되면 OK
        any_xy = False
        for a in range(rec_size):
            for b in range(rec_size):
                if a == b: continue
                if 0 < rec[a] < w and 0 < rec[b] < h:
                    any_xy = True; break
            if any_xy: break
        if any_xy: valid += 1
    coverage_after = (len(extras) - needed) / max(1, len(extras))
    consumed_ratio = needed / max(1, len(extras))
    base = valid / count
    # 길이의 절반 이상을 소비할수록 점수 가산
    return (base * (0.4 + 0.6 * consumed_ratio), count)


def main():
    if not MAPS.exists():
        print(f'  ERROR: {MAPS} not found')
        return 1
    files = sorted(MAPS.glob('map*_mp'))
    summaries = []
    sizes_score = collections.Counter()
    sizes_total = collections.Counter()

    for f in files:
        info = parse_mp(f.read_bytes())
        if info is None:
            continue
        extras = info['extras']
        if len(extras) < 4:
            summaries.append({'file': f.name, 'name': info['name'], 'extras_len': len(extras), 'count': None})
            continue
        first = extras[0]
        # 6,7,8 byte record 이 가장 흔한 후보
        results = {}
        for rs in (4, 5, 6, 7, 8, 9, 10, 12):
            sc, cnt = score_record_size(extras, info['w'], info['h'], rs)
            results[rs] = {'score': round(sc, 3), 'count': cnt}
            sizes_total[rs] += sc
            if sc > 0.7:
                sizes_score[rs] += 1
        best = max(results.items(), key=lambda x: x[1]['score'])
        summaries.append({
            'file': f.name,
            'name': info['name'],
            'w': info['w'], 'h': info['h'],
            'extras_len': len(extras),
            'first_byte': first,
            'best_rec_size': best[0],
            'best_score': best[1]['score'],
            'scores': results,
            'extras_hex_head': extras[:24].hex(),
        })

    # 전체 통계
    rec_winner = sizes_total.most_common()
    print(f'maps parsed: {len(summaries)}')
    print('record-size aggregate score (sum across maps; higher=better):')
    for rs, s in sorted(rec_winner, key=lambda x: -x[1]):
        passes = sizes_score[rs]
        print(f'  rec_size={rs:2d}  agg={s:7.2f}  high-confidence(>0.7)={passes}')

    # best rec size per map 분포
    best_dist = collections.Counter(s['best_rec_size'] for s in summaries if s.get('best_rec_size'))
    print('\nbest record size distribution per map:')
    for rs, c in best_dist.most_common():
        print(f'  {rs}: {c} maps')

    # 첫 바이트 (count) 분포
    first_dist = collections.Counter(s['first_byte'] for s in summaries if 'first_byte' in s)
    print('\nfirst-byte (entity count?) distribution (top 15):')
    for v, c in first_dist.most_common(15):
        print(f'  {v:3d}: {c} maps')

    # map0 상세
    m0 = next((s for s in summaries if s['file'] == 'map0_mp'), None)
    if m0:
        print(f'\nmap0 detail: {m0["name"]} {m0["w"]}x{m0["h"]} extras={m0["extras_len"]} first={m0["first_byte"]}')
        for rs, r in m0['scores'].items():
            print(f'  rs={rs}: score={r["score"]} count={r["count"]}')
        print(f'  extras_hex_head: {m0["extras_hex_head"]}')

    OUT.write_text(json.dumps({'maps': summaries,
                               'rec_size_aggregate': dict(rec_winner),
                               'best_rec_size_distribution': dict(best_dist)},
                              indent=2), encoding='utf-8')
    print(f'\nwrote {OUT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
