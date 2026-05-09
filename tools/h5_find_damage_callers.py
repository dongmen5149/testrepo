"""Monster::AddEffectDamage / BATTLER::IncreaseHP 호출자 추적 + 호출 직전 컨텍스트 dump.

실제 데미지 공식이 어느 함수에서 계산되어 위 함수들로 들어가는지를 좁힌다.
"""
from __future__ import annotations
import pathlib, sys

import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"

TARGETS = [
    "_ZN7Monster15AddEffectDamageEs",
    "_ZN7BATTLER10IncreaseHPEi",
]


def main() -> int:
    so = lief.parse(str(SO))
    seg = []
    for s in so.segments:
        if s.type == lief.ELF.Segment.TYPE.LOAD:
            seg.append((s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content)))

    target_addrs: dict[int, str] = {}
    syms = []
    for s in so.symbols:
        n = s.name or ""
        if n and s.value and s.size:
            a = s.value & ~1
            if n in TARGETS:
                target_addrs[a] = n
            syms.append((a, s.size, n))

    # 함수 범위로 정렬해 caller 식별 가능하도록.
    syms.sort()

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    def read(va: int, sz: int) -> bytes | None:
        for v0, v1, d in seg:
            if v0 <= va < v1:
                return bytes(d[va - v0 : va - v0 + sz])
        return None

    def find_func(addr: int) -> tuple[int, int, str] | None:
        # 이진 탐색 대신 단순 선형 (수천 건이라 빠름)
        for a, sz, n in syms:
            if a <= addr < a + sz:
                return a, sz, n
        return None

    callers: dict[str, list[tuple[str, int]]] = {n: [] for n in TARGETS}
    for fn_addr, fn_size, fn_name in syms:
        if fn_size <= 4 or fn_size > 8000:
            continue
        data = read(fn_addr, fn_size)
        if data is None:
            continue
        for ins in md.disasm(data, fn_addr):
            if not ins.mnemonic.startswith("bl"): continue
            if not ins.op_str.startswith("#"): continue
            try:
                tgt = int(ins.op_str[1:], 0) & ~1
            except ValueError:
                continue
            if tgt in target_addrs and fn_name not in TARGETS:
                callers[target_addrs[tgt]].append((fn_name, ins.address))

    for tgt, lst in callers.items():
        print(f"\n=== callers of {tgt} ({len(lst)}) ===")
        seen = set()
        for fn, addr in lst:
            key = fn
            if key in seen: continue
            seen.add(key)
            print(f"  0x{addr:08x}  {fn}")

    out = ROOT / "work/h5/analysis/damage_callers.tsv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write("target\tcaller_fn\tcall_site\n")
        for tgt, lst in callers.items():
            for fn, addr in lst:
                f.write(f"{tgt}\t{fn}\t0x{addr:08x}\n")
    print(f"\nwrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
