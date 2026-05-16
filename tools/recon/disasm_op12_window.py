"""Disassemble a small window inside opcode 0x12 to verify dispatch mechanism.

Round 38 / 2EA: check whether 0x90e38 cmp+bls leads to a tbb/tbh JT (Thumb-2) or
a linear if-chain. Also dump the EUC-KR pair region (0x920c0~0x92180) to see how
Korean lead byte detection branches.
"""
from pathlib import Path

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
except ImportError as e:
    raise SystemExit("capstone not installed: pip install capstone") from e

BIN = Path("work/h3/extracted/client.bin64000")


def disasm_window(data: bytes, start: int, size: int, label: str) -> None:
    print(f"\n=== {label} (0x{start:08x}~0x{start+size:08x}, {size} bytes) ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = True
    for ins in md.disasm(data[start:start+size], start):
        # Highlight tbb/tbh (table branch byte/halfword, Thumb-2)
        flag = ""
        if ins.mnemonic in ("tbb", "tbh"):
            flag = "  <<< TABLE BRANCH"
        elif ins.mnemonic.startswith("b") and ins.mnemonic not in ("bic",):
            flag = "  <branch>"
        elif ins.mnemonic == "ldr" and "pc" in ins.op_str.lower():
            flag = "  <pc-rel ldr>"
        print(f"  0x{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{flag}")


def main() -> None:
    data = BIN.read_bytes()
    # Window 1: gate1 cmp+branch at 0x90e38 — what's the next 64 bytes after the gate?
    disasm_window(data, 0x90E30, 0x80, "gate1 region 0x90e30..0x90eb0")
    # Window 2: gate2 0x9131c — see if it's the tbb dispatcher
    disasm_window(data, 0x91314, 0x80, "gate2 region 0x91314..0x91394")
    # Window 3: EUC-KR pair 1 at 0x920c0..0x92180
    disasm_window(data, 0x920B8, 0xD0, "EUC-KR pair 1 (0x920b8..0x92188)")
    # Window 4: ASCII 'I' at 0x90200
    disasm_window(data, 0x901F8, 0x60, "ASCII 'I' token region (0x901f8..0x90258)")
    # Window 5: ASCII '2' at 0x91ac6
    disasm_window(data, 0x91AC0, 0x80, "ASCII '2' token region (0x91ac0..0x91b40)")


if __name__ == "__main__":
    main()
