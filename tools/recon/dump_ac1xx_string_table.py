"""Round 55 / 2VA: 0xac1xx-0xac25c 영역 dump (paired storage 가설 검증 완료
후 asset path table 의 전체 entry 확인).

GOT[+0xd28] = 0xac25c, GOT[+0xd38] = 0xac26c — paired 가 아니라
0xac1xx 부터 시작하는 asset path string table 내 두 인접 entry 인지 검증.
"""
from pathlib import Path

DATA = Path("work/h3/extracted/client.bin64000").read_bytes()


def main() -> None:
    # Look BEFORE 0xac25c to find string table start
    start_search = 0xac150
    end = 0xac280
    print(f"=== Byte dump 0x{start_search:05x}..0x{end:05x} (search backward for string table start) ===")
    for line_off in range(0, end - start_search, 16):
        addr = start_search + line_off
        if addr + 16 > len(DATA):
            break
        line_bytes = DATA[addr:addr + 16]
        hex_str = " ".join(f"{b:02x}" for b in line_bytes)
        ascii_str = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in line_bytes)
        marker = ""
        if addr <= 0xac25c < addr + 16:
            marker = "  ← +0xd28 anchor"
        elif addr <= 0xac26c < addr + 16:
            marker = "  ← +0xd38 anchor"
        print(f"  0x{addr:05x}: {hex_str}  |{ascii_str}|{marker}")


if __name__ == "__main__":
    main()
