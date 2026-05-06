"""
sprite + _pa + sound 인식 후 남은 .bin 들을 매직별 클러스터링.

산출:
  work/h5/analysis/residual_clusters.txt
"""
from __future__ import annotations
import sys, struct, pathlib, collections, statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'residual_clusters.txt'


def is_sprite(d: bytes) -> bool:
    if len(d) < 14: return False
    if d[8] not in (0x14, 0x18): return False
    cnt = struct.unpack_from('<I', d, 0)[0]
    if cnt == 0 or cnt > 64: return False
    # outer 구조 일관성: u32 count + per_frame (u32 len + payload[len])
    pos = 4
    for _ in range(cnt):
        if pos + 4 > len(d): return False
        ln = struct.unpack_from('<I', d, pos)[0]
        if pos + 4 + ln > len(d): return False
        pos += 4 + ln
    return pos == len(d)


def is_pa(d: bytes) -> bool:
    if len(d) < 5: return False
    c = d[0]
    return 0 < c <= 64 and len(d) == c * 4 + 1


def main() -> int:
    clusters: dict[str, list] = collections.defaultdict(list)
    classified = collections.Counter()
    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        if d[:4] == b'OggS' or d[:4] == b'MMMD':
            classified['sound'] += 1; continue
        if is_sprite(d):
            classified['sprite'] += 1; continue
        if is_pa(d):
            classified['pa'] += 1; continue
        magic = d[:4].hex() if len(d) >= 4 else d.hex()
        clusters[magic].append((p, d))

    sorted_clusters = sorted(clusters.items(), key=lambda kv: -len(kv[1]))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(f'classified: {dict(classified)}\n')
        f.write(f'residual files: {sum(len(v) for v in clusters.values())} in {len(clusters)} distinct magics\n\n')
        for magic, items in sorted_clusters[:30]:
            sizes = [len(d) for _, d in items]
            f.write(f'== magic {magic}  count={len(items)}  size: min={min(sizes)} max={max(sizes)} median={int(statistics.median(sizes))}\n')
            for p, d in items[:3]:
                hd = ' '.join(f'{b:02x}' for b in d[:32])
                ascii_repr = ''.join(chr(b) if 0x20 <= b < 0x7f else '.' for b in d[:32])
                f.write(f'   {p.name}  ({len(d)}B)\n')
                f.write(f'     hex:   {hd}\n')
                f.write(f'     ascii: {ascii_repr}\n')
            f.write('\n')

        # tail summary
        if len(sorted_clusters) > 30:
            tail_files = sum(len(v) for _, v in sorted_clusters[30:])
            f.write(f'\n... and {len(sorted_clusters)-30} smaller magic groups ({tail_files} files)\n')

    print(open(OUT, encoding='utf-8').read()[:5000])
    return 0


if __name__ == '__main__':
    sys.exit(main())
