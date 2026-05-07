"""
Hero3 _cif animation 분석 도구 (2026-05-07 갱신).

핵심 발견 (h0_cif, 8025 byte):
- 헤더 10 byte: slot_count, category, indices[8]
- 프레임 레코드: 가변 길이, `0a XX YY` 마커로 시작 (XX=type, YY=cell_count?)
- 첫 그룹 8개 (offset 12~339): `0a 02 0b` 헤더, 41 byte fixed stride
- 두번째 그룹 8개 (offset 341~669): `0a 05 ??` 헤더, 41 byte stride
- 그룹 사이 1 byte separator (offset 340 = `08` = 다음 그룹 frame count 추정)
- 전체 113 frame 추출 (변동 길이 그룹 포함)

Cell layout 가설 (group1, `0a 02 0b` 레코드, 41 byte):
- 헤더 3 byte: [duration=0x0a, type=0x02, count=0x0b]
- 셀 9개 × 4 byte = 36 byte (offset 3..38) — 각 셀 [x_s8, y_s8, bm_ref_u8, flag_u8]
- 트레일러 2 byte (offset 39..40): 미해독
- y-bobbing 검증: R0→R2, R4→R6 비교 시 각 4-byte 셀의 offset 1 (y) 만 ±1 변화
- cell 2 (offset 11..14) 는 bobbing 없음 → 그림자 셀 추정

미해결:
- count(0x0b=11) vs 실측 9 cells 불일치 — count 의미 재해석 필요
- 트레일러 2 byte 정체
- 셀 ref → BM 파일 매핑 (indices=[1,2,3,10,17,19,16,8] 와 연결 안 됨)
- group2 (`0a 05 ??`) 는 cell 0/1 swap 패턴 — 다른 액션/방향

사용:
    python analyze_cif.py [path/to/h0_cif]
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


def main(argv: list[str]) -> int:
    src = pathlib.Path(argv[1] if len(argv) > 1 else 'work/extracted/hero/h0_cif')
    data = src.read_bytes()
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
