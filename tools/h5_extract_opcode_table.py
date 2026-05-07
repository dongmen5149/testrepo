"""
EventProc::onFunction switch 본문에서 opcode → (Event_*, arg_size) 매핑 추출.

입력: work/h5/analysis/opcode_dispatch.c (Ghidra 디컴파일)
산출: work/h5/analysis/opcode_table.tsv  (opcode, event_name, arg_size)
"""
from __future__ import annotations
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'work' / 'h5' / 'analysis' / 'opcode_dispatch.c'
OUT = ROOT / 'work' / 'h5' / 'analysis' / 'opcode_table.tsv'


def main() -> int:
    text = SRC.read_text(encoding='utf-8')
    # only grab the onFunction body
    m = re.search(r'EventProc::onFunction\b.*?\bswitch\(param_1\)\s*\{(.*?)^}', text, re.DOTALL | re.MULTILINE)
    if not m:
        # fallback: extract from "case 0:" through last "case " up to "default" or end of function
        start = text.find('switch(param_1)')
        if start < 0:
            print('switch not found'); return 1
        body = text[start:]
    else:
        body = m.group(1)

    # parse case blocks
    rows = []
    # match: case N: ... getNextCutom(param_2,&local_XX, SIZE); ... Event_NAME(...)
    case_pat = re.compile(
        r'case\s+(0x[0-9a-fA-F]+|\d+)\s*:(.*?)(?=case\s+(?:0x[0-9a-fA-F]+|\d+)\s*:|^\}|^  \w+\s*=)',
        re.DOTALL | re.MULTILINE
    )
    # simpler: split at 'case N:' boundaries
    case_split = re.split(r'\bcase\s+(0x[0-9a-fA-F]+|\d+)\s*:', body)
    # case_split = [pre, op0, body0, op1, body1, ...]
    for i in range(1, len(case_split), 2):
        op_str = case_split[i]
        block = case_split[i+1] if i+1 < len(case_split) else ''
        op = int(op_str, 0)
        # find getNextCutom(...,N) in block (may not exist — some opcodes have no args)
        size_m = re.search(r'getNextCutom\s*\([^,]+,[^,]+,\s*(\d+)\s*\)', block)
        size = int(size_m.group(1)) if size_m else 0
        # find first Event_X( call
        ev_m = re.search(r'\b(Event_\w+)\s*\(', block)
        ev_name = ev_m.group(1) if ev_m else '?'
        rows.append((op, ev_name, size))

    rows.sort()
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('opcode\tevent_name\targ_size\n')
        for op, ev, sz in rows:
            f.write(f'{op}\t{ev}\t{sz}\n')

    print(f'extracted {len(rows)} opcode mappings -> {OUT}')
    print(f'\nopcode → event (first 30):')
    for op, ev, sz in rows[:30]:
        print(f'  0x{op:02x}  {ev}({sz}B)')
    print(f'\nopcode range: 0x{rows[0][0]:02x} .. 0x{rows[-1][0]:02x}')
    print(f'unique events: {len(set(r[1] for r in rows))}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
