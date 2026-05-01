"""모든 _scn dialogue JSON 을 모아 단일 corpus 파일로 빌드.

출력:
    work/converted/dialogue_corpus.json
        [
            {"event": "e0000", "offset": 1080, "text": "솔티아"},
            ...
        ]

i18n 번역 작업의 베이스라인. 중복 텍스트는 unique 화 가능.
"""
from __future__ import annotations
import json, pathlib, sys
from collections import Counter

CONVERTED = pathlib.Path(__file__).parent.parent.parent / 'work' / 'converted'


def main():
    event_dir = CONVERTED / 'event'
    if not event_dir.exists():
        print(f'No event dir at {event_dir}', file=sys.stderr)
        return 1

    all_lines = []
    text_freq = Counter()
    for jpath in sorted(event_dir.glob('*_scn.json')):
        info = json.loads(jpath.read_text(encoding='utf-8'))
        event_name = jpath.stem.replace('_scn', '')
        for d in info.get('dialogue', []):
            all_lines.append({
                'event': event_name,
                'offset': d['offset'],
                'text': d['text'],
                'char_count': d['char_count'],
            })
            text_freq[d['text']] += 1

    out = CONVERTED / 'dialogue_corpus.json'
    out.write_text(json.dumps({
        'total_lines': len(all_lines),
        'unique_texts': len(text_freq),
        'lines': all_lines,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'corpus: {len(all_lines)} lines, {len(text_freq)} unique → {out}')

    # 빈도 상위 100개도 별도 dump (가장 많이 등장한 단어/구절 — 캐릭터 이름 등)
    top = text_freq.most_common(200)
    top_path = CONVERTED / 'dialogue_top_texts.json'
    top_path.write_text(json.dumps(
        [{'text': t, 'count': c} for t, c in top], ensure_ascii=False, indent=2),
        encoding='utf-8')
    print(f'top 200 frequent texts → {top_path}')


if __name__ == '__main__':
    sys.exit(main() or 0)
