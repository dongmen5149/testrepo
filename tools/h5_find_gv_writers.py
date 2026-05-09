#!/usr/bin/env python3
"""HERO 객체 (= gv+0x1474 sub-struct) 의 stat offset 0x22d..0x2fc 범위에
write 하는 모든 함수를 추적.

전략:
  1) 모든 텍스트 심볼 (function) 을 disasm.
  2) 각 함수에서 다음 패턴을 찾는다:
     - mov rN, #IMM(high) ; (add rN, rN, #IMM(low))?  → reg = composed offset
     - strX rM, [rB, rN]   → store at offset reg=composed
     - strX rM, [rB, #OFF] → direct
  3) offset 이 0x22d..0x2fc 범위에 들어가면 (+ rB 가 r0 등 'this' 후보)
     해당 함수 이름과 함께 기록.
  4) 함수 이름을 demangle 휴리스틱으로 의미 추출.

산출:
  work/h5/analysis/gv_substruct_writers.tsv
    offset, type, store_op, func_addr, func_name, func_size
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import capstone
import lief

REPO = Path(__file__).resolve().parents[1]
SO = REPO / "work" / "h5" / "extracted" / "lib" / "armeabi" / "libHeroesLore5.so"
TSV_OUT = REPO / "work" / "h5" / "analysis" / "gv_substruct_writers.tsv"
TXT_OUT = REPO / "work" / "h5" / "analysis" / "gv_substruct_writers_summary.txt"

# We focus on the BATTLER stat region 0x278..0x2fc plus the small-stat region 0x22d..0x277
RANGE_LO = 0x22D
RANGE_HI = 0x300

STORE_TYPE = {
    "strb": "u8",
    "strh": "u16",
    "str": "u32",
}


def main() -> int:
    raw = SO.read_bytes()
    so = lief.parse(str(SO))

    seg_data: list[tuple[int, int, bytes]] = []
    for s in so.segments:
        if s.type != lief.ELF.Segment.TYPE.LOAD:
            continue
        seg_data.append(
            (s.virtual_address, s.virtual_address + s.virtual_size, bytes(s.content))
        )

    def read(va: int, n: int) -> bytes | None:
        for v0, v1, data in seg_data:
            if v0 <= va < v1:
                o = va - v0
                return bytes(data[o : o + n])
        return None

    md_arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md_thumb = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

    seen_syms: dict[int, tuple[str, int, bool]] = {}
    for sym in so.symbols:
        n = sym.name or ""
        if not n or not sym.value or not sym.size:
            continue
        addr = sym.value & ~1
        thumb = bool(sym.value & 1)
        if addr in seen_syms:
            continue
        seen_syms[addr] = (n, sym.size, thumb)

    out_rows: list[dict] = []
    func_count = 0

    for addr, (name, size, thumb) in seen_syms.items():
        if size < 4 or size > 4000:
            continue
        data = read(addr, size)
        if data is None:
            continue
        md = md_thumb if thumb else md_arm
        func_count += 1

        # Track register immediates for offset composition.
        reg_imm: dict[str, int] = {}
        try:
            insns = list(md.disasm(data, addr))
        except Exception:
            continue

        for i, ins in enumerate(insns):
            mnem = ins.mnemonic
            opstr = ins.op_str

            # Reset on call/branch out of function.
            if mnem in ("bl", "blx", "bx"):
                # keep regs but conservatively clear caller-saved
                for r in ("r0", "r1", "r2", "r3", "r12", "ip"):
                    reg_imm.pop(r, None)

            # mov rX, #imm
            m = re.match(r"^(r\d+),\s*#(-?(?:0x[\da-f]+|\d+))$", opstr)
            if mnem == "mov" and m:
                reg_imm[m.group(1)] = int(m.group(2), 0)
                continue
            # movw / movs handled the same
            if mnem in ("movw", "movs") and m:
                reg_imm[m.group(1)] = int(m.group(2), 0)
                continue

            # add rX, rX, #imm
            m = re.match(r"^(r\d+),\s*(r\d+),\s*#(-?(?:0x[\da-f]+|\d+))$", opstr)
            if mnem == "add" and m:
                dst, src, imm = m.group(1), m.group(2), int(m.group(3), 0)
                if src in reg_imm:
                    reg_imm[dst] = reg_imm[src] + imm
                else:
                    reg_imm.pop(dst, None)
                continue

            # strX rS, [rB, rO]
            m = re.match(r"^(r\d+),\s*\[(r\d+),\s*(r\d+)\]$", opstr)
            if mnem in STORE_TYPE and m:
                src, base, off_reg = m.group(1), m.group(2), m.group(3)
                off = reg_imm.get(off_reg)
                if off is not None and RANGE_LO <= off < RANGE_HI:
                    out_rows.append(
                        {
                            "offset": off,
                            "type": STORE_TYPE[mnem],
                            "store_op": f"{mnem} {src}, [{base}, {off_reg}]  ; {off_reg}={off:#x}",
                            "ins_addr": ins.address,
                            "func_addr": addr,
                            "func_name": name,
                            "func_size": size,
                        }
                    )
                continue

            # strX rS, [rB, #OFF]
            m = re.match(r"^(r\d+),\s*\[(r\d+),\s*#(-?(?:0x[\da-f]+|\d+))\](!)?$", opstr)
            if mnem in STORE_TYPE and m:
                src, base, imm = m.group(1), m.group(2), int(m.group(3), 0)
                if RANGE_LO <= imm < RANGE_HI:
                    out_rows.append(
                        {
                            "offset": imm,
                            "type": STORE_TYPE[mnem],
                            "store_op": f"{mnem} {src}, [{base}, #{imm:#x}]",
                            "ins_addr": ins.address,
                            "func_addr": addr,
                            "func_name": name,
                            "func_size": size,
                        }
                    )
                continue

    # Write TSV
    out_rows.sort(key=lambda r: (r["offset"], r["func_addr"]))
    TSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with TSV_OUT.open("w", encoding="utf-8") as fp:
        fp.write("offset\ttype\tstore_op\tins_addr\tfunc_addr\tfunc_size\tfunc_name\n")
        for r in out_rows:
            fp.write(
                f"{r['offset']:#x}\t{r['type']}\t{r['store_op']}\t"
                f"{r['ins_addr']:#x}\t{r['func_addr']:#x}\t{r['func_size']}\t{r['func_name']}\n"
            )

    # Summary by offset → list of unique function names (name-only), sorted by usage count.
    by_offset: dict[int, dict[str, int]] = {}
    for r in out_rows:
        by_offset.setdefault(r["offset"], {}).setdefault(r["func_name"], 0)
        by_offset[r["offset"]][r["func_name"]] += 1

    with TXT_OUT.open("w", encoding="utf-8") as fp:
        fp.write(
            f"# scanned {func_count} functions, {len(out_rows)} stores into [{RANGE_LO:#x}..{RANGE_HI:#x})\n\n"
        )
        for off in sorted(by_offset):
            fp.write(f"## offset {off:#x}  (var_id ~{off_to_var_id(off)})\n")
            for fname, cnt in sorted(by_offset[off].items(), key=lambda x: -x[1]):
                fp.write(f"  {cnt:>3}  {fname}\n")
            fp.write("\n")

    print(f"functions scanned: {func_count}")
    print(f"stores recorded: {len(out_rows)}")
    print(f"unique offsets: {len(by_offset)}")
    print(f"wrote {TSV_OUT.relative_to(REPO)}")
    print(f"wrote {TXT_OUT.relative_to(REPO)}")
    return 0


def off_to_var_id(off: int) -> str:
    """rough var_id estimate from gv_substruct_layout.tsv"""
    # 0x22d → 58 (s8); 0x278..0x2fa step 2 → 111+
    if off == 0x22D:
        return "58"
    if 0x234 <= off <= 0x24A and off % 2 == 0:
        return str(59 + (off - 0x234) // 2)
    if 0x24C <= off <= 0x277:
        return str(67 + (off - 0x24C))
    if 0x278 <= off <= 0x2C0 and off % 2 == 0:
        return str(111 + (off - 0x278) // 2)
    if 0x2A8 <= off <= 0x2FA and off % 2 == 0:
        return str(126 + (off - 0x2A8) // 2)
    if off == 0x2FC:
        return "249"
    return "?"


if __name__ == "__main__":
    raise SystemExit(main())
