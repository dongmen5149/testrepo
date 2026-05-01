"""PIC 패턴(LDR Rn, [pc, #imm] + ADD Rn, pc)으로 string xref 찾기.

result_addr = (I_add + 4) + literal_value  where I_add = I_ldr + 2

To target file offset T:
    literal_value V = T - I_ldr - 6

평소 컴파일러는 LDR + ADD 를 인접 배치하지만 일부 최적화는 따로 둘 수 있음.
일단 인접 패턴부터 검사.
"""
from __future__ import annotations
import struct, pathlib

ROOT = pathlib.Path(__file__).parent.parent.parent
BIN = ROOT / 'work' / 'extracted' / 'client.bin64000'

TARGETS = {
    0x0a61c8: 'frameBuf is NULL',
    0x0a5d94: '/hero/h00000_bm',
    0x0a5d84: '/hero/h0_cif',
    0x0a5db4: '/boss/boss9000_bm',
    0x0a5da4: '/boss/boss0_cif',
    0x0a5d64: '/boss/bossh_dat',
    0x0a8c28: '/enemy/e1000_bm',
    0x0aac6c: '/map/map0_mp',
    0x0a7f88: '/font/table',
    0x0a7f64: '[HFontError] Font data not loaded.',
    0x0a6888: 'onEventMessageOkKey()',
    0x0a8c18: '/enemy/e000_cif',
    0x0a91a0: '/dat/i0_dat',
    0x0aac58: '/event/e0000_scn',
}


def is_add_rn_pc(instr16: int, rn: int) -> bool:
    """ADD Rn, PC 인코딩 검사. T2: 0100 0100 D Rm[3:0] Rdn[2:0] = 0x4478..0x44FF"""
    if (instr16 & 0xff00) != 0x4400:
        return False
    # Rm 은 PC (r15) = 1111
    rm = (instr16 >> 3) & 0xf
    if rm != 15:
        return False
    # Rdn 결정
    dn = (instr16 >> 7) & 1
    rdn_low = instr16 & 0x7
    rdn = (dn << 3) | rdn_low
    return rdn == rn


def find_xrefs(data: bytes, target_offset: int):
    """target_offset 을 가리키는 LDR+ADD pc-rel 패턴 위치 반환."""
    hits = []
    for off in range(0, len(data) - 4, 2):
        instr = struct.unpack_from('<H', data, off)[0]
        # T1 LDR Rt, [PC, #imm]
        if (instr & 0xf800) != 0x4800:
            continue
        rt = (instr >> 8) & 0x07
        imm8 = instr & 0xff
        pc = (off + 4) & ~3
        lit_addr = pc + imm8 * 4
        if lit_addr + 4 > len(data):
            continue
        lit_val = struct.unpack_from('<I', data, lit_addr)[0]

        # 다음 명령이 ADD Rt, PC 인지
        next_off = off + 2
        if next_off + 2 > len(data):
            continue
        next_instr = struct.unpack_from('<H', data, next_off)[0]
        if not is_add_rn_pc(next_instr, rt):
            continue

        # 결과 주소
        # ADD Rt, PC 의 PC = next_off + 4
        result = (next_off + 4 + lit_val) & 0xffffffff
        if result == target_offset:
            hits.append((off, rt, lit_addr, lit_val))
    return hits


def main():
    data = BIN.read_bytes()
    print(f'Loaded: {len(data)} bytes\n')

    # 각 target 마다 xref 찾기
    total = 0
    all_hits = {}
    for target, label in TARGETS.items():
        hits = find_xrefs(data, target)
        all_hits[target] = hits
        total += len(hits)
        if hits:
            print(f'{target:#08x} {label!r}: {len(hits)} xref(s)')
            for ldr_off, rt, lit_addr, lit_val in hits[:5]:
                print(f'    @ {ldr_off:#08x}: LDR R{rt}, [PC, #imm] (lit @ {lit_addr:#x} = {lit_val:#x}); next: ADD R{rt}, PC')
        else:
            print(f'{target:#08x} {label!r}: no PIC xref')

    print(f'\nTotal xrefs found: {total}')

    # 'frameBuf is NULL' 의 xref 가 핵심. 그 주변 컨텍스트 출력
    framebuf_hits = all_hits.get(0x0a61c8, [])
    if framebuf_hits:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        for ldr_off, rt, lit_addr, lit_val in framebuf_hits[:3]:
            print(f'\n=== Context around frameBuf-NULL xref @ {ldr_off:#x} ===')
            ctx_start = max(0, ldr_off - 64)
            ctx_end = min(len(data), ldr_off + 32)
            for ins in md.disasm(data[ctx_start:ctx_end], ctx_start):
                marker = '  >>>' if ins.address == ldr_off else '     '
                print(f'{marker} {ins.address:#08x}: {ins.mnemonic:8} {ins.op_str}')


if __name__ == '__main__':
    main()
