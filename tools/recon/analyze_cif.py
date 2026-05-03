"""_cif animation_data 영역 통계 분석.

확인된 헤더: uint16 slot_count + slot_count bytes indices.
미해독 영역: 그 이후의 animation_data (timing/event sequence).

가설: 9-byte record 가설(PROGRESS) 검증 + 0xff terminator + `19 19` (frame size?) 패턴 검색.

출력: work/cif_anim_summary.json
"""
from __future__ import annotations
import collections, json, pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXT  = ROOT / 'work' / 'extracted'
OUT  = ROOT / 'work' / 'cif_anim_summary.json'


def parse(data: bytes):
    slot_count = struct.unpack_from('<H', data, 0)[0]
    body = data[2 + slot_count:]
    return slot_count, body


def main():
    files = list(EXT.rglob('*_cif'))
    print(f'cif files: {len(files)}')

    sizes = []
    slot_dist = collections.Counter()
    body_byte_freq = collections.Counter()
    has_ff_term = 0
    has_1919   = 0
    nine_byte_record_score = 0   # body len이 9의 배수인 파일 수
    eight_byte_record_score = 0
    seven_byte_record_score = 0

    for f in files:
        data = f.read_bytes()
        if len(data) < 2: continue
        slot_count, body = parse(data)
        sizes.append(len(data))
        slot_dist[slot_count] += 1
        if not body:
            continue
        if body.endswith(b'\xff'): has_ff_term += 1
        if b'\x19\x19' in body: has_1919 += 1
        # body 길이 가설 검증
        bl = len(body)
        if bl % 9 == 0: nine_byte_record_score += 1
        if bl % 8 == 0: eight_byte_record_score += 1
        if bl % 7 == 0: seven_byte_record_score += 1
        for b in body[:200]:
            body_byte_freq[b] += 1

    avg = sum(sizes) // max(1, len(sizes))
    print(f'avg size: {avg} bytes  (range {min(sizes)}~{max(sizes)})')
    print(f'\nslot count distribution:')
    for s, c in sorted(slot_dist.items()):
        print(f'  slots={s}: {c} files')
    print(f'\nstructural hints:')
    print(f'  ends with 0xff:    {has_ff_term} / {len(files)}')
    print(f'  contains 19 19:    {has_1919} / {len(files)}')
    print(f'  body % 7 == 0:     {seven_byte_record_score} / {len(files)}')
    print(f'  body % 8 == 0:     {eight_byte_record_score} / {len(files)}')
    print(f'  body % 9 == 0:     {nine_byte_record_score} / {len(files)}')
    print(f'\ntop 20 bytes in animation body (first 200 bytes per file):')
    for b, c in body_byte_freq.most_common(20):
        print(f'  {b:#04x}  count={c}')

    OUT.write_text(json.dumps({
        'files': len(files),
        'avg_size': avg,
        'slot_distribution': dict(slot_dist),
        'ends_with_ff': has_ff_term,
        'contains_1919': has_1919,
        'body_mod_7': seven_byte_record_score,
        'body_mod_8': eight_byte_record_score,
        'body_mod_9': nine_byte_record_score,
        'top_body_bytes': [(f'{b:#04x}', c) for b, c in body_byte_freq.most_common(64)],
    }, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT}')


if __name__ == '__main__':
    main()
