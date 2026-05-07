"""enemy_g.dat 의 record raw bytes 직접 검사."""
import pathlib, csv, struct, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAMES = ROOT / 'work/h5/analysis/asset_names.tsv'
ENTRIES = ROOT / 'work/h5/vfs_entries'

with open(NAMES, encoding='utf-8') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        if r['recovered_name'] == 'c/csv/enemy_g.dat':
            p = ENTRIES / f'{int(r["index"]):05d}_{int(r["hash"],16):08x}.bin'
            break

d = p.read_bytes()
print(f'file size: {len(d)} ({len(d) - 4} payload, /121 = {(len(d)-4)//121})')
print(f'count={struct.unpack_from("<H", d, 0)[0]}, payload_sz={struct.unpack_from("<H", d, 2)[0]}')

for idx in [0, 2, 3, 7, 50, 100]:
    off = 4 + idx * 121
    rec = d[off:off + 121]
    print(f'\n=== record #{idx} (file offset {off}) ===')
    for i in range(0, 0x30, 4):
        chunk = rec[i:i+4]
        u16a = int.from_bytes(chunk[:2], 'little') if len(chunk) >= 2 else 0
        u16b = int.from_bytes(chunk[2:4], 'little') if len(chunk) >= 4 else 0
        u32 = int.from_bytes(chunk, 'little') if len(chunk) >= 4 else 0
        print(f'  off=0x{i:02x}: {chunk.hex():12} u16_le=({u16a},{u16b})  u32_le={u32}')
