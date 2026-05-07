"""
analyze_cif 단위 테스트.

실행:
    python -m unittest tools/recon/test_analyze_cif.py
또는:
    python tools/recon/test_analyze_cif.py
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from analyze_cif import find_frames, parse_cells_4byte, s8


class TestS8(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(s8(0), 0)
        self.assertEqual(s8(1), 1)
        self.assertEqual(s8(127), 127)

    def test_negative(self):
        self.assertEqual(s8(0x80), -128)
        self.assertEqual(s8(0xff), -1)
        self.assertEqual(s8(0xfb), -5)


class TestParseCells(unittest.TestCase):
    def test_h0_cif_R0(self):
        # h0_cif R0 (offset 12) — known good frame from §4.3 분석
        rec = bytes.fromhex(
            '0a020bfbf52700f4fa2301fffd010000f62501fdf82501edf4020005f8250019ff000000ed0600ffe9'
        )
        cells = parse_cells_4byte(rec, offset=3, n=9)
        self.assertEqual(len(cells), 9)
        # cell 0: x=-5 y=-11 ref=0x27 flag=0x00
        self.assertEqual((cells[0]['x'], cells[0]['y'], cells[0]['ref'], cells[0]['flag']),
                         (-5, -11, 0x27, 0x00))
        # cell 8: x=0 y=-19 ref=0x06 flag=0x00
        self.assertEqual((cells[8]['x'], cells[8]['y'], cells[8]['ref'], cells[8]['flag']),
                         (0, -19, 0x06, 0x00))
        # All refs should fall within the h1 BM pool (≤0x44 for clean render group)
        for c in cells:
            self.assertLess(c['ref'], 0x45, f'cell {c["idx"]} ref out of pool')


class TestFindFramesH0(unittest.TestCase):
    """실제 h0_cif 파일에 대한 통합 테스트."""

    @classmethod
    def setUpClass(cls):
        cls.cif_path = pathlib.Path('work/extracted/hero/h0_cif')
        if not cls.cif_path.exists():
            raise unittest.SkipTest('h0_cif not extracted')
        cls.data = cls.cif_path.read_bytes()

    def test_total_frames(self):
        frames = find_frames(self.data)
        self.assertEqual(len(frames), 113, '§4.3 분석 시 113 frame 확정')

    def test_first_8_frames_stride_41(self):
        frames = find_frames(self.data)
        for k in range(7):
            self.assertEqual(frames[k+1] - frames[k], 41,
                             f'group1 frame {k} stride should be 41')

    def test_group_lead_0a020b_present(self):
        frames = find_frames(self.data)
        leads = {self.data[off:off+3].hex() for off in frames[:8]}
        self.assertIn('0a020b', leads, 'group1 lead 0a020b 누락')


if __name__ == '__main__':
    unittest.main()
