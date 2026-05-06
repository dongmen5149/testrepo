"""
잔여 .bin 1,138개를 size + 내부 마커로 재분류.

분류 카테고리:
  TINY_META   : 50B 이하, signed int16 LE 패턴이 다수 → 애니메이션 hitbox/offset
  SMALL_SCRIPT: 50–500B, `19 19` 마커 포함 → 애니메이션 정의/스크립트
  LARGE_ANIM  : >500B, `19 19` 마커 다수 포함 → 큰 애니메이션 시퀀스
  LARGE_RAW   : >1KB 인데 19 19 마커 없음 → 미상 raw 데이터
"""
from __future__ import annotations
import sys, struct, pathlib, collections, statistics

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'residual_categories.txt'


def is_sprite(d: bytes) -> bool:
    if len(d) < 14 or d[8] not in (0x04, 0x08, 0x14, 0x18): return False
    cnt = struct.unpack_from('<I', d, 0)[0]
    if cnt == 0 or cnt > 64: return False
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


def classify(d: bytes) -> str:
    n = len(d)
    marker_count = 0
    i = 0
    while i < n - 1:
        if d[i] == 0x19 and d[i+1] == 0x19:
            marker_count += 1
            i += 2
        else:
            i += 1
    if n <= 50:
        return 'TINY_META'
    if marker_count >= 1 and n <= 500:
        return 'SMALL_SCRIPT'
    if marker_count >= 2 and n > 500:
        return 'LARGE_ANIM'
    if n > 1024 and marker_count == 0:
        return 'LARGE_RAW'
    if marker_count >= 1:
        return 'MID_SCRIPT'
    return 'OTHER'


def main() -> int:
    cat_files: dict[str, list] = collections.defaultdict(list)
    cat_bytes: dict[str, int] = collections.defaultdict(int)
    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        if d[:4] == b'OggS' or d[:4] == b'MMMD': continue
        if is_sprite(d): continue
        if is_pa(d): continue
        c = classify(d)
        cat_files[c].append((p, d))
        cat_bytes[c] += len(d)

    with open(OUT, 'w', encoding='utf-8') as f:
        total_files = sum(len(v) for v in cat_files.values())
        total_bytes = sum(cat_bytes.values())
        f.write(f'residual: {total_files} files / {total_bytes:,} bytes\n\n')
        f.write(f'{"category":15s} {"files":>8s}  {"bytes":>14s}  {"pct_files":>10s}  {"pct_bytes":>10s}\n')
        for c in sorted(cat_files, key=lambda k: -len(cat_files[k])):
            n = len(cat_files[c])
            b = cat_bytes[c]
            f.write(f'{c:15s} {n:8d}  {b:14,}  {100*n/total_files:9.1f}%  {100*b/total_bytes:9.1f}%\n')
        f.write('\n')

        for c in sorted(cat_files, key=lambda k: -len(cat_files[k])):
            items = cat_files[c]
            sizes = [len(d) for _, d in items]
            f.write(f'\n## {c}  (n={len(items)} sz: min={min(sizes)} med={int(statistics.median(sizes))} max={max(sizes)})\n')
            for p, d in items[:4]:
                hd = ' '.join(f'{b:02x}' for b in d[:32])
                f.write(f'   {p.name} ({len(d)}B)  hex32: {hd}\n')

    print(open(OUT, encoding='utf-8').read()[:4000])
    return 0


if __name__ == '__main__':
    sys.exit(main())
