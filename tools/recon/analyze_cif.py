"""
Hero3 _cif animation 분석 도구.

핵심 발견 (h0_cif, 8025 byte):
- 헤더 10 byte: slot_count, category, indices[8]
- 프레임 레코드: 가변 길이, `0a XX YY` 마커로 시작 (XX=type, YY=cell_count?)
- 첫 그룹 8개 (offset 12~339): `0a 02 0b` 헤더, 41 byte fixed stride
- 두번째 그룹 8개 (offset 341~669): `0a 05 ??` 헤더, 41 byte stride
- 셀 (offset 3..38): 4 byte stride, [x_s8, y_s8, bm_ref_u8, flag_u8]

Boss/enemy cif (2026-05-09, FUN_00098ef8 @ 0x98ef8 알고리즘 적용):
- 헤더 (2 + slot_count) byte: slot_count, category, indices[slot_count]
- 본문: 4 byte stride 셀 스트림 (frame 헤더 없음)
- Cell byte 0 분해:
    bit 7      = special flag (abort/extension)
    bits 5..6  = orientation (0/1/2)
    bits 0..4  = cell ref (slot index 또는 5-bit ref)
- Sentinel cell: byte 0 == 0x7f (orient=3 ref=31 인 형태). 디코더가 skip.
- bytes 1..3 = (x_s8, y_s8, extra_u8) 추정. boss/enemy 실제 좌표/플래그 필드는 미확정 (BM 매핑까지 검증되면 확정 가능).

사용:
    python analyze_cif.py [path/to/h0_cif]
    python analyze_cif.py [path/to/e000_cif] --boss
"""
from __future__ import annotations
import sys, pathlib
from collections import Counter


def find_frames(data: bytes, start: int = 10) -> list[int]:
    frames = []
    i = start
    while i < len(data) - 1:
        if data[i] != 0x0a:
            i += 1
            continue
        frames.append(i)
        nxt = i + 41
        if nxt < len(data) and data[nxt] == 0x0a:
            i = nxt
        else:
            j = nxt
            while j < len(data) and data[j] != 0x0a:
                j += 1
            i = j if j < len(data) else len(data)
    return frames


def diff_frames(a: bytes, b: bytes) -> str:
    return ' '.join(f'{(y-x)&0xff:02x}' if x != y else '..' for x, y in zip(a, b))


def s8(b: int) -> int:
    return b - 256 if b >= 128 else b


def parse_cells_4byte(rec: bytes, offset: int = 3, n: int = 9) -> list[dict]:
    cells = []
    for k in range(n):
        o = offset + k * 4
        if o + 4 > len(rec):
            break
        cells.append({
            'idx': k, 'x': s8(rec[o]), 'y': s8(rec[o+1]),
            'ref': rec[o+2], 'flag': rec[o+3]
        })
    return cells


# ----- Boss/enemy cif decoder (FUN_00098ef8 알고리즘) -----

SENTINEL_CELL_BYTE = 0x7f


def decode_cell_byte(cb: int) -> dict:
    """FUN_00098ef8 의 cell byte 분해.

    bit 7     = special flag (특수 셀, decoder 가 별도 처리)
    bits 5..6 = orientation (0/1/2; sentinel 시 3)
    bits 0..4 = ref / cell type (5-bit, 0..31)

    Sentinel cell 은 byte 0 == 0x7f (orient=3, ref=31, special=0).
    """
    return {
        'is_sentinel': cb == SENTINEL_CELL_BYTE,
        'orient': (cb >> 5) & 3,
        'ref': cb & 0x1f,
        'special': (cb & 0x80) != 0,
    }


def parse_boss_header(data: bytes) -> dict:
    """Boss/enemy cif 헤더 파싱. body 시작 offset 도 반환.

    body_offset 은 `2 + slot_count` (indices end). 실제 binary 의 FUN_00098ef8 은
    indices 이후 추가 metadata bytes (h0 = 2B `04 08`, boss0 = 3B `01 09 12`) 를 더 skip 할
    가능성 있음 — 이 metadata 가 anim/frame count 일 것으로 추정. 미확정.
    """
    if len(data) < 2:
        return {'slot_count': 0, 'category': 0, 'indices': [], 'body_offset': 0}
    sc = data[0]
    cat = data[1]
    end = 2 + sc
    indices = list(data[2:end]) if end <= len(data) else []
    return {'slot_count': sc, 'category': cat, 'indices': indices, 'body_offset': end}


def parse_boss_cells(body: bytes, max_cells: int = -1) -> list[dict]:
    """4-byte stride 셀 스트림을 디코딩.

    각 셀 dict: idx, offset, is_sentinel, orient, ref, special, x, y, extra.
    sentinel 도 결과에 포함됨 (이후 단계에서 frame splitter 가 처리).
    body 길이가 4 의 배수가 아니면 trailing 부분은 무시.
    """
    cells = []
    n = len(body) // 4
    if max_cells >= 0:
        n = min(n, max_cells)
    for k in range(n):
        o = k * 4
        cb = body[o]
        c = decode_cell_byte(cb)
        c['idx'] = k
        c['offset'] = o
        c['x'] = s8(body[o + 1])
        c['y'] = s8(body[o + 2])
        c['extra'] = body[o + 3]
        cells.append(c)
    return cells


def split_frames_by_sentinel(cells: list[dict]) -> list[list[dict]]:
    """Sentinel cell 을 frame 경계로 보고 frame 단위로 분할.

    sentinel cell 자체는 frame 에 포함되지 않음. 빈 frame (sentinel 연속) 도 보존하지 않음.
    sentinel 이 0건인 파일 (대부분 enemy) 은 전체를 1 frame 으로 반환.
    """
    frames: list[list[dict]] = []
    current: list[dict] = []
    for c in cells:
        if c['is_sentinel']:
            if current:
                frames.append(current)
                current = []
        else:
            current.append(c)
    if current:
        frames.append(current)
    return frames


def boss_cif_summary(data: bytes) -> dict:
    """단일 boss/enemy cif 의 통계 + frame 분할 요약."""
    h = parse_boss_header(data)
    body = data[h['body_offset']:]
    cells = parse_boss_cells(body)
    sentinels = sum(1 for c in cells if c['is_sentinel'])
    specials = sum(1 for c in cells if c['special'])
    frames = split_frames_by_sentinel(cells)
    frame_lens = [len(f) for f in frames]
    refs = [c['ref'] for c in cells if not c['is_sentinel']]
    from collections import Counter
    return {
        'header': h,
        'body_bytes': len(body),
        'cells_total': len(cells),
        'sentinels': sentinels,
        'specials': specials,
        'frames': len(frames),
        'frame_len_min': min(frame_lens) if frame_lens else 0,
        'frame_len_max': max(frame_lens) if frame_lens else 0,
        'frame_len_avg': (sum(frame_lens) / len(frame_lens)) if frame_lens else 0,
        'top_refs': Counter(refs).most_common(8),
    }


def _print_boss(src: pathlib.Path, data: bytes) -> int:
    s = boss_cif_summary(data)
    h = s['header']
    print(f'file: {src} ({len(data)} bytes)  [boss/enemy mode]')
    print(f'header: slot_count={h["slot_count"]} category={h["category"]} indices={h["indices"]} body_off={h["body_offset"]}')
    print(f'body={s["body_bytes"]}B  cells_total={s["cells_total"]}  sentinels={s["sentinels"]}  specials={s["specials"]}')
    print(f'frames(by sentinel): {s["frames"]}  len min/avg/max = {s["frame_len_min"]}/{s["frame_len_avg"]:.1f}/{s["frame_len_max"]}')
    print(f'top refs: {s["top_refs"]}')
    body = data[h['body_offset']:]
    cells = parse_boss_cells(body, max_cells=12)
    print('first 12 cells:')
    for c in cells:
        tag = 'SENT' if c['is_sentinel'] else ('SPEC' if c['special'] else '    ')
        print(f'  c{c["idx"]:2d}@{c["offset"]:5d} {tag} orient={c["orient"]} ref={c["ref"]:2d}'
              f' x={c["x"]:+4d} y={c["y"]:+4d} extra=0x{c["extra"]:02x}')
    return 0


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith('-')]
    boss_mode = '--boss' in argv
    src = pathlib.Path(args[0] if args else 'work/h3/extracted/hero/h0_cif')
    data = src.read_bytes()
    if boss_mode:
        return _print_boss(src, data)
    print(f'file: {src} ({len(data)} bytes)')
    print(f'header: {data[:10].hex()}')
    frames = find_frames(data)
    print(f'frame count (41-stride heuristic): {len(frames)}')
    print(f'first 16 frame offsets: {frames[:16]}')

    leads = Counter(data[off:off+3].hex() for off in frames)
    print(f'frame leads (top 10): {leads.most_common(10)}')

    if len(frames) >= 8:
        print('\n--- group1 sample (frames 0,2,4,6) ---')
        for i in [0, 2, 4, 6]:
            rec = data[frames[i]:frames[i]+41]
            print(f'  R{i} @{frames[i]}: {rec.hex()}')
        r0 = data[frames[0]:frames[0]+41]
        r2 = data[frames[2]:frames[2]+41]
        print(f'  R0->R2 deltas: {diff_frames(r0, r2)}')
        print('\n  Cells of R0 (4-byte stride, offset 3, n=9):')
        for c in parse_cells_4byte(r0):
            print(f'    cell {c["idx"]}: x={c["x"]:+4d} y={c["y"]:+4d} ref=0x{c["ref"]:02x} flag=0x{c["flag"]:02x}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
