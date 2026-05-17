"""Round 48 / 2OA: task[0xa848] sub-struct offset 패턴 추출.

Round 47에서 FUN_00085578c (`&task[0xa848]` getter, 34 callers system-wide)를
식별. 본 스크립트는 각 BL@call_site 직후 8 instr 윈도우를 disasm하여
`ldr/str Rd, [r0|r3, #imm]` 패턴의 첫 immediate offset을 추출 → task[0xa848]
sub-struct 의 field offset 분포를 매핑한다.

Output: read offsets (LDR), write offsets (STR), per-site detail.
"""
from pathlib import Path
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

# Round 47에서 식별된 34 callers (BL FUN_85578c 호출 사이트).
# 일부 사이트는 동일 함수 내 다중 호출.
SITES = [
    0x57036, 0x5707c, 0x575f6, 0x57602, 0x5760c, 0x579a0, 0x579aa,
    0x57bc6, 0x57bd2, 0x857ba, 0x85ab8, 0x85b2e, 0x85e98, 0x85f56,
    0x85f82, 0x85fe4, 0x86010, 0x86062, 0x861d2, 0x862de, 0x86a34,
    0x87c60, 0x88a44, 0x88ed2, 0x89b2c, 0x8a06a, 0x8ad44, 0x8d890,
    0x901c4, 0x905be,
]


def parse_imm_offset(op_str: str):
    """Return immediate offset from `[Rb, #imm]` op_str, or None."""
    if "#" not in op_str:
        # `[Rb]` form = +0
        if "[" in op_str and "]" in op_str:
            return 0
        return None
    try:
        tail = op_str.split("#")[-1]
        off_str = tail.rstrip("]").strip()
        return int(off_str, 0)
    except Exception:
        return None


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    offsets_ldr = Counter()
    offsets_str = Counter()
    per_site = defaultdict(list)
    no_match = []

    for bl in SITES:
        window_end = min(bl + 4 + 0x40, len(DATA))
        instrs_seen = 0
        matched = False
        for ins in md.disasm(DATA[bl + 4:window_end], bl + 4):
            instrs_seen += 1
            if instrs_seen > 12:
                break
            # FUN_85578c returns `&task[0xa848]` in r0. We want the FIRST
            # memory access via r0 or any register that copies r0.
            mnem = ins.mnemonic
            op = ins.op_str
            if mnem in ("bl", "blx", "b", "bx"):
                break
            if mnem.startswith(("ldr", "str")):
                # Only count if base reg is r0 or r3 (common after BL return copy)
                if "[r0" in op or "[r3" in op or "[r1" in op or "[r2" in op:
                    off = parse_imm_offset(op)
                    if off is not None:
                        if mnem.startswith("ldr"):
                            offsets_ldr[off] += 1
                        else:
                            offsets_str[off] += 1
                        per_site[bl].append((ins.address, mnem, op))
                        matched = True
                        break
        if not matched:
            no_match.append(bl)

    print("=== task[0xa848] sub-struct LDR offsets (read) ===")
    for off, cnt in offsets_ldr.most_common(20):
        print(f"  +0x{off:04x}: {cnt}")
    print()
    print("=== task[0xa848] sub-struct STR offsets (write) ===")
    for off, cnt in offsets_str.most_common(20):
        print(f"  +0x{off:04x}: {cnt}")
    print()
    print("=== Per-site first ldr/str ===")
    for bl in SITES:
        if per_site[bl]:
            addr, mnem, op = per_site[bl][0]
            print(f"  BL@0x{bl:05x} -> 0x{addr:05x} {mnem:6} {op}")
    if no_match:
        print()
        print("=== No immediate-offset ldr/str within 12 instr ===")
        for bl in no_match:
            print(f"  BL@0x{bl:05x}")


if __name__ == "__main__":
    main()
