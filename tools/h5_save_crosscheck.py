"""Save/Load write↔read event 매칭으로 파일 layout 확정.

각 save 함수 write event 와 대응하는 load 함수 read event 를 file offset 별로
정렬하여, 동일 offset 의 read/write pair 가 같은 size 인지 cross-check.

사용: python tools/h5_save_crosscheck.py <save_sym> <load_sym>
"""
from __future__ import annotations
import pathlib, sys, csv

ROOT = pathlib.Path(__file__).resolve().parent.parent
ANL = ROOT / 'work/h5/analysis'

# Patterns
WRITE_KINDS = {'tobyte', 'strb', 'strh', 'str'}
READ_KINDS = {'bytetoint', 'ldrb', 'ldrh', 'ldr', 'ldrsb', 'ldrsh'}


def load_events(sym: str) -> list[dict]:
    path = ANL / f'{sym}_writes.tsv'
    out = []
    with path.open(encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            off = row['offset']
            try:
                off_int = int(off, 0) if off != '?' else None
            except ValueError:
                off_int = None
            row['offset_int'] = off_int
            row['size_int'] = int(row['size']) if row['size'] != '?' else None
            out.append(row)
    return out


def filter_by_buf(events: list[dict], buf_filter: set[str]) -> list[dict]:
    """특정 buffer register 만 통과 (file buffer 추적용)."""
    return [e for e in events if e['buf'] in buf_filter]


def collect_offsets(events: list[dict], kinds: set[str]) -> dict:
    """offset → list of (size, kind, addr) 집계."""
    by_off = {}
    for e in events:
        if e['kind'] not in kinds: continue
        off = e['offset_int']
        if off is None: continue
        by_off.setdefault(off, []).append((e['size_int'], e['kind'], e['addr']))
    return by_off


def main():
    if len(sys.argv) < 3:
        # Default: SaveHeroData ↔ LoadHeroData
        save_sym = '_ZN4HERO12SaveHeroDataEa'
        load_sym = '_ZN4HERO12LoadHeroDataEa'
        # The file buffer in save = r4 + offset variants seen as r1 (via passing to ToByte)
        save_bufs = {'r4', 'r1'}
        # The file buffer in load = r5 + offset variants (via passing to ByteToInt). Usually r5 or r6.
        load_bufs = {'r6', 'r0'}
    else:
        save_sym, load_sym = sys.argv[1], sys.argv[2]
        save_bufs = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else {'r4', 'r1'}
        load_bufs = set(sys.argv[4].split(',')) if len(sys.argv) > 4 else {'r6', 'r0'}

    saves = load_events(save_sym)
    loads = load_events(load_sym)
    saves_buf = filter_by_buf(saves, save_bufs)
    loads_buf = filter_by_buf(loads, load_bufs)

    s_off = collect_offsets(saves_buf, WRITE_KINDS)
    l_off = collect_offsets(loads_buf, READ_KINDS)

    all_offs = sorted(set(s_off.keys()) | set(l_off.keys()))
    print(f'{"offset":<8}  {"save_size":<10}  {"load_size":<10}  {"match":<6}  note')
    matched = 0
    s_only = 0
    l_only = 0
    mismatch = 0
    for off in all_offs:
        s = s_off.get(off, [])
        l = l_off.get(off, [])
        s_sz = ','.join(f'{sz}({k})' for sz, k, _ in s)
        l_sz = ','.join(f'{sz}({k})' for sz, k, _ in l)
        s_sizes = {sz for sz, _, _ in s}
        l_sizes = {sz for sz, _, _ in l}
        if s and l:
            if s_sizes & l_sizes:
                m = 'OK'
                matched += 1
            else:
                m = 'MISS'
                mismatch += 1
        elif s and not l:
            m = 'S>'
            s_only += 1
        else:
            m = '<L'
            l_only += 1
        if not s_sz: s_sz = '-'
        if not l_sz: l_sz = '-'
        print(f'0x{off:04x}    {s_sz:<10}  {l_sz:<10}  {m:<6}')

    print()
    print(f'summary: matched={matched}  mismatch={mismatch}  save-only={s_only}  load-only={l_only}')
    print(f'(filters: save_bufs={save_bufs}, load_bufs={load_bufs})')


if __name__ == '__main__':
    main()
