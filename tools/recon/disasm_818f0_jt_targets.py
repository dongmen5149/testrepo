"""Round 51 / 2RA: FUN_818f0 의 8 distinct JT target handlers 본문 dump.

decode_818f0_jt.py 결과:
  - arg=-16 → 0x8199c   (FUN_818f0 fall-through init path)
  - arg=-5  → 0x81b9c   ★ letter input?
  - arg=-4  → 0x8263a
  - arg=-3  → 0x823ea
  - arg=-2  → 0x82a98
  - arg=-1  → 0x828f6
  - arg=+55 → 0x82c2c   (ASCII '7')
  - arg=+57 → 0x82d18   (ASCII '9')

각 target → 다음 BL 또는 다음 b/bx/mov pc 까지 dump.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

TARGETS = [
    (-16, 0x8199c, 0x81b80),
    (-5,  0x81b9c, 0x823e8),  # large gap so include all up to next target
    (-3,  0x823ea, 0x82638),
    (-4,  0x8263a, 0x828f4),
    (-1,  0x828f6, 0x82a98),
    (-2,  0x82a98, 0x82c2c),
    (+55, 0x82c2c, 0x82d18),
    (+57, 0x82d18, 0x82df4),
]


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for arg, start, end in TARGETS:
        print(f"\n=== arg={arg:+d}  handler @ 0x{start:05x}..0x{end:05x} ({end-start} bytes) ===")
        if start >= len(DATA):
            print(f"(OUT of binary, size 0x{len(DATA):x})")
            continue
        end = min(end, len(DATA))
        bls = 0
        max_lines = 40
        line_count = 0
        for ins in md.disasm(DATA[start:end], start):
            marker = ""
            if ins.mnemonic == "bl":
                bls += 1
                tok = ins.op_str.strip().lstrip("#")
                try:
                    t = int(tok, 0)
                    marker = f"  <BL 0x{t:x}>"
                except Exception:
                    marker = "  <BL>"
            elif ins.mnemonic.startswith("cmp"):
                marker = "  <cmp>"
            elif ins.mnemonic in ("b", "bx", "mov") and "pc" in ins.op_str:
                marker = "  <FLOW>"
            print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
            line_count += 1
            if line_count >= max_lines:
                print(f"  ... (truncated, {bls} BLs so far)")
                break
        else:
            print(f"  -- total BL: {bls}")


if __name__ == "__main__":
    main()
