"""
convert_text 단위 테스트.

실행:
    python -m unittest tools.converter.test_convert_text
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from convert_text import parse_text_table


def build_text_table(strings_eckr: list[bytes]) -> bytes:
    """테스트용 _txt 파일 생성: header(4B) + offsets(2*N) + 문자열들."""
    import struct
    count = len(strings_eckr)
    header_len = 4 + count * 2
    offsets: list[int] = []
    body = bytearray()
    for s in strings_eckr:
        offsets.append(header_len + len(body))
        body += s + b'\x00'
    total_len = header_len + len(body)
    out = bytearray()
    out += struct.pack('<HH', total_len, count)
    for off in offsets:
        out += struct.pack('<H', off)
    out += body
    return bytes(out)


class TestParseTextTable(unittest.TestCase):
    def test_single_string(self):
        # "hello" in EUC-KR (ASCII compatible)
        data = build_text_table([b'hello'])
        out = parse_text_table(data)
        self.assertEqual(out, ['hello'])

    def test_multiple_strings(self):
        data = build_text_table([b'a', b'bb', b'ccc'])
        self.assertEqual(parse_text_table(data), ['a', 'bb', 'ccc'])

    def test_empty_strings(self):
        data = build_text_table([b'', b'x'])
        self.assertEqual(parse_text_table(data), ['', 'x'])

    def test_korean_eckr(self):
        # "한글" in EUC-KR
        han = '한글'.encode('euc-kr')
        data = build_text_table([han])
        self.assertEqual(parse_text_table(data), ['한글'])

    def test_real_ingame_txt(self):
        p = pathlib.Path('work/h3/extracted/dat/InGame_txt')
        if not p.exists():
            self.skipTest('InGame_txt not extracted')
        out = parse_text_table(p.read_bytes())
        # PROGRESS.md: 196 strings in InGame_txt
        self.assertEqual(len(out), 196)


if __name__ == '__main__':
    unittest.main()
