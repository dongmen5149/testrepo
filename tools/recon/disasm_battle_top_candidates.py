"""Round 55 / 2VD: arith-heavy top 후보 5개 prologue + key literal dump.

Round 55 arith-heavy grep top candidates:
  - FUN_95408 (1208B, 34 mul, 96 subs) ★ TOP
  - FUN_95a64  (988B, 26 mul, 80 subs) ★ 인접
  - FUN_4de34  (632B, 21 mul, 44 subs)
  - FUN_26130  (784B, 14 mul, 55 subs, 12 cmp)
  - FUN_47814  (436B, 13 mul, 14 cmp)
  - FUN_4f358  (896B, 10 mul, 34 asrs, 64 subs, 12 cmp)

각 후보의 prologue 30 inst + 첫 5 cmp + 신규 literal (task field offsets) 추출.
"""
import struct
from pathlib import Path
from collections import Counter
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def dump_candidate(start: int, size: int, label: str) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    end = start + size
    print(f"\n========== {label} @ 0x{start:05x}..0x{end:05x} ({size}B) ==========")
    print(f"\n=== prologue (30 instr) ===")
    count = 0
    for ins in md.disasm(DATA[start:start + 120], start):
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
        elif ins.mnemonic in ("muls", "mul"):
            marker = f"  ★MUL"
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
        count += 1
        if count >= 30:
            break

    # Full body literal scan
    lits = []
    for ins in md.disasm(DATA[start:end], start):
        if ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                pc = (ins.address + 4) & ~3
                lit_addr = pc + imm
                if lit_addr + 4 <= len(DATA):
                    lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                    lits.append(lit)
            except Exception:
                pass
    lit_cnt = Counter(lits)
    print(f"\nTop literals (≥2 refs):")
    for v, n in lit_cnt.most_common(15):
        if n >= 2:
            note = ""
            if 0x100 <= v <= 0xc000:
                note = " ★ task_struct offset?"
            elif 0xffff0000 == (v & 0xffff0000):
                note = " (sl-rel GOT slot)"
            elif v < len(DATA):
                note = " (binary addr)"
            print(f"  LIT 0x{v:08x} x{n}{note}")


def main() -> None:
    CANDIDATES = [
        (0x95408, 1208, "FUN_95408 (34 mul, 96 subs, 4 BL)"),
        (0x95a64,  988, "FUN_95a64 (26 mul, 80 subs, 2 BL)"),
        (0x4de34,  632, "FUN_4de34 (21 mul, 44 subs, 2 BL)"),
        (0x26130,  784, "FUN_26130 (14 mul, 55 subs, 12 cmp)"),
        (0x4f358,  896, "FUN_4f358 (10 mul, 34 asrs, 64 subs)"),
        (0x47814,  436, "FUN_47814 (13 mul, 14 cmp)"),
    ]
    for addr, size, label in CANDIDATES:
        dump_candidate(addr, size, label)


if __name__ == "__main__":
    main()
