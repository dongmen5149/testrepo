"""Disasm FUN_000245fc record loop body to understand 0x158-stride record structure.

Round 40 / 2GA: trace the loop 0x24648..0x2467e + the special path at 0x246e8.
Goal: identify all record offsets accessed + the inner sub-struct shape.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    # Cover the record array setup + main loop + special path at 0x246e8
    print("=== FUN_000245fc record loop (0x24632..0x24716) ===")
    for ins in md.disasm(data[0x24634:0x24716], 0x24634):
        marker = ""
        if ins.mnemonic == "bl":
            marker = "  <BL>"
        elif ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic", "bfi"):
            marker = "  <branch>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        elif ins.mnemonic.startswith("ldr") and ins.mnemonic != "ldr":
            marker = "  <ldr-variant>"
        print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
