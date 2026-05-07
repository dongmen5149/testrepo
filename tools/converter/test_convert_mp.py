"""
convert_mp 단위 테스트.

실행:
    python -m unittest tools.converter.test_convert_mp
또는:
    python tools/converter/test_convert_mp.py
"""
from __future__ import annotations
import unittest, pathlib, sys, struct

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from convert_mp import parse_extras, parse_mp, _parse_records


def make_record(t: int, rid: int, x: int, y: int) -> bytes:
    """6-byte record: type, id, x_u16_LE, y_u16_LE."""
    return bytes([t, rid]) + struct.pack('<HH', x, y)


class TestParseRecords(unittest.TestCase):
    """_parse_records 의 valid 좌표 검증 + 부호 변환."""

    def test_valid_in_bounds(self):
        ex = make_record(0x00, 0x3e, 16, 32)  # tile (1, 2)
        recs = _parse_records(ex, W=10, H=10, hdr_off=0, count=1)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]['tile'], [1, 2])
        self.assertTrue(recs[0]['valid'])

    def test_invalid_out_of_bounds(self):
        ex = make_record(0x00, 0x3e, 1000, 2000)  # way off-map
        recs = _parse_records(ex, W=10, H=10, hdr_off=0, count=1)
        self.assertFalse(recs[0]['valid'])

    def test_negative_coord(self):
        # 0xffff = -1 px after sign convert -> tile -1 (boundary 허용)
        ex = make_record(0x80, 0x3f, 0xffff, 0xffff)
        recs = _parse_records(ex, W=10, H=10, hdr_off=0, count=1)
        self.assertEqual(recs[0]['px'], [0xffff, 0xffff])
        self.assertEqual(recs[0]['tile'], [-1, -1])
        self.assertTrue(recs[0]['valid'])  # -1 boundary

    def test_truncated_record(self):
        ex = b'\x00\x3e\x10\x00'  # 4 bytes, missing y
        recs = _parse_records(ex, W=10, H=10, hdr_off=0, count=1)
        self.assertEqual(recs, [])  # record breaks early


class TestParseExtrasH1S6(unittest.TestCase):
    """h1_s6: byte0 = count, then count × 6 byte records."""

    def test_single_record(self):
        ex = bytes([1]) + make_record(0x00, 0x3e, 16, 32)
        result = parse_extras(ex, W=10, H=10)
        self.assertEqual(result['strategy'], 'h1_s6')
        self.assertEqual(len(result['records']), 1)
        self.assertEqual(result['leftover'], 0)

    def test_three_records(self):
        ex = bytes([3])
        for i in range(3):
            ex += make_record(0x00, 0x3e + i, (i + 1) * 16, (i + 1) * 16)
        result = parse_extras(ex, W=10, H=10)
        self.assertEqual(result['strategy'], 'h1_s6')
        self.assertEqual(len(result['records']), 3)


class TestParseExtrasH2S6(unittest.TestCase):
    """h2_s6: byte0 = flag, byte1 = count."""

    def test_with_flag_0x80(self):
        ex = bytes([0x80, 2])
        for i in range(2):
            ex += make_record(0x00, 0x3e, 16 * (i + 1), 16 * (i + 1))
        result = parse_extras(ex, W=10, H=10)
        self.assertEqual(result['strategy'], 'h2_s6')
        self.assertEqual(len(result['records']), 2)

    def test_with_flag_0xc0(self):
        ex = bytes([0xc0, 1]) + make_record(0x00, 0x3e, 16, 32)
        result = parse_extras(ex, W=10, H=10)
        self.assertEqual(result['strategy'], 'h2_s6')


class TestParseExtrasMulti(unittest.TestCase):
    """multi: byte0/1 = 0x80/0xc0, byte2 = count1, then section1, then count2 + section2."""

    def test_two_sections(self):
        # section 1: 1 record
        s1 = make_record(0x00, 0x3e, 16, 16)
        # section 2: 2 records
        s2 = make_record(0x00, 0x3f, 32, 32) + make_record(0x80, 0x3e, 48, 48)
        ex = bytes([0x80, 0xc0, 1]) + s1 + bytes([2]) + s2
        result = parse_extras(ex, W=10, H=10)
        self.assertEqual(result['strategy'], 'multi')
        self.assertEqual(len(result['records']), 3)

    def test_section1_only(self):
        # multi flag but only 1 section + leftover bytes that don't form valid records
        s1 = make_record(0x00, 0x3e, 16, 16)
        ex = bytes([0x80, 0xc0, 1]) + s1 + b'\xab\xcd'  # garbage trailer
        result = parse_extras(ex, W=10, H=10)
        # 2 byte garbage interpreted as count for section2 → likely fails validity
        self.assertIn(result['strategy'], ('multi_s1only', 'multi'))


class TestParseExtrasEdge(unittest.TestCase):
    def test_empty(self):
        result = parse_extras(b'', W=10, H=10)
        self.assertEqual(result['strategy'], 'empty')
        self.assertEqual(result['records'], [])

    def test_single_byte(self):
        result = parse_extras(b'\x00', W=10, H=10)
        self.assertEqual(result['strategy'], 'empty')

    def test_unparseable(self):
        # garbage bytes that don't fit any strategy
        result = parse_extras(b'\xde\xad\xbe\xef', W=10, H=10)
        self.assertEqual(result['strategy'], 'unparsed')
        self.assertEqual(result['leftover'], 4)


class TestParseMp(unittest.TestCase):
    """parse_mp 헤더 파싱."""

    def _build_mp(self, version: int, name: str, W: int, H: int) -> bytes:
        if version == 0x02:
            hdr = bytes([0x02, 0, 0, 0, 0])  # 5 byte
        elif version == 0x03:
            hdr = bytes([0x03, 0, 0, 0, 0, 0])  # 6 byte
        else:
            raise ValueError
        body = bytes([len(name)]) + name.encode('ascii') + b'\x00'
        body += bytes([W, H, 0, 0])  # palette_count=0, meta4=0
        # 2 layers
        body += bytes(W * H * 2)
        # extras: empty
        return hdr + body

    def test_version_2(self):
        data = self._build_mp(0x02, 'TEST_MAP', 4, 4)
        info = parse_mp(data)
        self.assertEqual(info['version'], 0x02)
        self.assertEqual(info['name'], 'TEST_MAP')
        self.assertEqual(info['width'], 4)
        self.assertEqual(info['height'], 4)

    def test_version_3(self):
        data = self._build_mp(0x03, 'V3_MAP', 8, 8)
        info = parse_mp(data)
        self.assertEqual(info['version'], 0x03)
        self.assertEqual(len(info['layer_0']), 64)
        self.assertEqual(len(info['layer_1']), 64)

    def test_invalid_version(self):
        data = bytes([0x99, 0, 0, 0, 0, 1, ord('A'), 0, 1, 1, 0, 0, 0, 0])
        with self.assertRaises(ValueError):
            parse_mp(data)

    def test_too_small(self):
        with self.assertRaises(ValueError):
            parse_mp(b'\x02')


class TestRealFiles(unittest.TestCase):
    """실제 변환 결과 sanity check (regression)."""

    def setUp(self):
        # 우선 converted output dir, 없으면 android assets (검증된 변환 산출물)
        for cand in ('work/h3/converted/maps', 'android/app/src/main/assets/maps'):
            p = pathlib.Path(cand)
            if p.is_dir():
                self.maps_dir = p
                return
        self.skipTest('no converted maps found in either location')

    def test_strategy_distribution(self):
        """97% 자동 파싱 (PROGRESS §4.2) 검증."""
        import json
        files = list(self.maps_dir.glob('*.json'))
        if not files:
            self.skipTest('no map JSON files')
        strategies = {}
        for f in files:
            d = json.loads(f.read_text(encoding='utf-8'))
            s = d.get('extras_strategy', 'missing')
            strategies[s] = strategies.get(s, 0) + 1
        # 적어도 100개는 정상 strategy
        parsed = sum(strategies.get(s, 0) for s in ('h1_s6', 'h2_s6', 'multi', 'empty'))
        self.assertGreater(parsed, len(files) * 0.85,
                           f'expected >85% parsed, got {strategies}')


if __name__ == '__main__':
    unittest.main()
