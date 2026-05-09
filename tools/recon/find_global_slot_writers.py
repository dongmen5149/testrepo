"""§4.4 후속 — 특정 GOT 글로벌 슬롯에 write 하는 사이트 추적 (자동 분석 2U).

배경 (2026-05-10 PM-6 발견):
  FUN_0004ad10 (context_getter) 가 단일 슬롯 GOT base + 0x444 = 0xB3084 의 값 반환.
  이 슬롯이 게임의 핵심 single global state pointer 후보.
  → 누가 이 슬롯에 write 하는지 식별 = 게임 init / state transition entry 포인트.

전략:
  binary 전체 capstone 디스어셈블 → 다음 패턴 검색:
  1. `str.w rN, [sl, #0x444]` — direct Thumb-2 store
  2. `str rN, [rM, #0x444]` 어디든 (base reg 가 sl 일 가능성 높음)
  3. `add rD, sl, #imm; str rN, [rD, #...]` — 두-단계 store
  4. PC-rel literal load 로 0x444 또는 0xb3084 같은 값을 받는 pattern (간접 셋업)

또한 read 패턴도 같이 추적해서 read/write 비율 확인.

기본 타겟: GOT_BASE = 0xb2c40, SLOT_OFFSET = 0x444 → SLOT_ADDR = 0xb3084.
다른 슬롯도 분석할 수 있도록 인자 받음.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
DECOMPILED = REPO / "work" / "ghidra_out" / "all_decompiled.c"

GOT_BASE = 0x000B2C40

ENTRY_RE = re.compile(
    r'^(?:void|undefined\d?|short|int|uint|char|byte|long|longlong|float|double|bool|ushort|ulong)\s+(FUN_([0-9a-f]+))\(',
    re.MULTILINE,
)


def collect_entries(text: str) -> tuple[list[int], list[str]]:
    seen = set()
    out = []
    for m in ENTRY_RE.finditer(text):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        out.append((name, int(m.group(2), 16)))
    out.sort(key=lambda x: x[1])
    return [a for _, a in out], [n for n, _ in out]


def find_enclosing_func(addr: int, addrs: list[int], names: list[str]) -> str:
    lo, hi = 0, len(addrs) - 1
    result = "?"
    while lo <= hi:
        mid = (lo + hi) // 2
        if addrs[mid] <= addr:
            result = names[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot-offset", type=lambda x: int(x, 0), default=0x444,
                        help="GOT slot offset (default: 0x444 = FUN_0004ad10's slot)")
    args = parser.parse_args()
    slot_offset = args.slot_offset
    slot_addr = GOT_BASE + slot_offset
    print(f"=== tracking writes to slot at GOT+0x{slot_offset:x} (= 0x{slot_addr:08x}) ===")

    if not BIN.exists() or not DECOMPILED.exists():
        print("!! input missing")
        return
    data = BIN.read_bytes()
    text = DECOMPILED.read_text(encoding="utf-8", errors="replace")
    entries_addr, entries_name = collect_entries(text)
    print(f"=== {len(entries_addr)} decompiled function entries ===")

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False

    print(f"=== walking {len(data)} bytes (Thumb auto-skip) ===")
    instrs: list[dict] = []
    pos = 0
    end = len(data)
    while pos < end:
        chunk = data[pos:end]
        any_emitted = False
        last = pos
        for ins in md.disasm(chunk, pos):
            instrs.append({
                "addr": ins.address, "mnem": ins.mnemonic,
                "op_str": ins.op_str, "size": ins.size,
            })
            last = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            pos = last
        pos += 2
    print(f"=== {len(instrs)} instructions disassembled ===")

    # Patterns to search:
    # A. str/strb/strh Rt, [sl, #0x444]   or  [r10, #0x444]
    # B. ldr/ldrb/ldrh Rt, [sl, #0x444]
    # C. PC-rel LDR with target value == slot_offset (immediate)
    # D. movw/mov.w Rd, #slot_offset   (loaded into reg, may be used as offset)

    str_pattern_re = re.compile(rf"\[(?:sl|r10),\s*#0x{slot_offset:x}\b")
    ldr_pattern_re = re.compile(rf"\[(?:sl|r10),\s*#0x{slot_offset:x}\b")

    write_sites: list[dict] = []
    read_sites: list[dict] = []
    pcrel_lit_sites: list[dict] = []  # PC-rel LDR loading slot_offset value
    movw_sites: list[dict] = []  # movw Rd, #slot_offset

    write_mnems = {"str", "str.w", "strb", "strb.w", "strh", "strh.w"}
    read_mnems = {"ldr", "ldr.w", "ldrb", "ldrb.w", "ldrh", "ldrh.w"}

    for i, ins in enumerate(instrs):
        op_str = ins["op_str"]
        op_norm = op_str.replace(" ", "")
        # Direct [sl, #0x444] pattern
        if str_pattern_re.search(op_str) and ins["mnem"] in write_mnems:
            write_sites.append({"idx": i, "addr": ins["addr"], "mnem": ins["mnem"], "op_str": op_str})
        elif ldr_pattern_re.search(op_str) and ins["mnem"] in read_mnems:
            read_sites.append({"idx": i, "addr": ins["addr"], "mnem": ins["mnem"], "op_str": op_str})

        # PC-rel LDR with literal value matching slot_offset or slot_addr
        if ins["mnem"] in ("ldr", "ldr.w") and "[pc," in op_norm:
            try:
                imm = int(op_norm.split("#", 1)[1].rstrip("]"), 0)
                pc = (ins["addr"] + 4) & ~3
                target = pc + imm
                if 0 <= target < len(data) - 4:
                    import struct
                    v = struct.unpack("<I", data[target:target+4])[0]
                    if v == slot_offset:
                        pcrel_lit_sites.append({"idx": i, "addr": ins["addr"], "lit_addr": target,
                                                "value": v, "mnem": ins["mnem"], "op_str": op_str})
                    elif v == slot_addr:
                        pcrel_lit_sites.append({"idx": i, "addr": ins["addr"], "lit_addr": target,
                                                "value": v, "mnem": ins["mnem"], "op_str": op_str,
                                                "note": "absolute slot address"})
            except (IndexError, ValueError):
                pass

        # movw Rd, #slot_offset
        if ins["mnem"] in ("movw", "mov.w", "mov", "movs"):
            try:
                parts = op_str.split(",")
                if len(parts) >= 2 and parts[1].strip().startswith("#"):
                    imm = int(parts[1].strip().lstrip("#"), 0)
                    if imm == slot_offset:
                        movw_sites.append({"idx": i, "addr": ins["addr"], "mnem": ins["mnem"], "op_str": op_str})
            except (IndexError, ValueError):
                pass

    print(f"\n=== direct [sl, #0x{slot_offset:x}] write sites: {len(write_sites)} ===")
    for w in write_sites[:30]:
        func = find_enclosing_func(w["addr"], entries_addr, entries_name)
        print(f"  0x{w['addr']:08x} (in {func}): {w['mnem']:8s} {w['op_str']}")
    if len(write_sites) > 30:
        print(f"  ... ({len(write_sites)-30} more)")

    print(f"\n=== direct [sl, #0x{slot_offset:x}] read sites: {len(read_sites)} ===")
    for r in read_sites[:30]:
        func = find_enclosing_func(r["addr"], entries_addr, entries_name)
        print(f"  0x{r['addr']:08x} (in {func}): {r['mnem']:8s} {r['op_str']}")
    if len(read_sites) > 30:
        print(f"  ... ({len(read_sites)-30} more)")

    print(f"\n=== PC-rel LDR loading literal 0x{slot_offset:x}: {len(pcrel_lit_sites)} sites ===")
    for p in pcrel_lit_sites[:20]:
        func = find_enclosing_func(p["addr"], entries_addr, entries_name)
        note = f"  [{p.get('note','')}]" if p.get("note") else ""
        print(f"  0x{p['addr']:08x} (in {func}): {p['mnem']:8s} {p['op_str']} = 0x{p['value']:x}{note}")
    if len(pcrel_lit_sites) > 20:
        print(f"  ... ({len(pcrel_lit_sites)-20} more)")

    print(f"\n=== movw Rd, #0x{slot_offset:x}: {len(movw_sites)} sites ===")
    for m in movw_sites[:20]:
        func = find_enclosing_func(m["addr"], entries_addr, entries_name)
        print(f"  0x{m['addr']:08x} (in {func}): {m['mnem']:8s} {m['op_str']}")

    # Group by enclosing function
    func_to_writes: defaultdict[str, list] = defaultdict(list)
    for w in write_sites:
        func = find_enclosing_func(w["addr"], entries_addr, entries_name)
        func_to_writes[func].append(w["addr"])
    func_to_reads: defaultdict[str, list] = defaultdict(list)
    for r in read_sites:
        func = find_enclosing_func(r["addr"], entries_addr, entries_name)
        func_to_reads[func].append(r["addr"])

    print(f"\n=== writer functions ({len(func_to_writes)}): ===")
    for func, addrs in sorted(func_to_writes.items(), key=lambda x: -len(x[1])):
        print(f"  {func:<26} {len(addrs):>3} writes  (first @0x{addrs[0]:08x})")

    print(f"\n=== reader functions ({len(func_to_reads)}): ===")
    for func, addrs in sorted(func_to_reads.items(), key=lambda x: -len(x[1]))[:30]:
        print(f"  {func:<26} {len(addrs):>3} reads   (first @0x{addrs[0]:08x})")

    # Also look for two-step pattern: add rD, sl, #imm  followed by  str/ldr Rt, [rD, ...]
    # where (sl + imm + small_offset) approximates slot_offset
    two_step_writes = 0
    two_step_reads = 0
    for i, ins in enumerate(instrs):
        if ins["mnem"] in ("add", "adds", "add.w") and "sl" in ins["op_str"]:
            parts = ins["op_str"].split(",")
            if len(parts) >= 3 and parts[2].strip().startswith("#"):
                try:
                    imm = int(parts[2].strip().lstrip("#"), 0)
                    if abs(imm - slot_offset) < 0x80:  # close to target offset
                        # Check next 3 instr for str/ldr [rD, #small_offset]
                        rd = parts[0].strip()
                        for j in range(i + 1, min(i + 4, len(instrs))):
                            if rd in instrs[j]["op_str"] and "[" in instrs[j]["op_str"]:
                                if instrs[j]["mnem"] in write_mnems:
                                    two_step_writes += 1
                                elif instrs[j]["mnem"] in read_mnems:
                                    two_step_reads += 1
                                break
                except (IndexError, ValueError):
                    pass

    print(f"\n=== two-step access (add sl, near-offset → str/ldr): writes {two_step_writes}, reads {two_step_reads} ===")

    out = {
        "slot_offset": f"0x{slot_offset:x}",
        "slot_addr": f"0x{slot_addr:08x}",
        "got_base": f"0x{GOT_BASE:08x}",
        "direct_writes": len(write_sites),
        "direct_reads": len(read_sites),
        "writers_by_func": {f: len(a) for f, a in sorted(func_to_writes.items(), key=lambda x: -len(x[1]))},
        "readers_by_func": {f: len(a) for f, a in sorted(func_to_reads.items(), key=lambda x: -len(x[1]))},
        "writer_sites": [
            {"addr": f"0x{w['addr']:08x}", "func": find_enclosing_func(w["addr"], entries_addr, entries_name),
             "mnem": w["mnem"], "op_str": w["op_str"]}
            for w in write_sites
        ],
        "reader_sites": [
            {"addr": f"0x{r['addr']:08x}", "func": find_enclosing_func(r["addr"], entries_addr, entries_name),
             "mnem": r["mnem"], "op_str": r["op_str"]}
            for r in read_sites
        ],
        "pcrel_lit_count": len(pcrel_lit_sites),
        "movw_count": len(movw_sites),
        "two_step_writes": two_step_writes,
        "two_step_reads": two_step_reads,
    }
    out_path = REPO / "work" / "h3" / f"global_slot_0x{slot_offset:x}_writers.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {out_path}")


if __name__ == "__main__":
    main()
