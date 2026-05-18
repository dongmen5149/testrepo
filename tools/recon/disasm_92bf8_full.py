"""Round 51 / 2RB: FUN_92bf8 본문 dump (200B).

Round 50 finding: FUN_92cc0 = '2'/'8' UP/DOWN dispatcher, FUN_92d30 = '4'/'6' LEFT/RIGHT.
FUN_92bf8 = 4 callers system-wide (Round 50). 후보: mode 1/2/3/4 별 처리.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    start, end = 0x92bf8, 0x92cc0
    print(f"=== FUN_92bf8 @ 0x{start:05x}..0x{end:05x} ({end - start} bytes) ===")
    bls = 0
    cmps = []
    for ins in md.disasm(DATA[start:end], start):
        marker = ""
        if ins.mnemonic == "bl":
            bls += 1
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                marker = f"  <BL 0x{t:x}>"
            except Exception:
                marker = "  <BL>"
        elif ins.mnemonic.startswith("cmp"):
            cmps.append(ins.op_str)
            marker = "  <cmp>"
        elif ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                pc = (ins.address + 4) & ~3
                lit_addr = pc + imm
                lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                marker = f"  <LIT@0x{lit_addr:05x}=0x{lit:08x}>"
            except Exception:
                pass
        elif ins.mnemonic in ("bx", "mov") and "lr" in ins.op_str:
            marker = "  <RET>"
        elif ins.mnemonic == "mov" and ins.op_str.startswith("pc"):
            marker = "  <PC>"
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
    print(f"  -- BL count: {bls}, cmps: {cmps}")


if __name__ == "__main__":
    main()
