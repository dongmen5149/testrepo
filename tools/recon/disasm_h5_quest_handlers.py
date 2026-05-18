"""QuestCheck 의 cond_type 별 handler 디스어셈블 (Round 60).

Round 60 dispatch 발견:
  - 0xd3ca4: ldrb r1, [r6, +0x114]  (phase1 cond_type)
  - 0xd3cb0: cmp r2, #0x10; ble 0xd3f04  (≤ 16 default)
  - 0xd3cb8: sub r2, r2, #0x11; cmp r2, #3; jumptable
    - case 17 → 0xd3e98 (monster kill)
    - case 18 → 0xd3e58 (quest switch)
    - case 19 → 0xd3cd8 (fall-through, immediate)
    - case 20 → 0xd3ddc

목적:
  1. 0xd3f04 default handler (cond_type 13/14 처리) 디스어셈블
  2. 0xd3e98 (cond_type 17 handler) 디스어셈블 — 비교용
  3. 각 handler 가 phase1 의 어떤 byte 와 어떤 값을 비교하는지
"""
from __future__ import annotations
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa: E402

from elftools.elf.elffile import ELFFile
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM


HANDLERS = {
    0xd3f04: "DEFAULT (cond_type ≤ 16, includes 13/14)",
    0xd3e98: "cond_type 17 (monster kill)",
    0xd3e58: "cond_type 18 (quest switch)",
    0xd3cd8: "cond_type 19",
    0xd3ddc: "cond_type 20",
}


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

    # 각 handler 의 시작 ~ 다음 handler 직전까지 출력
    handler_addrs = sorted(HANDLERS.keys())
    for i, h in enumerate(handler_addrs):
        next_h = handler_addrs[i + 1] if i + 1 < len(handler_addrs) else (addr + size)
        print(f"\n=== {HANDLERS[h]} @ {h:#x} (block until {next_h:#x}) ===")
        in_block = False
        for ins in instrs:
            if ins.address == h: in_block = True
            if not in_block: continue
            if ins.address >= next_h: break
            # 최대 30 lines per handler
            print(f"  {ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")


if __name__ == "__main__":
    main()
