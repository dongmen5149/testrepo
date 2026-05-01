"""client.bin64000 에서 ASCII/EUC-KR 문자열 추출.
파일 I/O 시그니처, 에러 메시지, 디버그 라벨 등이 보이면 함수 식별의 단서.
"""
from __future__ import annotations
import sys, pathlib

BIN = pathlib.Path(__file__).parent.parent.parent / 'work' / 'extracted' / 'client.bin64000'


def is_printable(b: int) -> bool:
    return 0x20 <= b < 0x7f


def find_ascii_strings(data: bytes, min_len: int = 4) -> list[tuple[int, str]]:
    out = []
    i = 0
    while i < len(data):
        if is_printable(data[i]):
            j = i
            while j < len(data) and is_printable(data[j]):
                j += 1
            if j - i >= min_len:
                out.append((i, data[i:j].decode('ascii', errors='replace')))
            i = j
        else:
            i += 1
    return out


def find_euckr_strings(data: bytes, min_chars: int = 3) -> list[tuple[int, str]]:
    """EUC-KR 한글 시퀀스 탐지: 0xA1-0xFE 첫 바이트 + 0xA1-0xFE 두번째."""
    out = []
    i = 0
    while i < len(data) - 1:
        if 0xa1 <= data[i] <= 0xfe and 0xa1 <= data[i + 1] <= 0xfe:
            j = i
            chars = 0
            while j < len(data) - 1 and 0xa1 <= data[j] <= 0xfe and 0xa1 <= data[j + 1] <= 0xfe:
                j += 2
                chars += 1
            if chars >= min_chars:
                try:
                    s = data[i:j].decode('euc-kr')
                    out.append((i, s))
                except UnicodeDecodeError:
                    pass
            i = max(j, i + 1)
        else:
            i += 1
    return out


if __name__ == '__main__':
    data = BIN.read_bytes()
    print(f'Loaded {BIN.name}: {len(data)} bytes')

    ascii_strs = find_ascii_strings(data)
    print(f'\n=== ASCII strings (>=4 chars): {len(ascii_strs)} ===')
    # 파일 경로/확장자 패턴 우선
    interesting_keywords = ('boss', 'enemy', 'hero', 'npc', 'map', 'menu', 'comm', 'snd', 'event',
                            'logo', 'skill', 'fgi', 'font', '.bm', '.cif', '.pa', '.mp', '.dat',
                            '.scn', '.txt', '.mf', '_bm', '_cif', '_pa', '_mp', '_dat',
                            'open', 'read', 'load', 'draw', 'render', 'sprite', 'frame', 'palette')
    print('\n  -- file/loader related --')
    for off, s in ascii_strs:
        ls = s.lower()
        if any(k in ls for k in interesting_keywords):
            print(f'  {off:#08x}: {s!r}')

    print('\n  -- top 50 longest --')
    for off, s in sorted(ascii_strs, key=lambda x: -len(x[1]))[:50]:
        print(f'  {off:#08x}: {s!r}')

    eu = find_euckr_strings(data)
    print(f'\n=== EUC-KR strings (>=3 chars): {len(eu)} ===')
    for off, s in eu[:30]:
        print(f'  {off:#08x}: {s!r}')
