"""
Hero5 sprite (.bin, sprite-like) → PNG 디코더.

확정된 포맷:
  outer:
    u32 frame_count
    per frame: u32 frame_length + frame_payload[frame_length]

  frame payload (type=0x14, variant ∈ 0x02..0x10 = 팔레트 색 개수):
    u8  type        // 0x14
    u8  palcnt      // 팔레트 엔트리 수 (RGB565 LE)
    u16 width  LE
    u16 height LE
    bytes palette[palcnt * 2]              // RGB565 LE
    bytes pixels[ ceil(w/2) * h ]          // 4-bit packed, high nibble first
                                           // 행 단위 패딩 (행마다 ceil(w/2) bytes)
                                           // 인덱스 0 = 투명

  특수 케이스:
    type=0x14 var=0x01 w=h=1 frame_len=9  → 더미/터미네이터 프레임 (스킵)
    type=0x18 var=*                        → 별도 인코딩 (미해독, 스킵)

검증:
  01252_ed3ad1c9.bin frame[0]: w=16 h=19 var=0x0f → palette 30B + pixels 152B = 182B ✓
  00181_c0167aba.bin frame[0]: w=65 h=22 var=0x0b → palette 22B + pixels 726B = 748B ✓

사용:
    python convert_h5_sprite.py <input.bin> <output_dir>
"""
from __future__ import annotations
import sys, struct, pathlib
from PIL import Image


def rgb565_to_rgba(v: int, transparent: bool = False) -> tuple[int, int, int, int]:
    if transparent:
        return (255, 0, 255, 0)
    r = (v >> 11) & 0x1f
    g = (v >> 5) & 0x3f
    b = v & 0x1f
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31, 255)


def decode_frame(payload: bytes) -> tuple[Image.Image | None, dict]:
    if len(payload) < 6:
        return None, {'reason': 'short header'}
    t = payload[0]
    var = payload[1]
    w = struct.unpack_from('<H', payload, 2)[0]
    h = struct.unpack_from('<H', payload, 4)[0]
    info = {'type': t, 'variant': var, 'w': w, 'h': h}

    # 더미 프레임
    if t == 0x14 and var == 0x01 and w == 1 and h == 1:
        info['reason'] = 'dummy 1x1 stub'
        return None, info
    if t != 0x14:
        info['reason'] = f'unsupported type 0x{t:02x}'
        return None, info
    if w == 0 or h == 0:
        info['reason'] = 'zero dim'
        return None, info

    palcnt = var
    pal_bytes = palcnt * 2
    row_bytes = (w + 1) // 2
    need = pal_bytes + row_bytes * h
    if len(payload) < 6 + need:
        info['reason'] = f'payload too short: need {need} got {len(payload)-6}'
        return None, info

    palette = []
    for i in range(palcnt):
        v = struct.unpack_from('<H', payload, 6 + i * 2)[0]
        palette.append(rgb565_to_rgba(v, transparent=(i == 0)))

    pix_off = 6 + pal_bytes
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        row_off = pix_off + y * row_bytes
        for x in range(w):
            b = payload[row_off + (x >> 1)]
            idx = (b >> 4) if (x & 1) == 0 else (b & 0xf)
            if idx < palcnt:
                px[x, y] = palette[idx]
            # else leave transparent
    info['palcnt'] = palcnt
    return img, info


def walk_frames(d: bytes):
    cnt = struct.unpack_from('<I', d, 0)[0]
    pos = 4
    for i in range(cnt):
        if pos + 4 > len(d): return
        ln = struct.unpack_from('<I', d, pos)[0]
        if pos + 4 + ln > len(d): return
        yield i, d[pos+4:pos+4+ln]
        pos += 4 + ln


def decode_file(path: pathlib.Path, out_dir: pathlib.Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    d = path.read_bytes()
    stats = {'frames': 0, 'rendered': 0, 'skipped': 0, 'errors': []}
    for i, payload in walk_frames(d):
        stats['frames'] += 1
        try:
            img, info = decode_frame(payload)
            if img is None:
                stats['skipped'] += 1
                continue
            out = out_dir / f'frame_{i:02d}_{info["w"]}x{info["h"]}_pal{info["palcnt"]}.png'
            img.save(out)
            stats['rendered'] += 1
        except Exception as e:
            stats['errors'].append(f'frame {i}: {e}')
    return stats


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src = pathlib.Path(argv[1])
    dst = pathlib.Path(argv[2])
    stats = decode_file(src, dst)
    print(f'  {src.name} → {dst}: rendered={stats["rendered"]} skipped={stats["skipped"]} errors={len(stats["errors"])}')
    for e in stats['errors'][:5]:
        print(f'    ! {e}')
    return 0 if not stats['errors'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
