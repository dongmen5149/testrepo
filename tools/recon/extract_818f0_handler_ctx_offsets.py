"""Round 51 / 2RA: FUN_818f0 의 8 handlers 가 ctx (FUN_4ad10 반환값) 에서
읽는 byte offset 추출.

패턴 (모든 handler 동일):
  BL FUN_4ad10                   ; r0 = ctx_ptr
  adds r3, r0, #0                ; r3 = ctx_ptr
  ldr r1/r2/r0, [pc, #imm]       ; r1/r2/r0 = LITERAL_OFFSET
  adds r3, r3, r1/r2/r0          ; r3 = ctx + offset
  ldrb r3, [r3]                  ; state_byte = ctx[offset]

각 handler 의 "ldr Rx, [pc, #imm]" 직후 첫번째 literal 추출 = ctx offset.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

HANDLERS = [
    (-16, 0x8199c, 0x819a8),  # ldr r0, [pc, #0x31c] at 0x819a6
    (-5,  0x81b9c, 0x81bb0),  # ldr r1, [pc, #0x11c] at 0x81ba6
    (-3,  0x823ea, 0x82400),
    (-4,  0x8263a, 0x82650),
    (-1,  0x828f6, 0x8290c),
    (-2,  0x82a98, 0x82aae),
    (+55, 0x82c2c, 0x82c40),
    (+57, 0x82d18, 0x82d2a),
]


def main() -> None:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    print(f"{'arg':>4}  {'handler':>9}  {'ldr_addr':>9}  {'pc_imm':>7}  {'lit_addr':>9}  {'ctx_off':>10}  size_limit  meaning")
    print("-" * 100)
    for arg, hstart, hend in HANDLERS:
        size = hend - hstart + 0x20
        ldr_addr = None
        ldr_imm = None
        cmp_limit = None
        for ins in md.disasm(DATA[hstart:hstart + size], hstart):
            if ins.mnemonic == "ldr" and "[pc" in ins.op_str and ldr_addr is None:
                # First `ldr Rx, [pc, #imm]` AFTER initial BL
                if ins.address > hstart + 4:  # skip first instruction (BL)
                    try:
                        imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                        ldr_addr = ins.address
                        ldr_imm = imm
                    except Exception:
                        pass
            elif ins.mnemonic.startswith("cmp") and cmp_limit is None and ldr_addr is not None:
                try:
                    cmp_limit = int(ins.op_str.split(", ")[1].lstrip("#"), 0)
                except Exception:
                    pass
                break
        if ldr_addr is None:
            print(f"  arg={arg:+d}: no ldr found")
            continue
        pc = (ldr_addr + 4) & ~3
        lit_addr = pc + ldr_imm
        lit_val = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
        # ctx_off interpretation: signed (could be negative)
        if lit_val & 0x80000000:
            lit_signed = lit_val - 0x100000000
        else:
            lit_signed = lit_val
        print(f"  {arg:+4d}  0x{hstart:05x}     0x{ldr_addr:05x}    0x{ldr_imm:03x}  0x{lit_addr:05x}    0x{lit_val:08x}  cmp <=#{cmp_limit if cmp_limit is not None else '?'}")


if __name__ == "__main__":
    main()
