"""Hero5 NPC Dialog 시스템 전체 디스어셈블 (Round 68).

기존 disasm_h5_dialog_motion.py 의 PASS 1 summary 결과(R67) 를 토대로,
다음 3종 함수의 full 디스어셈블을 출력하고 state machine 식별 자료를 생성.

  - EventProc::Event_DialogWindow @ 0x6eb38 (656B)
  - DIALOG_INFO::DialogWindow_Proc @ 0x71b48 (912B)
  - EventProc::Event_SituateDialogText @ 0x73030 (600B)

추가로 dispatch 가설을 자동 추출:
  - cmp Rn, #imm 패턴 모음
  - strb Rn, [r4, #offset] 패턴 모음 (DIALOG_INFO field write)
  - bl <addr> 호출 그래프 (외부 도움 함수)
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
    ("_ZN9EventProc18Event_DialogWindowEa", "EventProc::Event_DialogWindow"),
    ("_ZN11DIALOG_INFO17DialogWindow_ProcEv", "DIALOG_INFO::DialogWindow_Proc"),
    ("_ZN9EventProc23Event_SituateDialogTextEhahh", "EventProc::Event_SituateDialogText"),
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


def analyze_patterns(instrs):
    """패턴 추출.

    Returns:
        cmp_imms: [(addr, reg, imm), ...]
        field_writes: {offset: [(addr, value_reg, ctx_instr), ...]}
        bl_calls: Counter of target addresses
        mov_imms_to_arg: [(addr, reg, imm), ...]  (r0, r1, r2 만)
    """
    cmp_imms = []
    field_writes = defaultdict(list)
    bl_calls = Counter()
    mov_imms_to_arg = []
    prev_movs = {}  # reg -> last imm value

    for ins in instrs:
        m = ins.mnemonic
        op = ins.op_str
        # cmp Rn, #imm
        if m == "cmp" and "#" in op:
            parts = op.split(", ")
            if len(parts) == 2 and parts[1].startswith("#"):
                try:
                    imm = int(parts[1][1:], 0)
                    cmp_imms.append((ins.address, parts[0], imm))
                except ValueError:
                    pass
        # strb Rn, [Rb, #offset]  (DIALOG_INFO field write 후보)
        if m == "strb" and "[" in op and "#" in op:
            try:
                left, rest = op.split(", [", 1)
                rb, off = rest.rstrip("]").split(", #")
                offset = int(off, 0)
                field_writes[offset].append((ins.address, left, rb))
            except (ValueError, IndexError):
                pass
        # bl/blx target
        if m in ("bl", "blx") and op.startswith("#"):
            try:
                tgt = int(op[1:], 0)
                bl_calls[tgt] += 1
            except ValueError:
                pass
        # mov rN, #imm  (인자 셋업 후보)
        if m == "mov" and op.startswith(("r0, #", "r1, #", "r2, #", "r3, #")):
            parts = op.split(", #")
            if len(parts) == 2:
                try:
                    imm = int(parts[1], 0)
                    mov_imms_to_arg.append((ins.address, parts[0], imm))
                    prev_movs[parts[0]] = imm
                except ValueError:
                    pass
    return cmp_imms, field_writes, bl_calls, mov_imms_to_arg


def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    for sym, label in TARGETS:
        addr, instrs, size = disasm_full(b, data, sym, label)
        if instrs is None:
            print(f"# [skip] {label} not found")
            continue
        print("=" * 78)
        print(f"# {label} @ {addr:#x} ({size}B, ARM)")
        print("=" * 78)
        # 전체 디스어셈블 (압축 X — 패턴 식별용)
        for ins in instrs:
            print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")

        cmp_imms, field_writes, bl_calls, mov_imms = analyze_patterns(instrs)
        print(f"\n  # --- 패턴 요약 ---")
        print(f"  cmp imm 수: {len(cmp_imms)}, strb to base offset 수: {sum(len(v) for v in field_writes.values())}, bl 호출 수: {sum(bl_calls.values())}")
        print(f"  strb offsets used: {sorted(field_writes.keys())}")
        print(f"  주요 bl 호출 target (top 8):")
        for tgt, cnt in bl_calls.most_common(8):
            print(f"    {tgt:#x} : {cnt}회")
        print()


if __name__ == "__main__":
    main()
