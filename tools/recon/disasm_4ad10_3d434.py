"""Round 51 / 2RA: FUN_818f0 의 두 핵심 helper (FUN_4ad10, FUN_3d434) 본문.

FUN_4ad10: 모든 8개 handler 가 처음에 호출하여 state-context ptr 을 받음.
FUN_3d434: arg=-16 / -5 handler 에서 추가 호출 (input event 처리).

각 본문 첫 120B + 모든 BL/literal 추출.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def dump(start: int, size: int, label: str) -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print(f"\n=== {label} @ 0x{start:05x} (first {size}B) ===")
    bls = 0
    for ins in md.disasm(DATA[start:start + size], start):
        marker = ""
        if ins.mnemonic == "bl":
            bls += 1
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                marker = f"  <BL 0x{t:x}>"
            except Exception:
                marker = "  <BL>"
        elif ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            # Resolve PC-rel
            try:
                imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                pc = (ins.address + 4) & ~3
                lit_addr = pc + imm
                lit = int.from_bytes(DATA[lit_addr:lit_addr+4], "little")
                marker = f"  <LIT@0x{lit_addr:05x} = 0x{lit:08x}>"
            except Exception:
                pass
        elif ins.mnemonic in ("bx", "mov") and "lr" in ins.op_str:
            marker = "  <RET>"
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
    print(f"  -- total BL: {bls}")


def main() -> None:
    dump(0x4ad10, 80, "FUN_4ad10")
    dump(0x3d434, 200, "FUN_3d434")


if __name__ == "__main__":
    main()
