"""HERO::HeroSkillAtkHardCode disasm — 클래스/스킬별 하드코드 분기.

888B, callee 37개. Formula VM 을 우회하는 직접 계산 코드가 있을 가능성.
"""
from __future__ import annotations
import pathlib

import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"


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

    out = ROOT / "work/h5/analysis/skill_hardcode.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for sym in so.symbols:
            if sym.name == "_ZN4HERO20HeroSkillAtkHardCodeEP13HeroSkillInfoP7BATTLER" and sym.size:
                addr = sym.value & ~1
                sz = sym.size
                f.write(f"=== HERO::HeroSkillAtkHardCode  @0x{addr:08x}  size={sz} ===\n")
                for ins in md.disasm(read(addr, sz), addr):
                    cmt = ""
                    if ins.mnemonic.startswith(("bl", "b")) and ins.op_str.startswith("#"):
                        try:
                            t = int(ins.op_str[1:], 0) & ~1
                            tn = addr_to_name.get(t)
                            if tn:
                                cmt = f"  ; -> {tn[:100]}"
                        except ValueError:
                            pass
                    f.write(f"  0x{ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}{cmt}\n")
                break
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
