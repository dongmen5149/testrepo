"""Round 48 / 2OA-4: literal pool values 가 가리키는 주소의 실체 확인.

가설: 0x22xxx-0x2dxxx 값들은 menu/screen handler 함수 주소 또는 데이터 포인터.
각 값 위치에서 Thumb disassembly를 시도하고, push {} 류의 함수 프롤로그를 탐지.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

# Literal pool values from analyze_a848_litpool_states.py
TARGETS = [
    (0x2268a, "site 0x905ae"),
    (0x28bde, "site 0x8a05a"),
    (0x29116, "site 0x89b22"),
    (0x29d7e, "site 0x88eba"),
    (0x2afe8, "site 0x87c50"),
    (0x2d116, "site 0x85b22"),
]


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for target, origin in TARGETS:
        # Thumb function pointer convention: odd = code, even = data
        # All our values are even -> NOT thumb function pointer directly
        # But may be either: (a) PC-aligned/decoded later, (b) data struct pointer
        print(f"\n=== Target 0x{target:05x} (from {origin}) ===")
        # Try disasm 8 instr at the value
        end = min(target + 0x20, len(DATA))
        instrs = list(md.disasm(DATA[target:end], target))
        if not instrs:
            print(f"  [no thumb disasm at 0x{target:05x}]")
        else:
            for ins in instrs[:6]:
                print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}")
        # Also dump first 16 bytes raw
        raw = DATA[target:target + 16]
        hex_str = " ".join(f"{b:02x}" for b in raw)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in raw)
        print(f"  raw: {hex_str} | {ascii_str}")


if __name__ == "__main__":
    main()
