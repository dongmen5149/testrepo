"""Verify 3 candidate indirect entry functions found in Round 42.

Round 43 / 2JA: candidates 0x28ada, 0x28de8, 0x424c2 had no push prologue within 0x800
backwards. Extend search to 0x4000 (= 16KB) and check BL caller count.

A true indirect entry function:
  - has push prologue within reasonable range
  - has 0 BL callers (only invoked via indirect call through GVM firmware)
"""
import struct
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")


def find_push_before(data: bytes, target: int, max_back: int = 0x4000) -> int | None:
    """Search backwards for first Thumb push prologue or function-boundary marker."""
    for off in range(target, max(0, target - max_back), -2):
        if off + 2 > len(data):
            continue
        w = int.from_bytes(data[off:off+2], "little")
        # Thumb-1 push {..., lr}
        if 0xB500 <= w <= 0xB5FF:
            return off
        # Thumb-2 push (T2 encoding)
        if w == 0xE92D:
            return off
    return None


def thumb_bl_callers(data: bytes, target: int) -> list[int]:
    """Return all BL caller addresses that target this address."""
    callers = []
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
            caller_pc = i + 4
            t = (caller_pc + imm32) & 0xFFFFFFFF
            if t == target:
                callers.append(i)
    return callers


def main() -> None:
    data = BIN.read_bytes()
    candidates = [
        ("0x28ada (event trigger site)", 0x28ADA),
        ("0x28de8 (event trigger site)", 0x28DE8),
        ("0x424c2 (event trigger site)", 0x424C2),
    ]
    for label, addr in candidates:
        print(f"\n=== {label} ===")
        # Extended push prologue search
        push_addr = find_push_before(data, addr, 0x4000)
        if push_addr is None:
            print(f"  NO push within 0x4000 backwards — likely indirect-only entry")
        else:
            offset = addr - push_addr
            print(f"  push @ 0x{push_addr:08x} (offset +0x{offset:x}, {offset} bytes)")
            # Check BL callers for the containing function
            callers = thumb_bl_callers(data, push_addr)
            print(f"  {len(callers)} BL callers for func 0x{push_addr:08x}:")
            for c in callers[:10]:
                print(f"    caller @ 0x{c:08x}")
            if len(callers) == 0:
                print(f"  ⭐ 0 BL callers = likely INDIRECT-ONLY ENTRY FUNCTION!")


if __name__ == "__main__":
    main()
