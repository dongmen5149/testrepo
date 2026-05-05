"""0xf81f (RGB565 magenta = transparent color) 상수 사용 위치 추적.

후보 인스트럭션:
  - MOVW Rn, #0xf81f (T3 32-bit) : HW1=0xF24F, HW2=(Rd<<8) | 0x001F
  - MOV.W Rn, #imm32_table : 32-bit immediate from literal pool
  - LDR Rn, [pc, #imm] with literal == 0x0000f81f
  - 16-bit immediate compare via CMP Rn, #imm (8-bit only, can't fit 0xf81f)
  - 또는 byte 단위 비교 (1f, f8 separately)
"""
from __future__ import annotations
import struct, pathlib
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

_g = select()
BIN = _g.binary_path
assert BIN is not None, f'{_g.id} has no native binary'


def main():
    data = BIN.read_bytes()
    code_end = 0xa5000  # 코드/데이터 경계 추정

    # (1) 32-bit aligned 0x0000f81f literal pool 항목 찾기
    print('=== 32-bit literal pool entries containing 0xf81f ===')
    f81f_lits = []
    for off in range(0, code_end, 4):
        if off + 4 > len(data):
            break
        v = struct.unpack_from('<I', data, off)[0]
        if v == 0x0000f81f or v == 0xf81f0000 or v == 0xf81ff81f or (v & 0xffff) == 0xf81f or (v >> 16) == 0xf81f:
            f81f_lits.append((off, v))
    print(f'  found: {len(f81f_lits)}')
    for off, v in f81f_lits[:30]:
        print(f'    {off:#08x}: 0x{v:08x}')

    # (2) MOVW Rn, #0xf81f 인코딩 검색 (T3)
    # HW1 인코딩: 1111 0 i 1 0 0 1 0 0 imm4
    # 0xf81f → imm4=0xf, i=1, imm3=0, imm8=0x1f
    # HW1 = 11110 1 100100 1111 = 0xF24F
    # HW2 = 0 000 Rd 00011111 = 0x001F | (Rd << 8)
    print('\n=== MOVW Rn, #0xf81f (T3 32-bit) occurrences ===')
    movw_count = 0
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = False
    for off in range(0, code_end, 2):
        if off + 4 > len(data):
            break
        hw1 = struct.unpack_from('<H', data, off)[0]
        hw2 = struct.unpack_from('<H', data, off + 2)[0]
        # 정확 매칭: HW1 = 0xF24F, HW2 lower = 0x001F + Rd<<8
        if hw1 == 0xf24f and (hw2 & 0xf0ff) == 0x001f:
            rd = (hw2 >> 8) & 0xf
            movw_count += 1
            if movw_count <= 30:
                # 컨텍스트
                ctx = data[max(0, off - 8):off + 16]
                ins_list = list(md.disasm(ctx, max(0, off - 8)))
                main_ins = next((i for i in ins_list if i.address == off), None)
                main_str = f'{main_ins.mnemonic} {main_ins.op_str}' if main_ins else 'movw rN, #0xf81f'
                print(f'  {off:#08x}: {main_str}')
    print(f'  total MOVW occurrences: {movw_count}')

    # (3) f81f 의 가장 빈번한 사용 위치 = 비트맵 디코더 후보
    # literal pool 가까운 명령들의 컨텍스트 출력
    if f81f_lits:
        print(f'\n=== Disassembly near first 0xf81f literal ({f81f_lits[0][0]:#x}) ===')
        lit_off = f81f_lits[0][0]
        # 이 literal 을 PC-rel LDR 로 가져오는 명령 찾기
        for off in range(max(0, lit_off - 1024), lit_off, 2):
            instr = struct.unpack_from('<H', data, off)[0]
            if (instr & 0xf800) != 0x4800:
                continue
            rt = (instr >> 8) & 0x07
            imm8 = instr & 0xff
            pc = (off + 4) & ~3
            target = pc + imm8 * 4
            if target == lit_off:
                print(f'\n  Found LDR R{rt}, [PC, #{imm8*4}] at {off:#08x} that reads 0xf81f')
                ctx_start = max(0, off - 64)
                ctx_end = min(len(data), off + 32)
                for ins in md.disasm(data[ctx_start:ctx_end], ctx_start):
                    marker = '  >>>' if ins.address == off else '     '
                    print(f'{marker} {ins.address:#08x}: {ins.mnemonic:8} {ins.op_str}')
                break


if __name__ == '__main__':
    main()
