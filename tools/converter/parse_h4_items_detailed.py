"""Hero4 R73 — ITM/DAT 26 파일 entry struct 정밀 파싱.

R69 에서 평문 확인. 두 sub-pattern:
    _SD (shop/category lists): `[size:1B][00][nlen:1B][name:EUC-KR][item_id:1B][ff][slot:1B]`
    _DAT (extended item data): `[size:1B][00][nn:1B][nlen:1B][name:EUC-KR][stat_block:varB]`

각 entry 에서 item_id + slot code 추출 (slot 0x6a/0x6b = gender or category).

산출: work/h4/converted/h4_items_detailed.json
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
ITM_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'ITM' / 'DAT'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_items_detailed.json'


def is_korean_pair(b1: int, b2: int) -> bool:
    return 0xa1 <= b1 <= 0xfe and 0xa1 <= b2 <= 0xfe


def parse_sd(data: bytes) -> list[dict]:
    """`_ITM_*_SD` 파싱: shop list with name + item_id + slot byte."""
    entries = []
    i = 0
    while i < len(data) - 5:
        # try: [size][00][nlen][name][id][ff]
        size_field = data[i]
        if data[i+1] != 0:
            i += 1
            continue
        name_len = data[i+2]
        if not (4 <= name_len <= 14 and name_len % 2 == 0):
            i += 1
            continue
        if i + 3 + name_len + 2 > len(data):
            break
        name_bytes = data[i+3:i+3+name_len]
        if not is_korean_pair(name_bytes[0], name_bytes[1]):
            i += 1
            continue
        if data[i+3+name_len+1] != 0xff:
            i += 1
            continue
        item_id = data[i+3+name_len]
        slot = data[i+3+name_len+2] if i+3+name_len+2 < len(data) else None
        try:
            name = name_bytes.decode('euc-kr', errors='replace').replace('\x00', '').strip()
        except Exception:
            i += 1
            continue
        entries.append({
            'offset': hex(i),
            'size_field': size_field,
            'name_len': name_len,
            'name': name,
            'item_id': item_id,
            'slot_byte': slot,
            'slot_hex': f'0x{slot:02x}' if slot is not None else None,
        })
        i += 3 + name_len + 3  # advance past slot byte
    return entries


def parse_dat(data: bytes) -> list[dict]:
    """`_ITM_*_DAT` 파싱: extended item data with stat block.

    Pattern: [size:1B][00][tier:1B][nlen:1B][name:EUC-KR][stat_block:varB]
    tier byte = 0/1/4/8 (chapter or category index).
    """
    entries = []
    i = 0
    while i < len(data) - 5:
        size_field = data[i]
        if data[i+1] != 0:
            i += 1
            continue
        tier = data[i+2]
        name_len = data[i+3]
        if not (4 <= name_len <= 14 and name_len % 2 == 0):
            i += 1
            continue
        if i + 4 + name_len > len(data):
            break
        name_bytes = data[i+4:i+4+name_len]
        if not is_korean_pair(name_bytes[0], name_bytes[1]):
            i += 1
            continue
        try:
            name = name_bytes.decode('euc-kr', errors='replace').replace('\x00', '').strip()
        except Exception:
            i += 1
            continue
        body_start = i + 4 + name_len
        # 다음 entry 시작 — 같은 size_field 또는 비슷한 패턴
        next_i = body_start
        while next_i < len(data) - 5:
            if data[next_i+1] == 0:
                nl2 = data[next_i+3]
                if (4 <= nl2 <= 14 and nl2 % 2 == 0
                        and next_i + 4 + nl2 <= len(data)
                        and is_korean_pair(data[next_i+4], data[next_i+5])):
                    # size_field 도 reasonable 한지 (smaller != next entry mid-stream)
                    if data[next_i] >= 0x16 and data[next_i] <= 0x80:
                        break
            next_i += 1
        else:
            next_i = len(data)
        stats = data[body_start:next_i]
        # Extract first 12 bytes of stat block (typical = price LE16, level/req, atk, def, etc.)
        entries.append({
            'offset': hex(i),
            'size_field': size_field,
            'tier_byte': tier,
            'name_len': name_len,
            'name': name,
            'stat_len': len(stats),
            'stats_bytes': list(stats[:24]),
            'stats_LE16': [stats[j] | (stats[j+1] << 8) for j in range(0, min(24, len(stats)) - 1, 2)],
        })
        i = next_i
    return entries


def main():
    out: dict = {
        'meta': {
            'round': 'R73',
            'date': '2026-05-19',
            'source': str(ITM_DIR.relative_to(ROOT)),
            'pattern_sd': '[size:1B][00][nlen:1B][name:EUC-KR][item_id:1B][ff][slot:1B]',
            'pattern_dat': '[size:1B][00][00][nlen:1B][name:EUC-KR][stat_block:varB]',
        },
        'sd_files': [],
        'dat_files': [],
    }

    total = 0
    for f in sorted(ITM_DIR.glob('_ITM_*_SD')):
        data = f.read_bytes()
        entries = parse_sd(data)
        out['sd_files'].append({
            'file': f.name, 'size': len(data), 'count': len(entries),
            'entries': entries,
        })
        total += len(entries)
        print(f'{f.name}: {len(entries)} entries (SD)')
        if entries:
            slots = sorted({e['slot_byte'] for e in entries if e['slot_byte'] is not None})
            print(f'  slot_bytes: {[f"0x{s:02x}" for s in slots]}')
            for e in entries[:5]:
                print(f"    [{e['offset']:>5}] id={e['item_id']:3} slot={e['slot_hex']} {e['name']!r}")

    for f in sorted(ITM_DIR.glob('_ITM_*_DAT')):
        data = f.read_bytes()
        entries = parse_dat(data)
        out['dat_files'].append({
            'file': f.name, 'size': len(data), 'count': len(entries),
            'entries': entries,
        })
        total += len(entries)
        print(f'{f.name}: {len(entries)} entries (DAT)')
        for e in entries[:3]:
            le16 = e['stats_LE16'][:6]
            print(f"    [{e['offset']:>5}] {e['name']!r:20} stat_len={e['stat_len']} LE16[:6]={le16}")

    out['meta']['total_entries'] = total
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nTotal: {total} item entries → {OUT}')


if __name__ == '__main__':
    main()
