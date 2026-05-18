"""QuestMgr::QuestRewardData 디스어셈블 (Round 65).

목적:
  - reward type 6/10/11/12 의 .so 내부 dispatch 추적 (R56 미해석 4 type)
  - 함수 entry @ 0xd458c, 크기 1552B (lief symbol)
  - reward type 별 jumptable / cmp imm / strb / 외부 함수 호출 패턴 추출

전략:
  1. lief 로 ELF 파싱 → QuestRewardData 의 정확한 주소/크기 확인
  2. capstone Thumb 디스어셈블 (h5 .so 는 ARM/Thumb 혼재, 함수 LSB 로 모드 결정)
  3. dispatch 구조 (cmp/sub + ble + ldr pc 패턴) + 외부 함수 호출 (bl 0xXXXXX) 추출
  4. type 6/10/11/12 에 해당하는 case 블록 식별
"""
from __future__ import annotations
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

import lief
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB


TARGET_NAME = "_ZN8QuestMgr15QuestRewardDataEah"
DEMANGLED = "QuestMgr::QuestRewardData(char, unsigned char)"


def find_symbol(bin_path: str, name: str):
    b = lief.parse(bin_path)
    for s in b.symbols:
        if s.name == name:
            return int(s.value), int(s.size)
    return None, None


def main() -> None:
    g = select("h5")
    addr, size = find_symbol(g.binary_path, TARGET_NAME)
    assert addr is not None, f"symbol {TARGET_NAME} not found"
    thumb = bool(addr & 1)
    addr_aligned = addr & ~1
    print(f"# {DEMANGLED}")
    print(f"# symbol @ {addr:#x} (LSB={addr&1} → {'Thumb' if thumb else 'ARM'} mode), size={size}B")
    print()

    with open(g.binary_path, "rb") as f:
        data = f.read()

    # ELF segment → file offset 매핑 (단순 .text 영역 가정)
    b = lief.parse(g.binary_path)
    file_offset = None
    for seg in b.segments:
        if seg.virtual_address <= addr_aligned < seg.virtual_address + seg.virtual_size:
            file_offset = seg.file_offset + (addr_aligned - seg.virtual_address)
            break
    assert file_offset is not None, "segment 매핑 실패"

    chunk = data[file_offset:file_offset + size]

    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB if thumb else CS_MODE_ARM)
    md.detail = True
    instrs = list(md.disasm(chunk, addr_aligned))

    # 1) cmp imm + bl/blx 패턴 추출 — reward type dispatch 단서
    print("# === cmp / sub / bl 패턴 ===\n")
    for ins in instrs:
        if ins.mnemonic.startswith("cmp") and ins.op_str:
            print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
        elif ins.mnemonic.startswith(("sub", "add")) and "#" in ins.op_str:
            # case 변환용 sub r,r,#N 패턴
            if ", #" in ins.op_str and any(t in ins.op_str for t in ("r0", "r1", "r2", "r3", "r4")):
                # case 추론 도움
                pass
        elif ins.mnemonic in ("bl", "blx", "b", "bne", "beq", "ble", "bgt", "bhi", "bls"):
            if ins.op_str.startswith("#0x"):
                target = int(ins.op_str[1:], 16)
                print(f"  {ins.address:08x}: {ins.mnemonic:8} {target:#x}")
        elif ins.mnemonic.startswith("ldrb") and "[" in ins.op_str:
            print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
        elif ins.mnemonic.startswith("strb") and "[" in ins.op_str:
            print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")

    print("\n# === 전체 디스어셈블 ===\n")
    for ins in instrs:
        print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
