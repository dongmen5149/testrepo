"""Round 50 / 2QC: FUN_818f0 prologue + initialization 본문 dump.

Round 49 finding 정정: entity_arg 가 signed int [-0x10..-1]. "74-entity loop"
가설 재분석 필요.

prologue 와 local[-4] 초기화 패턴, cmp #0x49 의미 추적.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    # Prologue (head 80 bytes)
    print("=== FUN_818f0 prologue + init (0x818f0..0x81940) ===")
    for ins in md.disasm(DATA[0x818f0:0x81940], 0x818f0):
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
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
