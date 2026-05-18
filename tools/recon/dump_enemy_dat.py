"""Round 56 / 2WA: enemy_dat / enemyh_dat / char_dat / drop_dat structure 분석.

work/h3/extracted/dat/ 에서 발견된 게임 데이터 파일들. Hero3 의 enemy stats
는 binary 외부 dat 파일에 위치 — R55 의 "전투 = NPC table + SCN opcode 조합" 가설 확인.

파일 크기:
  enemy_dat   = 5495 bytes (main enemy table)
  enemyh_dat  = 5495 bytes (hard mode? identical size)
  enemyg_dat  = 3542 bytes (graphics info?)
  char_dat    = 348 bytes  (character classes)
  drop_dat    = 3080 bytes (item drop table)
  droph_dat   = 3080 bytes (hard drop)
  getitem_dat = 400 bytes  (item acquisition)
  des_dat     = 824 bytes  (descriptions/strings)
"""
import struct
from pathlib import Path

DAT_DIR = Path("work/h3/extracted/dat")


def hex_dump(data: bytes, base: int = 0, length: int = 0) -> None:
    """Print 16-byte rows of hex + ASCII."""
    if length == 0:
        length = len(data)
    length = min(length, len(data))
    for row_off in range(0, length, 16):
        chunk = data[row_off:row_off + 16]
        hex_str = " ".join(f"{b:02x}" for b in chunk)
        ascii_str = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in chunk)
        print(f"  +0x{base + row_off:04x}: {hex_str:<47}  |{ascii_str}|")


def main() -> None:
    files = [
        ("enemy_dat",   200),
        ("enemyh_dat",  200),
        ("enemyg_dat",  160),
        ("char_dat",    348),  # entire file (small)
        ("drop_dat",    160),
        ("droph_dat",   160),
        ("getitem_dat", 400),  # entire file
        ("des_dat",     200),
    ]
    for fname, dump_len in files:
        path = DAT_DIR / fname
        if not path.exists():
            print(f"\n=== {fname}: NOT FOUND ===")
            continue
        data = path.read_bytes()
        print(f"\n========== {fname} (total {len(data)}B, dumping first {min(dump_len, len(data))}B) ==========")
        hex_dump(data, 0, dump_len)

        # Try common stride hypotheses (header + entries)
        if fname.startswith("enemy") or fname.startswith("char") or fname == "drop_dat":
            print(f"\n  Stride hypothesis testing:")
            for header_size in [0, 1, 2, 4, 6, 8]:
                rest = len(data) - header_size
                for stride in [40, 48, 50, 52, 54, 56, 60, 64, 70, 72, 80, 84, 88, 96, 100, 104, 108, 110, 120, 128]:
                    if rest > 0 and rest % stride == 0 and rest // stride >= 2:
                        print(f"    header={header_size}B, stride={stride}B → {rest // stride} entries")


if __name__ == "__main__":
    main()
