"""client.bin* 의 PC-relative 32-bit literal 풀에서 known string 주소를 찾아 xref 식별.

Thumb-2 LDR rN, [pc, #imm] : 4-byte aligned (pc = (cur+4) & ~3), imm 0..1020 (10-bit).
Thumb-2 32-bit LDR (T4)   : range ±4095.
일단 모든 32-bit 워드를 스캔해 known string offsets 와 매칭.

base address 가정: 0x00000000 (file offset = memory offset). 잘못되면 base 후보를 바꿔가며 재시도.

TARGETS 와 code_end 는 게임별 string_offsets.json 에서 자동 로드.
사전준비: HERO_GAME=<id> python tools/recon/extract_strings.py --json work/<id>/converted/string_offsets.json --quiet
"""
from __future__ import annotations
import struct, pathlib

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402
from recon._targets import load_targets  # noqa: E402

_g = select()
BIN = _g.binary_path
assert BIN is not None, f'{_g.id} has no native binary'


def main():
    # priority_only=True: frameBuf/Font/NULL 같은 핵심 라벨만 (xref 보고 noise 줄임)
    TARGETS, code_end_auto = load_targets(priority_only=True)
    if not TARGETS:
        # 폴백: priority 라벨이 없으면 전체 path-like
        TARGETS, code_end_auto = load_targets()
    data = BIN.read_bytes()
    print(f'[{_g.id}] Loaded {BIN.name}: {len(data)} bytes (0x{len(data):x})')
    print(f'[{_g.id}] {len(TARGETS)} TARGETS loaded (priority labels)')

    # 코드 vs 데이터 경계: extract_strings.py 가 추정한 첫 path-like offset (4KB align)
    code_end = code_end_auto or (len(data) // 2)
    print(f'\nScanning 32-bit words in [0x0, 0x{code_end:x}) for string xrefs...')

    found = {addr: [] for addr in TARGETS}
    for off in range(0, min(code_end, len(data) - 4)):
        if off & 3:
            continue  # 4-byte aligned literal pool
        v = struct.unpack_from('<I', data, off)[0]
        if v in TARGETS:
            found[v].append(off)

    print(f'\nLiteral pool xrefs found:')
    for addr, label in TARGETS.items():
        refs = found[addr]
        print(f'\n  {addr:#08x} {label!r}')
        if not refs:
            print(f'    (no refs found at base=0)')
        else:
            for r in refs[:10]:
                print(f'    literal pool entry @ {r:#08x}')

    # 이제 가장 흥미로운 것: 'frameBuf is NULL' 의 xref 위치 주변에서 함수 시작 찾기
    framebuf_addr = next((a for a, lbl in TARGETS.items() if 'framebuf' in lbl.lower()), None)
    framebuf_refs = found.get(framebuf_addr, []) if framebuf_addr else []
    if framebuf_refs:
        print(f'\n=== {TARGETS[framebuf_addr]!r} literal pool entries → tracing back to LDR instructions ===')
        # LDR rN, [pc, #imm] 인코딩: 0x4800-0x4FFF (T1 16-bit)
        # 또는 LDR.W rN, [pc, #imm] (T4 32-bit)
        for lit_off in framebuf_refs:
            # 이 literal pool 항목을 참조하는 LDR 명령은 lit_off 보다 작은 PC를 가져야 함
            # Thumb T1 LDR pc-rel: pc = (instr_addr + 4) & ~3, target = pc + imm*4
            # 즉 instr_addr = lit_off - 4 - imm*4 (and align)
            # imm 범위 0..255 (8-bit) → instr_addr 범위 lit_off-1024..lit_off-4
            print(f'\n  Literal @ {lit_off:#08x} — searching nearby Thumb LDR pc-rel instructions...')
            search_start = max(0, lit_off - 1024)
            search_end = lit_off
            for pc_addr in range(search_start, search_end, 2):
                instr = struct.unpack_from('<H', data, pc_addr)[0]
                # T1 LDR Rt, [PC, #imm8*4]  =  01001 ttt iiiiiiii  (0x4800..0x4FFF)
                if (instr & 0xf800) == 0x4800:
                    rt = (instr >> 8) & 0x07
                    imm8 = instr & 0xff
                    pc = (pc_addr + 4) & ~3
                    target = pc + imm8 * 4
                    if target == lit_off:
                        print(f'    {pc_addr:#08x}: LDR R{rt}, [PC, #{imm8*4}] -> {target:#08x}')


if __name__ == '__main__':
    main()
