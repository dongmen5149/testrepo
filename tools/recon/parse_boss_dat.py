"""Round 58 / 2YA: boss_dat / bossh_dat 파싱 (enemy_dat 와 동일 구조 가정).

boss_dat (508B) first bytes: 1e 00 04 b8 ae c3 f7 ...
  = size(0x1e=30) + 00 + name_len(0x04) + 4B EUC-KR name "미츠"/"미차" + stats

Expected structure (R56 enemy_dat 와 동일):
  [size-2] [00] [name_len] [name + '@'?] [19B stat block] [trailer 01 1e?]
"""
import struct
from pathlib import Path

from parse_enemy_dat import parse_entries, interpret_stats


def main() -> None:
    for fname in ["boss/boss_dat", "boss/bossh_dat"]:
        path = Path("work/h3/extracted") / fname
        data = path.read_bytes()
        entries = parse_entries(data)
        print(f"\n========== {fname}: {len(data)}B, {len(entries)} entries ==========")
        print(f"\n  {'pos':>5}  {'size':>4}  {'name':<10}  lvl  {'f4_5':>5}  {'f6_7':>5}  {'f8_9':>5}  {'f10_11':>6}  {'f12_13':>6}  {'f14_15':>6}  f16  f17  f18  trailer")
        for e in entries:
            s = interpret_stats(e["stats_bytes"])
            print(f"  0x{e['pos']:04x}  {e['total']:>4}  {e['name']:<10}  {s.get('lvl', 0):>3}  "
                  f"{s.get('f4_5', 0):>5}  {s.get('f6_7', 0):>5}  {s.get('f8_9', 0):>5}  "
                  f"{s.get('f10_11', 0):>6}  {s.get('f12_13', 0):>6}  {s.get('f14_15', 0):>6}  "
                  f"{s.get('f16', 0):>3}  {s.get('f17', 0):>3}  {s.get('f18', 0):>3}  {e.get('trailer', '')}")

        # bytes after last entry
        if entries:
            last = entries[-1]
            end_pos = last["pos"] + last["total"]
            if end_pos < len(data):
                remaining = data[end_pos:].hex(" ")
                print(f"\n  remaining {len(data) - end_pos}B after last entry: {remaining[:200]}")


if __name__ == "__main__":
    main()
