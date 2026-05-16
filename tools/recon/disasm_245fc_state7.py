"""Disasm FUN_000245fc state 7 path (0x24714..0x24780).

Round 39 / 2FA: see what mode==7 does — uses task_struct[0xa1f6/0xa288/0xa289].
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    print("=== FUN_000245fc state-7 path (0x24714..0x24780) ===")
    for ins in md.disasm(data[0x24714:0x24780], 0x24714):
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
