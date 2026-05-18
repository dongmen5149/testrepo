"""Hero5 Dialog 시스템에서 호출되는 helper 함수들의 ELF symbol 이름을 추출."""
from __future__ import annotations
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief

TARGETS = [
    0x59400,   # text/dialog draw call
    0x5f000,   # input wait
    0x6ab40,   # transition trigger
    0x9e540,   # string fetch
    0x520c8,   # text measure 1
    0x520d0,   # text measure 2
    0x438e8,   # ??
    0x82248,   # ??
    0x8245c,   # DrawDialogBox
    0x445b4,   # ??
    0x438e0,   # ??
    0x44370,   # ??
    0x1431a0,  # ??
    0x52098,   # ??
    0x72f54,   # ??
    0x9e540,   # str fetch
]

def main():
    g = select("h5")
    b = lief.parse(g.binary_path)
    by_addr = {}
    for s in b.symbols:
        v = int(s.value)
        if v & 1:
            v -= 1
        by_addr.setdefault(v, []).append(s.name)
    for t in sorted(set(TARGETS)):
        names = by_addr.get(t, [])
        print(f"{t:#10x}: {names}")

if __name__ == "__main__":
    main()
