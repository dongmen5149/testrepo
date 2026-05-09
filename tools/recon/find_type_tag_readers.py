"""§4.4 후속 — 큐 type tag reader 함수 자동 검색 (자동 분석 2S).

배경 (2026-05-10 PM-5 발견):
  큐 protocol 의 type tag = 0x05 (가장 흔함, 16 emit) + 0x00/0x01/0x04/0x1f 등.
  writer 측은 byte_append immediate 분석으로 4 함수 식별. 이번에는 reader 측 식별.

전략:
  바이너리 전체 capstone 디스어셈블 → cmp #0x05 + 조건 분기 패턴 검색 → 포함 함수 식별.
  추가로 다른 type tags (0x00, 0x01, 0x04, 0x1f) 도 같이 검색해서 reader 후보 종합 매핑.

reader 식별 휴리스틱:
  1. 한 함수 안에 여러 type tag cmp arm 있으면 dispatcher 가능성 ↑
  2. cmp 직후 BL 패턴 → 각 type 별 핸들러 호출
  3. 큐 reader (FUN_0007e184/0x7e63c) 호출 직후 cmp 패턴 → 큐에서 byte 읽고 분기하는 reader 확정

출력:
  type tag 별 cmp 사이트 + 포함 함수 + 함수별 type tag coverage 매트릭스.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
DECOMPILED = REPO / "work" / "ghidra_out" / "all_decompiled.c"
OUT = REPO / "work" / "h3" / "type_tag_readers.json"

# Known type tags from PM-5 cumulative analysis
TYPE_TAGS = [0x00, 0x01, 0x03, 0x04, 0x05, 0x14, 0x1f, 0x3d, 0x3e, 0x3f, 0x40, 0x41]

# Queue reader API addresses (consumer side)
QUEUE_READERS = {
    0x0007e184: "memcpy_read",
    0x0007e63c: "consumer_?",
    0x0007ea98: "buffer_status",
}

COND_BRANCH = {"beq", "bne", "blt", "ble", "bgt", "bge", "bcs", "bcc", "bls", "bhi", "bmi", "bpl"}

ENTRY_RE = re.compile(
    r'^(?:void|undefined\d?|short|int|uint|char|byte|long|longlong|float|double|bool|ushort|ulong)\s+(FUN_([0-9a-f]+))\(',
    re.MULTILINE,
)


def collect_entries(text: str) -> list[tuple[str, int]]:
    seen = set()
    out = []
    for m in ENTRY_RE.finditer(text):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        out.append((name, int(m.group(2), 16)))
    out.sort(key=lambda x: x[1])
    return out


def find_enclosing_func(addr: int, entries_addr: list[int], entries_name: list[str]) -> str:
    """Binary search for enclosing function name."""
    lo, hi = 0, len(entries_addr) - 1
    result = "?"
    while lo <= hi:
        mid = (lo + hi) // 2
        if entries_addr[mid] <= addr:
            result = entries_name[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return result


def main() -> None:
    if not BIN.exists() or not DECOMPILED.exists():
        print("!! input missing")
        return
    data = BIN.read_bytes()
    text = DECOMPILED.read_text(encoding="utf-8", errors="replace")
    entries = collect_entries(text)
    entries_addr = [a for _, a in entries]
    entries_name = [n for n, _ in entries]

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False

    print(f"=== scanning {len(data)} bytes for cmp+branch arms with type tags ===")
    type_tag_set = set(TYPE_TAGS)

    # Find all cmp+conditional branch pairs across the entire binary.
    # Walk with auto-skip (Thumb alignment).
    pos = 0
    end = len(data)
    instrs: list[dict] = []
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

    # Find cmp #imm followed within 2 instr by cond branch
    cmp_arms: list[dict] = []
    bl_sites_to_readers: dict[int, list[int]] = defaultdict(list)  # addr -> list of caller positions
    for i, ins in enumerate(instrs):
        # Track BLs to queue readers (for reader-call-then-cmp identification)
        if ins["mnem"] in ("bl", "blx"):
            tok = ins["op_str"].strip().lstrip("#")
            if tok.startswith("0x"):
                try:
                    t = int(tok, 16)
                    if t in QUEUE_READERS:
                        bl_sites_to_readers[t].append(i)
                except ValueError:
                    pass
        if ins["mnem"] not in ("cmp", "cmn"):
            continue
        parts = [p.strip() for p in ins["op_str"].split(",")]
        if len(parts) < 2 or not parts[1].startswith("#"):
            continue
        try:
            imm = int(parts[1].lstrip("#"), 0)
        except ValueError:
            continue
        if imm not in type_tag_set:
            continue
        # Look ahead 1-2 instr for conditional branch
        for j in range(i + 1, min(i + 3, len(instrs))):
            jn = instrs[j]
            if jn["mnem"] in COND_BRANCH:
                cmp_arms.append({
                    "cmp_addr": ins["addr"],
                    "cmp_reg": parts[0],
                    "imm": imm,
                    "branch_kind": jn["mnem"],
                })
                break
            if jn["mnem"] in ("cmp", "cmn"):
                break

    print(f"\n=== {len(cmp_arms)} cmp+branch sites with type tags ===")

    # Group by enclosing function
    func_arms: defaultdict[str, list[dict]] = defaultdict(list)
    for arm in cmp_arms:
        func = find_enclosing_func(arm["cmp_addr"], entries_addr, entries_name)
        func_arms[func].append(arm)

    # Per-function type tag coverage
    func_summary = []
    for func, arms in func_arms.items():
        tag_counter = Counter(a["imm"] for a in arms)
        func_summary.append({
            "func": func,
            "total_arms": len(arms),
            "distinct_tags": len(tag_counter),
            "tags": dict(tag_counter),
            "first_arm": arms[0]["cmp_addr"],
        })
    func_summary.sort(key=lambda x: (-x["distinct_tags"], -x["total_arms"]))

    print(f"\n=== {len(func_summary)} distinct caller functions ===")
    print(f"top 30 by distinct type tag count (likely dispatcher / reader):")
    print(f"{'rank':<5} {'func':<26} {'arms':<5} {'tags':<5} {'tag_dist':<60}")
    print("-" * 110)
    for i, f in enumerate(func_summary[:30], 1):
        tag_str = ", ".join(f"0x{t:02x}:{c}" for t, c in sorted(f["tags"].items()))
        print(f"{i:<5} {f['func']:<26} {f['total_arms']:<5} {f['distinct_tags']:<5} {tag_str}")

    # Type tag prevalence
    all_tags = Counter()
    for arm in cmp_arms:
        all_tags[arm["imm"]] += 1
    print(f"\n=== type tag prevalence (cmp arm count) ===")
    for tag in TYPE_TAGS:
        c = all_tags.get(tag, 0)
        marker = ""
        if tag == 0x05:
            marker = " ⭐ type-5 (PM-5 dominant)"
        elif tag == 0x00:
            marker = " (null check, not necessarily type tag)"
        print(f"  cmp #0x{tag:02x}: {c} sites{marker}")

    # Functions that call queue readers + have type tag cmp arms (= confirmed readers)
    print(f"\n=== queue reader call sites + nearby type tag cmp ===")
    confirmed_readers = []
    for reader_addr, sites in bl_sites_to_readers.items():
        rname = QUEUE_READERS[reader_addr]
        for site_idx in sites:
            site_ins = instrs[site_idx]
            # Check if there's a cmp #type_tag within 5 instr after the BL (reader returned, now cmp on byte)
            for j in range(site_idx + 1, min(site_idx + 8, len(instrs))):
                if instrs[j]["mnem"] in ("cmp", "cmn"):
                    parts = [p.strip() for p in instrs[j]["op_str"].split(",")]
                    if len(parts) >= 2 and parts[1].startswith("#"):
                        try:
                            imm = int(parts[1].lstrip("#"), 0)
                            if imm in type_tag_set:
                                func = find_enclosing_func(site_ins["addr"], entries_addr, entries_name)
                                confirmed_readers.append({
                                    "site": site_ins["addr"],
                                    "reader": rname,
                                    "cmp_addr": instrs[j]["addr"],
                                    "imm": imm,
                                    "func": func,
                                })
                                break
                        except ValueError:
                            pass

    print(f"  found {len(confirmed_readers)} BL_to_reader → cmp #type_tag patterns")
    for cr in confirmed_readers[:30]:
        print(f"  0x{cr['site']:08x} (in {cr['func']}): bl {cr['reader']} → 0x{cr['cmp_addr']:08x}: cmp #0x{cr['imm']:02x}")

    out = {
        "type_tags_searched": TYPE_TAGS,
        "total_cmp_arm_sites": len(cmp_arms),
        "type_tag_prevalence": {f"0x{t:02x}": all_tags.get(t, 0) for t in TYPE_TAGS},
        "top_functions_by_type_tag": [
            {
                "func": f["func"],
                "total_arms": f["total_arms"],
                "distinct_tags": f["distinct_tags"],
                "tags": {f"0x{t:02x}": c for t, c in f["tags"].items()},
                "first_arm": f"0x{f['first_arm']:08x}",
            }
            for f in func_summary[:50]
        ],
        "confirmed_readers": [
            {
                "site": f"0x{cr['site']:08x}",
                "reader": cr["reader"],
                "cmp_addr": f"0x{cr['cmp_addr']:08x}",
                "imm": cr["imm"],
                "func": cr["func"],
            }
            for cr in confirmed_readers
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
