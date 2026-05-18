"""QuestMgr::QuestCheck @ 0xd3acc 의 전체 디스어셈블 + cond_type dispatch 추론 (Round 59).

QuestMgr::QuestCheck(a,b,c,d) — 1492B 의 큰 함수. cond_type (Round 56 의
14/13/17 분포) 의 dispatch 가 여기에 있을 가능성. CMP imms 외에 LDRB 패턴
(`ldrb rN, [obj, #imm]`) 도 추출해서 phase1 objective 의 byte 0 (type) 가 어디서
어떻게 분기하는지 파악.

부수: LoadQuestData 의 layout 처리도 같이 추출 (struct +0x114..+0x128 phase1 offsets).
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
        symbols = {}
        for section in elf.iter_sections():
            if section.name not in (".symtab", ".dynsym"): continue
            for sym in section.iter_symbols():
                if sym.name == "_ZN8QuestMgr10QuestCheckEaaaa":
                    symbols["QuestCheck"] = (sym["st_value"] & ~1, sym["st_size"])
        f.seek(0); data = f.read()

    addr, size = symbols["QuestCheck"]
    print(f"# QuestMgr::QuestCheck @ {addr:#x} +{size}B (ARM)\n")

    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True
    buf = data[addr:addr + size]

    # 1. CMP imms 와 그 후 BNE 패턴 — case 후보
    print("=== CMP #imm + branch (case dispatch) ===")
    instrs = list(md.disasm(buf, addr))
    for i, ins in enumerate(instrs):
        if ins.mnemonic == "cmp" and "#" in ins.op_str:
            m = re.search(r"#(0x[0-9a-f]+|-?\d+)", ins.op_str)
            if m:
                v = m.group(1)
                imm = int(v, 16) if v.startswith("0x") else int(v)
                if 0 <= imm <= 50:
                    # 다음 1-2 instruction 도 출력
                    nxt = instrs[i + 1] if i + 1 < len(instrs) else None
                    nxt_str = f" → {nxt.mnemonic} {nxt.op_str}" if nxt else ""
                    print(f"  {ins.address:08x}: {ins.mnemonic:6} {ins.op_str:18s}{nxt_str}")

    # 2. LDRB / LDRSB — byte field reads (phase1 objective byte fetch 후보)
    print("\n=== LDRB/LDRSB (byte field reads) — top frequency offsets ===")
    from collections import Counter
    off_counter = Counter()
    for ins in instrs:
        if ins.mnemonic in ("ldrb", "ldrsb"):
            m = re.search(r"#(0x[0-9a-f]+|\d+)", ins.op_str)
            if m:
                v = m.group(1)
                imm = int(v, 16) if v.startswith("0x") else int(v)
                off_counter[imm] += 1
    for off, cnt in off_counter.most_common(15):
        print(f"  +{off:#06x}: {cnt} reads")

    # 3. BL (function calls) — what does QuestCheck dispatch to?
    print("\n=== BL calls ===")
    bl_targets = Counter()
    for ins in instrs:
        if ins.mnemonic == "bl":
            m = re.search(r"#(0x[0-9a-f]+)", ins.op_str)
            if m:
                bl_targets[int(m.group(1), 16)] += 1
    for tgt, cnt in bl_targets.most_common(20):
        print(f"  {tgt:#08x}: {cnt} calls")

    # 4. 첫 80 instructions 자세히
    print("\n=== First 80 instructions ===")
    for ins in instrs[:80]:
        print(f"  {ins.address:08x}: {ins.mnemonic:6} {ins.op_str}")


if __name__ == "__main__":
    main()
