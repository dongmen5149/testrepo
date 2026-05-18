"""Round 52 / 2SA: FUN_818f0 의 30 leaf handlers 식별용 short dump.

각 leaf 의 첫 12 instr (≈24B) 만 dump → BL/cmp pattern 로 역할 추정.
"""
import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()

# (event_arg, entity_state(or list), leaf_addr)
LEAVES = [
    # arg = -16
    (-16, [0],     0x819e2),
    (-16, [1, 8],  0x819ec),
    (-16, [2],     0x81a32),
    (-16, [10],    0x81ac0),
    (-16, [4],     0x81af6),
    (-16, [3],     0x81b2c),
    (-16, [5],     0x81b48),
    (-16, [6,11,12], 0x81b64),
    (-16, [9],     0x81b80),
    # arg = -5 (letter input subsystem)
    (-5, [0],      0x81be2),
    (-5, [1],      0x81c48),
    (-5, [8],      0x81ce8),
    (-5, [2],      0x81f18),
    (-5, [10],     0x8210e),
    (-5, [4],      0x82126),
    (-5, [9],      0x8213e),
    (-5, [6,7,11,12], 0x8225c),
    (-5, [3],      0x82278),
    (-5, [5],      0x823ce),
    # arg = -3
    (-3, [2,8],    0x82458),
    (-3, [3,9],    0x824e8),
    (-3, [4],      0x824f6),
    (-3, [10],     0x82598),
    # arg = -4
    (-4, [2,8],    0x8267c),
    (-4, [3,9],    0x8270a),
    (-4, [4],      0x82716),
    (-4, [10],     0x82804),
    # arg = -1
    (-1, [0,1],    0x82936),
    (-1, [2,8],    0x82942),
    (-1, [4],      0x829da),
    (-1, [10],     0x82a40),
    # arg = -2
    (-2, [0,1],    0x82ad8),
    (-2, [2,8],    0x82ae4),
    (-2, [4],      0x82b9c),
    (-2, [10],     0x82be4),
    # arg = +55 (post-guard)
    (+55, ["guard 2/8"], 0x82c56),
    # arg = +57 (post-guard)
    (+57, ["guard 2/8"], 0x82d42),
]


def dump_short(start: int, max_inst: int = 14) -> tuple[str, list[int], list[str]]:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    bls = []
    cmps = []
    lines = []
    count = 0
    for ins in md.disasm(DATA[start:start + 60], start):
        marker = ""
        if ins.mnemonic == "bl":
            tok = ins.op_str.strip().lstrip("#")
            try:
                t = int(tok, 0)
                bls.append(t)
                marker = f" <BL 0x{t:x}>"
            except Exception:
                bls.append(0)
        elif ins.mnemonic.startswith("cmp"):
            cmps.append(ins.op_str)
            marker = " <cmp>"
        elif ins.mnemonic == "ldr" and "[pc" in ins.op_str:
            try:
                imm = int(ins.op_str.split("#")[1].rstrip("]"), 0)
                pc = (ins.address + 4) & ~3
                lit_addr = pc + imm
                lit = struct.unpack("<I", DATA[lit_addr:lit_addr + 4])[0]
                marker = f" <LIT=0x{lit:x}>"
            except Exception:
                pass
        elif ins.mnemonic in ("b", "bx") and ("82df4" in ins.op_str or "lr" in ins.op_str):
            marker = " <EXIT>"
        lines.append(f"    0x{ins.address:05x}: {ins.mnemonic:8} {ins.op_str}{marker}")
        count += 1
        if count >= max_inst:
            break
    return "\n".join(lines), bls, cmps


def main() -> None:
    last_arg = None
    for arg, states, addr in LEAVES:
        if arg != last_arg:
            print(f"\n========== event_arg = {arg:+d} ==========")
            last_arg = arg
        sstr = ",".join(str(s) for s in states)
        print(f"\n--- state {{{sstr}}} -> leaf @ 0x{addr:05x} ---")
        snippet, bls, cmps = dump_short(addr)
        print(snippet)
        if bls:
            unique_bls = sorted(set(bls))
            print(f"  BL targets: {[hex(b) for b in unique_bls]}")
        if cmps:
            print(f"  cmps: {cmps}")


if __name__ == "__main__":
    main()
