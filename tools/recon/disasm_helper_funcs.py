"""§4.4 dispatcher handler 들에서 가장 많이 호출된 helper 함수의 prologue capstone 디스어셈블.

disasm_all_dispatcher_handlers.py 결과의 cross_handler_bl_top 이 가리키는 helper 들의
첫 ~80 명령어를 출력해서 각 함수의 역할 (sprite drawer / sound / state mutator 등) 추측.

PROGRESS.md 는 다음 helper 두 개를 이미 식별:
  0x00099764 : sound trigger (h2 dispatcher 2 분석)
  0x0003ecfc : sprite text drawing
"""
from __future__ import annotations

import json
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
SUMMARY = REPO / "work" / "h3" / "dispatcher_handlers_summary.json"
OUT = REPO / "work" / "h3" / "helper_func_prologues.json"

# Top callers (집계: dispatcher 1/3/4 handlers)
TOP_HELPERS = [
    0x000A42A0,   # 65 calls
    0x0004AD10,   # 23
    0x00010F84,   # 15
    0x000A42A4,   # 14 (인접 — 같은 함수 진입의 다른 entry?)
    0x0009F624,   # 12
    0x000010F4,   # 11
    0x00000F9C,   # 11
    0x0000D53C,   # 10
    0x00000FFC,   # 10
    0x0009FD64,   # 9
    0x000010C0,   # 8
    0x00099764,   # 7  (already known: sound trigger)
    0x0003ECFC,   # 6  (already known: sprite text drawing)
    0x0009FB78,   # 6
    0x00099A9C,   # 5
]

PROLOGUE_LIMIT = 60  # 명령어 수


def disasm_prologue(md: capstone.Cs, data: bytes, addr: int) -> dict:
    """addr 부터 PROLOGUE_LIMIT 명령어 디스어셈블."""
    chunk = data[addr : addr + 0x200]
    instrs: list[str] = []
    bl_targets: list[str] = []
    pcrel: list[str] = []
    for i, ins in enumerate(md.disasm(chunk, addr)):
        if i >= PROLOGUE_LIMIT:
            break
        instrs.append(f"  0x{ins.address:08x}: {ins.mnemonic:<8} {ins.op_str}")
        if ins.mnemonic in ("bl", "blx"):
            tgt = ins.op_str.strip().lstrip("#")
            if tgt.startswith("0x"):
                bl_targets.append(tgt)
        if ins.mnemonic in ("ldr", "ldr.w") and "pc" in ins.op_str.lower():
            pcrel.append(f"0x{ins.address:08x}: {ins.op_str}")
    return {
        "addr": f"0x{addr:08x}",
        "instr_count": len(instrs),
        "bl_targets": bl_targets,
        "pcrel_ldr": pcrel,
        "lines": instrs,
    }


def main() -> None:
    if not BIN.exists():
        print(f"!! binary missing: {BIN}")
        return

    data = BIN.read_bytes()
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False

    out: list[dict] = []
    for addr in TOP_HELPERS:
        print(f"=== helper 0x{addr:08x} ===")
        res = disasm_prologue(md, data, addr)
        for line in res["lines"][:30]:
            print(line)
        if len(res["lines"]) > 30:
            print(f"  ... ({len(res['lines']) - 30} more)")
        if res["bl_targets"]:
            print(f"  BL targets: {', '.join(res['bl_targets'][:10])}")
        if res["pcrel_ldr"]:
            print(f"  PC-rel LDR: {len(res['pcrel_ldr'])} sites")
        print()
        out.append(res)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"saved: {OUT}")


if __name__ == "__main__":
    main()
