#!/usr/bin/env python3
"""DES variant disassembler — dumps ARM disasm of all DES-related functions
plus auto-detects S-box / permutation tables in .rodata.

Output:
  work/h5/analysis/des_disasm.txt  — concatenated disasm
  work/h5/analysis/des_tables.json — detected table addresses + sizes

Run after `pip install lief capstone`.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import capstone
import lief

REPO = Path(__file__).resolve().parents[1]
SO = REPO / "work" / "h5" / "extracted" / "lib" / "armeabi" / "libHeroesLore5.so"
OUT_DIR = REPO / "work" / "h5" / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DES_SYMBOLS = [
    "MX_desInit",
    "char2binary",
    "binary2char",
    "new_bit_permutation",
    "desRound",
    "new_encrypt",
    "new_decrypt",
    "DESdecrypt",
    "startDes",
    "MX_desEncrypt",
    "MX_desDecrypt",
    "MX_desEncryptPKCS7",
    "MX_desDecryptPKCS7",
]


def file_offset_for_va(b: lief.Binary, va: int) -> int | None:
    for seg in b.segments:
        if seg.virtual_address <= va < seg.virtual_address + seg.virtual_size:
            return seg.file_offset + (va - seg.virtual_address)
    return None


def read_va(b: lief.Binary, raw: bytes, va: int, n: int) -> bytes | None:
    off = file_offset_for_va(b, va)
    if off is None:
        return None
    return raw[off : off + n]


def main() -> int:
    if not SO.exists():
        print(f"missing: {SO}", file=sys.stderr)
        return 1

    raw = SO.read_bytes()
    b = lief.parse(str(SO))
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md.detail = True

    sym_by_name: dict[str, tuple[int, int]] = {}
    for s in b.dynamic_symbols:
        if s.name in DES_SYMBOLS:
            sym_by_name[s.name] = (s.value & ~1, s.size)

    missing = [n for n in DES_SYMBOLS if n not in sym_by_name]
    if missing:
        print(f"warning: missing symbols: {missing}", file=sys.stderr)

    # Collect PC-relative loads to build candidate table list
    table_refs: dict[int, set[str]] = {}

    out_path = OUT_DIR / "des_disasm.txt"
    with out_path.open("w", encoding="utf-8") as fp:
        for name in DES_SYMBOLS:
            if name not in sym_by_name:
                continue
            va, size = sym_by_name[name]
            data = read_va(b, raw, va, size)
            if data is None:
                fp.write(f"// {name}: cannot map VA {va:#x}\n\n")
                continue
            fp.write(f"// ===== {name} @ {va:#010x} ({size}B) =====\n")
            for ins in md.disasm(data, va):
                # Resolve PC-relative loads (ldr rN, [pc, #imm])
                op_str = ins.op_str
                m = re.match(r"(\w+),\s*\[pc,\s*#(-?0x[\da-f]+|-?\d+)\]", op_str)
                if ins.mnemonic == "ldr" and m:
                    imm = int(m.group(2), 0)
                    eff = (ins.address + 8 + imm) & ~3
                    pool = read_va(b, raw, eff, 4)
                    if pool and len(pool) == 4:
                        ptr = int.from_bytes(pool, "little")
                        op_str = f"{op_str} ; [{eff:#x}]={ptr:#x}"
                        # If ptr lies in .rodata-ish range, record candidate
                        if 0x100000 <= ptr < 0x200000:
                            table_refs.setdefault(ptr, set()).add(name)
                fp.write(f"  {ins.address:08x}: {ins.mnemonic:8s} {op_str}\n")
            fp.write("\n")

    # Heuristic: classify each candidate ptr by surrounding bytes
    table_info: list[dict] = []
    for ptr in sorted(table_refs):
        chunk = read_va(b, raw, ptr, 4)
        if chunk is None:
            continue
        # Probe up to 4096 bytes — many DES tables are 64..256 bytes
        big = read_va(b, raw, ptr, 4096) or b""
        first16 = big[:16].hex()
        # Try interpreting first 64 bytes as u8 array
        u8_64 = list(big[:64])
        looks_like_perm = all(0 <= v < 64 for v in u8_64) and len(set(u8_64)) >= 50
        looks_like_sbox = all(0 <= v < 16 for v in u8_64)
        # u32 array variant
        u32_64 = [int.from_bytes(big[i : i + 4], "little") for i in range(0, 256, 4)]
        looks_like_perm_u32 = all(0 <= v < 64 for v in u32_64) and len(set(u32_64)) >= 50

        info = {
            "va": f"{ptr:#x}",
            "size_known": None,
            "first16": first16,
            "u8_perm": looks_like_perm,
            "u8_sbox4": looks_like_sbox,
            "u32_perm": looks_like_perm_u32,
            "referenced_by": sorted(table_refs[ptr]),
        }
        table_info.append(info)

    # Augment with known DES symbols present as data
    for sym_name in ["KEY4REAL", "KEY4ENCRYPT", "__DES_KEY__"]:
        for s in b.dynamic_symbols:
            if s.name == sym_name:
                ptr = s.value & ~1
                table_info.append(
                    {
                        "va": f"{ptr:#x}",
                        "size_known": s.size,
                        "name": sym_name,
                        "first16": (read_va(b, raw, ptr, 16) or b"").hex(),
                    }
                )

    (OUT_DIR / "des_tables.json").write_text(
        json.dumps({"tables": table_info}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"wrote {out_path}")
    print(f"wrote {OUT_DIR / 'des_tables.json'}")
    print(f"  {len(table_info)} candidate tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
