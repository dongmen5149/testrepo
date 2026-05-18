"""Round 57 / 2XD: Hero3 의 encrypted dat 파일들 DES 복호화 시도.

key: "0EP@KO91" (8 bytes ASCII, Hero5 와 동일한 DES key)
mode: ECB (가장 흔한 방식, R55 의 H5 정적분석 결과)

대상 파일들 (work/h3/extracted/dat/):
  drop_dat    (3080B = 385 blocks of 8B)
  droph_dat   (3080B)
  getitem_dat ( 400B = 50 blocks)
  des_dat     ( 824B = 103 blocks)
  others (i*_dat) - 일부 가능성
"""
from pathlib import Path

try:
    from Crypto.Cipher import DES
    HAS_PYCRYPTO = True
except ImportError:
    HAS_PYCRYPTO = False
    # Fallback: pure-Python DES
    print("pycryptodome not installed — install via: pip install pycryptodome")
    import sys
    sys.exit(1)


DAT_DIR = Path("work/h3/extracted/dat")
OUT_DIR = Path("work/h3/extracted/dat_decrypted")
OUT_DIR.mkdir(parents=True, exist_ok=True)

KEY = b"0EP@KO91"
assert len(KEY) == 8


def try_decrypt(path: Path) -> None:
    data = path.read_bytes()
    print(f"\n=== {path.name} ({len(data)}B) ===")
    if len(data) % 8 != 0:
        print(f"  size {len(data)} not multiple of 8 — padding required (skip raw ECB)")
        # Still try by padding to multiple of 8 for inspection
        pad_len = 8 - (len(data) % 8)
        padded = data + b"\0" * pad_len
        print(f"  padded to {len(padded)}B")
        data = padded

    cipher = DES.new(KEY, DES.MODE_ECB)
    plain = cipher.decrypt(data)

    out_path = OUT_DIR / (path.name + ".plain")
    out_path.write_bytes(plain)

    # Print first 128B + last 64B
    print(f"  decrypted → {out_path}")
    print(f"  first 64B hex: {plain[:64].hex(' ')}")
    print(f"  first 64B ascii: {''.join(chr(b) if 0x20 <= b < 0x7f else '.' for b in plain[:64])}")
    print(f"  last  32B hex: {plain[-32:].hex(' ')}")
    # Check for Korean EUC-KR or ASCII patterns
    korean_count = sum(1 for b in plain if 0xa0 <= b <= 0xfe)
    ascii_count = sum(1 for b in plain if 0x20 <= b < 0x7f)
    null_count = plain.count(0)
    print(f"  byte distribution: korean-range={korean_count} ascii={ascii_count} null={null_count} (total={len(plain)})")


def main() -> None:
    print(f"key: {KEY!r} (8 bytes, DES ECB mode)")
    for fname in ["drop_dat", "droph_dat", "getitem_dat", "des_dat",
                  "char_dat", "i0_dat", "i1_dat", "i15_dat"]:
        path = DAT_DIR / fname
        if path.exists():
            try_decrypt(path)


if __name__ == "__main__":
    main()
