"""§4.4 후속 — top PIC stub 함수 일괄 분석 (자동 분석 2I 후속).

배경 (2026-05-10 PM-3 후속):
  rank_pic_stubs.py 로 402 stub 우선순위 ranking. 가장 가치 있는 함수 후보
  (high callers / high BL / queue caller) 를 capstone walk_with_skip 으로
  본문 분석.

이번 도구의 목적:
  1. 사전 정의된 TARGETS 리스트의 각 함수 본문 디스어셈블 (auto-skip)
  2. 각 함수의 시그니처 추출:
     - code_blocks / instr_count / size
     - BL 통계 (top callees, veneer ratio)
     - cmp #imm 분포 (state machine / dispatcher 식별)
     - state offset access 패턴 (str/ldr [Rn, #imm])
     - PC-rel LDR top literals + 카테고리
     - GVM 큐 API 호출 여부
  3. 함수별 카테고리 자동 추정:
     - state_machine (cmp 분포 풍부)
     - heavy_dispatcher (BL 매우 많음 + 다양한 target)
     - queue_writer (0x7e150 / 0x7e1c4 호출)
     - queue_reader (0x7e184 호출)
     - drawing_loop (drawText/drawSprite 패턴)
     - sequential (특별 패턴 없이 순차)
"""
from __future__ import annotations

import json
import re
import struct
from collections import Counter
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
DECOMPILED = REPO / "work" / "ghidra_out" / "all_decompiled.c"
OUT = REPO / "work" / "h3" / "top_stubs_analysis.json"

VENEERS = set(range(0x000A42A0, 0x000A42CE, 2))

# Known queue/io API addresses
QUEUE_FUNCS = {
    0x0007e150: "byte_append",
    0x0007e184: "memcpy_read",
    0x0007e1c4: "u32_append",
    0x0007e204: "u32_write_indirect",
    0x0007e890: "flush_swap",
    0x0007e7ac: "init_or_helper",
    0x0007e0e4: "alloc_buffer",
    0x0007ea98: "buffer_status",
    0x0007e63c: "consumer_?",
    0x0007e4c4: "set_byte",
}

# Known UI helpers (from 2026-05-09 PM-3 + 2026-05-10 PM-2)
UI_HELPERS = {
    0x0000d53c: "screen_ptr_getter",
    0x0003ecfc: "draw_text_sprite",
    0x00099764: "sound_trigger",
    0x0000defc: "draw_rect",
    0x0009f624: "graphics_primitive",
    0x0009fb78: "memset_like",
    0x0009f82c: "?_helper",
    0x0000ec80: "?_helper",
}

# Top stub candidates to analyze (from rank_pic_stubs.py + find_queue_callers.py results)
TARGETS = [
    # rank, addr, name, hint
    (1, 0x000818f0, "FUN_000818f0", "biggest dense (287 BLs / 5.4KB)"),
    (2, 0x00075b98, "FUN_00075b98", "most-called helper (58 callers / 324 bytes)"),
    (3, 0x0003d5d0, "FUN_0003d5d0", "popular major (37 callers / 4.3KB / 99 BLs)"),
    (4, 0x00026a80, "FUN_00026a80", "huge (8.4KB / 209 BLs)"),
    (5, 0x00006334, "FUN_00006334", "largest (10KB / 187 BLs)"),
    (6, 0x00040ea0, "FUN_00040ea0", "tiny popular (38 callers / 68 bytes)"),
    (7, 0x000439a0, "FUN_000439a0", "popular helper (37 callers / 188 bytes)"),
    (8, 0x0008578c, "FUN_0008578c", "tiny dispatcher (34 callers / 24 bytes)"),
    (9, 0x00040ddc, "FUN_00040ddc", "tiny popular (32 callers / 32 bytes)"),
    (10, 0x00057394, "FUN_00057394", "QUEUE LIFECYCLE OWNER (29 q-calls)"),
    (11, 0x00056bf8, "FUN_00056bf8", "queue user (18 q-calls)"),
    (12, 0x000630e8, "FUN_000630e8", "queue user (14 q-calls / 3.9KB)"),
    (13, 0x0001f1e4, "FUN_0001f1e4", "huge dense (5.4KB / 136 BLs)"),
    (14, 0x000031dc, "FUN_000031dc", "huge dense (6.7KB / 131 BLs)"),
    (15, 0x0003add0, "FUN_0003add0", "0 callers (PIC-only) (3.1KB / 137 BLs)"),
]


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


def walk_with_skip(data: bytes, start: int, end: int) -> tuple[list[dict], list[tuple[int, int]]]:
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    instrs: list[dict] = []
    blocks: list[tuple[int, int]] = []
    pos = start
    while pos < end:
        chunk = data[pos:end]
        any_emitted = False
        last = pos
        block_first = pos
        for ins in md.disasm(chunk, pos):
            instrs.append({
                "addr": ins.address, "mnem": ins.mnemonic, "op_str": ins.op_str, "size": ins.size,
            })
            last = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            blocks.append((block_first, last))
            pos = last
        pos += 2
        if pos > end:
            break
    return instrs, blocks


def analyze_func(data: bytes, addr: int, end: int) -> dict:
    instrs, blocks = walk_with_skip(data, addr, end)
    total_code = sum(e - s for s, e in blocks)

    bl_targets = []
    cmp_imms = Counter()
    pcrel_lits = []
    state_writes = Counter()
    state_reads = Counter()
    queue_calls = Counter()
    ui_calls = Counter()
    veneer_calls = 0

    for ins in instrs:
        mnem = ins["mnem"]
        op_str = ins["op_str"]
        if mnem in ("bl", "blx"):
            tok = op_str.strip().lstrip("#")
            if tok.startswith("0x"):
                try:
                    t = int(tok, 16)
                    bl_targets.append(t)
                    if t in VENEERS:
                        veneer_calls += 1
                    if t in QUEUE_FUNCS:
                        queue_calls[QUEUE_FUNCS[t]] += 1
                    if t in UI_HELPERS:
                        ui_calls[UI_HELPERS[t]] += 1
                except ValueError:
                    pass
        if mnem in ("cmp", "cmn"):
            for tok in op_str.split(","):
                tok = tok.strip()
                if tok.startswith("#"):
                    try:
                        v = int(tok[1:], 0)
                        if -0x100 < v < 0x200:
                            cmp_imms[v] += 1
                    except ValueError:
                        pass
        if mnem in ("ldr", "ldr.w") and "[pc," in op_str.replace(" ", ""):
            try:
                imm = int(op_str.split("#", 1)[1].rstrip(" ]"), 0)
                pc = (ins["addr"] + 4) & ~3
                target = pc + imm
                if 0 <= target < len(data) - 4:
                    v = struct.unpack("<I", data[target:target+4])[0]
                    pcrel_lits.append(v)
            except (IndexError, ValueError):
                pass
        # state writes/reads: parse "Rt, [Rn, #imm]" (skip pc-rel)
        if "[" in op_str and "#" in op_str and "pc" not in op_str:
            try:
                _, mem_part = op_str.split(",", 1)
                mem_part = mem_part.strip()
                if not mem_part.startswith("["):
                    continue
                inside = mem_part.strip("[]").strip()
                if "#" not in inside:
                    continue
                _, off = inside.split(",", 1)
                off = off.strip().rstrip("]")
                if not off.startswith("#"):
                    continue
                imm = int(off[1:], 0)
                if mnem in ("str", "strb", "strh", "str.w", "strb.w", "strh.w"):
                    state_writes[imm] += 1
                elif mnem in ("ldr", "ldrb", "ldrh", "ldr.w", "ldrb.w", "ldrh.w"):
                    state_reads[imm] += 1
            except (ValueError, IndexError):
                pass

    bl_freq = Counter(bl_targets)
    distinct_cmp = len([v for v in cmp_imms.values() if v >= 1])
    cmp_total = sum(cmp_imms.values())
    distinct_cmp_arms = len([v for v in cmp_imms if 0 < v < 0x100])  # state arm candidates

    # Heuristic categorization
    categories = []
    if queue_calls:
        if queue_calls.get("byte_append", 0) + queue_calls.get("u32_append", 0) >= 3:
            categories.append("queue_writer")
        if queue_calls.get("memcpy_read", 0) >= 2:
            categories.append("queue_reader")
        if queue_calls.get("flush_swap", 0) >= 2:
            categories.append("queue_lifecycle")
    if ui_calls.get("draw_text_sprite", 0) + ui_calls.get("draw_rect", 0) >= 5:
        categories.append("drawing_heavy")
    if distinct_cmp_arms >= 5 and cmp_total >= 10:
        categories.append("state_machine_or_dispatcher")
    if len(bl_freq) >= 30:
        categories.append("subsystem_router")
    if not categories:
        categories.append("sequential")

    return {
        "addr": f"0x{addr:08x}",
        "size_bytes": end - addr,
        "code_blocks": len(blocks),
        "total_code_bytes": total_code,
        "instr_count": len(instrs),
        "bl_total": len(bl_targets),
        "bl_distinct": len(bl_freq),
        "veneer_calls": veneer_calls,
        "bl_top": [
            {"target": f"0x{t:08x}", "count": c, "is_veneer": t in VENEERS,
             "label": QUEUE_FUNCS.get(t, UI_HELPERS.get(t))}
            for t, c in bl_freq.most_common(10)
        ],
        "queue_calls": dict(queue_calls),
        "ui_calls": dict(ui_calls),
        "cmp_total": cmp_total,
        "cmp_distinct": distinct_cmp,
        "cmp_distinct_arms_1to255": distinct_cmp_arms,
        "cmp_top": [{"imm": v, "count": c} for v, c in cmp_imms.most_common(10)],
        "state_write_top": [{"offset": f"0x{o:03x}", "count": c} for o, c in state_writes.most_common(10)],
        "state_read_top": [{"offset": f"0x{o:03x}", "count": c} for o, c in state_reads.most_common(10)],
        "categories": categories,
    }


def main() -> None:
    if not BIN.exists() or not DECOMPILED.exists():
        print("!! input missing")
        return
    data = BIN.read_bytes()
    text = DECOMPILED.read_text(encoding="utf-8", errors="replace")
    entries = collect_entries(text)
    addrs_sorted = [a for _, a in entries]

    results = []
    for rank, addr, name, hint in TARGETS:
        # Find next entry
        idx = next((i for i, a in enumerate(addrs_sorted) if a == addr), None)
        if idx is None:
            print(f"!! {name} @ 0x{addr:08x} not in entries")
            continue
        end = addrs_sorted[idx + 1] if idx + 1 < len(addrs_sorted) else len(data)
        if end - addr > 0x4000:
            print(f"!! {name} size capped from {end-addr:#x} to 0x4000")
            end = addr + 0x4000
        info = analyze_func(data, addr, end)
        info["rank"] = rank
        info["name"] = name
        info["hint"] = hint
        results.append(info)
        # Print summary
        cats = "/".join(info["categories"])
        bl_top_str = ", ".join(f"0x{int(b['target'],16):x}({b['count']})" + (f"[{b['label']}]" if b['label'] else "") for b in info["bl_top"][:5])
        print(f"\n#{rank} {name} ({hint})")
        print(f"  size={info['size_bytes']:>5} code={info['total_code_bytes']:>5} instr={info['instr_count']:>4} BL={info['bl_total']}/{info['bl_distinct']}d veneer={info['veneer_calls']}")
        print(f"  cmp: total={info['cmp_total']} distinct={info['cmp_distinct']} arms={info['cmp_distinct_arms_1to255']}")
        if info["queue_calls"]:
            print(f"  queue: {info['queue_calls']}")
        if info["ui_calls"]:
            print(f"  ui: {info['ui_calls']}")
        print(f"  top BL: {bl_top_str}")
        print(f"  state writes top: {info['state_write_top'][:5]}")
        print(f"  state reads top:  {info['state_read_top'][:5]}")
        print(f"  categories: {cats}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\n=== saved {len(results)} stub analyses to {OUT} ===")


if __name__ == "__main__":
    main()
