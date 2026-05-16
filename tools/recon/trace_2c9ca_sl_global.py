"""Resolve the sl-relative global object accessed by FUN_0002c6a4 공통 handler 0x2c9ca and
FUN_0002cdb4 helper.

Round 42 / 2IA: extract the actual literal values used in the sl-relative loads,
then resolve them to GOT slot offsets (= sl + offset literal points to GOT slot).
"""
import struct
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")
GOT_BASE = 0xB2C40  # confirmed from Round 23+


def read_word(data: bytes, addr: int) -> int:
    return struct.unpack("<I", data[addr:addr+4])[0]


def thumb_pcrel_target(instr_addr: int, imm: int) -> int:
    """Compute Thumb LDR Rd,[pc,#imm] literal address.

    pc = (instr_addr + 4) & ~3, target = pc + imm.
    """
    return (((instr_addr + 4) & ~3) + imm)


def main() -> None:
    data = BIN.read_bytes()

    # FUN_0002cdb4 head (PIC sl setup):
    #   0x2cdbc: ldr r3, [pc, #0x3c]  → reads sl_anchor offset
    #   0x2cdbe: mov sl, r3
    #   0x2cdc0: add sl, pc          → sl = pc(0x2cdc0+4 = 0x2cdc4) + (sl_anchor offset)
    sl_anchor_addr = thumb_pcrel_target(0x2CDBC, 0x3C)
    sl_anchor_imm = read_word(data, sl_anchor_addr)
    sl_base = (0x2CDC0 + 4 + sl_anchor_imm) & 0xFFFFFFFF  # this is the sl base for FUN_0002cdb4
    print(f"FUN_0002cdb4 sl setup:")
    print(f"  literal at 0x{sl_anchor_addr:08x} = 0x{sl_anchor_imm:08x}")
    print(f"  sl = pc(0x{0x2CDC0+4:08x}) + 0x{sl_anchor_imm:08x} = 0x{sl_base:08x}")
    print(f"  sl - GOT_BASE = 0x{(sl_base - GOT_BASE) & 0xFFFFFFFF:08x}")
    print()

    # FUN_0002cdb4 body loads at 0x2cdc2 (ldr [pc, #0x3c]) and 0x2cdce (ldr [pc, #0x34]) and 0x2cdd6 (ldr [pc, #0x28]) and 0x2cde6 (ldr [pc, #0x18])
    sites = [
        (0x2CDC2, 0x3C, "global ptr literal"),
        (0x2CDCE, 0x34, "method-handle literal #1"),
        (0x2CDD6, 0x28, "method-handle literal #2"),
        (0x2CDE6, 0x18, "pending flag literal"),
    ]
    for instr_addr, imm, desc in sites:
        lit_addr = thumb_pcrel_target(instr_addr, imm)
        val = read_word(data, lit_addr)
        # sl + val = absolute (per ARM PIC convention)
        sl_relative_target = (sl_base + val) & 0xFFFFFFFF
        got_offset = (sl_relative_target - GOT_BASE) & 0xFFFFFFFF
        print(f"  ldr@0x{instr_addr:08x}: literal@0x{lit_addr:08x} = 0x{val:08x}")
        print(f"    -> sl+val = 0x{sl_relative_target:08x}")
        print(f"    -> GOT[+0x{got_offset:x}]    ({desc})")
        print()

    # Also for 0x2c9ca common handler (FUN_0002c6a4 sl setup at 0x2c6ae..0x2c6b2)
    # 0x2c6ae: ldr r1, [pc, #0x350] → sl_anchor
    # 0x2c6b0: mov sl, r1
    # 0x2c6b2: add sl, pc  → sl = pc(0x2c6b2+4 = 0x2c6b6) + sl_anchor
    sl_anchor_addr2 = thumb_pcrel_target(0x2C6AE, 0x350)
    sl_anchor_imm2 = read_word(data, sl_anchor_addr2)
    sl_base2 = (0x2C6B2 + 4 + sl_anchor_imm2) & 0xFFFFFFFF
    print(f"FUN_0002c6a4 sl setup:")
    print(f"  literal at 0x{sl_anchor_addr2:08x} = 0x{sl_anchor_imm2:08x}")
    print(f"  sl = 0x{sl_base2:08x}, sl - GOT = 0x{(sl_base2 - GOT_BASE) & 0xFFFFFFFF:08x}")
    print()

    # FUN_0002c6a4 common handler 0x2c9ca body:
    # 0x2c9ce: ldr r3, [pc, #0x4c]
    # 0x2c9da: ldr r3, [pc, #0x3c]
    # 0x2c9e2: ldr r3, [pc, #0x38]
    # 0x2c9f2: ldr r3, [pc, #0x28]
    sites2 = [
        (0x2C9CE, 0x4C, "global ptr literal (common)"),
        (0x2C9DA, 0x3C, "method-handle literal #A"),
        (0x2C9E2, 0x38, "method-handle literal #B"),
        (0x2C9F2, 0x28, "pending flag literal (common)"),
    ]
    for instr_addr, imm, desc in sites2:
        lit_addr = thumb_pcrel_target(instr_addr, imm)
        val = read_word(data, lit_addr)
        sl_relative_target = (sl_base2 + val) & 0xFFFFFFFF
        got_offset = (sl_relative_target - GOT_BASE) & 0xFFFFFFFF
        print(f"  ldr@0x{instr_addr:08x}: literal@0x{lit_addr:08x} = 0x{val:08x}")
        print(f"    -> sl+val = 0x{sl_relative_target:08x}")
        print(f"    -> GOT[+0x{got_offset:x}]    ({desc})")
        print()


if __name__ == "__main__":
    main()
