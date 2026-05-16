"""Decode the 74-entry inner JT inside opcode 0x12 at 0x90200 dispatch.

Round 38 / 2EA: standard Hero3 SL-relative JT — entries follow the literal at
ldr r3, [pc, #0x2fc] (= 0x90210 + 4 + 0x2fc & ~3 = 0x90510).
"""
import struct
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()

    # ldr r3, [pc, #0x2fc] at 0x90210 — pc is 0x90212+2 = 0x90214, then ALIGN(pc,4) = 0x90214, +0x2fc = 0x90510
    # We need to align(pc+4, 4)+offset; for Thumb-2 ldr [pc, #imm], pc = (curr_pc + 4) & ~3
    # Let me extract the literals at 0x90510 and 0x90518
    for lit_addr in (0x90510, 0x90514, 0x90518, 0x9051c, 0x90520):
        val = struct.unpack("<I", data[lit_addr:lit_addr+4])[0]
        print(f"  literal @ 0x{lit_addr:08x} = 0x{val:08x}")

    # The 'I' bound is 0x49 = 73 decimal, so JT has 0x4a = 74 entries.
    # Determine JT base: it's at sl + literal_at_0x90210
    # And entries are at JT_base + index*4, each pointing to (sl + JT_entry)
    # We don't know sl statically — but standard pattern: sl is set to a binary-relative anchor.
    # The first literal (at 0x90510) should be the JT_base offset relative to sl
    # The second literal (at 0x90518) should be the code-base offset relative to sl
    #
    # From Round 36 we know FUN_0008e89e outer JT is at 0xabc68 and uses sl-relative addressing.
    # By inspection, the literals at 0x90510 / 0x90518 should encode where the JT lives.

    # Let's try common candidate JT bases by scanning a region for 74 valid Hero3-internal offsets
    # FUN_0008e89e range = 0x8e89e..0x929e8. JT entries are offsets to be added to code base.
    print("\n=== Scanning for 74-entry JT base inside FUN_0008e89e ===")
    candidates = []
    for off in range(0x8E89E, 0x929E8 - 74 * 4, 4):
        valid = 0
        for i in range(74):
            rel = struct.unpack("<i", data[off + i*4:off + i*4 + 4])[0]
            # Estimate: if entry magnitude < 0x40000 (256KB), it likely fits as a code-base relative offset
            if -0x100000 < rel < 0x100000:
                valid += 1
            else:
                break
        if valid >= 60:
            candidates.append((off, valid))
    print(f"  found {len(candidates)} candidate bases (≥60 valid entries)")
    for c, v in candidates[:5]:
        print(f"  0x{c:08x}: {v}/74 entries pass magnitude check")

    # Also check region near 0xabc68 (outer JT) for an adjacent 74-entry JT
    print("\n=== Try candidate JT bases adjacent to 0xabc68 (outer SCN JT) ===")
    for base in (0xABCB4, 0xABCB8, 0xABCBC, 0xABCC0, 0xABCC4, 0xABCC8, 0xABE00, 0xABE08, 0xAC000):
        print(f"\n--- JT @ 0x{base:08x} (74 entries) ---")
        dests = {}
        for i in range(min(74, (len(data) - base) // 4)):
            rel = struct.unpack("<i", data[base + i*4:base + i*4 + 4])[0]
            # Try interpreting as code-base relative offset (offset directly to FUN_0008e89e somewhere)
            abs_t = (base + rel) & 0xFFFFFFFF
            dests.setdefault(abs_t, []).append(i)
        in_func = sum(1 for d in dests if 0x8e89e <= d <= 0x929e8)
        print(f"  destinations in FUN_0008e89e range: {in_func}/{len(dests)}")
        if in_func >= 30:
            for d, cases in sorted(dests.items())[:10]:
                in_range = "★" if 0x8e89e <= d <= 0x929e8 else " "
                print(f"  {in_range} 0x{d:08x}: cases {cases[:5]}{'...' if len(cases) > 5 else ''}")


if __name__ == "__main__":
    main()
