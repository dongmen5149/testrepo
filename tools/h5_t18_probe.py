"""
type=0x18 frame 인코딩 분석.

가설:
  H1: RGB565 raw  (payload = w*h*2)
  H2: u16 palcnt + palette + 8-bit indexed
  H3: variant 가 RLE 토큰 / 압축 플래그
"""
from __future__ import annotations
import sys, struct, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'work' / 'h5' / 'vfs_entries'


def walk_frames(d: bytes):
    cnt = struct.unpack_from('<I', d, 0)[0]
    pos = 4
    for i in range(cnt):
        if pos + 4 > len(d): return
        ln = struct.unpack_from('<I', d, pos)[0]
        if pos + 4 + ln > len(d): return
        yield i, d[pos+4:pos+4+ln]
        pos += 4 + ln


def main() -> int:
    t18_frames = []
    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        if len(d) < 14: continue
        if d[8] not in (0x14, 0x18): continue
        cnt = struct.unpack_from('<I', d, 0)[0]
        if cnt == 0 or cnt > 64: continue
        for i, payload in walk_frames(d):
            if len(payload) < 6: continue
            if payload[0] == 0x18:
                w = struct.unpack_from('<H', payload, 2)[0]
                h = struct.unpack_from('<H', payload, 4)[0]
                t18_frames.append((p.name, i, payload[1], w, h, len(payload), payload))

    print(f'type=0x18 frames: {len(t18_frames)}')
    if not t18_frames:
        return 0

    # bpp distribution
    bpp = collections.Counter()
    var_bpp = collections.Counter()
    for name, idx, var, w, h, pl, pay in t18_frames:
        if w * h == 0: continue
        b = (pl - 6) * 8 / (w * h)
        bpp[round(b)] += 1
        var_bpp[(var, round(b))] += 1

    print('bpp dist (rounded to int):')
    for k, v in sorted(bpp.items()):
        print(f'  {k:3d} bpp: {v}')

    # exact match for RGB565 raw: payload-6 == w*h*2 ?
    rgb565_exact = sum(1 for n,i,v,w,h,pl,_ in t18_frames if pl - 6 == w*h*2)
    print(f'\npayload-6 == w*h*2 (RGB565 raw exact): {rgb565_exact}/{len(t18_frames)}')

    # samples — first 5 frames, hexdump of first 32 bytes
    print('\nsamples (first 32 bytes of payload):')
    for name, idx, var, w, h, pl, pay in t18_frames[:8]:
        hd = ' '.join(f'{b:02x}' for b in pay[:32])
        body_minus_hdr = pl - 6
        ratio = body_minus_hdr / (w*h) if w*h else 0
        print(f'  {name} f{idx} var=0x{var:02x} {w}x{h} pl={pl} body={body_minus_hdr} ratio={ratio:.2f}')
        print(f'    hex: {hd}')

    # variant byte is the tricky bit — check if (variant) corresponds to palette size
    # also: maybe variant is high byte and there's a u16 at offset 1?
    print('\nvariant byte distribution (top 20):')
    var_dist = collections.Counter(v for _,_,v,_,_,_,_ in t18_frames)
    for k, v in var_dist.most_common(20):
        print(f'  0x{k:02x}: {v}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
