"""
convert_dat 단위 테스트.

실행:
    python -m unittest tools.converter.test_convert_dat
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from convert_dat import extract_strings, parse_dat


class TestExtractStrings(unittest.TestCase):
    def test_single_korean(self):
        # '한글' EUC-KR = b'\xc7\xd1\xb1\xdb' (4 byte, 2 chars)
        data = b'\xc7\xd1\xb1\xdb'
        out = extract_strings(data)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['text'], '한글')
        self.assertEqual(out[0]['offset'], 0)

    def test_skip_short_runs(self):
        # min_chars=2 default → 1-char run is skipped
        data = b'\xc7\xd1' + b'\x00' * 10  # only 1 char
        out = extract_strings(data, min_chars=2)
        self.assertEqual(out, [])

    def test_min_chars_threshold(self):
        # 1 char run included with min_chars=1
        data = b'\xc7\xd1' + b'\x00' * 4
        out = extract_strings(data, min_chars=1)
        self.assertEqual(len(out), 1)

    def test_multiple_runs_separated(self):
        # 2 separate Korean runs
        han1 = '안녕'.encode('euc-kr')
        han2 = '세상'.encode('euc-kr')
        data = han1 + b'\x00\x01\x02' + han2
        out = extract_strings(data)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]['text'], '안녕')
        self.assertEqual(out[1]['text'], '세상')
        self.assertEqual(out[1]['offset'], len(han1) + 3)

    def test_ascii_does_not_match(self):
        # ASCII bytes (< 0xa1) shouldn't match
        out = extract_strings(b'hello world\x00')
        self.assertEqual(out, [])

    def test_partial_lead_byte_advances(self):
        # 0xa1 lead with non-trailing byte should not match
        data = b'\xa1\x00\xa1\x00'
        out = extract_strings(data)
        self.assertEqual(out, [])


class TestParseDat(unittest.TestCase):
    def test_basic_structure(self):
        data = b'\x01\x02\x03\x04\x05\x06\x07\x08' + '한글'.encode('euc-kr')
        info = parse_dat(data)
        self.assertEqual(info['size'], len(data))
        self.assertEqual(info['header_8_hex'], '0102030405060708')
        self.assertEqual(len(info['korean_strings']), 1)

    def test_short_data_header(self):
        info = parse_dat(b'\x01\x02')
        self.assertEqual(info['header_8_hex'], '0102')


if __name__ == '__main__':
    unittest.main()
