"""
Hero5 미매칭 .bin (Hero3/4 파서 hit 없음) 을 첫 4바이트 매직별 클러스터링.

각 클러스터의 첫 파일 1개를 hexdump 32바이트 + 통계 (count/size 분포) 출력.

산출:
  work/h5/analysis/unknown_clusters.txt
"""
from __future__ import annotations
import sys, pathlib, struct, collections, statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools' / 'converter'))
from convert_text import parse_text_table  # noqa
from convert_mp import parse_mp  # noqa
from convert_bm_v2 import find_frame_markers  # noqa

SRC = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'unknown_clusters.txt'


def is_unmatched(data: bytes) -> bool:
    """probe 와 동일 로직 (smaf/ogg/pa/mp/bm/cif/txt 어느것도 hit 안하면 unmatched)."""
    if data[:4] == b'OggS' or data[:4] == b'MMMD':
        return False
    # txt
    if len(data) >= 4:
        try:
            declared = struct.unpack_from('<H', data, 0)[0]
            count = struct.unpack_from('<H', data, 2)[0]
            if declared == len(data) and count > 0 and 4 + count*2 <= len(data):
                ss = parse_text_table(data)
                if any(s.strip() for s in ss):
                    return False
        except Exception:
            pass
    # pa
    if len(data) >= 5:
        c = data[0]
        if c and c <= 64 and len(data) == c*4+1:
            return False
    # mp
    if len(data) >= 10 and data[0] in (0x02, 0x03):
        try:
            parse_mp(data)
            return False
        except Exception:
            pass
    # bm
    if find_frame_markers(data):
        return False
    # cif (weak)
    if len(data) >= 4 and data[0] <= 8 and b'\x19\x19' in data:
        return False
    return True


def main() -> int:
    clusters: dict[str, list] = collections.defaultdict(list)
    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        if not is_unmatched(d):
            continue
        magic = d[:4].hex() if len(d) >= 4 else d.hex()
        clusters[magic].append((p, d))

    sorted_clusters = sorted(clusters.items(), key=lambda kv: -len(kv[1]))

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(f'unmatched .bin clusters: {len(clusters)} distinct magics, {sum(len(v) for v in clusters.values())} files\n\n')
        for magic, items in sorted_clusters:
            sizes = [len(d) for _, d in items]
            f.write(f'== magic {magic}  count={len(items)}  size: min={min(sizes)} max={max(sizes)} median={int(statistics.median(sizes))}\n')
            # show first 3 files: name + 32-byte hexdump
            for p, d in items[:3]:
                hd = ' '.join(f'{b:02x}' for b in d[:32])
                ascii_repr = ''.join(chr(b) if 0x20 <= b < 0x7f else '.' for b in d[:32])
                f.write(f'   {p.name}  ({len(d)}B)\n')
                f.write(f'     hex:   {hd}\n')
                f.write(f'     ascii: {ascii_repr}\n')
            # interpret first 4 bytes as LE uint32 (likely entry count)
            if len(items[0][1]) >= 4:
                u32 = struct.unpack_from('<I', items[0][1], 0)[0]
                f.write(f'   first-uint32-LE: {u32}\n')
            f.write('\n')

    print(f'wrote {OUT}')
    print(open(OUT, encoding='utf-8').read()[:6000])
    return 0


if __name__ == '__main__':
    sys.exit(main())
