"""각 [speaker] 태그 직전의 byte 시퀀스를 모아 통계 — 대사 표시 opcode 후보 추출.

가설: [name] 등장 직전 1~6 byte 가 "다음 대사 시작" 명령일 가능성.

출력: work/scn_dialogue_opcode.json
"""
from __future__ import annotations
import collections, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCN  = ROOT / 'work' / 'extracted' / 'event'
OUT  = ROOT / 'work' / 'scn_dialogue_opcode.json'


def main():
    files = sorted(SCN.glob('e*_scn'))
    prefix_freq = collections.Counter()  # 1-byte
    pair_freq   = collections.Counter()  # 2-byte
    triple_freq = collections.Counter()  # 3-byte
    samples = collections.defaultdict(list)
    total_tags = 0

    for f in files:
        data = f.read_bytes()
        i = 0
        while i < len(data):
            if data[i] == 0x5b and i > 0:
                end = data.find(b']', i + 1)
                if end > 0 and end - i < 32:
                    total_tags += 1
                    p1 = data[i-1]
                    prefix_freq[p1] += 1
                    if i >= 2:
                        p2 = data[i-2:i]
                        pair_freq[bytes(p2)] += 1
                    if i >= 3:
                        p3 = data[i-3:i]
                        triple_freq[bytes(p3)] += 1
                    i = end + 1
                    continue
            i += 1

    print(f'speaker tags total: {total_tags}')
    print('\nTop 20 1-byte prefix:')
    for b, c in prefix_freq.most_common(20):
        print(f'  {b:#04x}  count={c}')
    print('\nTop 20 2-byte prefix:')
    for b, c in pair_freq.most_common(20):
        hex_ = ' '.join(f'{x:02x}' for x in b)
        print(f'  {hex_}  count={c}')
    print('\nTop 20 3-byte prefix:')
    for b, c in triple_freq.most_common(20):
        hex_ = ' '.join(f'{x:02x}' for x in b)
        print(f'  {hex_}  count={c}')

    OUT.write_text(json.dumps({
        'total_tags': total_tags,
        'top_1byte': [(f'{b:#04x}', c) for b, c in prefix_freq.most_common(64)],
        'top_2byte': [(' '.join(f'{x:02x}' for x in b), c) for b, c in pair_freq.most_common(64)],
        'top_3byte': [(' '.join(f'{x:02x}' for x in b), c) for b, c in triple_freq.most_common(64)],
    }, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT}')


if __name__ == '__main__':
    main()
