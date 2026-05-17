"""Round 48 / 2OC: FUN_000818f0 entity update loop의 0x8195c 부근 letter input 트리거 컨텍스트.

Round 47에서 FUN_0003a86c (letter input entry)의 4 callers 중 하나가
FUN_000818f0+0x6c (0x8195c). 본 스크립트는 0x8195c 주변 30 instr 윈도우를
disasm해서:
1. 어떤 조건(cmp) 후 FUN_3a86c 가 호출되는지
2. r0 (entity arg) 의 출처 (task field 또는 외부 인자)
3. 호출 후 어떤 처리가 이어지는지
를 추출한다.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)

    # First, confirm exact BL FUN_3a86c address within FUN_000818f0
    # Search 0x818f0 to 0x82690 (estimated function end) for BL with target 0x3a86c
    print("=== BL FUN_3a86c sites within FUN_000818f0 ===")
    bl_sites = []
    for ins in md.disasm(DATA[0x818f0:0x82690], 0x818f0):
        if ins.mnemonic == "bl":
            try:
                target = int(ins.op_str.strip().lstrip("#"), 0)
                # BL is PC+offset; capstone already resolves
                if 0x3a86c <= target <= 0x3a87c:  # Allow off-by-thumb-bit
                    bl_sites.append(ins.address)
            except Exception:
                pass
    for site in bl_sites:
        print(f"  0x{site:05x}: bl FUN_3a86c")
    if not bl_sites:
        # Maybe BL is elsewhere; rescan with broader target tolerance
        print("  [no exact match — scanning ALL BLs in range 0x3a86c..0x3a880]")
        for ins in md.disasm(DATA[0x818f0:0x82690], 0x818f0):
            if ins.mnemonic == "bl":
                target_str = ins.op_str.strip().lstrip("#")
                if "0x3a8" in target_str:
                    print(f"  0x{ins.address:05x}: bl {target_str}")
                    bl_sites.append(ins.address)

    if not bl_sites:
        print("  [no BL FUN_3a86c found in range — check function bounds]")
        return

    # For each BL site, dump 40 bytes before + 40 after
    for site in bl_sites:
        print(f"\n=== Context around BL@0x{site:05x} ===")
        start = max(0, site - 0x40)
        end = min(len(DATA), site + 0x40)
        for ins in md.disasm(DATA[start:end], start):
            marker = ""
            if ins.address == site:
                marker = "  <-- BL FUN_3a86c"
            elif ins.mnemonic.startswith("cmp"):
                marker = "  <cmp>"
            elif ins.mnemonic in ("bl", "blx"):
                marker = "  <BL>"
            elif ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic", "bfi"):
                marker = "  <branch>"
            print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
