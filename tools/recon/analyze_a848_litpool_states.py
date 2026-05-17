"""Round 48 / 2OA-3: literal pool 기반 state ID 값 추출.

이전 분석에서 일부 BL@FUN_85578c 사이트는 `ldr r2, [pc, #N]` 패턴.
PC-relative literal load 의 word 값을 디코딩 → state ID 추가 후보.
"""
import struct
from pathlib import Path

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

# (ldr_addr, pc_imm) pairs from previous analyze_a848_state_values output
LDR_SITES = [
    (0x85b22, 0x350),
    (0x87c50, 0x78),
    (0x88eba, 0x6c),
    (0x89b22, 0x34c),
    (0x8a05a, 0x6c),
    (0x905ae, 0x364),
]


def resolve_pc_relative(ldr_addr: int, imm: int) -> int:
    """Thumb LDR pc-relative: pc = align(ldr_addr + 4, 4)."""
    pc = (ldr_addr + 4) & ~3
    return pc + imm


def main() -> None:
    for ldr_addr, imm in LDR_SITES:
        lit_addr = resolve_pc_relative(ldr_addr, imm)
        if lit_addr + 4 > len(DATA):
            print(f"  0x{ldr_addr:05x} ldr r2, [pc, #0x{imm:x}] -> 0x{lit_addr:05x} OUT OF RANGE")
            continue
        val = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
        print(f"  0x{ldr_addr:05x} ldr r2, [pc, #0x{imm:x}] -> literal @0x{lit_addr:05x} = 0x{val:08x} ({val} / {val & 0xFFFF}/{val >> 16})")


if __name__ == "__main__":
    main()
