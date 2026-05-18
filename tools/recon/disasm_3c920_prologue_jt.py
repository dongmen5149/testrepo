"""Round 51 / 2RC: FUN_3c920 prologue + dispatch JT 추출 (2836B, 33-arm cmp).

Round 46 finding: cmp 'd'/'f'/'g'/'h'/'i' 33 arms = phone keypad letter mapping.
전체 본문 dump 대신 prologue (160B) + dispatch JT 구조만 추출.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("=== FUN_3c920 prologue + dispatch (0x3c920..0x3ca10) ===")
    bls, cmps = 0, []
    for ins in md.disasm(DATA[0x3c920:0x3ca10], 0x3c920):
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
    print(f"\n  BL count: {bls}")
    print(f"  cmps ({len(cmps)}): {cmps[:10]}")

    # Now scan full function for ALL cmps to count branches
    print("\n=== Full FUN_3c920 cmp scan (0x3c920..0x3d434) ===")
    all_cmps = []
    for ins in md.disasm(DATA[0x3c920:0x3d434], 0x3c920):
        if ins.mnemonic.startswith("cmp"):
            all_cmps.append(ins.op_str)
    print(f"  total cmps: {len(all_cmps)}")
    # Count by literal
    char_cmps = []
    for c in all_cmps:
        if ", #" in c:
            try:
                imm = int(c.split(", #")[1], 0)
                char_cmps.append(imm)
            except Exception:
                pass
    from collections import Counter
    cnt = Counter(char_cmps)
    print(f"  unique cmp values: {len(cnt)}")
    # Show ASCII-printable cmp values
    print(f"  ASCII-printable cmp values:")
    for v, n in sorted(cnt.items()):
        if 0x20 <= v < 0x80:
            ascii_char = chr(v) if 0x20 <= v < 0x7f else "?"
            print(f"    cmp #0x{v:02x} ('{ascii_char}') x{n}")


if __name__ == "__main__":
    main()
