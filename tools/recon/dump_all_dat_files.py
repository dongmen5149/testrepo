"""Round 58 / 2YA: 모든 dat 파일의 raw byte dump (entropy 분석 + 평문/암호화 판별).

R56 에서 enemy_dat 만 평문 EUC-KR 확인. 이제 boss/quest/shop/smith/npcg/s4 dat 도 검증.
"""
from pathlib import Path
from collections import Counter
import math

ALL_DAT_FILES = [
    ("boss/boss_dat",      508),
    ("boss/bossh_dat",     508),
    ("dat/quest_00_dat",   4851),
    ("dat/quest_01_dat",   4216),
    ("dat/quest_10_dat",   5360),
    ("dat/quest_11_dat",   4269),
    ("dat/shop_dat",       72),
    ("dat/shoph_dat",      72),
    ("dat/smith_dat",      896),
    ("dat/smithh_dat",     896),
    ("npc/npcg_dat",       1014),
    ("skill/s4_dat",       894),
    # known from R56
    ("dat/drop_dat",       3080),
    ("dat/droph_dat",      3080),
    ("dat/getitem_dat",    400),
]


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    cnt = Counter(data)
    total = len(data)
    h = 0.0
    for c in cnt.values():
        p = c / total
        h -= p * math.log2(p)
    return h


def main() -> None:
    EXTRACTED = Path("work/h3/extracted")
    for rel, _expect_size in ALL_DAT_FILES:
        path = EXTRACTED / rel
        data = path.read_bytes()
        h = shannon_entropy(data)
        is_8x = (len(data) % 8 == 0)
        ascii_count = sum(1 for b in data if 0x20 <= b < 0x7f)
        korean_high = sum(1 for b in data if 0xa0 <= b < 0xff)
        null_count = data.count(0)

        # detect korean EUC-KR pattern: paired bytes (high, mid)
        euc_pairs = 0
        for i in range(len(data) - 1):
            b1, b2 = data[i], data[i + 1]
            if 0xa1 <= b1 <= 0xfe and 0xa1 <= b2 <= 0xfe:
                euc_pairs += 1

        flag = ""
        if h < 5.5:
            flag = " ★ LOW ENTROPY (plaintext or structured)"
        elif h > 7.5:
            flag = " ★ HIGH ENTROPY (encrypted/compressed)"

        print(f"\n=== {rel} ({len(data)}B, mod8={is_8x}) ===")
        print(f"  entropy: {h:.3f}/8.0{flag}")
        print(f"  ascii={ascii_count} ({100*ascii_count//len(data)}%)  "
              f"korean-high={korean_high}  null={null_count}  "
              f"euc-kr-pairs={euc_pairs}")
        # First 64B hex + ASCII
        chunk = data[:64]
        hex_str = " ".join(f"{b:02x}" for b in chunk)
        ascii_str = "".join(chr(b) if 0x20 <= b < 0x7f else "." for b in chunk)
        print(f"  first 64B hex: {hex_str}")
        print(f"  first 64B asc: |{ascii_str}|")


if __name__ == "__main__":
    main()
