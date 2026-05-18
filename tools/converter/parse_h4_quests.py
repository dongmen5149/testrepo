"""Hero4 NPC/_QUEST_{0,1}_DAT 평문 파싱 → JSON catalog.

Hero4 Round 70 (2026-05-19). Round 69 에서 복호화 완료 후 평문 entropy 6.1 확인됨.
Hero3 R58 의 quest_dat 패턴 변종:

    Hero3:   [size+2:1B] [00] [name_len:1B] [name:EUC-KR] [body...]
    Hero4:   [size_field:1B] [00 00 00] [name_len:1B] [name:EUC-KR]
             [body: desc_len:1B + EUC-KR description + 0x11/0x0a category marker + ...]

각 entry 의 끝은 다음 entry 시작 (size_field + 0x00 0x00 0x00 + valid name_len) 직전까지.

산출:
    work/h4/converted/h4_quests.json — Hero4 의 모든 quest (name, body, raw_size)
"""
from __future__ import annotations
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
QUEST_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'NPC'
OUT_JSON = ROOT / 'work' / 'h4' / 'converted' / 'h4_quests.json'


def is_entry_start(data: bytes, i: int) -> bool:
    """`[size:1B] [00 00 00] [name_len:1B] [EUC-KR pair...]` 패턴 확인."""
    if i + 7 > len(data):
        return False
    if data[i+1] != 0 or data[i+2] != 0 or data[i+3] != 0:
        return False
    name_len = data[i+4]
    if not (4 <= name_len <= 30):
        return False
    if i + 5 + name_len > len(data):
        return False
    # name 첫 영역에 EUC-KR Korean pair 가 적어도 한 개 (space/digit prefix 도 허용)
    first = data[i+5:i+5+min(8, name_len)]
    has_korean = any(0xa1 <= first[k] <= 0xfe and k+1 < len(first) and 0xa1 <= first[k+1] <= 0xfe
                     for k in range(len(first) - 1))
    return has_korean


def parse_quest_file(path: pathlib.Path) -> list[dict]:
    data = path.read_bytes()
    entries = []
    i = 0
    while i < len(data) - 8:
        if not is_entry_start(data, i):
            i += 1
            continue
        size_field = data[i]
        name_len = data[i+4]
        name_bytes = data[i+5:i+5+name_len]
        try:
            name = name_bytes.decode('euc-kr', errors='replace').replace('\x00', '').strip()
        except Exception:
            i += 1
            continue
        body_start = i + 5 + name_len
        # 다음 entry 시작까지 body
        next_i = body_start
        while next_i < len(data) - 8:
            if is_entry_start(data, next_i):
                break
            next_i += 1
        else:
            next_i = len(data)
        body_bytes = data[body_start:next_i]
        # body 첫 byte = description length (heuristic)
        desc_len_hint = body_bytes[0] if body_bytes else 0
        desc_start = 1 if 0x10 <= desc_len_hint <= 0x60 else 0
        try:
            body_text = body_bytes[desc_start:].decode('euc-kr', errors='replace')
        except Exception:
            body_text = ''
        # 카테고리 marker (`\n메인퀘스트` or `\x11위치:NPC`) 찾기
        category = ''
        if '메인퀘스트' in body_text:
            category = '메인퀘스트'
        elif '\x11' in body_text:
            # \x11 다음 텍스트가 위치:NPC
            idx = body_text.index('\x11')
            tail = body_text[idx+1:]
            # 첫 control byte 까지
            end = len(tail)
            for k, c in enumerate(tail):
                if ord(c) < 0x20 and c not in '\n\t':
                    end = k
                    break
            category = tail[:end].strip()
        # description = body_text 의 첫 control char 까지
        desc = ''
        for k, c in enumerate(body_text):
            if ord(c) < 0x20 and c not in '\n\t':
                desc = body_text[:k]
                break
        else:
            desc = body_text
        desc = desc.strip()

        entries.append({
            'offset': hex(i),
            'size_field': size_field,
            'name': name,
            'description': desc,
            'category': category,
            'raw_bytes': next_i - i,
        })
        i = next_i
    return entries


def main():
    out: dict = {
        'meta': {
            'game': 'Hero4 (영웅서기4)',
            'round': 'R70',
            'date': '2026-05-19',
            'source_files': ['work/h4/decrypted/NPC/_QUEST_0_DAT', 'work/h4/decrypted/NPC/_QUEST_1_DAT'],
            'pattern': 'Hero3 quest_dat 변종: [size:1B][00 00 00][name_len:1B][name:EUC-KR][body]',
        },
        'files': {},
    }

    total_quests = 0
    for fn in ['_QUEST_0_DAT', '_QUEST_1_DAT']:
        p = QUEST_DIR / fn
        if not p.exists():
            print(f'MISSING: {p}', file=sys.stderr)
            continue
        entries = parse_quest_file(p)
        out['files'][fn] = {
            'size': p.stat().st_size,
            'count': len(entries),
            'quests': entries,
        }
        total_quests += len(entries)
        print(f'\n=== {fn}: {len(entries)} quests ===')
        for e in entries[:5]:
            print(f'  [{e["offset"]:>6}] {e["name"]!r}  ({e["category"]!r})')
            print(f'    → {e["description"][:80]!r}')

    out['meta']['total_quests'] = total_quests
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nTotal: {total_quests} quests → {OUT_JSON}')


if __name__ == '__main__':
    main()
