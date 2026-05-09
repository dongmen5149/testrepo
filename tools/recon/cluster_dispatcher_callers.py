"""dispatcher caller (376+213건) 를 caller 함수 단위로 클러스터링.

각 BL 위치 → 포함하는 함수 식별 → 함수별 caller 카운트.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
SRC = REPO / "work" / "ghidra_out" / "all_decompiled.c"

DISPATCHERS = {
    0x0003ECFC: "dispatcher_1 (jt 0xa9cc4)",
    0x0003F710: "dispatcher_2 (jt 0xa9d70)",
}

# Cache: (start_addr, end_addr, name) for all functions
def parse_function_addrs() -> list[tuple[int, str]]:
    """Return [(addr, name)] sorted by addr from all_decompiled.c."""
    text = SRC.read_text(encoding="utf-8", errors="replace")
    pat = re.compile(r"^[\w\s\*]+\s(FUN_([0-9a-fA-F]+)|UndefinedFunction_([0-9a-fA-F]+))\s*\(", re.MULTILINE)
    funcs = []
    for m in pat.finditer(text):
        addr_str = m.group(2) or m.group(3)
        addr = int(addr_str, 16)
        funcs.append((addr, f"FUN_{addr:08x}"))
    funcs = sorted(set(funcs))
    return funcs


def find_containing_func(addr: int, funcs: list[tuple[int, str]]) -> str:
    """Binary search for largest func_addr <= addr."""
    lo, hi = 0, len(funcs)
    while lo < hi:
        mid = (lo + hi) // 2
        if funcs[mid][0] <= addr:
            lo = mid + 1
        else:
            hi = mid
    if lo == 0:
        return "?"
    return funcs[lo - 1][1]


def decode_bl(first: int, second: int, pc: int) -> int | None:
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
        imm32 = imm32 - 0x100000000
    return (pc + imm32) & 0xFFFFFFFF


def main() -> None:
    data = BIN.read_bytes()
    funcs = parse_function_addrs()
    print(f"functions in decompiled output: {len(funcs)}")
    print()

    for target, label in DISPATCHERS.items():
        print(f"=== {label} (0x{target:08x}) ===")
        bl_callers: list[int] = []
        for off in range(0, len(data) - 4, 2):
            first, second = struct.unpack("<HH", data[off : off + 4])
            t = decode_bl(first, second, off + 4)
            if t is None:
                continue
            if t == target or t == target | 1:
                bl_callers.append(off)
        # cluster by containing function
        by_func: Counter = Counter()
        for off in bl_callers:
            fn = find_containing_func(off, funcs)
            by_func[fn] += 1
        print(f"  total BL callers: {len(bl_callers)}")
        print(f"  distinct caller functions: {len(by_func)}")
        print()
        print(f"  top 20 caller functions (most BL calls):")
        for fn, cnt in by_func.most_common(20):
            print(f"    {fn}: {cnt} calls")
        print()


if __name__ == "__main__":
    main()
