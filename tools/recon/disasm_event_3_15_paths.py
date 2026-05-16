"""Disasm event 3 specific path (0x2c848) + event 15 specific path (0x2c952).

Round 43 / 2JD:
- event 3 (most popular, 8 callers) → 0x2c848
- event 15 → 0x2c952 (cmp #0xc bne 0x2c95a 의 fall-through)
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
    # event 3 specific path
    disasm_window(data, 0x2C848, 0x2C950, "event 3 specific path (0x2c848)")
    # event 15 specific path (from cmp #0xc bne 0x2c95a fall-through)
    disasm_window(data, 0x2C952, 0x2C9CA, "event 15 specific path (0x2c952)")


if __name__ == "__main__":
    main()
