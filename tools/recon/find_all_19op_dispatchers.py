"""모든 19-opcode dispatcher 자동 발견.

dispatcher 표지:
  - `if (0x12 < *(uint *)(DAT_xxx + unaff_r7))`  (또는 short 변형)
  - `(*(code *)((int)&DAT_000b2c40 + ... * 4 + DAT_yyy))()`
  - `Could not recover jumptable at 0x...`

각 dispatcher 의 jump table 위치 + 19 entries 디코드 → 모든 handler 매핑 표.
"""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "work" / "ghidra_out" / "all_decompiled.c"
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
GHIDRA_LISTING = None  # we don't have direct listing — parse decompiled source
GOT_BASE = 0x000B2C40

# Pattern: dispatcher trio
DISPATCHER_PATTERN = re.compile(
    r"if\s*\(\s*0x12\s*<\s*\*\(uint\s*\*\)\(\s*(DAT_[0-9a-fA-F]+)\s*\+\s*unaff_r7\s*\).*?"
    r"(?:Could not recover jumptable at 0x([0-9a-fA-F]+).*?)?"
    r"\(\s*\*\s*\(\s*code\s*\*\s*\)\s*\(\s*\(int\s*\)\s*&\s*DAT_000b2c40\s*\+\s*"
    r"\*\(int\s*\*\)\(\s*\(int\s*\)\s*&\s*DAT_000b2c40\s*\+\s*\*\(int\s*\*\)\(\s*\1\s*\+\s*unaff_r7\s*\)\s*\*\s*4\s*\+\s*"
    r"(DAT_[0-9a-fA-F]+)\s*\)\s*\+\s*\3\s*\)\s*\)\s*\(\s*\)",
    re.DOTALL,
)

FUNC_HEADER = re.compile(r"^[\w\s\*]+\s(FUN_[0-9a-fA-F]+|UndefinedFunction_[0-9a-fA-F]+)\s*\(", re.MULTILINE)


def find_function_for_position(text: str, pos: int) -> tuple[str, int] | None:
    """Find which function contains the given character position."""
    last_match = None
    for m in FUNC_HEADER.finditer(text):
        if m.start() > pos:
            break
        last_match = m
    if last_match is None:
        return None
    addr_match = re.search(r"FUN_([0-9a-fA-F]+)", last_match.group(0))
    if not addr_match:
        return None
    return f"0x{addr_match.group(1).lower()}", last_match.start()


def find_dat_value_in_listing(dat_label: str) -> int | None:
    """Try to find DAT_xxxxx defined as a 4-byte literal in raw binary.

    Strategy: DAT_xxxxx is at file offset xxxxx. Read 4 bytes there.
    """
    addr = int(dat_label.removeprefix("DAT_"), 16)
    data = BIN.read_bytes()
    if addr + 4 > len(data):
        return None
    return struct.unpack("<I", data[addr : addr + 4])[0]


def to_signed_32(v: int) -> int:
    return v - 0x100000000 if v >= 0x80000000 else v


def decode_jumptable(jt_base_addr: int) -> list[tuple[int, int]]:
    """Read 19 4-byte entries at jt_base_addr (file offset). Return [(opcode, handler_addr)]."""
    data = BIN.read_bytes()
    out = []
    for op in range(19):
        off = jt_base_addr + op * 4
        if off + 4 > len(data):
            return []
        entry = struct.unpack("<I", data[off : off + 4])[0]
        handler = (GOT_BASE + entry) & 0xFFFFFFFF
        out.append((op, handler))
    return out


def main() -> None:
    text = SRC.read_text(encoding="utf-8", errors="replace")

    # Find all positions matching the dispatcher pattern (without the optional jt comment)
    # Simpler: find `if (0x12 < *(uint *)(DAT_xxx + unaff_r7))` then look ~10 lines down for jump table
    simple_pat = re.compile(
        r"if\s*\(\s*0x12\s*<\s*\*\(uint\s*\*\)\(\s*(DAT_[0-9a-fA-F]+)\s*\+\s*unaff_r7\s*\)\s*\)",
    )

    found = []
    for m in simple_pat.finditer(text):
        opcode_dat = m.group(1)
        # search next 800 chars for the jump table call line
        tail = text[m.end() : m.end() + 800]
        jt_m = re.search(
            r"\*\(int\s*\*\)\(\s*"
            + re.escape(opcode_dat)
            + r"\s*\+\s*unaff_r7\s*\)\s*\*\s*4\s*\+\s*(DAT_[0-9a-fA-F]+)\s*\)",
            tail,
        )
        jt_dat = jt_m.group(1) if jt_m else None
        # which function contains this match?
        fn = find_function_for_position(text, m.start())
        # find "Could not recover jumptable at 0xXXXX"
        cnr = re.search(r"Could not recover jumptable at 0x([0-9a-fA-F]+)", tail)
        cnr_addr = f"0x{cnr.group(1).lower()}" if cnr else None
        found.append({
            "func": fn[0] if fn else "?",
            "func_pos": fn[1] if fn else 0,
            "opcode_dat": opcode_dat,
            "jt_dat": jt_dat,
            "cannot_recover_at": cnr_addr,
            "match_pos": m.start(),
        })

    print(f"found {len(found)} dispatcher pattern occurrences")
    print()
    # dedupe by func
    by_func: dict[str, list[dict]] = {}
    for f in found:
        by_func.setdefault(f["func"], []).append(f)

    print(f"{'function':<14} {'jt_dat':<14} {'jt_base':>10} {'cnr':<11}")
    print("-" * 60)

    all_dispatchers = []
    for fn, lst in by_func.items():
        for f in lst:
            jt_dat = f["jt_dat"] or "?"
            jt_value = find_dat_value_in_listing(jt_dat) if jt_dat != "?" else None
            jt_base = (GOT_BASE + jt_value) & 0xFFFFFFFF if jt_value is not None else None
            jt_base_str = f"0x{jt_base:08x}" if jt_base else "?"
            print(f"{fn:<14} {jt_dat:<14} {jt_base_str:>10} {f['cannot_recover_at']}")
            if jt_base:
                handlers = decode_jumptable(jt_base)
                if handlers:
                    distinct = sorted({h for _, h in handlers})
                    print(f"  → 19 entries, {len(distinct)} distinct handlers:")
                    # Group by handler
                    by_handler: dict[int, list[int]] = {}
                    for op, h in handlers:
                        by_handler.setdefault(h, []).append(op)
                    for h in sorted(by_handler):
                        ops = by_handler[h]
                        if len(ops) == 1:
                            op_str = f"0x{ops[0]:02x}"
                        else:
                            op_str = f"0x{ops[0]:02x}~0x{ops[-1]:02x}" if ops == list(range(ops[0], ops[-1]+1)) else ",".join(f"0x{o:02x}" for o in ops)
                        print(f"     opcode {op_str:<14}: 0x{h:08x}")
                    all_dispatchers.append({
                        "func": fn,
                        "jt_dat": jt_dat,
                        "jt_base": f"0x{jt_base:08x}",
                        "cnr": f["cannot_recover_at"],
                        "handlers_by_opcode": [{"opcode": op, "handler": f"0x{h:08x}"} for op, h in handlers],
                        "distinct_handlers": [f"0x{h:08x}" for h in distinct],
                    })
            print()

    # Save
    out = REPO / "work" / "h3" / "all_19op_dispatchers.json"
    out.write_text(json.dumps(all_dispatchers, indent=2), encoding="utf-8")
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
