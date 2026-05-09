"""7 handler 주소가 진짜 함수 시작인지 raw binary 에서 ARM Thumb prologue 패턴 확인."""
from __future__ import annotations

import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"

HANDLERS = [
    ("0x95bfe", "0x00~0x0c (13 opcodes)"),
    ("0x960e8", "0x0d"),
    ("0x962f4", "0x0e"),
    ("0x9651c", "0x0f"),
    ("0x9685c", "0x10"),
    ("0x96aa6", "0x11"),
    ("0x96bf8", "0x12"),
]


def disasm_thumb_short(word: int) -> str:
    """Decode common ARM Thumb prologue patterns."""
    # push {regs, lr}: 0xb500..0xb5ff
    if (word & 0xFE00) == 0xB400:
        regs = []
        for i in range(8):
            if word & (1 << i):
                regs.append(f"r{i}")
        if word & 0x100:
            regs.append("lr")
        return f"push {{{','.join(regs)}}}"
    # sub sp, #imm: 0xB080..
    if (word & 0xFF80) == 0xB080:
        imm = (word & 0x7F) * 4
        return f"sub sp,#{imm:#x}"
    # mov r7, sp / add r7, sp, #imm — various encodings
    if (word & 0xFFC7) == 0x466F or (word & 0xFFF8) == 0x4670:
        return "mov r7,sp"
    return f"(? {word:04x})"


def main() -> None:
    data = BIN.read_bytes()
    print(f"binary size: 0x{len(data):x}")
    print()

    for addr_str, desc in HANDLERS:
        addr = int(addr_str, 16)
        # In ARM Thumb mode the LSB is set; clear for actual byte offset
        # But since handler addresses came from a jump-table entry that's already been
        # added to GOT base, they should be even (byte-aligned)
        word_offset = addr & ~1
        if word_offset + 8 > len(data):
            print(f"{addr_str}: out of range")
            continue
        words = struct.unpack("<HHHH", data[word_offset : word_offset + 8])
        print(f"{addr_str}  ({desc})")
        for i, w in enumerate(words):
            print(f"  +{i*2:>2}: {w:04x}  {disasm_thumb_short(w)}")
        # Look at branch back: is this near another function's body?
        # Quick: check 8 bytes before — if we see a `bx lr` (0x4770) or pop {pc} (0xbd??),
        # that's a function epilogue → handler is a real function start
        if word_offset >= 4:
            prev = struct.unpack("<H", data[word_offset - 2 : word_offset])[0]
            note = "PREV: "
            if prev == 0x4770:
                note += "bx lr (epilogue) ← prev function ended"
            elif (prev & 0xFF00) == 0xBD00:
                note += "pop {...,pc} (epilogue) ← prev function ended"
            else:
                note += f"{prev:04x}"
            print(f"  prev: {note}")
        print()


if __name__ == "__main__":
    main()
