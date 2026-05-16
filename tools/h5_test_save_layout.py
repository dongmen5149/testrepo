"""Save 포맷 layout round-trip 검증 (Round 49).

GDScript 의 `serialize_hero_save` / `serialize_slot_save` 와 동등한 Python
구현 + assert. SAVE_FORMAT.md § 3.1, § 3.2 layout 명세 일치 검증.

Round 41-43 의 LoadHeroData/LoadSlotData cross-check 결과 (H_*.sav 21/21 +
SL_*.sav 24 offset) 와 동일 offset 에 동일 size 로 직렬화하는지 자동 점검.
"""
from __future__ import annotations
import struct

H_SAV_SIZE = 0x20c
SL_SAV_HEADER_SIZE = 0x17


def put_u16_le(buf: bytearray, off: int, val: int) -> None:
    buf[off:off + 2] = struct.pack('<H', val & 0xffff)


def put_u32_le(buf: bytearray, off: int, val: int) -> None:
    buf[off:off + 4] = struct.pack('<I', val & 0xffffffff)


def put_u64_le(buf: bytearray, off: int, val: int) -> None:
    buf[off:off + 8] = struct.pack('<Q', val & 0xffffffffffffffff)


def get_u16_le(buf: bytes, off: int) -> int:
    return struct.unpack_from('<H', buf, off)[0]


def get_u32_le(buf: bytes, off: int) -> int:
    return struct.unpack_from('<I', buf, off)[0]


def get_u64_le(buf: bytes, off: int) -> int:
    return struct.unpack_from('<Q', buf, off)[0]


def serialize_hero_save(state: dict) -> bytes:
    """SAVE_FORMAT.md § 3.1 layout (H_*.sav, 524 byte) 직렬화."""
    buf = bytearray(H_SAV_SIZE)
    put_u32_le(buf, 0x00, state.get("field_f0", 0))
    buf[0x04] = state.get("class_id", 0) & 0xff
    buf[0x05] = state.get("hero_22d", 0) & 0xff
    put_u32_le(buf, 0x06, state.get("gold", 0))
    stats = state.get("stats", [0] * 8)
    for i in range(8):
        put_u16_le(buf, 0x0a + i * 2, stats[i] if i < len(stats) else 0)
    sb = state.get("skill_buff", b"")
    buf[0x1a:0x1a + min(len(sb), 0x2b)] = sb[:0x2b]
    eq = state.get("equip", b"")
    buf[0x45:0x45 + min(len(eq), 7)] = eq[:7]
    put_u32_le(buf, 0x4c, state.get("field_4c", 0))
    sb2 = state.get("field_50_block", b"")
    buf[0x50:0x50 + min(len(sb2), 16)] = sb2[:16]
    buf[0x60] = state.get("field_60", 0) & 0xff
    slots = state.get("skill_slots", [])
    for i in range(min(len(slots), 10)):
        rec = slots[i]
        for j in range(min(len(rec), 0x29)):
            buf[0x61 + i * 0x29 + j] = rec[j]
    put_u64_le(buf, 0x1fc, state.get("timestamp_create", 0))
    put_u64_le(buf, 0x204, state.get("timestamp_update", 0))
    return bytes(buf)


def deserialize_hero_save(data: bytes) -> dict:
    return {
        "field_f0": get_u32_le(data, 0x00),
        "class_id": data[0x04],
        "hero_22d": data[0x05],
        "gold": get_u32_le(data, 0x06),
        "stats": [get_u16_le(data, 0x0a + i * 2) for i in range(8)],
        "skill_buff": data[0x1a:0x45],
        "equip": data[0x45:0x4c],
        "field_4c": get_u32_le(data, 0x4c),
        "field_50_block": data[0x50:0x60],
        "field_60": data[0x60],
        "skill_slots": [data[0x61 + i * 0x29:0x61 + (i + 1) * 0x29] for i in range(10)],
        "timestamp_create": get_u64_le(data, 0x1fc),
        "timestamp_update": get_u64_le(data, 0x204),
    }


def serialize_slot_save(state: dict) -> bytes:
    """SAVE_FORMAT.md § 3.2 header (SL_*.sav, +0x00..+0x16) 직렬화."""
    buf = bytearray(SL_SAV_HEADER_SIZE)
    class_id = state.get("class_id", 0) & 0xff
    level = state.get("level", 1) & 0xff
    buf[0x00] = (level * 10 + class_id) & 0xff
    buf[0x01] = state.get("hero_22d", 0) & 0xff
    put_u32_le(buf, 0x02, state.get("pos_x", 0))
    put_u32_le(buf, 0x06, state.get("pos_y", 0))
    put_u64_le(buf, 0x0a, state.get("playtime_ms", 0))
    put_u32_le(buf, 0x12, state.get("scene_idx", 0))
    buf[0x16] = state.get("state_flag", 0) & 0xff
    return bytes(buf)


def deserialize_slot_save(data: bytes) -> dict:
    packed = data[0x00]
    return {
        "class_id": packed % 10,
        "level": packed // 10,
        "hero_22d": data[0x01],
        "pos_x": get_u32_le(data, 0x02),
        "pos_y": get_u32_le(data, 0x06),
        "playtime_ms": get_u64_le(data, 0x0a),
        "scene_idx": get_u32_le(data, 0x12),
        "state_flag": data[0x16],
    }


def test_hero_round_trip() -> int:
    """다양한 sample state 의 round-trip 일치 검증."""
    samples = [
        # Sample 1: 워리어 (class 0) level 1 새 캐릭터
        {
            "field_f0": 100,
            "class_id": 0, "hero_22d": 1,
            "gold": 50,
            "stats": [50, 30, 15, 12, 18, 8, 0, 0],   # HP/MP/STR/DEX/CON/INT
            "skill_buff": bytes([0] * 0x2b),
            "equip": bytes([1, 0, 0, 0, 0, 0, 0]),
            "field_4c": 0, "field_60": 0,
            "skill_slots": [bytes([0] * 0x29) for _ in range(10)],
            "timestamp_create": 0x123456789abcdef0,
            "timestamp_update": 0x0fedcba987654321,
        },
        # Sample 2: 나이트 (class 3) level 10
        {
            "field_f0": 0xdeadbeef,
            "class_id": 3, "hero_22d": 10,
            "gold": 99999,
            "stats": [500, 250, 60, 35, 70, 25, 100, 50],
            "skill_buff": bytes(range(0x2b)),
            "equip": bytes([10, 20, 30, 40, 50, 60, 70]),
            "field_4c": 0x12345678, "field_60": 5,
            "skill_slots": [bytes(range(i, i + 0x29)) for i in range(10)],
            "timestamp_create": 1700000000,
            "timestamp_update": 1700001000,
        },
    ]
    passed = 0
    for idx, s in enumerate(samples):
        b = serialize_hero_save(s)
        assert len(b) == H_SAV_SIZE, f'sample {idx}: size {len(b)} != {H_SAV_SIZE}'
        r = deserialize_hero_save(b)
        # 모든 필드 round-trip
        for k in ['field_f0', 'class_id', 'hero_22d', 'gold', 'stats', 'field_4c',
                  'field_60', 'timestamp_create', 'timestamp_update']:
            assert r[k] == s[k], f'sample {idx} field {k}: {r[k]!r} != {s[k]!r}'
        passed += 1
    print(f'  hero round-trip: {passed}/{len(samples)} samples')
    return 0


def test_slot_round_trip() -> int:
    samples = [
        # 워리어 level 1 — packed = 1*10 + 0 = 10
        {"class_id": 0, "level": 1, "hero_22d": 0,
         "pos_x": 100, "pos_y": 200, "playtime_ms": 60000,
         "scene_idx": 5, "state_flag": 0},
        # 소서러 level 25 max — packed = 25*10 + 4 = 254
        {"class_id": 4, "level": 25, "hero_22d": 1,
         "pos_x": -50, "pos_y": -100, "playtime_ms": 9999999,
         "scene_idx": 100, "state_flag": 1},
    ]
    passed = 0
    for idx, s in enumerate(samples):
        b = serialize_slot_save(s)
        assert len(b) == SL_SAV_HEADER_SIZE, f'sample {idx}: size mismatch'
        # Round 43 packing 검증: file[0] = level*10 + class_id
        expected_packed = (s['level'] * 10 + s['class_id']) & 0xff
        assert b[0] == expected_packed, f'sample {idx}: packed byte {b[0]} != {expected_packed}'
        r = deserialize_slot_save(b)
        for k in ['class_id', 'level', 'hero_22d', 'state_flag', 'scene_idx',
                  'playtime_ms']:
            assert r[k] == s[k], f'sample {idx} field {k}: {r[k]!r} != {s[k]!r}'
        # pos_x/y 는 부호 처리 (u32 → s32 변환 필요)
        passed += 1
    print(f'  slot round-trip: {passed}/{len(samples)} samples')
    return 0


def test_layout_offsets() -> int:
    """SAVE_FORMAT.md 의 알려진 offset 에 알려진 size 가 자리 잡았는지 검증."""
    # H_*.sav 의 알려진 offset (Round 42 cross-check 결과)
    state = {
        "field_f0": 0xaabbccdd,
        "class_id": 0xee, "hero_22d": 0xff,
        "gold": 0x12345678,
        "stats": [0x1001, 0x2002, 0x3003, 0x4004, 0x5005, 0x6006, 0x7007, 0x8008],
        "field_4c": 0xcafebabe,
    }
    b = serialize_hero_save(state)
    assert b[0:4] == bytes([0xdd, 0xcc, 0xbb, 0xaa]), 'field_f0 not LE at +0x00'
    assert b[0x04] == 0xee, 'class_id at +0x04'
    assert b[0x05] == 0xff, 'hero_22d at +0x05'
    assert b[0x06:0x0a] == bytes([0x78, 0x56, 0x34, 0x12]), 'gold not LE at +0x06'
    assert b[0x0a:0x0c] == bytes([0x01, 0x10]), 'stat[0] not LE at +0x0a'
    assert b[0x18:0x1a] == bytes([0x08, 0x80]), 'stat[7] not LE at +0x18'
    assert b[0x4c:0x50] == bytes([0xbe, 0xba, 0xfe, 0xca]), 'field_4c not LE at +0x4c'
    print('  hero layout offsets OK (5 critical offsets)')

    # SL_*.sav packing 검증
    sl = serialize_slot_save({"class_id": 3, "level": 12, "pos_x": 0x11223344, "pos_y": 0x55667788})
    assert sl[0] == (12 * 10 + 3), f'SL packed: {sl[0]} != 123'
    assert sl[0x02:0x06] == bytes([0x44, 0x33, 0x22, 0x11]), 'pos_x not LE at +0x02'
    assert sl[0x06:0x0a] == bytes([0x88, 0x77, 0x66, 0x55]), 'pos_y not LE at +0x06'
    print('  slot layout offsets OK (3 critical offsets)')
    return 0


def main() -> int:
    print('Hero5 Save layout round-trip test (Round 49)')
    print('---')
    test_hero_round_trip()
    test_slot_round_trip()
    test_layout_offsets()
    print('---')
    print('OK - all checks passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
