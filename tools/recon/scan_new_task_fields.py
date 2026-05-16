"""Wide-scan for new task fields discovered in Round 46.

Round 46 / 2MC:
- task[0xa848] (FUN_00085578c getter, 34 callers across binary)
- task[0xa280] (FUN_00092bd0 byte reader, 15 callers)
"""
from collections import Counter
import struct
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")
TARGETS = {
    0xa848: "FUN_00085578c &task getter target (34 callers)",
    0xa280: "FUN_00092bd0 byte reader target (15 callers)",
    # Compare with already-known fields
    0x9c71: "Round 27/45 byte cluster",
    0xa0c0: "NPC subsystem mode (Round 39)",
    0x9cb8: "callback queue base (Round 40)",
}


def main() -> None:
    data = BIN.read_bytes()
    counts: Counter[int] = Counter()
    sites: dict[int, list[int]] = {k: [] for k in TARGETS}
    for off in range(0, len(data) - 4, 4):
        val = struct.unpack("<I", data[off:off+4])[0]
        if val in TARGETS:
            counts[val] += 1
            sites[val].append(off)

    print("=== Task field literal occurrences ===")
    for offset, desc in sorted(TARGETS.items()):
        print(f"  task[0x{offset:x}]: {counts[offset]:4} sites  ({desc})")

    print()
    print("=== Sample sites for new fields ===")
    for offset, desc in [(0xa848, "task[0xa848]"), (0xa280, "task[0xa280]")]:
        sample = ", ".join(f"0x{s:08x}" for s in sites[offset][:10])
        print(f"  {offset}: {sample}")


if __name__ == "__main__":
    main()
