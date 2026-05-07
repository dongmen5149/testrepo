"""
Hero3 _mp → JSON tilemap.

확정된 포맷:
    uint8 version              // 0x02 또는 0x03
    bytes meta[hdr_size-1]     // version 0x02: 4바이트, 0x03: 5바이트 추가 (의미 미확정)
    uint8 name_length
    char  name[name_length]    // ASCII (예: "NEOSOLTIA", "SMALL_FACTORY_4")
    uint8 nul                  // 0x00
    uint8 width
    uint8 height
    uint8 palette_count
    uint8 meta4
    uint8 palette[palette_count]
    bytes layer_0[W*H]         // terrain
    bytes layer_1[W*H]         // objects/collision
    bytes extras[]             // 데코레이션/이벤트 마커 (2026-05-07 부분 해독)

extras 포맷 (97% 맵, 2026-05-07 해독):
    헤더 변형 3가지:
      A) [count]                   1 byte         h1_s6
      B) [flag] [count]            2 byte         h2_s6  (flag = 0x80 또는 0xc0)
      C) [flag1] [flag2] [count1]  3 byte + ...   multi   (두 섹션, 각 [count] 헤더)
    각 레코드 6 byte:
      type_u8 (0x00/0x80, facing/state 추정)
      id_u8   (오브젝트 종류; 0x3e/0x3f 데코 우세)
      x_u16_LE (픽셀, /16 = tile)
      y_u16_LE (픽셀, /16 = tile)
    NPC 위치는 extras 가 아니라 _scn opcode 스트림에 있는 것으로 추정 (§4.4 미해독).

사용:
    python convert_mp.py <input.mp> <output.json>
"""
from __future__ import annotations
import sys, json, pathlib


def _parse_records(ex: bytes, W: int, H: int, hdr_off: int, count: int) -> list[dict]:
    recs = []
    for i in range(count):
        off = hdr_off + i * 6
        if off + 6 > len(ex):
            break
        t = ex[off]
        rid = ex[off + 1]
        x = ex[off + 2] | (ex[off + 3] << 8)
        y = ex[off + 4] | (ex[off + 5] << 8)
        sx = x if x < 0x8000 else x - 0x10000
        sy = y if y < 0x8000 else y - 0x10000
        tx, ty = sx // 16, sy // 16
        valid = (-1 <= tx <= W and -1 <= ty <= H)
        recs.append({
            'off': off, 'type': t, 'id': rid,
            'px': [x, y], 'tile': [tx, ty], 'valid': valid,
        })
    return recs


def parse_extras(ex: bytes, W: int, H: int) -> dict:
    """
    Auto-detect header variant and parse 6-byte records.
    Returns {'strategy': str, 'records': [...], 'leftover': int}.
    """
    if len(ex) < 2:
        return {'strategy': 'empty', 'records': [], 'leftover': len(ex)}

    # h2_s6 strict: byte0=flag, byte1=count
    cnt = ex[1]
    if cnt > 0 and 2 + cnt * 6 <= len(ex):
        recs = _parse_records(ex, W, H, 2, cnt)
        if recs and all(r['valid'] for r in recs):
            return {'strategy': 'h2_s6', 'records': recs, 'leftover': len(ex) - (2 + cnt * 6)}

    # h1_s6 strict: byte0=count
    cnt = ex[0]
    if cnt > 0 and 1 + cnt * 6 <= len(ex):
        recs = _parse_records(ex, W, H, 1, cnt)
        if recs and all(r['valid'] for r in recs):
            return {'strategy': 'h1_s6', 'records': recs, 'leftover': len(ex) - (1 + cnt * 6)}

    # multi-section: byte0=flag1, byte1=flag2 (both 0x80/0xc0), byte2=count1
    if len(ex) >= 4 and ex[0] in (0x80, 0xc0) and ex[1] in (0x80, 0xc0):
        s1c = ex[2]
        s1_end = 3 + s1c * 6
        if s1c > 0 and s1_end <= len(ex):
            s1 = _parse_records(ex, W, H, 3, s1c)
            if s1 and all(r['valid'] for r in s1):
                if s1_end < len(ex):
                    s2c = ex[s1_end]
                    s2_end = s1_end + 1 + s2c * 6
                    if s2_end <= len(ex):
                        s2 = _parse_records(ex, W, H, s1_end + 1, s2c)
                        if s2 and all(r['valid'] for r in s2):
                            return {'strategy': 'multi', 'records': s1 + s2, 'leftover': len(ex) - s2_end}
                    return {'strategy': 'multi_s1only', 'records': s1, 'leftover': len(ex) - s1_end}
                return {'strategy': 'multi', 'records': s1, 'leftover': 0}

    return {'strategy': 'unparsed', 'records': [], 'leftover': len(ex)}


def parse_mp(data: bytes) -> dict:
    if len(data) < 10:
        raise ValueError(f'too small: {len(data)} bytes')
    version = data[0]
    if version == 0x02:
        hdr_size = 5
    elif version == 0x03:
        hdr_size = 6
    else:
        raise ValueError(f'unknown version {version:#x}')

    name_len = data[hdr_size]
    name_start = hdr_size + 1
    name_end = name_start + name_len
    if name_end >= len(data):
        raise ValueError('name overflow')
    name = data[name_start:name_end].decode('ascii', errors='replace')
    if data[name_end] != 0:
        raise ValueError(f'missing NUL after name @ {name_end}')

    pos = name_end + 1
    width = data[pos]; pos += 1
    height = data[pos]; pos += 1
    pal_count = data[pos]; pos += 1
    meta4 = data[pos]; pos += 1
    palette = list(data[pos:pos + pal_count])
    pos += pal_count

    grid_start = pos
    cell_count = width * height
    layer0 = list(data[grid_start:grid_start + cell_count])
    layer1 = list(data[grid_start + cell_count:grid_start + 2 * cell_count])
    extras_start = grid_start + 2 * cell_count
    extras = data[extras_start:] if extras_start < len(data) else b''

    parsed = parse_extras(extras, width, height)

    return {
        'version': version,
        'meta_header_hex': data[1:hdr_size].hex(),
        'name': name,
        'width': width,
        'height': height,
        'palette_count': pal_count,
        'meta4': meta4,
        'palette': palette,
        'layer_0': layer0,
        'layer_1': layer1,
        'extras_size': len(extras),
        'extras_strategy': parsed['strategy'],
        'extras_leftover': parsed['leftover'],
        'extras_records': parsed['records'],
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    info = parse_mp(src.read_bytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(info, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({info["name"]} {info["width"]}x{info["height"]}, '
          f'{info["extras_strategy"]}, {len(info["extras_records"])} records)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
