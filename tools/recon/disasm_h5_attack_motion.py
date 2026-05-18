"""Hero5 HERO::ChangeAttackMotion + CheckWeaponMotion 정밀 디스어셈블 (Round 69).

R67 PASS 1 summary 에서 식별된 미해결 dispatch:
  - cmp r0, #0xd / #0x14 / #0xe / #0x17  (입력 → 분기)
  - mov r1, #0x18 / #0x26 / #0x16 / #0xa / #0xf  (CHAR::SetMotion 인자 = motion id)

R67 가설: 0xd=13/0x14=20/0xe=14/0x17=23 = skill_type 또는 weapon kind?
          0x18=24/0x26=38/0x16=22/0xa=10/0xf=15 = motion id 의 실 값

본 도구는 ChangeAttackMotion (340B) + CheckWeaponMotion (256B) 두 함수의
full disasm 을 출력하고 추가로:
  - cmp imm 패턴 분포
  - mov imm 후 bl SetMotion / bl SetMainState 호출 패턴
  - bl 호출 그래프 (외부 helper 함수)
  - 호출자 식별 (HERO_TakeItem? skill_use_path?)
"""
from __future__ import annotations
import pathlib
import sys
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

import lief
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB


TARGETS = [
    ("_ZN4HERO18ChangeAttackMotionEP13HeroSkillInfo", "HERO::ChangeAttackMotion"),
    ("_ZN4HERO17CheckWeaponMotionEv", "HERO::CheckWeaponMotion"),
]


def find_symbol(b, name: str):
    for s in b.symbols:
        if s.name == name:
            return int(s.value), int(s.size)
    return None, None


def disasm_full(b, data: bytes, name: str, label: str):
    addr, size = find_symbol(b, name)
    if addr is None:
        return None, None, None
    thumb = bool(addr & 1)
    addr_aligned = addr & ~1
    file_offset = None
    for seg in b.segments:
        if seg.virtual_address <= addr_aligned < seg.virtual_address + seg.virtual_size:
            file_offset = seg.file_offset + (addr_aligned - seg.virtual_address)
            break
    if file_offset is None:
        return None, None, None
    chunk = data[file_offset:file_offset + size]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    md.detail = True
    instrs = list(md.disasm(chunk, addr_aligned))
    return addr, instrs, size


def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    # helper symbol 룩업 (bl 타겟 해석용)
    by_addr = {}
    for s in b.symbols:
        v = int(s.value)
        if v & 1:
            v -= 1
        if int(s.size) > 0 and v not in by_addr:
            by_addr[v] = s.name

    for sym, label in TARGETS:
        addr, instrs, size = disasm_full(b, data, sym, label)
        if instrs is None:
            print(f"# [skip] {label} not found")
            continue
        print("=" * 78)
        print(f"# {label} @ {addr:#x} ({size}B, ARM)")
        print("=" * 78)

        cmp_imms = []
        mov_imms = []
        bl_calls = Counter()
        bl_call_seq = []  # ordered list of bl targets
        strb_offsets = defaultdict(list)
        movs_recent = {}  # reg -> imm just before next bl

        for ins in instrs:
            m, op = ins.mnemonic, ins.op_str
            print(f"  {ins.address:08x}: {m:8} {op}")
            if m == "cmp" and "#" in op:
                parts = op.split(", ")
                if len(parts) == 2 and parts[1].startswith("#"):
                    try:
                        imm = int(parts[1][1:], 0)
                        cmp_imms.append((ins.address, parts[0], imm))
                    except ValueError:
                        pass
            if m == "mov" and op.startswith(("r0, #", "r1, #", "r2, #", "r3, #")):
                parts = op.split(", #")
                if len(parts) == 2:
                    try:
                        imm = int(parts[1], 0)
                        mov_imms.append((ins.address, parts[0], imm))
                        movs_recent[parts[0]] = (ins.address, imm)
                    except ValueError:
                        pass
            if m in ("bl", "blx") and op.startswith("#"):
                try:
                    tgt = int(op[1:], 0)
                    bl_calls[tgt] += 1
                    sym_name = by_addr.get(tgt, "?")
                    bl_call_seq.append((ins.address, tgt, sym_name, dict(movs_recent)))
                    movs_recent.clear()
                except ValueError:
                    pass
            if m == "strb" and "[" in op and "#" in op:
                try:
                    left, rest = op.split(", [", 1)
                    rb, off = rest.rstrip("]").split(", #")
                    offset = int(off, 0)
                    strb_offsets[offset].append((ins.address, left, rb))
                except (ValueError, IndexError):
                    pass

        print(f"\n  # --- 패턴 요약 ---")
        print(f"  cmp imm: {len(cmp_imms)}, mov imm to argreg: {len(mov_imms)}, bl: {sum(bl_calls.values())}")
        print(f"  cmp imm 분포: {Counter(imm for _, _, imm in cmp_imms).most_common(10)}")
        print(f"  strb offsets (this+off): {sorted(strb_offsets.keys())}")
        print(f"\n  # --- bl 호출 그래프 (순서대로) ---")
        for caller_addr, tgt, sym_name, movs in bl_call_seq:
            args = ", ".join(f"{r}={v:#x}" for r, (_, v) in movs.items())
            short = sym_name.replace("_ZN", "").replace("E", "")
            print(f"    @{caller_addr:08x} → {tgt:#x} ({sym_name})   args: [{args}]")
        print()


if __name__ == "__main__":
    main()
