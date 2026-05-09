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
from analyze_cif import (
    find_frames, parse_cells_4byte, s8,
    decode_cell_byte, parse_boss_header, parse_boss_cells,
    split_frames_by_sentinel, boss_cif_summary, SENTINEL_CELL_BYTE,
)


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
        cls.cif_path = pathlib.Path('work/h3/extracted/hero/h0_cif')
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


class TestWalkCycleStructure(unittest.TestCase):
    """h0 4x8 walk-cycle 구조 검증 (h4-h11 은 다른 인코딩 사용 — 2026-05-08 발견)."""

    def setUp(self):
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'converter'))
        try:
            from bake_hero_walkcycle import has_h0_walkcycle_structure
        except ImportError as e:
            self.skipTest(f'bake_hero_walkcycle import failed: {e}')
        self.check = has_h0_walkcycle_structure

    def test_h0_matches(self):
        p = pathlib.Path('work/h3/extracted/hero/h0_cif')
        if not p.exists():
            self.skipTest('h0_cif not extracted')
        data = p.read_bytes()
        frames = find_frames(data)
        self.assertTrue(self.check(data, frames), 'h0 must match 4x8 walk-cycle structure')

    def test_h4_does_not_match(self):
        p = pathlib.Path('work/h3/extracted/hero/h4_cif')
        if not p.exists():
            self.skipTest('h4_cif not extracted')
        data = p.read_bytes()
        frames = find_frames(data)
        self.assertFalse(self.check(data, frames),
                         'h4 must NOT match — uses different walk-cycle encoding')

    def test_h11_does_not_match(self):
        p = pathlib.Path('work/h3/extracted/hero/h11_cif')
        if not p.exists():
            self.skipTest('h11_cif not extracted')
        data = p.read_bytes()
        frames = find_frames(data)
        self.assertFalse(self.check(data, frames),
                         'h11 must NOT match — uses different walk-cycle encoding')


class TestBossCellByteDecode(unittest.TestCase):
    """FUN_00098ef8 cell byte 분해 검증."""

    def test_sentinel(self):
        c = decode_cell_byte(SENTINEL_CELL_BYTE)
        self.assertTrue(c['is_sentinel'])
        self.assertEqual(c['orient'], 3)
        self.assertEqual(c['ref'], 31)
        self.assertFalse(c['special'])

    def test_zero_cell(self):
        c = decode_cell_byte(0x00)
        self.assertFalse(c['is_sentinel'])
        self.assertEqual(c['orient'], 0)
        self.assertEqual(c['ref'], 0)
        self.assertFalse(c['special'])

    def test_orient_ref_split(self):
        # 0x33 = 0b00110011 → orient=1 ref=19 special=0
        c = decode_cell_byte(0x33)
        self.assertEqual(c['orient'], 1)
        self.assertEqual(c['ref'], 19)
        self.assertFalse(c['special'])

    def test_special_bit(self):
        # 0x80 = special bit set, orient=0 ref=0
        c = decode_cell_byte(0x80)
        self.assertTrue(c['special'])
        self.assertEqual(c['orient'], 0)
        self.assertEqual(c['ref'], 0)

    def test_special_with_orient_ref(self):
        # 0xf7 = 0b11110111 → special=1 orient=3 ref=23
        c = decode_cell_byte(0xf7)
        self.assertTrue(c['special'])
        self.assertEqual(c['orient'], 3)
        self.assertEqual(c['ref'], 23)


class TestParseBossHeader(unittest.TestCase):
    def test_boss0_header(self):
        # boss0_cif: 01 00 08 ... → sc=1 cat=0 indices=[8] body_off=3
        h = parse_boss_header(bytes.fromhex('010008010912'))
        self.assertEqual(h['slot_count'], 1)
        self.assertEqual(h['category'], 0)
        self.assertEqual(h['indices'], [8])
        self.assertEqual(h['body_offset'], 3)

    def test_e100_multi_slot(self):
        # e100_cif: sc=4 cat=0 indices=[1,2,3,4] body_off=6
        h = parse_boss_header(bytes.fromhex('04000102030400ff'))
        self.assertEqual(h['slot_count'], 4)
        self.assertEqual(h['indices'], [1, 2, 3, 4])
        self.assertEqual(h['body_offset'], 6)


class TestParseBossCells(unittest.TestCase):
    def test_basic_cells(self):
        # 3 cells: sentinel, normal, special
        body = bytes.fromhex('7f00ffff' '20053a01' '8002edf7')
        cells = parse_boss_cells(body)
        self.assertEqual(len(cells), 3)
        self.assertTrue(cells[0]['is_sentinel'])
        self.assertEqual((cells[1]['orient'], cells[1]['ref'], cells[1]['x'], cells[1]['y']),
                         (1, 0, 5, 0x3a))
        self.assertTrue(cells[2]['special'])

    def test_max_cells_limit(self):
        body = b'\x00' * 40  # 10 cells worth
        cells = parse_boss_cells(body, max_cells=3)
        self.assertEqual(len(cells), 3)

    def test_trailing_partial_ignored(self):
        # 9 bytes = 2 full cells + 1 trailing byte (ignored)
        body = b'\x00\x01\x02\x03' + b'\x10\x20\x30\x40' + b'\xff'
        cells = parse_boss_cells(body)
        self.assertEqual(len(cells), 2)


class TestSplitFramesBySentinel(unittest.TestCase):
    def test_split_two_frames(self):
        cells = [
            {'is_sentinel': True}, {'idx': 0, 'is_sentinel': False},
            {'idx': 1, 'is_sentinel': False}, {'is_sentinel': True},
            {'idx': 2, 'is_sentinel': False},
        ]
        frames = split_frames_by_sentinel(cells)
        self.assertEqual(len(frames), 2)
        self.assertEqual(len(frames[0]), 2)
        self.assertEqual(len(frames[1]), 1)

    def test_no_sentinels(self):
        cells = [{'idx': i, 'is_sentinel': False} for i in range(5)]
        frames = split_frames_by_sentinel(cells)
        self.assertEqual(len(frames), 1)
        self.assertEqual(len(frames[0]), 5)

    def test_consecutive_sentinels_collapse(self):
        cells = [
            {'is_sentinel': True}, {'is_sentinel': True},
            {'idx': 0, 'is_sentinel': False}, {'is_sentinel': True},
        ]
        frames = split_frames_by_sentinel(cells)
        self.assertEqual(len(frames), 1)
        self.assertEqual(len(frames[0]), 1)


class TestBossCifSummaryRealFile(unittest.TestCase):
    """실제 boss/enemy cif 에 대한 통합 테스트."""

    def test_boss0_summary(self):
        p = pathlib.Path('work/h3/extracted/boss/boss0_cif')
        if not p.exists():
            self.skipTest('boss0_cif not extracted')
        s = boss_cif_summary(p.read_bytes())
        self.assertEqual(s['header']['slot_count'], 1)
        self.assertEqual(s['header']['indices'], [8])
        # boss0 has 46 aligned 0x7f sentinels (4-byte aligned scan)
        self.assertGreaterEqual(s['sentinels'], 40)
        self.assertGreater(s['frames'], 1)

    def test_e000_summary(self):
        p = pathlib.Path('work/h3/extracted/enemy/e000_cif')
        if not p.exists():
            self.skipTest('e000_cif not extracted')
        s = boss_cif_summary(p.read_bytes())
        self.assertEqual(s['header']['slot_count'], 1)
        self.assertEqual(s['header']['indices'], [4])
        # e000 has zero 0x7f bytes — single frame
        self.assertEqual(s['sentinels'], 0)
        self.assertEqual(s['frames'], 1)


if __name__ == '__main__':
    unittest.main()
