"""Round 50 / 2QF: FUN_82df4 본문 (44B, FUN_818f0 post-call cleanup)."""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("=== FUN_82df4 full disasm (0x82df4..0x82e20) ===")
    for ins in md.disasm(DATA[0x82df4:0x82e20], 0x82df4):
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
        elif ins.mnemonic.startswith("b"):
            marker = "  <branch>" if ins.mnemonic not in ("bic", "bfi", "bl", "blx", "bx") else ""
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
