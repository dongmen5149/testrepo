"""Save 함수의 buffer write event 자동 추출.

Save 함수들은 다음 패턴으로 buffer 에 데이터를 씁니다:
  Int32ToByte(buf, value, offset)  →  buf[offset..offset+4] = value (LE)
  Int64ToByte(buf, value, offset)  →  buf[offset..offset+8] = value
  Int16ToByte(buf, value, offset)  →  buf[offset..offset+2]
  Int8ToByte (or strb)             →  buf[offset] = byte
  memcpy(buf+const, src, size)     →  bulk copy

이 도구는 ARM disasm + register state propagation 으로 위 호출의 인수를
추출하여 file_offset → source/size 매핑을 자동 생성합니다.

사용: python tools/h5_extract_save_writes.py <symbol>

산출: work/h5/analysis/<symbol>_writes.tsv
"""
from __future__ import annotations
import pathlib, sys, lief, capstone

ROOT = pathlib.Path(__file__).resolve().parent.parent
SO = ROOT / 'work/h5/extracted/lib/armeabi/libHeroesLore5.so'
OUT = ROOT / 'work/h5/analysis'

# Util symbols (resolved at runtime, mapped to size in bytes)
TOBYTE_SIZE = {
    '_ZN10StaticUtil10Int8ToByteEcPhi': 1,
    '_ZN10StaticUtil11Int16ToByteEsPhi': 2,
    '_ZN10StaticUtil11Int32ToByteEiPhi': 4,
    '_ZN10StaticUtil11Int64ToByteExPhi': 8,
}

MEMCPY = 0x3130c  # well-known memcpy address


def load_symbol(symbol: str):
    elf = lief.parse(str(SO))
    info = None
    name_by_addr = {}
    for s in elf.symbols:
        if not s.size: continue
        a = s.value & ~1
        name_by_addr.setdefault(a, s.name or '')
        if s.name == symbol:
            info = (a, s.size)
    if not info:
        raise SystemExit(f'{symbol} not found')

    addr, sz = info
    data = b''
    for seg in elf.segments:
        if seg.type != lief.ELF.Segment.TYPE.LOAD: continue
        v0 = seg.virtual_address
        v1 = v0 + seg.virtual_size
        if v0 <= addr < v1:
            data = bytes(seg.content)[addr - v0:addr - v0 + sz]
            break
    return addr, data, name_by_addr


def main():
    sym = sys.argv[1] if len(sys.argv) > 1 else '_ZN8SlotInfo12SaveSlotDataEa'
    addr, data, names = load_symbol(sym)

    # Identify tobyte addresses
    tobyte_addr = {}
    for a, n in names.items():
        if n in TOBYTE_SIZE:
            tobyte_addr[a] = TOBYTE_SIZE[n]

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    md.detail = True
    insns = list(md.disasm(data, addr))

    # State tracker: r0..r12 = (kind, value) where kind in {'imm', 'unknown'}
    #   limited to track immediate constants and mov chains.
    regs = {f'r{i}': ('?', 0) for i in range(13)}
    regs['ip'] = ('?', 0)
    regs['lr'] = ('?', 0)
    regs['sp'] = ('?', 0)
    regs['fp'] = ('?', 0)
    regs['sl'] = ('?', 0)
    regs['sb'] = ('?', 0)

    def reg(name):
        return regs.get(name, ('?', 0))

    events = []
    for ins in insns:
        m = ins.mnemonic
        op = ins.op_str

        # Track simple mov rX, #imm
        if m == 'mov':
            parts = op.split(', ')
            if len(parts) == 2 and parts[1].startswith('#'):
                try:
                    val = int(parts[1][1:], 0)
                    regs[parts[0]] = ('imm', val)
                except ValueError:
                    regs[parts[0]] = ('?', 0)
            elif len(parts) == 2 and parts[1] in regs:
                regs[parts[0]] = regs[parts[1]]
            else:
                # mov rX, rY
                if len(parts) == 2 and parts[0] in regs:
                    regs[parts[0]] = ('?', 0)
        elif m == 'add':
            # add rD, rS, #imm  → if rS is known imm, propagate
            parts = op.split(', ')
            if len(parts) == 3 and parts[2].startswith('#'):
                src = reg(parts[1])
                try:
                    add_val = int(parts[2][1:], 0)
                except ValueError:
                    add_val = None
                if src[0] == 'imm' and add_val is not None:
                    regs[parts[0]] = ('imm', src[1] + add_val)
                else:
                    regs[parts[0]] = ('?', 0)
            else:
                if len(parts) >= 1 and parts[0] in regs:
                    regs[parts[0]] = ('?', 0)
        elif m == 'ldr':
            # destination becomes unknown
            parts = op.split(', ')
            if parts[0] in regs:
                regs[parts[0]] = ('?', 0)
        elif m in ('strb', 'strh', 'str'):
            # Direct write to [r4, #imm] etc — emit event
            parts = op.split(', ', 1)
            if len(parts) == 2:
                src = parts[0]
                tgt = parts[1].strip()
                if tgt.startswith('[') and ',' in tgt:
                    base, offrest = tgt[1:].split(',', 1)
                    offrest = offrest.strip().rstrip(']').strip()
                    if offrest.startswith('#'):
                        try:
                            off = int(offrest[1:], 0)
                            sz_map = {'strb': 1, 'strh': 2, 'str': 4}
                            events.append({
                                'addr': ins.address,
                                'kind': m,
                                'buf_reg': base.strip(),
                                'offset': off,
                                'size': sz_map[m],
                                'src_reg': src,
                            })
                        except ValueError:
                            pass
                elif tgt.startswith('['):
                    # [r4] no offset
                    base = tgt[1:].rstrip(']').strip()
                    sz_map = {'strb': 1, 'strh': 2, 'str': 4}
                    events.append({
                        'addr': ins.address,
                        'kind': m,
                        'buf_reg': base,
                        'offset': 0,
                        'size': sz_map[m],
                        'src_reg': src,
                    })
        elif m in ('bl', 'blx') and op.startswith('#'):
            try:
                t = int(op[1:], 0) & ~1
            except ValueError:
                continue
            if t in tobyte_addr:
                sz = tobyte_addr[t]
                r2 = reg('r2')
                events.append({
                    'addr': ins.address,
                    'kind': 'tobyte',
                    'buf_reg': 'r1',
                    'offset': r2[1] if r2[0] == 'imm' else None,
                    'size': sz,
                    'src_reg': f'r0(value), {names[t]}',
                })
                # r0 clobbered, etc.
                for r in ('r0', 'r1', 'r2', 'r3', 'ip', 'lr'):
                    regs[r] = ('?', 0)
            elif t == MEMCPY:
                r2 = reg('r2')
                events.append({
                    'addr': ins.address,
                    'kind': 'memcpy',
                    'buf_reg': 'r0',
                    'offset': None,
                    'size': r2[1] if r2[0] == 'imm' else None,
                    'src_reg': 'r1',
                })
                for r in ('r0', 'r1', 'r2', 'r3', 'ip', 'lr'):
                    regs[r] = ('?', 0)
            else:
                for r in ('r0', 'r1', 'r2', 'r3', 'ip', 'lr'):
                    regs[r] = ('?', 0)

    # Output
    OUT.mkdir(parents=True, exist_ok=True)
    base = sym.replace('_ZN', '').replace('_ZNK', '')[:40]
    out_path = OUT / f'{sym}_writes.tsv'
    with out_path.open('w', encoding='utf-8') as f:
        f.write('addr\tkind\tbuf\toffset\tsize\tsource\n')
        for e in events:
            off_str = f'0x{e["offset"]:x}' if isinstance(e['offset'], int) else '?'
            sz_str = str(e['size']) if e['size'] is not None else '?'
            f.write(f'0x{e["addr"]:08x}\t{e["kind"]}\t{e["buf_reg"]}\t{off_str}\t{sz_str}\t{e["src_reg"]}\n')

    print(f'extracted {len(events)} write events → {out_path}')
    print('\nFirst 30 events:')
    for e in events[:30]:
        off_str = f'0x{e["offset"]:x}' if isinstance(e['offset'], int) else '?'
        sz_str = str(e['size']) if e['size'] is not None else '?'
        print(f'  0x{e["addr"]:08x}  {e["kind"]:7}  buf={e["buf_reg"]:3}  off={off_str:6}  size={sz_str:3}  src={e["src_reg"]}')


if __name__ == '__main__':
    main()
