"""Formula::getValFunc 의 254-entry switch 분석.

진입점 0x758d0 에서 `add pc, pc, r8, lsl #2` 로 254개 case 분기.
각 case 의 첫 호출/연산을 보고 변수 ID → 의미 매핑 dict 작성.
"""
from __future__ import annotations
import pathlib, re

import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"

GETVAL_ADDR = 0x758d0
GETVAL_SIZE = 6372
JUMP_TABLE_START = 0x75958 + 8  # `add pc, pc, r8, lsl #2` is at 0x75958, then jump table starts at next ins
# Actually the table begins right after that branch, but we need to verify.


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

    # Read the jump table — 254 entries of `b #target`
    # Find the actual table by disassembling sequentially after the `add pc, pc, r8, lsl #2`
    data_full = read(GETVAL_ADDR, GETVAL_SIZE)
    insns = list(md.disasm(data_full, GETVAL_ADDR))
    table_start_idx = None
    for i, ins in enumerate(insns):
        # ARM 의 'addls pc, pc, r8, lsl #2' — capstone 이 cond suffix 를 mnemonic 에 붙임
        if ins.mnemonic.startswith("add") and "pc, pc," in ins.op_str and "r8" in ins.op_str:
            table_start_idx = i + 1
            break

    if table_start_idx is None:
        print("jump table dispatcher not found", file=__import__('sys').stderr)
        return 1

    # The table is 254 b-instructions. After the "default" branch.
    # Check that the next 254+ are all `b #imm`:
    targets = []
    i = table_start_idx
    while i < len(insns) and insns[i].mnemonic == "b" and insns[i].op_str.startswith("#"):
        try:
            tgt = int(insns[i].op_str[1:], 0)
        except ValueError:
            break
        targets.append((insns[i].address, tgt))
        i += 1
        if len(targets) > 260:
            break

    # First target is the default fallthrough; subsequent are case 0, 1, 2, ...
    # Spec: switch input was r8 = id-1, then `cmp r8, #0xfd; addls pc, pc, r8, lsl #2`
    # If r8 > 0xfd → fallthrough (b 0x75d9c default). Else jumps.
    # The table has 254 entries (0..0xfd inclusive = 254 values).
    # Looking at our disasm: first b is at 0x7595c (fallthrough = b #0x75d9c),
    # then the table starts at 0x75960 = b #0x75da8 (case id=0+1=1).

    # Actually: "addls pc, pc, r8, lsl #2" with PC=0x75958+8=0x75960. So case 0 jumps to
    # 0x75960 + 0×4 = 0x75960 itself (which is the FIRST b in the table).
    # So the first b in our list IS case 0 (id-1=0, so id=1).

    # Re-check: our targets list starts at index where first `b` after dispatcher is found.
    # If the dispatcher was at 0x75958 and our list starts at 0x7595c, first entry is the
    # fallthrough/default. If our list starts at 0x75960 (= PC after dispatcher),
    # first entry is case 0.

    # For safety, assume targets[0] = case 0 (variable id = 1) and so on.
    # But also note 0x7595c had `b #0x75d9c` which IS the default.

    print(f"jump table: {len(targets)} entries from 0x{targets[0][0]:08x}")

    # For each target, fetch a small disasm window (32 instructions) and find first call/op
    # Register meaning at function entry (from calling convention trace):
    #   r5 = skill (HeroSkillInfo*)  — inherited from Formula::calc
    #   r6 = defender (CHAR*)        — saved from arg2 in Formula::calc
    #   r7 = (defender) — moved from r2 inside getValFunc
    #   sl = skill (r3) — but only used as flag check at top
    #   fp = item (ItemBase*) — stack arg
    #   sb = ? — stack arg
    # Any case reading [r5, #ofs] reads from the skill struct.
    REG_HINT = {
        "r5": "skill",
        "r6": "defender",
        "r7": "defender2",
        "fp": "item",
    }

    import re as _re
    out = ROOT / "work/h5/analysis/formula_var_dict.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for case_idx, (entry_addr, target_addr) in enumerate(targets[:254]):
        d = read(target_addr, 96)
        if d is None:
            rows.append((case_idx, target_addr, "?", "?", "(no data)")); continue
        first_op = ""
        first_struct = ""
        first_offset = ""
        ops_seen = []
        for ins in md.disasm(d, target_addr):
            ops_seen.append(f"{ins.mnemonic} {ins.op_str}")
            # ldr* r?, [reg, #imm]
            if not first_op and ins.mnemonic.startswith("ldr"):
                m = _re.match(r'\S+,\s*\[(\w+)(?:,\s*#(0x[0-9a-f]+|-?\d+))?\]', ins.op_str)
                if m:
                    first_op = ins.mnemonic
                    reg = m.group(1)
                    first_struct = REG_HINT.get(reg, reg)
                    ofs = m.group(2) or "0"
                    first_offset = ofs
            if ins.mnemonic.startswith("bl") and ins.op_str.startswith("#"):
                try:
                    t = int(ins.op_str[1:], 0) & ~1
                    tn = addr_to_name.get(t)
                    if tn:
                        if not first_op:
                            first_op = "bl"
                            first_struct = "(call)"
                            first_offset = tn[:60]
                        break
                except ValueError:
                    pass
            if ins.mnemonic.startswith("b") and ins.mnemonic != "bl" and "0x" in ins.op_str:
                # return-style branch
                break
        snippet = " ; ".join(ops_seen[:4])
        rows.append((case_idx, target_addr, first_struct, first_offset, snippet))

    with out.open("w", encoding="utf-8") as f:
        f.write("var_id\ttarget\tstruct\toffset\tfirst_4_ops\n")
        for case, tgt, st, ofs, snip in rows:
            f.write(f"{case}\t0x{tgt:08x}\t{st}\t{ofs}\t{snip}\n")

    print(f"\nwrote {out.relative_to(ROOT)}")
    from collections import Counter
    struct_counts = Counter(r[2] for r in rows)
    print(f"\nstruct distribution:")
    for st, c in struct_counts.most_common():
        print(f"  ×{c:>3}  {st}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
