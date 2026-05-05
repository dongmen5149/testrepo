"""Capstone 으로 client.bin64000 을 Thumb 모드 디스어셈블.

전략:
  1. 첫 256바이트 디스어셈블해 진입점/헤더 구조 파악
  2. 모든 LDR Rt, [PC, #imm] 인코딩(0x4800..0x4FFF) 찾기
  3. 각 LDR 의 literal pool 값을 관찰 → pattern 발견 시 base address 후보 도출
"""
from __future__ import annotations
import struct, pathlib
import collections
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

_g = select()
BIN = _g.binary_path
assert BIN is not None, f'{_g.id} has no native binary'


def main():
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

    print('=== Disassembly of first 64 bytes (entry/header area) ===')
    for ins in md.disasm(data[:64], 0x0):
        print(f'  {ins.address:#06x}: {ins.mnemonic:8} {ins.op_str}')

    print('\n=== LDR Rt, [PC, #imm] occurrences (T1 16-bit) ===')
    print('  scanning code region [0x0..0xa5000)...')
    ldr_targets = []
    code_end = 0xa5000
    for off in range(0, code_end - 2, 2):
        instr = struct.unpack_from('<H', data, off)[0]
        if (instr & 0xf800) == 0x4800:  # T1 LDR pc-rel
            rt = (instr >> 8) & 0x07
            imm8 = instr & 0xff
            pc = (off + 4) & ~3
            target = pc + imm8 * 4
            if target + 4 <= len(data):
                val = struct.unpack_from('<I', data, target)[0]
                ldr_targets.append((off, rt, target, val))

    print(f'  total T1 LDR pc-rel: {len(ldr_targets)}')

    # literal value 분포 분석
    val_hist = collections.Counter(v for _, _, _, v in ldr_targets)
    print(f'\n  Top 30 most-loaded literal values:')
    for v, c in val_hist.most_common(30):
        print(f'    0x{v:08x}  ({c} loads)')

    # high-value literal (looks like absolute addresses) 분포
    print(f'\n  Literals in range [0x100000, 0x200000):')
    high = [v for _, _, _, v in ldr_targets if 0x100000 <= v < 0x200000]
    print(f'    count = {len(high)}, min = {min(high) if high else None:#x}, max = {max(high) if high else None:#x}')

    # 0xa61c8 + various base 후보 들이 literals 에 있는지
    print(f'\n  Trying various base candidates against "frameBuf is NULL" (0xa61c8):')
    str_off = 0xa61c8
    candidates = [0x0, 0x8000, 0x10000, 0x100000, 0x200000, 0x10000000, 0x60000000, 0x80000000]
    val_set = set(v for _, _, _, v in ldr_targets)
    for base in candidates:
        target = base + str_off
        hit = target in val_set
        print(f'    BASE 0x{base:08x} → expect literal 0x{target:08x}: {"HIT" if hit else "miss"}')

    # 전체 literal 값 중 0xa00000 - 0xb00000 범위의 값 = "ROData reference" 추정
    print(f'\n  Literals ending with low bits in [0xa5000, 0xb3a10) (rodata file range):')
    print(f'    가설: literal = BASE + file_offset, file_offset 가 rodata 범위에 있는 경우')
    rodata_refs = []
    for off, rt, target, val in ldr_targets:
        for base_test in [0x0, 0x8000, 0x10000, 0x100000, 0x200000, 0x60100000]:
            file_off = val - base_test
            if 0xa5000 <= file_off < 0xb3a10:
                rodata_refs.append((off, val, base_test, file_off))
                break
    print(f'    candidate refs to rodata: {len(rodata_refs)}')
    base_count = collections.Counter(b for _, _, b, _ in rodata_refs)
    print(f'    base distribution: {dict(base_count)}')


if __name__ == '__main__':
    main()
