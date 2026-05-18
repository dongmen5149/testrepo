"""Round 53 / 2TD: FUN_439a0 (FUN_9a008 dominant helper) prologue + stats.

2372B function called 7x from FUN_9a008 (Round 52 stats). 가장 빈번한 helper.
"""
import struct
from pathlib import Path
from collections import Counter
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    start, end = 0x439a0, 0x442e4

    print(f"=== FUN_439a0 prologue (first 50 instr) ===")
    count = 0
    for ins in md.disasm(DATA[start:start + 200], start):
        marker = ""
        if ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                marker = f"  <BL 0x{t:x}>"
            except Exception:
                pass
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        elif ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                pc = (ins.address + 4) & ~3
                lit_addr = pc + imm
                lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                marker = f"  <LIT=0x{lit:x}>"
            except Exception:
                pass
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
        count += 1
        if count >= 50:
            break

    print("\n=== Full FUN_439a0 stats ===")
    bls, cmps = [], []
    for ins in md.disasm(DATA[start:end], start):
        if ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                bls.append(int(tok, 0))
            except Exception:
                pass
        elif ins.mnemonic.startswith("cmp"):
            if ", #" in ins.op_str:
                try:
                    cmps.append(int(ins.op_str.split(", #")[1], 0))
                except Exception:
                    pass

    bl_cnt = Counter(bls)
    cmp_cnt = Counter(cmps)
    print(f"\nTotal BL: {len(bls)} (unique: {len(bl_cnt)})")
    print(f"Top 15 BL targets:")
    for t, n in bl_cnt.most_common(15):
        print(f"  BL 0x{t:05x} x{n}")

    print(f"\nTotal cmp #imm: {len(cmps)} (unique: {len(cmp_cnt)})")
    print(f"All cmp values:")
    for v, n in sorted(cmp_cnt.items()):
        ascii_str = f" ('{chr(v)}')" if 0x20 <= v < 0x7f else ""
        print(f"  cmp #0x{v:02x}{ascii_str} x{n}")


if __name__ == "__main__":
    main()
