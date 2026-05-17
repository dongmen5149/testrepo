"""Round 49 / 2PB: task[0xa848]+0x0c (render+save 공유 sub-state) 의 graphics_primitive
호출로 흐르는 인자 추적.

FUN_57394 의 4 사이트에서 +0x0c 가 어디로 흘러가는지:
- 0x575fc: ldr r3, [r3, #0xc]   (READ)
- 0x57602: str r3, [r2, #0xc]   (WRITE)
- 0x579a8: str r3, [r2, #0xc]   (WRITE)
- 0x57bcc: ldr r3, [r3, #0xc]   (READ)

각 READ 후 8 instr 윈도우에서 그 값이:
- graphics_primitive (0x9f624) 호출 인자 (r0/r1/r2/r3) 인가
- 다른 BL 인자인가
- 즉시 즐쳐지거나 stack 에 저장되는가
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
import capstone

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

SITES = [
    (0x575fc, "READ"),
    (0x57602, "WRITE"),
    (0x579a8, "WRITE"),
    (0x57bcc, "READ"),
]


def walk_with_skip(start: int, end: int):
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    instrs = []
    pos = start
    while pos < end:
        any_emitted = False
        last = pos
        for ins in md.disasm(DATA[pos:end], pos):
            instrs.append(ins)
            last = ins.address + ins.size
            any_emitted = True
        if any_emitted:
            pos = last
        pos += 2
    return instrs


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("=== Round 49 / 2PB: task[0xa848]+0x0c → graphics_primitive arg trace ===\n")
    for site_addr, kind in SITES:
        print(f"\n{'='*70}")
        print(f"Site 0x{site_addr:05x} ({kind})")
        print(f"{'='*70}")
        start = max(0, site_addr - 0x20)
        end = min(len(DATA), site_addr + 0x60)
        for ins in md.disasm(DATA[start:end], start):
            marker = ""
            if ins.address == site_addr:
                marker = f"  <-- {kind}"
            elif ins.mnemonic == "bl":
                tok = ins.op_str.strip().lstrip("#")
                try:
                    t = int(tok, 0)
                    if t == 0x9f624:
                        marker = "  <-- GRAPHICS_PRIMITIVE"
                    elif t == 0x7e150:
                        marker = "  <-- byte_append"
                    elif t == 0x7e1c4:
                        marker = "  <-- u32_append"
                    elif t == 0x4ad10:
                        marker = "  <-- context_getter"
                    elif t == 0xd53c:
                        marker = "  <-- screen_ptr_getter"
                    else:
                        marker = f"  <BL 0x{t:x}>"
                except Exception:
                    marker = "  <BL>"
            elif ins.mnemonic.startswith("cmp"):
                marker = "  <cmp>"
            print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
