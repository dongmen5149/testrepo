"""Hero5 enemy_g.dat 의 121B record layout 자동 추출.

방법:
  1. Map::MapEnemyG_set(int, int) 함수 본문 disasm
  2. 패턴: `ldrb/ldrh/ldr Rx, [Rsrc, #N]` (record 안 byte N 읽기)
              ↓ 직후
           `strb/strh/str Rx, [Rdst, #M]`  (in-memory struct offset M 에 쓰기)
  3. 매핑 (record offset N, in-memory struct offset M, size) 수집
  4. Init_ENEMY_G_DATA 에서 알아낸 in-memory struct field 와 결합

산출:
  work/h5/analysis/enemy_g_layout.tsv
"""
from __future__ import annotations
import pathlib, sys, re
import lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / "work/h5/extracted/lib/armeabi/libHeroesLore5.so"
OUT = ROOT / "work/h5/analysis/enemy_g_layout.tsv"


def find_func(b: lief.ELF.Binary, mangled: str) -> tuple[int, int]:
    syms = list(b.dynamic_symbols) + list(b.symtab_symbols)
    for s in syms:
        if s.name == mangled and s.size > 0:
            return (s.value & ~1, s.size)
    return (0, 0)


def disasm(b: lief.ELF.Binary, addr: int, sz: int) -> list:
    code = bytes(b.get_content_from_virtual_address(addr, sz))
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md.detail = True
    return list(md.disasm(code, addr))


# in-memory struct 의 field 이름 추정 (Init_ENEMY_G_DATA 패턴 기반)
# offset → (field_name_guess, size)
INMEM_FIELDS = {
    0x00: ('byte_00', 1), 0x01: ('byte_01', 1), 0x02: ('byte_02', 1),
    0x03: ('byte_03', 1), 0x04: ('byte_04', 1), 0x05: ('byte_05', 1),
    0x06: ('byte_06', 1), 0x07: ('byte_07', 1), 0x08: ('byte_08', 1),
    0x09: ('byte_09', 1), 0x0a: ('byte_0a', 1), 0x0b: ('byte_0b', 1),
    0x0c: ('int_0c', 4), 0x10: ('int_10', 4),
    0x14: ('int_14', 4), 0x18: ('int_18', 4),
    0x1c: ('byte_1c', 1), 0x1d: ('byte_1d', 1),
    0x1e: ('short_1e_HP_or_MAXHP', 2),
    0x20: ('short_20_MP_or_MAXMP', 2),
    0x22: ('short_22_ATK_or_X', 2),
    0x24: ('short_24_DEF_or_Y', 2),
    0x26: ('byte_26', 1),
    0x27: ('byte_27', 1),
}


def main() -> int:
    b = lief.ELF.parse(str(SO))

    # 1) Init_ENEMY_G_DATA — struct field/offset 확인
    addr_init, sz_init = find_func(b, '_ZN3Map17Init_ENEMY_G_DATAEP13_ENEMY_G_DATA')
    print(f'Init_ENEMY_G_DATA: 0x{addr_init:08x} sz={sz_init}')
    init_offsets = []  # [(offset, mnemonic_size)]
    for ins in disasm(b, addr_init, sz_init):
        if ins.mnemonic in ('strb', 'strh', 'str') and len(ins.operands) >= 2:
            mem = ins.operands[1]
            if mem.type == capstone.arm.ARM_OP_MEM and mem.mem.disp >= 0:
                # only Rn = r1 (this argument)
                if mem.mem.base in (capstone.arm.ARM_REG_R1, capstone.arm.ARM_REG_R6):
                    sz = {'strb':1, 'strh':2, 'str':4}[ins.mnemonic]
                    init_offsets.append((mem.mem.disp, sz))
    print(f'  initialized field offsets: {len(init_offsets)} (in-memory struct)')

    # 2) MapEnemyG_set — record byte → struct field 매핑
    addr_set, sz_set = find_func(b, '_ZN3Map13MapEnemyG_setEii')
    print(f'\nMapEnemyG_set: 0x{addr_set:08x} sz={sz_set}')
    insns = disasm(b, addr_set, sz_set)
    print(f'  decoded {len(insns)} insns')

    # 패턴: ldrb Rdst, [Rsrc, #recN]   →   strb Rdst, [Rdst2, #structM]
    # ARM ldrh/ldr 도 처리. 실제로는 ldrb/ldrh/ldr 와 strb/strh/str 짝짓기.
    pairs: list[tuple[int, int, int, str]] = []  # (record_off, struct_off, size, mnem)
    last_load: dict[int, tuple[int, int, str]] = {}  # reg → (record_off, size, mnem)

    LD_SIZE = {'ldrb': 1, 'ldrh': 2, 'ldr': 4, 'ldrsb': 1, 'ldrsh': 2}
    ST_SIZE = {'strb': 1, 'strh': 2, 'str': 4}

    for ins in insns:
        ops = ins.operands
        if ins.mnemonic in LD_SIZE and len(ops) >= 2:
            dst = ops[0]
            mem = ops[1]
            if dst.type == capstone.arm.ARM_OP_REG and mem.type == capstone.arm.ARM_OP_MEM:
                # only ldrXY [base, #imm] (no shifted index reg)
                # MapEnemyG_set 는 r3 가 record offset (computed via add r3, r7, #N)
                # 즉 ldrb r2, [r5, r3] 형태. 상수 disp 없음.
                # → 이전 add r3, r7, #N 의 #N + base offset 을 추적 필요.
                # 단순화: shift-index 모드의 ldrb 는 별도 처리.
                pass
        elif ins.mnemonic in ST_SIZE and len(ops) >= 2:
            pass

    # 더 단순한 패턴 매칭: 텍스트 op_str 분석으로 add r3, r7, #N + ldrb/h/x [r5, r3] + strb/h [r6, #M]
    # MapEnemyG_set 의 실제 구조는:
    #   add r3, r7, #N        ; r3 = record_offset_in_dat = stride*idx + N
    #   ldrb r2, [r5, r3]     ; r2 = record byte at offset (r3-r7)
    #   strb r2, [r6, #M]     ; in-memory struct offset M 에 저장
    add_rN: dict[str, int] = {}   # reg -> imm offset (relative to r7)
    last_loaded: dict[str, tuple[int, int]] = {}  # reg -> (record_off, size)

    for ins in insns:
        m = ins.mnemonic
        os_ = ins.op_str
        # add Rd, r7, #imm
        am = re.match(r'(\w+),\s*r7,\s*#(0x[0-9a-fA-F]+|\d+)$', os_)
        if m == 'add' and am:
            rd = am.group(1)
            imm = int(am.group(2), 0)
            add_rN[rd] = imm
            continue
        # ldrb/ldrh/ldr Rdst, [r5, Roff]
        lm = re.match(r'(\w+),\s*\[r5,\s*(\w+)\]', os_)
        if m in LD_SIZE and lm:
            rdst = lm.group(1)
            roff = lm.group(2)
            if roff in add_rN:
                rec_off = add_rN[roff]
                last_loaded[rdst] = (rec_off, LD_SIZE[m])
            continue
        # strb/strh Rsrc, [r6, #imm]
        sm = re.match(r'(\w+),\s*\[r6,\s*#(0x[0-9a-fA-F]+|\d+)\]', os_)
        if m in ST_SIZE and sm:
            rsrc = sm.group(1)
            struct_off = int(sm.group(2), 0)
            if rsrc in last_loaded:
                rec_off, size = last_loaded[rsrc]
                pairs.append((rec_off, struct_off, size, m))

    print(f'  record→struct pairs: {len(pairs)}')
    if pairs:
        print(f'  first 5: {pairs[:5]}')

    # 출력
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('record_off\tstruct_off\tsize\tmnem\tinmem_field\n')
        for rec, st, sz, mn in sorted(set(pairs)):
            # struct_off 는 r6 + 0x1f0 base 라 실제 in-memory struct offset = struct_off - 0x1f0
            real_off = st - 0x1f0
            field = INMEM_FIELDS.get(real_off, ('?', 0))
            f.write(f'{rec}\t{real_off}\t{sz}\t{mn}\t{field[0]}\n')
    print(f'wrote {OUT}')

    # 핵심 매핑 출력
    print('\n=== record_offset → field (BATTLER stat candidates) ===')
    interesting = []
    for rec, st, sz, mn in sorted(set(pairs)):
        real_off = st - 0x1f0
        if real_off in INMEM_FIELDS:
            interesting.append((rec, real_off, sz, INMEM_FIELDS[real_off][0]))
    for rec, st, sz, fname in sorted(interesting):
        print(f'  record[{rec}..{rec+sz-1}] → struct[{st:#04x}] {fname} ({sz}B)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
