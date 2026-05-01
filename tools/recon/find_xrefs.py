"""client.bin64000 의 PC-relative 32-bit literal 풀에서 known string 주소를 찾아 xref 식별.

Thumb-2 LDR rN, [pc, #imm] : 4-byte aligned (pc = (cur+4) & ~3), imm 0..1020 (10-bit).
Thumb-2 32-bit LDR (T4)   : range ±4095.
일단 모든 32-bit 워드를 스캔해 known string offsets 와 매칭.

base address 가정: 0x00000000 (file offset = memory offset). 잘못되면 base 후보를 바꿔가며 재시도.
"""
from __future__ import annotations
import struct, pathlib

ROOT = pathlib.Path(__file__).parent.parent.parent
BIN = ROOT / 'work' / 'extracted' / 'client.bin64000'

# 추적할 핵심 문자열 위치 (extract_strings.py 결과 기반)
TARGETS = {
    0x0a61c8: 'frameBuf is NULL',
    0x0a5d94: '/hero/h00000_bm',
    0x0a5d84: '/hero/h0_cif',
    0x0a5db4: '/boss/boss9000_bm',
    0x0a5da4: '/boss/boss0_cif',
    0x0a8c28: '/enemy/e1000_bm',
    0x0aac6c: '/map/map0_mp',
    0x0a7f88: '/font/table',
    0x0a7f64: '[HFontError] Font data not loaded.',
    0x0a6888: 'onEventMessageOkKey()',
    0x0a6a50: 'eventIdx -----:: ',
}


def main():
    data = BIN.read_bytes()
    print(f'Loaded {BIN.name}: {len(data)} bytes (0x{len(data):x})')

    # 코드 vs 데이터 경계 추정: 첫 ASCII 문자열 클러스터 시작 (0xa5d60 부근)
    # 보수적으로 0xa5800 까지를 코드+데이터 영역으로 보고 모든 32-bit 워드 스캔
    code_end = 0x0a5800
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
    framebuf_refs = found.get(0x0a61c8, [])
    if framebuf_refs:
        print(f'\n=== "frameBuf is NULL" literal pool entries → tracing back to LDR instructions ===')
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
