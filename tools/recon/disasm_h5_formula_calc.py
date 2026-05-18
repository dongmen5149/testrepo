"""Hero5 Formula::calc (@0x7749c) 정밀 disasm (Round 71).

목적: ProcHeroSkill 안의 `Formula::calc(id=0x6f=111, ...)` 호출에서 id 가 calc_pl
범위 (0..38) 밖인데 어떻게 dispatch 되는지 확인. 또한 id=0x63=99 의 의미.

R5 BATTLE_FORMULA.md: id 0-999 → calc_pl, 1000-1999 → calc_en, 2000-3007 → calc_sk.
"""
from __future__ import annotations
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM

def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)
    # ELF symbol resolve
    by_addr = {}
    for s in b.symbols:
        v = int(s.value) & ~1
        sz = int(s.size)
        if sz > 0:
            by_addr.setdefault(v, []).append(s.name)

    # Formula::calc (target 0x7749c)
    target_addr = 0x7749c
    target_size = None
    for s in b.symbols:
        if s.name == "_ZN7Formula4calcEiP4CHARS1_P13HeroSkillInfoP8ItemBase":
            target_size = int(s.size)
            break
    print(f"# Formula::calc @ {target_addr:#x} (size {target_size}B)")

    # segment mapping
    file_off = None
    for seg in b.segments:
        if seg.virtual_address <= target_addr < seg.virtual_address + seg.virtual_size:
            file_off = seg.file_offset + (target_addr - seg.virtual_address)
            break
    chunk = data[file_off:file_off + target_size]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    instrs = list(md.disasm(chunk, target_addr))
    print(f"# {len(instrs)} instructions")
    print()
    for ins in instrs:
        sym = ""
        if ins.mnemonic in ("bl", "blx") and ins.op_str.startswith("#"):
            try:
                tgt = int(ins.op_str[1:], 0)
                names = by_addr.get(tgt & ~1, [])
                if names:
                    sym = f"  ; {names[0]}"
            except ValueError:
                pass
        print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{sym}")


if __name__ == "__main__":
    main()
