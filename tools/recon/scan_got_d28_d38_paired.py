"""Round 55 / 2VA: GOT[+0xd28] + GOT[+0xd38] paired storage system wide-scan.

Round 54 mode 4 finding: state 7/10 → GOT[+0xd28], state 9 → GOT[+0xd38].
인접 16B 간격 paired slot — player party 버퍼 vs enemy 버퍼 후보 검증.

전략:
1. binary 내 GOT[+0xd28] / GOT[+0xd38] 의 raw value 확인 (data 영역)
2. binary 전체에서 두 슬롯 reference 모두 wide-scan
3. reference 함수 카운트 + access pattern 추출
"""
import struct
from pathlib import Path
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40


def main() -> None:
    # 1. Raw GOT slot values
    print("=== GOT slot raw values ===")
    for off in [0xd28, 0xd38, 0x16c, 0x18, 0x444]:
        addr = GOT_BASE + off
        if addr + 4 > len(DATA):
            print(f"  GOT[+0x{off:03x}] @ 0x{addr:05x} = (out of binary, GVM-injected)")
            continue
        val = struct.unpack("<I", DATA[addr:addr + 4])[0]
        in_bin = "binary" if val < len(DATA) else "EXTERNAL (GVM heap)"
        print(f"  GOT[+0x{off:03x}] @ 0x{addr:05x} = 0x{val:08x}  ({in_bin})")
    print()

    # 2. Scan binary disasm for `ldr Rx, [pc, #imm]` where literal = 0xd28 or 0xd38
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    md.detail = False

    # Walk binary with Thumb auto-skip
    instrs = []
    pos = 0
    end = len(DATA)
    while pos < end:
        chunk = DATA[pos:end]
        last = pos
        any_emit = False
        for ins in md.disasm(chunk, pos):
            instrs.append((ins.address, ins.mnemonic, ins.op_str))
            last = ins.address + ins.size
            any_emit = True
        if any_emit:
            pos = last
        pos += 2

    print(f"=== {len(instrs)} instructions disassembled ===")

    # Search for `ldr Rx, [pc, #imm]` where literal value = 0xd28 / 0xd38
    sites_d28 = []
    sites_d38 = []
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
            if lit == 0xd28:
                sites_d28.append(addr)
            elif lit == 0xd38:
                sites_d38.append(addr)
        except (IndexError, ValueError):
            pass

    print(f"\n=== GOT[+0xd28] sites: {len(sites_d28)} ===")
    for s in sites_d28[:20]:
        print(f"  ldr@0x{s:05x}")

    print(f"\n=== GOT[+0xd38] sites: {len(sites_d38)} ===")
    for s in sites_d38[:20]:
        print(f"  ldr@0x{s:05x}")

    # Enclose: try to map to FUN_xxxx by finding nearest preceding push prologue
    print(f"\n=== Site-to-function mapping (nearest preceding push) ===")
    push_addrs = []
    for addr, mnem, op_str in instrs:
        if mnem == "push" and ("lr" in op_str or "r7" in op_str):
            push_addrs.append(addr)

    def enclose(site_addr: int) -> int | None:
        # Binary search the largest push <= site
        lo, hi = 0, len(push_addrs)
        while lo < hi:
            mid = (lo + hi) // 2
            if push_addrs[mid] <= site_addr:
                lo = mid + 1
            else:
                hi = mid
        return push_addrs[lo - 1] if lo > 0 else None

    func_d28 = Counter(enclose(s) for s in sites_d28)
    func_d38 = Counter(enclose(s) for s in sites_d38)

    print(f"\nGOT[+0xd28] readers by enclosing function (top 15):")
    for f, n in func_d28.most_common(15):
        if f is not None:
            print(f"  FUN_{f:05x}: {n}x")

    print(f"\nGOT[+0xd38] readers by enclosing function (top 15):")
    for f, n in func_d38.most_common(15):
        if f is not None:
            print(f"  FUN_{f:05x}: {n}x")

    # Cross-functional pairing: functions that read BOTH slots
    both = set(func_d28.keys()) & set(func_d38.keys())
    if None in both:
        both.discard(None)
    print(f"\nFunctions that read BOTH GOT[+0xd28] and GOT[+0xd38] ({len(both)}):")
    for f in sorted(both):
        d28_n = func_d28[f]
        d38_n = func_d38[f]
        print(f"  FUN_{f:05x}: +0xd28={d28_n}x, +0xd38={d38_n}x")


if __name__ == "__main__":
    main()
