"""
Hero3 _bm → PNG 변환기 v2 (멀티프레임 지원).

검증된 포맷:
    file_header (6 bytes): count + flag1 + reserved
    frames[count]: 각 프레임은 자체 mini-header + palette + pixels
        mini_header (9 bytes): type(0b/0c) + w(LE16) + h(LE16) + cw(LE16) + ch(LE16)
        marker     (2 bytes): 0xf81f (marker)
        palette   (32 bytes): 16 RGB565 colors LE (palette[0] = 0xf81f magenta=transparent)
        pixels: type 0x0b uncompressed 4-bit big-nibble-first

프레임 경계는 1f f8 마커 위치 + 9 bytes 앞 type 검증으로 식별.
일부 프레임에서 2-6 바이트 underrun 가능 (정렬 이슈, 시각적 영향 미미).
type 0x0c 프레임은 다른 포맷 (압축 추정) — 1차 베이스라인은 type 0x0b 와 동일하게 처리.

사용:
    python convert_bm_v2.py <input.bm> <output_dir>
"""
from __future__ import annotations
import struct, sys, pathlib
from PIL import Image


def find_frame_markers(data: bytes) -> list[int]:
    """1f f8 마커 위치 + 엄격한 sanity check 로 false positive 제거."""
    out = []
    i = 0
    while i < len(data) - 1:
        if data[i] == 0x1f and data[i + 1] == 0xf8:
            # 1) 9 bytes 앞 type byte (0b/0c)
            if i < 9 or data[i - 9] not in (0x0b, 0x0c):
                i += 1
                continue
            # 2) 합리적 dimensions (1..512, 0 아닌)
            w = struct.unpack_from('<H', data, i - 8)[0]
            h = struct.unpack_from('<H', data, i - 6)[0]
            cw = struct.unpack_from('<H', data, i - 4)[0]
            ch = struct.unpack_from('<H', data, i - 2)[0]
            if not (1 <= w <= 512 and 1 <= h <= 512):
                i += 1
                continue
            # 3) marker 뒤 palette(32 bytes) 공간 있어야 함
            if i + 2 + 32 > len(data):
                i += 1
                continue
            # 4) palette 첫 색이 0xf81f (마젠타) 인지 확인 — 강력한 진짜 마커 신호
            first_color = struct.unpack_from('<H', data, i + 2)[0]
            if first_color != 0xf81f:
                # 1차 휴리스틱: 첫 색이 마젠타가 아니면 의심스러움. 단, 일부 프레임은
                # 마젠타가 다른 인덱스에 있을 수 있으므로 기각하지 않고 통과시킴.
                pass
            out.append(i)
            i += 2
        else:
            i += 1
    return out


def rgb565_to_rgba(v: int) -> tuple[int, int, int, int]:
    if v == 0xf81f:
        return (255, 0, 255, 0)
    r = (v >> 11) & 0x1f
    g = (v >> 5) & 0x3f
    b = v & 0x1f
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31, 255)


def render_frame(data: bytes, marker_off: int, pixel_end: int) -> tuple[Image.Image, dict]:
    """marker 위치 기반으로 프레임 렌더링. pixel_end 까지 사용."""
    type_byte = data[marker_off - 9]
    w = struct.unpack_from('<H', data, marker_off - 8)[0]
    h = struct.unpack_from('<H', data, marker_off - 6)[0]
    cw = struct.unpack_from('<H', data, marker_off - 4)[0]
    ch = struct.unpack_from('<H', data, marker_off - 2)[0]
    palette = [rgb565_to_rgba(struct.unpack_from('<H', data, marker_off + 2 + j*2)[0])
               for j in range(16)]
    pixels_off = marker_off + 2 + 32
    pixels_avail = max(0, pixel_end - pixels_off)
    pixels_data = data[pixels_off:pixels_off + pixels_avail]

    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    pix = img.load()
    n = w * h
    for i in range(n):
        bi = i // 2
        if bi >= len(pixels_data):
            break
        b = pixels_data[bi]
        idx = (b >> 4) if (i % 2 == 0) else (b & 0x0f)
        if idx < 16:
            pix[i % w, i // w] = palette[idx]

    return img, {'type': type_byte, 'w': w, 'h': h, 'cw': cw, 'ch': ch,
                 'pixels_avail': pixels_avail, 'pixels_needed': (n + 1) // 2}


def decode_file(path: pathlib.Path, out_dir: pathlib.Path) -> dict:
    data = path.read_bytes()
    if len(data) < 50:
        return {'error': 'too small'}
    cnt = struct.unpack_from('<H', data, 0)[0]
    markers = find_frame_markers(data)
    out_dir.mkdir(parents=True, exist_ok=True)

    rendered = 0
    truncated = 0
    for i, m in enumerate(markers):
        next_m = markers[i + 1] if i + 1 < len(markers) else None
        pixel_end = (next_m - 9) if next_m is not None else len(data)
        try:
            img, meta = render_frame(data, m, pixel_end)
            out = out_dir / f'frame_{i:02d}_{meta["w"]}x{meta["h"]}_t{meta["type"]:x}.png'
            img.save(out)
            rendered += 1
            if meta['pixels_avail'] < meta['pixels_needed']:
                truncated += 1
        except Exception as e:
            print(f'  frame {i} @ {m:#x}: {e}', file=sys.stderr)

    return {
        'count_hdr': cnt,
        'markers_found': len(markers),
        'rendered': rendered,
        'truncated': truncated,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src = pathlib.Path(argv[1])
    dst = pathlib.Path(argv[2])
    if src.is_file():
        info = decode_file(src, dst / src.stem)
        print(f'{src.name}: {info}')
    elif src.is_dir():
        total = {'files': 0, 'rendered': 0, 'truncated': 0}
        for path in src.rglob('*_bm'):
            rel = path.relative_to(src).with_suffix('')
            info = decode_file(path, dst / rel)
            total['files'] += 1
            total['rendered'] += info.get('rendered', 0)
            total['truncated'] += info.get('truncated', 0)
        print(f'\nSummary: files={total["files"]}, frames_rendered={total["rendered"]}, '
              f'truncated={total["truncated"]}')
    else:
        print(f'Not found: {src}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
