"""Round 53 / 2TA: FUN_9a008 의 JT_1 7 leaves 의 첫 80B dump.

JT_1 leaves (from decode_9a008_nested_jts.py):
  idx=0 → 0x9a056   (default path 진입)
  idx=1 → 0x9a556
  idx=2 → 0x9aabe
  idx=3 → 0x9b258
  idx=4 → 0x9b7e6
  idx=5 → 0x9bce6
  idx=6 → 0x9bfc8

각 leaf 의 BL targets + cmp pattern 으로 정체 추정.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

LEAVES = [
    (0, 0x9a056),
    (1, 0x9a556),
    (2, 0x9aabe),
    (3, 0x9b258),
    (4, 0x9b7e6),
    (5, 0x9bce6),
    (6, 0x9bfc8),
]


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for idx, addr in LEAVES:
        print(f"\n=== JT_1[{idx}] leaf @ 0x{addr:05x} (first 30 instr) ===")
        bls, cmps, lits = [], [], []
        count = 0
        for ins in md.disasm(DATA[addr:addr + 100], addr):
            marker = ""
            if ins.mnemonic == "bl":
                tok = ins.op_str.strip().lstrip("#")
                try:
                    t = int(tok, 0)
                    bls.append(t)
                    marker = f" <BL 0x{t:x}>"
                except Exception:
                    pass
            elif ins.mnemonic.startswith("cmp"):
                cmps.append(ins.op_str)
                marker = " <cmp>"
            elif ins.mnemonic == "ldr" and "[pc" in ins.op_str:
                try:
                    imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                    pc = (ins.address + 4) & ~3
                    lit_addr = pc + imm
                    lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                    lits.append(lit)
                    marker = f" <LIT=0x{lit:x}>"
                except Exception:
                    pass
            print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
            count += 1
            if count >= 30:
                break
        if bls:
            print(f"  BL: {sorted({hex(b) for b in bls})}  ({len(bls)} calls)")
        if cmps:
            print(f"  cmps: {cmps}")
        if lits:
            unique_lits = sorted({hex(l) for l in lits})
            print(f"  literals: {unique_lits}")


if __name__ == "__main__":
    main()
