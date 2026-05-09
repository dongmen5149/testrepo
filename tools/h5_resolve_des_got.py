#!/usr/bin/env python3
"""Resolve PC-relative GOT lookups in DES functions to find table addresses.

ARM PIC pattern (used throughout libHeroesLore5):
  ldr r4, [pc, #X]       ; r4 = literal at pc+X (the GOT base offset)
  add r4, pc, r4         ; r4 = current_pc+8 + literal = absolute GOT base
  ...
  ldr r3, [pc, #Y]       ; r3 = small literal (offset into GOT)
  ldr rN, [r4, r3]       ; rN = *(GOT_base + offset) → resolved symbol address

Both GOT offsets and the symbols they point to are tracked via
dynamic relocations (R_ARM_GLOB_DAT). We use lief to enumerate them.

Output: work/h5/analysis/des_got_resolved.json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import capstone
import lief

REPO = Path(__file__).resolve().parents[1]
SO = REPO / "work" / "h5" / "extracted" / "lib" / "armeabi" / "libHeroesLore5.so"
OUT = REPO / "work" / "h5" / "analysis" / "des_got_resolved.json"

DES_FUNCS = ["MX_desInit", "char2binary", "binary2char", "new_bit_permutation",
             "desRound", "new_decrypt", "new_encrypt", "DESdecrypt", "startDes",
             "MX_desEncrypt", "MX_desDecrypt", "MX_desEncryptPKCS7",
             "MX_desDecryptPKCS7"]


def main() -> int:
    raw = SO.read_bytes()
    b = lief.parse(str(SO))

    # Build GOT relocation map: offset → symbol info
    # R_ARM_GLOB_DAT (R_ARM type=21) writes symbol address to that offset
    # R_ARM_RELATIVE (type=23) writes (load_base + addend)
    got_map: dict[int, dict] = {}
    for r in b.dynamic_relocations:
        sym = r.symbol
        info = {"type": str(r.type)}
        if sym is not None and sym.name:
            info["sym"] = sym.name
            info["sym_value"] = sym.value
            info["sym_size"] = sym.size
        # R_ARM_RELATIVE: target value = file value at that offset (which is the addend)
        if "RELATIVE" in info["type"]:
            # Read 4 bytes at the GOT location to get addend
            seg = next((s for s in b.segments
                        if s.virtual_address <= r.address < s.virtual_address + s.virtual_size),
                       None)
            if seg:
                fo = seg.file_offset + (r.address - seg.virtual_address)
                info["addend"] = int.from_bytes(raw[fo:fo + 4], "little")
        got_map[r.address] = info

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md.detail = True

    # Symbol lookup
    sym_by_name = {s.name: (s.value & ~1, s.size) for s in b.dynamic_symbols}

    # For each DES function, walk instructions and resolve GOT loads
    results: dict[str, list] = {}
    for fname in DES_FUNCS:
        if fname not in sym_by_name:
            continue
        va, sz = sym_by_name[fname]
        seg = next(s for s in b.segments
                   if s.virtual_address <= va < s.virtual_address + s.virtual_size)
        fo = seg.file_offset + (va - seg.virtual_address)
        data = raw[fo:fo + sz]

        # Pass 1: track literal pool reads (ldr rN, [pc, #imm]) → register holds literal
        reg_state: dict[str, int] = {}     # register → constant value (literal pool load)
        got_base_reg: set[str] = set()      # registers known to hold the GOT base
        got_base_val: int | None = None

        entries = []
        for ins in md.disasm(data, va):
            opstr = ins.op_str
            # Handle pc-relative ldr
            m = re.match(r"(\w+),\s*\[pc,\s*#(-?(?:0x[\da-f]+|\d+))\]", opstr)
            if ins.mnemonic == "ldr" and m:
                dst = m.group(1)
                imm = int(m.group(2), 0)
                eff = (ins.address + 8 + imm) & ~3
                pool_seg = next((s for s in b.segments
                                 if s.virtual_address <= eff < s.virtual_address + s.virtual_size),
                                None)
                if pool_seg:
                    pool_off = pool_seg.file_offset + (eff - pool_seg.virtual_address)
                    val = int.from_bytes(raw[pool_off:pool_off + 4], "little")
                    reg_state[dst] = val
                continue
            # Handle add rN, pc, rN → makes GOT base
            m = re.match(r"(\w+),\s*pc,\s*(\w+)$", opstr)
            if ins.mnemonic == "add" and m:
                dst, src = m.group(1), m.group(2)
                if src in reg_state:
                    base = (ins.address + 8 + reg_state[src]) & 0xFFFFFFFF
                    reg_state[dst] = base
                    got_base_reg.add(dst)
                    if got_base_val is None:
                        got_base_val = base
                continue
            # Handle ldr rN, [rBase, rOff] where rBase is GOT base
            m = re.match(r"(\w+),\s*\[(\w+),\s*(\w+)\]$", opstr)
            if ins.mnemonic == "ldr" and m:
                dst, base, off = m.group(1), m.group(2), m.group(3)
                if base in got_base_reg and off in reg_state:
                    got_addr = (reg_state[base] + reg_state[off]) & 0xFFFFFFFF
                    got_info = got_map.get(got_addr, {})
                    entry = {
                        "ins": f"{ins.address:08x}",
                        "got_addr": f"{got_addr:#x}",
                        "got_offset": f"{reg_state[off]:#x}",
                        **got_info,
                    }
                    entries.append(entry)
                    # Record resolution into reg_state for further tracking
                    if "sym" in got_info:
                        reg_state[dst] = got_info.get("sym_value", 0)
                    continue
            # ldr rN, [rBase, #imm] with base in reg_state
            m = re.match(r"(\w+),\s*\[(\w+),\s*#(-?(?:0x[\da-f]+|\d+))\]$", opstr)
            if ins.mnemonic == "ldr" and m:
                dst, base, imm_s = m.group(1), m.group(2), m.group(3)
                if base in got_base_reg:
                    imm = int(imm_s, 0)
                    got_addr = (reg_state[base] + imm) & 0xFFFFFFFF
                    got_info = got_map.get(got_addr, {})
                    entry = {
                        "ins": f"{ins.address:08x}",
                        "got_addr": f"{got_addr:#x}",
                        "got_offset_imm": f"{imm:#x}",
                        **got_info,
                    }
                    entries.append(entry)
                    continue

        results[fname] = {
            "va": f"{va:#x}",
            "size": sz,
            "got_base": f"{got_base_val:#x}" if got_base_val else None,
            "got_lookups": entries,
        }

    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT}")
    for fn, info in results.items():
        if info["got_lookups"]:
            print(f"  {fn}: {len(info['got_lookups'])} GOT lookups, base={info['got_base']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
