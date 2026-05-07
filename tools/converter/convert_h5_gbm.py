"""
Hero5 .gbm (map tile/face/obj/fgi) 디코더.

근거: `GbmImage::LoadImageResID @ 0x00095370` (work/h5/analysis/gbm_loader.c).

헤더 (6 bytes):
  u8  format       ; low nibble = bit depth (4 또는 8), high nibble = subtype
  u8  paletteSize  ; 팔레트 엔트리 수
  u16 width  LE
  u16 height LE

페이로드:
  - 8-bit indexed: width × height 바이트 (palette index)
  - 4-bit packed:  ceil(width/2) × height 바이트 (high nibble first)
  - 팔레트:        paletteSize × 2 바이트 (RGB565 LE)

파일 사이즈 = 6 + W×H (or 4-bit packed) + 2×paletteSize.

검증: face_00 (23,957B) = 6 + 119×197 + 2×254 = 6 + 23,443 + 508 = 23,957 ✓

팔레트 위치: pixels 뒤 (검증).

산출:
  work/h5/converted/gbm/<category>/<name>.png
  work/h5/analysis/gbm_summary.txt
"""
from __future__ import annotations
import pathlib, csv, struct, collections
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT_DIR = ROOT / 'work' / 'h5' / 'converted' / 'gbm'
OUT_SUM = ROOT / 'work' / 'h5' / 'analysis' / 'gbm_summary.txt'


def rgb565_to_rgba(p: int) -> tuple[int, int, int, int]:
    r5 = (p >> 11) & 0x1F
    g6 = (p >> 5) & 0x3F
    b5 = p & 0x1F
    return ((r5 * 255 + 15) // 31, (g6 * 255 + 31) // 63,
            (b5 * 255 + 15) // 31, 255)


def decode_gbm(data: bytes):
    if len(data) < 6:
        return None
    fmt, pal_sz = data[0], data[1]
    w, h = struct.unpack_from('<HH', data, 2)
    bit_depth = fmt & 0x0F
    subtype = fmt >> 4
    if bit_depth == 8:
        pixel_bytes = w * h
    elif bit_depth == 4:
        pixel_bytes = ((w + 1) // 2) * h
    else:
        return None
    expected = 6 + pixel_bytes + pal_sz * 2
    if len(data) != expected:
        return None
    pixels = data[6:6 + pixel_bytes]
    palette = data[6 + pixel_bytes:]
    pal_rgba = []
    for i in range(pal_sz):
        v = struct.unpack_from('<H', palette, i*2)[0]
        pal_rgba.append(rgb565_to_rgba(v))
    if pal_rgba:
        pal_rgba[0] = (*pal_rgba[0][:3], 0)  # idx 0 = transparent
    rgba = bytearray(w * h * 4)
    if bit_depth == 8:
        for y in range(h):
            for x in range(w):
                idx = pixels[y*w + x]
                if idx < pal_sz:
                    r, g, b, a = pal_rgba[idx]
                    o = (y*w + x) * 4
                    rgba[o] = r; rgba[o+1] = g; rgba[o+2] = b; rgba[o+3] = a
    else:  # 4-bit
        row_bytes = (w + 1) // 2
        for y in range(h):
            for x in range(w):
                b = pixels[y * row_bytes + x // 2]
                idx = (b >> 4) if (x % 2 == 0) else (b & 0x0F)
                if idx < pal_sz:
                    r, g, bl, a = pal_rgba[idx]
                    o = (y*w + x) * 4
                    rgba[o] = r; rgba[o+1] = g; rgba[o+2] = bl; rgba[o+3] = a
    return {
        'fmt': fmt, 'subtype': subtype, 'bit_depth': bit_depth,
        'pal_sz': pal_sz, 'width': w, 'height': h,
        'rgba': bytes(rgba),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gbm_entries = []
    with open(NAMES, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['recovered_name'].endswith('.gbm'):
                gbm_entries.append(row)

    fmt_dist = collections.Counter()
    bd_dist = collections.Counter()
    sub_dist = collections.Counter()
    decoded = 0
    failed = []

    for e in gbm_entries:
        idx = int(e['index']); h = int(e['hash'], 16)
        p = ENTRIES / f'{idx:05d}_{h:08x}.bin'
        if not p.exists(): continue
        d = p.read_bytes()
        info = decode_gbm(d)
        if info is None:
            failed.append((idx, e['recovered_name'], len(d)))
            continue
        decoded += 1
        fmt_dist[info['fmt']] += 1
        bd_dist[info['bit_depth']] += 1
        sub_dist[info['subtype']] += 1

        if HAS_PIL:
            # save PNG
            cat = pathlib.PurePosixPath(e['recovered_name']).parts
            sub = '/'.join(cat[1:-1]) if len(cat) > 2 else 'misc'
            stem = pathlib.PurePosixPath(e['recovered_name']).stem
            outp = OUT_DIR / sub / f'{stem}.png'
            outp.parent.mkdir(parents=True, exist_ok=True)
            img = Image.frombytes('RGBA', (info['width'], info['height']), info['rgba'])
            img.save(outp)

    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write(f'.gbm files: {len(gbm_entries)}\n')
        f.write(f'decoded:    {decoded} ({100*decoded/max(1,len(gbm_entries)):.1f}%)\n')
        f.write(f'failed:     {len(failed)}\n\n')
        f.write(f'format byte distribution:\n')
        for k, v in fmt_dist.most_common():
            f.write(f'  0x{k:02x}  ×{v}\n')
        f.write(f'\nbit depth distribution:\n')
        for k, v in bd_dist.most_common():
            f.write(f'  {k}-bit  ×{v}\n')
        f.write(f'\nsubtype (high nibble) distribution:\n')
        for k, v in sub_dist.most_common():
            f.write(f'  0x{k:x}  ×{v}\n')
        if failed:
            f.write(f'\nfailed files (first 30):\n')
            for idx, name, sz in failed[:30]:
                f.write(f'  {idx:5}  {name:40}  size={sz}\n')

    print(f'.gbm decoded: {decoded}/{len(gbm_entries)} ({100*decoded/max(1,len(gbm_entries)):.1f}%)')
    print(f'failed: {len(failed)}')
    print(f'format byte distribution: {dict(fmt_dist.most_common(8))}')
    print(f'bit depth: {dict(bd_dist.most_common())}')
    if not HAS_PIL:
        print('(PIL not installed — skipping PNG output)')
    else:
        print(f'PNGs written to {OUT_DIR}/')
    if failed[:5]:
        print(f'first 5 failed: {failed[:5]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
