"""Hero4 HDAT/_H_PS000..PS008 (9 캐릭터 클래스 progression) 의 entry layout 추론.

각 파일이 동일 70 byte (PS008 만 69) → 같은 schema 의 다른 값. byte position 별로
9개 파일의 값 분포 / 패턴을 분석하여 field 경계 + 의미 추정.

전제 (Phase A docs/h4/formats/hdat.md):
- 9개 캐릭터 데이터 (Hero3 의 리츠/케이/...와 유사)
- 공통 prefix `06 00 01 02 03 04` → byte 6 (`01`/`02`/`03`/`04`) = 클래스 분류
- 클래스: 1=워리어계, 2=마법계, 3=도적계, 4=궁수계 추정

Output: byte-position table + 추정 field 경계 + JSON.
"""
from __future__ import annotations
import json, pathlib

HDAT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / 'work' / 'h4' / 'extracted' / 'HDAT'
OUT = pathlib.Path(__file__).resolve().parent.parent.parent / 'work' / 'h4' / 'converted' / 'hdat_ps_analysis.json'


def main():
    files = sorted(HDAT_DIR.glob('_H_PS*'))
    if not files:
        print('No _H_PS files found')
        return 1

    data_map = {f.name: f.read_bytes() for f in files}
    max_len = max(len(d) for d in data_map.values())
    n = len(data_map)
    print(f'== Hero4 _H_PS* layout analysis ({n} files, max {max_len} bytes) ==\n')

    # Per-byte 분석: position 별 값 분포
    print(f'{"pos":>4} {"hex":>6} ' + ' '.join(f'{k.replace("_H_PS","PS"):>4}' for k in data_map) + '  notes')
    rows = []
    for pos in range(max_len):
        vals = []
        for fn in sorted(data_map):
            d = data_map[fn]
            vals.append(d[pos] if pos < len(d) else None)

        # 분석: distinct count, monotonic, range
        present = [v for v in vals if v is not None]
        distinct = len(set(present))
        is_const = distinct == 1
        is_seq = present == sorted(present) or present == sorted(present, reverse=True)
        notes = []
        if is_const:
            notes.append(f'CONST=0x{present[0]:02x}')
        else:
            notes.append(f'distinct={distinct}')
        if distinct > 1 and all(v is not None for v in vals):
            if max(vals) - min(vals) <= 4 and distinct <= 4:
                notes.append('small-enum')
            elif max(vals) >= 100:
                notes.append('large-val')
        row = {
            'pos': pos,
            'hex': f'0x{pos:02x}',
            'values': [f'{v:02x}' if v is not None else '--' for v in vals],
            'distinct': distinct,
            'min': min(present) if present else None,
            'max': max(present) if present else None,
            'is_const': is_const,
        }
        rows.append(row)
        vals_disp = ' '.join(f'{v:02x}  ' if v is not None else '--  ' for v in vals)
        print(f'{pos:4d} {pos:#06x} {vals_disp}  {", ".join(notes)}')

    # 추정 field 경계: const run / repeating pattern / class byte
    print('\n== 추정 field 경계 ==')

    # Class byte (offset 6 documented)
    class_vals = [data_map[f][6] for f in sorted(data_map)]
    print(f'  offset 6 (class): {[hex(v) for v in class_vals]}')
    class_distribution = {}
    for v in class_vals:
        class_distribution[v] = class_distribution.get(v, 0) + 1
    print(f'  class distribution: {class_distribution}')

    # Const run 식별
    const_runs = []
    cur_start = None
    for pos in range(max_len):
        if rows[pos]['is_const']:
            if cur_start is None:
                cur_start = pos
        else:
            if cur_start is not None:
                if pos - cur_start >= 2:
                    const_runs.append((cur_start, pos - 1, rows[cur_start]['values'][0]))
                cur_start = None
    if cur_start is not None and max_len - cur_start >= 2:
        const_runs.append((cur_start, max_len - 1, rows[cur_start]['values'][0]))
    print(f'\n  const runs (length >= 2):')
    for s, e, v in const_runs:
        print(f'    [{s:3}..{e:3}] = 0x{v} (len {e-s+1})')

    # 16-bit LE 가능성 — 인접 byte 쌍을 uint16 로 보면 의미있는 값?
    print(f'\n  16-bit LE 후보 (pos i, i+1 → uint16):')
    for i in range(0, max_len - 1, 2):
        u16_vals = []
        for fn in sorted(data_map):
            d = data_map[fn]
            if i + 1 < len(d):
                u16_vals.append(int.from_bytes(d[i:i+2], 'little'))
        if len(set(u16_vals)) >= 3 and all(v < 0x4000 for v in u16_vals):
            vals_disp = ' '.join(f'{v:5}' for v in u16_vals)
            print(f'    pos {i:3}..{i+1:3}: {vals_disp}')

    # JSON 저장
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        'files': list(sorted(data_map)),
        'byte_positions': rows,
        'class_byte_offset': 6,
        'class_distribution': {str(k): v for k, v in class_distribution.items()},
        'const_runs': [{'start': s, 'end': e, 'value': v} for s, e, v in const_runs],
    }, indent=2, ensure_ascii=False))
    print(f'\nWrote analysis to {OUT}')
    return 0


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.exit(main())
