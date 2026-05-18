"""Round 54 / 2UD: FUN_0009ada4 (FUN_9a008 mode 2 sub-leaf) prologue + cmp/BL/literal 통계.

task[+0x9bb4] dominant reader (41 reads in this function alone). 가설: 캐릭터 status effect 엔진.

Note: FUN_9ada4 는 FUN_9a008 (0x9a008..0x9c280) 영역 내부 — Ghidra 가 별도 entry 로 인식하지만
실제는 mode 2 sub-JT 의 한 opcode leaf.
"""
import struct
from pathlib import Path
from collections import Counter
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    start, end = 0x9ada4, 0x9ada4 + 0x1500  # 5340B size cap

    print(f"=== FUN_9ada4 prologue (first 60 instr) ===")
    count = 0
    for ins in md.disasm(DATA[start:start + 240], start):
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
        if count >= 60:
            break

    print("\n=== Full FUN_9ada4 stats ===")
    bls, cmps, lits = [], [], []
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
        elif ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                pc = (ins.address + 4) & ~3
                lit_addr = pc + imm
                if lit_addr + 4 <= len(DATA):
                    lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                    lits.append(lit)
            except Exception:
                pass

    bl_cnt = Counter(bls)
    cmp_cnt = Counter(cmps)
    lit_cnt = Counter(lits)

    print(f"\nTotal BL: {len(bls)} (unique: {len(bl_cnt)})")
    print(f"Top 15 BL targets:")
    for t, n in bl_cnt.most_common(15):
        print(f"  BL 0x{t:05x} x{n}")

    print(f"\nTotal cmp #imm: {len(cmps)} (unique: {len(cmp_cnt)})")
    print(f"Top 25 cmp values:")
    for v, n in cmp_cnt.most_common(25):
        ascii_str = f" ('{chr(v)}')" if 0x20 <= v < 0x7f else ""
        print(f"  cmp #0x{v:02x} (={v}){ascii_str} x{n}")

    print(f"\nTop 20 PC-rel literals (≥ 2 refs):")
    for lit, n in lit_cnt.most_common(40):
        if n >= 2:
            # Interpret if it could be task_struct offset, GOT offset, or PIC base
            note = ""
            if 0xb2c40 <= lit <= 0xb2c40 + 0x4000:
                note = " (GOT region)"
            elif 0x8000 <= lit <= 0xc000:
                note = " (likely task_struct offset)"
            elif lit & 0xffff0000 == 0xffff0000:
                note = " (sl-rel offset, GOT slot)"
            print(f"  LIT 0x{lit:08x}{note} x{n}")


if __name__ == "__main__":
    main()
