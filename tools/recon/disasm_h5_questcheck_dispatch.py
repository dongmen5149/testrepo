"""QuestCheck 의 cond_type dispatch 위치 찾기 (Round 60).

QuestCheck (@ 0xd3acc, 1492B) 내부에서 phase1 objective 의 type byte (+0x114) 를
LDRB 한 직후 dispatch 패턴을 찾는다. LDRB 후 CMP imm 으로 cond_type 14/13/17
같은 값과 비교하는지 확인.
"""
from __future__ import annotations
import pathlib, sys, re

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


def main() -> None:
    g = select("h5")
    bin_path = g.binary_path
    with open(bin_path, "rb") as f:
        elf = ELFFile(f)
        addr = None; size = None
        for section in elf.iter_sections():
            if section.name not in (".symtab", ".dynsym"): continue
            for sym in section.iter_symbols():
                if sym.name == "_ZN8QuestMgr10QuestCheckEaaaa":
                    addr = sym["st_value"] & ~1
                    size = sym["st_size"]
        f.seek(0); data = f.read()

    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    instrs = list(md.disasm(data[addr:addr + size], addr))
    print(f"# QuestCheck dispatch trace (LDRB +0x114, +0x115, +0x116 context)")

    for i, ins in enumerate(instrs):
        # phase1 시작 offset 가 0x114 / 0x115 / 0x116 (type/sub/value bytes)
        if ins.mnemonic in ("ldrb", "ldrsb"):
            m = re.search(r"#(0x[0-9a-f]+|\d+)", ins.op_str)
            if not m: continue
            v = m.group(1)
            off = int(v, 16) if v.startswith("0x") else int(v)
            # phase1 objective bytes 영역
            if not (0x114 <= off <= 0x140):
                continue
            print(f"\n--- {ins.address:08x}: {ins.mnemonic} {ins.op_str}  (phase1 byte at +{off:#x}) ---")
            # 다음 10 instructions 출력
            for j in range(i, min(i + 12, len(instrs))):
                marker = " ← target" if j == i else ""
                print(f"  {instrs[j].address:08x}: {instrs[j].mnemonic:8} {instrs[j].op_str}{marker}")

    # 추가: CMP r?, #13 / #14 / #17 / #0xd / #0xe / #0x11 검색 (case key 추정값)
    print("\n\n# CMP with cond_type 후보값 (13/14/17/0xd/0xe/0x11):")
    targets = {13, 14, 17, 0xd, 0xe, 0x11}
    hits = []
    for i, ins in enumerate(instrs):
        if ins.mnemonic != "cmp" or "#" not in ins.op_str: continue
        m = re.search(r"#(0x[0-9a-f]+|-?\d+)", ins.op_str)
        if not m: continue
        v = m.group(1)
        imm = int(v, 16) if v.startswith("0x") else int(v)
        if imm in targets:
            hits.append((i, ins, imm))
    for i, ins, imm in hits:
        # 컨텍스트 5줄
        print(f"\n  {ins.address:08x}: {ins.mnemonic} {ins.op_str} (matches {imm:#x})")
        for j in range(max(0, i - 3), min(i + 4, len(instrs))):
            print(f"    {instrs[j].address:08x}: {instrs[j].mnemonic:8} {instrs[j].op_str}")

    # 추가: 0xd3cb0 의 case dispatch 영역 (jumptable)
    print("\n\n# Jumptable dispatch around 0xd3cb0 (case 0..3):")
    for ins in instrs:
        if 0xd3cb0 <= ins.address <= 0xd3d00:
            print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
