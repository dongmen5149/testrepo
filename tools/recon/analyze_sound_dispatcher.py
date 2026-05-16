"""Analyze FUN_0003d5d0 sound dispatcher head to identify sound_id → sd file mapping.

Round 45 / 2LB: 4332B / 22 cmp arms / 37 callers (Round 22 finding).
Extract first dispatch logic + check if sound_id is index into a JT.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True

    # Head: first 0x80 bytes
    print("=== FUN_0003d5d0 head (0x3d5d0..0x3d650) ===")
    for ins in md.disasm(data[0x3D5D0:0x3D650], 0x3D5D0):
        marker = ""
        if ins.mnemonic == "bl":
            marker = "  <BL>"
        elif ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic", "bfi"):
            marker = "  <branch>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        elif ins.mnemonic == "ldr" and "pc" in ins.op_str.lower():
            marker = "  <pc-rel ldr>"
        elif ins.mnemonic == "mov" and "pc" in ins.op_str:
            marker = "  ⭐ <JT JUMP>"
        print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
