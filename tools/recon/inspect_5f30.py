"""0x5f30 주변 메모리 검사 — 0x91e7c (ChangeAttackMotion) 가 어떤 테이블에 들어있나."""
from __future__ import annotations
import pathlib, sys, struct
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from _game import select  # noqa
import lief

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

    # 0x5f30 주변 ±0x40 byte dump (u32 LE)
    print("# 0x5f30 주변 u32 LE dump (각 u32 = 8 byte 단위)")
    for off in range(0x5f00, 0x5f80, 4):
        val = struct.unpack("<I", data[off:off+4])[0]
        sym = by_addr.get(val & ~1, [""])[0]
        marker = "  <-- 0x91e7c here" if off == 0x5f30 else ""
        print(f"  {off:#08x}: {val:#010x}  {sym}{marker}")

    # 0x91e7c 의 sibling 함수 (HERO 클래스 attack 관련) 모두 표시
    print("\n# 0x5f30 영역 함수 ptr 의 의미 추측 — 인근 HERO 함수 심볼")
    for off in range(0x5f00, 0x5f80, 4):
        val = struct.unpack("<I", data[off:off+4])[0]
        sym = by_addr.get(val & ~1, [""])[0]
        if "HERO" in sym or "CHAR" in sym or "skill" in sym.lower():
            print(f"  {off:#08x}: {val:#10x}  {sym}")

if __name__ == "__main__":
    main()
