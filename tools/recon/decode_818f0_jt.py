"""Round 51 / 2RA: FUN_818f0 의 74 JT entries 전체 디코드.

JT 디스패치 (Round 50 disasm 결과):
  0x81988: ldr r3, [r2]                          ; r3 = local[-0x6c] = arg + 0x10 (idx)
  0x8198a: lsls r2, r3, #2                       ; r2 = idx * 4
  0x8198c: ldr r3, [pc, #0x330]                  ; LITERAL1 (sl-rel offset)
  0x8198e: add r3, sl                            ; r3 = sl + LIT1 (JT base addr)
  0x81990: adds r3, r2, r3                       ; r3 = JT_base + idx*4
  0x81992: ldr r2, [r3]                          ; r2 = JT[idx] (offset value)
  0x81994: ldr r3, [pc, #0x328]                  ; LITERAL2 (sl-rel offset)
  0x81996: add r3, sl                            ; r3 = sl + LIT2 (target base)
  0x81998: adds r3, r2, r3                       ; r3 = target_base + JT[idx]
  0x8199a: mov pc, r3                            ; INDIRECT JT JUMP

LITERAL1 pc-rel = (0x8198c+4)&~3 + 0x330 = 0x81990 + 0x330 = 0x81cc0
LITERAL2 pc-rel = (0x81994+4)&~3 + 0x328 = 0x81998 + 0x328 = 0x81cc0
→ 같은 literal! self-relative JT pattern (FUN_3a86c 와 동일).

전략:
1. LITERAL @ 0x81cc0 읽기
2. JT_base = sl + LITERAL = 0xb2c40 + LIT (32-bit modular)
3. 74 entries 읽고 target = JT_base + JT[idx] 계산
4. idx ∈ [0..0x49] (74), arg = idx - 0x10 (signed [-0x10..0x39])
5. fall-through default = 0x8199c (BL 0x3d434) — JT[0] 이 가리킬 가능성 있음
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40
SL_BASE = GOT_BASE


def resolve_pc_rel(ldr_addr: int, imm: int) -> int:
    pc = (ldr_addr + 4) & ~3
    return pc + imm


def read_word(addr: int) -> int:
    if addr + 4 > len(DATA):
        return 0
    return struct.unpack("<I", DATA[addr:addr + 4])[0]


def main() -> None:
    lit1_addr = resolve_pc_rel(0x8198c, 0x330)
    lit1 = read_word(lit1_addr)
    lit2_addr = resolve_pc_rel(0x81994, 0x328)
    lit2 = read_word(lit2_addr)
    print("=== JT base lookup ===")
    print(f"LITERAL1 @ 0x{lit1_addr:05x} = 0x{lit1:08x}")
    print(f"LITERAL2 @ 0x{lit2_addr:05x} = 0x{lit2:08x}")
    if lit1_addr == lit2_addr:
        print("(both load same literal pool slot — SELF-RELATIVE JT)")
    print()

    jt_base = (SL_BASE + lit1) & 0xFFFFFFFF
    print("=== JT base address ===")
    print(f"JT_base = sl + LIT1 = 0x{SL_BASE:05x} + 0x{lit1:08x} = 0x{jt_base:08x}")
    if jt_base + 74 * 4 > len(DATA):
        print(f"(JT extends beyond binary @ 0x{jt_base:05x}, binary size 0x{len(DATA):x})")
        return
    print()

    print(f"=== 74 JT entries @ 0x{jt_base:05x} (self-relative offsets) ===")
    entries = []
    for i in range(74):
        entry_addr = jt_base + i * 4
        entry = read_word(entry_addr)
        if entry & 0x80000000:
            entry_signed = entry - 0x100000000
        else:
            entry_signed = entry
        target = (jt_base + entry) & 0xFFFFFFFF
        entries.append((entry, entry_signed, target))
        target_clean = target & ~1
        thumb_bit = "thumb" if (target & 1) else "arm/data"
        in_range = "" if target_clean < len(DATA) else " (OUT)"
        arg_signed = i - 0x10
        print(f"  idx={i:3d}  arg={arg_signed:+4d} (0x{arg_signed & 0xff:02x})  "
              f"JT[{i:2d}]@0x{entry_addr:05x}=0x{entry:08x}({entry_signed:+d})  -> 0x{target_clean:05x} [{thumb_bit}]{in_range}")

    print()
    print("=== Distinct JT targets ===")
    seen = {}
    for i, (e, es, t) in enumerate(entries):
        tc = t & ~1
        seen.setdefault(tc, []).append((i, i - 0x10))
    for tgt, hits in sorted(seen.items()):
        idxs = ", ".join(f"i{i}(a={a:+d})" for i, a in hits)
        in_range = "" if tgt < len(DATA) else " (OUT)"
        print(f"  0x{tgt:05x}{in_range}  ({len(hits):2d}x)  : {idxs}")

    print()
    print(f"Total distinct targets: {len(seen)}")


if __name__ == "__main__":
    main()
