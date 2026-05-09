"""4 NPC/menu dispatcher 의 handler 영역 일괄 capstone 디스어셈블 (§4.4 자동 분석 2A).

PROGRESS.md 핸드오프의 4 dispatcher:
  - dispatcher 1: jt @ 0x000a9cc4 (host = FUN_0005d214, NPC dispatcher 1)
  - dispatcher 2: jt @ 0x000a9d70 (host = FUN_0005f948, menu/dialog) — 별도 도구로 처리됨
  - dispatcher 3: jt @ 0x000abaa8 (host = FUN_0008b2e8 inline @ 0x8c19c)
  - dispatcher 4: jt @ 0x000abc68 (host = FUN_0008dcd8 inline @ 0x8eb80)

각 jt 19 entries (4-byte) → 7 distinct handler.
이 도구는 dispatcher 1/3/4 를 대상으로:
  1. jump table 디코드 → 7 distinct handler 주소
  2. 각 handler 본문 capstone 디스어셈블 (다음 handler 까지 또는 hard cap)
  3. BL/BLX target / PC-relative LDR / NPC record offset access 추출
  4. 종합 결과 → work/h3/dispatcher_handlers_summary.json

NPC record offset 휴리스틱:
  - ARM Thumb 의 "slot * 0x3c4 + base + offset" 접근은 capstone 에서 직접 매칭 어려움
  - 대신: 모든 ldrh/ldrb/ldr 의 immediate offset 분포 + (slot 곱셈 시그니처 = 0xc4 03 lit) 위치 카운트
"""
from __future__ import annotations

import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
OUT = REPO / "work" / "h3" / "dispatcher_handlers_summary.json"

GOT_BASE = 0x000B2C40

# (dispatcher_id, jt_base, label)
DISPATCHERS = [
    (1, 0x000A9CC4, "NPC dispatcher 1 (host=FUN_0005d214)"),
    (3, 0x000ABAA8, "NPC dispatcher 3 (host inline 0x8c19c in FUN_0008b2e8)"),
    (4, 0x000ABC68, "NPC dispatcher 4 (host inline 0x8eb80 in FUN_0008dcd8)"),
]

# Hard cap to bound disassembly per handler if next-handler-start unknown
HANDLER_HARD_CAP = 0x800  # 2 KB


def to_signed_32(v: int) -> int:
    return v - 0x100000000 if v >= 0x80000000 else v


def decode_jumptable(data: bytes, jt_base: int) -> list[tuple[int, int]]:
    out = []
    for op in range(19):
        off = jt_base + op * 4
        entry = struct.unpack("<I", data[off : off + 4])[0]
        handler = (GOT_BASE + entry) & 0xFFFFFFFF
        out.append((op, handler))
    return out


def disasm_handler(
    md: capstone.Cs,
    data: bytes,
    start: int,
    end: int,
) -> dict:
    """단일 handler 본문 디스어셈블."""
    chunk = data[start:end]
    bl_targets: list[tuple[int, int]] = []  # (instr_addr, target)
    pcrel_ldr: list[tuple[int, str]] = []
    record_off_hint: Counter = Counter()
    instr_count = 0
    first_25 = []

    for ins in md.disasm(chunk, start):
        instr_count += 1
        mnem = ins.mnemonic
        op_str = ins.op_str
        if instr_count <= 25:
            first_25.append(f"  0x{ins.address:08x}: {mnem:<8} {op_str}")
        if mnem in ("bl", "blx"):
            tgt = op_str.strip().lstrip("#")
            if tgt.startswith("0x"):
                try:
                    bl_targets.append((ins.address, int(tgt, 16)))
                except ValueError:
                    pass
        if mnem == "ldr" and "pc" in op_str.lower():
            pcrel_ldr.append((ins.address, op_str))

        # NPC record offset hint:
        #   ldrh / ldrb / ldr with immediate in range 0x100..0x400
        #   (slot record stride is 0x3c4 = 964 bytes)
        if mnem in ("ldrh", "ldrh.w", "ldrb", "ldrb.w", "ldr", "ldr.w", "strh", "strb", "str"):
            # parse "[rN, #0xNN]"
            for tok in op_str.split(","):
                tok = tok.strip().rstrip("]").lstrip("[")
                if tok.startswith("#"):
                    try:
                        v = int(tok[1:], 0)
                        if 0x100 <= v <= 0x400:
                            record_off_hint[v] += 1
                    except ValueError:
                        pass

    return {
        "start": f"0x{start:08x}",
        "end": f"0x{end:08x}",
        "size": end - start,
        "instr_count": instr_count,
        "first_25_instrs": first_25,
        "bl_targets": [
            {"at": f"0x{a:08x}", "target": f"0x{t:08x}"} for a, t in bl_targets
        ],
        "bl_target_freq": [
            {"target": f"0x{t:08x}", "count": c}
            for t, c in Counter(t for _, t in bl_targets).most_common()
        ],
        "pcrel_ldr": [{"at": f"0x{a:08x}", "expr": e} for a, e in pcrel_ldr],
        "record_offset_hint": [
            {"offset": f"0x{o:03x}", "count": c}
            for o, c in record_off_hint.most_common()
        ],
    }


def main() -> None:
    if not BIN.exists():
        print(f"!! binary missing: {BIN}")
        print(f"   extract first: cd work/h3/extracted && unzip -j -o ../../../Hero3/0103EFD4.jar client.bin64000")
        return

    data = BIN.read_bytes()
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False

    summary = {
        "binary": str(BIN.relative_to(REPO)),
        "binary_size": len(data),
        "got_base": f"0x{GOT_BASE:08x}",
        "dispatchers": [],
    }

    cross_handler_bl: Counter = Counter()
    cross_handler_record_off: Counter = Counter()

    for disp_id, jt_base, label in DISPATCHERS:
        print(f"=== dispatcher {disp_id}: {label} ===")
        print(f"jt_base = 0x{jt_base:08x}")

        opcodes = decode_jumptable(data, jt_base)
        # group by handler
        by_handler: dict[int, list[int]] = defaultdict(list)
        for op, h in opcodes:
            by_handler[h].append(op)
        # sort handler addresses
        sorted_handlers = sorted(by_handler.keys())
        # boundaries: each handler ends where the next one starts
        boundaries: list[tuple[int, int]] = []
        for i, h in enumerate(sorted_handlers):
            if i + 1 < len(sorted_handlers):
                end = sorted_handlers[i + 1]
            else:
                end = h + HANDLER_HARD_CAP
            # cap end to binary length
            end = min(end, len(data))
            boundaries.append((h, end))

        disp_record: dict = {
            "id": disp_id,
            "label": label,
            "jt_base": f"0x{jt_base:08x}",
            "opcodes": [
                {"opcode": op, "handler": f"0x{h:08x}"} for op, h in opcodes
            ],
            "distinct_handlers": [f"0x{h:08x}" for h in sorted_handlers],
            "handlers": [],
        }

        for h, end in boundaries:
            ops = sorted(by_handler[h])
            ops_str = (
                f"0x{ops[0]:02x}~0x{ops[-1]:02x}"
                if ops == list(range(ops[0], ops[-1] + 1))
                else ",".join(f"0x{o:02x}" for o in ops)
            )
            print(f"  handler 0x{h:08x} (opcodes {ops_str}, size 0x{end - h:x})")
            res = disasm_handler(md, data, h, end)
            res["opcodes"] = ops
            res["opcodes_label"] = ops_str
            disp_record["handlers"].append(res)

            # accumulate cross-handler stats
            for tgt_freq in res["bl_target_freq"]:
                cross_handler_bl[tgt_freq["target"]] += tgt_freq["count"]
            for off_rec in res["record_offset_hint"]:
                cross_handler_record_off[off_rec["offset"]] += off_rec["count"]

        summary["dispatchers"].append(disp_record)
        print()

    # Cross-dispatcher BL frequency (helper functions)
    summary["cross_handler_bl_top"] = [
        {"target": tgt, "count": c} for tgt, c in cross_handler_bl.most_common(30)
    ]
    summary["cross_handler_record_offset"] = [
        {"offset": off, "count": c}
        for off, c in cross_handler_record_off.most_common()
    ]

    print("=== top BL targets across all handlers ===")
    for tgt, c in cross_handler_bl.most_common(15):
        print(f"  {tgt}: {c} calls")
    print()
    print("=== record-offset hint (ldrh/ldrb/ldr immediate 0x100~0x400) ===")
    for off, c in sorted(cross_handler_record_off.items(), key=lambda x: -x[1]):
        print(f"  {off}: {c}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
