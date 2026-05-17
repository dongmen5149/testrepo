"""Round 48 / 2OD: FUN_85edc + FUN_85fc8 raw disasm + 분석.

두 함수 모두 task[0xa848] flag byte (+0x01 또는 +0x02) reader. 본문 전체 풀이.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def disasm(start: int, end: int, label: str) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print(f"\n=== {label} (0x{start:05x}..0x{end:05x}, {end - start}B) ===")
    for ins in md.disasm(DATA[start:end], start):
        marker = ""
        if ins.mnemonic == "bl":
            marker = "  <BL>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        elif ins.mnemonic.startswith("ldrb"):
            marker = "  <ldrb>"
        elif ins.mnemonic.startswith("strb"):
            marker = "  <strb>"
        elif ins.mnemonic in ("ldr",) and "[pc" in ins.op_str:
            marker = "  <pc-rel>"
        elif ins.mnemonic in ("b",) or (ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic", "bfi", "bl", "blx", "bx")):
            marker = "  <branch>"
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


def main() -> None:
    disasm(0x85edc, 0x85fc8, "FUN_85edc (236B)")
    disasm(0x85fc8, 0x86040, "FUN_85fc8 (120B)")


if __name__ == "__main__":
    main()
