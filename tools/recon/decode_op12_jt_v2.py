"""Decode opcode 0x12's inner JT with the correct sl-relative model.

Round 38 / 2EA:
  sl = 0xb2c40 (GOT base)
  JT base   = sl + (-0x6f8c) = 0xabcb4
  CODE base = sl + 0x17ac    = 0xb43ec
  index r3  comes from task_struct[0x9e28] (sound state #1 / mode byte)
  dest = CODE_base + signed(JT[index])

The cmp r1, #0x49 gate at 0x90200 bounds the index to ≤ 73 (0x49), so up to 74 entries.
"""
import struct
from pathlib import Path

BIN = Path("work/h3/extracted/client.bin64000")
JT_BASE = 0xABCB4
CODE_BASE = 0xB43EC
COUNT = 74


def main() -> None:
    data = BIN.read_bytes()
    print(f"=== opcode 0x12 inner JT @ 0x{JT_BASE:08x}, code base 0x{CODE_BASE:08x}, {COUNT} entries ===\n")
    dests: dict[int, list[int]] = {}
    rows = []
    for i in range(COUNT):
        off = JT_BASE + i * 4
        entry = struct.unpack("<i", data[off:off + 4])[0]
        dest = (CODE_BASE + entry) & 0xFFFFFFFF
        dests.setdefault(dest, []).append(i)
        in_range = 0x8E89E <= dest <= 0x929E8
        rows.append((i, entry, dest, in_range))
        marker = "★" if in_range else " "
        print(f"  {marker} case={i:2}: entry=0x{entry:08x} -> 0x{dest:08x}")

    in_func = sum(1 for _, _, d, ir in rows if ir)
    print(f"\nunique destinations: {len(dests)} (in FUN_0008e89e range: {in_func}/{COUNT})")
    print("\n=== destination histogram ===")
    for d, cases in sorted(dests.items(), key=lambda x: -len(x[1])):
        marker = "★" if 0x8E89E <= d <= 0x929E8 else " "
        print(f"  {marker} 0x{d:08x} : {len(cases)} cases -> {cases}")


if __name__ == "__main__":
    main()
