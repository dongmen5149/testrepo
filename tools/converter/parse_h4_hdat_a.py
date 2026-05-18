"""Hero4 HDAT Group A (Round 69 decoded) entry layout 분석.

Round 68 에서 SCN 동일 DES 키 (J@IWO8N7) + mx_des_decrypt 로 복호화 완료.
이 모듈은 복호화 결과 8 파일의 entry layout 을 구조적으로 추출:

    _H_BH (168B)    Battle Hero base info (4 heroes)
    _H_BS (136B)    Battle Skill / Stats (numeric)
    _H_SA (960B)    Shop Alpha (item ids + prices)
    _H_SS (1624B)   Shop Skills (skill names + costs)
    _H_S000 (1232B) Skill set 0 — 대검/양손검 (Tír)
    _H_S001 (1176B) Skill set 1 — 사격/더블건
    _H_S002 (1184B) Skill set 2 — 대검/마검 (variant)
    _H_S003 (1240B) Skill set 3 — 단도/마법

각 파일은 `[count:1B] [reserved:1-3B] [entry × N]` 패턴 추정.
entry 시작에 `[size+2:1B] [name_len:1B] [name:EUC-KR]` (Hero3 enemy_dat 동일 패턴).
"""
from __future__ import annotations
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
HDAT_DIR = ROOT / 'work' / 'h4' / 'decrypted' / 'HDAT'
OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def find_korean_runs(data: bytes, min_len: int = 4) -> list[tuple[int, int, str]]:
    """모든 EUC-KR Korean run 의 (offset, length, text) 리스트."""
    runs = []
    i = 0
    while i < len(data) - 1:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
            start = i
            while i < len(data) - 1 and 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i+1] <= 0xfe:
                i += 2
            if i - start >= min_len:
                try:
                    s = data[start:i].decode('euc-kr', errors='replace')
                    runs.append((start, i - start, s))
                except Exception:
                    pass
        else:
            i += 1
    return runs


def parse_entries_by_name_marker(data: bytes) -> list[dict]:
    """Hero3 enemy/boss_dat 패턴: `[size+2:1B] [00] [name_len:1B] [name:EUC-KR]`.

    각 entry 의 시작은 size byte + 00 (separator) + name_len + EUC-KR text.
    스캔하며 모든 entry 후보 추출.
    """
    entries = []
    i = 0
    # Skip 1B count + reserved if present (heuristic: data[1]==0)
    if len(data) >= 4 and data[1] == 0:
        i = 0  # entry 가 byte 0 부터 시작할 수도

    while i < len(data) - 3:
        # entry candidate: data[i] = size+2, data[i+1] = 0 (or other), data[i+2] = name_len
        size_field = data[i]
        sep = data[i+1]
        name_len = data[i+2]
        if (3 <= name_len <= 40
                and i + 3 + name_len <= len(data)
                and all(0xa1 <= data[i+3+k] <= 0xfe for k in range(min(name_len, 4)))
                and name_len % 2 == 0):
            name_bytes = data[i+3:i+3+name_len]
            try:
                name = name_bytes.decode('euc-kr', errors='replace')
            except Exception:
                i += 1
                continue
            total = size_field + 2  # Hero3 pattern (size + 2 includes header)
            if total < name_len + 3 or i + total > len(data):
                total = name_len + 3 + 16  # fallback
            entries.append({
                'offset': i,
                'size_field': size_field,
                'sep': sep,
                'name_len': name_len,
                'name': name,
                'total_estimate': total,
            })
            i += max(total, name_len + 3)
        else:
            i += 1
    return entries


def analyze(file_path: pathlib.Path) -> dict:
    data = file_path.read_bytes()
    name = file_path.name
    header = list(data[:8])
    korean = find_korean_runs(data, min_len=4)
    entries = parse_entries_by_name_marker(data)
    # Stride 추정: 두 entry 사이 거리
    strides = []
    for j in range(1, len(entries)):
        strides.append(entries[j]['offset'] - entries[j-1]['offset'])

    return {
        'file': name,
        'size': len(data),
        'header_8B': header,
        'korean_run_count': len(korean),
        'entries_found': len(entries),
        'entries': entries[:25],  # 처음 25 entries만
        'strides': strides[:25],
        'stride_summary': {
            'min': min(strides) if strides else None,
            'max': max(strides) if strides else None,
            'mode': max(set(strides), key=strides.count) if strides else None,
        },
        'korean_samples': [{'off': hex(o), 'len': l, 'text': t} for o, l, t in korean[:25]],
    }


def main():
    files = ['_H_BH', '_H_BS', '_H_SA', '_H_SS', '_H_S000', '_H_S001', '_H_S002', '_H_S003']
    results = {}
    for fn in files:
        p = HDAT_DIR / fn
        if not p.exists():
            print(f'MISSING: {fn}', file=sys.stderr)
            continue
        r = analyze(p)
        results[fn] = r
        # Compact print
        print(f'\n=== {fn} ({r["size"]}B) ===')
        print(f'  header: {bytes(r["header_8B"]).hex()}')
        print(f'  entries: {r["entries_found"]},  strides: {r["strides"][:8]}')
        if r['stride_summary']['mode'] is not None:
            print(f'  stride_mode: {r["stride_summary"]["mode"]}  '
                  f'(min={r["stride_summary"]["min"]} max={r["stride_summary"]["max"]})')
        for e in r['entries'][:8]:
            print(f'  @0x{e["offset"]:04x} [size_field={e["size_field"]}, name_len={e["name_len"]}] {e["name"]!r}')

    out = OUT_DIR / 'hdat_a_parsed.json'
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nSaved: {out}')


if __name__ == '__main__':
    main()
