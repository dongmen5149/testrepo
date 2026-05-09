"""§4.4 후속 — dispatcher 함수의 cmp arm 별 핸들러 BL 매핑 (자동 분석 2T).

배경 (2026-05-10 PM-6 발견):
  FUN_0009b252 (4KB) = 가장 강력한 type-tag reader 후보. 86 cmp arms + 53 context_getter calls.

이번 도구의 목적:
  각 cmp arm 의 분기 블록을 식별 → 그 블록 안에서 호출하는 BL targets 추출.
  → cmp #imm 마다 어떤 핸들러로 분기하는지 매핑.

알고리즘:
  1. 함수 본문 walk_with_skip 으로 디스어셈블
  2. 각 cmp+conditional branch arm 에 대해:
     - branch_target 위치부터 시작
     - 다음 cmp/conditional branch 또는 unconditional jump/return 까지가 arm body
     - arm body 안의 BL targets 수집
  3. {arm_imm: [bl_targets, ...]} 매핑 생성
  4. arm body 길이 + BL count + cmp 추가 등 통계
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"

VENEERS = set(range(0x000A42A0, 0x000A42CE, 2))

KNOWN_TARGETS = {
    0x0007e150: "byte_append",
    0x0007e184: "memcpy_read",
    0x0007e1c4: "u32_append",
    0x0007e890: "flush_swap",
    0x0007e63c: "consumer_?",
    0x0007e4c4: "set_byte",
    0x00099764: "sound_trigger",
    0x0003ecfc: "draw_text_sprite",
    0x0000d53c: "screen_ptr_getter",
    0x0000defc: "draw_rect",
    0x0009f624: "graphics_primitive",
    0x0009fb78: "memset_like",
    0x0004ad10: "task_ptr_getter",  # PM-6 정정
    0x00006334: "main_dispatcher",
    0x000031dc: "chain_dispatcher",
    0x00057394: "render_buffer",
    0x0003d5d0: "sound_dispatcher",
    0x00056bf8: "queue_codec",
    0x00060ab4: "page2_ui",
    0x00064048: "default_key_handler",
    0x000630e8: "cmd_processor",
    0x00075b98: "init_reset_helper",
}

COND_BRANCH = {"beq", "bne", "blt", "ble", "bgt", "bge", "bcs", "bcc", "bls", "bhi", "bmi", "bpl"}
UNCOND_BRANCH = {"b", "b.w", "bx", "bl", "blx"}  # bl/blx are calls but b is jump
RETURN_INS = {"bx", "pop"}


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
    return instrs


def find_branch_target(op_str: str) -> int | None:
    tok = op_str.strip().lstrip("#")
    if tok.startswith("0x"):
        try:
            return int(tok, 16)
        except ValueError:
            return None
    return None


def find_arm_body_end(instrs: list[dict], start_idx: int, max_lookahead: int = 60) -> int:
    """Find the end of an arm body — stops at next cmp/branch/return."""
    end = min(start_idx + max_lookahead, len(instrs))
    for j in range(start_idx, end):
        mnem = instrs[j]["mnem"]
        op_str = instrs[j]["op_str"]
        # Stop at next conditional branch or new cmp
        if mnem in COND_BRANCH:
            return j + 1
        if mnem in ("cmp", "cmn"):
            return j
        # Stop at unconditional branch (b only, not bl/blx)
        if mnem in ("b", "b.w"):
            return j + 1
        # Stop at pop {... pc} (return)
        if mnem == "pop" and "pc" in op_str:
            return j + 1
        # Stop at bx lr
        if mnem == "bx" and "lr" in op_str:
            return j + 1
    return end


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("addr", help="function start address (hex)")
    parser.add_argument("end", help="function end address (hex, exclusive)")
    parser.add_argument("--label", default="dispatcher", help="output label")
    args = parser.parse_args()

    start = int(args.addr, 16)
    end = int(args.end, 16)
    label = args.label
    out_path = REPO / "work" / "h3" / f"{label}_arms.json"

    if not BIN.exists():
        print(f"!! binary missing: {BIN}")
        return
    data = BIN.read_bytes()
    print(f"=== {label} arm-by-arm analysis (0x{start:08x}~0x{end:08x}, {end-start} bytes) ===")
    instrs = walk_with_skip(data, start, end)
    addr_to_idx = {ins["addr"]: i for i, ins in enumerate(instrs)}
    print(f"=== {len(instrs)} instructions ===")

    # Find cmp+conditional branch pairs
    arms: list[dict] = []
    for i, ins in enumerate(instrs):
        if ins["mnem"] not in ("cmp", "cmn"):
            continue
        parts = [p.strip() for p in ins["op_str"].split(",")]
        if len(parts) < 2 or not parts[1].startswith("#"):
            continue
        try:
            imm = int(parts[1].lstrip("#"), 0)
        except ValueError:
            continue
        # Look ahead 1-2 instr for cond branch
        for j in range(i + 1, min(i + 3, len(instrs))):
            jn = instrs[j]
            if jn["mnem"] in COND_BRANCH:
                tgt = find_branch_target(jn["op_str"])
                arms.append({
                    "cmp_addr": ins["addr"],
                    "cmp_reg": parts[0],
                    "imm": imm,
                    "branch_addr": jn["addr"],
                    "branch_kind": jn["mnem"],
                    "branch_target": tgt,
                    "branch_idx": j,
                })
                break
            if jn["mnem"] in ("cmp", "cmn"):
                break

    print(f"=== {len(arms)} cmp+branch arms ===")

    # For each arm, identify the arm body (taken branch) and extract BL targets
    arm_handlers: list[dict] = []
    for arm in arms:
        tgt = arm["branch_target"]
        if tgt is None or tgt not in addr_to_idx:
            arm_handlers.append({**arm, "bl_targets": [], "body_size": 0, "body_end_idx": None})
            continue
        body_start = addr_to_idx[tgt]
        body_end = find_arm_body_end(instrs, body_start, max_lookahead=80)
        bl_targets = []
        for j in range(body_start, body_end):
            ins = instrs[j]
            if ins["mnem"] in ("bl", "blx"):
                bt = find_branch_target(ins["op_str"])
                if bt is not None:
                    bl_targets.append(bt)
        arm_handlers.append({
            **arm,
            "body_start": tgt,
            "body_end_idx": body_end,
            "body_size": body_end - body_start,
            "bl_targets": bl_targets,
        })

    # Print summary
    arm_imm_counter = Counter(a["imm"] for a in arms)
    print(f"\n=== arm imm distribution (top 30) ===")
    for v, c in arm_imm_counter.most_common(30):
        ascii_marker = f" ('{chr(v)}')" if 0x20 <= v < 0x7F else ""
        print(f"  cmp #0x{v:02x} ({v:4d}){ascii_marker}: {c}x")

    print(f"\n=== arms with BL targets (head 50) ===")
    interesting_arms = [a for a in arm_handlers if a["bl_targets"]]
    for arm in interesting_arms[:50]:
        bl_str = ", ".join(
            f"0x{t:x}" + (f"[{KNOWN_TARGETS[t]}]" if t in KNOWN_TARGETS else "")
            for t in arm["bl_targets"][:5]
        )
        if len(arm["bl_targets"]) > 5:
            bl_str += f" (+{len(arm['bl_targets'])-5})"
        ascii_marker = f" ('{chr(arm['imm'])}')" if 0x20 <= arm['imm'] < 0x7F else ""
        print(f"  cmp #0x{arm['imm']:02x}{ascii_marker} @0x{arm['cmp_addr']:08x} → 0x{arm['branch_target']:08x} (body {arm['body_size']} instr): {bl_str}")
    if len(interesting_arms) > 50:
        print(f"  ... ({len(interesting_arms)-50} more)")

    # BL target frequency across all arms
    all_bl = Counter()
    for arm in arm_handlers:
        for t in arm["bl_targets"]:
            all_bl[t] += 1
    print(f"\n=== BL target frequency (top 20) ===")
    for t, c in all_bl.most_common(20):
        label_str = f" [{KNOWN_TARGETS[t]}]" if t in KNOWN_TARGETS else ""
        veneer_str = " (veneer)" if t in VENEERS else ""
        print(f"  0x{t:08x}: {c}x{label_str}{veneer_str}")

    # Group BLs by arm imm value (which type tag is handled by which functions?)
    imm_to_bls = defaultdict(Counter)
    for arm in arm_handlers:
        for t in arm["bl_targets"]:
            imm_to_bls[arm["imm"]][t] += 1
    print(f"\n=== per-imm BL target distribution (head 15 imms with BLs) ===")
    sorted_imms = sorted(imm_to_bls.items(), key=lambda x: -sum(x[1].values()))
    for imm, bl_counter in sorted_imms[:15]:
        ascii_marker = f" ('{chr(imm)}')" if 0x20 <= imm < 0x7F else ""
        print(f"\n  cmp #0x{imm:02x}{ascii_marker} ({imm}) — total BLs: {sum(bl_counter.values())}")
        for t, c in bl_counter.most_common(8):
            label_str = f" [{KNOWN_TARGETS[t]}]" if t in KNOWN_TARGETS else ""
            print(f"    {c}x → 0x{t:08x}{label_str}")

    out = {
        "label": label,
        "func_addr": f"0x{start:08x}",
        "func_end": f"0x{end:08x}",
        "instr_count": len(instrs),
        "arm_count": len(arms),
        "arms": [
            {
                "cmp_addr": f"0x{a['cmp_addr']:08x}",
                "imm": a["imm"],
                "imm_hex": f"0x{a['imm']:02x}",
                "branch_target": f"0x{a['branch_target']:08x}" if a["branch_target"] else None,
                "body_size_instr": a.get("body_size", 0),
                "bl_targets": [f"0x{t:08x}" for t in a.get("bl_targets", [])],
            }
            for a in arm_handlers
        ],
        "imm_distribution": [{"imm": v, "count": c} for v, c in arm_imm_counter.most_common()],
        "bl_target_freq": [
            {"target": f"0x{t:08x}", "count": c, "label": KNOWN_TARGETS.get(t)}
            for t, c in all_bl.most_common(50)
        ],
        "imm_to_bls": {
            f"0x{imm:02x}": [{"target": f"0x{t:08x}", "count": c, "label": KNOWN_TARGETS.get(t)}
                              for t, c in counter.most_common()]
            for imm, counter in imm_to_bls.items()
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {out_path}")


if __name__ == "__main__":
    main()
