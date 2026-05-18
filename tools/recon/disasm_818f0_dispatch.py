"""Round 51 / 2RA helper: FUN_818f0 의 JT dispatch (0x81980..0x819b0) 정밀 disasm.

decode_818f0_jt.py 작성 전에 dispatch 인코딩 (PC-rel offsets) 을 확인.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    start, end = 0x81960, 0x819b0
    print(f"=== FUN_818f0 dispatch window 0x{start:05x}..0x{end:05x} ===")
    for ins in md.disasm(DATA[start:end], start):
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
