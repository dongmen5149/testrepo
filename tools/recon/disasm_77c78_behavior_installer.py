"""Round 52 / 2SB: FUN_77c78 behavior installer 본문 dump (236B).

Round 51 finding: vtable[+0x54] alloc 직후 호출 (0x85c04).
호출 pattern: r0 = (task[+0xa32c] ? *GOT[+0xb44] : *GOT[+0xb48])  (behavior fp)
   → FUN_77c78(fp)  → result stored at local[-0xc]
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("=== FUN_77c78 full (0x77c78..0x77d64) ===")
    bls, cmps = 0, []
    for ins in md.disasm(DATA[0x77c78:0x77d64], 0x77c78):
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
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
    print(f"\n  BL: {bls}, cmps: {cmps}")


if __name__ == "__main__":
    main()
