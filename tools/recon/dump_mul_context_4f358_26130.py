"""Round 55 / 2VD: FUN_4f358 와 FUN_26130 의 mul/asrs/cmp 컨텍스트 dump.

FUN_4f358: 10 mul, 34 asrs, 64 subs, 12 cmp — asrs 비율 높음 (signed division 패턴)
FUN_26130: 14 mul, 55 subs, 12 cmp — cmp 12회 = 범위 검사 다수
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def dump_contexts(start: int, size: int, label: str, focus_mnemonics: set[str]) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    end = start + size
    insns = list(md.disasm(DATA[start:end], start))
    print(f"\n========== {label} ==========")

    seen_ctx = set()  # avoid duplicate adjacent windows
    for i, ins in enumerate(insns):
        if ins.mnemonic in focus_mnemonics:
            window_id = i // 4  # group neighboring focus instructions
            if window_id in seen_ctx:
                continue
            seen_ctx.add(window_id)
            print(f"\n  --- {ins.mnemonic} @ 0x{ins.address:05x}: {ins.op_str} ---")
            for j in range(max(0, i - 2), min(i + 3, len(insns))):
                marker = "  ★" if j == i else "   "
                ins2 = insns[j]
                op_str = ins2.op_str
                if ins2.mnemonic == "ldr" and "[pc" in op_str:
                    try:
                        imm = int(op_str.split("#")[1].rstrip("]"), 0)
                        pc = (ins2.address + 4) & ~3
                        lit_addr = pc + imm
                        if lit_addr + 4 <= len(DATA):
                            lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                            op_str = f"{op_str}  <LIT=0x{lit:x}>"
                    except Exception:
                        pass
                print(f"  {marker}0x{ins2.address:05x}: {ins2.mnemonic:8} {op_str}")


def main() -> None:
    # FUN_4f358: focus on muls + immediate cmps + asrs
    dump_contexts(0x4f358, 896, "FUN_4f358 (mul context)", {"muls", "mul"})
    dump_contexts(0x4f358, 896, "FUN_4f358 (asrs context, first 10)", {"asrs"})
    # FUN_26130: focus on muls + cmp
    dump_contexts(0x26130, 784, "FUN_26130 (mul context)", {"muls", "mul"})


if __name__ == "__main__":
    main()
