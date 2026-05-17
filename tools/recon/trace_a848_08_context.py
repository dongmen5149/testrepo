"""Round 50 / 2QD: task[0xa848]+0x08 access 컨텍스트 추적.

Round 49의 stack reload tracking 결과 +0x08 = 7 reads + 3 writes (DOMINANT new field).
사이트들 (4 functions에 분산):
  - FUN_85b18 (880B): 0x85b8e/a2/b4/cc/c1a — 5 accesses
  - FUN_85e88 (84B): 0x85ea6/b8/c8 — 3 accesses
  - FUN_88eb0 (3176B): 0x890fa — 1 access
  - FUN_89b18 (1336B): 0x89c02 — 1 access

각 사이트 부근 컨텍스트 dump → +0x08 의 의미 추정.
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

SITES = [
    (0x85b8e, "FUN_85b18  ldr [+8]"),
    (0x85ba2, "FUN_85b18  ldr [+8]"),
    (0x85bb4, "FUN_85b18  str [+8]"),
    (0x85bcc, "FUN_85b18  str [+8]"),
    (0x85c1a, "FUN_85b18  ldr [+8]"),
    (0x85ea6, "FUN_85e88  ldr [+8]"),
    (0x85eb8, "FUN_85e88  ldr [+8]"),
    (0x85ec8, "FUN_85e88  str [+8]"),
    (0x890fa, "FUN_88eb0  ldr [+8]"),
    (0x89c02, "FUN_89b18  ldr [+8]"),
]


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    for site, label in SITES:
        print(f"\n{'='*60}")
        print(f"Site 0x{site:05x} ({label})")
        print(f"{'='*60}")
        start = max(0, site - 0x10)
        end = min(len(DATA), site + 0x20)
        for ins in md.disasm(DATA[start:end], start):
            marker = ""
            if ins.address == site:
                marker = "  <-- TARGET"
            elif ins.mnemonic == "bl":
                tok = ins.op_str.strip().lstrip("#")
                try:
                    t = int(tok, 0)
                    if t == 0x4ad10:
                        marker = "  <BL context_getter>"
                    elif t == 0x8578c:
                        marker = "  <BL FUN_85578c>"
                    else:
                        marker = f"  <BL 0x{t:x}>"
                except Exception:
                    marker = "  <BL>"
            print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
