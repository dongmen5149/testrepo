"""Round 48 / 2OA-5: BL FUN_85578c 직전 instructions full disasm.

이전 분석에서 sites 0x85b2e 등이 `ldr r2, [pc, #N]` → BL → `str r2, [r3]`
패턴인지 확인. 만약 r2 가 BL 호출 인자라면 FUN_85578c 가 단순 getter 가
아니라 setter 또는 multi-arg accessor.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

# Pick 3 representative sites
SITES_OF_INTEREST = [0x85b2e, 0x87c60, 0x89b2c, 0x905be]


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for bl in SITES_OF_INTEREST:
        print(f"\n========= BL@0x{bl:05x} context (24 bytes before + 24 after) =========")
        start = bl - 0x20
        end = bl + 0x20
        for ins in md.disasm(DATA[start:end], start):
            marker = " <-- BL FUN_85578c" if ins.address == bl else ""
            print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
