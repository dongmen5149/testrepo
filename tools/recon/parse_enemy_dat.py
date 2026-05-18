"""Round 56 / 2WA: enemy_dat 의 모든 entries 파싱.

발견된 구조 (byte 0..2 header + name + '@' + 19B stats):
  [0]: total entry size
  [1]: reserved (0)
  [2]: name length (incl '@')
  [3..3+name_len-1]: EUC-KR name + '@'
  [3+name_len..size-1]: 19-byte stat block

stat block hypothesis (after lvl byte + 3 padding):
  +0:     level (byte)
  +1..+3: padding 0
  +4..+5: int16 BE (HP or MP?)
  +6..+7: int16 BE (HP/main stat)
  +8..+9: int16 BE
  +10..+11: int16 BE (gold?)
  +12..+13: int16 BE (atk?)
  +14..+15: int16 BE
  +16: byte
  +17: byte
  +18: byte
"""
import struct
from pathlib import Path


def parse_entries(data: bytes) -> list[dict]:
    """Entry layout (revised after Round 56 dump):
       [size_minus_2] [00] [name_len] [name + '@'] [19B stats] [01 1e trailer]
       total = size_minus_2 + 2
    """
    entries = []
    pos = 0
    while pos < len(data):
        if pos + 3 > len(data):
            break
        size_byte = data[pos]
        _resv = data[pos + 1]
        name_len = data[pos + 2]
        total_size = size_byte + 2                # incl 2-byte trailer "01 1e"
        if total_size < 24 or pos + total_size > len(data):
            break
        name_with_sep = data[pos + 3 : pos + 3 + name_len]
        name_bytes = name_with_sep.rstrip(b"@")
        stat_start = pos + 3 + name_len
        stat_block = data[stat_start : stat_start + 19]
        trailer = data[stat_start + 19 : stat_start + 21]
        try:
            name_str = name_bytes.decode("cp949")
        except UnicodeDecodeError:
            name_str = name_bytes.hex()
        entries.append({
            "pos": pos,
            "size_byte": size_byte,
            "total": total_size,
            "name_len": name_len,
            "name": name_str,
            "stat_len": len(stat_block),
            "stats": stat_block.hex(" "),
            "stats_bytes": stat_block,
            "trailer": trailer.hex(),
        })
        pos += total_size
    return entries


def interpret_stats(stat_bytes: bytes) -> dict:
    """Interpret 19-byte stat block."""
    if len(stat_bytes) < 19:
        return {"raw": stat_bytes.hex()}
    b = stat_bytes
    return {
        "lvl": b[0],
        "pad": b[1:4].hex(),
        "f4_5": struct.unpack(">H", b[4:6])[0],
        "f6_7": struct.unpack(">H", b[6:8])[0],
        "f8_9": struct.unpack(">H", b[8:10])[0],
        "f10_11": struct.unpack(">H", b[10:12])[0],
        "f12_13": struct.unpack(">H", b[12:14])[0],
        "f14_15": struct.unpack(">H", b[14:16])[0],
        "f16": b[16],
        "f17": b[17],
        "f18": b[18],
    }


def main() -> None:
    for fname in ["enemy_dat", "enemyh_dat"]:
        path = Path("work/h3/extracted/dat") / fname
        data = path.read_bytes()
        entries = parse_entries(data)
        print(f"\n========== {fname}: {len(data)}B, {len(entries)} entries ==========")
        print(f"\n  {'pos':>5}  {'size':>4}  {'name':<18}  lvl  {'f4_5':>5}  {'f6_7':>5}  {'f8_9':>5}  {'f10_11':>6}  {'f12_13':>6}  {'f14_15':>6}  f16  f17  f18")
        for e in entries[:20]:
            s = interpret_stats(e["stats_bytes"])
            print(f"  0x{e['pos']:04x}  {e['total']:>4}  {e['name']:<18}  {s.get('lvl', 0):>3}  "
                  f"{s.get('f4_5', 0):>5}  {s.get('f6_7', 0):>5}  {s.get('f8_9', 0):>5}  "
                  f"{s.get('f10_11', 0):>6}  {s.get('f12_13', 0):>6}  {s.get('f14_15', 0):>6}  "
                  f"{s.get('f16', 0):>3}  {s.get('f17', 0):>3}  {s.get('f18', 0):>3}")

        # Field stats across all entries
        if entries:
            print(f"\n  Total entries: {len(entries)}")
            fields = ["lvl", "f4_5", "f6_7", "f8_9", "f10_11", "f12_13", "f14_15", "f16", "f17", "f18"]
            print(f"  field min/max/avg:")
            for f in fields:
                vals = [interpret_stats(e["stats_bytes"]).get(f, 0) for e in entries]
                if vals:
                    print(f"    {f:>7}: min={min(vals):>5}  max={max(vals):>5}  avg={sum(vals)//len(vals):>5}")


if __name__ == "__main__":
    main()
