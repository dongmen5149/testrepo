"""Round 84 — Hero4 _ITM_OPTION enchantment pool 파싱.

1928B 평문(R83 복호화). entry = mixed ASCII + EUC-KR text label
(예: "HPmax L1", "근접공격 L2", "직격 L1") + stat bytes.

산출: work/h4/converted/h4_itm_option_pool.json
"""
from __future__ import annotations
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / 'work' / 'h4' / 'decrypted' / 'ITM' / 'DAT' / '_ITM_OPTION'
OUT = ROOT / 'work' / 'h4' / 'converted' / 'h4_itm_option_pool.json'


def is_text_byte(b: int) -> bool:
    return 0x20 <= b <= 0x7e or 0xa1 <= b <= 0xfe


def extract_text_runs(data: bytes) -> list[dict]:
    runs = []
    i = 0
    while i < len(data):
        j = i
        while j < len(data) and is_text_byte(data[j]):
            j += 1
        if j - i >= 4:
            try:
                s = data[i:j].decode('euc-kr', errors='replace')
                if any(c.isalpha() or '가' <= c <= '힯' for c in s):
                    runs.append({'offset': i, 'byte_len': j-i, 'text': s})
            except Exception:
                pass
        i = max(j, i+1)
    return runs


def main():
    data = SRC.read_bytes()
    runs = extract_text_runs(data)

    # Classify by suffix Lk
    lvl_pattern = re.compile(r'L([1-9])')
    by_lvl = {}
    base_names = []
    for r in runs:
        m = lvl_pattern.search(r['text'])
        lv = m.group(1) if m else None
        base = r['text'].rsplit('L', 1)[0].strip().rstrip('PZ').strip() if lv else r['text']
        r['level'] = lv
        r['base_name'] = base
        if lv is not None:
            by_lvl.setdefault(lv, []).append(r)
        base_names.append(base)

    unique_bases = sorted(set(b for b in base_names if b))

    out = {
        'meta': {
            'round': 'R84',
            'date': '2026-05-19',
            'source': str(SRC.relative_to(ROOT)),
            'file_size': len(data),
            'text_run_count': len(runs),
        },
        'by_level': {lv: len(items) for lv, items in by_lvl.items()},
        'unique_base_names': unique_bases,
        'unique_base_count': len(unique_bases),
        'entries': runs,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"=== _ITM_OPTION ({len(data)}B) ===")
    print(f"text runs: {len(runs)}")
    print(f"level distribution: {out['by_level']}")
    print(f"unique enchantment types ({len(unique_bases)}): {unique_bases}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == '__main__':
    main()
