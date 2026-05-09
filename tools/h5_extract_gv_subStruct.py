#!/usr/bin/env python3
"""var_id 58-160 (전역 state) 의 정확한 offset + 데이터 타입 추출.

`Formula::getValFunc` 의 case body 패턴 (4 변형):

1) ldrb 직접 immediate 형:
    ldr r2, [pc, #X]
    mov r3, #0x1440 ; add r3, r3, #0x34   ; r3 = 0x1474
    ldr r2, [r4, r2]                      ; r2 = gv 포인터
    ldr r3, [r2, r3]                      ; r3 = sub-struct 포인터
    ldrb r0, [r3, #OFF]                   ; OFF = 0x22d, 0x24c, ... (s8)

2) ldrsh + mov r3, #IMM 형:
    ... (위와 동일 prefix)
    ldr r2, [r2, r3]                      ; r2 = sub-struct 포인터 (← reuse r2)
    mov r3, #IMM                          ; r3 = struct field offset
    ldrsh r0, [r2, r3]                    ; s16 read

3) ldrsh + mov + add #2 형 (offset 이 mov immediate 인코딩 한계 초과 시):
    ...
    mov r3, #IMM
    add r3, r3, #2                        ; offset = IMM + 2
    ldr r2, [r1, r2]                      ; r2 = sub-struct ptr (변형 chain)
    ldrsh r0, [r2, r3]

4) 두 번째 chain 변형 (r1 매개체 사용):
    ldr r3, [pc, #X]
    mov r2, #0x1440 ; add r2, r2, #0x34   ; r2 = 0x1474
    ldr r1, [r4, r3]                      ; r1 = gv 포인터
    mov r3, #IMM ; (add r3, r3, #2)?
    ldr r2, [r1, r2]                      ; r2 = sub-struct ptr
    ldrsh r0, [r2, r3]

산출: work/h5/analysis/gv_substruct_layout.tsv
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import capstone
import lief

REPO = Path(__file__).resolve().parents[1]
SO = REPO / "work" / "h5" / "extracted" / "lib" / "armeabi" / "libHeroesLore5.so"
TSV_IN = REPO / "work" / "h5" / "analysis" / "formula_var_dict.tsv"
TSV_OUT = REPO / "work" / "h5" / "analysis" / "gv_substruct_layout.tsv"


LDR_TYPE = {
    "ldrb": "u8",
    "ldrsb": "s8",
    "ldrh": "u16",
    "ldrsh": "s16",
    "ldr": "u32",
}


def main() -> int:
    raw = SO.read_bytes()
    b = lief.parse(str(SO))

    def va2off(va: int):
        for s in b.segments:
            if s.virtual_address <= va < s.virtual_address + s.virtual_size:
                return s.file_offset + (va - s.virtual_address)
        return None

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    rows = TSV_IN.read_text(encoding="utf-8").splitlines()
    out_rows: list[dict] = []
    for line in rows[1:]:
        cols = line.split("\t")
        if len(cols) < 5:
            continue
        var_id = int(cols[0])
        target = int(cols[1], 0)
        first_ops = cols[4]
        if "0x1440" not in first_ops or "#0x34" not in first_ops:
            continue

        off = va2off(target)
        if off is None:
            continue
        disasm = list(md.disasm(raw[off : off + 80], target))[:14]

        # Track register state for the offset register (r3 typically)
        # We watch for: mov rX, #imm; (add rX, rX, #N)?; then ldrXX r0, [rY, rX or #imm]
        reg_imm: dict[str, int] = {}
        load_info: dict | None = None
        sign_extend = False
        # Walk past the gv-chain prefix to find offset compute + final load
        for i, ins in enumerate(disasm):
            opstr = ins.op_str
            mnem = ins.mnemonic
            # mov rX, #imm
            m = re.match(r"^(r\d+),\s*#(-?(?:0x[\da-f]+|\d+))$", opstr)
            if mnem == "mov" and m:
                reg_imm[m.group(1)] = int(m.group(2), 0)
                continue
            # add rX, rX, #imm
            m = re.match(r"^(r\d+),\s*(r\d+),\s*#(-?(?:0x[\da-f]+|\d+))$", opstr)
            if mnem == "add" and m:
                dst, src, imm = m.group(1), m.group(2), int(m.group(3), 0)
                if src in reg_imm:
                    reg_imm[dst] = reg_imm[src] + imm
                continue
            # ldrX r0, [rY, #imm]
            m = re.match(
                r"^(r\d+),\s*\[(r\d+),\s*#(-?(?:0x[\da-f]+|\d+))\]$", opstr
            )
            if mnem in LDR_TYPE and m and m.group(1) == "r0":
                base = m.group(2)
                imm = int(m.group(3), 0)
                # Skip the chain reads (base in {r4, pc} or imm == 0 with non-substruct base)
                if base not in ("r4", "pc"):
                    load_info = {
                        "type": LDR_TYPE[mnem],
                        "offset": imm,
                        "load_op": ins.op_str,
                    }
                    # Check sign-extension follow-up
                    rest = disasm[i + 1 : i + 4]
                    if (
                        load_info["type"] == "u8"
                        and rest
                        and rest[0].mnemonic == "lsl"
                        and "#0x18" in rest[0].op_str
                    ):
                        sign_extend = True
                    break
                continue
            # ldrX r0, [rY, rZ]
            m = re.match(r"^(r\d+),\s*\[(r\d+),\s*(r\d+)\]$", opstr)
            if mnem in LDR_TYPE and m and m.group(1) == "r0":
                base, off_reg = m.group(2), m.group(3)
                if off_reg in reg_imm and base not in ("r4", "pc"):
                    load_info = {
                        "type": LDR_TYPE[mnem],
                        "offset": reg_imm[off_reg],
                        "load_op": f"{ins.op_str}  ; {off_reg}={reg_imm[off_reg]:#x}",
                    }
                    rest = disasm[i + 1 : i + 4]
                    if (
                        load_info["type"] == "u8"
                        and rest
                        and rest[0].mnemonic == "lsl"
                        and "#0x18" in rest[0].op_str
                    ):
                        sign_extend = True
                    break

        if load_info is None:
            continue

        type_str = load_info["type"]
        if type_str == "u8" and sign_extend:
            type_str = "s8"
        out_rows.append(
            {
                "var_id": var_id,
                "type": type_str,
                "offset": load_info["offset"],
                "load_op": load_info["load_op"],
            }
        )

    out_rows.sort(key=lambda r: r["var_id"])

    with TSV_OUT.open("w", encoding="utf-8") as fp:
        fp.write("var_id\ttype\toffset\tload_op\n")
        for r in out_rows:
            fp.write(
                f"{r['var_id']}\t{r['type']}\t{r['offset']:#x}\t{r['load_op']}\n"
            )
    print(f"wrote {TSV_OUT} ({len(out_rows)} entries)")

    # Emit summary by offset → which var_ids read same field
    offset_groups: dict[int, list[int]] = {}
    for r in out_rows:
        offset_groups.setdefault(r["offset"], []).append(r["var_id"])
    duplicates = {k: v for k, v in offset_groups.items() if len(v) > 1}
    if duplicates:
        print(f"  {len(duplicates)} offsets read by multiple var_ids:")
        for off, ids in sorted(duplicates.items()):
            print(f"    {off:#x}: var_ids {ids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
