"""
Hero5 sprite-like .bin 일괄 PNG 디코딩.

산출: work/h5/converted/sprites/<file>/frame_NN_*.png
"""
from __future__ import annotations
import sys, struct, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools' / 'converter'))
from convert_h5_sprite import decode_file, decode_frame, walk_frames  # noqa

SRC = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'work' / 'h5' / 'converted' / 'sprites'


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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    total = collections.Counter()
    skip_reasons: collections.Counter = collections.Counter()
    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        if not is_sprite(d): continue
        total['files'] += 1
        s = decode_file(p, OUT / p.stem)
        total['frames'] += s['frames']
        total['rendered'] += s['rendered']
        total['skipped'] += s['skipped']
        total['errors'] += len(s['errors'])
        for i, payload in walk_frames(d):
            img, info = decode_frame(payload)
            if img is None:
                skip_reasons[info.get('reason', '?')] += 1
    print(dict(total))
    print('skip reasons:', skip_reasons.most_common())
    return 0


if __name__ == '__main__':
    sys.exit(main())
