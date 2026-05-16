"""Disasm FUN_00025f30 — mode 7 event handler.

Round 40 / 2GB: called as bl FUN_00025f30(r0=0x12, r1=0xb, r2=&task[0xa288], r3=&task[0xa289]).
Returns r0 (used as condition for FUN_0002c6a4(0x11) event trigger).

Profile: 444B / 221 instr / 3 arms (cmp #0xf, #0, #0xc) / BL = 1× ctx only.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    print("=== FUN_00025f30 (0x25f30..0x260ec, 444 bytes) ===")
    for ins in md.disasm(data[0x25F30:0x260EC], 0x25F30):
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
