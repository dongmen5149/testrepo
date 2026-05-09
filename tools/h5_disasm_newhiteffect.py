"""HERO::NewHitEffect 와 HeroSkillAtkHardCode disasm + 분석.

1712B / 888B 크기의 핵심 데미지 함수에서 ATK/DEF/Crit 공식을 추출.
"""
from __future__ import annotations
import pathlib, sys

import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"

TARGETS = [
    ("_ZN4HERO12NewHitEffectEP13HeroSkillInfoP7BATTLER",
     "HERO::NewHitEffect(HeroSkillInfo*, BATTLER*)"),
    ("_ZN4HERO20HeroSkillAtkHardCodeEP13HeroSkillInfoP7BATTLER",
     "HERO::HeroSkillAtkHardCode(HeroSkillInfo*, BATTLER*)"),
    ("_ZN12TargetEffect12NewHitEffectEP13HeroSkillInfoP7BATTLER",
     "TargetEffect::NewHitEffect(HeroSkillInfo*, BATTLER*)"),
]


def main() -> int:
    so = lief.parse(str(SO))
    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    def read(va: int, sz: int) -> bytes | None:
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va - v0 : va - v0 + sz])
        return None

    addr_to_name: dict[int, str] = {}
    for s in so.symbols:
        n = s.name or ""
        if n and s.value and s.size:
            addr_to_name.setdefault(s.value & ~1, n)

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    out = ROOT / "work/h5/analysis/battle_newhiteffect.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for mangled, pretty in TARGETS:
            info = None
            for s in so.symbols:
                if s.name == mangled and s.size:
                    info = (s.value & ~1, s.size); break
            if not info:
                f.write(f"\n=== {pretty} ===\n  (not found)\n")
                continue
            addr, sz = info
            data = read(addr, sz)
            f.write(f"\n=== {pretty}  @0x{addr:08x}  size={sz}  ===\n")
            for ins in md.disasm(data, addr):
                comment = ""
                if ins.mnemonic.startswith(("bl", "b")) and ins.op_str.startswith("#"):
                    try:
                        tgt = int(ins.op_str[1:], 0) & ~1
                        tn = addr_to_name.get(tgt)
                        if tn:
                            comment = f"  ; -> {tn[:100]}"
                    except ValueError:
                        pass
                f.write(f"  0x{ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}{comment}\n")

    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
