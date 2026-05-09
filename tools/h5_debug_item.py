"""decode_h5_item.py 의 parse_equip_extra 디버그."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / 'converter'))
from decode_h5_item import parse_equip_extra, find

p = find('c/csv/item_00.dat')
print(f"path={p}")
d = p.read_bytes()
import struct
count = struct.unpack_from('<H', d, 0)[0]
print(f"count={count}")
pos = 2
# 첫 record 만
rec_sz = struct.unpack_from('<H', d, pos)[0]; pos += 2
prefix = struct.unpack_from('<H', d, pos)[0]; pos += 2
strlen = d[pos]; pos += 1
name = d[pos:pos+strlen].decode('euc-kr', errors='replace')
pos += strlen
extra_len = rec_sz - 3 - strlen
extra = d[pos:pos+extra_len]
print(f"rec_sz={rec_sz}  prefix=0x{prefix:x}  strlen={strlen}  name={name}  extra_len={extra_len}")
print(f"extra hex: {extra.hex()}")
result = parse_equip_extra(extra)
print(f"parse_equip_extra result: {result}")
