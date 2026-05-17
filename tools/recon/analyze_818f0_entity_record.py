"""Round 49 / 2PE: FUN_000818f0 entity record offset 추출.

Round 48에서 FUN_818f0 = 74-entity iteration loop (stride 0x10). 본 라운드에서
entity pointer (loop variable, stride 0x10) 를 통해 access 되는 모든 offset 들을
수집해 entity record 구조 추출.

전략:
1. FUN_818f0 (5424B) 전체 disasm
2. entity ptr 후보 register 추적:
   - loop 시작 시 entity_base + counter * 0x10 형식으로 계산되는 register
   - 또는 stack[-4] 등에 저장된 entity ptr
3. 모든 `ldr/str Rd, [entity_reg, #N]` 패턴에서 N 수집
"""
from pathlib import Path
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

FUN_START = 0x818f0
FUN_END = 0x82e20


def walk_with_skip(start: int, end: int):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    instrs = []
    pos = start
    while pos < end:
        any_emitted = False
        last = pos
        for ins in md.disasm(DATA[pos:end], pos):
            instrs.append({"addr": ins.address, "mnem": ins.mnemonic, "op_str": ins.op_str})
            last = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            pos = last
        pos += 2
    return instrs


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


def main() -> None:
    instrs = walk_with_skip(FUN_START, FUN_END)
    print(f"FUN_818f0: {len(instrs)} instructions decoded\n")

    # Strategy 1: track register loaded from stack[-4]
    # We know from Round 48: local[-4] holds entity_ptr (current entity in iteration)
    # Pattern: `subs r3, r7, #4; ldr r3, [r3]` → r3 = local[-4] = entity_ptr
    #
    # We track which registers currently hold entity_ptr after such loads.

    entity_regs = set()
    stack_reg_for_4 = set()  # registers known to point to stack[-4] location
    accesses = []

    for i, ins in enumerate(instrs):
        mnem = ins["mnem"]
        op = ins["op_str"]
        parts = [p.strip() for p in op.split(",")]
        if not parts:
            continue
        dst = parts[0]

        # `subs Rd, r7, #4` → Rd points to stack[-4] location
        if mnem == "subs" and len(parts) == 3 and parts[2] == "#4" and parts[1] == "r7":
            stack_reg_for_4.add(dst)
            entity_regs.discard(dst)
            continue

        # `adds Rd, r7, #0; subs Rd, #4` (2-step alternative)
        if mnem == "adds" and len(parts) == 3 and parts[2] == "#0" and parts[1] == "r7":
            # First step — Rd = r7. We need to see subs Rd, #4 next.
            # Mark dst as r7-tracked but with no offset yet.
            # For simplicity, we don't track this case here (less common in FUN_818f0).
            entity_regs.discard(dst)
            stack_reg_for_4.discard(dst)
            continue

        # BL clobbers caller-saved
        if mnem in ("bl", "blx"):
            for r in ("r0", "r1", "r2", "r3", "r12", "lr"):
                entity_regs.discard(r)
                stack_reg_for_4.discard(r)
            continue

        # ldr Rd, [Rb] or [Rb, #imm]
        if mnem == "ldr":
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                rd = parts2[0].strip()
                bracket = parse_bracket(parts2[1].strip())
                if bracket:
                    base, off = bracket
                    # Reload from stack[-4]: base in stack_reg_for_4 and off == 0
                    if base in stack_reg_for_4 and off == 0:
                        entity_regs.add(rd)
                        continue
                    # Or directly from [r7, #N] — but r7+N positive doesn't access r7-4 in Thumb
                    # Field access via entity_reg
                    if base in entity_regs:
                        accesses.append((ins["addr"], mnem, op, off))
                        # rd is loaded — clobber its prior tracking
                        entity_regs.discard(rd)
                        continue
                # No match — clobber rd
                entity_regs.discard(rd)
                stack_reg_for_4.discard(rd)
            continue

        if mnem in ("ldrb", "ldrh"):
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                rd = parts2[0].strip()
                bracket = parse_bracket(parts2[1].strip())
                if bracket and bracket[0] in entity_regs:
                    accesses.append((ins["addr"], mnem, op, bracket[1]))
                entity_regs.discard(rd)
                stack_reg_for_4.discard(rd)
            continue

        if mnem == "str":
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                bracket = parse_bracket(parts2[1].strip())
                if bracket and bracket[0] in entity_regs:
                    accesses.append((ins["addr"], mnem, op, bracket[1]))
            continue

        if mnem in ("strb", "strh"):
            parts2 = op.split(",", 1)
            if len(parts2) == 2:
                bracket = parse_bracket(parts2[1].strip())
                if bracket and bracket[0] in entity_regs:
                    accesses.append((ins["addr"], mnem, op, bracket[1]))
            continue

        # `mov/movs/adds Rd, Rs(, #0)` propagates entity_reg
        if mnem in ("mov", "movs") and len(parts) == 2 and not parts[1].startswith("#"):
            src = parts[1]
            if src in entity_regs:
                entity_regs.add(dst)
                continue
            entity_regs.discard(dst)
            continue
        if mnem == "adds" and len(parts) == 3 and parts[2] == "#0":
            src = parts[1]
            if src in entity_regs:
                entity_regs.add(dst)
                continue
            entity_regs.discard(dst)
            continue

        # Modifying instr — clobber dst
        if mnem in ("adds", "subs", "lsls", "lsrs", "asrs", "ands", "orrs",
                    "eors", "rsbs", "negs", "muls", "mvns", "mov", "movs"):
            entity_regs.discard(dst)
            stack_reg_for_4.discard(dst)

    print(f"Total entity_record accesses found: {len(accesses)}\n")

    ldr = Counter()
    ldrb = Counter()
    str_ = Counter()
    strb = Counter()
    for _, mnem, _, off in accesses:
        if mnem == "ldr":
            ldr[off] += 1
        elif mnem == "ldrb":
            ldrb[off] += 1
        elif mnem == "ldrh":
            ldr[off] += 1
        elif mnem == "str":
            str_[off] += 1
        elif mnem == "strb":
            strb[off] += 1
        elif mnem == "strh":
            str_[off] += 1

    print("--- LDR (word/half read) ---")
    for off, cnt in sorted(ldr.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- LDRB (byte read) ---")
    for off, cnt in sorted(ldrb.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- STR (word/half write) ---")
    for off, cnt in sorted(str_.items()):
        print(f"  +0x{off:04x}: {cnt}")
    print("\n--- STRB (byte write) ---")
    for off, cnt in sorted(strb.items()):
        print(f"  +0x{off:04x}: {cnt}")

    print(f"\n=== Sample accesses (first 30) ===")
    for addr, mnem, op, off in accesses[:30]:
        print(f"  0x{addr:05x} {mnem:6} {op}  (+0x{off:x})")


if __name__ == "__main__":
    main()
