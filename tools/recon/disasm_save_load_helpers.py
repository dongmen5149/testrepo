"""Round 53 / 2TB+2TC: FUN_77c78 의 4 helper 본문 dump.

  FUN_99a9c (144B): query/find (record_ptr + size 반환)
  FUN_9f624 (6B):   tiny — veneer/trampoline?
  FUN_d060  (148B): setup helper
  FUN_5610c (88B):  process helper (16B name 추가 인자)
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def dump(start: int, end: int, label: str) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print(f"\n=== {label} @ 0x{start:05x}..0x{end:05x} ({end - start}B) ===")
    bls, cmps = 0, []
    for ins in md.disasm(DATA[start:end], start):
        marker = ""
        if ins.mnemonic == "bl":
            bls += 1
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                marker = f"  <BL 0x{t:x}>"
            except Exception:
                pass
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
    print(f"  -- BL: {bls}, cmps: {cmps}")


def main() -> None:
    dump(0x99a9c, 0x99b2c, "FUN_99a9c (query)")
    dump(0x9f624, 0x9f62a, "FUN_9f624 (tiny)")
    dump(0xd060,  0xd0f4,  "FUN_d060 (setup)")
    dump(0x5610c, 0x56164, "FUN_5610c (process)")


if __name__ == "__main__":
    main()
