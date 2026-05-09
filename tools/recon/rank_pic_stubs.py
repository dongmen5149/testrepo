"""§4.4 후속 — 402 PIC stub 함수 우선순위 ranking (자동 분석 2I).

배경 (2026-05-10 PM-2 발견):
  Ghidra 가 1470 함수 중 ~402 (~27%) 를 다음 패턴으로 디컴파일 실패:
    void FUN_xxx(void) {
      /* WARNING: Subroutine does not return */
      FUN_0004ad10();
    }
  Ghidra 는 prologue 만 보고 control flow 추적 실패. 실제는 PIC 함수 본체.

이번 도구의 목적:
  1. all_decompiled.c 에서 402 stub 함수 주소 추출
  2. 각 함수의 진짜 크기 추정 (다음 함수 entry 까지 거리)
  3. raw bytes 에서 BL 명령 카운트 (Thumb-2 BL 패턴 디코드)
  4. 호출 빈도 (다른 함수에서 얼마나 많이 BL 로 호출되는지)
  5. ranking → 분석 우선순위 결정

호출 빈도 산출:
  바이너리 전체에 대해 capstone 으로 BL 디스어셈블 → 각 stub 주소가 BL target 에
  몇 번 등장하는지 카운트. PIC indirect call 은 못 잡지만 직접 BL 만으로도 의미 있음.

스코어 (간단 가중):
  rank = caller_count*5 + bl_in_func*1 + log2(size+1)*2
"""
from __future__ import annotations

import json
import math
import re
import struct
from collections import Counter
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
DECOMPILED = REPO / "work" / "ghidra_out" / "all_decompiled.c"
OUT = REPO / "work" / "h3" / "pic_stubs_ranked.json"

# Pattern matches: void/undefined4 FUN_xxxxx(...) { /* WARNING: Subroutine does not return */ FUN_0004ad10(); }
STUB_RE = re.compile(
    r'^(?:void|undefined\d?)\s+(FUN_([0-9a-f]+))\([^)]*\)\s*\n\s*\n?\{\s*\n?\s*/\* WARNING: Subroutine does not return \*/\s*\n\s*FUN_0004ad10\(\);\s*\n\}',
    re.MULTILINE,
)

# Match all FUN_xxxxxxxx entries (whether stub or not) for size estimation
ENTRY_RE = re.compile(r'^(?:void|undefined\d?|short|int|uint|char|byte|long|longlong|float|double|bool|ushort|ulong)\s+(FUN_([0-9a-f]+))\(', re.MULTILINE)


def collect_stubs(text: str) -> list[tuple[str, int]]:
    """Return [(name, addr), ...] for all stub functions."""
    return [(m.group(1), int(m.group(2), 16)) for m in STUB_RE.finditer(text)]


def collect_all_entries(text: str) -> list[tuple[str, int]]:
    """Return [(name, addr), ...] for all decompiled function entries (sorted by addr)."""
    seen = set()
    entries = []
    for m in ENTRY_RE.finditer(text):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        entries.append((name, int(m.group(2), 16)))
    entries.sort(key=lambda x: x[1])
    return entries


def build_bl_target_map(data: bytes, end_addr: int) -> Counter:
    """Disassemble binary in Thumb mode, count BL targets across all instructions."""
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    counter: Counter = Counter()
    pos = 0
    while pos < end_addr:
        chunk = data[pos:end_addr]
        any_emitted = False
        last = pos
        for ins in md.disasm(chunk, pos):
            if ins.mnemonic in ("bl", "blx"):
                tok = ins.op_str.strip().lstrip("#")
                if tok.startswith("0x"):
                    try:
                        counter[int(tok, 16)] += 1
                    except ValueError:
                        pass
            last = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            pos = last
        pos += 2
    return counter


def count_bls_in_range(data: bytes, start: int, end: int) -> tuple[int, int]:
    """Return (bl_count, instr_count) inside [start, end)."""
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    bl_count = 0
    instr_count = 0
    pos = start
    while pos < end:
        chunk = data[pos:end]
        any_emitted = False
        last = pos
        for ins in md.disasm(chunk, pos):
            instr_count += 1
            if ins.mnemonic in ("bl", "blx"):
                bl_count += 1
            last = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            pos = last
        pos += 2
    return bl_count, instr_count


def main() -> None:
    if not DECOMPILED.exists():
        print(f"!! decompiled missing: {DECOMPILED}")
        return
    if not BIN.exists():
        print(f"!! binary missing: {BIN}")
        return

    text = DECOMPILED.read_text(encoding="utf-8", errors="replace")
    data = BIN.read_bytes()

    stubs = collect_stubs(text)
    entries = collect_all_entries(text)
    print(f"=== {len(stubs)} stub functions found ===")
    print(f"=== {len(entries)} total decompiled entries ===")

    # Map addr -> next entry addr (for size estimation)
    addrs_sorted = [a for _, a in entries]
    addrs_set = set(addrs_sorted)
    next_addr = {}
    for i, a in enumerate(addrs_sorted):
        next_addr[a] = addrs_sorted[i + 1] if i + 1 < len(addrs_sorted) else len(data)

    # Build full-binary BL target counter (for caller_count)
    print("\nbuilding global BL target map (capstone full-binary scan)...")
    bl_targets = build_bl_target_map(data, len(data))
    print(f"distinct BL targets: {len(bl_targets)}, total BL instructions: {sum(bl_targets.values())}")

    # For each stub: gather size, in-function BL count, caller count
    rows = []
    for name, addr in stubs:
        if addr not in next_addr:
            continue
        end = next_addr[addr]
        # Cap reasonable size (some entries might be very far if Ghidra missed entries)
        size = end - addr
        if size > 0x4000:  # 16KB cap — likely wrong neighbor
            size_capped = 0x4000
        else:
            size_capped = size
        bl_count, instr_count = count_bls_in_range(data, addr, addr + size_capped)
        caller_count = bl_targets.get(addr, 0) + bl_targets.get(addr + 1, 0)  # Thumb bit may flip
        # Score
        score = caller_count * 5 + bl_count * 1 + math.log2(size_capped + 1) * 2
        rows.append({
            "name": name,
            "addr": addr,
            "addr_hex": f"0x{addr:08x}",
            "size_bytes": size,
            "size_capped": size_capped,
            "bl_count": bl_count,
            "instr_count": instr_count,
            "caller_count": caller_count,
            "score": round(score, 2),
        })

    rows.sort(key=lambda r: r["score"], reverse=True)

    print(f"\n=== top 30 stub functions by composite score ===")
    print(f"{'rank':<5} {'addr':<12} {'name':<24} {'size':>6} {'BLs':>5} {'callers':>8} {'score':>7}")
    print("-" * 70)
    for i, r in enumerate(rows[:30], 1):
        print(f"{i:<5} {r['addr_hex']:<12} {r['name']:<24} {r['size_bytes']:>6} {r['bl_count']:>5} {r['caller_count']:>8} {r['score']:>7}")

    # Top 5 size; top 5 caller
    print(f"\n=== top 10 by SIZE ===")
    for r in sorted(rows, key=lambda r: r["size_bytes"], reverse=True)[:10]:
        print(f"  0x{r['addr']:08x} {r['name']:<24} size={r['size_bytes']:>5} BLs={r['bl_count']:>4} callers={r['caller_count']:>3}")

    print(f"\n=== top 10 by CALLER_COUNT ===")
    for r in sorted(rows, key=lambda r: r["caller_count"], reverse=True)[:10]:
        print(f"  0x{r['addr']:08x} {r['name']:<24} callers={r['caller_count']:>3} size={r['size_bytes']:>5} BLs={r['bl_count']:>4}")

    print(f"\n=== top 10 by BL_COUNT (most internal calls) ===")
    for r in sorted(rows, key=lambda r: r["bl_count"], reverse=True)[:10]:
        print(f"  0x{r['addr']:08x} {r['name']:<24} BLs={r['bl_count']:>4} size={r['size_bytes']:>5} callers={r['caller_count']:>3}")

    # Stats
    sizes = [r["size_bytes"] for r in rows]
    bls = [r["bl_count"] for r in rows]
    callers = [r["caller_count"] for r in rows]
    print(f"\n=== distribution ===")
    print(f"  size:    min={min(sizes)} median={sorted(sizes)[len(sizes)//2]} max={max(sizes)}")
    print(f"  BLs:     min={min(bls)} median={sorted(bls)[len(bls)//2]} max={max(bls)}")
    print(f"  callers: min={min(callers)} median={sorted(callers)[len(callers)//2]} max={max(callers)}")
    no_caller = sum(1 for c in callers if c == 0)
    print(f"  stubs with 0 direct callers (PIC-indirect only): {no_caller} / {len(rows)}")

    # Save full ranking
    out = {
        "stub_count": len(stubs),
        "ranked": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
