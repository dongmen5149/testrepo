"""Disasm tiny FUN_00041a68 (20 bytes, 4 callers).

Round 40 / 2GA: record handler called when 0x158-stride record [+0x11] != 0.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    print("=== FUN_00041a68 (20 bytes) ===")
    for ins in md.disasm(data[0x41A68:0x41A7C], 0x41A68):
        print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
