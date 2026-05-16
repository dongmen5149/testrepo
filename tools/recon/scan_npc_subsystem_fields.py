"""Wide-scan for task_struct fields used by the NPC subsystem (Round 40).

Round 41 / 2HF: count PC-relative LDR sites referencing the following NPC-subsystem fields:
- 0x0a5d: callback gate (FUN_00041a68 reads)
- 0x02b8: callback gate 2 (= 0xae << 2)
- 0xa0c0: subsystem mode byte (FUN_000245fc dispatch)
- 0xa1f6: mode 7 gate
- 0xa288, 0xa289: NPC index pair (mode 7 query results)
- 0x290: last_event_id storage (FUN_0002c6a4 tail)

Strategy: scan all 4-byte aligned literals in the binary for these specific values.
Then map back to the PC-relative LDR site at literal_addr-N (need careful range scan).

For simplicity, just count literal occurrences as upper bound on usage.
"""
from collections import Counter
from pathlib import Path
import struct

BIN = Path("work/h3/extracted/client.bin64000")
TARGETS = {
    0x0a5d: "callback gate (FUN_00041a68)",
    0x02b8: "callback gate 2",
    0xa0c0: "subsystem mode byte",
    0xa1f6: "mode 7 gate",
    0xa288: "NPC index lo",
    0xa289: "NPC index hi",
    0x290:  "last_event_id (FUN_0002c6a4 tail)",
    0x9cb8: "callback queue base ptr",
    0x9cbc: "callback queue src ptr",
    0x9cc0: "callback queue count 1",
    0x9ccc: "callback queue count 2",
    0x9cd4: "callback queue cursor 1",
    0x9cd8: "callback queue base ptr 2",
}


def main() -> None:
    data = BIN.read_bytes()
    counts: Counter[int] = Counter()
    sites: dict[int, list[int]] = {k: [] for k in TARGETS}
    # Scan 4-byte aligned values (LDR pcrel literals are 4-aligned in ARM/Thumb)
    for off in range(0, len(data) - 4, 4):
        val = struct.unpack("<I", data[off:off+4])[0]
        if val in TARGETS:
            counts[val] += 1
            sites[val].append(off)

    print("=== Task field literal occurrence counts ===")
    print(f"{'value':>10}  count  description")
    for val, desc in sorted(TARGETS.items()):
        print(f"  0x{val:08x}  {counts[val]:5}  {desc}")

    print()
    print("=== Sample literal sites (first 6 per field) ===")
    for val, desc in sorted(TARGETS.items()):
        if counts[val] == 0:
            continue
        sample = ", ".join(f"0x{s:08x}" for s in sites[val][:6])
        print(f"  0x{val:08x}: {sample}")


if __name__ == "__main__":
    main()
