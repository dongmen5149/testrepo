"""
Hero5 잔여 .bin 에서 EUC-KR 한글 시퀀스 일괄 추출.

산출:
  work/h5/converted/text/<file>.json   - 파일별 추출 결과
  work/h5/converted/text/_corpus.txt   - 전체 한글 통합 (i18n 베이스)
"""
from __future__ import annotations
import sys, struct, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'work' / 'h5' / 'vfs_entries'
OUT = ROOT / 'work' / 'h5' / 'converted' / 'text'


def is_sprite(d: bytes) -> bool:
    if len(d) < 14 or d[8] not in (0x04, 0x08, 0x14, 0x18): return False
    cnt = struct.unpack_from('<I', d, 0)[0]
    if cnt == 0 or cnt > 64: return False
    pos = 4
    for _ in range(cnt):
        if pos + 4 > len(d): return False
        ln = struct.unpack_from('<I', d, pos)[0]
        if pos + 4 + ln > len(d): return False
        pos += 4 + ln
    return pos == len(d)


def is_pa(d: bytes) -> bool:
    if len(d) < 5: return False
    c = d[0]
    return 0 < c <= 64 and len(d) == c * 4 + 1


def extract_korean(d: bytes, min_chars: int = 3) -> list[dict]:
    out = []
    i = 0
    while i < len(d) - 1:
        if 0xa1 <= d[i] <= 0xfe and 0xa1 <= d[i+1] <= 0xfe:
            j = i
            while j < len(d) - 1 and 0xa1 <= d[j] <= 0xfe and 0xa1 <= d[j+1] <= 0xfe:
                j += 2
            if (j - i) // 2 >= min_chars:
                try:
                    s = d[i:j].decode('euc-kr')
                    out.append({'offset': i, 'text': s})
                except UnicodeDecodeError:
                    pass
            i = max(j, i + 1)
        else:
            i += 1
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    corpus: dict[str, list[str]] = {}  # text -> source files
    total_files = 0
    total_strings = 0

    for p in sorted(SRC.glob('*.bin')):
        d = p.read_bytes()
        if d[:4] in (b'OggS', b'MMMD'): continue
        if is_sprite(d) or is_pa(d): continue
        strings = extract_korean(d)
        if not strings: continue
        total_files += 1
        total_strings += len(strings)
        out_file = OUT / f'{p.stem}.json'
        out_file.write_text(json.dumps(strings, ensure_ascii=False, indent=2), encoding='utf-8')
        for s in strings:
            corpus.setdefault(s['text'], []).append(p.stem)

    # corpus
    cpath = OUT / '_corpus.txt'
    with open(cpath, 'w', encoding='utf-8') as f:
        f.write(f'unique strings: {len(corpus)}  total occurrences: {total_strings}  source files: {total_files}\n\n')
        # sorted by frequency
        for text, sources in sorted(corpus.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            f.write(f'  [{len(sources):3d}x] {text}\n')

    print(f'files with korean: {total_files}')
    print(f'total strings: {total_strings}')
    print(f'unique strings: {len(corpus)}')
    print(f'corpus -> {cpath}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
