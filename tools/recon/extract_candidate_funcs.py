"""find_dispatcher_candidates.py 에서 뽑힌 후보 함수의 본문을 추출."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "work" / "ghidra_out" / "all_decompiled.c"
OUT = REPO / "work" / "h3" / "candidate_funcs"


def extract(text: str, addr: str) -> str | None:
    addr = addr.removeprefix("0x").lower().zfill(8)
    pat = re.compile(rf"^[\w\s\*]+\s(FUN_|UndefinedFunction_){addr}\s*\(", re.MULTILINE)
    m = pat.search(text)
    if not m:
        return None
    start = m.start()
    depth = 0
    seen_brace = False
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
            seen_brace = True
        elif text[i] == "}":
            depth -= 1
            if seen_brace and depth == 0:
                return text[start : i + 1]
        i += 1
    return None


def main() -> None:
    addrs = sys.argv[1:]
    if not addrs:
        # default: top dispatcher + mainloop candidates
        meta = json.loads((REPO / "work" / "h3" / "dispatcher_candidates.json").read_text())
        addrs = [c["addr"] for c in meta["mainloop_candidates"][:10]]
        addrs += [c["addr"] for c in meta["dispatcher_candidates"][:10]]

    OUT.mkdir(parents=True, exist_ok=True)
    text = SRC.read_text(encoding="utf-8", errors="replace")
    for addr in addrs:
        body = extract(text, addr)
        if body is None:
            print(f"!! not found: {addr}")
            continue
        outfile = OUT / f"{addr.removeprefix('0x').lower().zfill(8)}.c"
        outfile.write_text(body, encoding="utf-8")
        lines = body.count("\n")
        print(f"  {addr} -> {outfile.name} ({lines} lines)")


if __name__ == "__main__":
    main()
