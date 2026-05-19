"""Round 82 — Hero4 ITM/_ITEMDROP + BASIC_SM_DAT + _ITM_SD0/1/2 정밀.

이 파일들은 DES 암호화되지 않은 평문. 트랙 C 정리.

산출: work/h4/converted/h4_itemdrop_sm.json
"""
from __future__ import annotations
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[2]
ITM = ROOT / 'work' / 'h4' / 'extracted' / 'ITM'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_itemdrop_sm.json'


def parse_itemdrop(data: bytes) -> list[dict]:
    """9 × 8B records. [type=0x06][00][slot0..slot5] with 0xff = empty."""
    records = []
    for i in range(0, len(data), 8):
        rec = data[i:i+8]
        if len(rec) < 8: break
        slots = list(rec[2:])
        used = [s for s in slots if s != 0xff]
        records.append({
            'idx': i // 8,
            'type_byte': rec[0],
            'reserved': rec[1],
            'slots_raw': slots,
            'slots_used_count': len(used),
            'unique_items': sorted(set(used)),
        })
    return records


def parse_basic_sm(data: bytes) -> list[dict]:
    """5 × 44B records. byte[0]=0x2a marker, byte[2]=id."""
    records = []
    for i in range(0, len(data), 44):
        rec = data[i:i+44]
        if len(rec) < 44 or rec[0] != 0x2a: break
        records.append({
            'idx': i // 44,
            'marker': hex(rec[0]),
            'id': rec[2],
            'first8': rec[:8].hex(),
            'middle': rec[8:32].hex(),
            'tail': rec[32:].hex(),
            'stat_block_4_8': list(rec[4:8]),
        })
    return records


def parse_sd(data: bytes) -> list[dict]:
    """SD shop catalog. [size:1B][00][nlen:1B][name:EUC-KR][rest...]"""
    entries = []
    i = 0
    while i < len(data) - 4:
        if data[i+1] == 0 and 3 <= data[i+2] <= 20:
            nlen = data[i+2]
            if i + 3 + nlen <= len(data):
                try:
                    name = data[i+3:i+3+nlen].decode('euc-kr', errors='replace')
                    # entry's actual end: search next valid header or end
                    j = i + 3 + nlen
                    next_entry_start = None
                    for k in range(j, len(data) - 4):
                        if data[k+1] == 0 and 3 <= data[k+2] <= 20:
                            # try decode as KR
                            try:
                                cand_nlen = data[k+2]
                                cand_name = data[k+3:k+3+cand_nlen]
                                if any(0xa1 <= cand_name[m] <= 0xfe for m in range(min(2, len(cand_name)))):
                                    next_entry_start = k
                                    break
                            except: pass
                    if next_entry_start is None: next_entry_start = len(data)
                    entries.append({
                        'offset': i,
                        'size_field': data[i],
                        'nlen': nlen,
                        'name': name,
                        'entry_byte_len': next_entry_start - i,
                        'tail_first8': data[i+3+nlen:i+3+nlen+8].hex(),
                    })
                    i = next_entry_start
                    continue
                except Exception:
                    pass
        i += 1
    return entries


def main():
    out = {
        'meta': {
            'round': 'R82',
            'date': '2026-05-19',
            'source': 'work/h4/extracted/ITM (모두 plaintext, DES 미사용)',
        },
        'itemdrop': {},
        'basic_sm_dat': {},
        'sd': {},
    }

    # _ITEMDROP
    data = (ITM/'_ITEMDROP').read_bytes()
    recs = parse_itemdrop(data)
    out['itemdrop'] = {'file_size': len(data), 'records': recs,
                      'hypothesis': '9 × 8B drop tables (slot[0..5], 0xff=empty). Progressive item indices (20→25) = floor/area별 drop pool'}

    # BASIC_SM_DAT
    data = (ITM/'BASIC_SM_DAT').read_bytes()
    recs = parse_basic_sm(data)
    out['basic_sm_dat'] = {'file_size': len(data), 'records': recs,
                           'hypothesis': '5 × 44B records (0x2a marker). 추정: 5 시스템 메뉴/상점 또는 5 기본 캐릭터 프로필'}

    # SD shops
    for fn in ['_ITM_SD0', '_ITM_SD1', '_ITM_SD2']:
        data = (ITM/fn).read_bytes()
        entries = parse_sd(data)
        out['sd'][fn] = {'file_size': len(data), 'entry_count': len(entries), 'entries': entries[:30]}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"=== _ITEMDROP ({out['itemdrop']['file_size']}B, 9 records) ===")
    for r in out['itemdrop']['records']:
        print(f"  rec{r['idx']}: slots={r['slots_raw']} unique_items={r['unique_items']}")

    print(f"\n=== BASIC_SM_DAT ({out['basic_sm_dat']['file_size']}B, 5 records) ===")
    for r in out['basic_sm_dat']['records']:
        print(f"  rec{r['idx']} id={r['id']}: stat[4-8]={r['stat_block_4_8']}")

    print(f"\n=== _ITM_SD0/1/2 entry counts ===")
    for fn, info in out['sd'].items():
        print(f"  {fn}: {info['entry_count']} entries  first names: {[e['name'] for e in info['entries'][:5]]}")

    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
