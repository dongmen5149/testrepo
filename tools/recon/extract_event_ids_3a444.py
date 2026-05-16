"""Extract event_id immediates at each FUN_0003a444 → FUN_0002c6a4 call site.

Round 43 / 2JB: 4 BL sites at 0x3a516/+0xd2, 0x3a66a/+0x226, 0x3a694/+0x250, 0x3a828/+0x3e4.
Look at the 16 bytes before each BL to find `movs r0, #imm` or similar event_id setup.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")


def main() -> None:
    data = BIN.read_bytes()
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True

    call_sites = [
        ("FUN_0003a444 +0xd2", 0x3A516),
        ("FUN_0003a444 +0x226", 0x3A66A),
        ("FUN_0003a444 +0x250", 0x3A694),
        ("FUN_0003a444 +0x3e4", 0x3A828),
        # Also: other key callers of FUN_0002c6a4
        ("FUN_000241dc +0x98", 0x24274),  # 5th indirect entry
        ("FUN_000245fc mode 7 +0x150", 0x2474C),  # known r0=0x11
        ("FUN_000818f0 entity update +0xf4", 0x819E4),
        ("FUN_0002ae44 +0x40", 0x2AE84),
        ("FUN_0002ae44 +0x6a", 0x2AEAE),
        ("FUN_0002ae44 +0x294", 0x2B0D8),
        ("FUN_0002ae44 +0x2a6", 0x2B0EA),
        ("FUN_00026a80 (subsystem router) +0x205a", 0x28ADA),
        ("FUN_00026a80 (subsystem router) +0x2368", 0x28DE8),
        ("FUN_00041c14 (cluster #1 SM) +0x8ae", 0x424C2),
        ("FUN_00053e08 +0x2be", 0x540C6),
        ("FUN_00086058 +0x6a", 0x860C2),
        ("FUN_000933e8 +0x6c", 0x93454),
    ]

    for label, bl_addr in call_sites:
        # Show 16 bytes (8 instructions) before the BL
        start = max(0, bl_addr - 0x10)
        print(f"\n=== {label} (BL @ 0x{bl_addr:08x}) ===")
        for ins in md.disasm(data[start:bl_addr + 4], start):
            mark = "  <BL>" if ins.mnemonic == "bl" else ""
            print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{mark}")


if __name__ == "__main__":
    main()
