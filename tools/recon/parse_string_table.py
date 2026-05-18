"""Round 60: menu/*.txt + dat/InGame_txt 의 string table 파싱.

Format (discovered):
  [0..1]  LE16 total_size  (= file size)
  [2..3]  LE16 count       (= number of strings)
  [4..4+2*count)  LE16 offsets (absolute, relative to file start)
  [end of table..EOF]  null-terminated EUC-KR strings

검증:
  chatacterhader_txt (134B): size=0x0086=134 ✓ count=10
  countryheader_txt (62B):   size=0x003e=62 ✓ count=4
    → "네오솔티아", "아스크라", "네오솔티아-수도", "아스크라-수도"
"""
import json
import struct
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def parse_string_table(data: bytes) -> list[str]:
    """[LE16 size][LE16 count][LE16 offsets×count][...strings...]"""
    if len(data) < 4:
        return []
    total = struct.unpack_from("<H", data, 0)[0]
    count = struct.unpack_from("<H", data, 2)[0]
    if total != len(data) or count == 0 or count > 1000:
        return []
    offsets = []
    for i in range(count):
        off = struct.unpack_from("<H", data, 4 + 2 * i)[0]
        if off >= len(data):
            return []
        offsets.append(off)
    strings = []
    for i, off in enumerate(offsets):
        end = offsets[i + 1] if i + 1 < len(offsets) else len(data)
        raw = data[off:end].rstrip(b"\x00")
        try:
            s = raw.decode("cp949")
        except UnicodeDecodeError:
            s = raw.hex()
        strings.append(s)
    return strings


def main() -> None:
    targets = [
        ("menu/chatacterbody_txt", "Class descriptions"),
        ("menu/chatacterhader_txt", "Class names"),
        ("menu/countrybody_txt", "Country descriptions"),
        ("menu/countryheader_txt", "Country names"),
        ("menu/helpbody_txt", "Help text"),
        ("dat/InGame_txt", "In-game UI strings"),
    ]
    EXT = Path("work/h3/extracted")
    OUT = Path("work/h3/recon")

    all_dump = {}
    for relpath, label in targets:
        data = (EXT / relpath).read_bytes()
        strings = parse_string_table(data)
        print(f"\n========== {relpath} ({len(data)}B) — {label} ==========")
        if not strings:
            print(f"  PARSE FAILED — first 32B: {data[:32].hex(' ')}")
            continue
        print(f"  Parsed {len(strings)} strings:")
        for i, s in enumerate(strings):
            preview = s[:120].replace("\n", " | ")
            print(f"  [{i:>3}] {preview!r}")
        all_dump[relpath] = strings

    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "string_tables.json"
    out.write_text(json.dumps(all_dump, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDumped: {out}")


if __name__ == "__main__":
    main()
