"""Round 50 / 2QA: FUN_3a86c의 16 JT entries 전체 디코드.

JT 디스패치 (Round 49 finding):
  0x3a8aa: ldr r3, [r7-0xc]              ; r3 = entity_arg + 0x10 (= idx, 0..0xf)
  0x3a8ac: lsls r2, r3, #2                ; r2 = idx * 4
  0x3a8ae: ldr r3, [pc, #0x128]           ; r3 = LITERAL1 (sl-rel offset)
  0x3a8b0: add r3, sl                     ; r3 = sl + LITERAL1 = GOT slot addr (JT base)
  0x3a8b2: adds r3, r2, r3                ; r3 = JT_base + idx*4
  0x3a8b4: ldr r2, [r3]                   ; r2 = JT[idx] (offset)
  0x3a8b6: ldr r3, [pc, #0x120]           ; r3 = LITERAL2 (sl-rel offset)
  0x3a8b8: add r3, sl                     ; r3 = sl + LITERAL2 = target base GOT slot
  0x3a8ba: adds r3, r2, r3                ; r3 = target_base + JT[idx]
  0x3a8bc: mov pc, r3                     ; pc = target_base + JT[idx]

전략:
1. LITERAL1/LITERAL2 pc-rel 풀이 → sl-rel offsets
2. sl = GOT base = 0xb2c40 (Round 42)
3. GOT[+LITERAL1] = JT base pointer (binary 내 word table 위치)
4. GOT[+LITERAL2] = target base (target 함수 주소 베이스)
5. JT 16 entries 읽어서 각각 디코드
6. 각 target = target_base + JT[idx] 의 실제 주소 추출
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40
SL_BASE = GOT_BASE  # sl is set to GOT base in FUN_3a86c prologue


def resolve_pc_rel(ldr_addr: int, imm: int) -> int:
    pc = (ldr_addr + 4) & ~3
    return pc + imm


def read_word(addr: int) -> int:
    if addr + 4 > len(DATA):
        return 0
    return struct.unpack("<I", DATA[addr:addr + 4])[0]


def main() -> None:
    # LITERAL1 / LITERAL2 (same literal pool slot @ 0x3a9d8, value = 0xffff481c)
    lit1_addr = resolve_pc_rel(0x3a8ae, 0x128)
    lit1 = read_word(lit1_addr)
    print(f"=== JT base lookup ===")
    print(f"LITERAL1 @ 0x{lit1_addr:05x} = 0x{lit1:08x}")
    lit2_addr = resolve_pc_rel(0x3a8b6, 0x120)
    lit2 = read_word(lit2_addr)
    print(f"LITERAL2 @ 0x{lit2_addr:05x} = 0x{lit2:08x}")
    print("(both load same literal — SELF-RELATIVE JT pattern)")
    print()

    # Self-relative JT pattern:
    # JT_base = sl + LITERAL = 0xb2c40 + 0xffff481c = 0xa745c (32-bit modular)
    # Entries at JT_base + idx*4 (16 entries = 0xa745c..0xa749c)
    # Target for each = JT_base + JT[idx]  (entry is signed offset from JT base)
    jt_base = (SL_BASE + lit1) & 0xFFFFFFFF
    print(f"=== JT base address ===")
    print(f"JT_base = sl + LITERAL1 = 0x{SL_BASE:05x} + 0x{lit1:x} = 0x{jt_base:08x}")

    if jt_base + 0x40 > len(DATA):
        print(f"(JT base @ 0x{jt_base:05x} extends beyond binary)")
        return
    print()

    # Read 16 entries
    print(f"=== 16 JT entries @ 0x{jt_base:05x} (self-relative offsets) ===")
    entries = []
    for i in range(16):
        entry_addr = jt_base + i * 4
        entry = read_word(entry_addr)
        # Treat as signed 32-bit
        if entry & 0x80000000:
            entry_signed = entry - 0x100000000
        else:
            entry_signed = entry
        target = (jt_base + entry) & 0xFFFFFFFF
        entries.append((entry, entry_signed, target))
        in_range = "" if target < len(DATA) else " (OUT)"
        # Thumb function: target should have low bit set; clear it for symbol comparison
        target_clean = target & ~1
        thumb_bit = " thumb" if target & 1 else " arm/data"
        print(f"  idx={i:2d}  JT[{i}] @ 0x{entry_addr:05x} = 0x{entry:08x} ({entry_signed:+d})  -> 0x{target_clean:05x}{thumb_bit}{in_range}")

    # Entity_arg mapping
    print()
    print("=== entity_arg mapping (idx = entity_arg + 0x10, entity_arg ∈ [-0x10..-1]) ===")
    seen_targets = {}
    for i, (entry, esigned, target) in enumerate(entries):
        ea = i - 0x10  # signed entity_arg
        target_clean = target & ~1
        seen_targets.setdefault(target_clean, []).append((i, ea))
        in_range = "" if target_clean < len(DATA) else " (OUT)"
        print(f"  entity_arg = {ea:+3d} (0x{ea & 0xff:02x})  idx={i:2d}  -> 0x{target_clean:05x}{in_range}")

    # Distinct targets
    print()
    print(f"=== Distinct JT targets ({len(seen_targets)}) ===")
    for tgt, hits in sorted(seen_targets.items()):
        idxs = ", ".join(f"idx{i}(ea={ea:+d})" for i, ea in hits)
        in_range = "" if tgt < len(DATA) else " (OUT)"
        print(f"  0x{tgt:05x}{in_range}  : {idxs}")


if __name__ == "__main__":
    main()
