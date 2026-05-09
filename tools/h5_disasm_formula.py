"""Formula VM 분석 — Hero5 의 데미지 공식이 어떻게 인코딩되었는지 추적.

Formula::dataLoad → 외부 파일 (csv/dat) 로드.
Formula::calc(formula_id, attacker, defender, skill, item) — 진입점.
Formula::calcByFormula — 스택 기반 인터프리터.
Formula::getValFunc — 6372B 거대 switch (변수 참조).
"""
from __future__ import annotations
import pathlib

import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"

TARGETS = [
    "_ZN7Formula8dataLoadEv",
    "_ZN7Formula4calcEiP4CHARS1_P13HeroSkillInfoP8ItemBase",
    "_ZN7Formula13calcByFormulaEjiP4CHARS1_P13HeroSkillInfoP8ItemBase",
    "_ZN7Formula16getNumberInStackEPhiP4CHARS2_P13HeroSkillInfoP8ItemBase",
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

    out = ROOT / "work/h5/analysis/formula_vm.txt"
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
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
