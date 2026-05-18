"""Hero5 NPC Dialog + Battle Motion 디스어셈블 (Round 67).

목적:
  - EventProc::Event_DialogWindow (0x6eb38, 656B) — NPC dialog 시스템 entry
  - DIALOG_INFO::DialogWindow_Proc (0x71b48, 912B) — Dialog 진행 처리
  - EventProc::Event_SituateDialogText (0x73030, 600B) — text 배치
  - HERO::ChangeAttackMotion (0x91e7c, 340B) — 공격 motion 전환
  - HERO::CheckWeaponMotion (0x8dd58, 256B) — weapon-specific motion
  - HERO::SetAttackMotion (0x98870, 160B) — attack motion setter
  - HERO::SetDieMotion / SetAttackedMotion / SetWalkMotion 일괄

전략:
  1. lief 로 ELF symbol/segment 매핑
  2. capstone ARM/Thumb 디스어셈블
  3. cmp imm / bl / strb 패턴 추출 → dispatch / state machine 식별
  4. dialog event code + motion enum 확정
"""
from __future__ import annotations
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

import lief
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB


TARGETS = [
    ("_ZN9EventProc18Event_DialogWindowEa", "EventProc::Event_DialogWindow"),
    ("_ZN11DIALOG_INFO17DialogWindow_ProcEv", "DIALOG_INFO::DialogWindow_Proc"),
    ("_ZN9EventProc23Event_SituateDialogTextEhahh", "EventProc::Event_SituateDialogText"),
    ("_ZN4HERO18ChangeAttackMotionEP13HeroSkillInfo", "HERO::ChangeAttackMotion"),
    ("_ZN4HERO17CheckWeaponMotionEv", "HERO::CheckWeaponMotion"),
    ("_ZN4HERO15SetAttackMotionEaa", "HERO::SetAttackMotion"),
    ("_ZN4HERO12SetDieMotionEv", "HERO::SetDieMotion"),
    ("_ZN4HERO17SetAttackedMotionEaa", "HERO::SetAttackedMotion"),
    ("_ZN4HERO13SetWalkMotionEa", "HERO::SetWalkMotion"),
    ("_ZN4HERO9SetMotionEa", "CHAR::SetMotion (HERO override)"),
    ("_ZN4CHAR9SetMotionEa", "CHAR::SetMotion"),
]


def find_symbol(b, name: str):
    for s in b.symbols:
        if s.name == name:
            return int(s.value), int(s.size)
    return None, None


def disasm_one(b, file_data: bytes, name: str, label: str, summary_only: bool = False) -> None:
    addr, size = find_symbol(b, name)
    if addr is None:
        print(f"# [skip] {name} not found")
        return
    thumb = bool(addr & 1)
    addr_aligned = addr & ~1
    # segment → file offset
    file_offset = None
    for seg in b.segments:
        if seg.virtual_address <= addr_aligned < seg.virtual_address + seg.virtual_size:
            file_offset = seg.file_offset + (addr_aligned - seg.virtual_address)
            break
    if file_offset is None:
        print(f"# [skip] {name} segment 매핑 실패")
        return
    chunk = file_data[file_offset:file_offset + size]
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    md.detail = True
    instrs = list(md.disasm(chunk, addr_aligned))

    print(f"\n# === {label} @ {addr:#x} ({size}B, {'Thumb' if thumb else 'ARM'}) ===\n")
    if summary_only:
        # cmp imm + bl + strb 만 (dispatch + 외부 호출 단서)
        for ins in instrs:
            if ins.mnemonic.startswith("cmp") or ins.mnemonic in ("bl", "blx"):
                print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
            elif ins.mnemonic.startswith("strb") and "[" in ins.op_str:
                # motion enum write
                print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
            elif ins.mnemonic.startswith("mov") and ins.op_str.startswith(("r0, #", "r1, #", "r2, #")):
                # motion enum/event code candidate
                if "#0x" in ins.op_str or any(f"#{n}" in ins.op_str for n in range(50)):
                    print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
    else:
        for ins in instrs:
            print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")


def main() -> None:
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    # 1단계 — summary (cmp/mov/strb/bl 만) 로 빠른 패턴 파악
    print("=" * 60)
    print("# PASS 1: SUMMARY (cmp / mov imm / strb / bl 만)")
    print("=" * 60)
    for sym, label in TARGETS:
        disasm_one(b, data, sym, label, summary_only=True)

    # 2단계 — Motion setters 만 full disasm (mov r1, #N before bl SetMotion 추적)
    print("\n" + "=" * 60)
    print("# PASS 2: FULL DISASM (Motion setters)")
    print("=" * 60)
    for sym, label in [
        ("_ZN4HERO15SetAttackMotionEaa", "HERO::SetAttackMotion"),
        ("_ZN4HERO13SetWalkMotionEa", "HERO::SetWalkMotion"),
        ("_ZN4HERO17SetAttackedMotionEaa", "HERO::SetAttackedMotion"),
        ("_ZN4HERO12SetDieMotionEv", "HERO::SetDieMotion"),
        ("_ZN4CHAR9SetMotionEa", "CHAR::SetMotion"),
    ]:
        disasm_one(b, data, sym, label, summary_only=False)


if __name__ == "__main__":
    main()
