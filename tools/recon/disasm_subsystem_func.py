"""§4.4 후속 — 핵심 subsystem 함수 본문 디스어셈블 + 패턴 추출 (자동 분석 2K/2L/2M).

사용:
  python tools/recon/disasm_subsystem_func.py <addr_hex> [end_hex] [--label NAME]

예시:
  python tools/recon/disasm_subsystem_func.py 0x57394 0x58172 --label render_buffer    # 2K
  python tools/recon/disasm_subsystem_func.py 0x06334 0x08aca --label main_dispatcher  # 2L
  python tools/recon/disasm_subsystem_func.py 0x3d5d0 0x3e690 --label sound_dispatcher # 2M

출력:
  1. capstone walk_with_skip 으로 전체 본문 디스어셈블
  2. cmp #imm + 조건 분기 → "switch arm" 추출 (각 arm 의 시작 주소 + 그 arm 안에서 호출하는 BL)
  3. 흥미 BL target (byte_append / u32_append / sound_trigger 등) 의 인자 backtrace:
     - BL 직전 ~3 instr 안에서 r0 ~ r3 셋업 명령 검색
     - movs/mov #imm → 즉시값 추출
     - movs Rd, Rs → 다른 레지스터로부터의 값 (해석 보류)
  4. PC-rel LDR target 값 카테고리화
  5. JSON dump → work/h3/<label>_disasm.json
"""
from __future__ import annotations

import argparse
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"

VENEERS = set(range(0x000A42A0, 0x000A42CE, 2))

# Known interesting BL targets — for arg backtrace
TARGETS_OF_INTEREST = {
    0x0007e150: "byte_append",
    0x0007e184: "memcpy_read",
    0x0007e1c4: "u32_append",
    0x0007e204: "u32_write_indirect",
    0x0007e890: "flush_swap",
    0x0007e7ac: "init_or_helper",
    0x0007e0e4: "alloc_buffer",
    0x0007e4c4: "set_byte",
    0x0007e63c: "consumer_?",
    0x00099764: "sound_trigger",
    0x0003ecfc: "draw_text_sprite",
    0x0000d53c: "screen_ptr_getter",
    0x0000defc: "draw_rect",
    0x0009f624: "graphics_primitive",
    0x0009fb78: "memset_like",
    0x0004ad10: "context_getter",
    0x0009fd64: "?_helper_9fd64",
}

# Conditional branches — for cmp+branch arm detection
COND_BRANCH = {"beq", "bne", "blt", "ble", "bgt", "bge", "bcs", "bcc", "bls", "bhi", "bmi", "bpl", "bvs", "bvc"}


def walk_with_skip(data: bytes, start: int, end: int) -> list[dict]:
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False
    instrs = []
    pos = start
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
        if pos > end:
            break
    return instrs


def parse_imm(tok: str) -> int | None:
    tok = tok.strip().lstrip("#")
    try:
        return int(tok, 0)
    except ValueError:
        return None


def normalize_reg(r: str) -> str:
    """Normalize ARM register aliases (sb/sl/fp/ip/sp/lr/pc) to rN form."""
    aliases = {
        "sb": "r9", "sl": "r10", "fp": "r11", "ip": "r12",
        "sp": "r13", "lr": "r14", "pc": "r15",
    }
    return aliases.get(r, r)


def track_reg_value(instrs: list[dict], idx: int, target_reg: str,
                     depth: int = 15, visited: set | None = None) -> dict:
    """Walk back from instrs[idx-1] looking for target_reg's source.

    Recursive register propagation. Supports:
      - mov Rd, #imm           → immediate
      - mov Rd, Rs             → chain to Rs
      - ldr Rd, [pc, #imm]     → PC-rel literal
      - movw Rd, #imm          → Thumb-2 16-bit literal
      - adds Rd, Rs, #imm      → chain + offset
      - adds/subs Rd, #imm     → self-modify (chain prior Rd value)
      - lsls Rd, Rs, #imm      → shift

    Returns dict with: imm, pcrel_addr, src_chain (list of {addr, mnem, op_str}), unresolved_reason
    """
    if visited is None:
        visited = set()
    target_reg = normalize_reg(target_reg)
    state_key = (idx, target_reg, depth)
    if state_key in visited:
        return {"imm": None, "unresolved_reason": "cycle", "src_chain": []}
    visited.add(state_key)
    if depth <= 0:
        return {"imm": None, "unresolved_reason": "depth_exceeded", "src_chain": []}

    chain: list[dict] = []
    for j in range(idx - 1, -1, -1):
        ins = instrs[j]
        mnem = ins["mnem"]
        op_str = ins["op_str"].replace(" ", "")
        parts = op_str.split(",")
        if not parts:
            continue
        rd = normalize_reg(parts[0])
        # If this instr does not write target_reg, skip
        # Heuristic: most write instructions have Rd as first operand.
        if rd != target_reg:
            continue

        step = {"addr": ins["addr"], "mnem": mnem, "op_str": ins["op_str"]}
        chain.append(step)

        # mov Rd, #imm   |  movs Rd, #imm  |  mov.w Rd, #imm  |  movw Rd, #imm
        if mnem in ("mov", "movs", "mov.w", "movw") and len(parts) >= 2 and parts[1].startswith("#"):
            imm = parse_imm(parts[1])
            return {"imm": imm, "src_chain": chain}

        # mov Rd, Rs (single src reg)
        if mnem in ("mov", "movs", "mov.w") and len(parts) == 2 and parts[1].startswith("r") and not parts[1].startswith("r,"):
            src = parts[1]
            sub = track_reg_value(instrs, j, src, depth - 1, visited)
            sub["src_chain"] = chain + sub.get("src_chain", [])
            return sub

        # ldr Rd, [pc, #imm]   (literal pool)
        if mnem in ("ldr", "ldr.w") and "[pc,#" in op_str:
            try:
                imm = parse_imm(op_str.split("#", 1)[1].rstrip("]"))
                pc = (ins["addr"] + 4) & ~3
                return {"pcrel_addr": pc + imm, "src_chain": chain}
            except (IndexError, ValueError):
                return {"imm": None, "src_chain": chain, "unresolved_reason": "ldr_pcrel_parse_fail"}

        # ldr Rd, [Rn, #imm]  or  ldrb/ldrh — value comes from memory
        if mnem in ("ldr", "ldrb", "ldrh", "ldr.w", "ldrb.w", "ldrh.w") and "[" in op_str:
            return {"imm": None, "src_chain": chain, "unresolved_reason": f"mem_load:{op_str}"}

        # adds Rd, Rs, #imm  (3-arg form)
        if mnem in ("adds", "add") and len(parts) == 3 and parts[2].startswith("#"):
            offset = parse_imm(parts[2])
            sub = track_reg_value(instrs, j, parts[1], depth - 1, visited)
            if sub.get("imm") is not None and offset is not None:
                sub["imm"] = sub["imm"] + offset
            sub["src_chain"] = chain + sub.get("src_chain", [])
            return sub

        # adds Rd, #imm  (2-arg, Rd self-modify)
        if mnem in ("adds", "subs") and len(parts) == 2 and parts[1].startswith("#"):
            offset = parse_imm(parts[1])
            sub = track_reg_value(instrs, j, target_reg, depth - 1, visited)
            if sub.get("imm") is not None and offset is not None:
                if mnem == "adds":
                    sub["imm"] += offset
                else:
                    sub["imm"] -= offset
            sub["src_chain"] = chain + sub.get("src_chain", [])
            return sub

        # lsls Rd, Rs, #imm  (logical left shift)
        if mnem == "lsls" and len(parts) == 3 and parts[2].startswith("#"):
            shift = parse_imm(parts[2])
            sub = track_reg_value(instrs, j, parts[1], depth - 1, visited)
            if sub.get("imm") is not None and shift is not None:
                sub["imm"] = (sub["imm"] << shift) & 0xFFFFFFFF
            sub["src_chain"] = chain + sub.get("src_chain", [])
            return sub

        # asrs/lsrs Rd, Rs, #imm
        if mnem in ("asrs", "lsrs") and len(parts) == 3 and parts[2].startswith("#"):
            shift = parse_imm(parts[2])
            sub = track_reg_value(instrs, j, parts[1], depth - 1, visited)
            if sub.get("imm") is not None and shift is not None:
                if mnem == "asrs":
                    # arithmetic shift — preserve sign
                    val = sub["imm"]
                    if val & 0x80000000:
                        val = val - 0x100000000
                    sub["imm"] = (val >> shift) & 0xFFFFFFFF
                else:
                    sub["imm"] = (sub["imm"] >> shift) & 0xFFFFFFFF
            sub["src_chain"] = chain + sub.get("src_chain", [])
            return sub

        # adds Rd, Rs, Rt  — value depends on two regs, give up tracking sum
        # Other unknown writers — return chain so caller can see context
        return {"imm": None, "src_chain": chain, "unresolved_reason": f"unsupported:{mnem} {ins['op_str']}"}

    return {"imm": None, "src_chain": chain, "unresolved_reason": "no_writer_found"}


def backtrace_r0(instrs: list[dict], idx: int, lookback: int = 15) -> dict:
    """Backtrace r0 via strengthened register propagation (kept name for back-compat)."""
    sub = track_reg_value(instrs, idx, "r0", depth=lookback)
    info = {"r0_imm": sub.get("imm"), "r0_src_reg": None, "r0_src_addr": None,
            "r0_pcrel": sub.get("pcrel_addr"), "r0_unresolved": sub.get("unresolved_reason"),
            "r0_chain_len": len(sub.get("src_chain", []))}
    if sub.get("src_chain"):
        info["r0_src_addr"] = sub["src_chain"][0]["addr"]
    if sub.get("unresolved_reason") and sub.get("unresolved_reason").startswith("unsupported"):
        info["r0_src_reg"] = "?other"
    return info


def backtrace_args(instrs: list[dict], idx: int, lookback: int = 15) -> dict:
    """Backtrace r0..r3 (ARM AAPCS first 4 args) for a BL site."""
    out = {}
    for reg_idx in range(4):
        reg = f"r{reg_idx}"
        sub = track_reg_value(instrs, idx, reg, depth=lookback)
        out[reg] = {
            "imm": sub.get("imm"),
            "pcrel": sub.get("pcrel_addr"),
            "unresolved": sub.get("unresolved_reason"),
            "chain_len": len(sub.get("src_chain", [])),
        }
    # Capture previous 3 raw instructions for context (helps debugging chain_len=0 cases)
    prev = []
    for j in range(max(0, idx - 3), idx):
        prev.append({"addr": instrs[j]["addr"], "mnem": instrs[j]["mnem"], "op_str": instrs[j]["op_str"]})
    out["_prev"] = prev
    return out


def find_arms(instrs: list[dict]) -> list[dict]:
    """Find cmp #imm followed (within 2 instr) by a conditional branch.

    Returns [{addr, imm, branch_target, branch_kind}, ...].
    """
    arms = []
    by_addr = {ins["addr"]: i for i, ins in enumerate(instrs)}
    for i, ins in enumerate(instrs):
        if ins["mnem"] not in ("cmp", "cmn"):
            continue
        # Extract imm
        op_parts = [p.strip() for p in ins["op_str"].split(",")]
        if len(op_parts) < 2 or not op_parts[1].startswith("#"):
            continue
        imm = parse_imm(op_parts[1])
        if imm is None:
            continue
        # Look ahead 1-2 instr for conditional branch
        for j in range(i + 1, min(i + 3, len(instrs))):
            jn = instrs[j]
            if jn["mnem"] in COND_BRANCH:
                tok = jn["op_str"].strip().lstrip("#")
                target = None
                if tok.startswith("0x"):
                    try:
                        target = int(tok, 16)
                    except ValueError:
                        pass
                arms.append({
                    "cmp_addr": ins["addr"],
                    "cmp_reg": op_parts[0],
                    "imm": imm,
                    "branch_addr": jn["addr"],
                    "branch_kind": jn["mnem"],
                    "branch_target": target,
                })
                break
            if jn["mnem"] in ("cmp", "cmn"):
                break  # next cmp
    return arms


def extract_bls_with_args(instrs: list[dict], data: bytes) -> list[dict]:
    """For each BL to a TARGET_OF_INTEREST, backtrace r0..r3 to find args."""
    out = []
    for i, ins in enumerate(instrs):
        if ins["mnem"] not in ("bl", "blx"):
            continue
        tok = ins["op_str"].strip().lstrip("#")
        if not tok.startswith("0x"):
            continue
        try:
            t = int(tok, 16)
        except ValueError:
            continue
        if t not in TARGETS_OF_INTEREST:
            continue
        args = backtrace_args(instrs, i)
        # Back-compat fields for r0
        r0 = args["r0"]
        out.append({
            "site": ins["addr"],
            "target": t,
            "label": TARGETS_OF_INTEREST[t],
            "r0_imm": r0["imm"],
            "r0_src_reg": "?other" if (r0["unresolved"] and r0["unresolved"].startswith("unsupported")) else None,
            "r0_pcrel": r0["pcrel"],
            "r0_unresolved": r0["unresolved"],
            "r0_chain_len": r0["chain_len"],
            "r1_imm": args["r1"]["imm"],
            "r1_pcrel": args["r1"]["pcrel"],
            "r1_chain_len": args["r1"]["chain_len"],
            "r2_imm": args["r2"]["imm"],
            "r2_chain_len": args["r2"]["chain_len"],
            "r3_imm": args["r3"]["imm"],
            "r3_chain_len": args["r3"]["chain_len"],
            "prev_instrs": args["_prev"],
        })
    return out


def categorize_pcrel(value: int) -> str:
    if value == 0:
        return "zero"
    if 1 <= value < 0x80:
        return "small_int"
    if 0x80 <= value < 0x1000:
        return "medium_int"
    if 0x9000 <= value <= 0xC000:
        return "got_slot_offset"
    if 0xA0000 <= value <= 0xB3000:
        return "binary_addr_strings_or_jt"
    if value & 0x80000000:
        return "negative_signed_offset"
    if 0x10000 <= value < 0xA0000:
        return "binary_addr"
    return "other"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("addr", help="function start address (hex)")
    parser.add_argument("end", nargs="?", default=None, help="function end address (hex, exclusive)")
    parser.add_argument("--label", default="subsystem", help="output label")
    args = parser.parse_args()

    start = int(args.addr, 16)
    end = int(args.end, 16) if args.end else (start + 0x4000)
    label = args.label
    out_path = REPO / "work" / "h3" / f"{label}_disasm.json"

    if not BIN.exists():
        print(f"!! binary missing: {BIN}")
        return
    data = BIN.read_bytes()

    print(f"=== {label} (0x{start:08x} ~ 0x{end:08x}, {end-start} bytes / {(end-start)/1024:.1f} KB) ===")
    instrs = walk_with_skip(data, start, end)
    print(f"instructions: {len(instrs)}")

    # 1. cmp arms
    arms = find_arms(instrs)
    print(f"\n=== {len(arms)} cmp+branch arms found ===")
    arm_imms = Counter()
    for a in arms:
        arm_imms[a["imm"]] += 1
    print("imm distribution (top 20):")
    for v, c in arm_imms.most_common(20):
        ascii_marker = f" ('{chr(v)}')" if 0x20 <= v < 0x7F else ""
        print(f"  cmp #0x{v:02x} ({v:4d}){ascii_marker}: {c}x")

    print("\n=== arms in code order (head 30) ===")
    for a in arms[:30]:
        ascii_marker = f" ('{chr(a['imm'])}')" if 0x20 <= a['imm'] < 0x7F else ""
        tgt = f"0x{a['branch_target']:08x}" if a["branch_target"] else "?"
        print(f"  0x{a['cmp_addr']:08x}: cmp {a['cmp_reg']}, #0x{a['imm']:02x}{ascii_marker}  → {a['branch_kind']} {tgt}")
    if len(arms) > 30:
        print(f"  ... ({len(arms)-30} more)")

    # 2. BL with args (for byte_append / u32_append / sound_trigger / etc.)
    bls = extract_bls_with_args(instrs, data)
    print(f"\n=== {len(bls)} interesting BL sites (with arg backtrace) ===")
    by_target = defaultdict(list)
    for b in bls:
        by_target[b["label"]].append(b)
    for tlabel, lst in sorted(by_target.items(), key=lambda x: -len(x[1])):
        print(f"\n  {tlabel}: {len(lst)} calls")
        for b in lst[:20]:
            arg_str = ""
            if b["r0_imm"] is not None:
                arg_str = f"r0=#0x{b['r0_imm']:x} ({b['r0_imm']})"
            elif b.get("r0_imm_add") is not None:
                arg_str = f"r0+=#0x{b['r0_imm_add']:x}"
            elif b["r0_src_reg"]:
                arg_str = f"r0=<{b['r0_src_reg']}>"
            elif b["r0_pcrel"]:
                pcrel_addr = b["r0_pcrel"]
                if 0 <= pcrel_addr < len(data) - 4:
                    v = struct.unpack("<I", data[pcrel_addr:pcrel_addr+4])[0]
                    arg_str = f"r0=*0x{pcrel_addr:08x}=0x{v:x}"
                else:
                    arg_str = f"r0=*0x{pcrel_addr:08x}=?"
            else:
                arg_str = "r0=?"
            print(f"    0x{b['site']:08x}: bl {tlabel}  ({arg_str})")
        if len(lst) > 20:
            print(f"    ... ({len(lst)-20} more)")

    # Tabulate byte_append / u32_append immediate values (display list opcodes!)
    if "byte_append" in by_target or "u32_append" in by_target or "set_byte" in by_target:
        print("\n=== queue producer immediate value distribution ===")
        for tname in ("byte_append", "u32_append", "set_byte"):
            lst = by_target.get(tname, [])
            if not lst:
                continue
            imms = Counter()
            unknown = 0
            for b in lst:
                if b["r0_imm"] is not None:
                    imms[b["r0_imm"]] += 1
                else:
                    unknown += 1
            print(f"  {tname} ({len(lst)} calls, {unknown} unknown source):")
            for v, c in imms.most_common():
                ascii_marker = f" ('{chr(v)}')" if 0x20 <= v < 0x7F else ""
                print(f"    #0x{v:02x} ({v:4d}){ascii_marker}: {c}x")

    # Sound trigger immediate (sound IDs!)
    if "sound_trigger" in by_target:
        print("\n=== sound_trigger r0 distribution (sound IDs) ===")
        imms = Counter()
        unknown = 0
        for b in by_target["sound_trigger"]:
            if b["r0_imm"] is not None:
                imms[b["r0_imm"]] += 1
            else:
                unknown += 1
        print(f"  ({len(by_target['sound_trigger'])} total, {unknown} indirect/unknown)")
        for v, c in imms.most_common():
            print(f"    sound id 0x{v:02x} ({v:3d}): {c}x")

    # 3. PC-rel LDR literals
    pcrel_lits = []
    for ins in instrs:
        op_str = ins["op_str"].replace(" ", "")
        if ins["mnem"] in ("ldr", "ldr.w") and "[pc," in op_str:
            try:
                imm = parse_imm(op_str.split("#", 1)[1].rstrip("]"))
                if imm is None:
                    continue
                pc = (ins["addr"] + 4) & ~3
                tgt = pc + imm
                if 0 <= tgt < len(data) - 4:
                    v = struct.unpack("<I", data[tgt:tgt+4])[0]
                    pcrel_lits.append({"site": ins["addr"], "target": tgt, "value": v,
                                       "category": categorize_pcrel(v)})
            except (IndexError, ValueError):
                pass
    cat_counter = Counter(p["category"] for p in pcrel_lits)
    print(f"\n=== {len(pcrel_lits)} PC-rel LDR literals — category distribution ===")
    for cat, c in cat_counter.most_common():
        print(f"  {cat:30s}: {c}")

    # Save full JSON
    out = {
        "label": label,
        "addr_start": f"0x{start:08x}",
        "addr_end": f"0x{end:08x}",
        "size_bytes": end - start,
        "instr_count": len(instrs),
        "arms": [
            {
                "cmp_addr": f"0x{a['cmp_addr']:08x}",
                "cmp_reg": a["cmp_reg"],
                "imm": a["imm"],
                "imm_hex": f"0x{a['imm']:02x}",
                "branch_addr": f"0x{a['branch_addr']:08x}",
                "branch_kind": a["branch_kind"],
                "branch_target": f"0x{a['branch_target']:08x}" if a["branch_target"] else None,
            }
            for a in arms
        ],
        "arm_imm_dist": [{"imm": v, "count": c} for v, c in arm_imms.most_common()],
        "interesting_bls": [
            {
                "site": f"0x{b['site']:08x}",
                "target": f"0x{b['target']:08x}",
                "label": b["label"],
                "r0_imm": b["r0_imm"],
                "r0_imm_hex": (f"0x{b['r0_imm']:x}" if b["r0_imm"] is not None else None),
                "r0_src_reg": b["r0_src_reg"],
                "r0_pcrel": (f"0x{b['r0_pcrel']:08x}" if b["r0_pcrel"] else None),
            }
            for b in bls
        ],
        "interesting_bl_summary": {tlabel: len(lst) for tlabel, lst in by_target.items()},
        "pcrel_literals_categories": dict(cat_counter),
        "pcrel_literals": [
            {"site": f"0x{p['site']:08x}", "target": f"0x{p['target']:08x}",
             "value": f"0x{p['value']:08x}", "category": p["category"]}
            for p in pcrel_lits
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {out_path}")


if __name__ == "__main__":
    main()
