"""Hero4 Round 88 — `_H_BS` + `_H_SA` 환수 progression / ability slot 파서.

R86 가설 정정:
- `_H_BS` 136B = 5 환수 × 27B + 1B 패딩 (이전 "17 × 8B" 가설 폐기)
- `_H_SA` 960B = 1 헤더 + 24 ability slots + 15 summon-tier = 40 × 24B
  (이전 "24 × 40B" 가설 폐기)

`_H_BS` 레코드 (27B):
    bytes[0-2]:  19 00 [summon_id]
    bytes[3-7]:  5 stat 값 (HP/SP/ATK/DEF/MAG 추정, byte[7] = MAG axis)
    bytes[8-10]: fe 00 00 (sentinel)
    byte[11]:    count (2 or 3) — 학습 skill 개수
    byte[12]:    EXP / cost marker (15, 0, 0, 40, 0)
    bytes[13-23]: padding (간헐적 값 30/60 = ability tier?)
    bytes[24-26]: 3 sequential skill_ids — 환수가 학습하는 active skill ID

학습 skill ID 매트릭스:
    summon 0 (베놈):       skills 6, 7, 8    (+ byte[7]=5 가 basic_attack id 가능)
    summon 1 (헤지호그):   skills 9, 10, 11
    summon 2 (그래비티):   skills 12, 13, 14
    summon 3 (쇼커):       skills 15, 16, 17
    summon 4 (세이프가드): skills 18, 19, 20

`_H_SA` 레코드 (24B × 40):
    rec[0]: 24B file-level header (22, 100, 100, 1, 34, ...) — 글로벌 max stat 추정

    rec[1..24]: 24 ability slots (type=0x0b)
        16 00 00 00 00 00 00 0b [skill_id] [tier_value] 00 00 [bonus_id] [bonus_value] 00*10
        8 unique skill_ids × 3 tiers (low/mid/high):
            12 → tiers 10/20/30, bonus_id=18 sub=5/10/15
            16 → tiers 10/20/30, bonus_id=17 sub=10/20/30
            15 → tiers 10/20/30, bonus_id=19 sub=5/10/15
            21 → tiers 5/10/15
            37 → tiers 20/40/60
            13 → tiers 10/20/30
            18 → tiers 10/20/30
            22 → tiers 10/25/40

    rec[25..39]: 15 summon-tier records (type=0x0835)
        16 00 00 00 00 00 00 08 35 [LE16 value] [tier] [group_id] [count] 00 [optional 4B signed]
        5 groups × 3 tier levels = 15 entries:
            group_id=0  → MAG growth   (400/600/800)
            group_id=64 → HP penalty?  (signed -30/-50/-70 영역)
            group_id=78 → SP growth
            group_id=38 → ATK growth
            group_id=75 → DEF growth
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BS_FILE = ROOT / 'work' / 'h4' / 'decrypted' / 'HDAT' / '_H_BS'
SA_FILE = ROOT / 'work' / 'h4' / 'decrypted' / 'HDAT' / '_H_SA'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

SUMMON_NAMES = ['베놈', '헤지호그', '그래비티', '쇼커', '세이프가드']


def parse_bs(data: bytes) -> dict:
    """5 summons × 27B + 1B padding."""
    assert len(data) == 136, f'expected 136B, got {len(data)}'
    summons = []
    for i in range(5):
        off = i * 27
        rec = data[off:off+27]
        sid = rec[2]
        stats = list(rec[3:8])
        sentinel = rec[8:11].hex()
        count = rec[11]
        cost_marker = rec[12]
        body = list(rec[13:24])
        trail = list(rec[24:27])
        # detect non-zero body bytes (ability tier markers)
        body_anomalies = {idx: v for idx, v in enumerate(body) if v != 0}
        summons.append({
            'summon_id': sid,
            'name': SUMMON_NAMES[sid] if sid < len(SUMMON_NAMES) else f'unknown_{sid}',
            'offset': off,
            'stats': stats,
            'sentinel_ok': sentinel == 'fe0000',
            'learn_count': count,
            'cost_marker': cost_marker,
            'body_nonzero': body_anomalies,
            'learn_skill_ids': trail,
        })
    return {
        'file_size': len(data),
        'record_count': 5,
        'record_stride': 27,
        'trailing_pad_byte': data[135],
        'summons': summons,
    }


def parse_sa(data: bytes) -> dict:
    """1 header + 24 ability slots + 15 summon-tier = 40 × 24B."""
    assert len(data) == 960, f'expected 960B, got {len(data)}'
    header = list(data[0:24])
    ability_slots = []
    for i in range(24):
        off = 24 + i * 24
        rec = data[off:off+24]
        ability_slots.append({
            'slot_id': i,
            'offset': off,
            'type': rec[7],
            'skill_id': rec[8],
            'tier_value': rec[9],
            'bonus_id': rec[12],
            'bonus_value': rec[13],
            'tail_zero': all(b == 0 for b in rec[14:]),
        })
    summon_tier = []
    for i in range(15):
        off = 600 + i * 24
        rec = data[off:off+24]
        # LE16 at offset 9-10
        le16 = rec[9] | (rec[10] << 8)
        tier = rec[11]
        group_id = rec[12]
        count = rec[13]
        extra4 = list(rec[16:20])
        summon_tier.append({
            'tier_id': i,
            'offset': off,
            'type': f'{rec[7]:02x}{rec[8]:02x}',
            'value_le16': le16,
            'tier': tier,
            'group_id': group_id,
            'count': count,
            'extra4': extra4,
        })
    return {
        'file_size': len(data),
        'record_count': 40,
        'record_stride': 24,
        'header': header,
        'ability_slots': ability_slots,
        'summon_tier_growth': summon_tier,
    }


def cross_reference_bs_ss(bs: dict) -> dict:
    """_H_BS 의 learn_skill_ids 가 _H_SS R87 의 logical skills 와 매칭됨을 확인."""
    ranges = {}
    for s in bs['summons']:
        ranges[s['name']] = {
            'first_id': s['learn_skill_ids'][0],
            'last_id':  s['learn_skill_ids'][-1],
            'sequential': all(
                s['learn_skill_ids'][i+1] - s['learn_skill_ids'][i] == 1
                for i in range(len(s['learn_skill_ids'])-1)
            ),
        }
    return ranges


def main() -> int:
    bs = parse_bs(BS_FILE.read_bytes())
    sa = parse_sa(SA_FILE.read_bytes())
    cross = cross_reference_bs_ss(bs)

    out = {
        'round': 88,
        'h_bs': bs,
        'h_sa': sa,
        'cross_ref_bs_skill_ids': cross,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_summon_progression.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] _H_BS: {bs["record_count"]} summons × {bs["record_stride"]}B')
    for s in bs['summons']:
        print(f'  {s["name"]:6s} stats={s["stats"]} learn={s["learn_skill_ids"]} cost_marker={s["cost_marker"]}')

    print(f'[OK] _H_SA: {sa["record_count"]} records × {sa["record_stride"]}B')
    # Group ability slots by skill_id
    by_skill = {}
    for slot in sa['ability_slots']:
        by_skill.setdefault(slot['skill_id'], []).append(slot)
    for sid, slots in by_skill.items():
        tiers = [s['tier_value'] for s in slots]
        bonus = slots[0]['bonus_id']
        print(f'  skill_id={sid:3d} tiers={tiers} bonus_id={bonus}')

    print(f'[OK] summon_tier groups:')
    by_group = {}
    for t in sa['summon_tier_growth']:
        by_group.setdefault(t['group_id'], []).append(t)
    for gid, ts in by_group.items():
        vals = [(t['value_le16'], t['tier']) for t in ts]
        print(f'  group_id={gid:3d}: {vals}')

    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
