"""
Hero5 sprite-like .bin 의 outer 구조 검증.

가설들:
  (A) u32 count + u32 total_length + flat data of total_length bytes
  (B) u32 count + per_frame[count] = (u32 length + payload[length])
  (C) u32 count + u32 first_frame_length + first_frame + ...

각 가설을 1번 후보(magic 07000000)에 적용해서 일관성 확인.
"""
from __future__ import annotations
import sys, struct, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'work' / 'h5' / 'vfs_entries'

# Sprite-like clusters — magic = LE uint32 count, count is small (1..32), 9th byte = 0x14.
def is_sprite_like(d: bytes) -> bool:
    if len(d) < 14:
        return False
    if d[8] != 0x14:
        return False
    cnt = struct.unpack_from('<I', d, 0)[0]
    if cnt == 0 or cnt > 64:
        return False
    return True


def parse_hyp_b(d: bytes) -> dict:
    """가설 B: u32 count + per_frame (u32 length + payload[length])."""
    cnt = struct.unpack_from('<I', d, 0)[0]
    pos = 4
    frames = []
    for i in range(cnt):
        if pos + 4 > len(d):
            return {'ok': False, 'why': f'frame {i} length header overflow at {pos}', 'frames': frames}
        ln = struct.unpack_from('<I', d, pos)[0]
        if pos + 4 + ln > len(d):
            return {'ok': False, 'why': f'frame {i} payload overflow: ln={ln} pos={pos}', 'frames': frames}
        # peek inner header
        hdr = d[pos+4:pos+10] if ln >= 6 else b''
        frames.append({
            'idx': i, 'pos': pos, 'len': ln,
            'magic9': f'{hdr[0]:02x}' if hdr else '',
            'variant': f'{hdr[1]:02x}' if len(hdr) >= 2 else '',
            'w': struct.unpack_from('<H', hdr, 2)[0] if len(hdr) >= 4 else 0,
            'h': struct.unpack_from('<H', hdr, 4)[0] if len(hdr) >= 6 else 0,
        })
        pos += 4 + ln
    return {'ok': pos == len(d), 'consumed': pos, 'total': len(d),
            'remaining': len(d) - pos, 'frames': frames}


def main() -> int:
    # Sample 5 sprite-like clusters
    target_magics = ['07000000', '0d000000', '04000000', '11000000', '0c000000']
    by_magic: dict[str, list[pathlib.Path]] = collections.defaultdict(list)
    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        if is_sprite_like(d):
            by_magic[d[:4].hex()].append(p)

    for mg in target_magics:
        files = by_magic.get(mg, [])
        if not files:
            print(f'magic {mg}: no files'); continue
        print(f'\n== magic {mg}  total {len(files)} files')
        ok_n = 0
        for p in files:
            d = p.read_bytes()
            r = parse_hyp_b(d)
            if r['ok']:
                ok_n += 1
        print(f'   hypothesis B (per-frame length-prefix): {ok_n}/{len(files)} consistent')
        # show first 3 in detail
        for p in files[:3]:
            d = p.read_bytes()
            r = parse_hyp_b(d)
            status = 'OK' if r['ok'] else f"FAIL ({r.get('why', 'rem='+str(r.get('remaining')))})"
            print(f"   {p.name} ({len(d)}B) → {status}")
            for fr in r['frames'][:5]:
                print(f"      frame[{fr['idx']}] pos={fr['pos']} len={fr['len']} hdr={fr['magic9']}.{fr['variant']} w={fr['w']} h={fr['h']}")
            if len(r['frames']) > 5:
                print(f"      ... and {len(r['frames'])-5} more frames")
    return 0


if __name__ == '__main__':
    sys.exit(main())
