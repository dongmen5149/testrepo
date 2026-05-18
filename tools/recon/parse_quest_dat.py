"""Round 58 / 2YA: quest_*_dat 파싱.

quest_00_dat (4851B) entropy=5.94, Korean dominant — quest 텍스트 평문.
첫 byte: 61 00 0c = size 0x61 (97) + 00 + name_len 0x0c (12).
4 files: quest_00 (4851B), quest_01 (4216B), quest_10 (5360B), quest_11 (4269B).

가설: same enemy_dat-like layout but with quest description as "name" + text body.
"""
from pathlib import Path


def parse_quest_entries(data: bytes) -> list[dict]:
    """Try variable-length entry parsing."""
    entries = []
    pos = 0
    while pos < len(data):
        if pos + 3 > len(data):
            break
        size_byte = data[pos]
        _resv = data[pos + 1]
        name_len = data[pos + 2]
        total = size_byte + 2
        if total < 16 or pos + total > len(data):
            # Try without +2 fallback
            total = size_byte
            if total < 16 or pos + total > len(data):
                print(f"  parse halted at 0x{pos:04x} (size_byte=0x{size_byte:02x}, name_len=0x{name_len:02x})")
                break
        if name_len > total or name_len == 0:
            print(f"  invalid entry at 0x{pos:04x}: size=0x{size_byte:02x}, name_len=0x{name_len:02x}")
            break
        name_with_sep = data[pos + 3 : pos + 3 + name_len]
        name_bytes = name_with_sep.rstrip(b"@\0")
        try:
            name_str = name_bytes.decode("cp949")
        except UnicodeDecodeError:
            name_str = name_bytes.hex()
        body = data[pos + 3 + name_len : pos + total]
        try:
            body_str = body.decode("cp949", errors="replace").rstrip("\0")
        except Exception:
            body_str = body.hex()
        entries.append({
            "pos": pos,
            "total": total,
            "name_len": name_len,
            "name": name_str,
            "body_len": len(body),
            "body_preview": body_str[:80],
        })
        pos += total
    return entries


def main() -> None:
    for fname in ["quest_00_dat", "quest_01_dat", "quest_10_dat", "quest_11_dat"]:
        path = Path("work/h3/extracted/dat") / fname
        data = path.read_bytes()
        entries = parse_quest_entries(data)
        print(f"\n========== {fname}: {len(data)}B, {len(entries)} entries ==========")
        for i, e in enumerate(entries[:8]):
            print(f"\n  Entry {i} @ 0x{e['pos']:04x} (total={e['total']}B):")
            print(f"    name: {e['name']!r}")
            print(f"    body ({e['body_len']}B preview): {e['body_preview']!r}")
        if len(entries) > 8:
            print(f"\n  ... ({len(entries) - 8} more entries)")


if __name__ == "__main__":
    main()
