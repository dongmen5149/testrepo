"""Round 59 / 2ZA-2ZC: char_dat / npcg_dat / s4_dat 파싱.

char_dat (348B): 캐릭터 클래스 정의 — 8-15 entries 예상
  R56 byte dump 에서 발견: header(3) + name1(4) + sep(1) + name2(8) + sep(1) + 6B stats
  예: 1b 00 04 b8 ae c3 f7 0c be ee bd e4 c6 ae bf f6 b8 ae be ee 00 04 05 11 0c 00 06 00 00
       size  ?  nl=4 (name1)         nl2=12 (name2)                              ...

npcg_dat (1014B, entropy 3.62): 78 entries × 13B 추정
  R58 dump: 0b 00 01 11 00 00 00 ff ff ff ff ff 06 | 0b 00 01 00 00 00 00 00 00 ff ff ff ff 06 | ...
            size=11 hdr? followed by graphics data

s4_dat (894B): skill text + binary
  R58 dump: 41 00 04 c3 a2 bc fa 00 1c c7 d1 20 bc d5 ...
            size=0x41 (65) + nl=4 (name "차스") + body
"""
import struct
from pathlib import Path


def parse_char_dat(data: bytes) -> list[dict]:
    """char_dat: header(3) + name1(4) + name2_len(1) + name2(N) + sep(1) + 6B stats."""
    entries = []
    pos = 0
    while pos < len(data):
        if pos + 3 > len(data):
            break
        size_byte = data[pos]
        _resv = data[pos + 1]
        name1_len = data[pos + 2]
        if size_byte == 0 or name1_len == 0 or pos + size_byte > len(data):
            break
        # name1 from pos+3
        name1_bytes = data[pos + 3 : pos + 3 + name1_len]
        try:
            name1 = name1_bytes.decode("cp949")
        except UnicodeDecodeError:
            name1 = name1_bytes.hex()

        # next byte = name2_len
        n2_off = pos + 3 + name1_len
        if n2_off >= len(data):
            break
        name2_len = data[n2_off]
        name2_bytes = data[n2_off + 1 : n2_off + 1 + name2_len]
        try:
            name2 = name2_bytes.decode("cp949")
        except UnicodeDecodeError:
            name2 = name2_bytes.hex()

        # stats — between name2 end and entry end. Try total = size_byte + 2 (enemy-style trailer).
        stat_start = n2_off + 1 + name2_len
        total = size_byte + 2
        if pos + total > len(data):
            total = size_byte
        stat_bytes = data[stat_start : pos + total]
        entries.append({
            "pos": pos,
            "size": size_byte,
            "total": total,
            "name1": name1, "name1_len": name1_len,
            "name2": name2, "name2_len": name2_len,
            "stats_hex": stat_bytes.hex(" "),
            "stats_bytes": stat_bytes,
        })
        pos += total
    return entries


def parse_npcg_dat(data: bytes) -> list[dict]:
    """npcg_dat: entries with variable size.
       Pattern: size_byte + 00 + small_int(1) + body
       Trailer often ends with `06` (?). Each entry around 13-14B.
    """
    entries = []
    pos = 0
    while pos < len(data):
        if pos + 3 > len(data):
            break
        size_byte = data[pos]
        if size_byte == 0 or pos + size_byte + 2 > len(data):
            break
        # Try total = size_byte + 2 (like enemy)
        total = size_byte + 2
        body = data[pos : pos + total]
        entries.append({
            "pos": pos,
            "size": size_byte,
            "total": total,
            "body_hex": body.hex(" "),
        })
        pos += total
    return entries


def parse_s4_dat(data: bytes) -> list[dict]:
    """s4_dat: variable entries with EUC-KR skill names + body."""
    entries = []
    pos = 0
    while pos < len(data):
        if pos + 3 > len(data):
            break
        size_byte = data[pos]
        _resv = data[pos + 1]
        name_len = data[pos + 2]
        if size_byte == 0 or name_len == 0:
            break
        total = size_byte + 2
        if total < 8 or pos + total > len(data):
            break
        name_bytes = data[pos + 3 : pos + 3 + name_len]
        try:
            name = name_bytes.decode("cp949").rstrip("\0")
        except UnicodeDecodeError:
            name = name_bytes.hex()
        body = data[pos + 3 + name_len : pos + total]
        # Try ASCII description first (often plain Korean text)
        try:
            desc_str = body.decode("cp949", errors="replace").rstrip("\0")
        except Exception:
            desc_str = body.hex()
        entries.append({
            "pos": pos,
            "size": size_byte,
            "name": name,
            "body_len": len(body),
            "desc_preview": desc_str[:80],
            "body_hex_preview": body[:32].hex(" "),
        })
        pos += total
    return entries


def main() -> None:
    EXT = Path("work/h3/extracted")

    # === char_dat ===
    print(f"\n========== char_dat (348B) ==========")
    data = (EXT / "dat" / "char_dat").read_bytes()
    entries = parse_char_dat(data)
    print(f"Parsed {len(entries)} entries\n")
    for e in entries:
        print(f"  0x{e['pos']:03x} size={e['size']}  name1={e['name1']!r:<10}  name2={e['name2']!r:<14}  stats: {e['stats_hex']}")

    # === npcg_dat ===
    print(f"\n========== npcg_dat (1014B) ==========")
    data = (EXT / "npc" / "npcg_dat").read_bytes()
    entries = parse_npcg_dat(data)
    print(f"Parsed {len(entries)} entries")
    for e in entries[:20]:
        print(f"  0x{e['pos']:03x} size={e['size']:>3} total={e['total']:>3}  body: {e['body_hex']}")
    if len(entries) > 20:
        print(f"  ... ({len(entries) - 20} more)")

    # === s4_dat ===
    print(f"\n========== s4_dat (894B) ==========")
    data = (EXT / "skill" / "s4_dat").read_bytes()
    entries = parse_s4_dat(data)
    print(f"Parsed {len(entries)} entries\n")
    for e in entries:
        print(f"  0x{e['pos']:03x} size={e['size']}  name={e['name']!r:<16}  body({e['body_len']}B): {e['desc_preview']!r}")


if __name__ == "__main__":
    main()
