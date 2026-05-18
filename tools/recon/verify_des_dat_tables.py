"""Round 57 / 2XD: des_dat 파일이 DES 알고리즘 IP table 인지 검증.

표준 DES Initial Permutation (1-indexed, ITU-T X.509 spec):
   58, 50, 42, 34, 26, 18, 10,  2,
   60, 52, 44, 36, 28, 20, 12,  4,
   62, 54, 46, 38, 30, 22, 14,  6,
   64, 56, 48, 40, 32, 24, 16,  8,
   57, 49, 41, 33, 25, 17,  9,  1,
   59, 51, 43, 35, 27, 19, 11,  3,
   61, 53, 45, 37, 29, 21, 13,  5,
   63, 55, 47, 39, 31, 23, 15,  7

0-indexed (subtract 1) → first byte = 57 = 0x39
hex first row (0-indexed): 39 31 29 21 19 11 09 01

But des_dat first row is: 3a 32 2a 22 1a 12 0a 02 = 58 50 42 34 26 18 10 2 (1-indexed!)

So des_dat stores IP in 1-INDEXED form (standard FIPS PUB 46-3).
"""
from pathlib import Path

DAT_DIR = Path("work/h3/extracted/dat")

STANDARD_IP_1IDX = [
    58, 50, 42, 34, 26, 18, 10,  2,
    60, 52, 44, 36, 28, 20, 12,  4,
    62, 54, 46, 38, 30, 22, 14,  6,
    64, 56, 48, 40, 32, 24, 16,  8,
    57, 49, 41, 33, 25, 17,  9,  1,
    59, 51, 43, 35, 27, 19, 11,  3,
    61, 53, 45, 37, 29, 21, 13,  5,
    63, 55, 47, 39, 31, 23, 15,  7,
]

STANDARD_IP_INV_1IDX = [
    40,  8, 48, 16, 56, 24, 64, 32,
    39,  7, 47, 15, 55, 23, 63, 31,
    38,  6, 46, 14, 54, 22, 62, 30,
    37,  5, 45, 13, 53, 21, 61, 29,
    36,  4, 44, 12, 52, 20, 60, 28,
    35,  3, 43, 11, 51, 19, 59, 27,
    34,  2, 42, 10, 50, 18, 58, 26,
    33,  1, 41,  9, 49, 17, 57, 25,
]


def main() -> None:
    data = (DAT_DIR / "des_dat").read_bytes()
    print(f"des_dat size: {len(data)}B")
    print(f"\nFirst 64 bytes (= IP table?):")
    print(f"  expected (IP, 1-idx): {STANDARD_IP_1IDX[:16]}")
    print(f"  actual:               {list(data[:16])}")
    match_ip = list(data[:64]) == STANDARD_IP_1IDX
    print(f"  match IP table?      {match_ip}")

    if match_ip:
        print(f"\nNext 64 bytes (= IP^-1 table?):")
        print(f"  expected (IP^-1, 1-idx): {STANDARD_IP_INV_1IDX[:16]}")
        print(f"  actual:                  {list(data[64:80])}")
        match_ipinv = list(data[64:128]) == STANDARD_IP_INV_1IDX
        print(f"  match IP^-1?            {match_ipinv}")

    # Show byte structure
    print(f"\n=== Hex dump of des_dat (first 200B) ===")
    for row in range(0, 200, 16):
        line = data[row:row + 16]
        hex_str = " ".join(f"{b:02x}" for b in line)
        dec_str = " ".join(f"{b:3d}" for b in line)
        print(f"  +0x{row:03x}: {hex_str}")
        print(f"         dec: {dec_str}")

    # Try standard DES tables of size:
    # IP: 64 bytes (0..63)
    # IP^-1: 64 bytes (64..127)
    # E: 48 bytes (128..175)
    # P: 32 bytes (176..207)
    # S1..S8: 8*64 = 512 bytes... but des_dat is only 824B
    # PC1: 56 bytes
    # PC2: 48 bytes
    # Total: 64+64+48+32+512+56+48 = 824 bytes ★ exact match!
    print(f"\n=== des_dat 824 bytes = standard DES tables breakdown ===")
    tables = [
        ("IP",     0,    64),
        ("IP^-1",  64,   64),
        ("E",      128,  48),
        ("P",      176,  32),
        ("S1-S8",  208, 512),  # 8 boxes × 64 entries
        ("PC1",    720,  56),
        ("PC2",    776,  48),
    ]
    for name, off, sz in tables:
        if off + sz <= len(data):
            sample = list(data[off:off + min(sz, 8)])
            print(f"  {name:8} offset 0x{off:03x} size {sz:>3}B  first 8: {sample}")


if __name__ == "__main__":
    main()
