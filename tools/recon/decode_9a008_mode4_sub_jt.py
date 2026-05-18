"""Round 54 / 2UA: FUN_9a008 mode 4 (JT_1[4]) 의 31-entry sub-JT 디코드.

JT_1[4] @ 0x9b7e6:
  0x9b80c: ldr r3, [pc, #0xec] → LIT = 0xffffa3ec (sl-rel)
  cmp r1, #0x1e (=30 max) → 31 entries
sub-JT base = sl + 0xffffa3ec = 0xb2c40 + 0xffffa3ec = 0xad02c

또한 mode 4 의 7 distinct leaf 정체 추정용 첫 10 inst dump.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40


def main() -> None:
    sl_offset = 0xffffa3ec
    jt_base = (GOT_BASE + sl_offset) & 0xFFFFFFFF
    count = 31
    print(f"=== JT_1[4] sub-JT @ 0x{jt_base:05x} (31 entries) ===")
    print()

    seen = {}
    for i in range(count):
        entry_addr = jt_base + i * 4
        entry = struct.unpack("<I", DATA[entry_addr:entry_addr + 4])[0]
        if entry & 0x80000000:
            entry_signed = entry - 0x100000000
        else:
            entry_signed = entry
        target = (jt_base + entry) & 0xFFFFFFFF
        tc = target & ~1
        seen.setdefault(tc, []).append(i)
        in_range = "" if tc < len(DATA) else " (OUT)"
        thumb = "thumb" if (target & 1) else "arm/data"
        print(f"  idx={i:2d}  JT[{i}]@0x{entry_addr:05x}=0x{entry:08x}({entry_signed:+d})  -> 0x{tc:05x} [{thumb}]{in_range}")

    print()
    print(f"=== Distinct targets ({len(seen)}) ===")
    for tgt, idxs in sorted(seen.items()):
        idx_str = ",".join(str(i) for i in idxs)
        in_range = "" if tgt < len(DATA) else " (OUT)"
        print(f"  0x{tgt:05x}{in_range}  ({len(idxs)}x: i={idx_str})")

    print()
    print(f"=== 각 distinct leaf 의 첫 8 inst ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for tgt in sorted(seen.keys()):
        if tgt >= len(DATA):
            continue
        print(f"\n--- leaf @ 0x{tgt:05x} (states {','.join(str(i) for i in seen[tgt])}) ---")
        count_inst = 0
        for ins in md.disasm(DATA[tgt:tgt + 50], tgt):
            marker = ""
            if ins.mnemonic == "bl":
                tok = ins.op_str.strip().lstrip("#")
                try:
                    t = int(tok, 0)
                    marker = f" <BL 0x{t:x}>"
                except Exception:
                    pass
            elif ins.mnemonic.startswith("cmp"):
                marker = " <cmp>"
            elif ins.mnemonic == "ldr" and "[pc" in ins.op_str:
                try:
                    imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                    pc = (ins.address + 4) & ~3
                    lit_addr = pc + imm
                    lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                    marker = f" <LIT=0x{lit:x}>"
                except Exception:
                    pass
            print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
            count_inst += 1
            if count_inst >= 8:
                break


if __name__ == "__main__":
    main()
