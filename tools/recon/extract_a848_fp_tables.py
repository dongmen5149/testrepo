"""Round 48 / 2OD-2: FUN_85edc/85fc8 의 sl-rel function pointer table 주소 추출.

각 `ldr r3, [pc, #N]; add r3, sl; ldr r3, [r3]` 패턴 → GOT-relative slot 추적.
slot = sl + literal[pc+N]; *slot = function pointer table base.

GOT base = sl = 0xb2c40 (Round 42 확정).
"""
import struct
from pathlib import Path

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40

# (ldr_addr, pc_imm) pairs from FUN_85edc and FUN_85fc8
LDR_SITES = [
    (0x85ee6, 0xc8, "FUN_85edc GOT-base setup"),  # ldr r3, [pc, #0xc8]; mov sl, r3; add sl, pc
    (0x85f4e, 0x70, "FUN_85edc func_table_1 base @ byte1 dispatch"),
    (0x85f7a, 0x48, "FUN_85edc func_table_2 base @ byte2 dispatch"),
    (0x85fd2, 0x60, "FUN_85fc8 GOT-base setup"),
    (0x85fdc, 0x58, "FUN_85fc8 func_table_2 base @ byte2 dispatch"),
    (0x86008, 0x30, "FUN_85fc8 func_table_1 base @ byte1 dispatch"),
]


def resolve_pc_relative(ldr_addr: int, imm: int) -> int:
    pc = (ldr_addr + 4) & ~3
    return pc + imm


def main() -> None:
    for ldr_addr, imm, label in LDR_SITES:
        lit_addr = resolve_pc_relative(ldr_addr, imm)
        if lit_addr + 4 > len(DATA):
            print(f"  0x{ldr_addr:05x} +0x{imm:x}: OOR")
            continue
        lit_val = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
        # sl-rel: sl_base + lit_val = GOT entry address
        # The literal here is `lit_val + pc(after add sl, pc)` — but since we're already
        # past the GOT-base setup, the literal is a GOT offset.
        # For GOT-base setup: literal points to GOT base PC-rel offset
        # For dispatch site: literal is GOT slot offset (small value)
        print(f"\n  Site 0x{ldr_addr:05x} ldr r3, [pc, #0x{imm:x}]:")
        print(f"    literal @ 0x{lit_addr:05x} = 0x{lit_val:08x}")
        print(f"    {label}")
        # For dispatch sites: GOT-slot offset is relative to sl (which was set to GOT base)
        # Effective addr: sl + lit_val
        if lit_val < 0x10000:
            slot_addr = GOT_BASE + lit_val
            if slot_addr + 4 <= len(DATA):
                slot_val = struct.unpack("<I", DATA[slot_addr:slot_addr + 4])[0]
                print(f"    GOT[+0x{lit_val:x}] @ 0x{slot_addr:05x} = 0x{slot_val:08x}")


if __name__ == "__main__":
    main()
