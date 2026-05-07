"""
Hero5 .scn 본문 (Interpreter bytecode) 디스어셈블러.

근거: `Interpreter::doScript`, `Interpreter::doEvent`, `Interpreter::open`,
`Interpreter::Strings::init`, `Interpreter::Scripts::init`
(work/h5/analysis/interpreter_core.c 디컴파일).

구조:
  [0..10]   : 11-byte 헤더 (convert_h5_scn.py 가 파싱한 그대로)
  [11..]    : Strings table + Scripts table + main event stream

스트림 포맷 (`Token::getNextByte` 가 1바이트씩 읽음):
  - 일반 opcode (signed byte >= 0): index → Scripts table 의 sub-token
  - 0xFF (signed -1): escape — 다음 바이트가 argCount, 이어서 argCount 개의
    sub-event 길이가 나오고 각각 재귀 처리 (doEvent)
  - doScript 의 경우: 0xFF + stringID + argCount + (stringID, argSize)×argCount

이 디스어셈블러는 표면적 구조만 dump 한다 (opcode → 의미 매핑은 EventProc
서브클래스 vtable 추가 분석 필요).

산출:
  work/h5/analysis/scn_disasm/<index>_<name>.txt — 파일별 opcode dump
  work/h5/analysis/scn_disasm_summary.txt
"""
from __future__ import annotations
import pathlib, csv, collections

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
NAMES = ROOT / 'work' / 'h5' / 'analysis' / 'asset_names.tsv'
OUT_DIR = ROOT / 'work' / 'h5' / 'analysis' / 'scn_disasm'
OUT_SUM = ROOT / 'work' / 'h5' / 'analysis' / 'scn_disasm_summary.txt'


def disasm_body(body: bytes) -> tuple[list[tuple], dict]:
    """Return (events, stats)."""
    events = []
    pos = 0
    op_count = collections.Counter()
    arg_count_dist = collections.Counter()
    while pos < len(body):
        op = body[pos]; pos += 1
        op_count[op] += 1
        if op == 0xFF:
            # escape — used by doEvent for compound ops
            if pos >= len(body): break
            argc = body[pos]; pos += 1
            if argc > 0x13:
                # doEvent treats >0x13 as terminator-like
                events.append(('END', op, argc))
                break
            arg_sizes = []
            for _ in range(argc):
                if pos >= len(body): break
                arg_sizes.append(body[pos]); pos += 1
            # then argc sub-events of given sizes
            sub = []
            for sz in arg_sizes:
                end = min(pos + sz, len(body))
                sub.append(body[pos:end])
                pos = end
            events.append(('ESC', argc, arg_sizes, sub))
            arg_count_dist[argc] += 1
        else:
            events.append(('OP', op))
    stats = {
        'op_dist': op_count,
        'arg_count_dist': arg_count_dist,
        'event_count': len(events),
    }
    return events, stats


def fmt_event(e) -> str:
    if e[0] == 'OP':
        return f'OP   0x{e[1]:02x}'
    if e[0] == 'END':
        return f'END  esc=0xff arg=0x{e[2]:02x}'
    if e[0] == 'ESC':
        argc = e[1]; sizes = e[2]; subs = e[3]
        s = f'ESC  argc={argc} sizes=[{",".join(str(x) for x in sizes)}]'
        for i, sub in enumerate(subs):
            s += f'\n      sub{i}({len(sub)}B): {sub.hex()}'
        return s
    return repr(e)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scn_entries = []
    with open(NAMES, encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter='\t'):
            if row['recovered_name'].endswith('.scn'):
                scn_entries.append(row)

    total_op_dist = collections.Counter()
    total_argc_dist = collections.Counter()
    files_done = 0
    body_size_dist = collections.Counter()

    for e in scn_entries:
        idx = int(e['index']); h = int(e['hash'], 16)
        p = ENTRIES / f'{idx:05d}_{h:08x}.bin'
        if not p.exists(): continue
        d = p.read_bytes()
        body = d[11:]
        body_size_dist[len(body)//100*100] += 1
        events, stats = disasm_body(body)
        total_op_dist.update(stats['op_dist'])
        total_argc_dist.update(stats['arg_count_dist'])
        files_done += 1

        # write per-file disasm
        safe_name = e['recovered_name'].replace('/', '_').replace('\\', '_')
        out_p = OUT_DIR / f'{idx:05d}_{safe_name}.txt'
        with open(out_p, 'w', encoding='utf-8') as out:
            out.write(f'# {e["recovered_name"]}  size={d}B  body={len(body)}B\n')
            out.write(f'# header_hex: {d[:11].hex()}\n')
            out.write(f'# events={len(events)}\n\n')
            for ev in events[:80]:  # cap for readability
                out.write(fmt_event(ev) + '\n')

    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write(f'.scn files disassembled: {files_done}\n\n')
        f.write(f'top-level opcode distribution (top 40):\n')
        for op, c in total_op_dist.most_common(40):
            f.write(f'  0x{op:02x}  ×{c}\n')
        f.write(f'\nESC arg-count distribution:\n')
        for argc, c in total_argc_dist.most_common():
            f.write(f'  argc={argc:3d}  ×{c}\n')

    print(f'disassembled {files_done}/{len(scn_entries)} .scn files')
    print(f'unique top-level opcodes: {len(total_op_dist)}')
    print(f'top 10 opcodes:')
    for op, c in total_op_dist.most_common(10):
        print(f'  0x{op:02x}  ×{c}')
    print(f'\nESC argc distribution: {dict(total_argc_dist.most_common(10))}')
    print(f'\nwrote per-file disasm to {OUT_DIR}/')
    print(f'wrote summary to {OUT_SUM}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
