"""[speaker] 이후 (대사 텍스트 끝) 부터 다음 [speaker] 사이의 byte 영역 분석.

가설: 대사가 끝나고 다음 화자 등장까지 사이에 분기/이펙트/사운드/페이드 명령 들어있음.

출력: work/scn_inter_summary.json + 빈번 시퀀스 top
"""
from __future__ import annotations
import collections, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCN  = ROOT / 'work' / 'extracted' / 'event'
OUT  = ROOT / 'work' / 'scn_inter_summary.json'


def is_kr_lead(b: int) -> bool: return 0xa1 <= b <= 0xfe


def main():
    files = sorted(SCN.glob('e*_scn'))
    inter_sizes = collections.Counter()
    inter_byte_freq = collections.Counter()
    inter_pair_freq = collections.Counter()
    inter_triple_freq = collections.Counter()
    inter_total = 0

    for f in files:
        data = f.read_bytes()
        # 화자 태그 위치 모두 수집
        tag_positions: list[tuple[int, int]] = []   # (start, end_after_])
        i = 0
        while i < len(data):
            if data[i] == 0x5b:
                end = data.find(b']', i + 1)
                if end > 0 and end - i < 32:
                    tag_positions.append((i, end + 1))
                    i = end + 1
                    continue
            i += 1
        # 인접 태그 사이 영역에서 "마지막 한국어 텍스트 끝 ~ 다음 태그 시작" 만 추출
        for k in range(len(tag_positions) - 1):
            start = tag_positions[k][1]
            end   = tag_positions[k + 1][0]
            # 한국어 런 스킵: 태그 끝 이후의 텍스트 영역 건너뛰기
            j = start
            last_kr_end = j
            while j < end:
                if j + 1 < end and is_kr_lead(data[j]) and is_kr_lead(data[j+1]):
                    j += 2
                    last_kr_end = j
                else:
                    j += 1
            inter = data[last_kr_end:end]
            if not inter: continue
            inter_total += 1
            inter_sizes[len(inter)] += 1
            for b in inter:
                inter_byte_freq[b] += 1
            for x in range(len(inter) - 1):
                inter_pair_freq[(inter[x], inter[x+1])] += 1
            for x in range(len(inter) - 2):
                inter_triple_freq[(inter[x], inter[x+1], inter[x+2])] += 1

    print(f'inter regions: {inter_total}')
    print('\nsize distribution (top):')
    for sz, c in inter_sizes.most_common(15):
        print(f'  size={sz}: {c}')
    print('\ntop 15 single bytes:')
    for b, c in inter_byte_freq.most_common(15):
        print(f'  {b:#04x}  {c}')
    print('\ntop 15 byte pairs:')
    for (a, b), c in inter_pair_freq.most_common(15):
        print(f'  {a:#04x} {b:#04x}  {c}')
    print('\ntop 10 byte triples:')
    for (a, b, c2), c in inter_triple_freq.most_common(10):
        print(f'  {a:#04x} {b:#04x} {c2:#04x}  {c}')

    OUT.write_text(json.dumps({
        'inter_total': inter_total,
        'size_top':   [(s, c) for s, c in inter_sizes.most_common(40)],
        'top_bytes':  [(f'{b:#04x}', c) for b, c in inter_byte_freq.most_common(40)],
        'top_pairs':  [(' '.join(f'{x:02x}' for x in p), c) for p, c in inter_pair_freq.most_common(40)],
        'top_triples':[(' '.join(f'{x:02x}' for x in p), c) for p, c in inter_triple_freq.most_common(40)],
    }, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT}')


if __name__ == '__main__':
    main()
