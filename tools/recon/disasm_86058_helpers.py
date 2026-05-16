"""Disasm 4 helper functions called by FUN_00086058 (7th indirect entry).

Round 46 / 2MA, 2ME, 2MF:
- FUN_00085578c (24B, 34 callers) — sub-command resolver
- FUN_00085aa8 (112B, 1 caller exclusive) — event 3 path helper
- FUN_00092bd0 (40B, 15 callers) — byte query
- FUN_00092cc0 (112B, 5 callers) — default path
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def disasm(data: bytes, start: int, end: int, label: str) -> None:
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
    disasm(data, 0x8578C, 0x857A4, "FUN_00085578c (sub-command resolver, 24B, 34 callers)")
    disasm(data, 0x85AA8, 0x85B18, "FUN_00085aa8 (event 3 path helper, 112B, 1 caller)")
    disasm(data, 0x92BD0, 0x92BF8, "FUN_00092bd0 (byte query, 40B, 15 callers)")
    disasm(data, 0x92CC0, 0x92D30, "FUN_00092cc0 (default path, 112B, 5 callers)")


if __name__ == "__main__":
    main()
