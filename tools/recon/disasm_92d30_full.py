"""Round 50 / 2QB-2: FUN_92d30 raw disasm.

FUN_92d30 (112B) = '4' LEFT / '6' RIGHT phone keypad horizontal nav handler.
FUN_92cc0 (Round 46) = '2' UP / '8' DOWN vertical handler 의 짝.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("=== FUN_92d30 full disasm (0x92d30..0x92da0) ===")
    for ins in md.disasm(DATA[0x92d30:0x92da0], 0x92d30):
        marker = ""
        if ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                marker = f"  <BL 0x{t:x}>"
            except Exception:
                marker = "  <BL>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        elif ins.mnemonic in ("b", "beq", "bne", "blt", "ble", "bgt", "bge",
                              "bcs", "bcc", "bls", "bhi", "bmi", "bpl"):
            marker = "  <branch>"
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
