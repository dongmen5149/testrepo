"""HERO::ChangeAttackMotion (0x91e7c) 의 cross-reference 찾기.

bl 호출이 0건이므로 (vtable / function pointer table) 가능성.
.so 전체에서 u32 LE 0x91e7c 또는 0x91e7d (thumb bit) 검색.
"""
from __future__ import annotations
import pathlib, sys, struct
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief

TARGET = 0x91e7c
THUMB_TARGET = 0x91e7d  # ARM mode 인 경우 무관

def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    # u32 LE 검색
    print(f"# Searching for u32 LE references to {TARGET:#x} (and thumb variant {THUMB_TARGET:#x})\n")
    needle1 = struct.pack("<I", TARGET)
    needle2 = struct.pack("<I", THUMB_TARGET)
    needle3 = struct.pack("<I", TARGET | 1)
    hits = []
    pos = 0
    while True:
        i = data.find(needle1, pos)
        if i < 0:
            break
        hits.append((i, "ARM"))
        pos = i + 1
    pos = 0
    while True:
        i = data.find(needle2, pos)
        if i < 0:
            break
        if (i, "ARM") not in hits:
            hits.append((i, "thumb"))
        pos = i + 1

    # file offset → virtual address
    print(f"# Hits: {len(hits)}")
    for file_off, kind in hits:
        # find segment
        vaddr = None
        for seg in b.segments:
            seg_off = int(seg.file_offset)
            seg_size = int(seg.physical_size)
            if seg_off <= file_off < seg_off + seg_size:
                vaddr = int(seg.virtual_address) + (file_off - seg_off)
                seg_flags = int(seg.flags)
                break
        vstr = hex(vaddr) if vaddr is not None else "None"
        print(f"  file_off={file_off:#x}  vaddr={vstr:>10}  ({kind})")

    # 추가: ARM mode 의 ldr/blx 명령어로 indirect 호출 패턴 검색
    # (literal pool 에서 load 한 후 blx/bx 호출) — 위 hits 가 그 literal pool 위치
    print("\n# Symbol info for each hit's surrounding region:")
    by_addr = {}
    for s in b.symbols:
        v = int(s.value) & ~1
        sz = int(s.size)
        if sz > 0:
            by_addr.setdefault(v, []).append((s.name, sz))
    funcs = sorted(by_addr.items())
    def find_enclosing(addr):
        # binary search
        lo, hi = 0, len(funcs)
        while lo < hi:
            mid = (lo + hi) // 2
            v, names = funcs[mid]
            if addr < v:
                hi = mid
            else:
                # check if addr < v + first size
                max_sz = max(sz for _, sz in names)
                if addr < v + max_sz:
                    return (v, names[0][0], max_sz)
                lo = mid + 1
        # fallback: nearest preceding
        if lo > 0:
            v, names = funcs[lo - 1]
            return (v, names[0][0], 0)
        return None
    for file_off, kind in hits:
        # vaddr 계산 다시
        vaddr = None
        for seg in b.segments:
            seg_off = int(seg.file_offset)
            seg_size = int(seg.physical_size)
            if seg_off <= file_off < seg_off + seg_size:
                vaddr = int(seg.virtual_address) + (file_off - seg_off)
                break
        if vaddr is None:
            continue
        f = find_enclosing(vaddr)
        if f:
            v, name, sz = f
            print(f"  vaddr={vaddr:#x} in/near {name} @ {v:#x} (size {sz})")
        else:
            print(f"  vaddr={vaddr:#x} no enclosing function")


if __name__ == "__main__":
    main()
