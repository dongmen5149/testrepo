"""특정 함수 (Formula::calc 호출자) 를 disasm 해서 호출 직전 패턴 분석.

CommonUi::GetSkillDiscription 가 8개 calc_pl 호출 모두 포함 → 좋은 샘플.
"""
from __future__ import annotations
import pathlib
import sys

import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "_ZN8CommonUi19GetSkillDiscriptionEPcaP13HeroSkillInfo"
    so = lief.parse(str(SO))
    addr_to_name = {}
    info = None
    for s in so.symbols:
        if not s.value or not s.size:
            continue
        a = s.value & ~1
        addr_to_name.setdefault(a, s.name or "")
        if s.name == target:
            info = (a, s.size)
    if not info:
        print(f"[!] {target} 없음")
        return 1
    addr, sz = info
    seg = [(s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content))
           for s in so.segments if s.type == lief.ELF.Segment.TYPE.LOAD]
    data = b""
    for v0, v1, d in seg:
        if v0 <= addr < v1:
            data = d[addr - v0: addr - v0 + sz]
            break
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    print(f"=== {target}  @0x{addr:08x}  size={sz} ===")
    for ins in md.disasm(data, addr):
        line = f"  0x{ins.address:08x}  {ins.mnemonic:<6} {ins.op_str}"
        # bl target 표시
        if ins.mnemonic in ("bl", "blx") and ins.op_str.startswith("#"):
            try:
                t = int(ins.op_str[1:], 0) & ~1
                tn = addr_to_name.get(t)
                if tn:
                    # simple demangle
                    s = tn[3:] if tn.startswith("_ZN") else tn
                    line += f"  ; -> {tn[:80]}"
            except ValueError:
                pass
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
