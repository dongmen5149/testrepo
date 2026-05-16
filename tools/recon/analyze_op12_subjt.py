"""Locate inline JT(s) inside opcode 0x12 — sub-dispatcher for the 13 inner opcodes.

Round 38 / 2EA: 0x90e38 (cmp #0xc bls 0x90e78) + 0x9131c (cmp #0xc bhi 0x91390)
suggest an internal 13-entry JT immediately after each gate.
"""
import struct
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")


def show_region(data: bytes, base: int, count: int = 13) -> None:
    """Try interpreting `count` 4-byte signed offsets as inline JT entries."""
    print(f"\n=== Trying JT @ 0x{base:08x} ({count} entries × 4 bytes = {count*4} bytes) ===")
    dests: dict[int, list[int]] = {}
    for i in range(count):
        off = base + i * 4
        if off + 4 > len(data):
            break
        rel = struct.unpack("<i", data[off:off+4])[0]
        abs_t = (base + rel) & 0xFFFFFFFF
        dests.setdefault(abs_t, []).append(i)
        print(f"  case={i:2}: rel=0x{rel:08x}  -> 0x{abs_t:08x}")
    print(f"unique dests: {len(dests)}")
    for d, cases in sorted(dests.items()):
        print(f"  0x{d:08x} : cases {cases}")


def find_jt_after(data: bytes, gate_addr: int, search_window: int = 0x80) -> None:
    """Heuristic: scan addresses near gate_addr for a 4-byte-aligned candidate JT base.

    JT entries in this binary are signed 32-bit relative offsets (each in range that lands within FUN_0008e89e = 0x8e89e..0x929e8).
    """
    print(f"\n=== scanning for JT near 0x{gate_addr:08x} (window ±0x{search_window:x}) ===")
    candidates = []
    for off in range(gate_addr, gate_addr + search_window, 2):
        if off + 16 > len(data):
            break
        # Check 4 consecutive 4-byte offsets — if they all land inside FUN_0008e89e, it's likely JT
        in_range_count = 0
        for i in range(4):
            rel = struct.unpack("<i", data[off + i*4:off + i*4 + 4])[0]
            abs_t = (off + rel) & 0xFFFFFFFF
            if 0x8e89e <= abs_t <= 0x929e8:
                in_range_count += 1
        if in_range_count >= 3:
            candidates.append(off)
    print(f"  candidates: {[f'0x{c:08x}' for c in candidates[:10]]}")


def main() -> None:
    data = BIN.read_bytes()
    # Two suspected gates: 0x90e38 (cmp 0xc bls 0x90e78) and 0x9131c (cmp 0xc bhi 0x91390)
    # The branch goes either INTO the JT-driven dispatch or OVER it.
    # 'bls' means "if r3 <= 0xc, branch to 0x90e78" → 0x90e78 is the dispatch path (likely starts with `tbb` or table read)
    # 'bhi' means "if r3 > 0xc, branch to 0x91390" → so the fall-through (r3 <= 0xc) at 0x9131c+2 onwards is the dispatch
    for gate_name, gate_dest in [
        ("gate1 cmp#0xc bls → 0x90e78", 0x90E78),
        ("gate2 cmp#0xc bhi over → 0x91320 fall-through", 0x91320),
    ]:
        find_jt_after(data, gate_dest, 0x80)

    # Try common JT bases right after the branches
    # First gate destination 0x90e78 — if it's a load+jump pattern, jt is usually adjacent (8~16 bytes after)
    for base in (0x90E78, 0x90E80, 0x90E84, 0x90E90, 0x91320, 0x9132C, 0x9133C):
        show_region(data, base, 13)


if __name__ == "__main__":
    main()
