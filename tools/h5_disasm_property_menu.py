"""StateInGameMenu::DrawPropertyMenu 의 stat 표시 패턴 추출.

이 함수는 각 stat 라벨을 다음 패턴으로 표시:
  ldr   rA, [pc, #...]    ; rA = string_table_ptr 또는 stat_label
  ...
  ldrsh rB, [r4, #cache_off]  ; rB = HERO+cache_off 값 (calc_pl 결과)
  bl    DrawText           ; 라벨 + 값 출력

추출:
  → (sequence_idx, label_str_va, cache_offset, code_va)

DrawPropertyMenu 가 5072B → 모든 ldr/ldrsh from [r4, #N] 추적해서
N 들의 sequence 를 출력.
"""
from __future__ import annotations
import pathlib
import struct

import lief
import capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/property_menu_offsets.tsv"

TARGET = "_ZN15StateInGameMenu16DrawPropertyMenuEv"


def main() -> int:
    so = lief.parse(str(SO))
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    info = None
    addr_to_name = {}
    for s in so.symbols:
        if not s.value or not s.size:
            continue
        a = s.value & ~1
        addr_to_name.setdefault(a, s.name or "")
        if s.name == TARGET:
            info = (a, s.size)
    if not info:
        print(f"[!] {TARGET} 없음")
        return 1
    fn_addr, fn_sz = info

    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    def get_data(va: int, sz: int) -> bytes | None:
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va - v0: va - v0 + sz])
        return None

    def read_u32(va: int) -> int | None:
        for v0, v1, d in seg:
            if v0 <= va < v1 - 3:
                return struct.unpack_from("<I", d, va - v0)[0]
        return None

    data = get_data(fn_addr, fn_sz)
    if not data:
        return 1

    # 모든 ldr/ldrsh/ldrh from [r4, #N] 추출 (HERO this 가 보통 r4 또는 r5 에 spilled)
    # r4 가 가장 흔한 this pointer placement
    rows = []  # (va, mnemonic, dst, base_reg, offset_imm)
    for ins in md.disasm(data, fn_addr):
        m = ins.mnemonic
        op = ins.op_str
        # ldr* rD, [rB, #N]
        if m in ("ldr", "ldrh", "ldrsh", "ldrb", "ldrsb"):
            # 단순 형태만
            if "[r4, #" in op or "[r5, #" in op or "[fp, #" in op:
                # 각 stat 의 cache offset 추출 — 0x100~0x1800 범위
                try:
                    off_str = op.rsplit("#", 1)[-1].rstrip("]")
                    off_val = int(off_str, 0)
                    if 0x100 <= off_val <= 0x1800:
                        rows.append((ins.address, m, op, off_val))
                except ValueError:
                    pass

    # 출력
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write("seq\tva\tmnemonic\toffset\toperand\n")
        for i, (va, m, op, off) in enumerate(rows):
            f.write(f"{i}\t0x{va:08x}\t{m}\t0x{off:x}\t{op}\n")

    # offset 빈도
    print(f"[+] {OUT} ({len(rows)} ldr*)")
    print()
    print("== unique cache offset 빈도 ==")
    from collections import Counter
    cnt = Counter(off for _, _, _, off in rows)
    for off, c in sorted(cnt.items(), key=lambda r: r[0]):
        print(f"  0x{off:>4x}  ({c}x)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
