"""§4.4 dispatcher caller 자동 추적.

scn_dispatch_evt @ 0x8e112 의 incoming caller 를 Ghidra 가 추적 못함 (PIC).
raw binary 에서 다음 패턴들을 검색:

  1. 직접 주소: 0x0008e112, 0x0008e113 (Thumb LSB+1), 0x0008e89e, 0x0008e89f
  2. GOT-relative offset: target - GOT_BASE
     - 0x8e113 - 0xb2c40 = 0xffffdb4d3 (signed)
     - 0x8e89f - 0xb2c40 = 0xffffdbc5f
"""
from __future__ import annotations

import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
GOT_BASE = 0x000B2C40


def to_signed_32(v: int) -> int:
    return v - 0x100000000 if v >= 0x80000000 else v


def search_pattern(data: bytes, pattern: bytes, label: str) -> list[int]:
    hits = []
    i = 0
    while True:
        i = data.find(pattern, i)
        if i < 0:
            break
        hits.append(i)
        i += 1
    print(f"  {label} ({pattern.hex()}): {len(hits)} hits")
    if hits:
        for h in hits[:20]:
            print(f"    @ 0x{h:08x}")
    return hits


def main() -> None:
    data = BIN.read_bytes()
    print(f"binary size: 0x{len(data):x}")
    print()

    targets = [
        ("0x8e112", 0x0008e112),
        ("0x8e113 (Thumb)", 0x0008e113),
        ("0x8e89e", 0x0008e89e),
        ("0x8e89f (Thumb)", 0x0008e89f),
    ]

    print("=== absolute address pattern (4-byte LE) ===")
    for label, addr in targets:
        pat = struct.pack("<I", addr)
        search_pattern(data, pat, f"abs {label}")
    print()

    print("=== GOT-relative offset (target - 0xb2c40) ===")
    for label, addr in targets:
        offset = (addr - GOT_BASE) & 0xFFFFFFFF
        pat = struct.pack("<I", offset)
        search_pattern(data, pat, f"got_rel {label}  (={offset:#010x})")
    print()

    # Also search for Thumb BL instruction encoding to 0x8e112 / 0x8e89e:
    # BL (T1 encoding) is two halfwords. Searching directly is complex; skip for now.
    # Indicate: if no hits above, caller likely uses computed call (table lookup)


if __name__ == "__main__":
    main()
