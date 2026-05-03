"""각 _scn 파일의 헤더 영역(첫 [speaker] 등장 전) byte 분석.

가설: 첫 화자 태그 이전 영역은 이벤트 메타데이터(map id, trigger, flags 등) 일 수 있음.

출력: work/scn_header_summary.json
"""
from __future__ import annotations
import collections, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCN  = ROOT / 'work' / 'extracted' / 'event'
OUT  = ROOT / 'work' / 'scn_header_summary.json'


def main():
    files = sorted(SCN.glob('e*_scn'))
    sizes = collections.Counter()
    samples = []
    no_speaker = 0

    for f in files:
        data = f.read_bytes()
        first_tag = data.find(b'[')
        if first_tag < 0:
            no_speaker += 1
            continue
        header = data[:first_tag]
        sizes[len(header)] += 1
        samples.append({
            'file': f.name,
            'header_size': len(header),
            'header_hex': header.hex(),
        })

    print(f'files w/o speaker tag: {no_speaker}')
    print(f'\nheader size distribution (top 20):')
    for s, c in sizes.most_common(20):
        print(f'  size={s:5d}: {c}')

    # 처음 10 헤더 출력
    samples.sort(key=lambda x: x['header_size'])
    print(f'\nshortest 10 headers:')
    for s in samples[:10]:
        print(f'  {s["file"]}  ({s["header_size"]} bytes)  {s["header_hex"]}')
    print(f'\nlongest 5 headers:')
    for s in samples[-5:]:
        print(f'  {s["file"]}  ({s["header_size"]} bytes)  {s["header_hex"][:96]}...')

    OUT.write_text(json.dumps({
        'no_speaker_files': no_speaker,
        'size_distribution': sorted(sizes.items()),
        'samples': samples[:30],
    }, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT}')


if __name__ == '__main__':
    main()
