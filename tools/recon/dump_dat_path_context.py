"""Round 57 / 2XA: dat path strings 주변 영역 dump + pointer table 검색.

25개 path string 의 주소 → 어떤 reference 패턴인지 식별:
1. 주변 바이트로 string layout 확인 (length-prefixed? @-terminated? null-terminated?)
2. 같은 영역 (0xa5xxx, 0xa63xx, 0xa6axx, 0xab4xx) 에서 pointer table 검색
"""
import struct
from pathlib import Path

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()
GOT_BASE = 0xb2c40

# Found in Round 57 / 2XA grep
DAT_STRINGS = {
    0xa5d64: "/boss/bossh_dat",
    0xa5d74: "/boss/boss_dat",
    0xa6394: "/dat/enemyh_dat",
    0xa63a4: "/dat/enemy_dat",
    0xa63b4: "/dat/enemyg_dat",
    0xa63c4: "/dat/droph_dat",
    0xa63d4: "/dat/drop_dat",
    0xa6878: "/dat/char_dat",
    0xa6ab4: "/dat/getitem_dat",
    0xa7130: "/dat/InGame_txt",
    0xa889c: "/dat/ph001_pa",
    0xa8c18: "/enemy/e000_cif",
    0xa8c28: "/enemy/e1000_bm",
    0xa8c38: "/enemy/e0100_bm",
    0xa8c48: "/dat/pe000_pa",
    0xa8c58: "/enemy/e100_cif",
    0xa91a0: "/dat/i0_dat",
    0xa91f8: "/dat/quest_00_dat",
    0xab410: "/npc/npcg_dat",
    0xab420: "/dat/shoph_dat",
    0xab430: "/dat/shop_dat",
    0xab724: "/dat/smithh_dat",
    0xab734: "/dat/smith_dat",
    0xac584: "/dat/des_dat",
    0xad138: "/skill/s4_dat",
}


def hex_line(addr: int, length: int = 16) -> str:
    bytes_ = DATA[addr:addr + length]
    hex_str = " ".join(f"{b:02x}" for b in bytes_)
    ascii_str = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in bytes_)
    return f"  0x{addr:05x}: {hex_str}  |{ascii_str}|"


def main() -> None:
    # Dump 16B before each path string + 16B of string
    print(f"=== Path string surrounding bytes (8B before + 24B after) ===\n")
    for path_addr, path in sorted(DAT_STRINGS.items()):
        start = max(0, path_addr - 8)
        end = min(len(DATA), path_addr + 24)
        bytes_ = DATA[start:end]
        # Compute position of string within
        rel_pos = path_addr - start
        hex_parts = []
        ascii_parts = []
        for i, b in enumerate(bytes_):
            marker = "★" if i == rel_pos else " "
            hex_parts.append(f"{b:02x}")
            ascii_parts.append(chr(b) if 0x20 <= b < 0x7f else ".")
        hex_str = " ".join(hex_parts[:rel_pos]) + "  ★" + " ".join(hex_parts[rel_pos:rel_pos+24])
        print(f"  {path:<20} @ 0x{path_addr:05x}:")
        print(f"  before(8B): {' '.join(hex_parts[:rel_pos])}")
        print(f"  string  : {' '.join(hex_parts[rel_pos:])}")
        print()

    # Look for pointer table — sequential 4-byte aligned pointers
    print(f"\n=== Searching for pointer tables that contain dat string addrs ===")
    string_addrs_set = set(DAT_STRINGS.keys())

    # Scan binary for 4-byte aligned words matching a string address
    table_hits = {}  # word_addr → string addr
    for addr in range(0, len(DATA) - 4, 4):
        val = struct.unpack("<I", DATA[addr:addr + 4])[0]
        if val in string_addrs_set:
            table_hits[addr] = val

    # Cluster table hits into regions
    print(f"Found {len(table_hits)} word locations referencing dat path strings.")
    if not table_hits:
        return
    hit_addrs = sorted(table_hits.keys())
    # Find clusters (consecutive 4-byte hits)
    clusters = []
    cur_cluster = [hit_addrs[0]]
    for a in hit_addrs[1:]:
        if a - cur_cluster[-1] <= 16:
            cur_cluster.append(a)
        else:
            clusters.append(cur_cluster)
            cur_cluster = [a]
    clusters.append(cur_cluster)

    print(f"=== Clustered into {len(clusters)} regions ===\n")
    for cl in clusters:
        print(f"  Cluster @ 0x{cl[0]:05x}..0x{cl[-1] + 4:05x} ({len(cl)} entries):")
        for a in cl:
            v = table_hits[a]
            name = DAT_STRINGS.get(v, "?")
            print(f"    +0x{a - cl[0]:04x}  0x{a:05x} → 0x{v:05x}  {name}")


if __name__ == "__main__":
    main()
