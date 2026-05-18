"""Round 54 / 2UD: 전투 시스템 후보 함수 본문 (prologue + stats).

task[+0x9c70] (party member array @ 60B stride) 의 top readers:
  - FUN_3a028 (500B, 8 reads) ★
  - FUN_630e8 (3936B, 4 reads) ★ — 큰 함수
  - FUN_88a30 (1152B, 2 reads)

각 함수의 prologue 50 inst + 전체 cmp/BL 통계 → 전투 패턴 검색.
"""
import struct
from pathlib import Path
from collections import Counter
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def dump_function(start: int, end: int, label: str) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print(f"\n========== {label} @ 0x{start:05x}..0x{end:05x} ({end - start}B) ==========")
    print(f"\n=== prologue (first 40 instr) ===")
    count = 0
    for ins in md.disasm(DATA[start:start + 160], start):
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
                if lit_addr + 4 <= len(DATA):
                    lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                    marker = f"  <LIT=0x{lit:x}>"
            except Exception:
                pass
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
        count += 1
        if count >= 40:
            break

    print(f"\n=== Full {label} stats ===")
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

    print(f"Total BL: {len(bls)} (unique: {len(bl_cnt)})")
    print(f"Top 10 BL targets:")
    for t, n in bl_cnt.most_common(10):
        print(f"  BL 0x{t:05x} x{n}")
    print(f"Total cmp #imm: {len(cmps)} (unique: {len(cmp_cnt)})")
    print(f"Top 15 cmp values:")
    for v, n in cmp_cnt.most_common(15):
        ascii_str = f" ('{chr(v)}')" if 0x20 <= v < 0x7f else ""
        print(f"  cmp #0x{v:02x} (={v}){ascii_str} x{n}")
    print(f"Top 10 PC-rel literals (≥ 3 refs, looks like task field offsets):")
    for lit, n in lit_cnt.most_common(50):
        if n >= 3 and 0x100 <= lit <= 0xc000:
            print(f"  LIT 0x{lit:08x} x{n}")


def main() -> None:
    dump_function(0x3a028, 0x3a21c, "FUN_3a028 (500B, 8x task[+0x9c70])")
    dump_function(0x630e8, 0x64048, "FUN_630e8 (3936B, 4x task[+0x9c70])")
    dump_function(0x88a30, 0x88eb0, "FUN_88a30 (1152B, 2x task[+0x9c70])")


if __name__ == "__main__":
    main()
