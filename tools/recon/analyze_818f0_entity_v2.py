"""Round 49 / 2PE v2: FUN_000818f0 entity record offset 추출 (단순화 버전).

전략:
- FUN_818f0 (5424B) 내에서 `subs Rx, r7, #4` 또는 `ldr Rx, [r7, #?]` 패턴으로
  stack[-4] 위치를 가리키는 reg 찾기.
- 직후 `ldr Rd, [Rx]` 가 entity_ptr 를 register 에 로드.
- 그 register 가 다음 8 instr 안에서 어떤 `[Rd, #imm]` 형태의 access 인지 수집.
- 각 reload site 별로 분리하여 추적 (간단한 local window analysis).
"""
from pathlib import Path
from collections import Counter
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


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
    instrs = walk_with_skip(0x818f0, 0x82e20)
    print(f"FUN_818f0: {len(instrs)} instructions")

    # Find all `subs Rx, r7, #4` patterns
    stack_minus4_sites = []
    for i, ins in enumerate(instrs):
        if ins["mnem"] == "subs":
            parts = [p.strip() for p in ins["op_str"].split(",")]
            if len(parts) == 3 and parts[1] == "r7" and parts[2] == "#4":
                stack_minus4_sites.append((i, parts[0], ins["addr"]))
    print(f"\n=== {len(stack_minus4_sites)} `subs Rx, r7, #4` sites found ===")

    # For each, look at next instr for `ldr Rd, [Rx]` (entity ptr reload)
    entity_reloads = []  # list of (reload_addr, entity_reg, dst_reg, idx_in_instrs)
    for idx, reg, addr in stack_minus4_sites:
        if idx + 1 >= len(instrs):
            continue
        nxt = instrs[idx + 1]
        if nxt["mnem"] != "ldr":
            continue
        parts2 = nxt["op_str"].split(",", 1)
        if len(parts2) != 2:
            continue
        rd = parts2[0].strip()
        bracket = parse_bracket(parts2[1].strip())
        if not bracket:
            continue
        base, off = bracket
        if base != reg or off != 0:
            continue
        entity_reloads.append((nxt["addr"], reg, rd, idx + 1))
    print(f"\n=== {len(entity_reloads)} entity_ptr reload sites (`subs Rx, r7, #4; ldr Rd, [Rx]`) ===")
    for ra, sr, dr, di in entity_reloads:
        print(f"  reload @0x{ra:05x}: ldr {dr}, [{sr}]")
        for j in range(di + 1, min(di + 6, len(instrs))):
            jin = instrs[j]
            print(f"    +{j-di}: 0x{jin['addr']:05x} {jin['mnem']:6} {jin['op_str']}")
        print()

    # For each reload, walk forward 12 instr looking for `ldr/str Ry, [Rd, #M]`
    accesses = []
    for reload_addr, sreg, dreg, didx in entity_reloads:
        for j in range(didx + 1, min(didx + 14, len(instrs))):
            jin = instrs[j]
            jmnem = jin["mnem"]
            jop = jin["op_str"]
            if jmnem in ("bl", "blx"):
                # caller-saved clobbered; continue but mark broken if dreg ∈ caller-saved
                if dreg in ("r0", "r1", "r2", "r3"):
                    break
                continue
            if jmnem.startswith(("ldr", "str")):
                parts2 = jop.split(",", 1)
                if len(parts2) == 2:
                    bracket = parse_bracket(parts2[1].strip())
                    if bracket and bracket[0] == dreg:
                        accesses.append((jin["addr"], jmnem, jop, bracket[1], reload_addr))
                        # If ldr Rd, [Rd, #x] — dreg now clobbered
                        rd = parts2[0].strip()
                        if jmnem.startswith("ldr") and rd == dreg:
                            break
                        continue
            # Check if dreg gets clobbered by any other instruction
            parts_op = [p.strip() for p in jop.split(",")]
            if parts_op and parts_op[0] == dreg and jmnem not in ("cmp", "tst", "cmn"):
                # Some instructions like `adds r3, r3, #N` modify r3
                # If it's `adds Rd, Rd, #N` or `subs Rd, Rd, #N` — Rd no longer entity_ptr
                if jmnem in ("adds", "subs"):
                    # Wait — `adds r3, #0x10` is the loop advance which means r3
                    # NOW points to NEXT entity, still entity-like. But for our analysis
                    # we just stop here; loop advance is rare and stops are conservative.
                    break

    print(f"\n=== Total entity record accesses: {len(accesses)} ===\n")

    ldr = Counter()
    ldrb = Counter()
    str_ = Counter()
    strb = Counter()
    for _, mnem, _, off, _ in accesses:
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

    print("\n=== First 30 accesses ===")
    for addr, mnem, op, off, rldr in accesses[:30]:
        print(f"  0x{addr:05x} {mnem:6} {op}  (+0x{off:x})  [reload@0x{rldr:05x}]")


if __name__ == "__main__":
    main()
