"""Find direct BL callers of FUN_00041c14 / FUN_00041c6e.

Round 37 / 2DQ: identify what invokes the cluster #1 state-machine processor."""
import struct
from pathlib import Path

BIN_PATH = Path("work/h3/extracted/client.bin64000")


def thumb_bl_targets(data: bytes) -> dict[int, list[int]]:
    """Scan all 32-bit Thumb-2 BL instructions and return target -> [caller_addr...]."""
    out: dict[int, list[int]] = {}
    # BL encoding: 1111 0Sii iiii iiii  1111 1jJj iiii iiii (J1 = bit13, J2 = bit11)
    for i in range(0, len(data) - 4, 2):
        w1 = int.from_bytes(data[i:i+2], "little")
        w2 = int.from_bytes(data[i+2:i+4], "little")
        if (w1 & 0xF800) == 0xF000 and (w2 & 0xD000) == 0xD000:
            s = (w1 >> 10) & 1
            imm10 = w1 & 0x3FF
            j1 = (w2 >> 13) & 1
            j2 = (w2 >> 11) & 1
            imm11 = w2 & 0x7FF
            i1 = 1 ^ j1 ^ s
            i2 = 1 ^ j2 ^ s
            imm32 = (s << 24) | (i1 << 23) | (i2 << 22) | (imm10 << 12) | (imm11 << 1)
            if s:
                imm32 |= 0xFF000000
                imm32 = imm32 - (1 << 32)
            # Caller PC = i + 4 (next instr)
            caller_pc = i + 4
            target = (caller_pc + imm32) & 0xFFFFFFFF
            out.setdefault(target, []).append(i)
    return out


def main() -> None:
    data = BIN_PATH.read_bytes()
    targets = thumb_bl_targets(data)
    for label_name, addr in [
        ("FUN_00041c14", 0x41C14),
        ("FUN_00041c6e (sub-label)", 0x41C6E),
        ("FUN_00041c6e | even", 0x41C6E & ~1),
        ("FUN_00041c14 | thumb", 0x41C14 | 1),
        ("FUN_00041c6e | thumb", 0x41C6E | 1),
        ("FUN_00040fb0 (parent state runner)", 0x40FB0),
        ("FUN_00040fb0 | even", 0x40FB0 & ~1),
        ("FUN_00098904 (op12 dispatcher)", 0x98904),
    ]:
        callers = targets.get(addr, [])
        print(f"{label_name} @ 0x{addr:08x}: {len(callers)} BL caller(s)")
        for c in callers[:20]:
            print(f"  caller @ 0x{c:08x}")

    # Also check the neighboring FUN_00042758 (init) for callers
    for label_name, addr in [
        ("FUN_00042758 (entity init)", 0x42758),
        ("FUN_00042758 | thumb", 0x42758 | 1),
    ]:
        callers = targets.get(addr, [])
        print(f"{label_name} @ 0x{addr:08x}: {len(callers)} BL caller(s)")
        for c in callers[:10]:
            print(f"  caller @ 0x{c:08x}")


if __name__ == "__main__":
    main()
