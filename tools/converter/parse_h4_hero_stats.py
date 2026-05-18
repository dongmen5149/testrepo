"""Hero4 R71 — _H_BH (168B) hero stat block 정밀 파싱.

R69 에서 4 entries × 40B 추정으로 부정확했던 layout 을 정밀화.

실제 구조 (2026-05-19):
    [0]      1B    file header (0x26)
    [1:41]   40B   Entry 0: 티르 normal (size_field=0x26, name_len=4)
    [41:81]  40B   Entry 1: 티르 (index=1, size_field=0x26, name_len=4)
    [81:123] 42B   Entry 2: 루레인 normal (size_field=0x28, name_len=6)
    [123:?]  46B   Entry 3: 루레인 (index=3, mode=1, size_field=0x28, name_len=6, +4B trailer)
    + 2B trailing 0

각 entry 헤더 (5B):
    [0] size_field   38 (티르) / 40 (루레인) — 본문 길이 추정
    [1] sep          00
    [2] index        0,1,2,3
    [3] mode         00 (티르 entries) / 01 (루레인 entries)
    [4] name_len     04 (티르) / 06 (루레인)

stats payload (entry length - 5 - name_len bytes):
    여러 byte/LE16 field 가 있지만 정확한 field 매핑은 Ghidra 분석 필요.
    관찰: position 1~2 가 level 후보 (티르 11/6, 루레인 10/5),
          position 14~20 = equip slot ID 후보 (10/20/40 패턴).

산출: work/h4/converted/h4_hero_stats.json
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SRC = ROOT / 'work' / 'h4' / 'decrypted' / 'HDAT' / '_H_BH'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_hero_stats.json'


def main():
    data = SRC.read_bytes()
    assert len(data) == 168, f'unexpected size {len(data)}'

    # 4 entries at known offsets (name search 검증됨)
    entries_meta = [
        (0,  'normal'),
        (40, 'normal'),
        (80, 'hard'),
        (122, 'hard'),
    ]
    # 더 정확한 offset 은 name 위치 검색으로
    name_positions = []
    TIRU = bytes.fromhex('c6bcb8a3')
    LURAN = bytes.fromhex('b7e7b7b9c0ce')
    for i in range(len(data) - 5):
        if data[i:i+4] == TIRU and (i == 0 or data[i-1] != TIRU[3]):
            name_positions.append((i, 4, 'normal' if data[i-2] == 0 else 'hard'))
        elif data[i:i+6] == LURAN:
            name_positions.append((i, 6, 'normal' if data[i-2] != 1 else 'hard'))
    # entries 는 name_pos - 5 부터 다음 entry 까지
    positions = [p[0] - 5 for p in name_positions]

    entries = []
    for idx, start in enumerate(positions):
        end = positions[idx+1] if idx + 1 < len(positions) else len(data)
        e = data[start:end]
        name_len = e[4]
        name = e[5:5+name_len].decode('euc-kr', errors='replace')
        stats = e[5+name_len:]
        # entry trailing zeros 제거 (실 payload)
        payload_end = len(stats)
        while payload_end > 0 and stats[payload_end-1] == 0:
            payload_end -= 1
        # 너무 많이 잘리지 않게 최소 10 byte 유지
        if payload_end < 10:
            payload_end = min(len(stats), 32)
        payload = stats[:payload_end]
        le16 = [stats[j] | (stats[j+1] << 8) for j in range(0, len(stats) - 1, 2)]
        entries.append({
            'entry_index': idx,
            'offset': hex(start),
            'size_field': e[0],
            'index_byte': e[2],
            'mode_byte': e[3],
            'mode_label': 'normal' if e[3] == 0 else 'hard',
            'name_len': name_len,
            'name': name,
            'stats_bytes': list(stats),
            'stats_LE16': le16,
            'stats_payload_hex': payload.hex(),
        })

    catalog = {
        'meta': {
            'source': str(SRC.relative_to(ROOT)),
            'round': 'R71',
            'date': '2026-05-19',
            'file_size': len(data),
            'file_header_byte': data[0],
            'entry_count': len(entries),
        },
        'entries': entries,
        'observations': {
            'heroes': ['티르', '루레인'],
            'mode_field': 'byte[3] of entry header — 0 = 티르 entries, 1 = 루레인 entries',
            'index_field': 'byte[2] of entry header — 0..3 sequential (티르 0/1 + 루레인 2/3)',
            'name_len_field': 'byte[4] — 4 (티르) / 6 (루레인)',
            'size_field': 'byte[0] — 0x26 (티르 38B) / 0x28 (루레인 40B); 본문 길이 추정',
            'level_candidate': 'stats byte[1] 후보 — 티르 11/6, 루레인 10/5 (스토리 진행 단계?)',
            'equip_slot_candidate': 'stats byte[14..20] = 10/20/40 패턴 — 시작 장비 ID 후보',
            'note': '정확한 field 매핑은 Ghidra 분석 필요. 이 파일은 구조만 추출.',
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Parsed {len(entries)} hero entries → {OUT}')
    for e in entries:
        print(f"  [{e['offset']:>6}] {e['name']!r} (idx={e['index_byte']}, mode={e['mode_label']}, "
              f"size={e['size_field']}, name_len={e['name_len']})")


if __name__ == '__main__':
    main()
