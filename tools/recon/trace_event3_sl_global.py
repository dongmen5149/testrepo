"""Trace sl-relative globals used by event 3 specific path (0x2c848).

Round 44 / 2KA: identify the global object used at:
  0x2c85c: ldr r3, [pc, #0x1b8]   ← load sl-rel offset literal
  0x2c85e: add r3, sl
  0x2c860: ldr r3, [r3]
  0x2c862: ldr r3, [r3]
  0x2c864: ldr r3, [r3, #0x10]  ← method [+0x10] (graphics call)
  0x2c870: ldr r3, [pc, #0x1a8]
  ... (more sl-relative loads)
"""
import struct
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")
GOT_BASE = 0xB2C40


def read_word(data: bytes, addr: int) -> int:
    return struct.unpack("<I", data[addr:addr+4])[0]


def thumb_pcrel_target(instr_addr: int, imm: int) -> int:
    return (((instr_addr + 4) & ~3) + imm)


def main() -> None:
    data = BIN.read_bytes()

    # FUN_0002c6a4 sl setup (from Round 42):
    #   0x2c6ae: ldr r1, [pc, #0x350] → sl_anchor offset
    #   0x2c6b0: mov sl, r1
    #   0x2c6b2: add sl, pc → sl = pc(0x2c6b2+4) + sl_anchor
    sl_anchor_addr = thumb_pcrel_target(0x2C6AE, 0x350)
    sl_anchor_imm = read_word(data, sl_anchor_addr)
    sl_base = (0x2C6B2 + 4 + sl_anchor_imm) & 0xFFFFFFFF
    print(f"sl base = 0x{sl_base:08x} (= GOT base? {'YES' if sl_base == GOT_BASE else 'NO'})")
    print()

    # event 3 specific path sl-relative loads
    # The disasm shows these LDR sites in event 3 path:
    sites = [
        (0x2C84E, 0x1E0, "task field offset (early)"),
        (0x2C85C, 0x1B8, "GRAPHICS OBJ ptr literal ⭐"),
        (0x2C870, 0x1A8, "another global literal"),
        (0x2C88A, 0x18C, "global literal #3"),
        (0x2C892, 0x188, "global literal #4"),
        (0x2C8AA, 0x174, "global literal #5"),
        (0x2C8F6, 0x13C, "global literal #6"),
        (0x2C90C, 0x128, "global literal #7"),
        (0x2C91A, 0x114, "global literal #8"),
        (0x2C92E, 0x10C, "global literal #9"),
    ]

    print("=== event 3 specific path sl-relative literals ===")
    for instr_addr, imm, desc in sites:
        lit_addr = thumb_pcrel_target(instr_addr, imm)
        if lit_addr + 4 > len(data):
            print(f"  ldr@0x{instr_addr:08x}: literal out of range")
            continue
        val = read_word(data, lit_addr)
        # Two interpretations:
        # (1) val is GOT slot offset (signed)
        # (2) val is sl-relative offset; resolve via sl+val and check if it's a GOT slot address
        sl_rel = (sl_base + val) & 0xFFFFFFFF
        got_offset = (sl_rel - GOT_BASE) & 0xFFFFFFFF
        if got_offset < 0x10000:  # reasonable GOT offset range
            print(f"  ldr@0x{instr_addr:08x}: literal@0x{lit_addr:08x} = 0x{val:08x}")
            print(f"    -> GOT[+0x{got_offset:x}]  ({desc})")
        else:
            print(f"  ldr@0x{instr_addr:08x}: literal@0x{lit_addr:08x} = 0x{val:08x}")
            print(f"    -> sl+0x{val:x} = 0x{sl_rel:08x} (out of GOT range, {desc})")


if __name__ == "__main__":
    main()
