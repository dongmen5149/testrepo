"""ARM Thumb BL 명령어를 binary 전체에서 디코드해서 dispatcher caller 찾기.

Ghidra Function Call Trees 가 incoming 0건이지만, 실제 binary 에는 BL 명령어가
있을 가능성. (Ghidra는 jump table indirect call 로 함수 흐름이 끊긴 경우
caller 추적 실패).

ARM Thumb-2 BL encoding (32-bit, 두 halfword):
  first  : 1111 0 S imm10        (= 0xF000 + S << 10 + imm10)
  second : 1 1 J1 1 J2 imm11      (= 0xD000 + J1<<13 + J2<<11 + imm11)
  imm32 = SignExtend(S : I1 : I2 : imm10 : imm11 : 0)
    I1 = NOT(J1 XOR S), I2 = NOT(J2 XOR S)
  target = (PC + imm32) where PC = addr_of_BL + 4
"""
from __future__ import annotations

import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"

TARGETS = {
    0x0006619C: "FUN_0006619c (caller-of-orchestrator)",
    0x0006619D: "FUN_0006619c (Thumb)",
}


def decode_bl(first: int, second: int, pc: int) -> int | None:
    """If (first, second) form a Thumb-2 BL, return target. Else None."""
    if (first & 0xF800) != 0xF000:
        return None
    if (second & 0xD000) != 0xD000:
        return None
    S = (first >> 10) & 1
    imm10 = first & 0x3FF
    J1 = (second >> 13) & 1
    J2 = (second >> 11) & 1
    imm11 = second & 0x7FF
    I1 = (~(J1 ^ S)) & 1
    I2 = (~(J2 ^ S)) & 1
    imm32 = (S << 24) | (I1 << 23) | (I2 << 22) | (imm10 << 12) | (imm11 << 1)
    if S:
        imm32 |= 0xFF000000
        # to signed
        imm32 = imm32 - 0x100000000
    target = (pc + imm32) & 0xFFFFFFFF
    return target


def decode_blx(first: int, second: int, pc: int) -> int | None:
    """BLX (T2): same as BL but second's bit 12 = 0 → ARM mode (clear LSB)."""
    if (first & 0xF800) != 0xF000:
        return None
    if (second & 0xD001) != 0xC000:
        return None
    S = (first >> 10) & 1
    imm10H = first & 0x3FF
    J1 = (second >> 13) & 1
    J2 = (second >> 11) & 1
    imm10L = (second >> 1) & 0x3FF
    I1 = (~(J1 ^ S)) & 1
    I2 = (~(J2 ^ S)) & 1
    imm32 = (S << 24) | (I1 << 23) | (I2 << 22) | (imm10H << 12) | (imm10L << 2)
    if S:
        imm32 = imm32 - 0x100000000
    target = ((pc & ~3) + imm32) & 0xFFFFFFFF
    return target


def main() -> None:
    data = BIN.read_bytes()
    print(f"binary size: 0x{len(data):x}")

    bl_callers: dict[int, list[tuple[int, str]]] = {t: [] for t in TARGETS}

    # Scan binary as Thumb halfwords
    for off in range(0, len(data) - 4, 2):
        first, second = struct.unpack("<HH", data[off : off + 4])
        pc = off + 4  # PC at instruction = offset + 4 in Thumb
        for decode_fn, kind in [(decode_bl, "BL"), (decode_blx, "BLX")]:
            target = decode_fn(first, second, pc)
            if target is None:
                continue
            # Check if target matches any of our addresses (with or without LSB)
            for t in TARGETS:
                if target == t or target == (t & ~1):
                    bl_callers.setdefault(t, []).append((off, kind))

    print()
    for target, hits in bl_callers.items():
        if hits:
            print(f"  {target:#010x} ({TARGETS[target]}): {len(hits)} caller(s)")
            for off, kind in hits[:10]:
                print(f"    {kind} @ 0x{off:08x}  →  0x{target:08x}")

    total = sum(len(v) for v in bl_callers.values())
    if total == 0:
        print("  no BL/BLX callers found for any target.")
        print()
        print("  → caller is via indirect call (function pointer table).")
    print()


if __name__ == "__main__":
    main()
