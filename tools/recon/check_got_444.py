"""Round 51 / 2RA: GOT[+0x444] 의 binary 내 값 확인.

FUN_4ad10 returns *(GOT_BASE + 0x444). 그 슬롯의 binary 내 raw 값과 주변 슬롯 dump.
"""
import struct
from pathlib import Path

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40

slot_addr = GOT_BASE + 0x444
print(f"GOT[+0x444] addr = 0x{slot_addr:05x}")
print(f"binary size = 0x{len(DATA):x}")

if slot_addr + 4 > len(DATA):
    print(f"(slot extends beyond binary by {slot_addr + 4 - len(DATA)} bytes)")
else:
    val = struct.unpack("<I", DATA[slot_addr:slot_addr + 4])[0]
    print(f"GOT[+0x444] @ 0x{slot_addr:05x} = 0x{val:08x}")

print()
print(f"=== Surrounding GOT region 0x{slot_addr - 0x40:05x}..0x{slot_addr + 0x40:05x} ===")
for off in range(-0x40, 0x44, 4):
    addr = slot_addr + off
    if addr < 0 or addr + 4 > len(DATA):
        print(f"  GOT[+0x{0x444 + off:03x}] @ 0x{addr:05x} = (out of range)")
        continue
    val = struct.unpack("<I", DATA[addr:addr + 4])[0]
    tag = " ★" if off == 0 else ""
    print(f"  GOT[+0x{0x444 + off:03x}] @ 0x{addr:05x} = 0x{val:08x}{tag}")
