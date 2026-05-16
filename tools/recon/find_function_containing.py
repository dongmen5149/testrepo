"""Find the function (push prologue) preceding a given address in binary.

Round 37 / 2DQ helper."""
import sys
from pathlib import Path


def find_thumb_push_before(data: bytes, target_addr: int, max_back: int = 0x800) -> int | None:
    """Walk backwards from target_addr looking for `push {...,lr}` (0xb500-0xb5ff) start.

    Returns the function start address or None.
    """
    for off in range(target_addr, max(0, target_addr - max_back), -2):
        if off + 2 > len(data):
            continue
        w = int.from_bytes(data[off:off+2], "little")
        # Thumb push: 1011 010M rrrr rrrr  (M=1 includes LR)
        if 0xB500 <= w <= 0xB5FF:
            return off
        # Thumb-2 push with high registers (encoding T2): 0xe92d ____
        if w == 0xE92D:
            return off
    return None


def main() -> None:
    bin_path = Path("work/h3/extracted/client.bin64000")
    data = bin_path.read_bytes()
    for addr_hex in sys.argv[1:]:
        addr = int(addr_hex, 16)
        prologue = find_thumb_push_before(data, addr)
        if prologue is None:
            print(f"0x{addr:08x}: no push prologue within 0x800 backwards")
        else:
            offset = addr - prologue
            print(f"0x{addr:08x}: function start = 0x{prologue:08x}  (offset +0x{offset:x})")


if __name__ == "__main__":
    main()
