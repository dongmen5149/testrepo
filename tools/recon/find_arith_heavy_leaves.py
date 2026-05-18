"""Round 55 / 2VD: arith-heavy leaf 함수 grep.

전투 시스템의 damage calculation 패턴 후보:
  - high mul / muls (damage = atk × mult)
  - high asrs / lsrs (signed div, defense reduction)
  - high subs (HP -= dmg)
  - high ldrb / strb (stat byte access)
  - LOW BL count (leaf function, no callees)
  - small size (100-500B)

전략:
1. Ghidra decompiled.c entries 의 모든 함수에 대해 disasm
2. 각 함수의 size + BL count + mul/asrs/lsrs/subs count + ldrb/strb count
3. arith_score = mul*5 + asrs*2 + subs*2 + ldrb*1 + strb*1
4. arith_score / size 비율 높은 함수 = 산술 집약
5. BL <= 3 (leaf) AND size in [100, 800] AND arith_score >= 15 필터
"""
from __future__ import annotations
import bisect
import re
from pathlib import Path
from collections import Counter
import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
DECOMPILED = REPO / "work" / "ghidra_out" / "all_decompiled.c"

ENTRY_RE = re.compile(
    r'^(?:void|undefined\d?|short|int|uint|char|byte|long|longlong|float|double|bool|ushort|ulong)\s+(FUN_([0-9a-f]+))\(',
    re.MULTILINE,
)


def collect_entries(text: str):
    seen = set()
    out = []
    for m in ENTRY_RE.finditer(text):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        out.append(int(m.group(2), 16))
    out.sort()
    return out


def main():
    data = BIN.read_bytes()
    text = DECOMPILED.read_text(encoding="utf-8", errors="replace")
    entries = collect_entries(text)
    print(f"=== {len(entries)} function entries ===")

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False

    # Determine each function's size by next entry
    sizes = []
    for i, addr in enumerate(entries):
        nxt = entries[i + 1] if i + 1 < len(entries) else len(data)
        sizes.append(nxt - addr)

    # Analyze each function
    candidates = []
    for addr, size in zip(entries, sizes):
        if size < 80 or size > 1500:
            continue
        if addr + size > len(data):
            continue
        chunk = data[addr:addr + size]
        counts = Counter()
        for ins in md.disasm(chunk, addr):
            counts[ins.mnemonic] += 1

        bl_count = counts.get("bl", 0)
        if bl_count > 4:                                # leaf 필터 (적은 BL)
            continue

        muls = counts.get("muls", 0) + counts.get("mul", 0)
        asrs = counts.get("asrs", 0)
        lsrs = counts.get("lsrs", 0)
        lsls = counts.get("lsls", 0)
        subs = counts.get("subs", 0)
        adds = counts.get("adds", 0)
        ldrb = counts.get("ldrb", 0)
        strb = counts.get("strb", 0)
        cmps = counts.get("cmp", 0) + counts.get("cmps", 0)

        # arith-focused score
        arith_score = muls * 8 + asrs * 3 + lsrs * 2 + subs * 2 + ldrb * 1 + strb * 1
        if arith_score < 20:
            continue
        # bonus for mul (rare, strong battle indicator)
        if muls == 0 and arith_score < 35:
            continue

        candidates.append({
            "addr": addr, "size": size,
            "bls": bl_count, "muls": muls, "asrs": asrs, "lsrs": lsrs,
            "lsls": lsls, "subs": subs, "adds": adds,
            "ldrb": ldrb, "strb": strb, "cmps": cmps,
            "score": arith_score,
        })

    # Sort by mul count first (strongest indicator), then by score
    candidates.sort(key=lambda c: (-c["muls"], -c["score"]))

    print(f"=== Top 30 arith-heavy leaf candidates ===\n")
    print(f"  {'addr':>9}  {'size':>5}  {'BL':>2}  {'mul':>3}  {'asrs':>4}  {'lsrs':>4}  {'subs':>4}  {'ldrb':>4}  {'strb':>4}  {'cmp':>3}  {'score':>5}")
    for c in candidates[:30]:
        print(f"  FUN_{c['addr']:05x}  {c['size']:>5}  {c['bls']:>2}  {c['muls']:>3}  "
              f"{c['asrs']:>4}  {c['lsrs']:>4}  {c['subs']:>4}  "
              f"{c['ldrb']:>4}  {c['strb']:>4}  {c['cmps']:>3}  {c['score']:>5}")


if __name__ == "__main__":
    main()
