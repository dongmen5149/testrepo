"""Hero4 R72 — E/_BSDAT_{0,1,2} (boss script) + E/_ESDAT_{0,1,2} (event script) 파싱.

R69 에서 J@IWO8N7 + mx_des_decrypt 로 평문 확인. 6 파일 = 3 BSDAT (각 2008B) + 3 ESDAT (각 13168B).

구조:
    BSDAT entry: [size:1B][00][name_len:1B][name:EUC-KR][body]
    ESDAT entry: [size:1B][00][00][name_len:1B][name:EUC-KR][body]  (quest_dat 와 동일)

body 는 SCN bytecode 유사 (opcode + immediate + ...). 정확한 dispatch 는 추후.

산출: work/h4/converted/h4_event_scripts.json
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
E_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'E'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_event_scripts.json'


def is_bsdat_entry(data: bytes, i: int) -> bool:
    """BSDAT: `[size:1B][00][name_len:1B][EUC-KR pair...]`"""
    if i + 6 > len(data):
        return False
    if data[i+1] != 0:
        return False
    name_len = data[i+2]
    if not (3 <= name_len <= 30):
        return False
    if i + 3 + name_len > len(data):
        return False
    # 첫 영역에 EUC-KR Korean pair
    first = data[i+3:i+3+min(6, name_len)]
    return any(0xa1 <= first[k] <= 0xfe and k+1 < len(first) and 0xa1 <= first[k+1] <= 0xfe
               for k in range(len(first) - 1))


def is_esdat_entry(data: bytes, i: int) -> bool:
    """ESDAT: `[size:1B][00][seq:1B][name_len:1B][EUC-KR pair or space...]`

    seq byte = sequential index (0,1,2,..) — 같은 entry name 의 variant 인덱스.
    """
    if i + 7 > len(data):
        return False
    if data[i+1] != 0:
        return False
    # data[i+2] = seq byte (0-255, variant index)
    name_len = data[i+3]
    if not (3 <= name_len <= 30):
        return False
    if i + 4 + name_len > len(data):
        return False
    first = data[i+4:i+4+min(6, name_len)]
    return any(0xa1 <= first[k] <= 0xfe and k+1 < len(first) and 0xa1 <= first[k+1] <= 0xfe
               for k in range(len(first) - 1))


def parse_with_detector(data: bytes, detector, header_size: int, name_off: int) -> list[dict]:
    entries = []
    i = 0
    while i < len(data) - 6:
        if not detector(data, i):
            i += 1
            continue
        size_field = data[i]
        name_len = data[i + header_size - 1]
        name_bytes = data[i+name_off:i+name_off+name_len]
        try:
            name = name_bytes.decode('euc-kr', errors='replace').replace('\x00', '').strip()
        except Exception:
            i += 1
            continue
        body_start = i + name_off + name_len
        # 다음 entry start 까지
        next_i = body_start
        while next_i < len(data) - 6:
            if detector(data, next_i):
                break
            next_i += 1
        else:
            next_i = len(data)
        body_bytes = data[body_start:next_i]
        # body 에서 EUC-KR run 검색 (대사/설명 추출)
        kor_samples = []
        j = 0
        while j < len(body_bytes) - 1 and len(kor_samples) < 4:
            if 0xa1 <= body_bytes[j] <= 0xfe and 0xa1 <= body_bytes[j+1] <= 0xfe:
                start = j
                while j < len(body_bytes) - 1 and 0xa1 <= body_bytes[j] <= 0xfe and 0xa1 <= body_bytes[j+1] <= 0xfe:
                    j += 2
                run = body_bytes[start:j]
                if len(run) >= 4:
                    try:
                        kor_samples.append(run.decode('euc-kr', errors='replace'))
                    except Exception:
                        pass
            else:
                j += 1
        entries.append({
            'offset': hex(i),
            'size_field': size_field,
            'name_len': name_len,
            'name': name,
            'body_size': next_i - body_start,
            'kor_samples': kor_samples,
        })
        i = next_i
    return entries


def parse_bsdat(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    entries = parse_with_detector(data, is_bsdat_entry, header_size=3, name_off=3)
    return {'file': path.name, 'size': len(data), 'count': len(entries), 'entries': entries}


def parse_esdat(path: pathlib.Path) -> dict:
    data = path.read_bytes()
    entries = parse_with_detector(data, is_esdat_entry, header_size=4, name_off=4)
    return {'file': path.name, 'size': len(data), 'count': len(entries), 'entries': entries}


def main():
    out = {
        'meta': {
            'round': 'R72',
            'date': '2026-05-19',
            'source': str(E_DIR.relative_to(ROOT)),
            'pattern_bsdat': '[size:1B][00][name_len:1B][name:EUC-KR][body]',
            'pattern_esdat': '[size:1B][00][00][name_len:1B][name:EUC-KR][body]',
        },
        'bsdat': [],
        'esdat': [],
    }
    total = 0
    for fn in ['_BSDAT_0', '_BSDAT_1', '_BSDAT_2']:
        p = E_DIR / fn
        if p.exists():
            r = parse_bsdat(p)
            out['bsdat'].append(r)
            total += r['count']
            print(f'{fn}: {r["count"]} entries')
            for e in r['entries'][:3]:
                print(f"  [{e['offset']:>6}] {e['name']!r}  body={e['body_size']}B")
                if e['kor_samples']:
                    print(f"      → {e['kor_samples']}")
    for fn in ['_ESDAT_0', '_ESDAT_1', '_ESDAT_2']:
        p = E_DIR / fn
        if p.exists():
            r = parse_esdat(p)
            out['esdat'].append(r)
            total += r['count']
            print(f'{fn}: {r["count"]} entries')
            for e in r['entries'][:3]:
                print(f"  [{e['offset']:>6}] {e['name']!r}  body={e['body_size']}B")
                if e['kor_samples']:
                    print(f"      → {e['kor_samples']}")
    out['meta']['total_entries'] = total
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nTotal: {total} entries → {OUT}')


if __name__ == '__main__':
    main()
