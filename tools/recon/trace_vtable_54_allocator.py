"""Round 51 / 2RD: ObjectB vtable[+0x54] allocator 본문 추적.

Round 50 finding: task[0xa848]+0x08 = 60-byte ObjectB instance (dynamically allocated).
  - vtable[+0x54] = allocator (NEW)
  - vtable[+0x58] = destructor (Round 47 의 method0x58 정체)

Round 50 raw disasm 발견: 0x85bc8 에서 'bl 0xa42a0' (veneer) 가 NEW 호출.
veneer 0xa42a0 의 본문 추출 + literal target 확인.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

    # Veneer 0xa42a0 (and check ±0xa429c/0xa42a4 for context)
    for vstart in [0xa429c, 0xa42a0, 0xa42a4, 0xa42a8]:
        print(f"\n=== veneer @ 0x{vstart:05x} (16B) ===")
        for ins in md.disasm(DATA[vstart:vstart + 16], vstart):
            marker = ""
            if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
                try:
                    imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                    pc = (ins.address + 4) & ~3
                    lit_addr = pc + imm
                    lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                    marker = f"  <LIT@0x{lit_addr:05x}=0x{lit:08x}>"
                except Exception:
                    pass
            print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")

    # Also dump the allocation site context (0x85bc8 ± 0x20)
    print(f"\n=== Allocation site context (0x85ba0..0x85c20) ===")
    for ins in md.disasm(DATA[0x85ba0:0x85c20], 0x85ba0):
        marker = ""
        if ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                marker = f"  <BL 0x{t:x}>"
            except Exception:
                marker = "  <BL>"
        elif ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                pc = (ins.address + 4) & ~3
                lit_addr = pc + imm
                lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                marker = f"  <LIT@0x{lit_addr:05x}=0x{lit:08x}>"
            except Exception:
                pass
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
