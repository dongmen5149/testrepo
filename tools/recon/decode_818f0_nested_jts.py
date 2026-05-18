"""Round 51 / 2RA: FUN_818f0 의 6 handlers (arg=-16,-5,-3,-4,-1,-2) 의 nested 2nd-level JT 디코드.

각 handler nested JT 패턴 (5 inst sequence):
  ldr Rx, [r_ctx_off]       ; idx = task[+0xac78]
  lsls r2, r3, #2           ; r2 = idx*4
  ldr r3, [pc, #imm_a]      ; LITa = JT base sl-rel offset
  add r3, sl
  adds r3, r2, r3
  ldr r2, [r3]              ; r2 = JT[idx]
  ldr r3, [pc, #imm_b]      ; LITb = target base sl-rel offset
  add r3, sl
  adds r3, r2, r3
  mov pc, r3                ; pc = target_base + JT[idx]

이미 추출한 disasm 결과에서 ldr+lsls+ldr 패턴의 두 PC-rel imm 을 알면 JT base + target base 식별.
모든 handler가 self-relative JT 패턴 → LITa = LITb (예상).
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40

# handler arg → (start_addr, cmp_limit) (count = limit + 1 entries)
HANDLERS = [
    (-16, 0x8199c, 12),
    (-5,  0x81b9c, 12),
    (-3,  0x823ea, 10),
    (-4,  0x8263a, 10),
    (-1,  0x828f6, 10),
    (-2,  0x82a98, 10),
]


def find_jt_dispatch(start: int, end: int) -> tuple[int, int] | None:
    """Find `lsls r2, r3, #2` followed by two `ldr Rx, [pc, #imm]; add Rx, sl` pairs.

    Returns (lita_imm, lita_addr) — both PC-rel imms point to same literal pool slot.
    """
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    insns = list(md.disasm(DATA[start:end], start))
    for i, ins in enumerate(insns):
        if ins.mnemonic == "lsls" and ", #2" in ins.op_str:
            # Look for next ldr r?, [pc, #...]
            for j in range(i + 1, min(i + 5, len(insns))):
                if insns[j].mnemonic == "ldr" and "[pc" in insns[j].op_str:
                    try:
                        imm = int(insns[j].op_str.split("#")[1].rstrip("]"), 0)
                        pc = (insns[j].address + 4) & ~3
                        return imm, pc + imm
                    except Exception:
                        pass
    return None


def main() -> None:
    print(f"{'arg':>4}  {'handler':>9}  {'jt_lit_addr':>12}  {'jt_lit_val':>10}  {'jt_base':>9}  count  entries")
    print("-" * 110)
    for arg, hstart, climit in HANDLERS:
        result = find_jt_dispatch(hstart, hstart + 0x80)
        if result is None:
            print(f"  arg={arg:+d}: dispatch not found")
            continue
        imm, lit_addr = result
        lit_val = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
        jt_base = (GOT_BASE + lit_val) & 0xFFFFFFFF
        count = climit + 1
        if jt_base + count * 4 > len(DATA):
            print(f"  arg={arg:+d}: JT @ 0x{jt_base:05x} out of range")
            continue
        # Read entries
        entries = []
        seen = {}
        for i in range(count):
            entry_addr = jt_base + i * 4
            entry = struct.unpack("<I", DATA[entry_addr:entry_addr + 4])[0]
            target = (jt_base + entry) & 0xFFFFFFFF
            tc = target & ~1
            entries.append(tc)
            seen.setdefault(tc, []).append(i)
        print(f"  {arg:+4d}  0x{hstart:05x}    0x{lit_addr:05x}     0x{lit_val:08x}  0x{jt_base:05x}  {count:2d}")
        for tgt, idxs in sorted(seen.items()):
            idx_str = ",".join(str(i) for i in idxs)
            in_range = "" if tgt < len(DATA) else " (OUT)"
            print(f"          → 0x{tgt:05x}{in_range}  ({len(idxs)}x: state={idx_str})")
        print()


if __name__ == "__main__":
    main()
