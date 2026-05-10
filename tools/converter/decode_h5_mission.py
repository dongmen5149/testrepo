"""
mission_list.dat 디코더 (Round 38 — 2026-05-10).

Round 37 에서 Mission::LoadMissionTable (0x8b73c, 460B) 가 LoadRes("/c/csv/mission_list.dat")
사용 발견. Round 38 에서 record byte → MissionInfo 44B field 정밀 매핑.

VFS:
  mission_list.dat: index=48, hash 0x43b86236, 5355B, count=105 missions

File layout (per record after u16 count):
  u16 record_size    (body size, header itself excluded)
  u8  strlen
  bytes[strlen]      name (EUC-KR)
  u8  mission_type   → MissionInfo +4
  u8  sub_type       → MissionInfo +5
  u8  target_count   → MissionInfo +6
  5 × 6 byte sub-conditions (각 6 byte):
    byte +0 → MissionInfo +7..+0xb (slot index)
    byte +1 → MissionInfo +0xc..+0x10 (sub-flag)
    bytes +2..+5 (u32) → MissionInfo +0x14, +0x18, +0x1c, +0x20, +0x24 (target values)
  u8 final_flag      → MissionInfo +0x28

MissionInfo struct (44B per entry):
  +0..+3 (u32) = name ptr (alloc'd separately, strlen+1 bytes)
  +4 = mission_type
  +5 = sub_type
  +6 = target_count
  +7..+0xb (5 byte) = 5 sub-condition slots (slot idx)
  +0xc..+0x10 (5 byte) = 5 sub-condition flags
  +0x14, +0x18, +0x1c, +0x20, +0x24 (5 × u32) = 5 sub-condition target values
  +0x28 = final flag (extra condition?)

13+ Mission::Check* 함수 (Round 37):
  CheckMissionRefine, CheckOrbCombine, CheckMissionMix,
  CheckMissionPlaytime, CheckMissionMoney, CheckMissionRank,
  CheckMissionSetItem, CheckCollection, CheckQuestComplete, etc.
  → mission_type 이 Check* 함수 dispatch key 일 가능성

산출:
  apps/hero5-godot/assets/gamedata/mission.json (105 missions)
"""
from __future__ import annotations
import csv, json, pathlib, struct

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ENTRIES = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'apps' / 'hero5-godot' / 'assets' / 'gamedata' / 'mission.json'
CATALOG = ROOT / 'work' / 'h5' / 'vfs_catalog.tsv'


def djb2(s: bytes) -> int:
    h = 0x1505
    for c in s: h = (c + h * 0x21) & 0xFFFFFFFF
    return h


def find_mission() -> pathlib.Path | None:
    target = djb2(b'c/csv/mission_list.dat')
    with open(CATALOG, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if int(r['hash'], 16) == target:
                vidx = int(r['index'])
                return ENTRIES / f'{vidx:05d}_{target:08x}.bin'
    return None


def parse_mission(buf: bytes) -> dict:
    if len(buf) < 2:
        return {'error': 'too small'}
    count = struct.unpack_from('<H', buf, 0)[0]
    pos = 2
    entries = []
    for i in range(count):
        if pos + 5 > len(buf):
            break
        rec_sz = struct.unpack_from('<H', buf, pos)[0]; pos += 2
        body_start = pos
        if pos + rec_sz > len(buf):
            break
        strlen = buf[pos]; pos += 1
        if strlen > rec_sz - 1:
            pos = body_start + rec_sz
            entries.append({'idx': i, 'name': '?', 'record_size': rec_sz})
            continue
        try:
            name = buf[pos:pos + strlen].decode('euc-kr', errors='replace')
        except Exception:
            name = ''
        pos += strlen

        # 3 header bytes
        if pos + 3 > body_start + rec_sz:
            entries.append({'idx': i, 'name': name, 'record_size': rec_sz})
            continue
        mission_type = buf[pos]; pos += 1
        sub_type = buf[pos]; pos += 1
        target_count = buf[pos]; pos += 1

        # 5 sub-conditions (6 byte each)
        sub_conditions = []
        for s in range(5):
            if pos + 6 > body_start + rec_sz:
                break
            slot_idx = buf[pos]; pos += 1
            sub_flag = buf[pos]; pos += 1
            target_value = struct.unpack_from('<I', buf, pos)[0]; pos += 4
            sub_conditions.append({
                'slot': slot_idx,
                'sub_flag': sub_flag,
                'target_value': target_value,
            })

        # Final flag
        final_flag = buf[pos] if pos < body_start + rec_sz else None
        pos = body_start + rec_sz

        entries.append({
            'idx': i,
            'name': name,
            'record_size': rec_sz,
            'mission_type': mission_type,
            'sub_type': sub_type,
            'target_count': target_count,
            'sub_conditions': sub_conditions,
            'final_flag': final_flag,
        })
    return {'count': count, 'entries': entries}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    p = find_mission()
    if not p or not p.exists():
        print(f'mission_list.dat not found: {p}')
        return 1
    result = parse_mission(p.read_bytes())
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    named = sum(1 for e in result.get('entries', []) if e.get('name', '?') != '?')
    print(f'wrote {OUT}')
    print(f'  count={result.get("count")}, named={named}')
    # mission_type 분포
    from collections import Counter
    types = Counter(e['mission_type'] for e in result.get('entries', []) if 'mission_type' in e)
    print(f'  mission_type distribution: {sorted(types.items())}')
    # 첫 5 sample
    print('\n  First 5 missions:')
    for e in result.get('entries', [])[:5]:
        sc = e.get('sub_conditions', [])
        sc_str = ' / '.join(f'(s={c["slot"]},f={c["sub_flag"]},v={c["target_value"]})' for c in sc[:3])
        print(f"    [{e.get('idx',0):3d}] {e.get('name','?'):>20s}  type={e.get('mission_type','?'):>3} sub={e.get('sub_type','?'):>3} cnt={e.get('target_count','?')}  {sc_str}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
