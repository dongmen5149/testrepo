"""Trace FUN_00085aa8 sl-relative literal for vtable [+0x60] object identity.

Round 47 / 2NC: 0x85af0 has `ldr r3, [pc, #0x20]` → load sl-relative offset.
Then `add r3, sl` resolves to GOT slot.
"""
import struct
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")
GOT_BASE = 0xB2C40


def thumb_pcrel_target(instr_addr: int, imm: int) -> int:
    return (((instr_addr + 4) & ~3) + imm)


def read_word(data: bytes, addr: int) -> int:
    return struct.unpack("<I", data[addr:addr+4])[0]


def main() -> None:
    data = BIN.read_bytes()

    # FUN_00085aa8 sl setup:
    #   0x85ab2: ldr r1, [pc, #0x54] → sl_anchor
    #   0x85ab4: mov sl, r1
    #   0x85ab6: add sl, pc → sl = pc(0x85ab6+4 = 0x85aba) + sl_anchor
    sl_anchor_addr = thumb_pcrel_target(0x85AB2, 0x54)
    sl_anchor_imm = read_word(data, sl_anchor_addr)
    sl_base = (0x85AB6 + 4 + sl_anchor_imm) & 0xFFFFFFFF
    print(f"FUN_00085aa8 sl base = 0x{sl_base:08x}")
    print(f"  sl - GOT = 0x{(sl_base - GOT_BASE) & 0xFFFFFFFF:08x}")
    print()

    # sl-relative loads:
    # 0x85ada: ldr r1, [pc, #0x30]   — task field offset for state clear
    # 0x85ae6: ldr r2, [pc, #0x28]   — memset_like literal
    # 0x85af0: ldr r3, [pc, #0x20]   — ⭐ global obj ptr literal
    sites = [
        (0x85ADA, 0x30, "state clear field offset"),
        (0x85AE6, 0x28, "memset_like arg"),
        (0x85AF0, 0x20, "⭐ global obj ptr literal"),
    ]
    for instr_addr, imm, desc in sites:
        lit_addr = thumb_pcrel_target(instr_addr, imm)
        if lit_addr + 4 > len(data):
            print(f"  ldr@0x{instr_addr:08x}: literal out of range")
            continue
        val = read_word(data, lit_addr)
        sl_rel = (sl_base + val) & 0xFFFFFFFF
        got_offset = (sl_rel - GOT_BASE) & 0xFFFFFFFF
        print(f"  ldr@0x{instr_addr:08x}: literal@0x{lit_addr:08x} = 0x{val:08x}")
        if got_offset < 0x10000:
            print(f"    -> GOT[+0x{got_offset:x}]  ({desc})")
        else:
            print(f"    -> sl + 0x{val:x} = 0x{sl_rel:08x} (out of GOT range, {desc})")


if __name__ == "__main__":
    main()
