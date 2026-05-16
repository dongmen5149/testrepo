"""Disasm tiny FUN_000260ec (68 bytes, 2 callers) — 2nd FUN_00025f30 caller wrapper.

Round 41 / 2HD: see what the wrapper does (probably another NPC query context).
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    print("=== FUN_000260ec (0x260ec..0x26130, 68 bytes) ===")
    for ins in md.disasm(data[0x260EC:0x26130], 0x260EC):
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
