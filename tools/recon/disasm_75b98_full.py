"""Round 50 / 2QE: FUN_75b98 본문 (324B, render flush, mode=7,1,1 인자).

FUN_57394 의 dirty path 에서 호출: FUN_75b98(&task[0xa848]+0x10, 7, 1, 1).
- r0 = &task[0xa848]+0x10 (render sub-struct ptr)
- r1 = 7 (mode?)
- r2 = 1
- r3 = 1
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("=== FUN_75b98 full disasm (0x75b98..0x75cdc) ===")
    for ins in md.disasm(DATA[0x75b98:0x75cdc], 0x75b98):
        marker = ""
        if ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                if t == 0x4ad10:
                    marker = "  <BL context_getter>"
                elif t == 0x9fb78:
                    marker = "  <BL memset_like>"
                elif t == 0xa42a4 or t == 0xa429c:
                    marker = "  <BL veneer (indirect call)>"
                else:
                    marker = f"  <BL 0x{t:x}>"
            except Exception:
                marker = "  <BL>"
        elif ins.mnemonic.startswith("cmp"):
            marker = "  <cmp>"
        elif ins.mnemonic in ("b", "beq", "bne", "blt", "ble", "bgt", "bge",
                              "bcs", "bcc", "bls", "bhi", "bmi", "bpl"):
            marker = "  <branch>"
        elif "ldr" in ins.mnemonic and "[pc" in ins.op_str:
            marker = "  <pc-rel>"
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
