"""
convert_palette 단위 테스트.

실행:
    python -m unittest tools.converter.test_convert_palette
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from convert_palette import parse_palette


class TestParsePaletteHero3(unittest.TestCase):
    """Hero3 _pa: count(1B) + count × 4 byte (BGRA-like)."""

    def test_single_color(self):
        data = bytes([1]) + bytes([0x12, 0x34, 0x56, 0x00])
        out = parse_palette(data)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['bytes'], [0x12, 0x34, 0x56, 0x00])
        self.assertEqual(out[0]['rgba_be'], '#12345600')
        self.assertEqual(out[0]['argb_le'], '#00563412')

    def test_multiple_colors(self):
        data = bytes([3]) + bytes(3 * 4)  # 3 colors × 4 byte = 12 zero bytes
        out = parse_palette(data)
        self.assertEqual(len(out), 3)
        for c in out:
            self.assertEqual(c['bytes'], [0, 0, 0, 0])

    def test_size_mismatch_raises(self):
        # count=2 expects 9 bytes (h3) or 17 (h4); pass 8.
        with self.assertRaises(ValueError):
            parse_palette(bytes([2]) + bytes(7))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            parse_palette(b'')


class TestParsePaletteHero4(unittest.TestCase):
    """Hero4 _PAL: count(1B) + count × 8 byte (primary RGBA + secondary RGBA)."""

    def test_single_color_pair(self):
        data = bytes([1]) + bytes([0xff, 0x00, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00])
        out = parse_palette(data)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['primary'], '#ff0000')
        self.assertEqual(out[0]['secondary'], '#800000')
        self.assertEqual(out[0]['primary_alpha'], 0)
        self.assertEqual(out[0]['secondary_alpha'], 0)

    def test_alpha_field(self):
        data = bytes([1]) + bytes([0xff, 0xff, 0xff, 0xc0, 0x80, 0x80, 0x80, 0xff])
        out = parse_palette(data)
        self.assertEqual(out[0]['primary_alpha'], 0xc0)
        self.assertEqual(out[0]['secondary_alpha'], 0xff)


if __name__ == '__main__':
    unittest.main()
