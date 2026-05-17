"""Round 49 / 2PC: task[0xa848] deferred stack-cached sub-field 추출 (v2).

Round 48 에서 18 callers 가 BL FUN_85578c → adds r2, r0, #0 → `adds r3, r7, #0;
subs r3, #N; str r2, [r3]` 또는 직접 `str r2, [r7, #-N]` 등으로 &task[0xa848]
포인터를 로컬 stack 에 저장. 이후 함수 본문 전체에서 reload 후 sub-field access.

v2 변경:
- `adds Rd, r7, #0; subs Rd, #N; str rX, [Rd]` 패턴 정확히 해석 → slot = r7 - N
- Per-site disasm 을 함수 전체로 확장 (FUN_BOUNDS 갱신)
"""
from pathlib import Path
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

SITES = [
    0x57036, 0x5707c, 0x575f6, 0x57602, 0x5760c, 0x579a0, 0x579aa,
    0x57bc6, 0x57bd2, 0x857ba, 0x85ab8, 0x85b2e, 0x85e98, 0x85f56,
    0x85f82, 0x85fe4, 0x86010, 0x86062, 0x861d2, 0x862de, 0x86a34,
    0x87c60, 0x88a44, 0x88ed2, 0x89b2c, 0x8a06a, 0x8ad44, 0x8d890,
    0x901c4, 0x905be,
]

FUN_BOUNDS = [
    (0x56f3c, 0x5727c),
    (0x57394, 0x581a8),
    (0x857a4, 0x85aa8),
    (0x85aa8, 0x85b18),
    (0x85b18, 0x85e88),
    (0x85e88, 0x85edc),
    (0x85edc, 0x85fc8),
    (0x85fc8, 0x86040),
    (0x86058, 0x861a8),
    (0x861a8, 0x862d4),
    (0x862d4, 0x8630c),
    (0x86a04, 0x87c44),
    (0x87c44, 0x88a30),
    (0x88a30, 0x88eb0),
    (0x88eb0, 0x89b18),
    (0x89b18, 0x8a050),
    (0x8a050, 0x8ad30),
    (0x8ad30, 0x8b2e8),
    (0x8d87c, 0x8dcd8),
    (0x901b0, 0x905a4),
    (0x905a4, 0x90b50),
]


def find_function_bound(addr: int):
    for start, end in FUN_BOUNDS:
        if start <= addr < end:
            return (start, end)
    return None


def parse_off(op_str: str):
    if "#" in op_str:
        try:
            tail = op_str.split("#")[-1]
            off_str = tail.rstrip("]").strip()
            return int(off_str, 0)
        except Exception:
            return None
    if "[" in op_str and "]" in op_str:
        return 0
    return None


def parse_bracket(op_str: str):
    """Parse `[Rb]` or `[Rb, #N]`."""
    if "[" not in op_str or "]" not in op_str:
        return None
    inside = op_str[op_str.index("[") + 1:op_str.index("]")]
    parts = [p.strip() for p in inside.split(",")]
    base = parts[0]
    off = 0
    if len(parts) > 1 and parts[1].startswith("#"):
        try:
            off = int(parts[1].lstrip("#"), 0)
        except Exception:
            return None
    return (base, off)


def walk_instrs(start: int, end: int):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    return [
        {"addr": ins.address, "mnem": ins.mnemonic, "op_str": ins.op_str}
        for ins in md.disasm(DATA[start:end], start)
    ]


def find_stack_store_v2(instrs, bl_idx: int):
    """Find slot offset relative to r7 after BL FUN_85578c.

    Tracks two register types:
      - addr_regs: holds &task[0xa848] (initially {r0})
      - stack_offsets: dict reg -> offset from r7 (initially {r7: 0})
    """
    addr_regs = {"r0"}
    stack_off = {"r7": 0}

    for i in range(bl_idx + 1, min(bl_idx + 24, len(instrs))):
        ins = instrs[i]
        mnem = ins["mnem"]
        op = ins["op_str"]

        # Stop at next BL
        if mnem in ("bl", "blx"):
            return None

        parts = [p.strip() for p in op.split(",")]
        if not parts:
            continue
        dst = parts[0]

        # Propagate addr_regs via adds Rd, Rs, #0 / mov Rd, Rs / movs Rd, Rs
        if mnem == "adds" and len(parts) == 3 and parts[2] == "#0":
            src = parts[1]
            if src in addr_regs:
                addr_regs.add(dst)
                continue
            if src == "r7":
                stack_off[dst] = 0
                addr_regs.discard(dst)
                continue
            if src in stack_off:
                stack_off[dst] = stack_off[src]
                addr_regs.discard(dst)
                continue
        if mnem in ("mov", "movs") and len(parts) == 2:
            src = parts[1]
            if src in addr_regs:
                addr_regs.add(dst)
                continue
            if src in stack_off:
                stack_off[dst] = stack_off[src]
                addr_regs.discard(dst)
                continue
            # Lose tracking for dst
            addr_regs.discard(dst)
            stack_off.pop(dst, None)

        # subs Rd, #N — self-modify
        if mnem == "subs" and len(parts) == 2 and parts[1].startswith("#"):
            try:
                n = int(parts[1].lstrip("#"), 0)
                if dst in stack_off:
                    stack_off[dst] -= n
                    continue
                if dst in addr_regs:
                    addr_regs.discard(dst)
            except Exception:
                pass
        # adds Rd, #N — self-modify
        if mnem == "adds" and len(parts) == 2 and parts[1].startswith("#"):
            try:
                n = int(parts[1].lstrip("#"), 0)
                if dst in stack_off:
                    stack_off[dst] += n
                    continue
            except Exception:
                pass

        # subs Rd, Rs, #N — 3-arg
        if mnem == "subs" and len(parts) == 3 and parts[2].startswith("#"):
            src = parts[1]
            try:
                n = int(parts[2].lstrip("#"), 0)
                if src in stack_off:
                    stack_off[dst] = stack_off[src] - n
                    addr_regs.discard(dst)
                    continue
                if src == "r7":
                    stack_off[dst] = -n
                    addr_regs.discard(dst)
                    continue
            except Exception:
                pass

        # str Rd, [Rb, #N] or str Rd, [Rb] — check if Rd is addr_reg and Rb is stack_reg
        if mnem == "str":
            # split to get [Rd, [Rb, #N]] -> parts is mixed
            # op_str like "r2, [r3]" or "r2, [r3, #0xc]"
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                rd = parts2[0].strip()
                bracket_str = parts2[1].strip()
                bracket = parse_bracket(bracket_str)
                if rd in addr_regs and bracket:
                    base_reg, base_off = bracket
                    if base_reg in stack_off:
                        return stack_off[base_reg] + base_off
                    if base_reg == "r7":
                        return base_off

        # Other instr that clobber dst regs
        if mnem.startswith(("ldr",)) and len(parts) >= 1:
            addr_regs.discard(dst)
            stack_off.pop(dst, None)

    return None


def walk_for_subfield_access(instrs, bl_idx: int, slot_off: int):
    """Walk from bl_idx onward, find reloads of stack[slot_off] then sub-field access."""
    out = []
    for i in range(bl_idx + 1, len(instrs)):
        ins = instrs[i]
        mnem = ins["mnem"]
        op = ins["op_str"]
        if mnem != "ldr":
            continue
        parts2 = op.split(",", 1)
        if len(parts2) != 2:
            continue
        rd = parts2[0].strip()
        bracket = parse_bracket(parts2[1].strip())
        if not bracket:
            continue
        base, off = bracket
        # Either direct `[r7, #slot_off]` or via reload chain
        if base == "r7" and off == slot_off:
            # Reload found: rd now holds &task[0xa848]
            reloaded = rd
            # Walk forward up to 8 instr looking for [reloaded, #M]
            for j in range(i + 1, min(i + 10, len(instrs))):
                jin = instrs[j]
                jmnem = jin["mnem"]
                jop = jin["op_str"]
                if jmnem in ("bl", "blx"):
                    break
                if jmnem.startswith(("ldr", "str")):
                    jparts = jop.split(",", 1)
                    if len(jparts) == 2:
                        jrd = jparts[0].strip()
                        jb = parse_bracket(jparts[1].strip())
                        if jb and jb[0] == reloaded:
                            out.append((jin["addr"], jmnem, jop, jb[1]))
                            # If reloaded clobbered by ldr, stop
                            if jmnem.startswith("ldr") and jrd == reloaded:
                                break
                # Track if reloaded reg gets clobbered by mov/adds/subs/etc
                jparts_all = [p.strip() for p in jop.split(",")]
                if jparts_all and jparts_all[0] == reloaded:
                    if jmnem in ("mov", "movs", "adds", "subs"):
                        # Could still be tracking if "Rd = Rd op X" — but for our purpose,
                        # any modification ends our window
                        break
    return out


def main() -> None:
    print("=== Round 49 / 2PC v2: deferred stack-cached sub-field extraction ===\n")
    all_ldr = Counter()
    all_str = Counter()
    all_ldrb = Counter()
    all_strb = Counter()
    per_site = []

    for bl in SITES:
        fb = find_function_bound(bl)
        if fb is None:
            per_site.append((bl, "no_func_bound", None, []))
            continue
        instrs = walk_instrs(fb[0], fb[1])
        bl_idx = None
        for i, ins in enumerate(instrs):
            if ins["addr"] == bl:
                bl_idx = i
                break
        if bl_idx is None:
            per_site.append((bl, "no_bl_idx", None, []))
            continue
        slot_off = find_stack_store_v2(instrs, bl_idx)
        if slot_off is None:
            per_site.append((bl, "no_store", None, []))
            continue

        accesses = walk_for_subfield_access(instrs, bl_idx, slot_off)
        for addr, mnem, op, off in accesses:
            if mnem == "ldr":
                all_ldr[off] += 1
            elif mnem == "ldrb":
                all_ldrb[off] += 1
            elif mnem == "ldrh":
                all_ldr[off] += 1
            elif mnem == "str":
                all_str[off] += 1
            elif mnem == "strb":
                all_strb[off] += 1
        per_site.append((bl, f"slot=r7{slot_off:+d}", slot_off, accesses))

    print("=== Aggregated sub-field access via stack-reload ===\n")
    print("--- LDR (word read) ---")
    for off, cnt in sorted(all_ldr.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- LDRB (byte read) ---")
    for off, cnt in sorted(all_ldrb.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- STR (word write) ---")
    for off, cnt in sorted(all_str.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- STRB (byte write) ---")
    for off, cnt in sorted(all_strb.items()):
        print(f"  +0x{off:04x}: {cnt}")

    print("\n=== Per-site ===")
    for bl, status, slot, accs in per_site:
        if accs:
            print(f"\n  BL@0x{bl:05x} ({status}): {len(accs)} accesses")
            for addr, mnem, op, off in accs[:8]:
                print(f"    0x{addr:05x} {mnem:6} {op}  (+0x{off:x})")
        else:
            print(f"  BL@0x{bl:05x} ({status}): no accesses")


if __name__ == "__main__":
    main()
