"""LoadItemTable 의 cat 17/18 영역 (0xa479c..0xa49c0) 을 추가 disasm.

dump_caller 가 0xa479c 의 invalid instruction (muleq — 사실 데이터/jumptable
literal) 에서 capstone disasm 가 멈췄음. 4-byte chunk 단위로 invalid 라도 건너뛰면서
계속 disasm.
"""
from __future__ import annotations
import pathlib
import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"

START_ADDR = 0xa479c
END_ADDR   = 0xa49c0


def main():
    so = lief.parse(str(SO))
    addr_to_name = {}
    for s in so.symbols:
        if not s.value or not s.size:
            continue
        addr_to_name.setdefault(s.value & ~1, s.name or "")
    seg = [(s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content))
           for s in so.segments if s.type == lief.ELF.Segment.TYPE.LOAD]
    full = b""
    base = 0
    for v0, v1, d in seg:
        if v0 <= START_ADDR < v1:
            base = v0
            full = d
            break
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md.skipdata = True   # 핵심 — invalid 만나면 .byte 로 출력 후 계속

    data = full[START_ADDR - base : END_ADDR - base]
    print(f"=== LoadItemTable tail @0x{START_ADDR:08x}..0x{END_ADDR:08x}  ({len(data)} bytes) ===")
    for ins in md.disasm(data, START_ADDR):
        line = f"  0x{ins.address:08x}  {ins.mnemonic:<6} {ins.op_str}"
        if ins.mnemonic in ("bl", "blx") and ins.op_str.startswith("#"):
            try:
                t = int(ins.op_str[1:], 0) & ~1
                tn = addr_to_name.get(t)
                if tn:
                    line += f"  ; -> {tn[:80]}"
            except ValueError:
                pass
        print(line)


if __name__ == "__main__":
    main()
