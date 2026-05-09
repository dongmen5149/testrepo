"""
extract_strings 단위 테스트.

실행:
    python -m unittest tools.recon.test_extract_strings
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from extract_strings import (
    is_printable, find_ascii_strings, find_euckr_strings,
    is_path_like, collect_targets, estimate_code_end,
)


class TestIsPrintable(unittest.TestCase):
    def test_ascii_letters(self):
        self.assertTrue(is_printable(ord('A')))
        self.assertTrue(is_printable(ord('z')))
        self.assertTrue(is_printable(ord('0')))

    def test_space_yes(self):
        self.assertTrue(is_printable(0x20))

    def test_control_no(self):
        self.assertFalse(is_printable(0x00))
        self.assertFalse(is_printable(0x1f))

    def test_del_and_high_no(self):
        self.assertFalse(is_printable(0x7f))
        self.assertFalse(is_printable(0xff))


class TestFindAsciiStrings(unittest.TestCase):
    def test_single_string(self):
        out = find_ascii_strings(b'\x00hello\x00\x00')
        self.assertEqual(out, [(1, 'hello')])

    def test_min_len_filter(self):
        # default min_len=4. b'\x00abc\x00world\x00' → 'abc' filtered, 'world' at offset 5
        self.assertEqual(find_ascii_strings(b'\x00abc\x00world\x00'), [(5, 'world')])

    def test_min_len_param(self):
        # min_len=2 → both kept
        self.assertEqual(
            find_ascii_strings(b'\x00abc\x00world\x00', min_len=2),
            [(1, 'abc'), (5, 'world')]
        )

    def test_runs_split_by_nonprintable(self):
        out = find_ascii_strings(b'aaaa\xffbbbb')
        self.assertEqual(len(out), 2)
        self.assertEqual([s for _, s in out], ['aaaa', 'bbbb'])

    def test_empty(self):
        self.assertEqual(find_ascii_strings(b''), [])


class TestFindEuckrStrings(unittest.TestCase):
    def test_korean_run(self):
        han = '한글이다'.encode('euc-kr')  # 4 chars
        out = find_euckr_strings(han)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], (0, '한글이다'))

    def test_min_chars_filter(self):
        han = '한'.encode('euc-kr')  # 1 char, default min_chars=3 → filtered
        self.assertEqual(find_euckr_strings(han), [])

    def test_ascii_does_not_match(self):
        self.assertEqual(find_euckr_strings(b'hello world'), [])

    def test_partial_lead_byte_does_not_match(self):
        # 0xa1 with non-trailing byte
        self.assertEqual(find_euckr_strings(b'\xa1\x00\xa1\x00'), [])


class TestIsPathLike(unittest.TestCase):
    def test_hero3_assets(self):
        self.assertTrue(is_path_like('/hero/h00000_bm'))
        self.assertTrue(is_path_like('/dat/InGame_txt'))
        self.assertTrue(is_path_like('/H4/PAL/_H_%03d_PAL'))

    def test_no_leading_slash(self):
        self.assertFalse(is_path_like('hero/h00000_bm'))

    def test_too_short(self):
        self.assertFalse(is_path_like('/a/b'))  # len < 5
        self.assertFalse(is_path_like('/'))

    def test_single_segment_no(self):
        # Need at least 2 separators
        self.assertFalse(is_path_like('/longpath'))


class TestCollectTargets(unittest.TestCase):
    def test_path_like_collected(self):
        strs = [(0x100, '/hero/h00000_bm'), (0x200, 'random text')]
        out = collect_targets(strs)
        self.assertIn(0x100, out)
        self.assertNotIn(0x200, out)

    def test_label_keyword_collected(self):
        # 'null' / 'not found' / 'failed' / 'error' are label keywords
        strs = [(0x300, 'frameBuf is NULL'), (0x400, 'Palette Index Not Found')]
        out = collect_targets(strs)
        self.assertEqual(set(out.keys()), {0x300, 0x400})

    def test_neutral_text_dropped(self):
        strs = [(0x500, 'just a normal string')]
        self.assertEqual(collect_targets(strs), {})


class TestEstimateCodeEnd(unittest.TestCase):
    def test_4kb_aligned_below_min_path(self):
        # min path offset 0x12345 → page (0x12000) — one page below
        out = estimate_code_end([(0x12345, '/dat/foo'), (0x12500, '/hero/bar')])
        self.assertEqual(out, 0x12000)

    def test_no_paths_returns_zero(self):
        self.assertEqual(estimate_code_end([(0x100, 'no slash')]), 0)


if __name__ == '__main__':
    unittest.main()
