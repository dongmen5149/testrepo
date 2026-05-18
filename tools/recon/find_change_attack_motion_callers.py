"""HERO::ChangeAttackMotion (@0x91e7c) 호출자 식별.

bl/blx #0x91e7c 명령어를 .so 전체에서 찾아 호출 위치 + 호출자 함수 식별.
"""
from __future__ import annotations
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

import os
TARGET = int(os.environ.get("TARGET_ADDR", "0x91e7c"), 0)


def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    # text segment 추출
    text_seg = None
    for seg in b.segments:
        if seg.flags == 5:  # R+X
            text_seg = seg
            break
    if text_seg is None:
        for seg in b.segments:
            if (int(seg.flags) & 1) != 0:
                text_seg = seg
                break
    base = int(text_seg.virtual_address)
    file_off = int(text_seg.file_offset)
    size = int(text_seg.virtual_size)
    chunk = data[file_off:file_off + size]

    # 함수 심볼 → 주소 범위 매핑
    funcs = []  # [(start, end, name), ...]
    for s in b.symbols:
        v = int(s.value)
        sz = int(s.size)
        if sz == 0:
            continue
        addr = v & ~1
        funcs.append((addr, addr + sz, s.name))
    funcs.sort()

    def find_func(addr):
        # binary search
        lo, hi = 0, len(funcs)
        while lo < hi:
            mid = (lo + hi) // 2
            s, e, _ = funcs[mid]
            if addr < s:
                hi = mid
            elif addr >= e:
                lo = mid + 1
            else:
                return funcs[mid]
        return None

    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = False
    instrs = md.disasm(chunk, base)
    callers = []
    for ins in instrs:
        if ins.mnemonic in ("bl", "blx") and ins.op_str == f"#{TARGET:#x}":
            f = find_func(ins.address)
            callers.append((ins.address, f))

    print(f"# Found {len(callers)} call sites to HERO::ChangeAttackMotion @ {TARGET:#x}\n")
    for addr, f in callers:
        if f:
            start, end, name = f
            offset = addr - start
            print(f"  {addr:#x}  in  {name}  (@{start:#x}, offset +{offset:#x} / size {end-start})")
        else:
            print(f"  {addr:#x}  (unknown function)")


if __name__ == "__main__":
    main()
