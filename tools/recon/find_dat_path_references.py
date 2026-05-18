"""Round 57 / 2XA: binary 내 /dat/* path string + reference site 검색.

전략:
1. binary 전체에서 "/dat/" 또는 "_dat" 문자열 검색 (raw byte)
2. 각 string 의 binary 내 주소 → PIC literal pool 에서 reference 검색
3. reference 한 함수 = dat file 로더
"""
import re
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from collections import Counter

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40


def main() -> None:
    # 1. Search for string patterns "/dat/" and "_dat"
    print("=== /dat/ + _dat path strings in binary ===\n")

    # Find all "/dat/" prefixes
    dat_patterns = [b"/dat/", b"_dat\0", b"/enemy", b"enemy_dat", b"char_dat", b"drop_dat", b"i_dat"]

    string_locations = {}  # offset → string content
    for pattern in dat_patterns:
        idx = 0
        while True:
            idx = DATA.find(pattern, idx)
            if idx < 0:
                break
            # Extract surrounding string (find null terminator within ±32B)
            start = idx
            # Walk back to find a null or non-printable byte
            while start > 0 and DATA[start - 1] != 0 and 0x20 <= DATA[start - 1] < 0x7f:
                start -= 1
            end = idx + len(pattern)
            while end < len(DATA) and DATA[end] != 0 and 0x20 <= DATA[end] < 0x7f:
                end += 1
            string_locations[start] = DATA[start:end].decode("latin-1")
            idx += 1

    print(f"=== Found {len(string_locations)} unique /dat/ * _dat strings ===")
    for addr in sorted(string_locations):
        print(f"  0x{addr:05x}: \"{string_locations[addr]}\"")

    # 2. For each string addr, find PC-rel references via disasm
    print(f"\n=== Scanning disasm for references to these string addrs ===")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = False

    # Walk binary with Thumb auto-skip
    instrs = []
    pos = 0
    while pos < len(DATA):
        chunk = DATA[pos:]
        last = pos
        any_emit = False
        for ins in md.disasm(chunk, pos):
            instrs.append((ins.address, ins.mnemonic, ins.op_str))
            last = ins.address + ins.size
            any_emit = True
        if any_emit:
            pos = last
        pos += 2

    string_addrs_set = set(string_locations.keys())

    # 2a. Direct PC-rel literal references
    direct_refs = {}  # string_addr → list of ldr_addrs
    sl_rel_refs = {}  # string_addr → list of (ldr_addr, sl_rel_offset) (PIC pattern)

    for addr, mnem, op_str in instrs:
        if mnem != "ldr" or "[pc," not in op_str.replace(" ", ""):
            continue
        try:
            imm = int(op_str.split("#")[1].rstrip("]"), 0)
            pc = (addr + 4) & ~3
            lit_addr = pc + imm
            if lit_addr + 4 > len(DATA):
                continue
            lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
        except (IndexError, ValueError):
            continue

        # Direct: lit == string_addr
        if lit in string_addrs_set:
            direct_refs.setdefault(lit, []).append(addr)
        # PIC pattern: lit = sl_rel_offset s.t. GOT_BASE + lit (as signed 32-bit) == string_addr
        # i.e. lit = string_addr - GOT_BASE (mod 32-bit)
        for s_addr in string_addrs_set:
            sl_rel = (s_addr - GOT_BASE) & 0xFFFFFFFF
            if lit == sl_rel:
                sl_rel_refs.setdefault(s_addr, []).append((addr, sl_rel))

    print(f"\n=== Direct PC-rel references ===")
    for s_addr, addrs in sorted(direct_refs.items()):
        s = string_locations[s_addr]
        print(f"\n  String 0x{s_addr:05x} \"{s}\":")
        for a in addrs[:10]:
            print(f"    ldr@0x{a:05x}")

    print(f"\n=== sl-relative (PIC) references ===")
    for s_addr, refs in sorted(sl_rel_refs.items()):
        s = string_locations[s_addr]
        print(f"\n  String 0x{s_addr:05x} \"{s}\" (sl_rel=0x{refs[0][1]:08x}):")
        for a, _ in refs[:10]:
            print(f"    ldr@0x{a:05x}")


if __name__ == "__main__":
    main()
