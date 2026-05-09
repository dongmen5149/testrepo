"""§4.4 mode 2 entry FUN_00060ab4 (9KB) capstone 디스어셈블 (자동 분석 2B).

Ghidra 미해독 9KB 함수. 본문 분석으로 sub-system 정체 (battle / cutscene / map transition?) 추측.

전략:
  1. 0x60ab4 부터 0x62d1c 까지 디스어셈블
  2. BL 호출 통계 → veneer (0xa42a0~0xa42cc) vs 실제 helper 분리
  3. PC-relative LDR literal 풀에서 16-bit signed offset 의 절대 주소 계산 → GOT 참조 추적
  4. _scn / _mp / record-stride (0x3c4) 등 magic number 검색
  5. inner branch 통계 → switch-like 패턴 카운트
  6. 첫 ~80 lines 출력 (state machine 구조 파악용)
"""
from __future__ import annotations

import json
import struct
from collections import Counter
from pathlib import Path

import capstone

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "work" / "h3" / "extracted" / "client.bin64000"
OUT = REPO / "work" / "h3" / "mode2_disasm.json"

START = 0x00060AB4
END = 0x00062D1C  # 9KB, FUN_00062d1c (3-way mode selector) 시작 직전

VENEERS = set(range(0x000A42A0, 0x000A42CE, 2))  # bx Rn veneers


def main() -> None:
    if not BIN.exists():
        print(f"!! binary missing: {BIN}")
        return

    data = bytes(BIN.read_bytes())
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    md.detail = False

    chunk = data[START:END]
    print(f"=== FUN_00060ab4 (mode 2, size 0x{END-START:x} bytes) ===")
    print()

    bl_targets: list[tuple[int, int]] = []  # (instr_addr, target)
    pcrel_ldr: list[tuple[int, str]] = []
    immediate_lits: Counter = Counter()
    branch_targets: list[int] = []
    cmp_imms: Counter = Counter()  # cmp Rn, #imm — switch detection
    instr_count = 0
    first_lines: list[str] = []

    for ins in md.disasm(chunk, START):
        instr_count += 1
        mnem = ins.mnemonic
        op_str = ins.op_str
        if instr_count <= 80:
            first_lines.append(f"  0x{ins.address:08x}: {mnem:<8} {op_str}")
        if mnem in ("bl", "blx"):
            tgt = op_str.strip().lstrip("#")
            if tgt.startswith("0x"):
                try:
                    bl_targets.append((ins.address, int(tgt, 16)))
                except ValueError:
                    pass
        if mnem in ("ldr", "ldr.w") and "[pc," in op_str.replace(" ", ""):
            pcrel_ldr.append((ins.address, op_str))
        if mnem in ("cmp", "cmn"):
            for tok in op_str.split(","):
                tok = tok.strip()
                if tok.startswith("#"):
                    try:
                        v = int(tok[1:], 0)
                        if 0 <= v < 0x100:
                            cmp_imms[v] += 1
                    except ValueError:
                        pass
        if mnem in ("b", "bl", "beq", "bne", "blt", "ble", "bgt", "bge", "bcs", "bcc", "bls", "bhi"):
            tgt = op_str.strip().lstrip("#")
            if tgt.startswith("0x"):
                try:
                    branch_targets.append(int(tgt, 16))
                except ValueError:
                    pass
        # Detect movw / movt or movs+lsl that load 0x3c4
        if mnem == "movw":
            for tok in op_str.split(","):
                if "#" in tok:
                    try:
                        v = int(tok.split("#")[1], 0)
                        immediate_lits[v] += 1
                    except (ValueError, IndexError):
                        pass

    print("\n".join(first_lines[:60]))
    if len(first_lines) > 60:
        print(f"  ... ({instr_count - 60} more instructions)")

    print()
    bl_freq = Counter(t for _, t in bl_targets)
    veneer_calls = sum(c for t, c in bl_freq.items() if t in VENEERS)
    real_calls = sum(c for t, c in bl_freq.items() if t not in VENEERS)
    print(f"=== BL stats: {len(bl_targets)} calls ({veneer_calls} veneer / {real_calls} direct) ===")
    print("top non-veneer BL targets:")
    for t, c in bl_freq.most_common():
        if t in VENEERS:
            continue
        print(f"  0x{t:08x}: {c}")
        if c < 2:
            break

    print()
    print(f"=== PC-rel LDR sites: {len(pcrel_ldr)} (literal pool refs) ===")
    for addr, expr in pcrel_ldr[:20]:
        print(f"  0x{addr:08x}: {expr}")

    print()
    print(f"=== cmp Rn, #imm distribution (switch detection) ===")
    for v, c in cmp_imms.most_common(20):
        marker = ""
        if 0x10 <= v <= 0x40:
            marker = "  ← possible switch arm"
        print(f"  cmp #0x{v:02x}: {c}{marker}")

    # Search for record-stride and other magic constants
    print()
    print(f"=== magic constants in literal pool ===")
    # Scan literal area for known constants
    found_lits: list[tuple[int, int]] = []
    # Walk word-aligned chunks looking for 0x3c4, 0xb2c40 (GOT), etc.
    for off in range(START, END - 4, 2):
        v = struct.unpack("<I", data[off : off + 4])[0]
        if v in (0x3C4, 0xB2C40, 0x3B3, 0x3B6, 0x3B8):
            found_lits.append((off, v))
    for off, v in found_lits:
        print(f"  0x{off:08x}: 0x{v:08x}")

    out = {
        "addr_start": f"0x{START:08x}",
        "addr_end": f"0x{END:08x}",
        "size": END - START,
        "instr_count": instr_count,
        "first_80_instrs": first_lines,
        "bl_targets_top": [
            {"target": f"0x{t:08x}", "count": c, "is_veneer": t in VENEERS}
            for t, c in bl_freq.most_common(40)
        ],
        "veneer_calls": veneer_calls,
        "direct_calls": real_calls,
        "pcrel_ldr_count": len(pcrel_ldr),
        "cmp_imm_dist": [
            {"imm": v, "count": c} for v, c in cmp_imms.most_common(30)
        ],
        "magic_constants_in_pool": [
            {"off": f"0x{off:08x}", "value": f"0x{v:08x}"} for off, v in found_lits
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nsaved: {OUT}")


if __name__ == "__main__":
    main()
