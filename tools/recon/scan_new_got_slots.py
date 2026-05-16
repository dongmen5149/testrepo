"""Wide-scan for usage of the newly identified GOT slots (Round 42).

Round 42 / 2IA: GOT[+0x78], GOT[+0x140], GOT[+0x160] = 3 new slot offsets.
Scan for the literal values (which appear in PIC pcrel literal pools) to estimate
system-wide usage.

Also recheck the 9 known slots for baseline (Round 33).
"""
from collections import Counter
from pathlib import Path
import struct

BIN = Path("work/h3/extracted/client.bin64000")

# Known GOT slots (Round 33) + new from Round 42
SLOTS = {
    0x18:  "ObjectB ptr (Round 21+33)",
    0x16c: "alt task_struct ptr (Round 23)",
    0x29e: "small flag (Round 22)",
    0x128: "secondary state ptr (Round 22)",
    0x444: "task_ptr (Round 22)",
    0x44c: "ObjectA ptr (Round 20)",
    0xd00: "StorageCell ptr (Round 22)",
    0xd04: "ObjectA helper data #1 (Round 22)",
    0xd08: "ObjectA helper data #2 (Round 22)",
    0xd1c: "ObjectA helper cluster (Round 25)",
    # Round 42 신규
    0x78:  "ObjectE ptr (Round 42 NEW)",
    0x140: "ObjectE pending flag ptr (Round 42 NEW)",
    0x160: "ObjectB pending flag ptr (Round 42 NEW)",
}


def main() -> None:
    data = BIN.read_bytes()
    # Scan 4-byte aligned literal values
    counts: Counter[int] = Counter()
    sites: dict[int, list[int]] = {k: [] for k in SLOTS}
    for off in range(0, len(data) - 4, 4):
        val = struct.unpack("<I", data[off:off+4])[0]
        if val in SLOTS:
            counts[val] += 1
            sites[val].append(off)

    print("=== GOT slot literal occurrence counts (binary-wide) ===")
    print(f"{'slot':>10}  count  description")
    for offset, desc in sorted(SLOTS.items()):
        print(f"  GOT[+0x{offset:x}]  {counts[offset]:5}  {desc}")

    print()
    print("=== Sample literal sites for new slots ===")
    for offset, desc in sorted(SLOTS.items()):
        if offset not in (0x78, 0x140, 0x160):
            continue
        sample = ", ".join(f"0x{s:08x}" for s in sites[offset][:10])
        print(f"  GOT[+0x{offset:x}] ({desc}):")
        print(f"    {sample}")


if __name__ == "__main__":
    main()
