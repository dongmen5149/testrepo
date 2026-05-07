"""
convert_scn 단위 테스트.

실행:
    python -m unittest tools.converter.test_convert_scn
또는:
    python tools/converter/test_convert_scn.py
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from convert_scn import extract_euckr_strings, parse_scn
import convert_scn_v2


class TestExtractEuckr(unittest.TestCase):
    """EUC-KR 한글 시퀀스 추출."""

    def test_pure_korean(self):
        # "안녕하세요" in EUC-KR
        kr = '안녕하세요'.encode('euc-kr')
        result = extract_euckr_strings(kr)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], '안녕하세요')
        self.assertEqual(result[0]['offset'], 0)
        self.assertEqual(result[0]['char_count'], 5)

    def test_korean_with_ascii_around(self):
        kr = b'\x01\x02' + '한국어'.encode('euc-kr') + b'\x00\xff'
        result = extract_euckr_strings(kr)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], '한국어')
        self.assertEqual(result[0]['offset'], 2)

    def test_multiple_segments(self):
        kr = '첫번째'.encode('euc-kr') + b'\x00\x00\x00' + '두번째'.encode('euc-kr')
        result = extract_euckr_strings(kr)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['text'], '첫번째')
        self.assertEqual(result[1]['text'], '두번째')

    def test_below_min_chars(self):
        # default min_chars=2, "가" 는 1 char → 제외
        kr = '가'.encode('euc-kr') + b'\x00\x00\x00' + '한국어'.encode('euc-kr')
        result = extract_euckr_strings(kr, min_chars=2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], '한국어')

    def test_min_chars_three(self):
        # "한국" 은 2 char, "한국어" 는 3 char → min_chars=3 이면 후자만
        kr = '한국'.encode('euc-kr') + b'\x00\x00\x00' + '한국어'.encode('euc-kr')
        result = extract_euckr_strings(kr, min_chars=3)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], '한국어')

    def test_empty(self):
        self.assertEqual(extract_euckr_strings(b''), [])

    def test_no_korean(self):
        result = extract_euckr_strings(b'\x00\x01\x02\xff\xfe\x80\x90')
        self.assertEqual(result, [])

    def test_invalid_utf8_in_range_skipped(self):
        # bytes in [0xa1, 0xfe] but not valid EUC-KR pair → skipped silently
        bad = bytes([0xa1, 0xa1, 0xff, 0xff, 0xa2, 0xa2])
        result = extract_euckr_strings(bad)
        # 0xa1 0xa1 is valid (HWP-style space), so we may get hits — just sanity check no crash
        self.assertIsInstance(result, list)


class TestParseScn(unittest.TestCase):
    """parse_scn 헤더 + dialogue 통합."""

    def test_minimal(self):
        # 4-byte header + simple dialogue
        data = b'\x01\x02\x03\x04' + '대화'.encode('euc-kr')
        info = parse_scn(data)
        self.assertEqual(info['size'], len(data))
        self.assertEqual(info['header_4_hex'], '01020304')
        self.assertEqual(len(info['dialogue']), 1)
        self.assertEqual(info['dialogue'][0]['text'], '대화')

    def test_no_dialogue(self):
        data = b'\xab\xcd\xef\x12' + b'\x00' * 20
        info = parse_scn(data)
        self.assertEqual(info['dialogue'], [])

    def test_multiple_dialogues(self):
        data = b'\x00\x00\x00\x00'
        data += '첫째'.encode('euc-kr') + b'\x00\x00'
        data += '둘째'.encode('euc-kr') + b'\x00\x00'
        data += '셋째'.encode('euc-kr')
        info = parse_scn(data)
        self.assertEqual(len(info['dialogue']), 3)
        self.assertEqual([d['text'] for d in info['dialogue']], ['첫째', '둘째', '셋째'])


class TestParseScnV2(unittest.TestCase):
    """convert_scn_v2 — speaker tag + mode + text triple 추출."""

    def test_speaker_tag(self):
        # [김철수] 안녕하세요
        data = b'[' + '김철수'.encode('euc-kr') + b']' + '안녕하세요'.encode('euc-kr')
        info = convert_scn_v2.parse_scn(data)
        self.assertEqual(info['count'], 1)
        e = info['entries'][0]
        self.assertEqual(e['speaker'], '김철수')
        self.assertEqual(e['text'], '안녕하세요')

    def test_mode_byte(self):
        # 0x00 [mode] 가 한국어 직전: mode_byte 인식
        data = b'\x00\x7c' + '대사'.encode('euc-kr')
        info = convert_scn_v2.parse_scn(data)
        self.assertEqual(info['count'], 1)
        self.assertEqual(info['entries'][0]['mode_byte'], '0x7c')

    def test_speaker_persists_across_entries(self):
        """화자 태그 한 번 등장하면 다음 entry 들도 같은 화자."""
        data = b'[' + '왕'.encode('euc-kr') + b']'
        data += '첫째'.encode('euc-kr') + b'\x00'
        data += b'\x00\x27' + '둘째'.encode('euc-kr')
        info = convert_scn_v2.parse_scn(data)
        self.assertEqual(info['count'], 2)
        self.assertEqual(info['entries'][0]['speaker'], '왕')
        self.assertEqual(info['entries'][1]['speaker'], '왕')

    def test_no_speaker(self):
        data = '독백'.encode('euc-kr')
        info = convert_scn_v2.parse_scn(data)
        self.assertEqual(info['count'], 1)
        self.assertIsNone(info['entries'][0]['speaker'])

    def test_empty(self):
        info = convert_scn_v2.parse_scn(b'')
        self.assertEqual(info['count'], 0)


class TestRealScnFiles(unittest.TestCase):
    """실제 변환 결과 sanity check (regression)."""

    def setUp(self):
        for cand in ('work/h3/converted/scn_v2',
                     'android/app/src/main/assets/scn_v2'):
            p = pathlib.Path(cand)
            if p.is_dir():
                self.scn_dir = p
                return
        self.skipTest('no converted scn output dir found')

    def test_entries_extraction_works(self):
        """변환된 .scn JSON 다수가 1+ entries 보유 (PROGRESS §4.4 잔여 dialogue 추출 검증)."""
        import json
        files = [f for f in self.scn_dir.glob('*.json') if not f.name.startswith('_')]
        if not files:
            self.skipTest('no scn JSON files')
        with_entries = 0
        total_entries = 0
        sample = files[:50]
        for f in sample:
            try:
                d = json.loads(f.read_text(encoding='utf-8'))
            except Exception:
                continue
            entries = d.get('entries', [])
            if entries:
                with_entries += 1
                total_entries += len(entries)
        self.assertGreater(with_entries, len(sample) // 2,
                           f'expected most files to have entries, got {with_entries}/{len(sample)}')
        self.assertGreater(total_entries, 100,
                           f'expected 100+ total dialogue entries, got {total_entries}')


if __name__ == '__main__':
    unittest.main()
