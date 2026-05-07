"""
Hero5 DEX 메소드 바이트코드 파서.

목표: classes.dex 의 `getUniqueAssetNameFromID(int)` 메소드 본문에서
const-string 시퀀스를 추출하여 assetID → name 테이블을 복원한다.

DEX bytecode 의 packed-switch / 단순 if-eqz 분기 모두에서
const-string 명령(opcode 0x1a, 0x1b)이 등장하는 순서대로 dump 한다.

산출:
  work/h5/analysis/dex_const_strings.tsv  — (method_class, method_name, order, string_idx, value)
  work/h5/analysis/asset_name_candidates.txt — 후보 이름 풀 (recover_names 에 주입)
"""
from __future__ import annotations
import struct, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEX = ROOT / 'work' / 'h5' / 'extracted' / 'classes.dex'
OUT_TSV = ROOT / 'work' / 'h5' / 'analysis' / 'dex_const_strings.tsv'
OUT_CAND = ROOT / 'work' / 'h5' / 'analysis' / 'asset_name_candidates.txt'

TARGET_METHOD_KEYWORDS = (
    'getUniqueAssetNameFromID',
    'getAssetName',
    'assetName',
)


def uleb128(buf: bytes, pos: int) -> tuple[int, int]:
    r, s = 0, 0
    while True:
        b = buf[pos]; pos += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, pos


def parse_strings(data: bytes) -> list[str]:
    sz = struct.unpack_from('<I', data, 0x38)[0]
    off = struct.unpack_from('<I', data, 0x3c)[0]
    out = []
    for i in range(sz):
        sd_off = struct.unpack_from('<I', data, off + i*4)[0]
        _, pos = uleb128(data, sd_off)
        end = data.index(b'\x00', pos)
        try:
            out.append(data[pos:end].decode('utf-8'))
        except UnicodeDecodeError:
            out.append('')
    return out


def parse_type_ids(data: bytes, strings: list[str]) -> list[str]:
    sz = struct.unpack_from('<I', data, 0x40)[0]
    off = struct.unpack_from('<I', data, 0x44)[0]
    return [strings[struct.unpack_from('<I', data, off + i*4)[0]] for i in range(sz)]


def parse_method_ids(data: bytes, types: list[str], strings: list[str]) -> list[tuple[str, str]]:
    """returns list of (class_descriptor, method_name)"""
    sz = struct.unpack_from('<I', data, 0x58)[0]
    off = struct.unpack_from('<I', data, 0x5c)[0]
    out = []
    for i in range(sz):
        cls_idx, _proto, name_idx = struct.unpack_from('<HHI', data, off + i*8)
        out.append((types[cls_idx], strings[name_idx]))
    return out


def parse_class_defs(data: bytes):
    sz = struct.unpack_from('<I', data, 0x60)[0]
    off = struct.unpack_from('<I', data, 0x64)[0]
    out = []
    for i in range(sz):
        cls_idx, access, superclass, ifaces_off, src_idx, ann_off, cdata_off, sv_off = \
            struct.unpack_from('<8I', data, off + i*32)
        out.append(cdata_off)
    return out


def walk_class_data(data: bytes, off: int):
    """yields (method_idx, code_off) for direct + virtual methods"""
    if off == 0: return
    pos = off
    sf, pos = uleb128(data, pos)
    inf, pos = uleb128(data, pos)
    dm, pos = uleb128(data, pos)
    vm, pos = uleb128(data, pos)
    # skip static fields
    for _ in range(sf):
        _, pos = uleb128(data, pos); _, pos = uleb128(data, pos)
    for _ in range(inf):
        _, pos = uleb128(data, pos); _, pos = uleb128(data, pos)
    last = 0
    for _ in range(dm):
        diff, pos = uleb128(data, pos); last += diff
        _, pos = uleb128(data, pos)
        coff, pos = uleb128(data, pos)
        yield last, coff
    last = 0
    for _ in range(vm):
        diff, pos = uleb128(data, pos); last += diff
        _, pos = uleb128(data, pos)
        coff, pos = uleb128(data, pos)
        yield last, coff


def extract_const_strings_from_code(data: bytes, code_off: int) -> list[int]:
    """Return list of string_idx in execution-order (just walk insn stream)."""
    if code_off == 0: return []
    # code_item header = 16 bytes:
    #   u16 registers_size, ins_size, outs_size, tries_size
    #   u32 debug_info_off, u32 insns_size
    insns_size = struct.unpack_from('<I', data, code_off + 12)[0]
    insns_off = code_off + 16
    out: list[int] = []
    i = 0
    while i < insns_size:
        op = data[insns_off + i*2]
        # const-string vAA, string@BBBB  -> 0x1a, 2 code units
        if op == 0x1a:
            sidx = struct.unpack_from('<H', data, insns_off + i*2 + 2)[0]
            out.append(sidx); i += 2; continue
        # const-string/jumbo vAA, string@BBBBBBBB  -> 0x1b, 3 code units
        if op == 0x1b:
            sidx = struct.unpack_from('<I', data, insns_off + i*2 + 2)[0]
            out.append(sidx); i += 3; continue
        # need to advance by instruction size; use opcode size table
        sz = INSN_SIZE[op]
        if sz == 0:
            # NOP-like / payload — handle special payloads
            # 0x00 followed by 0x01/0x02/0x03 is a switch/array-data payload
            ident = data[insns_off + i*2 + 1]
            if op == 0x00 and ident in (0x01, 0x02, 0x03):
                if ident == 0x01:  # packed-switch payload
                    size = struct.unpack_from('<H', data, insns_off + i*2 + 2)[0]
                    sz = (size * 2) + 4
                elif ident == 0x02:  # sparse-switch payload
                    size = struct.unpack_from('<H', data, insns_off + i*2 + 2)[0]
                    sz = (size * 4) + 2
                elif ident == 0x03:  # fill-array-data payload
                    elem_w = struct.unpack_from('<H', data, insns_off + i*2 + 2)[0]
                    cnt = struct.unpack_from('<I', data, insns_off + i*2 + 4)[0]
                    sz = ((elem_w * cnt + 1) // 2) + 4
                else:
                    sz = 1
            else:
                sz = 1
        i += sz
    return out


# DEX instruction sizes (in 16-bit code units), indexed by opcode.
# 0 = special / payload (handled separately above).
# Reference: https://source.android.com/docs/core/runtime/instruction-formats
INSN_SIZE = [1] * 256
_FMTS = {
    # 1 unit
    'ranges_1': [(0x00,0x00),(0x0e,0x0e),(0x73,0x73),(0x79,0x7a),(0xe3,0xff)],
    # 1 unit (10x, 12x, 11n, 11x): single code unit for most low ops
    # Use a simple catch-all then patch larger ones below
}
# default 1
for op in range(256): INSN_SIZE[op] = 1
# 2-unit opcodes (most "AA, BBBB" style)
for op in (0x01,):  # move/from16 still 1u (move vA,vB)
    pass
# Put a proper mapping based on official table:
# Format 10x,12x,11n,11x,10t : 1 code unit
# Format 20t, 22x, 21t,21s,21h,21c,23x,22b,22t,22s,22c,22cs : 2 code units
# Format 30t, 32x, 31i,31t,31c, 35c,35ms,35mi, 3rc,3rms,3rmi, 45cc, 4rcc : 3 code units
# Format 51l : 5 code units
TWO  = [
    0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,
    0x0d,
    0x14,0x15,0x16,0x17,0x19,0x1a,0x1c,0x1d,0x1e,0x1f,0x20,0x22,0x23,0x25,
    0x28,  # actually 10t=1u — keep
] + list(range(0x29,0x3e)) + list(range(0x52,0x73)) + [0x74,0x75,0x76,0x77,0x78,0xfe,0xfa,0xfb]
THREE = [0x0a,0x0b,0x0c,0x18,0x1b,0x24,0x26,0x27,0x6e,0x6f,0x70,0x71,0x72,0xf0,0xfc]
FIVE  = [0x18]  # const-wide is actually 0x18 51l = 5 units
# Reset & rebuild reliably from known-correct list:
# Use widely-used table from Smali docs:
SIZE_TABLE = {
    0x00:1,0x01:1,0x02:2,0x03:3,0x04:1,0x05:2,0x06:3,0x07:1,0x08:2,0x09:3,
    0x0a:1,0x0b:1,0x0c:1,0x0d:1,0x0e:1,0x0f:1,0x10:1,0x11:1,
    0x12:1,0x13:2,0x14:3,0x15:2,0x16:2,0x17:3,0x18:5,0x19:2,0x1a:2,0x1b:3,
    0x1c:2,0x1d:1,0x1e:1,0x1f:2,0x20:2,0x21:1,0x22:2,0x23:2,0x24:3,0x25:3,
    0x26:3,0x27:1,0x28:1,0x29:2,0x2a:3,0x2b:3,0x2c:3,0x2d:2,0x2e:2,0x2f:2,
    0x30:2,0x31:2,0x32:2,0x33:2,0x34:2,0x35:2,0x36:2,0x37:2,0x38:2,0x39:2,
    0x3a:2,0x3b:2,0x3c:2,0x3d:2,
    # 0x3e..0x43 unused
    0x44:2,0x45:2,0x46:2,0x47:2,0x48:2,0x49:2,0x4a:2,0x4b:2,0x4c:2,0x4d:2,
    0x4e:2,0x4f:2,0x50:2,0x51:2,
    0x52:2,0x53:2,0x54:2,0x55:2,0x56:2,0x57:2,0x58:2,
    0x59:2,0x5a:2,0x5b:2,0x5c:2,0x5d:2,0x5e:2,0x5f:2,
    0x60:2,0x61:2,0x62:2,0x63:2,0x64:2,0x65:2,0x66:2,
    0x67:2,0x68:2,0x69:2,0x6a:2,0x6b:2,0x6c:2,0x6d:2,
    0x6e:3,0x6f:3,0x70:3,0x71:3,0x72:3,
    0x74:3,0x75:3,0x76:3,0x77:3,0x78:3,
    0x7b:1,0x7c:1,0x7d:1,0x7e:1,0x7f:1,0x80:1,0x81:1,0x82:1,0x83:1,0x84:1,
    0x85:1,0x86:1,0x87:1,0x88:1,0x89:1,0x8a:1,0x8b:1,0x8c:1,0x8d:1,0x8e:1,
    0x8f:1,
    0x90:2,0x91:2,0x92:2,0x93:2,0x94:2,0x95:2,0x96:2,0x97:2,0x98:2,0x99:2,
    0x9a:2,0x9b:2,0x9c:2,0x9d:2,0x9e:2,0x9f:2,
    0xa0:2,0xa1:2,0xa2:2,0xa3:2,0xa4:2,0xa5:2,0xa6:2,0xa7:2,0xa8:2,0xa9:2,
    0xaa:2,0xab:2,0xac:2,0xad:2,0xae:2,0xaf:2,
    0xb0:1,0xb1:1,0xb2:1,0xb3:1,0xb4:1,0xb5:1,0xb6:1,0xb7:1,0xb8:1,0xb9:1,
    0xba:1,0xbb:1,0xbc:1,0xbd:1,0xbe:1,0xbf:1,
    0xc0:1,0xc1:1,0xc2:1,0xc3:1,0xc4:1,0xc5:1,0xc6:1,0xc7:1,0xc8:1,0xc9:1,
    0xca:1,0xcb:1,0xcc:1,0xcd:1,0xce:1,0xcf:1,
    0xd0:2,0xd1:2,0xd2:2,0xd3:2,0xd4:2,0xd5:2,0xd6:2,0xd7:2,
    0xd8:2,0xd9:2,0xda:2,0xdb:2,0xdc:2,0xdd:2,0xde:2,0xdf:2,
    0xe0:2,0xe1:2,0xe2:2,
    0xfa:4,0xfb:4,0xfc:3,0xfd:2,0xfe:2,0xff:2,
}
for op, sz in SIZE_TABLE.items():
    INSN_SIZE[op] = sz
# anything not in table: leave as 1 (will likely error or skip)


def main() -> int:
    data = DEX.read_bytes()
    if data[:4] != b'dex\n':
        print('not a DEX file', file=sys.stderr); return 1

    print(f'parsing strings...')
    strings = parse_strings(data)
    print(f'  {len(strings)} strings')

    types = parse_type_ids(data, strings)
    methods = parse_method_ids(data, types, strings)
    print(f'  {len(types)} types, {len(methods)} methods')

    cdata_offs = parse_class_defs(data)
    print(f'  {len(cdata_offs)} class_defs')

    OUT_TSV.parent.mkdir(parents=True, exist_ok=True)
    candidates: set[str] = set()
    rows = []
    methods_with_strings = 0

    for cdata_off in cdata_offs:
        for midx, code_off in walk_class_data(data, cdata_off):
            if code_off == 0: continue
            cls, mname = methods[midx]
            sidxs = extract_const_strings_from_code(data, code_off)
            if not sidxs: continue
            methods_with_strings += 1
            is_target = any(kw.lower() in mname.lower() for kw in TARGET_METHOD_KEYWORDS)
            for order, sidx in enumerate(sidxs):
                val = strings[sidx] if sidx < len(strings) else ''
                if is_target:
                    rows.append((cls, mname, order, sidx, val))
                # collect every const-string as candidate
                if val:
                    candidates.add(val)

    print(f'  methods with const-string: {methods_with_strings}')
    print(f'  unique const-string values: {len(candidates)}')
    print(f'  rows for target methods: {len(rows)}')

    # Dump full insn dump for getUniqueAssetNameFromID specifically
    print('\n[getUniqueAssetNameFromID full instruction dump]:')
    for cdata_off in cdata_offs:
        for midx, code_off in walk_class_data(data, cdata_off):
            cls, mname = methods[midx]
            if mname != 'getUniqueAssetNameFromID': continue
            print(f'\n--- {cls}::{mname}  code_off=0x{code_off:x} ---')
            if code_off == 0:
                print('  (abstract / native)'); continue
            insns_size = struct.unpack_from('<I', data, code_off + 12)[0]
            insns_off = code_off + 16
            print(f'  insns_size={insns_size} code units')
            i = 0
            while i < insns_size and i < 200:
                op = data[insns_off + i*2]
                arg = data[insns_off + i*2 + 1]
                extra = ''
                if op in (0x1a,):
                    sidx = struct.unpack_from('<H', data, insns_off + i*2 + 2)[0]
                    extra = f' string@{sidx}={strings[sidx]!r}'
                elif op == 0x1b:
                    sidx = struct.unpack_from('<I', data, insns_off + i*2 + 2)[0]
                    extra = f' string@{sidx}={strings[sidx]!r}'
                elif op in (0x6e,0x6f,0x70,0x71,0x72):
                    midx2 = struct.unpack_from('<H', data, insns_off + i*2 + 4)[0]
                    if midx2 < len(methods):
                        extra = f' method@{midx2}={methods[midx2][0]}::{methods[midx2][1]}'
                elif op == 0x54:  # iget-object
                    fidx = struct.unpack_from('<H', data, insns_off + i*2 + 2)[0]
                    extra = f' field@{fidx}'
                elif op == 0x60:  # sget
                    fidx = struct.unpack_from('<H', data, insns_off + i*2 + 2)[0]
                    extra = f' sfield@{fidx}'
                elif op in (0x12,0x13):  # const/4, const/16
                    if op == 0x12:
                        n = arg >> 4; n = n - 16 if n >= 8 else n
                        extra = f' #{n}'
                    else:
                        n = struct.unpack_from('<h', data, insns_off + i*2 + 2)[0]
                        extra = f' #{n}'
                sz = INSN_SIZE[op] if INSN_SIZE[op] else 1
                print(f'  [{i:04d}] op=0x{op:02x} sz={sz}{extra}')
                if sz == 0: break
                i += sz

    # Always emit candidate-method list for eamobile classes with const-strings
    print('\n[methods in co/kr/eamobile/* with >=1 const-string]:')
    for cdata_off in cdata_offs:
        for midx, code_off in walk_class_data(data, cdata_off):
            cls, mname = methods[midx]
            if 'co/kr/eamobile' not in cls: continue
            if code_off == 0: continue
            sidxs = extract_const_strings_from_code(data, code_off)
            if len(sidxs) >= 5:
                print(f'  {cls}::{mname}  strings={len(sidxs)}')

    with open(OUT_TSV, 'w', encoding='utf-8') as f:
        f.write('class\tmethod\torder\tstring_idx\tvalue\n')
        for r in rows:
            f.write('\t'.join(str(x) for x in r) + '\n')

    with open(OUT_CAND, 'w', encoding='utf-8') as f:
        for s in sorted(candidates):
            f.write(s + '\n')

    print(f'\nwrote {OUT_TSV}')
    print(f'wrote {OUT_CAND}')

    if False and rows:
        print('\nfirst 20 const-strings in target methods:')
        for r in rows[:20]:
            print(f'  {r[1]}[{r[2]:4d}]  → {r[4]!r}')
    else:
        print('\n(no methods matched target keywords — list method names containing "asset" or "name" candidates...)')
        names_seen = set()
        for cdata_off in cdata_offs:
            for midx, code_off in walk_class_data(data, cdata_off):
                cls, mname = methods[midx]
                if any(k in mname.lower() for k in ('asset','name','file','load','vfs')) \
                        and 'co/kr/eamobile' in cls:
                    key = (cls, mname)
                    if key in names_seen: continue
                    names_seen.add(key)
                    print(f'    {cls} :: {mname}')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
