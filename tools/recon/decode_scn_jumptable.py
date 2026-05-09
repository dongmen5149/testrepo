"""§4.4 _scn dispatcher jump table 디코드.

dispatcher 코드 (FUN_0008e89e 안):
    (*(code *)((int)&DAT_000b2c40 +
              *(int *)((int)&DAT_000b2c40 + opcode * 4 + DAT_0008ec74) +
              DAT_0008ec74))();

알려진 값:
    GOT base       = 0x000b2c40
    DAT_0008ec74   = 0xFFFF9028 (signed -0x6FD8)
    → jump_table_base = 0xb2c40 + 0xFFFF9028 = 0xb2c40 - 0x6FD8 = 0xABC68

각 entry [opcode]:
    entry_value = *(int *)(0xABC68 + 4 * opcode)
    handler_addr = 0xb2c40 + entry_value
"""
from __future__ import annotations

import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"

GOT_BASE = 0x000B2C40
DAT_0008EC74 = 0xFFFF9028  # signed = -0x6FD8

# (signed conversion)
def to_signed_32(v: int) -> int:
    return v - 0x100000000 if v >= 0x80000000 else v


def main() -> None:
    data = BIN.read_bytes()
    print(f"binary size: {len(data):,} bytes (= 0x{len(data):x})")

    offset = to_signed_32(DAT_0008EC74)
    print(f"DAT_0008ec74 signed: {offset:#x}")
    jt_base = (GOT_BASE + DAT_0008EC74) & 0xFFFFFFFF
    print(f"jump table base: 0x{GOT_BASE:08x} + 0x{DAT_0008EC74:08x} = 0x{jt_base:08x}")
    print()

    if jt_base + 19 * 4 > len(data):
        print(f"!! jump table extends beyond binary (need 0x{jt_base + 76:x}, have 0x{len(data):x})")
        return

    # Sanity: is file offset == virtual address? Check if 0x8e112 has Thumb push prologue
    push_check = data[0x8e110:0x8e114]
    print(f"sanity: bytes @ 0x8e110-13 = {push_check.hex()}")
    print()

    print("=" * 76)
    print("opcode → handler mapping (jump table @ 0x{:x})".format(jt_base))
    print("=" * 76)
    print(f"{'op':>4} {'jt_offset':>10} {'entry_value':>12} {'handler_offset':>15} {'handler_addr':>14}")

    handlers = []
    for op in range(19):  # 0~0x12
        jt_offset = jt_base + op * 4
        entry_bytes = data[jt_offset : jt_offset + 4]
        entry_value = struct.unpack("<I", entry_bytes)[0]
        handler_offset = to_signed_32(entry_value)
        handler_addr = (GOT_BASE + entry_value) & 0xFFFFFFFF
        handlers.append((op, handler_addr, handler_offset))
        print(
            f"  {op:>2} (0x{op:02x}) "
            f"0x{jt_offset:08x}  "
            f"0x{entry_value:08x}  "
            f"{handler_offset:>+15x}  "
            f"0x{handler_addr:08x}"
        )

    print()
    # Compact summary for handoff
    print("=== handoff summary ===")
    print("opcode → handler:")
    for op, addr, _ in handlers:
        print(f"  0x{op:02x}: FUN_{addr:08x}")

    # Check if same handlers repeat (some opcodes may share)
    print()
    distinct = set(addr for _, addr, _ in handlers)
    print(f"distinct handlers: {len(distinct)}/19")

    # Save JSON
    out = REPO / "work" / "h3" / "scn_dispatcher_jumptable.json"
    import json
    out.write_text(
        json.dumps(
            {
                "got_base": f"0x{GOT_BASE:08x}",
                "DAT_0008ec74": f"0x{DAT_0008EC74:08x}",
                "jump_table_base": f"0x{jt_base:08x}",
                "opcodes": [
                    {"op": op, "handler": f"0x{addr:08x}"}
                    for op, addr, _ in handlers
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nsaved: {out}")


if __name__ == "__main__":
    main()
