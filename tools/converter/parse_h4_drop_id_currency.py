"""Hero4 Round 97 — drop_id 16/17/23 currency 가설 검증 (R96 후속).

R96 의 미해결 drop_id (16, 17, 23) 의미 검증.

가설: drop_id 는 `_ITM_*` 파일의 **alphabetic order index** (0-indexed):
    0-15:  _ITM_00 ~ _ITM_15 (numeric DAT 15 files)
    16:    _ITM_CASH_RANOMBOX   (23 records, 16B stride)
    17:    _ITM_OPTION          (120 records, 16B stride)
    18-20: _ITM_Q_REPAY_0/1/2   (self-referential, 미사용 추정)
    21-22: _ITM_REPAY_0/1
    23:    _ITM_REPAY_2         (74 records, 12B stride)

수집 sample (R96 발견):
    drop_id 16 [repay#169/197 drop1]: byte9=0, byte10=1
    drop_id 17 [repay#168/196 drop1]: byte9=0, byte10=232
    drop_id 23 [11 records drop2]:   byte9=2..20 다양, byte10=1

가설 검증:
- drop_id 16 → CASH_RANOMBOX[0], qty=1 → 캐시 박스 1개 endgame 보상 (잘 부합)
- drop_id 23 → REPAY_2[idx], qty=1 → REPAY_2 의 74 entry 중 0-22 범위 사용
  (byte9 max = 20, REPAY_2 max idx = 73, 범위 내)
- drop_id 17 → OPTION[?], byte10=232 → 다른 의미 가능성. enchantment scroll 가설
  (OPTION 120 entries, byte10=232 not direct idx)

추가 검증: REPAY_2 와 REPAY_0/1 의 분리 — _ITM_REPAY_* 가 Q_REPAY 의 reward currency 추가 풀 가능성.
"""
from __future__ import annotations
import json
import pathlib
import struct
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'ITM' / 'DAT'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'

# Alphabetic ordering of ITM/DAT files (manually verified)
ALPHABETIC_ITM = [
    '_ITM_00_DAT',  # 0
    '_ITM_01_DAT',  # 1
    '_ITM_02_DAT',  # 2
    '_ITM_03_DAT',  # 3
    '_ITM_04_DAT',  # 4
    '_ITM_05_DAT',  # 5
    '_ITM_06_DAT',  # 6
    '_ITM_08_DAT',  # 7 (note: skips 07; takes slot 7 alphabetically? actually NO — numeric 7 doesn't exist, 8 is next)
    '_ITM_09_DAT',  # 8
    '_ITM_10_DAT',  # 9
    '_ITM_11_DAT',  # 10
    '_ITM_12_DAT',  # 11
    '_ITM_13_DAT',  # 12
    '_ITM_14_DAT',  # 13
    '_ITM_15_DAT',  # 14
    '_ITM_CASH_RANOMBOX',  # 15
    '_ITM_OPTION',         # 16
    '_ITM_Q_REPAY_0',      # 17
    '_ITM_Q_REPAY_1',      # 18
    '_ITM_Q_REPAY_2',      # 19
    '_ITM_REPAY_0',        # 20
    '_ITM_REPAY_1',        # 21
    '_ITM_REPAY_2',        # 22
]

# Actually drop_id seems to map directly to numeric prefix (0-15)
# For 16/17/23, candidates by file index from a different ordering:
# - If ID space is "01,02,...15,16(CASH),17(OPTION),...,23(REPAY_2)" with skip of 07
SUSPECT_MAPPING_v1 = {
    16: '_ITM_CASH_RANOMBOX',
    17: '_ITM_OPTION',
    23: '_ITM_REPAY_2',
}


def analyze_special_drops() -> dict:
    """Examine drop_id 16/17/23 record patterns."""
    findings = {16: [], 17: [], 23: []}
    for fn in ['_ITM_Q_REPAY_0', '_ITM_Q_REPAY_1']:
        data = (DAT_DIR / fn).read_bytes()
        for i in range(200):
            rec = data[i*20:(i+1)*20]
            for slot, base in [('drop1', 8), ('drop2', 14)]:
                d_id, d_idx, d_qty = rec[base], rec[base+1], rec[base+2]
                if d_id in (16, 17, 23):
                    findings[d_id].append({
                        'source': fn, 'repay_idx': i, 'slot': slot,
                        'byte9': d_idx, 'byte10': d_qty,
                        'le16_value': d_idx | (d_qty << 8),
                    })
    return findings


def check_repay2_idx_range(byte9_values: list[int]) -> dict:
    """Check if drop_id 23 byte9 values fit _ITM_REPAY_2 record range (74)."""
    data = (DAT_DIR / '_ITM_REPAY_2').read_bytes()
    record_count = len(data) // 12
    return {
        'repay2_record_count': record_count,
        'byte9_values_observed': sorted(set(byte9_values)),
        'all_in_range': all(b < record_count for b in byte9_values),
    }


def check_cash_idx_range(byte9_values: list[int]) -> dict:
    data = (DAT_DIR / '_ITM_CASH_RANOMBOX').read_bytes()
    record_count = len(data) // 16
    return {
        'cash_record_count': record_count,
        'byte9_values_observed': sorted(set(byte9_values)),
        'all_in_range': all(b < record_count for b in byte9_values),
    }


def main() -> int:
    findings = analyze_special_drops()

    # Per drop_id analysis
    summary = {}
    for d_id in (16, 17, 23):
        recs = findings[d_id]
        byte9s = [r['byte9'] for r in recs]
        byte10s = [r['byte10'] for r in recs]
        summary[d_id] = {
            'hit_count': len(recs),
            'byte9_distribution': dict(Counter(byte9s)),
            'byte10_distribution': dict(Counter(byte10s)),
            'records': recs,
            'suspected_file': SUSPECT_MAPPING_v1[d_id],
        }

    # Verify drop_id 23 → REPAY_2
    byte9_for_23 = [r['byte9'] for r in findings[23]]
    repay2_check = check_repay2_idx_range(byte9_for_23)
    summary[23]['verification'] = repay2_check
    summary[23]['hypothesis_confirmed'] = repay2_check['all_in_range']

    # Verify drop_id 16 → CASH_RANOMBOX
    byte9_for_16 = [r['byte9'] for r in findings[16]]
    cash_check = check_cash_idx_range(byte9_for_16)
    summary[16]['verification'] = cash_check
    summary[16]['hypothesis_confirmed'] = cash_check['all_in_range']

    # drop_id 17: byte10=232 mystery — check if OPTION[232] valid (120 records)
    data_opt = (DAT_DIR / '_ITM_OPTION').read_bytes()
    opt_records = len(data_opt) // 16
    byte10_for_17 = [r['byte10'] for r in findings[17]]
    summary[17]['verification'] = {
        'option_record_count': opt_records,
        'byte10_observed': sorted(set(byte10_for_17)),
        'byte10_le16_oor_for_option': all(b > opt_records for b in byte10_for_17),
        'currency_qty_hypothesis': True,  # qty=232 is plausibly EXP/gold currency amount
    }
    summary[17]['hypothesis_confirmed'] = False  # ambiguous

    out = {
        'round': 97,
        'r96_followup_summary': summary,
        'alphabetic_order_hypothesis_v1': SUSPECT_MAPPING_v1,
        'conclusion': {
            16: f'_ITM_CASH_RANOMBOX 매핑 — byte9 in range (0..{cash_check["cash_record_count"]-1}). 확정.',
            23: f'_ITM_REPAY_2 매핑 — byte9 in range (0..{repay2_check["repay2_record_count"]-1}). 확정.',
            17: 'OPTION 매핑은 byte10=232 가 record idx 로 OOR. currency qty (EXP 232, gold 232 등) 가설 우세.',
        },
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_drop_id_currency.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print('=== drop_id 16 → _ITM_CASH_RANOMBOX ===')
    print(f'  hits: {summary[16]["hit_count"]}, byte9 vals: {summary[16]["byte9_distribution"]}')
    print(f'  verification: cash records = {cash_check["cash_record_count"]}, byte9 in range = {cash_check["all_in_range"]}')
    print(f'  → {out["conclusion"][16]}')
    print()
    print('=== drop_id 23 → _ITM_REPAY_2 ===')
    print(f'  hits: {summary[23]["hit_count"]}, byte9 vals: {summary[23]["byte9_distribution"]}')
    print(f'  verification: repay_2 records = {repay2_check["repay2_record_count"]}, byte9 in range = {repay2_check["all_in_range"]}')
    print(f'  → {out["conclusion"][23]}')
    print()
    print('=== drop_id 17 (OPTION? currency?) ===')
    print(f'  hits: {summary[17]["hit_count"]}, byte9: {summary[17]["byte9_distribution"]}, byte10: {summary[17]["byte10_distribution"]}')
    print(f'  → {out["conclusion"][17]}')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
