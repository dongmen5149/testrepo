"""Hero5 HERO::ProcHeroSkill (@0x99278, 7972B) 구조 스캔 (Round 70).

7972B 거대 함수 — full disasm 은 너무 크므로 패턴 추출 + 핵심 영역 zoom:
  1. PASS 1: 함수 전체에서 cmp imm + bl target + ldrb [r1, #imm] (skill_info field access)
     + ldrb [r4, #imm] (this field access) 패턴 분포 수집
  2. PASS 2: entry (+0x0..+0x80) 정밀 disasm — initial dispatch 영역
  3. PASS 3: ChangeAttackMotion 호출 영역 (offset +0x488 = 0x99700 ± 0x40) 정밀 disasm
  4. helper 호출 그래프 + symbol resolution
  5. jumptable 후보 (addls pc, pc, r{N}, lsl #2 패턴) 검출
"""
from __future__ import annotations
import pathlib
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

import lief
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


PROC_HERO_SKILL = 0x99278
PROC_HERO_SKILL_SIZE = 7972


def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    # helper symbol 룩업
    by_addr = {}
    for s in b.symbols:
        v = int(s.value) & ~1
        sz = int(s.size)
        if sz > 0:
            by_addr.setdefault(v, []).append(s.name)

    # 함수 영역 → file offset
    file_offset = None
    for seg in b.segments:
        if seg.virtual_address <= PROC_HERO_SKILL < seg.virtual_address + seg.virtual_size:
            file_offset = seg.file_offset + (PROC_HERO_SKILL - seg.virtual_address)
            break
    assert file_offset is not None
    chunk = data[file_offset:file_offset + PROC_HERO_SKILL_SIZE]

    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True
    instrs = list(md.disasm(chunk, PROC_HERO_SKILL))
    print(f"# ProcHeroSkill @ {PROC_HERO_SKILL:#x} — 총 instruction: {len(instrs)}\n")

    # ============= PASS 1: 패턴 분포 =============
    cmp_imms = []
    bl_targets = Counter()
    bl_seq = []
    field_r1 = defaultdict(int)
    field_r4 = defaultdict(int)
    field_r5 = defaultdict(int)
    field_r6 = defaultdict(int)  # r6 = skill_info backup (0x99290 mov r6, r1)
    field_r7 = defaultdict(int)
    addls_jt = []

    for ins in instrs:
        m, op = ins.mnemonic, ins.op_str
        if m == "cmp" and "#" in op:
            parts = op.split(", ")
            if len(parts) == 2 and parts[1].startswith("#"):
                try:
                    imm = int(parts[1][1:], 0)
                    cmp_imms.append((ins.address, parts[0], imm))
                except ValueError:
                    pass
        elif m in ("bl", "blx") and op.startswith("#"):
            try:
                tgt = int(op[1:], 0)
                bl_targets[tgt] += 1
                bl_seq.append((ins.address, tgt))
            except ValueError:
                pass
        elif m in ("ldrb", "ldr", "ldrsb", "ldrh", "ldrsh") and "[" in op and "#" in op:
            try:
                # 예: ldrb r3, [r1, #0x10]
                _, rest = op.split(", [", 1)
                rest = rest.rstrip("]")
                parts = rest.split(", #")
                if len(parts) == 2:
                    rb = parts[0]
                    offset = int(parts[1], 0)
                    if rb == "r1":
                        field_r1[(m, offset)] += 1
                    elif rb == "r4":
                        field_r4[(m, offset)] += 1
                    elif rb == "r5":
                        field_r5[(m, offset)] += 1
                    elif rb == "r6":
                        field_r6[(m, offset)] += 1
                    elif rb == "r7":
                        field_r7[(m, offset)] += 1
            except (ValueError, IndexError):
                pass
        elif m == "addls" and "pc, pc," in op and "lsl #2" in op:
            addls_jt.append((ins.address, op))

    print("# === PASS 1: 패턴 분포 ===")
    print(f"\ncmp imm 분포 (top 15):")
    cmp_imm_counter = Counter(imm for _, _, imm in cmp_imms)
    for imm, cnt in cmp_imm_counter.most_common(15):
        print(f"  #{imm:#x} ({imm}): {cnt}회")

    print(f"\nbl 호출 target (top 20):")
    for tgt, cnt in bl_targets.most_common(20):
        names = by_addr.get(tgt, ["?"])
        print(f"  {tgt:#x}: {cnt}회 — {names[0]}")

    print(f"\nHeroSkillInfo (r1) field access (top 15, sorted by offset):")
    for (m, off), cnt in sorted(field_r1.items(), key=lambda x: x[0][1]):
        print(f"  [r1, +{off:#04x}]  {m:6}  {cnt}회")

    print(f"\nHERO this (r4) field access (sorted by offset):")
    for (m, off), cnt in sorted(field_r4.items(), key=lambda x: x[0][1])[:30]:
        print(f"  [r4, +{off:#04x}]  {m:6}  {cnt}회")

    print(f"\nHeroSkillInfo (r6 = skill_info backup) field access (sorted by offset):")
    for (m, off), cnt in sorted(field_r6.items(), key=lambda x: x[0][1])[:30]:
        print(f"  [r6, +{off:#04x}]  {m:6}  {cnt}회")

    print(f"\nr5 (보조 base) field access (sorted by offset):")
    for (m, off), cnt in sorted(field_r5.items(), key=lambda x: x[0][1])[:30]:
        print(f"  [r5, +{off:#04x}]  {m:6}  {cnt}회")

    print(f"\nJumptable (addls pc, pc, rN, lsl #2) 발견: {len(addls_jt)}회")
    for addr, op in addls_jt:
        print(f"  @{addr:#x}  {op}")
        # jumptable 직전 cmp imm 추출 (dispatch key)
        for cmp_addr, reg, imm in reversed(cmp_imms):
            if cmp_addr < addr and addr - cmp_addr < 0x20:
                print(f"    ← dispatch key: @{cmp_addr:#x}  cmp {reg}, #{imm}")
                break

    # ============= PASS 2: entry 영역 (+0x0..+0x80) =============
    print("\n\n# === PASS 2: entry 영역 (+0x0..+0x80) 정밀 disasm ===")
    for ins in instrs:
        if ins.address >= PROC_HERO_SKILL + 0x80:
            break
        print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")

    # ============= PASS 3: ChangeAttackMotion 호출 영역 (+0x488 ± 0x40) =============
    target_addr = PROC_HERO_SKILL + 0x488
    print(f"\n\n# === PASS 3: ChangeAttackMotion 호출 영역 ({target_addr-0x40:#x}..{target_addr+0x40:#x}) ===")
    for ins in instrs:
        if target_addr - 0x40 <= ins.address < target_addr + 0x40:
            marker = "  <-- ChangeAttackMotion call" if ins.address == target_addr else ""
            print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}{marker}")

    # ============= PASS 4: jumptable 영역 (각 jumptable 직전/직후) =============
    if addls_jt:
        for jt_addr, _ in addls_jt:
            print(f"\n\n# === PASS 4: jumptable @ {jt_addr:#x} 직전 12 + 직후 16 instr ===")
            jt_idx = -1
            for i, ins in enumerate(instrs):
                if ins.address == jt_addr:
                    jt_idx = i
                    break
            assert jt_idx >= 0
            for ins in instrs[max(0, jt_idx-12):jt_idx]:
                print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
            print(f"  -- jumptable here --")
            for ins in instrs[jt_idx:jt_idx+18]:
                print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
