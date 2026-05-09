"""심볼 substring 으로 함수 탐색."""
import sys, lief, pathlib
SO = pathlib.Path(__file__).resolve().parent.parent / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
so = lief.parse(str(SO))
needle = sys.argv[1] if len(sys.argv) > 1 else ""
for s in so.symbols:
    n = s.name or ""
    if needle in n and s.size:
        print(f"0x{s.value & ~1:08x}  size={s.size:>5}  {n}")
