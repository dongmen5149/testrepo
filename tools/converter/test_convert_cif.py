"""
convert_cif 단위 테스트.

실행:
    python -m unittest tools.converter.test_convert_cif
"""
from __future__ import annotations
import unittest, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from convert_cif import parse_cif, parse_cif_boss


class TestParseCifHeader(unittest.TestCase):
    def test_h0_header(self):
        # h0_cif 헤더: 8 slots, cat=0, indices=[1,2,3,10,17,19,16,8]
        d = bytes.fromhex('08000102030a1113100804080a020bfb')
        out = parse_cif(d)
        self.assertEqual(out['slot_count'], 8)
        self.assertEqual(out['category'], 0)
        self.assertEqual(out['indices'], [1, 2, 3, 10, 17, 19, 16, 8])

    def test_short_data_safe(self):
        out = parse_cif(b'')
        self.assertEqual(out['slot_count'], 0)
        self.assertEqual(out['indices'], [])


class TestParseCifBoss(unittest.TestCase):
    def test_boss0_cells(self):
        # boss0_cif: 헤더 sc=1 cat=0 idx=[8] body_off=3, 추가 metadata bytes 후 셀 시작.
        # parse_cif_boss 는 body_offset=3 부터 4-byte 셀 스트림으로 해석 (FUN_00098ef8 의
        # 단순화 — 실제 binary 의 pointer chain 까지 따라가진 않음).
        d = bytes.fromhex('010008010912' '7f00ffff' '2005d5cb' '2007e3d0')
        out = parse_cif_boss(d)
        self.assertEqual(out['slot_count'], 1)
        self.assertEqual(out['indices'], [8])
        # body=15B (data[3:]), 15//4=3 cells.
        self.assertEqual(out['cells_total'], 3)
        # 이 alignment 에서는 sentinel 0건 (0x7f 가 4-byte 경계에 안 떨어짐).
        # parse_boss_header 의 body_offset 은 indices end 까지만 — 실제 binary 가 더 skip 할 가능성 있음.
        self.assertEqual(out['sentinels'], 0)

    def test_e000_summary_via_parse(self):
        # e000_cif 첫 12 byte
        d = bytes.fromhex('010004' '04040400' '0400f700' '09080220')
        out = parse_cif_boss(d)
        self.assertEqual(out['slot_count'], 1)
        self.assertEqual(out['indices'], [4])
        self.assertEqual(out['sentinels'], 0)

    def test_real_boss0_file(self):
        p = pathlib.Path('work/h3/extracted/boss/boss0_cif')
        if not p.exists():
            self.skipTest('boss0_cif not extracted')
        out = parse_cif_boss(p.read_bytes())
        self.assertEqual(out['slot_count'], 1)
        self.assertEqual(out['indices'], [8])
        self.assertGreater(out['frames'], 1)
        self.assertGreaterEqual(out['sentinels'], 40)
        # frame_summaries 크기 64 cap
        self.assertLessEqual(len(out['frame_summaries']), 64)


if __name__ == '__main__':
    unittest.main()
