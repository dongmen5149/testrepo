"""_scn 파일들에서 [...] 패턴 안의 텍스트(화자/태그 추정) 를 추출.

가설: 0x5b ... 0x5d 안의 EUC-KR 텍스트가 화자 이름 또는 이벤트 태그.

출력:
  - work/scn_speakers.json  — {speaker: count, samples: [...]}
  - stdout: top 30
"""
from __future__ import annotations
import collections, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCN  = ROOT / 'work' / 'extracted' / 'event'
OUT  = ROOT / 'work' / 'scn_speakers.json'


def main():
    files = sorted(SCN.glob('e*_scn'))
    pattern = re.compile(rb'\[([^\[\]\x00]{1,30})\]')
    speakers = collections.Counter()
    samples: dict[str, list[str]] = collections.defaultdict(list)

    for f in files:
        data = f.read_bytes()
        for m in pattern.finditer(data):
            raw = m.group(1)
            # 모두 ASCII printable 만이면 태그(영문) 일 가능성, EUC-KR 면 한국어 화자
            try:
                text = raw.decode('euc-kr', errors='strict')
            except UnicodeDecodeError:
                continue
            # 너무 짧거나 제어문자만이면 건너뜀
            if len(text) < 1 or len(text) > 12: continue
            if not any(ord(c) >= 32 for c in text): continue
            speakers[text] += 1
            if len(samples[text]) < 3:
                samples[text].append(f.name)

    print(f'unique speaker/tag candidates: {len(speakers)}')
    print(f'\nTop 30:')
    for name, c in speakers.most_common(30):
        print(f'  {c:5d}  {name}')

    OUT.write_text(json.dumps({
        'count': len(speakers),
        'top': [(n, c, samples[n]) for n, c in speakers.most_common(200)],
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
