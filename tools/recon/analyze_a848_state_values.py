"""Round 48 / 2OA-2: task[0xa848] +0x00 에 쓰여지는 state ID 값 추출.

각 STR r2, [r3] 사이트에서 r2 의 값을 추적: 가장 가까운 직전의
`movs r2, #N` 또는 `mov r2, ...` 패턴을 찾아 state ID 후보를 수집한다.
"""
from pathlib import Path
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

# Round 47 BL FUN_85578c sites
SITES = [
    0x57036, 0x5707c, 0x575f6, 0x57602, 0x5760c, 0x579a0, 0x579aa,
    0x57bc6, 0x57bd2, 0x857ba, 0x85ab8, 0x85b2e, 0x85e98, 0x85f56,
    0x85f82, 0x85fe4, 0x86010, 0x86062, 0x861d2, 0x862de, 0x86a34,
    0x87c60, 0x88a44, 0x88ed2, 0x89b2c, 0x8a06a, 0x8ad44, 0x8d890,
    0x901c4, 0x905be,
]


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    per_site = []
    value_counter = Counter()

    for bl in SITES:
        # Look BACKWARD up to 20 instr for `movs r2, #N` / `mov r2, Rs`
        # Easiest approach: disasm 40 bytes BEFORE bl and walk
        start = max(0, bl - 0x80)
        instrs = list(md.disasm(DATA[start:bl + 0x20], start))
        # Find the BL location
        bl_idx = None
        for i, ins in enumerate(instrs):
            if ins.address == bl:
                bl_idx = i
                break
        if bl_idx is None:
            per_site.append((bl, "??", "BL not found"))
            continue
        # Search backward from bl_idx for the most recent r2 setter
        r2_setter = None
        for j in range(bl_idx - 1, max(0, bl_idx - 25), -1):
            ins = instrs[j]
            op = ins.op_str
            if op.startswith("r2") or op.startswith("r2,"):
                if ins.mnemonic in ("movs", "mov", "movw"):
                    r2_setter = (ins.address, ins.mnemonic, op)
                    break
                # ldr r2, [pc, #N] = literal pool load
                if ins.mnemonic.startswith("ldr") and "[pc" in op:
                    r2_setter = (ins.address, ins.mnemonic, op)
                    break
        # Also find the STR location after BL
        str_site = None
        for k in range(bl_idx + 1, min(len(instrs), bl_idx + 8)):
            ins = instrs[k]
            if ins.mnemonic.startswith("str") and "[r3" in ins.op_str:
                str_site = (ins.address, ins.mnemonic, ins.op_str)
                break
            if ins.mnemonic in ("bl", "blx", "b", "bx"):
                break

        per_site.append((bl, r2_setter, str_site))

        # Extract value if movs r2, #N
        if r2_setter and r2_setter[1] == "movs" and "#" in r2_setter[2]:
            try:
                val_str = r2_setter[2].split("#")[-1].strip()
                val = int(val_str, 0)
                value_counter[val] += 1
            except Exception:
                pass

    print("=== state ID values written to task[0xa848]+0x00 ===")
    print("(from `movs r2, #N` ~ `str r2, [r3]` patterns)")
    for val, cnt in value_counter.most_common(20):
        print(f"  state = {val} (0x{val:x}): {cnt} sites")
    print()
    print("=== Per-site r2-setter -> STR pair ===")
    for bl, setter, store in per_site:
        if isinstance(setter, tuple) and len(setter) == 3:
            s_str = f"0x{setter[0]:05x} {setter[1]} {setter[2]}"
        elif setter:
            s_str = str(setter)
        else:
            s_str = "??"
        if isinstance(store, tuple) and len(store) == 3:
            st_str = f"0x{store[0]:05x} {store[1]} {store[2]}"
        elif store:
            st_str = str(store)
        else:
            st_str = "(no STR)"
        print(f"  BL@0x{bl:05x}:")
        print(f"    r2 setter: {s_str}")
        print(f"    store    : {st_str}")


if __name__ == "__main__":
    main()
