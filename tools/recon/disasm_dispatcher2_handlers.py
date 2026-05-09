"""dispatcher 2 (_scn parser 후보) 의 6 unique handler capstone 디스어셈블.

handler 영역:
  opcode 0x00~0x0c: 0x68a28 (공통 default)
  opcode 0x0d:      0x68f1c
  opcode 0x0e:      0x6904c
  opcode 0x0f:      0x691cc
  opcode 0x10:      0x6941c
  opcode 0x11:      0x695e2
  opcode 0x12:      0x69734
  (다음 handler 까지 = handler 영역 끝)

각 handler 의 BL/BLX 호출 + LDR/STR 패턴 분석으로 의미 추측.
"""
from __future__ import annotations

import struct
from pathlib import Path
import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"

# (start, end) for each handler region — end = next handler start
HANDLERS = [
    (0x00, "0x00~0x0c default", 0x068a28, 0x068f1c),
    (0x0d, "opcode 0x0d", 0x068f1c, 0x06904c),
    (0x0e, "opcode 0x0e", 0x06904c, 0x0691cc),
    (0x0f, "opcode 0x0f", 0x0691cc, 0x06941c),
    (0x10, "opcode 0x10", 0x06941c, 0x0695e2),
    (0x11, "opcode 0x11", 0x0695e2, 0x069734),
    (0x12, "opcode 0x12", 0x069734, 0x06a000),  # rough end estimate
]


def decode_bl(first: int, second: int, pc: int) -> int | None:
    if (first & 0xF800) != 0xF000:
        return None
    if (second & 0xD000) != 0xD000:
        return None
    S = (first >> 10) & 1
    imm10 = first & 0x3FF
    J1 = (second >> 13) & 1
    J2 = (second >> 11) & 1
    imm11 = second & 0x7FF
    I1 = (~(J1 ^ S)) & 1
    I2 = (~(J2 ^ S)) & 1
    imm32 = (S << 24) | (I1 << 23) | (I2 << 22) | (imm10 << 12) | (imm11 << 1)
    if S:
        imm32 = imm32 - 0x100000000
    return (pc + imm32) & 0xFFFFFFFF


def main() -> None:
    data = BIN.read_bytes()
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = True

    for op, label, start, end in HANDLERS:
        size = end - start
        print(f"=== handler {label} @ 0x{start:08x} (size {size} bytes) ===")
        chunk = data[start:end]
        # Disassemble
        bl_targets = []
        ldr_pcrel = []
        instr_count = 0
        for ins in md.disasm(chunk, start):
            instr_count += 1
            mnem = ins.mnemonic
            op_str = ins.op_str
            # Print first ~30 instructions
            if instr_count <= 25:
                print(f"  0x{ins.address:08x}: {mnem:<8} {op_str}")
            # Track BL targets
            if mnem in ("bl", "blx"):
                # Try to parse target from op_str (Capstone usually resolves)
                try:
                    target_str = op_str.replace("#", "").strip()
                    if target_str.startswith("0x"):
                        bl_targets.append((ins.address, int(target_str, 16)))
                except ValueError:
                    pass
            # Track ldr Rn, [pc, ...]  (literal pool — DAT_xxx 참조)
            if mnem == "ldr" and "pc" in op_str.lower():
                ldr_pcrel.append((ins.address, op_str))

        if instr_count > 25:
            print(f"  ... ({instr_count - 25} more instructions)")

        print()
        print(f"  BL/BLX calls: {len(bl_targets)}")
        for addr, target in bl_targets[:15]:
            print(f"    0x{addr:08x}: → 0x{target:08x}")
        print()
        print(f"  PC-relative LDR (literal pool refs): {len(ldr_pcrel)}")
        for addr, op_str in ldr_pcrel[:8]:
            print(f"    0x{addr:08x}: {op_str}")

        print()
        print()


if __name__ == "__main__":
    main()
