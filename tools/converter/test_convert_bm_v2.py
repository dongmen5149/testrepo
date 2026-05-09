"""
convert_bm_v2 단위 테스트 (PIL 비의존 함수만).

실행:
    python -m unittest tools.converter.test_convert_bm_v2
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

# convert_bm_v2 는 PIL.Image 를 import — 환경에 따라 skip.
try:
    from convert_bm_v2 import find_frame_markers, rgb565_to_rgba
    PIL_OK = True
except ImportError:
    PIL_OK = False


@unittest.skipIf(not PIL_OK, 'Pillow not installed')
class TestRgb565(unittest.TestCase):
    def test_magenta_transparent(self):
        # 0xf81f = magenta = transparent marker
        self.assertEqual(rgb565_to_rgba(0xf81f), (255, 0, 255, 0))

    def test_pure_red(self):
        # R=31, G=0, B=0 → (255, 0, 0, 255)
        # bits: 11111 000000 00000 = 0xf800
        self.assertEqual(rgb565_to_rgba(0xf800), (255, 0, 0, 255))

    def test_pure_blue(self):
        # R=0, G=0, B=31 → (0, 0, 255, 255)  but NOT 0xf81f
        # bits: 00000 000000 11111 = 0x001f
        self.assertEqual(rgb565_to_rgba(0x001f), (0, 0, 255, 255))

    def test_black(self):
        self.assertEqual(rgb565_to_rgba(0x0000), (0, 0, 0, 255))


@unittest.skipIf(not PIL_OK, 'Pillow not installed')
class TestFindFrameMarkers(unittest.TestCase):
    def _make_frame(self, type_byte: int, w: int, h: int, palcnt: int = 4) -> bytes:
        # mini_header(9) + marker(2) + palette(palcnt*2)
        import struct
        return (bytes([type_byte])
                + struct.pack('<HHHH', w, h, w, palcnt)  # w, h, cw, palcnt
                + b'\x1f\xf8'                           # marker
                + b'\x00\x00' * palcnt)                 # palette

    def test_single_frame_detected(self):
        data = b'\x00' * 6 + self._make_frame(0x0b, 16, 16) + b'\x00' * 32
        markers = find_frame_markers(data)
        self.assertEqual(len(markers), 1)

    def test_invalid_type_byte_filtered(self):
        # type byte 0x05 is not 0b/0c → should be filtered out
        import struct
        data = (b'\x00' * 6
                + bytes([0x05])
                + struct.pack('<HHHH', 16, 16, 16, 4)
                + b'\x1f\xf8'
                + b'\x00' * 8)
        self.assertEqual(find_frame_markers(data), [])

    def test_zero_dimension_filtered(self):
        data = b'\x00' * 6 + self._make_frame(0x0c, 0, 16) + b'\x00' * 32
        self.assertEqual(find_frame_markers(data), [])

    def test_oversized_dimension_filtered(self):
        data = b'\x00' * 6 + self._make_frame(0x0b, 9999, 16) + b'\x00' * 32
        self.assertEqual(find_frame_markers(data), [])

    def test_multiple_frames(self):
        f1 = self._make_frame(0x0b, 16, 16, palcnt=4)
        f2 = self._make_frame(0x0c, 24, 24, palcnt=8)
        data = b'\x00' * 6 + f1 + b'\x00' * 32 + f2 + b'\x00' * 32
        self.assertEqual(len(find_frame_markers(data)), 2)


if __name__ == '__main__':
    unittest.main()
