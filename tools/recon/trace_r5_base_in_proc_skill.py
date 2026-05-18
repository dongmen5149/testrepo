"""ProcHeroSkill 안에서 r5 가 base ptr 로 reassign 되는 위치 추적 (Round 71).

r5 가 entry 에서 처음 `mov r5, #0` (loop counter) 으로 시작. 그 후 107회의
`[r5, +-0x190]` ldr 패턴 사용 = r5 가 어딘가에서 (big_struct + 0x190) 으로 재설정됨.

추적 전략:
  - r5 destination 의 모든 instructions 추출 (`mov r5, ...`, `ldr r5, ...`, `add r5, ...`)
  - 첫 ldr/add 에서 r5 가 어떤 source 에서 왔는지 확인
  - r5 가 (X + 0x190) 형식이면 big_struct = X
"""
from __future__ import annotations
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


PROC_HERO_SKILL = 0x99278
PROC_HERO_SKILL_SIZE = 7972


def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    file_offset = None
    for seg in b.segments:
        if seg.virtual_address <= PROC_HERO_SKILL < seg.virtual_address + seg.virtual_size:
            file_offset = seg.file_offset + (PROC_HERO_SKILL - seg.virtual_address)
            break
    chunk = data[file_offset:file_offset + PROC_HERO_SKILL_SIZE]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True
    instrs = list(md.disasm(chunk, PROC_HERO_SKILL))

    # r5 destination instructions
    r5_writes = []
    for ins in instrs:
        op = ins.op_str
        # destination = r5 -- 첫 operand 가 r5
        if op.startswith("r5,") or op.startswith("r5 "):
            r5_writes.append(ins)

    print(f"# r5 destination instructions: {len(r5_writes)}\n")
    for ins in r5_writes[:50]:
        print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")

    # 첫 ldr [r5, +-0x190] 이전의 r5 set 위치
    first_r5_neg_load = None
    for ins in instrs:
        if ins.mnemonic == "ldr" and "[r5, #-0x190]" in ins.op_str:
            first_r5_neg_load = ins
            break
    if first_r5_neg_load is not None:
        print(f"\n# 첫 ldr [r5, #-0x190] 위치: {first_r5_neg_load.address:#x}")
        # 그 직전 r5 set 명령들 (역순)
        print("# 직전 r5 destination set (역순, 최대 5개):")
        for ins in reversed(r5_writes):
            if ins.address < first_r5_neg_load.address:
                print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
                if len([x for x in r5_writes if x.address < first_r5_neg_load.address and x.address >= ins.address]) >= 5:
                    break

    # 첫 r5 set 가 ldr 또는 add 라면 그 source 추적
    # entry 의 r5 = 0 (loop counter) 이후 첫 reassign 위치 출력
    entry_loop_end = 0x992d8  # cmp r5, #0x3b; bne 992c0 (entry loop end)
    print(f"\n# entry loop 종료 (~{entry_loop_end:#x}) 이후 첫 r5 reassign:")
    for ins in r5_writes:
        if ins.address > entry_loop_end:
            # 이 위치의 +-16 instruction 컨텍스트
            print(f"\n# context around first post-loop r5 set @ {ins.address:#x}:")
            for ctx in instrs:
                if ins.address - 24 <= ctx.address <= ins.address + 16:
                    marker = "  <-- r5 set" if ctx.address == ins.address else ""
                    print(f"    {ctx.address:08x}: {ctx.mnemonic:8} {ctx.op_str}{marker}")
            break


if __name__ == "__main__":
    main()
