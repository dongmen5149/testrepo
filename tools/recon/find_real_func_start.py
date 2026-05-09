"""scn_dispatch_evt (0x8e112) 진짜 포함 함수 시작 찾기.

ARM Thumb 함수 prologue 패턴:
  - push {...}  : 0xb400 ~ 0xb5ff (소형: r0~r7 + 옵션 lr)
  - push {r4..r7, lr}: 0xb5f0 (가장 흔함)
  - push.w {r4..r11, lr}: 32-bit Thumb-2 encoding (e92d xxxx)

0x8e000 ~ 0x8e120 영역 + 그 직후 영역까지 push 명령 위치 모두 추출.
"""
from __future__ import annotations

import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"


def is_push(word: int) -> str | None:
    # T1 push: 0xb400..0xb5ff (push registers in r0-r7 plus optional LR)
    if (word & 0xFE00) == 0xB400:
        regs = []
        for i in range(8):
            if word & (1 << i):
                regs.append(f"r{i}")
        if word & 0x100:
            regs.append("lr")
        return f"push {{{','.join(regs)}}}"
    return None


def main() -> None:
    data = BIN.read_bytes()

    # Scan wider area
    print("scanning for push prologues in 0x8a000~0x8f000:")
    print()
    print(f"{'addr':<10} {'word':>6}  meaning")
    print("-" * 50)
    for off in range(0x8A000, min(0x8F000, len(data)), 2):
        word = struct.unpack("<H", data[off : off + 2])[0]
        p = is_push(word)
        if p:
            print(f"0x{off:08x}  {word:04x}  {p}")

    print()
    # Show interesting addresses
    print("known dispatcher-related addresses:")
    print("  0x8e112  scn_dispatch_evt entry (sub-block)")
    print("  0x8e89e  dispatcher tail (jump table call)")
    print("  0x8b726  sister dispatcher (different jump table)")


if __name__ == "__main__":
    main()
