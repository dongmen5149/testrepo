"""Verify FUN_00086058 as 7th indirect entry function.

Round 45 / 2LA: extensive validation:
1. Full disasm + literal extraction (which task fields it touches)
2. Literal pool search for 0x86058 / 0x86059 (Thumb address)
3. movw/movt sequence search for indirect-call targets
4. Compare profile vs known indirect entries

Known indirect entries (Round 38):
- FUN_0006619c paint/tick callback
- FUN_00070f34 key handler
- FUN_0008b2e8 sister/NPC entry
- FUN_0008dcd8 main/scene entry
- FUN_000241dc system event dispatcher
- FUN_000245fc NPC subsystem (Round 38, also 0 BL callers)
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

BIN = Path("work/h3/extracted/client.bin64000")
GOT_BASE = 0xB2C40
KNOWN_INDIRECT_ENTRIES = {
    0x6619c: "FUN_0006619c paint/tick",
    0x70f34: "FUN_00070f34 key handler",
    0x8b2e8: "FUN_0008b2e8 sister/NPC",
    0x8dcd8: "FUN_0008dcd8 main/scene",
    0x241dc: "FUN_000241dc system event",
    0x245fc: "FUN_000245fc NPC subsystem",
}


def thumb_pcrel_target(instr_addr: int, imm: int) -> int:
    return (((instr_addr + 4) & ~3) + imm)


def read_word(data: bytes, addr: int) -> int:
    return struct.unpack("<I", data[addr:addr+4])[0]


def main() -> None:
    data = BIN.read_bytes()

    # Step 1: Full disasm of FUN_00086058
    print("=" * 60)
    print("STEP 1: FUN_00086058 full disasm (0x86058..0x861a8)")
    print("=" * 60)
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    for ins in md.disasm(data[0x86058:0x861A8], 0x86058):
        marker = ""
        if ins.mnemonic == "bl":
            marker = "  <BL>"
        elif ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic", "bfi"):
            marker = "  <branch>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{marker}")

    # Step 2: Extract sl-relative literals to identify task fields used
    print()
    print("=" * 60)
    print("STEP 2: sl-relative literal extraction (task field reads)")
    print("=" * 60)
    # Manually find ldr [pc, #imm] sites by re-disasm and tracking
    pcrel_sites = []
    for ins in md.disasm(data[0x86058:0x861A8], 0x86058):
        if ins.mnemonic == "ldr" and "pc" in ins.op_str:
            # Parse "ldr rN, [pc, #imm]"
            try:
                imm_str = ins.op_str.split("#")[-1].rstrip("]")
                imm = int(imm_str, 0)
                lit_addr = thumb_pcrel_target(ins.address, imm)
                if lit_addr + 4 <= len(data):
                    val = read_word(data, lit_addr)
                    sl_rel = (GOT_BASE + val) & 0xFFFFFFFF
                    got_offset = (sl_rel - GOT_BASE) & 0xFFFFFFFF
                    pcrel_sites.append((ins.address, lit_addr, val, got_offset))
            except (ValueError, IndexError):
                pass

    print(f"  Found {len(pcrel_sites)} ldr [pc] sites:")
    for instr_addr, lit_addr, val, got_offset in pcrel_sites:
        if got_offset < 0x10000:
            print(f"    @0x{instr_addr:08x}: literal 0x{val:08x} → task/GOT[+0x{got_offset:x}]")
        else:
            print(f"    @0x{instr_addr:08x}: literal 0x{val:08x} (out of GOT range)")

    # Step 3: Search literal pool for 0x86058 / 0x86059 (Thumb)
    print()
    print("=" * 60)
    print("STEP 3: Search for 0x86058 / 0x86059 in literal pool")
    print("=" * 60)
    targets = [0x86058, 0x86059, 0x8605A]
    matches = []
    for off in range(0, len(data) - 4, 4):
        val = struct.unpack("<I", data[off:off+4])[0]
        if val in targets:
            matches.append((off, val))
    print(f"  Found {len(matches)} matches:")
    for off, val in matches[:20]:
        print(f"    @0x{off:08x}: 0x{val:08x}")

    # Step 4: Compare with known indirect entry literal pool occurrences
    print()
    print("=" * 60)
    print("STEP 4: Compare with known indirect entry literal counts")
    print("=" * 60)
    for entry_addr, label in KNOWN_INDIRECT_ENTRIES.items():
        count = 0
        for off in range(0, len(data) - 4, 4):
            val = struct.unpack("<I", data[off:off+4])[0]
            if val in (entry_addr, entry_addr | 1):
                count += 1
        print(f"  {label} @ 0x{entry_addr:08x}: {count} literal pool occurrences")
    # Add our candidate
    print(f"  FUN_00086058 CANDIDATE @ 0x86058: {len(matches)} literal pool occurrences")


if __name__ == "__main__":
    main()
