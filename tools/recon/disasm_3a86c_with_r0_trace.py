"""Round 49 / 2PD: FUN_3a86c letter input 본문 + r0=#2 sub-mode 의미 분석.

FUN_3a86c (388B / 177 instr) — letter input subsystem 진입점.
- cmp #0xf range guard at 0x3a89e
- cmp #0 at 0x3a93e 와 0x3a96c

본문에서 r0 (input sub-mode) 가 어떻게 사용되는지 추적:
1. prologue 에서 r0 가 어디에 저장되는지
2. cmp #0xf 의 비교 대상 (r2) 가 r0 인지
3. 분기 후 어떤 처리가 일어나는지
"""
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print("=== FUN_3a86c full disasm (0x3a86c-0x3a9f0) ===\n")
    for ins in md.disasm(DATA[0x3a86c:0x3a9f0], 0x3a86c):
        marker = ""
        if ins.mnemonic.startswith("cmp"):
            marker = "  <CMP>"
        elif ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                if t == 0x4ad10:
                    marker = "  <BL context_getter>"
                elif t == 0x3c920:
                    marker = "  <BL FUN_3c920 letter_core>"
                else:
                    marker = f"  <BL 0x{t:x}>"
            except Exception:
                marker = "  <BL>"
        elif ins.mnemonic in ("b", "beq", "bne", "blt", "ble", "bgt", "bge",
                              "bcs", "bcc", "bls", "bhi", "bmi", "bpl"):
            marker = "  <branch>"
        elif "ldr" in ins.mnemonic and "[pc" in ins.op_str:
            marker = "  <pc-rel>"
        print(f"  0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")


if __name__ == "__main__":
    main()
