"""NPC slot record (0x3c4 stride) 안에서 read 되는 모든 offset 추출.

dispatcher 1 (FUN_0005d214) 본문에서 record 인덱싱 패턴:
  *(... *)(<outer> * 0x3c4 + <inner> * 0x3c + <base> + OFFSET)

OFFSET 들을 모두 추출해서:
  - byte (char) read = flag, type, count
  - short read = coordinate, hp, parameter (좌표 후보!)
  - int read = pointer

좌표일 가능성이 높은 short pair (예: +0xN: x, +0xN+2: y) 를 식별.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "work" / "ghidra_out" / "all_decompiled.c"

# Pattern: ` * 0x3c4 + <something> * 0x3c + <base> + 0xNN`
RECORD_OFFSET_PAT = re.compile(
    r"\*\s*0x3c4\s*\+\s*[^+]+?\*\s*0x3c\s*\+\s*\*?\(?int\s*\*?\)?\(?[^+]*?\+\s*-?0x[0-9a-fA-F]+\s*\)\s*\+\s*(0x[0-9a-fA-F]+)\s*\)",
    re.DOTALL,
)

# Simpler: capture context around `0x3c4` lines
RECORD_LINE_PAT = re.compile(
    r"(\*\([^)]*\))\s*\(\s*[^)]*\*\s*0x3c4\s*\+[^)]*\*\s*0x3c\s*\+[^)]*\+\s*(0x[0-9a-fA-F]+)\s*\)",
    re.DOTALL,
)

# Even simpler: scan for "+ 0x3c4" then look for "+ 0x..)" within next 200 chars
SIMPLE_PAT = re.compile(
    r"\*\s*0x3c4\s*\+(?:[^+]|\+\s*[^0])*?\+\s*(0x[0-9a-fA-F]+)\s*\)",
)


def parse_hex(s: str) -> int | None:
    try:
        return int(s, 16)
    except ValueError:
        return None


def main() -> None:
    text = SRC.read_text(encoding="utf-8", errors="replace")

    # Find all "0x3c4" occurrences
    print("scanning for record-offset patterns ...")
    print()

    # For each `0x3c4`, look ahead within ~300 chars for `+ 0xNN)` pattern
    offset_count: Counter = Counter()
    offset_with_type: dict[int, Counter] = defaultdict(Counter)

    # Better approach: find all `* 0x3c4 + ... + 0xNN)` patterns globally
    # Pattern: `* 0x3c4` + ANY chars + `+ 0xNN)` (ending with close paren, indicating end of indexing)
    # `[\s\S]{0,400}?` allows any chars (incl. nested `)`) up to 400 limit
    full_pat = re.compile(
        r"\*\s*0x3c4\b[\s\S]{0,400}?\+\s*(0x[0-9a-fA-F]+)\s*\)",
    )
    seen_positions = set()
    for m in full_pat.finditer(text):
        pos = m.start()
        # avoid double-counting the same line
        if pos in seen_positions:
            continue
        seen_positions.add(pos)
        val = parse_hex(m.group(1))
        if val is None or val < 0x10 or val >= 0x400:
            continue
        if val in (0x3C, 0x3C4):
            continue
        offset_count[val] += 1
        # find access type — look just before this `* 0x3c4` in original text
        pre = text[max(0, pos - 300) : pos]
        cast_match = list(re.finditer(r"\*\s*\(\s*(\w+)\s*\*\s*\)", pre))
        if cast_match:
            cast = cast_match[-1].group(1).lower()
            if cast in ("short", "ushort", "undefined2"):
                offset_with_type[val]["short"] += 1
            elif cast in ("char", "byte", "undefined1", "uchar"):
                offset_with_type[val]["byte"] += 1
            elif cast in ("int", "uint", "undefined4"):
                offset_with_type[val]["int"] += 1
            else:
                offset_with_type[val]["?"] += 1
        else:
            offset_with_type[val]["?"] += 1

    print(f"found {len(offset_count)} distinct record offsets")
    print()
    print(f"{'offset':>8} {'count':>6} {'byte':>4} {'short':>5} {'int':>3} {'?':>3}")
    print("-" * 40)
    for off in sorted(offset_count):
        types = offset_with_type[off]
        print(
            f"  0x{off:03x} {offset_count[off]:>6} "
            f"{types.get('byte', 0):>4} {types.get('short', 0):>5} "
            f"{types.get('int', 0):>3} {types.get('?', 0):>3}"
        )

    # Highlight short pairs (potential coordinates)
    print()
    print("=== short type offsets (coordinate candidates) ===")
    short_offsets = [off for off in sorted(offset_count) if offset_with_type[off].get("short", 0) > 0]
    pairs_found = []
    for off in short_offsets:
        next_off = off + 2
        if next_off in offset_count and offset_with_type[next_off].get("short", 0) > 0:
            print(f"  0x{off:03x} + 0x{next_off:03x} (pair) -- likely (x, y)")
            pairs_found.append((off, next_off))
        else:
            print(f"  0x{off:03x}             -- single short")

    # Save
    out = REPO / "work" / "h3" / "npc_record_offsets.json"
    out.write_text(
        json.dumps(
            {
                "offset_count": {f"0x{k:x}": v for k, v in sorted(offset_count.items())},
                "offset_types": {f"0x{k:x}": dict(v) for k, v in offset_with_type.items()},
                "short_pairs": [
                    [f"0x{o:x}", f"0x{o+2:x}"]
                    for o in short_offsets
                    if (o + 2) in offset_count and offset_with_type[o + 2].get("short", 0) > 0
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print()
    print(f"saved: {out}")


if __name__ == "__main__":
    main()
