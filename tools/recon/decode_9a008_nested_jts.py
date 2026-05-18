"""Round 53 / 2TA: FUN_9a008 의 7+16 entry nested JT 디코드 + leaf 추출.

R52 prologue 분석 결과:
  - JT_1 @ sl + 0xffff9f90, idx (0..6), 7 entries  (cmp #6)
  - JT_2 @ sl + 0xffff9fac, idx (0..15), 16 entries (cmp #0xf)
sl_base = 0xb2c40 (GOT base).

각 JT 의 entry 와 target 추출, leaf 식별.
"""
import struct
from pathlib import Path

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40

JTS = [
    ("JT_1 (7 entries, cmp #6)",  0xffff9f90, 7),
    ("JT_2 (16 entries, cmp #0xf)", 0xffff9fac, 16),
]


def main() -> None:
    for label, sl_offset, count in JTS:
        jt_base = (GOT_BASE + sl_offset) & 0xFFFFFFFF
        print(f"\n=== {label} ===")
        print(f"  sl_offset = 0x{sl_offset:08x}  JT_base = 0x{GOT_BASE:05x} + 0x{sl_offset:x} = 0x{jt_base:08x}")
        if jt_base + count * 4 > len(DATA):
            print(f"  (JT extends beyond binary)")
            continue
        seen = {}
        for i in range(count):
            entry_addr = jt_base + i * 4
            entry = struct.unpack("<I", DATA[entry_addr:entry_addr + 4])[0]
            if entry & 0x80000000:
                entry_signed = entry - 0x100000000
            else:
                entry_signed = entry
            # target = JT_base + JT[idx] + idx*4 — wait, R51 saw `pc = jt_base + JT[idx]` (not idx*4 added)
            # Actually for FUN_9a008: 0x9a050: ldr r3, [r1, r2]  ; r3 = JT[idx*4]
            #                          0x9a052: adds r3, r3, r2   ; r3 = JT[idx] + r2 (=JT_base)
            #                          0x9a054: mov pc, r3
            # So target = JT_base + JT[idx]
            target = (jt_base + entry) & 0xFFFFFFFF
            tc = target & ~1
            seen.setdefault(tc, []).append(i)
            in_range = "" if tc < len(DATA) else " (OUT)"
            thumb = "thumb" if (target & 1) else "arm/data"
            print(f"  idx={i:2d}  JT[{i}]@0x{entry_addr:05x}=0x{entry:08x}({entry_signed:+d})  -> 0x{tc:05x} [{thumb}]{in_range}")
        print(f"  Distinct targets: {len(seen)}")
        for tgt, idxs in sorted(seen.items()):
            in_range = "" if tgt < len(DATA) else " (OUT)"
            idx_str = ",".join(str(i) for i in idxs)
            print(f"    0x{tgt:05x}{in_range}  ({len(idxs)}x: i={idx_str})")


if __name__ == "__main__":
    main()
