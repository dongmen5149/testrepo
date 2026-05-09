"""§4.4 mode 2 (FUN_00060ab4) inline literal-pool 추출 + UI 데이터 가설 검증 (자동 분석 2F).

전제 (2026-05-10 재해석):
  state[0x94] 는 3-페이지 UI 탭 인덱스 (mode/battle 아님).
  → FUN_00060ab4 (9KB, 이전 "mode 2") 는 page 2 UI 그리는 함수일 가능성.
  → 그러나 전 작업은 9KB 중 1.5KB 만 code, 7KB 데이터로 잘못 추정 (capstone 이 첫 literal pool 에서 stop).

이번 도구의 목적:
  1. FUN_00060ab4 의 모든 코드 블록 + inline literal pool 분리
  2. PC-rel LDR 가 가리키는 모든 32-bit 리터럴 값을 추출
  3. 리터럴 값을 카테고리별 분류 (small int, GOT slot, PIC offset 등)
  4. 인접 small-int sequence 를 UI 좌표 후보 (x,y,w,h 등) 로 식별
  5. 함수 종료 후 trailing data table (있다면) dump
"""
from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path
from typing import Iterable

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
OUT = REPO / "work" / "h3" / "mode2_ui_data.json"

START = 0x00060AB4
END = 0x00062D1C
GOT_BASE = 0x000B2C40

VENEERS = set(range(0x000A42A0, 0x000A42CE, 2))


def walk_with_skip(data: bytes, start: int, end: int) -> tuple[list[dict], list[tuple[int, int]]]:
    """Disassemble [start,end). When capstone stops, skip 2 bytes and resume.

    Returns (instructions, code_blocks).
      instructions: list of dicts with addr, mnem, op_str, size
      code_blocks: list of (start_addr, end_addr_exclusive) — contiguous decoded ranges
    """
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    instrs: list[dict] = []
    blocks: list[tuple[int, int]] = []
    cur_start = start
    cur_end = start
    pos = start
    while pos < end:
        offset = pos - START + 0  # data offset
        chunk = data[pos:end]
        block_first = pos
        last_addr = pos
        any_emitted = False
        for ins in md.disasm(chunk, pos):
            instrs.append({
                "addr": ins.address,
                "mnem": ins.mnemonic,
                "op_str": ins.op_str,
                "size": ins.size,
                "bytes": bytes(ins.bytes).hex(),
            })
            last_addr = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            blocks.append((block_first, last_addr))
            pos = last_addr
        # Skip 2 bytes (Thumb alignment) and try again
        pos += 2
        if pos > end:
            break
    return instrs, blocks


def categorize_literal(value: int, addr: int) -> str:
    """Classify a 32-bit literal by likely meaning."""
    sv = struct.unpack("<i", struct.pack("<I", value))[0]
    if value == 0:
        return "zero"
    if 1 <= value < 0x80:
        return "small_int"  # coord, count, flag
    if 0x80 <= value < 0x1000:
        return "medium_int"  # tile id, large coord, byte offset
    # PIC GOT-relative offsets are typically small signed ints (e.g., -0x100 to +0x10000)
    if 0x9000 <= value <= 0xC000:
        return "got_slot_offset"  # 0x9c84 etc — GOT slot index
    if 0xA0000 <= value <= 0xB3000:
        return "binary_addr_strings_or_jt"  # 0xaac58 area, jt area
    if value >= 0x60000 and value < 0x70000:
        return "binary_addr_self_function"
    if value >= 0xFFFF0000:
        return "negative_signed_offset"
    if value & 0x80000000:
        return "negative_signed_offset"
    if 0x10000 <= value < 0xA0000:
        return "binary_addr_other_function"
    return f"other_0x{value:x}"


def main() -> None:
    if not BIN.exists():
        print(f"!! binary missing: {BIN}")
        return
    data = bytes(BIN.read_bytes())
    print(f"=== FUN_00060ab4 ({END-START:#x} bytes / {(END-START)/1024:.1f} KB) ===")

    instrs, code_blocks = walk_with_skip(data, START, END)
    print(f"\ncode_blocks: {len(code_blocks)} (auto-detected)")
    total_code_bytes = sum(e - s for s, e in code_blocks)
    print(f"total decoded bytes: {total_code_bytes} ({total_code_bytes/(END-START)*100:.1f}% of region)")

    # Find data gaps between code blocks
    gaps: list[tuple[int, int]] = []
    prev_end = START
    for s, e in code_blocks:
        if s > prev_end:
            gaps.append((prev_end, s))
        prev_end = max(prev_end, e)
    if prev_end < END:
        gaps.append((prev_end, END))
    total_data_bytes = sum(e - s for s, e in gaps)
    print(f"data gaps: {len(gaps)}, total {total_data_bytes} bytes ({total_data_bytes/(END-START)*100:.1f}% of region)")

    print("\n=== code blocks (head 12) ===")
    for s, e in code_blocks[:12]:
        print(f"  0x{s:08x} ~ 0x{e:08x}  ({e-s:4d} bytes)")
    if len(code_blocks) > 12:
        print(f"  ... ({len(code_blocks)-12} more)")

    print("\n=== data gaps (head 12) ===")
    for s, e in gaps[:12]:
        print(f"  0x{s:08x} ~ 0x{e:08x}  ({e-s:4d} bytes)")
    if len(gaps) > 12:
        print(f"  ... ({len(gaps)-12} more)")

    # Collect all PC-rel LDR sites and resolve targets
    pcrel_ldrs: list[dict] = []
    for ins in instrs:
        mnem = ins["mnem"]
        op_str = ins["op_str"]
        addr = ins["addr"]
        if mnem in ("ldr", "ldr.w") and "[pc," in op_str.replace(" ", ""):
            # parse "[pc, #0x60]" or "[pc, #-0x60]"
            try:
                imm_str = op_str.split("#", 1)[1].rstrip(" ]")
                imm = int(imm_str, 0)
            except (IndexError, ValueError):
                continue
            # Thumb PC-rel: target = (PC & ~3) + imm, where PC = addr+4
            pc = (addr + 4) & ~3
            target = pc + imm
            if 0 <= target < len(data) - 4:
                value = struct.unpack("<I", data[target:target+4])[0]
                pcrel_ldrs.append({
                    "site": addr,
                    "target": target,
                    "value": value,
                    "category": categorize_literal(value, target),
                })

    print(f"\n=== PC-rel LDR resolved: {len(pcrel_ldrs)} sites ===")
    cat_counter = Counter(p["category"] for p in pcrel_ldrs)
    for cat, count in cat_counter.most_common():
        print(f"  {cat:36s}: {count}")

    # Show first 40 resolved LDRs
    print("\n=== top resolved literals (head 40) ===")
    for p in pcrel_ldrs[:40]:
        v = p["value"]
        sv = struct.unpack("<i", struct.pack("<I", v))[0]
        print(f"  ldr@0x{p['site']:08x} → [0x{p['target']:08x}] = 0x{v:08x} ({sv:11d}) [{p['category']}]")

    # Now scan EACH data gap as 4-byte aligned literals
    print("\n=== data gap literal dump (all gaps, 4-byte words) ===")
    gap_literals: list[dict] = []
    for s, e in gaps:
        # Align s up to 4-byte
        gs = (s + 3) & ~3
        ge = e & ~3
        if ge - gs < 4:
            continue
        words: list[dict] = []
        for off in range(gs, ge, 4):
            v = struct.unpack("<I", data[off:off+4])[0]
            sv = struct.unpack("<i", data[off:off+4])[0]
            words.append({
                "off": off,
                "value": v,
                "signed": sv,
                "category": categorize_literal(v, off),
            })
        gap_literals.append({
            "start": gs,
            "end": ge,
            "words": words,
        })

    # Print each gap's literal sequence
    for gl in gap_literals[:20]:
        s, e = gl["start"], gl["end"]
        words = gl["words"]
        print(f"  gap 0x{s:08x}~0x{e:08x} ({len(words)} words):")
        for w in words[:8]:
            print(f"    [0x{w['off']:08x}] 0x{w['value']:08x} ({w['signed']:11d}) [{w['category']}]")
        if len(words) > 8:
            print(f"    ... ({len(words)-8} more)")
    if len(gap_literals) > 20:
        print(f"  ... ({len(gap_literals)-20} more gaps)")

    # Pattern detection: look for "mostly small_int / medium_int" gaps that could be UI tables
    print("\n=== UI table candidates (gap with ≥4 small/medium literals) ===")
    ui_tables: list[dict] = []
    for gl in gap_literals:
        if len(gl["words"]) < 4:
            continue
        small_count = sum(1 for w in gl["words"] if w["category"] in ("small_int", "medium_int", "zero"))
        if small_count / len(gl["words"]) >= 0.7:
            ui_tables.append({
                "start": gl["start"],
                "end": gl["end"],
                "word_count": len(gl["words"]),
                "small_pct": small_count / len(gl["words"]),
            })
    for ut in ui_tables[:30]:
        print(f"  0x{ut['start']:08x}~0x{ut['end']:08x}  {ut['word_count']:3d} words  small_pct={ut['small_pct']:.0%}")

    # BL targets
    print("\n=== BL targets (non-veneer) ===")
    bl_targets = []
    for ins in instrs:
        if ins["mnem"] in ("bl", "blx"):
            tok = ins["op_str"].strip().lstrip("#")
            if tok.startswith("0x"):
                try:
                    bl_targets.append(int(tok, 16))
                except ValueError:
                    pass
    bl_freq = Counter(bl_targets)
    for tgt, c in bl_freq.most_common(20):
        v_marker = " (veneer)" if tgt in VENEERS else ""
        print(f"  0x{tgt:08x}: {c}{v_marker}")

    # cmp Rn, #imm distribution
    cmp_imms = Counter()
    for ins in instrs:
        if ins["mnem"] in ("cmp", "cmn"):
            for tok in ins["op_str"].split(","):
                tok = tok.strip()
                if tok.startswith("#"):
                    try:
                        v = int(tok[1:], 0)
                        if 0 <= v < 0x200:
                            cmp_imms[v] += 1
                    except ValueError:
                        pass
    print("\n=== cmp Rn, #imm dist (switch detection) ===")
    for v, c in cmp_imms.most_common(15):
        print(f"  cmp #0x{v:02x}: {c}")

    # Save JSON output
    out = {
        "function": "FUN_00060ab4",
        "addr_start": f"0x{START:08x}",
        "addr_end": f"0x{END:08x}",
        "size_bytes": END - START,
        "instr_count": len(instrs),
        "code_blocks": [
            {"start": f"0x{s:08x}", "end": f"0x{e:08x}", "size": e - s}
            for s, e in code_blocks
        ],
        "data_gaps": [
            {"start": f"0x{s:08x}", "end": f"0x{e:08x}", "size": e - s}
            for s, e in gaps
        ],
        "total_code_bytes": total_code_bytes,
        "total_data_bytes": total_data_bytes,
        "pcrel_ldr_resolved": [
            {
                "site": f"0x{p['site']:08x}",
                "target": f"0x{p['target']:08x}",
                "value": f"0x{p['value']:08x}",
                "category": p["category"],
            }
            for p in pcrel_ldrs
        ],
        "literal_categories": dict(cat_counter),
        "data_gap_literals": [
            {
                "start": f"0x{gl['start']:08x}",
                "end": f"0x{gl['end']:08x}",
                "words": [
                    {
                        "off": f"0x{w['off']:08x}",
                        "value": f"0x{w['value']:08x}",
                        "signed": w["signed"],
                        "category": w["category"],
                    }
                    for w in gl["words"]
                ],
            }
            for gl in gap_literals
        ],
        "ui_table_candidates": [
            {
                "start": f"0x{ut['start']:08x}",
                "end": f"0x{ut['end']:08x}",
                "word_count": ut["word_count"],
                "small_pct": round(ut["small_pct"], 3),
            }
            for ut in ui_tables
        ],
        "bl_targets_top": [
            {"target": f"0x{t:08x}", "count": c, "is_veneer": t in VENEERS}
            for t, c in bl_freq.most_common(40)
        ],
        "cmp_imm_dist": [{"imm": v, "count": c} for v, c in cmp_imms.most_common(30)],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
