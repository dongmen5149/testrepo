"""Find the next function start (push prologue) AFTER a given address.

Round 38 helper: bound FUN_00098904's end."""
import sys
from pathlib import Path


def find_thumb_push_after(data: bytes, start_addr: int, max_forward: int = 0x4000) -> int | None:
    """Walk forward looking for `push {...,lr}` or Thumb-2 push at 2-byte boundary."""
    addr = start_addr + 2  # skip the prologue itself
    while addr < min(len(data), start_addr + max_forward):
        if addr + 2 > len(data):
            break
        w = int.from_bytes(data[addr:addr + 2], "little")
        if 0xB500 <= w <= 0xB5FF:
            return addr
        if w == 0xE92D:
            return addr
        addr += 2
    return None


def main() -> None:
    bin_path = Path("work/h3/extracted/client.bin64000")
    data = bin_path.read_bytes()
    for addr_hex in sys.argv[1:]:
        addr = int(addr_hex, 16)
        nxt = find_thumb_push_after(data, addr)
        if nxt is None:
            print(f"0x{addr:08x}: no next push within 0x4000")
        else:
            print(f"0x{addr:08x}: next function start = 0x{nxt:08x}  (size = {nxt - addr} bytes / 0x{nxt - addr:x})")


if __name__ == "__main__":
    main()
