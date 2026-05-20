"""Hero4 Round 105 — drop_id 17 byte10=232 정확한 해석 (R97 정정).

R97 의 "byte10=232" 가설을 raw record 재검토로 정정.

발견 사실: drop_id 17 의 4 entries 가 모두 동일 raw bytes:
    `12000d008e0701001100e8030000ff0000000000`  (or `8cc60200` for gold file)

bytes[8-13] = [17, 0, 232, 3, 0, 0]

**R97 정정**:
    R97: byte[10]=232 (qty 232 으로 ambiguous 해석)
    R105: **bytes[10-11] LE16 = 0x03e8 = 1000** (qty 1000)

즉 drop_id 17 은 큰 qty (>255) 보상이므로 byte[10-11] 을 LE16 으로 사용하는
**variable-width qty field** 임이 확인됨.

이는 다른 drop_id (qty <= 255) 들과 동일 record layout 이지만 큰 qty 값이
LE16 으로 자연스럽게 들어가는 backward-compatible format.

drop_id 17 = `_ITM_OPTION` (alphabetic order index 유지) + **qty=1000**
→ endgame achievement (repay#168/196) 의 OPTION enchantment scroll/token **1000개** 보상.

대조 (qty < 256 인 drop_id 들):
- ITM_12 가면 qty=1 (단일 quest item)
- ITM_08 제련석 qty=5
- ITM_13 네트워크전용 qty=64 / 118 (단일 item 대량 보상)
- ITM_15 뇌격 qty=8 (환수 quest reward)
- drop_id 17 OPTION qty=**1000** (endgame 대량 보상)
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'ITM' / 'DAT'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def reread_drop_id_17() -> list[dict]:
    """drop_id 17 entries 의 byte field 재해석."""
    findings = []
    for fn in ['_ITM_Q_REPAY_0', '_ITM_Q_REPAY_1']:
        data = (DAT_DIR / fn).read_bytes()
        for i in range(200):
            rec = data[i*20:(i+1)*20]
            if rec[8] != 17:
                continue
            le16_qty_10_11 = rec[10] | (rec[11] << 8)
            findings.append({
                'source': fn,
                'repay_idx': i,
                'raw_bytes_8_13': list(rec[8:14]),
                'drop_id': rec[8],
                'byte_9_item_idx': rec[9],
                'r97_interpretation': {
                    'byte_10_as_qty': rec[10],
                    'note': 'AMBIGUOUS - qty 232 doesn\'t fit OPTION pool (120 records)'
                },
                'r105_interpretation': {
                    'bytes_10_11_le16_qty': le16_qty_10_11,
                    'note': f'qty {le16_qty_10_11} (=0x{le16_qty_10_11:04x}) of OPTION pool item'
                },
            })
    return findings


def main() -> int:
    findings = reread_drop_id_17()

    out = {
        'round': 105,
        'r97_followup': 'drop_id 17 byte10=232 ambiguity 정정',
        'correction': {
            'r97_claim': 'byte[10] alone = 232, ambiguous qty/idx',
            'r105_finding': 'bytes[10-11] LE16 = 0x03e8 = 1000 = qty (variable-width qty field)',
            'evidence': '4/4 occurrences identical bytes[10-13] = [232, 3, 0, 0] = LE16 1000',
        },
        'drop_id_17_records': findings,
        'record_format_revised': {
            'bytes_8': 'drop_id (ITM_file alphabetic order index)',
            'bytes_9': 'item_idx (item within file)',
            'bytes_10_11_le16': 'qty (1-65535, variable-width)',
            'bytes_12_13': 'reserved / padding',
        },
        'qty_examples_revisited': {
            'small_qty_byte_10_only': {
                'ITM_12 가면 (quest)': 1,
                'ITM_08 제련석 (자원)': 5,
                'ITM_15 뇌격 (환수)': 8,
                'ITM_13 네트워크전용 (consumable)': '64 / 118 (대량)',
            },
            'large_qty_le16': {
                'drop_id 17 OPTION (endgame)': 1000,
            },
        },
        'drop_id_17_endgame_interpretation': (
            'repay#168/196 = endgame achievement 의 OPTION 강화 scroll 1000개 보상. '
            '대량 currency-style reward.'
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / 'h4_drop_id_17_fix.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'=== R97 정정: drop_id 17 byte field 재해석 ===')
    print()
    print(f'  R97 가설: byte[10] = 232 (qty/idx ambiguous)')
    print(f'  R105 확정: bytes[10-11] LE16 = 0x03e8 = 1000 (variable-width qty)')
    print()
    print(f'=== drop_id 17 records (모두 동일) ===')
    for f in findings:
        print(f'  {f["source"]} #{f["repay_idx"]}: raw[8-13]={f["raw_bytes_8_13"]}, LE16 qty={f["r105_interpretation"]["bytes_10_11_le16_qty"]}')
    print()
    print('endgame achievement reward = OPTION enchantment 1000개')
    print()
    print(f'[WRITE] {out_path.relative_to(ROOT)} ({out_path.stat().st_size} B)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
