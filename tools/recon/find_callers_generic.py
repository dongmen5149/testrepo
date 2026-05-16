"""Generic BL caller lookup tool — given any target addresses, find their direct callers.

Round 38 / 2EC helper extending find_callers_41c14.py.
"""
import struct
import sys
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")


def thumb_bl_targets(data: bytes) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for i in range(0, len(data) - 4, 2):
        w1 = int.from_bytes(data[i:i + 2], "little")
        w2 = int.from_bytes(data[i + 2:i + 4], "little")
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
            caller_pc = i + 4
            target = (caller_pc + imm32) & 0xFFFFFFFF
            out.setdefault(target, []).append(i)
    return out


def main() -> None:
    data = BIN.read_bytes()
    targets = thumb_bl_targets(data)
    for addr_hex in sys.argv[1:]:
        addr = int(addr_hex, 16)
        callers = targets.get(addr, [])
        print(f"0x{addr:08x}: {len(callers)} BL caller(s)")
        for c in callers[:30]:
            print(f"  caller @ 0x{c:08x}")


if __name__ == "__main__":
    main()
