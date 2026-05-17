"""Round 49 / 2PC v3: task[0xa848] deferred stack-cached sub-field 추출.

v2 정정: ARM Thumb 는 ldr 의 negative immediate offset 미지원. Reload 는
multi-step 패턴 (`subs Rx, r7, #N; ldr Ry, [Rx]`). Forward-tracking으로 함수
본문 walk 하며 모든 register 의 stack offset 을 추적.

Tracked register types:
  - addr_regs: holds &task[0xa848]
  - stack_off: dict reg -> offset from r7
  - reloaded_addr_regs: holds &task[0xa848] AFTER reload (via ldr from stored slot)
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


def parse_bracket(op_str: str):
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


def analyze_function(instrs, bl_idx):
    """Forward-walk the function starting at bl_idx+1 (after BL FUN_85578c).

    Returns (slot_off or None, accesses [(addr, mnem, op, sub_offset)]).
    """
    # State maps
    addr_regs = {"r0"}        # regs holding &task[0xa848] (NOT via reload)
    stack_off = {"r7": 0}      # regs holding r7+offset (offset can be negative)
    reload_regs = set()        # regs holding &task[0xa848] AFTER reload
    slot_off = None
    accesses = []

    def clear_reg(reg):
        addr_regs.discard(reg)
        stack_off.pop(reg, None)
        reload_regs.discard(reg)

    for i in range(bl_idx + 1, len(instrs)):
        ins = instrs[i]
        mnem = ins["mnem"]
        op = ins["op_str"]
        parts = [p.strip() for p in op.split(",")]
        if not parts:
            continue
        dst = parts[0]

        # BL/B clobbers caller-saved (r0-r3, r12, lr) — but we can continue
        # tracking r4-r11/sl. For simplicity, stop on bl/b/bx (out of function flow).
        if mnem in ("bl", "blx"):
            # Clobber r0..r3, lr, r12
            for r in ("r0", "r1", "r2", "r3", "r12", "lr"):
                clear_reg(r)
            continue
        if mnem in ("bx", "pop"):
            if "pc" in op or "lr" in op:
                break

        # adds Rd, Rs, #imm  (3-arg)
        if mnem == "adds" and len(parts) == 3 and parts[2].startswith("#"):
            try:
                n = int(parts[2].lstrip("#"), 0)
            except Exception:
                clear_reg(dst); continue
            src = parts[1]
            if n == 0:
                if src in addr_regs:
                    addr_regs.add(dst); stack_off.pop(dst, None); reload_regs.discard(dst); continue
                if src in reload_regs:
                    reload_regs.add(dst); stack_off.pop(dst, None); addr_regs.discard(dst); continue
                if src in stack_off:
                    stack_off[dst] = stack_off[src]; addr_regs.discard(dst); reload_regs.discard(dst); continue
                if src == "r7":
                    stack_off[dst] = 0; addr_regs.discard(dst); reload_regs.discard(dst); continue
                clear_reg(dst); continue
            else:
                if src in stack_off:
                    stack_off[dst] = stack_off[src] + n; addr_regs.discard(dst); reload_regs.discard(dst); continue
                if src == "r7":
                    stack_off[dst] = n; addr_regs.discard(dst); reload_regs.discard(dst); continue
            clear_reg(dst); continue

        # subs Rd, Rs, #imm (3-arg)
        if mnem == "subs" and len(parts) == 3 and parts[2].startswith("#"):
            try:
                n = int(parts[2].lstrip("#"), 0)
            except Exception:
                clear_reg(dst); continue
            src = parts[1]
            if src in stack_off:
                stack_off[dst] = stack_off[src] - n; addr_regs.discard(dst); reload_regs.discard(dst); continue
            if src == "r7":
                stack_off[dst] = -n; addr_regs.discard(dst); reload_regs.discard(dst); continue
            clear_reg(dst); continue

        # adds Rd, #imm (2-arg, self-modify)
        if mnem == "adds" and len(parts) == 2 and parts[1].startswith("#"):
            try:
                n = int(parts[1].lstrip("#"), 0)
            except Exception:
                clear_reg(dst); continue
            if dst in stack_off:
                stack_off[dst] += n
                continue
            clear_reg(dst); continue

        # subs Rd, #imm (2-arg)
        if mnem == "subs" and len(parts) == 2 and parts[1].startswith("#"):
            try:
                n = int(parts[1].lstrip("#"), 0)
            except Exception:
                clear_reg(dst); continue
            if dst in stack_off:
                stack_off[dst] -= n
                continue
            clear_reg(dst); continue

        # mov/movs Rd, Rs (single src reg)
        if mnem in ("mov", "movs") and len(parts) == 2 and not parts[1].startswith("#"):
            src = parts[1]
            if src in addr_regs:
                addr_regs.add(dst); stack_off.pop(dst, None); reload_regs.discard(dst); continue
            if src in reload_regs:
                reload_regs.add(dst); stack_off.pop(dst, None); addr_regs.discard(dst); continue
            if src in stack_off:
                stack_off[dst] = stack_off[src]; addr_regs.discard(dst); reload_regs.discard(dst); continue
            clear_reg(dst); continue

        # mov/movs Rd, #imm
        if mnem in ("mov", "movs", "movw") and len(parts) >= 2 and parts[1].startswith("#"):
            clear_reg(dst); continue

        # str Rd, [Rb, #N]  or  str Rd, [Rb]
        if mnem == "str":
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                rd = parts2[0].strip()
                bracket = parse_bracket(parts2[1].strip())
                if rd in addr_regs and bracket:
                    base_reg, base_off = bracket
                    candidate_slot = None
                    if base_reg == "r7":
                        candidate_slot = base_off
                    elif base_reg in stack_off:
                        candidate_slot = stack_off[base_reg] + base_off
                    if candidate_slot is not None and slot_off is None:
                        slot_off = candidate_slot
                # Note: STR may also write SUB-FIELD via &task[0xa848] reload reg
                if bracket:
                    base_reg, base_off = bracket
                    if base_reg in (addr_regs | reload_regs):
                        accesses.append((ins["addr"], mnem, op, base_off))
            continue

        # strb/strh Rd, [Rb, #N]
        if mnem in ("strb", "strh"):
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                bracket = parse_bracket(parts2[1].strip())
                if bracket:
                    base_reg, base_off = bracket
                    if base_reg in (addr_regs | reload_regs):
                        accesses.append((ins["addr"], mnem, op, base_off))
            continue

        # ldr Rd, [Rb, #N]
        if mnem == "ldr":
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                rd = parts2[0].strip()
                bracket = parse_bracket(parts2[1].strip())
                if not bracket:
                    clear_reg(dst); continue
                base_reg, base_off = bracket
                # Reload detection: if base is r7 (or stack_off reg) and slot matches
                candidate_slot = None
                if base_reg == "r7":
                    candidate_slot = base_off
                elif base_reg in stack_off:
                    candidate_slot = stack_off[base_reg] + base_off
                if slot_off is not None and candidate_slot == slot_off:
                    # Reload! rd now holds &task[0xa848]
                    reload_regs.add(rd)
                    stack_off.pop(rd, None)
                    addr_regs.discard(rd)
                    continue
                # Else: sub-field access via existing addr_reg or reload_reg?
                if base_reg in (addr_regs | reload_regs):
                    accesses.append((ins["addr"], mnem, op, base_off))
                    # rd loaded — clobber any prior tracking
                    clear_reg(rd)
                    continue
                # Else: unrelated load — just clobber rd
                clear_reg(rd); continue
            continue

        # ldrb/ldrh
        if mnem in ("ldrb", "ldrh"):
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                rd = parts2[0].strip()
                bracket = parse_bracket(parts2[1].strip())
                if bracket:
                    base_reg, base_off = bracket
                    if base_reg in (addr_regs | reload_regs):
                        accesses.append((ins["addr"], mnem, op, base_off))
                clear_reg(rd); continue
            continue

        # Any other instr that writes dst — clear tracking
        if mnem in ("adds", "subs", "mov", "movs", "lsls", "lsrs", "asrs",
                    "ands", "orrs", "eors", "mvns", "rsbs", "muls",
                    "negs", "tst", "cmn", "cmp"):
            # cmp/tst don't write dst; skip
            if mnem in ("cmp", "tst", "cmn"):
                continue
            clear_reg(dst)
            continue

    return slot_off, accesses


def main() -> None:
    print("=== Round 49 / 2PC v3: deferred stack-cached sub-field extraction ===\n")
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
        slot, accesses = analyze_function(instrs, bl_idx)
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
            elif mnem == "strh":
                all_str[off] += 1
        slot_label = f"r7{slot:+d}" if slot is not None else "?"
        per_site.append((bl, slot_label, slot, accesses))

    print("=== Aggregated sub-field access (incl. stack-reload) ===\n")
    print("--- LDR/LDRH (word/half read) ---")
    for off, cnt in sorted(all_ldr.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- LDRB (byte read) ---")
    for off, cnt in sorted(all_ldrb.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- STR/STRH (word/half write) ---")
    for off, cnt in sorted(all_str.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- STRB (byte write) ---")
    for off, cnt in sorted(all_strb.items()):
        print(f"  +0x{off:04x}: {cnt}")

    print("\n=== Per-site (top 10 sites with accesses) ===")
    has_acc = [(bl, lab, s, a) for bl, lab, s, a in per_site if a]
    no_acc = [(bl, lab, s, a) for bl, lab, s, a in per_site if not a]
    for bl, label, slot, accs in has_acc[:15]:
        print(f"\n  BL@0x{bl:05x} (slot={label}): {len(accs)} accesses")
        for addr, mnem, op, off in accs[:10]:
            print(f"    0x{addr:05x} {mnem:6} {op}  (+0x{off:x})")

    print(f"\n=== {len(no_acc)} sites with no accesses found ===")
    for bl, lab, s, a in no_acc:
        print(f"  BL@0x{bl:05x} (slot={lab})")


if __name__ == "__main__":
    main()
