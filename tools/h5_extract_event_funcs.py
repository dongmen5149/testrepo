"""작은 Event_* 함수들을 일괄 disasm 해서 빠르게 의미 파악.

각 함수당 4-200B. 100개+ 함수를 한 파일에 dump.
"""
from __future__ import annotations
import pathlib

import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"


def main() -> int:
    so = lief.parse(str(SO))
    seg = [(s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content))
           for s in so.segments if s.type == lief.ELF.Segment.TYPE.LOAD]

    def read(va, sz):
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va-v0:va-v0+sz])

    addr_to_name = {}
    events = []
    seen = set()
    for s in so.symbols:
        n = s.name or ""
        if n and s.value and s.size:
            addr_to_name.setdefault(s.value & ~1, n)
        if "EventProc" in n and "Event_" in n and s.size and n not in seen:
            seen.add(n)
            events.append((s.size, s.value & ~1, n))
    events.sort()

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    out = ROOT / "work/h5/analysis/event_funcs_disasm.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write(f"# Hero5 EventProc::Event_* disasm dump  ({len(events)} 함수)\n")
        f.write(f"# size 오름차순. 4B = 빈 stub (return only).\n\n")
        for sz, addr, n in events:
            f.write(f"\n=== {n}  @0x{addr:08x}  size={sz} ===\n")
            for ins in md.disasm(read(addr, sz), addr):
                cmt = ""
                if ins.mnemonic.startswith(("bl", "b")) and ins.op_str.startswith("#"):
                    try:
                        t = int(ins.op_str[1:], 0) & ~1
                        tn = addr_to_name.get(t)
                        if tn:
                            cmt = f"  ; -> {tn[:90]}"
                    except ValueError:
                        pass
                f.write(f"  0x{ins.address:08x}  {ins.mnemonic:<8} {ins.op_str}{cmt}\n")
    print(f"wrote {out}  ({len(events)} 함수)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
