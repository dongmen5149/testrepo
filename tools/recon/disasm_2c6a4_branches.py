"""Disasm FUN_0002c6a4 event dispatcher with per-branch focus.

Round 41 / 2HA: trace the 9 cmp arms + their BL chains.
Goal: identify what events 8/c/d/e/f/10 共通 handler 0x2c9ca does,
and what the other branches (0x2c6f6, 0x2c848, 0x2c95a, 0x2ca6c) do.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def disasm_window(data: bytes, start: int, end: int, label: str) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    print(f"\n=== {label} (0x{start:08x}..0x{end:08x}, {end-start} bytes) ===")
    for ins in md.disasm(data[start:end], start):
        marker = ""
        if ins.mnemonic == "bl":
            marker = "  <BL>"
        elif ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic", "bfi"):
            marker = "  <branch>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{marker}")


def main() -> None:
    data = BIN.read_bytes()
    # Section 1: head + first dispatch (0x2c6a4..0x2c700)
    disasm_window(data, 0x2C6A4, 0x2C700, "head + entry dispatch")
    # Section 2: events 8/c/d/e/f/10 common handler (0x2c9ca..0x2ca40)
    disasm_window(data, 0x2C9CA, 0x2CA40, "common handler 0x2c9ca (events 8/c/d/e/f/10)")
    # Section 3: ending of common handler + return path
    disasm_window(data, 0x2CA40, 0x2CA88, "tail + return")


if __name__ == "__main__":
    main()
