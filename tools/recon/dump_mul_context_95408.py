"""Round 55 / 2VD: FUN_95408 의 mul instructions 주변 컨텍스트 dump.

34 muls 의 직전/직후 4 inst 를 보면 어떤 값들이 곱해지는지 = 어떤 stat 산술인지 식별.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def dump_mul_contexts(start: int, size: int, label: str) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    end = start + size
    insns = list(md.disasm(DATA[start:end], start))
    print(f"\n========== {label} mul contexts ==========")
    for i, ins in enumerate(insns):
        if ins.mnemonic in ("muls", "mul"):
            print(f"\n  --- mul @ 0x{ins.address:05x}: {ins.mnemonic} {ins.op_str} ---")
            for j in range(max(0, i - 3), min(i + 3, len(insns))):
                marker = "  ★" if j == i else "   "
                ins2 = insns[j]
                op_str = ins2.op_str
                # PC-rel literal resolution
                if ins2.mnemonic == "ldr" and "[pc" in op_str:
                    try:
                        imm = int(op_str.split("#")[1].rstrip("]"), 0)
                        pc = (ins2.address + 4) & ~3
                        lit_addr = pc + imm
                        if lit_addr + 4 <= len(DATA):
                            lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                            op_str = f"{op_str}  <LIT=0x{lit:x}>"
                    except Exception:
                        pass
                print(f"  {marker}0x{ins2.address:05x}: {ins2.mnemonic:8} {op_str}")


def main() -> None:
    dump_mul_contexts(0x95408, 1208, "FUN_95408")


if __name__ == "__main__":
    main()
