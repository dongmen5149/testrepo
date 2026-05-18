"""QuestCheck inner BL 함수 추적 + cond_type 14/13/17 의미 RE (Round 60).

Round 59 에서 QuestMgr::QuestCheck (@0xd3acc, 1492B) 의 inner BL 발견:
  - 0xd1df8 × 3 calls
  - 0x890c8 × 2 calls

이 두 함수를 디스어셈블해서:
  1. 심볼 이름 (있으면) — ELF symtab cross-check
  2. CMP imm 패턴 + 분기 — cond_type 14/13/17 의 case dispatch 있는지
  3. LDRB pattern — phase1 objective byte (type/sub/value) 어디서 읽는지
  4. 진입 인자 의미 (r0/r1/r2)

cond_type 분포 (Round 56 sweep):
  14 (38건) — most common
  13 (8건)
  17 (7건)
  255 (400건) = unused placeholder

이 type code 들이 QuestCheck inner BL 에서 어떻게 처리되는지 발견하는 것이 목표.
"""
from __future__ import annotations
import pathlib, sys, re
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB


# 추적 대상
INNER_FUNCS = [0xd1df8, 0x890c8]


def main() -> None:
    g = select("h5")
    bin_path = g.binary_path
    print(f"# Round 60 QuestCheck inner BL RE\n")

    with open(bin_path, "rb") as f:
        elf = ELFFile(f)
        # 1. 모든 심볼 수집해서 inner func 주소에 매칭되는 이름 찾기
        all_syms: dict[int, list[str]] = {}
        for section in elf.iter_sections():
            if section.name not in (".symtab", ".dynsym"): continue
            for sym in section.iter_symbols():
                addr = sym["st_value"] & ~1
                if addr == 0 or sym["st_size"] == 0: continue
                all_syms.setdefault(addr, []).append({
                    "name": sym.name,
                    "size": sym["st_size"],
                    "thumb": bool(sym["st_value"] & 1),
                })
        f.seek(0); data = f.read()

    # 2. 각 inner BL 의 정체 확인
    print("=== inner BL 함수 식별 ===")
    inner_meta = {}
    for addr in INNER_FUNCS:
        # exact match
        if addr in all_syms:
            syms = all_syms[addr]
            for s in syms:
                print(f"  {addr:#08x}: '{s['name']}' +{s['size']}B {'T' if s['thumb'] else 'A'}")
                inner_meta[addr] = s
                break
        else:
            # nearest enclosing
            candidates = [(a, s) for a, syms in all_syms.items() for s in syms
                          if a <= addr < a + s["size"]]
            if candidates:
                a, s = candidates[0]
                print(f"  {addr:#08x}: inside '{s['name']}' (@{a:#x} +{s['size']}B)")
                inner_meta[addr] = s
            else:
                print(f"  {addr:#08x}: NO symbol match")

    # 3. 각 inner 함수 디스어셈블
    for addr in INNER_FUNCS:
        meta = inner_meta.get(addr)
        if not meta: continue
        size = meta["size"]
        thumb = meta["thumb"]
        if addr + size > len(data):
            print(f"  ! {addr:#x} OOB"); continue

        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
        instrs = list(md.disasm(data[addr:addr + size], addr))
        print(f"\n\n=== {meta['name']} @ {addr:#x} +{size}B {'T' if thumb else 'A'} ===")
        print(f"  total instructions: {len(instrs)}")

        # CMP imm 패턴
        print("\n  CMP imm + branch:")
        cmps = []
        for i, ins in enumerate(instrs):
            if ins.mnemonic == "cmp" and "#" in ins.op_str:
                m = re.search(r"#(0x[0-9a-f]+|-?\d+)", ins.op_str)
                if m:
                    v = m.group(1)
                    imm = int(v, 16) if v.startswith("0x") else int(v)
                    if -16 <= imm <= 255:
                        cmps.append((ins.address, imm, ins))
        # 중복 제거
        seen = set()
        for a, imm, ins in cmps[:30]:
            if imm in seen: continue
            seen.add(imm)
            # 다음 instr 도 출력
            nxt = next((x for x in instrs if x.address > ins.address), None)
            nxt_str = f" → {nxt.mnemonic} {nxt.op_str[:40]}" if nxt else ""
            print(f"    {ins.address:08x}: cmp ?, #{imm} ({imm:#x}){nxt_str}")

        # LDRB offset 빈도
        ldrb_offs = Counter()
        for ins in instrs:
            if ins.mnemonic in ("ldrb", "ldrsb"):
                m = re.search(r"#(0x[0-9a-f]+|\d+)", ins.op_str)
                if m:
                    v = m.group(1)
                    off = int(v, 16) if v.startswith("0x") else int(v)
                    ldrb_offs[off] += 1
        print("\n  LDRB/LDRSB offsets (top 10):")
        for off, cnt in ldrb_offs.most_common(10):
            print(f"    +{off:#06x}: {cnt} reads")

        # BL targets
        bl_tgts = Counter()
        for ins in instrs:
            if ins.mnemonic == "bl":
                m = re.search(r"#(0x[0-9a-f]+)", ins.op_str)
                if m:
                    bl_tgts[int(m.group(1), 16)] += 1
        print("\n  BL targets (top 10):")
        for tgt, cnt in bl_tgts.most_common(10):
            # nearest symbol
            sym_name = ""
            for a, syms in all_syms.items():
                if a <= tgt < a + syms[0]["size"]:
                    sym_name = syms[0]["name"]
                    if a == tgt:
                        sym_name = f"{syms[0]['name']} (exact)"
                    break
            print(f"    {tgt:#08x}: {cnt}× — {sym_name[:80]}")

        # 첫 40 instructions
        print("\n  First 40 instructions:")
        for ins in instrs[:40]:
            print(f"    {ins.address:08x}: {ins.mnemonic:6} {ins.op_str}")


if __name__ == "__main__":
    main()
