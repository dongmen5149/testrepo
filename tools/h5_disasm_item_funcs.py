"""ItemInfo / EquipItemInfo 구조체 layout 추출.

CopyData 함수의 ldr/str 오프셋 패턴을 분석하면 멤버 변수 offset 이 모두 노출됨.
"""
from __future__ import annotations
import pathlib

import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"

TARGETS = [
    "_ZN13EquipItemInfo8CopyDataEPS_",
    "_ZN9ItemTable16GetItemTableInfoEP8ItemInfoaa",
    "_ZN13EquipItemInfo15IsEquipPossibleEa",
    "_ZN9ItemTable22GetSimpleItemTableInfoEP8ItemInfoaa",
    "_ZN9ItemTable13SetItemOptionEP8ItemInfoa",
    "_ZN15EquipItemSpirit18SetEquipItemSpiritEas",
    "_ZN9EquipItem12SetEquipItemEas",
]


def main() -> int:
    so = lief.parse(str(SO))
    seg = [(s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content))
           for s in so.segments if s.type == lief.ELF.Segment.TYPE.LOAD]

    def read(va, sz):
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va-v0:va-v0+sz])

    addr_to_name = {}
    for s in so.symbols:
        n = s.name or ""
        if n and s.value and s.size:
            addr_to_name.setdefault(s.value & ~1, n)

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    out = ROOT / "work/h5/analysis/item_funcs.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for sym_name in TARGETS:
            info = None
            for s in so.symbols:
                if s.name == sym_name and s.size:
                    info = (s.value & ~1, s.size); break
            if not info:
                f.write(f"\n=== {sym_name} ===\n  not found\n"); continue
            addr, sz = info
            data = read(addr, sz)
            f.write(f"\n=== {sym_name}  @0x{addr:08x}  size={sz} ===\n")
            for ins in md.disasm(data, addr):
                cmt = ""
                if ins.mnemonic.startswith(("bl", "b")) and ins.op_str.startswith("#"):
                    try:
                        t = int(ins.op_str[1:], 0) & ~1
                        tn = addr_to_name.get(t)
                        if tn:
                            cmt = f"  ; -> {tn[:90]}"
                    except ValueError:
                        pass
                f.write(f"  0x{ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}{cmt}\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
