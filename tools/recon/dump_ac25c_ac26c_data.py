"""Round 55 / 2VA: GOT[+0xd28] = 0xac25c, GOT[+0xd38] = 0xac26c 의
binary 내 raw data 영역 dump.

두 슬롯이 가리키는 정적 구조 확인. paired 16B 간격으로 인접.
"""
import struct
from pathlib import Path

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    base = 0xac25c
    print(f"=== Data @ 0x{base:05x}..0x{base + 0x100:05x} (raw words) ===")
    for off in range(0, 0x100, 4):
        addr = base + off
        if addr + 4 > len(DATA):
            print(f"  +0x{off:03x}  0x{addr:05x}: (out of binary)")
            break
        val = struct.unpack("<I", DATA[addr:addr + 4])[0]
        # Note for both anchors
        anchor = ""
        if off == 0x00:
            anchor = "  ← +0xd28 START"
        elif off == 0x10:
            anchor = "  ← +0xd38 START (16B gap)"
        # ASCII interpretation
        ascii_part = ""
        bytes_4 = DATA[addr:addr + 4]
        if all(0x20 <= b < 0x7f for b in bytes_4):
            ascii_part = f' "{bytes_4.decode("latin-1")}"'
        print(f"  +0x{off:03x}  0x{addr:05x}: 0x{val:08x}{ascii_part}{anchor}")

    # Also try to interpret as multiple struct layouts (some game tables use 16/32B entries)
    print("\n=== Byte dump @ 0xac25c..0xac28c (48B span around both anchors) ===")
    for line_off in range(0, 0x30, 16):
        addr = base + line_off
        if addr + 16 > len(DATA):
            break
        line_bytes = DATA[addr:addr + 16]
        hex_str = " ".join(f"{b:02x}" for b in line_bytes)
        ascii_str = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in line_bytes)
        print(f"  0x{addr:05x}: {hex_str}  |{ascii_str}|")


if __name__ == "__main__":
    main()
