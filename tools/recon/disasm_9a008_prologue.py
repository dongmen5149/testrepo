"""Round 52 / 2SE: FUN_9a008 super function prologue + cmp/BL 통계.

8.8KB (0x9a008..0x9c280) — Round 35 의 16.3KB SCN bytecode interpreter (FUN_8e89e) 와 함께
Hero3 의 거대 super function. battle 시스템 후보.

전략:
- prologue 160B disasm
- 전체 cmp value 분포 → opcode/state JT 추정
- 전체 BL target 분포 → 호출 helper 패턴
"""
import struct
from pathlib import Path
from collections import Counter
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    start, end = 0x9a008, 0x9c280
    print(f"=== FUN_9a008 prologue (first 200B) ===")
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
                marker = f"  <LIT@0x{lit_addr:05x}=0x{lit:08x}>"
            except Exception:
                pass
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
        count += 1
        if count >= 50:
            break

    print("\n=== Full FUN_9a008 stats ===")
    bl_targets = []
    cmp_vals = []
    for ins in md.disasm(DATA[start:end], start):
        if ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                bl_targets.append(t)
            except Exception:
                pass
        elif ins.mnemonic.startswith("cmp"):
            if ", #" in ins.op_str:
                try:
                    imm = int(ins.op_str.split(", #")[1], 0)
                    cmp_vals.append(imm)
                except Exception:
                    pass

    bl_cnt = Counter(bl_targets)
    cmp_cnt = Counter(cmp_vals)
    print(f"\nTotal BL: {len(bl_targets)} (unique targets: {len(bl_cnt)})")
    print(f"Top 20 BL targets:")
    for t, n in bl_cnt.most_common(20):
        print(f"  BL 0x{t:05x} x{n}")

    print(f"\nTotal immediate cmps: {len(cmp_vals)} (unique values: {len(cmp_cnt)})")
    print(f"Top 30 cmp immediate values:")
    for v, n in cmp_cnt.most_common(30):
        ascii_str = ""
        if 0x20 <= v < 0x7f:
            ascii_str = f" ('{chr(v)}')"
        print(f"  cmp #0x{v:02x}{ascii_str} x{n}")


if __name__ == "__main__":
    main()
