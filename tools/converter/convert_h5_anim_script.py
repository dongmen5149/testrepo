"""
Hero5 SMALL_SCRIPT / MID_SCRIPT / LARGE_ANIM 파서.

`19 19` 는 record terminator (animation event 끝).

확인된 record 패턴 (00825_96cd4dac.bin / 00826_96cd4dad.bin):
  파일 헤더: u8[4] 01 00 01 01
  record 0: <type:u8> <op:u8> <const:u16=0x0580> <timing:u16> [19 19]   = 8B
  record 1+: <00 chan:u8> <00 sub:u8> <const:u16=0x0580 or 0x0780> <timing:u16> [19 19]  = 10B

  chan/sub byte 들이 0x82, 0x50, 0x32 등 → 채널/이벤트 타입.
  timing u16 은 누적 증가 → tick count.

확인된 다른 sentinel: `20 20` (00827) — 큰 anim 파일 변종.
LARGE_ANIM (`19 19` + 큰 페이로드) 는 동일 구조의 multi-channel.

산출:
  work/h5/analysis/anim_records.tsv — 파일별 record 분리 결과
  work/h5/analysis/anim_records_summary.txt — 통계
"""
from __future__ import annotations
import pathlib, csv, collections, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'
OUT_TSV = ROOT / 'work' / 'h5' / 'analysis' / 'anim_records.tsv'
OUT_SUM = ROOT / 'work' / 'h5' / 'analysis' / 'anim_records_summary.txt'


def split_records(data: bytes, sentinel: bytes = b'\x19\x19'):
    """Find all sentinel positions and split into records."""
    positions = []
    i = 0
    while i < len(data) - 1:
        if data[i:i+2] == sentinel:
            positions.append(i)
            i += 2
        else:
            i += 1
    records = []
    prev = 0
    for pos in positions:
        records.append(data[prev:pos])
        prev = pos + 2
    if prev < len(data):
        records.append(data[prev:])  # trailing data without terminator
    return records, positions


def main() -> int:
    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    files_processed = 0
    files_with_marker = 0
    record_size_dist = collections.Counter()
    first_byte_dist = collections.Counter()
    channel_dist = collections.Counter()
    sentinel_use = collections.Counter()

    rows = []
    with open(CATALOG, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['type'] != 'bin': continue
            length = int(row['length'])
            if length < 30 or length > 100_000: continue
            idx = int(row['index']); h = int(row['hash'], 16)
            p = ENTRIES / f'{idx:05d}_{h:08x}.bin'
            if not p.exists(): continue
            d = p.read_bytes()
            files_processed += 1

            # check sentinels
            cnt_19 = sum(1 for i in range(len(d)-1) if d[i]==0x19 and d[i+1]==0x19)
            cnt_20 = sum(1 for i in range(len(d)-1) if d[i]==0x20 and d[i+1]==0x20)
            if cnt_19 < 2 and cnt_20 < 2:
                continue

            sentinel = b'\x19\x19' if cnt_19 >= cnt_20 else b'\x20\x20'
            sentinel_use[sentinel.hex()] += 1
            recs, pos = split_records(d, sentinel)
            if len(recs) < 2: continue
            files_with_marker += 1

            for r in recs:
                if not r: continue
                record_size_dist[len(r)] += 1
                first_byte_dist[r[0]] += 1
                # record format guess: <chan_hi:u8> <chan:u8> <const:u16> <timing:u16>
                if len(r) >= 6:
                    chan = r[1] if r[0] == 0 else r[0]
                    channel_dist[chan] += 1

            # only dump first 5 examples per record-size cluster to keep output manageable
            for ri, r in enumerate(recs[:8]):
                rows.append({
                    'file': p.name,
                    'sentinel': sentinel.hex(),
                    'record_idx': ri,
                    'len': len(r),
                    'hex': r.hex(),
                })

    with open(OUT_TSV, 'w', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else
                          ['file','sentinel','record_idx','len','hex'],
                          delimiter='\t')
        w.writeheader()
        for r in rows: w.writerow(r)

    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write(f'files processed (30B-100KB bin): {files_processed}\n')
        f.write(f'files with >=2 records (any sentinel): {files_with_marker}\n')
        f.write(f'\nsentinel usage:\n')
        for s, n in sentinel_use.most_common():
            f.write(f'  {s}  ×{n}\n')
        f.write(f'\nrecord size distribution (top 20):\n')
        for sz, n in sorted(record_size_dist.most_common(20)):
            f.write(f'  size={sz:5}B  ×{n}\n')
        f.write(f'\nrecord first-byte distribution (top 20):\n')
        for b, n in first_byte_dist.most_common(20):
            f.write(f'  0x{b:02x}  ×{n}\n')
        f.write(f'\nchannel byte distribution (top 30):\n')
        for c, n in channel_dist.most_common(30):
            f.write(f'  0x{c:02x}  ×{n}\n')

    print(f'files processed: {files_processed}')
    print(f'files with marker structure: {files_with_marker}')
    print(f'sentinel usage: {dict(sentinel_use.most_common())}')
    print(f'top record sizes: {record_size_dist.most_common(8)}')
    print(f'top channel bytes: {channel_dist.most_common(8)}')
    print(f'\nwrote {OUT_TSV}')
    print(f'wrote {OUT_SUM}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
