"""Hero4 Round 96 — Q_REPAY drop_id 의미 검증 (R90 후속).

R90 의 Q_REPAY_0/1 20B record 의 byte[8-16] drop slot 의 의미를 ITM 파일과 cross-ref.

Record layout (R90 확장):
    bytes[0-7]:  size_field(0x12) + sub(0x0e) + LE32 reward
    bytes[8-10]: drop slot 1 = [ITM_file_id:1B][item_idx:1B][qty:1B]
    bytes[11-13]: 0 padding
    bytes[14-16]: drop slot 2 (보통 [0xff,0,0] = empty)
    bytes[17-19]: 0 padding

ITM file 매핑:
    drop_id 0-6  → _ITM_00 ~ _ITM_06 (7 weapon classes + SD 보완)
    drop_id 8-15 → _ITM_08 ~ _ITM_15 (소비/장비/특수)
    drop_id 15   → _ITM_15 (환수 catalog, R92)

item_idx 는 ITM_XX_DAT entries 인덱스 (0-based).
out-of-range (item_idx > DAT.count-1) 일 때 _ITM_X_SD subdata 와 결합 가능성.
"""
from __future__ import annotations
import json
import pathlib
import struct
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'ITM' / 'DAT'
ITEMS_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_items_detailed.json'
QRM_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_quest_reward_map.json'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def load_item_index() -> dict:
    """Index ITM_XX_DAT entries by file number."""
    its = json.loads(ITEMS_JSON.read_text(encoding='utf-8'))
    out = {}
    for f in its['dat_files']:
        fn = f['file']
        if fn.startswith('_ITM_') and fn.endswith('_DAT') and fn[5:7].isdigit():
            n = int(fn[5:7])
            out[n] = {
                'file': fn,
                'count': f['count'],
                'entries': [e.get('name', '') for e in f.get('entries', [])],
            }
    # also SD count
    for f in its.get('sd_files', []):
        fn = f.get('file', '')
        if fn.startswith('_ITM_') and fn.endswith('_SD') and fn[5:6].isdigit():
            n = int(fn[5:6])
            if n in out:
                out[n]['sd_count'] = f['count']
    return out


def parse_drops(itm_idx: dict) -> dict:
    """Parse Q_REPAY_0 + Q_REPAY_1 drop slots."""
    all_drops = []
    drop_id_count = Counter()
    resolved_count = 0
    oor_count = 0
    empty_drop2_count = 0

    qrm = json.loads(QRM_JSON.read_text(encoding='utf-8'))
    qname_by_idx = {m['idx']: m['quest_name'] for m in qrm['quest_idx_to_reward']}

    for fn in ['_ITM_Q_REPAY_0', '_ITM_Q_REPAY_1']:
        data = (DAT_DIR / fn).read_bytes()
        for i in range(200):
            rec = data[i*20:(i+1)*20]
            drop1 = (rec[8], rec[9], rec[10])
            drop2 = (rec[14], rec[15], rec[16])
            if drop1[0] == 0xff or drop1[0] == 0:
                continue
            d_id, d_idx, d_qty = drop1
            info = {
                'source': fn,
                'repay_idx': i,
                'quest_name': qname_by_idx.get(i),
                'drop1': {'itm_id': d_id, 'item_idx': d_idx, 'qty': d_qty},
                'drop2': None,
            }
            if drop2[0] != 0xff and drop2[0] != 0:
                info['drop2'] = {'itm_id': drop2[0], 'item_idx': drop2[1], 'qty': drop2[2]}
            else:
                empty_drop2_count += 1
            # Resolve item name
            for slot, d in [('drop1', drop1), ('drop2', drop2)]:
                if d[0] == 0xff or d[0] == 0:
                    continue
                target = itm_idx.get(d[0])
                if target is None:
                    info[slot]['resolved_name'] = None
                    info[slot]['resolved_file'] = f'UNKNOWN_itm_{d[0]}'
                    continue
                info[slot]['resolved_file'] = target['file']
                info[slot]['dat_count'] = target['count']
                info[slot]['sd_count'] = target.get('sd_count', 0)
                if d[1] < target['count']:
                    info[slot]['resolved_name'] = target['entries'][d[1]]
                    info[slot]['source_section'] = 'DAT'
                    resolved_count += 1
                else:
                    # out-of-range — probably SD subdata
                    info[slot]['resolved_name'] = None
                    info[slot]['source_section'] = 'SD_or_OOR'
                    sd_count = target.get('sd_count', 0)
                    sd_idx = d[1] - target['count']
                    if sd_idx < sd_count:
                        info[slot]['source_section'] = f'SD[{sd_idx}]'
                    else:
                        oor_count += 1
            drop_id_count[d_id] += 1
            all_drops.append(info)
    return {
        'drop_records': all_drops,
        'drop_id_distribution': dict(drop_id_count),
        'total_records': len(all_drops),
        'resolved_in_DAT': resolved_count,
        'true_out_of_range': oor_count,
        'empty_drop2_count': empty_drop2_count,
    }


def main() -> int:
    itm_idx = load_item_index()
    result = parse_drops(itm_idx)

    out = {
        'round': 96,
        'meta': {
            'total_drop_records': result['total_records'],
            'resolved_in_DAT': result['resolved_in_DAT'],
            'requires_SD_lookup': result['total_records'] + (
                sum(1 for r in result['drop_records'] if r.get('drop2'))
            ) - result['resolved_in_DAT'] - result['true_out_of_range'],
            'true_out_of_range': result['true_out_of_range'],
            'drop_id_distribution': result['drop_id_distribution'],
        },
        'itm_file_counts': {
            f'_ITM_{n:02d}': {'dat_count': v['count'], 'sd_count': v.get('sd_count', 0)}
            for n, v in sorted(itm_idx.items())
        },
        'drop_records': result['drop_records'],
        'r90_followup_findings': {
            'drop_slot_format': 'byte[8]=ITM_file_id, byte[9]=item_idx, byte[10]=qty',
            'two_slots_per_record': 'drop1 at bytes[8-10], drop2 at bytes[14-16]',
            'common_drop_ids': 'ITM_12 가 가장 빈번 (각종 quest item: 가면/단열복 등)',
            'summon_drop': 'ITM_15 = R92 환수 catalog — quest 보상으로 환수 획득 가능',
            'sd_extension': 'item_idx > DAT.count 일 때 _ITM_X_SD subdata 영역 (DAT count 가산)',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_q_repay_drops.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'[OK] Total drop records: {result["total_records"]}')
    print(f'  resolved in DAT: {result["resolved_in_DAT"]}')
    print(f'  true out-of-range (after SD check): {result["true_out_of_range"]}')
    print(f'  drop_id distribution: {result["drop_id_distribution"]}')
    print()
    print('=== Sample resolved drops ===')
    for r in result['drop_records'][:15]:
        n = r['drop1'].get('resolved_name', '?')
        section = r['drop1'].get('source_section', '?')
        print(f'  repay#{r["repay_idx"]:3d} [{r["source"][-2:]}] {(r.get("quest_name") or "")[:18]:18s} '
              f'→ {r["drop1"]["resolved_file"]} item[{r["drop1"]["item_idx"]}] '
              f'={n!r} qty={r["drop1"]["qty"]} [{section}]')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
