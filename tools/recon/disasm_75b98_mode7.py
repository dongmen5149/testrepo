"""Round 51 / 2RE: FUN_75b98 mode=7 분기 정밀.

Round 50 finding: FUN_75b98 = render flush (256B buffer @ ctx+lit+0xa0 dirty check → memset → indirect render).
Round 50 partial: mode=7 분기 미해결.

전체 324B disasm + mode 분기 추출.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("=== FUN_75b98 full (0x75b98..0x75cdc) ===")
    bls, cmps = 0, []
    for ins in md.disasm(DATA[0x75b98:0x75cdc], 0x75b98):
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
            cmps.append((hex(ins.address), ins.op_str))
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
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
    print(f"\n  BL: {bls}")
    print(f"  cmps ({len(cmps)}): {cmps}")


if __name__ == "__main__":
    main()
