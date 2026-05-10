"""
enemy_NN.dat (Monster stat data) 디코더 (Round 35 — 2026-05-10).

NOTE: enemy_g.dat 의 121B record 와 다른 파일! enemy_g.dat 는 decode_h5_enemy.py
에서 처리. 이 디코더는 `/c/csv/enemy_0/1/2.dat` (3 difficulty levels) 을 처리.

Round 34 에서 Monster::setEnemyData (0xc1a94, 1532B) 가 LoadRes("/c/csv/enemy_%d.dat")
사용 발견. Round 35 에서 record byte → Monster field 정밀 매핑 추출.

VFS files (3 difficulty levels):
  enemy_0.dat: index=19, hash 0xfed40086, 23190B, 166 records (easy)
  enemy_1.dat: index=20, hash 0xfee61907, 23190B, 166 records (normal)
  enemy_2.dat: index=21, hash 0xfef83188, 23190B, 166 records (hard)

Record layout (variable-size, avg 140B):
  u16 record_size
  u8 name_len
  bytes[name_len]  name (EUC-KR)
  data bytes (after name) → Monster fields (Round 35 disasm 추적):
    byte 0..3   → +0x22c..+0x22f  (4 markers — class/idx codes)
    byte 4..5   → +0x234  (s16 stat 1)
    byte 6      → +0x23c
    byte 7      → +0x240
    byte 8..9   → +0x244  (s16 stat 2)
    byte 10..11 → +0x24c  (s16 stat 3)
    byte 12     → +0x230
    byte 13..14 → +0x236  (s16)
    byte 15     → +0x23d
    byte 16     → +0x241
    byte 17..18 → +0x246  (s16)
    byte 19..20 → +0x24e  (s16)
    byte 21     → +0x231
    byte 22..23 → +0x238  (s16)
    byte 24     → +0x23e
    byte 25     → +0x242
    byte 26..27 → +0x248  (s16)
    byte 28..29 → +0x250  (s16)
    byte 30     → +0x232
    byte 31..32 → +0x23a  (s16)
    byte 33     → +0x23f
    byte 34     → +0x243
    byte 35..36 → +0x24a  (s16)
    byte 37..38 → +0x252  (s16)
    byte 39..42 → +0x254  (u32) — drop threshold "skip" ✓ Round 31
    byte 43..46 → +0x258  (u32) — drop tier 1
    byte 47..50 → +0x25c  (u32) — drop tier 2
    byte 51..54 → +0x260  (u32) — drop tier 3
    byte 55..58 → +0x264  (u32) — drop tier 4
    byte 59..62 → +0x268  (u32) — drop tier 5
    byte 63..66 → +0x26c  (u32) — drop tier 6
    byte 67..72 → +0x270..+0x275  (drop count/type/markers, 6 byte u8)
                  byte 70 = drop_count (Round 27 0xbca68 reader)
                  byte 72 = drop_count_max (Round 27 0xbca44 reader)
    byte 73..74 → +0x276..+0x277
    byte 75..76 → +0x278  (s16)
    byte 77..79 → +0x27a..+0x27c
    byte 80..83 → +0xf4   (u32, BATTLER 영역)
    byte 84..(많은 s16) → +0xf8..+0x114 (BATTLER stats)

산출:
  apps/hero5-godot/assets/gamedata/monster.json
"""
from __future__ import annotations
import csv, json, pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'monster.json'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'


def djb2(s: bytes) -> int:
    h = 0x1505
    for c in s: h = (c + h * 0x21) & 0xFFFFFFFF
    return h


def find_enemy_file(idx: int) -> pathlib.Path | None:
    target = djb2(f'c/csv/enemy_{idx}.dat'.encode())
    with open(CATALOG, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if int(r['hash'], 16) == target:
                vidx = int(r['index'])
                return ENTRIES / f'{vidx:05d}_{target:08x}.bin'
    return None


def parse_record(record: bytes) -> dict:
    if len(record) < 1:
        return {}
    name_len = record[0]
    if name_len > len(record) - 1:
        return {'error': 'name_len exceeds record', 'name_len': name_len}
    name = record[1:1 + name_len].decode('euc-kr', errors='replace')
    data = record[1 + name_len:]

    rec: dict = {'name': name, 'name_len': name_len}
    if len(data) >= 4:
        rec['markers_22c'] = list(data[0:4])
    if len(data) >= 67:
        rec['drop_thresholds'] = {
            'skip':   struct.unpack_from('<I', data, 39)[0],
            'tier_1': struct.unpack_from('<I', data, 43)[0],
            'tier_2': struct.unpack_from('<I', data, 47)[0],
            'tier_3': struct.unpack_from('<I', data, 51)[0],
            'tier_4': struct.unpack_from('<I', data, 55)[0],
            'tier_5': struct.unpack_from('<I', data, 59)[0],
            'tier_6': struct.unpack_from('<I', data, 63)[0],
        }
    if len(data) >= 73:
        rec['drop_markers'] = {
            'b270': data[67],
            'b271_filter': data[68],
            'b272_subtype': data[69],
            'b273_count':   data[70],
            'b274_bonus':   data[71],
            'b275_count_max': data[72],
        }
    if len(data) >= 84:
        rec['stat_f4'] = struct.unpack_from('<I', data, 80)[0]
    rec['data_hex'] = data.hex()
    return rec


def parse_file(buf: bytes) -> dict:
    if len(buf) < 2:
        return {'error': 'too small'}
    count = struct.unpack_from('<H', buf, 0)[0]
    pos = 2
    entries = []
    for i in range(count):
        if pos + 2 > len(buf):
            break
        rec_sz = struct.unpack_from('<H', buf, pos)[0]; pos += 2
        if pos + rec_sz > len(buf):
            break
        record = buf[pos:pos + rec_sz]
        pos += rec_sz
        rec = parse_record(record)
        rec['idx'] = i
        rec['record_size'] = rec_sz
        entries.append(rec)
    return {'count': count, 'entries': entries}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out: dict = {'_meta': {'note': 'See decode_h5_monster.py docstring (Round 34/35).'}}
    diff_names = ['easy', 'normal', 'hard']
    for n in range(3):
        p = find_enemy_file(n)
        if not p:
            continue
        if not p.exists():
            print(f'  enemy_{n}: file missing')
            continue
        result = parse_file(p.read_bytes())
        out[f'enemy_{n}'] = result
        named = sum(1 for e in result.get('entries', []) if e.get('name'))
        diff = diff_names[n] if n < 3 else f'level_{n}'
        print(f'  enemy_{n}.dat ({diff}): {result.get("count")} entries, {named} named')
        for e in result.get('entries', [])[:3]:
            t = e.get('drop_thresholds', {})
            m = e.get('drop_markers', {})
            tiers = '/'.join(str(t.get(k, '-')) for k in ('skip','tier_1','tier_2','tier_3','tier_4','tier_5','tier_6'))
            cnt = f"{m.get('b273_count','?')}/{m.get('b275_count_max','?')}"
            print(f'    [{e.get("idx"):3d}] {e.get("name","?"):>15s}  thresholds={tiers}  drop_count={cnt}')
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nwrote {OUT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
