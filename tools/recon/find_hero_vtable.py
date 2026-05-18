"""HERO / CHAR / BATTLER vtable 위치 찾기 + ChangeAttackMotion 슬롯 식별."""
from __future__ import annotations
import pathlib, sys, struct
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief

# itanium ABI: _ZTV<class_name>
VTABLE_SYMBOLS = [
    "_ZTV4HERO",
    "_ZTV4CHAR",
    "_ZTV7BATTLER",
]

def main():
    g = select("h5")
    with open(g.binary_path, "rb") as f:
        data = f.read()
    b = lief.parse(g.binary_path)

    # 함수 심볼 lookup
    by_addr = {}
    for s in b.symbols:
        v = int(s.value) & ~1
        sz = int(s.size)
        if sz > 0:
            by_addr.setdefault(v, []).append(s.name)

    for vsym in VTABLE_SYMBOLS:
        found = None
        for s in b.symbols:
            if s.name == vsym:
                found = (int(s.value), int(s.size))
                break
        if not found:
            print(f"# [skip] {vsym} not found")
            continue
        vaddr, vsize = found
        vaddr = vaddr & ~1
        print(f"\n# === {vsym} @ {vaddr:#x} (size {vsize}) ===")
        # find file offset
        file_off = None
        for seg in b.segments:
            seg_addr = int(seg.virtual_address)
            seg_size = int(seg.virtual_size)
            if seg_addr <= vaddr < seg_addr + seg_size:
                file_off = int(seg.file_offset) + (vaddr - seg_addr)
                break
        if file_off is None:
            print(f"  [skip] segment mapping failed")
            continue
        # dump vtable entries
        for i in range(0, vsize, 4):
            entry_off = file_off + i
            if entry_off + 4 > len(data):
                break
            val = struct.unpack("<I", data[entry_off:entry_off+4])[0]
            sym = by_addr.get(val & ~1, [""])[0]
            marker = ""
            if "ChangeAttackMotion" in sym:
                marker = "  <-- ChangeAttackMotion"
            if sym or marker:
                print(f"  +{i:#04x}: {val:#10x}  {sym}{marker}")
            else:
                print(f"  +{i:#04x}: {val:#10x}")


if __name__ == "__main__":
    main()
