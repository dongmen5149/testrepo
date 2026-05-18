"""Thumb-2 BL 명령으로 0x91e7c 호출하는 위치 찾기.

Thumb-2 BL 인코딩 (4 byte LE pair):
  upper: 11110 S imm10[9:0]   (0xf000~0xf7ff bits)
  lower: 11 J1 1 J2 imm11[10:0]   (0xd000~0xffff bits, J1=1/J2=1 for BL)

본 도구는 4 byte sliding window 로 BL 후보 추출 + target 계산 + 0x91e7c 일치 검사.
"""
from __future__ import annotations
import pathlib, sys, struct
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief

TARGETS = {0x91e7c, 0x91e7d}  # ARM/thumb variants

def decode_thumb_bl(upper: int, lower: int, pc_after: int):
    """Decode Thumb-2 BL. Returns target or None."""
    if (upper & 0xf800) != 0xf000:
        return None
    if (lower & 0xd000) != 0xd000:
        return None
    S = (upper >> 10) & 1
    imm10 = upper & 0x3ff
    J1 = (lower >> 13) & 1
    J2 = (lower >> 11) & 1
    imm11 = lower & 0x7ff
    I1 = 1 ^ (J1 ^ S)
    I2 = 1 ^ (J2 ^ S)
    sign = -1 if S else 1
    imm = (I1 << 23) | (I2 << 22) | (imm10 << 12) | (imm11 << 1)
    if S:
        imm |= 0xff000000
        imm = imm - 0x100000000
    return pc_after + imm


def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    text_seg = None
    for seg in b.segments:
        flags = int(seg.flags)
        if (flags & 1) and seg.virtual_size > 0:
            text_seg = seg
            break
    base = int(text_seg.virtual_address)
    file_off = int(text_seg.file_offset)
    size = int(text_seg.virtual_size)

    # 함수 심볼 lookup for enclosing
    funcs = []
    for s in b.symbols:
        v = int(s.value) & ~1
        sz = int(s.size)
        if sz > 0:
            funcs.append((v, v + sz, s.name))
    funcs.sort()
    def find_enclosing(addr):
        lo, hi = 0, len(funcs)
        while lo < hi:
            mid = (lo + hi) // 2
            s, e, n = funcs[mid]
            if addr < s:
                hi = mid
            elif addr >= e:
                lo = mid + 1
            else:
                return funcs[mid]
        return None

    hits = []
    # iterate every 2-byte alignment (Thumb)
    for off in range(file_off, file_off + size - 4, 2):
        upper = struct.unpack("<H", data[off:off+2])[0]
        lower = struct.unpack("<H", data[off+2:off+4])[0]
        pc = base + (off - file_off) + 4  # PC ahead by 4 in Thumb
        target = decode_thumb_bl(upper, lower, pc)
        if target is None:
            continue
        if (target & ~1) == 0x91e7c:
            instr_addr = base + (off - file_off)
            hits.append((instr_addr, target))

    print(f"# Thumb-2 BL hits to 0x91e7c: {len(hits)}\n")
    for addr, tgt in hits[:50]:
        f = find_enclosing(addr)
        if f:
            s, e, n = f
            print(f"  {addr:#10x}  in  {n}  (@{s:#x}, offset +{addr-s:#x})")
        else:
            print(f"  {addr:#10x}  (no enclosing func)")


if __name__ == "__main__":
    main()
