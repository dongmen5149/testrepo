"""Disasm head of FUN_000245fc to see the state dispatch entry.

Round 39 / 2FA: 13 arms with cmp #0/3/4/7 + 7 ctx + 14 task_struct field reads —
need to confirm 4-way state machine dispatch on entry.
"""
from pathlib import Path

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError as e:
    raise SystemExit("capstone not installed: pip install capstone") from e

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    print(f"=== FUN_000245fc head (0x245fc..0x24700, 0x104 bytes) ===")
    for ins in md.disasm(data[0x245FC:0x24700], 0x245FC):
        marker = ""
        if ins.mnemonic == "bl":
            marker = "  <BL>"
        elif ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic", "bfi", "bfc"):
            marker = "  <branch>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
