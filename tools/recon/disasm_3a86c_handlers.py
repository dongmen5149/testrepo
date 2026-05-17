"""Round 50 / 2QA-2: FUN_3a86c 의 4 distinct JT target handlers 본문 분석.

JT 디코드 결과 (decode_3a86c_jt.py):
  - 0x3a8be: entity_arg -16, -5 (이미 Round 49 분석)
  - 0x3a9ca: entity_arg -15..-6 (10 entries) = escape/epilogue
  - 0x3a98c: entity_arg -4, -2
  - 0x3a952: entity_arg -3, -1
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def disasm_range(start: int, end: int, label: str) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print(f"\n=== {label} (0x{start:05x}..0x{end:05x}) ===")
    for ins in md.disasm(DATA[start:end], start):
        marker = ""
        if ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                if t == 0x4ad10:
                    marker = "  <BL context_getter>"
                elif t == 0x3c920:
                    marker = "  <BL FUN_3c920 letter_core>"
                elif t == 0x2d77c:
                    marker = "  <BL FUN_2d77c>"
                else:
                    marker = f"  <BL 0x{t:x}>"
            except Exception:
                marker = "  <BL>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        elif ins.mnemonic == "strb":
            marker = "  <STRB>"
        elif ins.mnemonic in ("b", "beq", "bne", "blt", "ble", "bgt", "bge",
                              "bcs", "bcc", "bls", "bhi", "bmi", "bpl"):
            marker = "  <branch>"
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


def main() -> None:
    # Handler 0x3a98c (entity_arg -4, -2)
    disasm_range(0x3a98c, 0x3a9ca, "Handler @0x3a98c (entity_arg -4, -2)")
    # Handler 0x3a952 (entity_arg -3, -1)
    disasm_range(0x3a952, 0x3a98c, "Handler @0x3a952 (entity_arg -3, -1)")
    # Handler 0x3a9ca (escape — entity_arg -15..-6 default)
    disasm_range(0x3a9ca, 0x3a9f0, "Handler @0x3a9ca (escape/epilogue)")


if __name__ == "__main__":
    main()
