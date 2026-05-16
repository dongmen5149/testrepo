"""Disasm FUN_0002cdb4 (84B, 5 callers) — helper for FUN_0002c6a4 common handler.

Round 41 / 2HA: identify what the helper does.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    print("=== FUN_0002cdb4 (0x2cdb4..0x2ce08, 84 bytes) ===")
    for ins in md.disasm(data[0x2CDB4:0x2CE08], 0x2CDB4):
        marker = ""
        if ins.mnemonic == "bl":
            marker = "  <BL>"
        elif ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic", "bfi"):
            marker = "  <branch>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
