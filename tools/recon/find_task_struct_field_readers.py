"""task_struct field reader 매핑 — Round 24 (2AZ).

배경 (Round 23 발견):
  Round 18~22 의 "GOT slot" 분류 다수가 사실 task_struct 필드 offset.
  진짜 GOT slot 은 8개 (0x18/0x16c/0x444/0x44c/0xd00/0x128/0xd04/0xd08).
  나머지 11+ "슬롯" 은 task_struct 안의 필드.

전략:
  binary 전체 capstone 디스어셈블 → 다음 패턴 검색:
    1. `bl 0x4ad10`  (context_getter)
    2. 직후 8 instr 안에 `ldr Rx, [pc, #imm]` (lit value = field_offset)
    3. 그 다음 `adds Ry, Rz, Rx` 또는 `adds Rx, R0, ...` (= ctx + field_offset)

각 field offset 에 대해:
  - reader 함수 (FUN_xxx) 분포
  - 사용 빈도
  - post-access 패턴 (ldr → byte/word, single/double indir, store/load)
  - 인접 field 클러스터링

기본 검색 offsets (지금까지 발견):
  0x29e, 0x9bb4, 0x9c70, 0x9c71, 0x9c84, 0x9cbc, 0x9cc0, 0x9cfe,
  0x9e28, 0x9e78, 0xa220, 0xa244, 0xa245, 0xa254, 0xac78
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
DECOMPILED = REPO / "work" / "ghidra_out" / "all_decompiled.c"

CONTEXT_GETTER = 0x0004AD10

# Known task_struct field offsets (Round 18~28 verified)
KNOWN_FIELDS = [
    0x29e,
    0x9afc, 0x9b01, 0x9b14, 0x9b1c,  # Round 25 신규 cluster #1
    0x9bb4, 0x9bb6, 0x9bb7, 0x9bc8,  # Round 25 bit flag substructure
    0x9bd0,                            # Round 25 ptr-to-object
    0x9c70, 0x9c71, 0x9c84, 0x9c85,   # Round 25 정정: 4개 인접 byte fields
    0x9cb8, 0x9cbc, 0x9cc0, 0x9cfe,   # record array slots
    0x9e28, 0x9e78,
    0xa220, 0xa244, 0xa245, 0xa254,
    # Round 28: 38B entity state record cluster (0xac78~0xac9d)
    0xac78, 0xac79, 0xac7a, 0xac7c,
    0xac80, 0xac84,
    0xac90, 0xac92, 0xac94, 0xac98, 0xac9c, 0xac9d,
]

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
        out.append((int(m.group(2), 16), name))
    out.sort()
    return [a for a, _ in out], [n for _, n in out]


def find_func(addr: int, addrs, names) -> str:
    idx = bisect.bisect_right(addrs, addr) - 1
    return names[idx] if idx >= 0 else "?"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--field", type=lambda x: int(x, 0), default=None,
                        help="single field offset to analyze (default: all known)")
    args = parser.parse_args()

    fields = [args.field] if args.field is not None else KNOWN_FIELDS

    print(f"=== scanning binary for task_struct field readers ===")
    print(f"=== fields: {[hex(f) for f in fields]} ===")

    data = BIN.read_bytes()
    text = DECOMPILED.read_text(encoding="utf-8", errors="replace")
    addrs, names = collect_entries(text)
    print(f"=== {len(addrs)} decompiled function entries ===")

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False

    print(f"=== walking {len(data)} bytes (Thumb auto-skip) ===")
    instrs: list[dict] = []
    pos = 0
    end = len(data)
    while pos < end:
        chunk = data[pos:end]
        any_emit = False
        last = pos
        for ins in md.disasm(chunk, pos):
            instrs.append({
                "addr": ins.address, "mnem": ins.mnemonic,
                "op_str": ins.op_str, "size": ins.size,
            })
            last = ins.address + ins.size
            any_emit = True
        if any_emit:
            pos = last
        pos += 2
    print(f"=== {len(instrs)} instructions disassembled ===")

    # 1. Find all `bl 0x4ad10` BL sites
    ctx_bl_target = f"#0x{CONTEXT_GETTER:x}"
    ctx_calls: list[int] = []
    for i, ins in enumerate(instrs):
        if ins["mnem"] == "bl" and ctx_bl_target in ins["op_str"]:
            ctx_calls.append(i)
    print(f"=== {len(ctx_calls)} context_getter BL sites ===")

    # 2. For each ctx call, track R0 propagation forward up to 16 instr.
    #    R0 may be saved to other registers via:
    #      - adds rZ, r0, #0      (save with flags)
    #      - mov rZ, r0           (plain move)
    #      - mov.w rZ, r0
    #    Then field access via:
    #      - ldr Rx, [pc, #imm]   (lit==field_offset)
    #      - adds Ry, <R0-equiv>, Rx   (or commuted)
    #
    # Also captures R0 reuse before save (common case: register r0 stays r0 directly).
    field_hits: dict[int, list[dict]] = defaultdict(list)

    SAVE_MNEM = {"adds", "add", "add.w", "mov", "mov.w", "movs"}

    def is_r0_save(parts: list[str], src_regs: set[str]) -> str | None:
        """Detect 'rZ <- r0-equivalent' patterns. Returns destination reg or None."""
        if len(parts) < 2:
            return None
        dst = parts[0]
        # mov rZ, rX  (where rX in src_regs)
        if len(parts) == 2 and parts[1] in src_regs:
            return dst
        # adds rZ, rX, #0  (move with flags)
        if len(parts) == 3 and parts[1] in src_regs and parts[2] == "#0":
            return dst
        # adds rZ, #0  (in-place, doesn't help)  -- skip
        return None

    for ctx_idx in ctx_calls:
        ctx_addr = instrs[ctx_idx]["addr"]
        # Track which registers currently hold the task_ptr value (R0 equivalent set)
        r0_equiv = {"r0"}
        ldr_target = None  # (idx, rd, lit_value)

        for fwd in range(1, 17):
            j = ctx_idx + fwd
            if j >= len(instrs):
                break
            ins = instrs[j]
            mnem = ins["mnem"]
            op_str = ins["op_str"]
            parts = [p.strip() for p in op_str.split(",")]

            # Stop if any branch instruction (non-conditional or conditional)
            if mnem.startswith("b") and mnem not in ("bic", "bics"):
                break

            # Track R0-propagation: save to other reg
            if mnem in SAVE_MNEM:
                saved_dst = is_r0_save(parts, r0_equiv)
                if saved_dst:
                    r0_equiv.add(saved_dst)

            # Check for ldr Rx, [pc, #imm]  (loading literal pool)
            if mnem in ("ldr", "ldr.w") and "[pc," in op_str.replace(" ", ""):
                try:
                    imm = int(op_str.split("#")[1].rstrip("]"), 0)
                    pc_aligned = (ins["addr"] + 4) & ~3
                    lit_addr = pc_aligned + imm
                    if 0 <= lit_addr + 4 <= len(data):
                        val = struct.unpack("<I", data[lit_addr:lit_addr + 4])[0]
                        if val in fields:
                            rd = parts[0]
                            ldr_target = (j, rd, val)
                except (IndexError, ValueError):
                    pass

            # Check for adds/add Ry, <R0-equiv>, Rx  (field access)
            if ldr_target is not None:
                ldr_idx, ldr_rd, lit_val = ldr_target
                if mnem in ("adds", "add", "add.w") and ldr_idx < j and len(parts) >= 3:
                    second = parts[1]
                    third = parts[2]
                    # Match: adds rY, <R0-equiv>, rLDR  OR  adds rY, rLDR, <R0-equiv>
                    matches = (
                        (second in r0_equiv and third == ldr_rd) or
                        (third in r0_equiv and second == ldr_rd)
                    )
                    if matches:
                        field_hits[lit_val].append({
                            "ctx_addr": ctx_addr,
                            "ldr_addr": instrs[ldr_idx]["addr"],
                            "add_addr": ins["addr"],
                            "r0_via": "direct" if "r0" in (second, third) else f"saved:{second if second in r0_equiv else third}",
                            "post_pattern": instrs[j+1]["mnem"] + " " + instrs[j+1]["op_str"] if j+1 < len(instrs) else "?",
                        })
                        ldr_target = None
                        break

    # 3. Map to enclosing functions
    print(f"\n=== task_struct field reader summary ===\n")
    summary = {}
    for field in sorted(fields):
        hits = field_hits.get(field, [])
        func_count: dict[str, int] = defaultdict(int)
        for h in hits:
            func_count[find_func(h["ctx_addr"], addrs, names)] += 1

        print(f"  field 0x{field:x} ({field:>5}): {len(hits)} verified ctx+field sites in {len(func_count)} unique funcs")
        if hits[:5]:
            for h in hits[:3]:
                f = find_func(h["ctx_addr"], addrs, names)
                print(f"    e.g. ctx@0x{h['ctx_addr']:08x} (in {f}) → ldr@0x{h['ldr_addr']:08x} → add@0x{h['add_addr']:08x}  next: {h['post_pattern']}")
        # top funcs
        if func_count:
            top_funcs = sorted(func_count.items(), key=lambda x: -x[1])[:5]
            print(f"    top readers: {', '.join(f'{f}({c}x)' for f, c in top_funcs)}")

        summary[hex(field)] = {
            "verified_sites": len(hits),
            "unique_funcs": len(func_count),
            "top_readers": dict(sorted(func_count.items(), key=lambda x: -x[1])[:10]),
            "first_sites": [{"ctx_addr": f"0x{h['ctx_addr']:08x}",
                             "ldr_addr": f"0x{h['ldr_addr']:08x}",
                             "r0_via": h.get("r0_via", "?"),
                             "add_addr": f"0x{h['add_addr']:08x}",
                             "func": find_func(h["ctx_addr"], addrs, names),
                             "post_pattern": h["post_pattern"]} for h in hits[:8]],
        }

    out_path = REPO / "work" / "h3" / "task_struct_field_readers.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nsaved: {out_path}")


if __name__ == "__main__":
    main()
