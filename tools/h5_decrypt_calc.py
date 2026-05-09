#!/usr/bin/env python3
"""calc_pl/en/sk.dat 평문 dump.

LoadResDecrypt 와 동일한 처리:
  [16B MD5(plain)][DES-encrypted body]
DES-decrypt body, 검증, 평문 저장.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from h5_des import mx_des_decrypt  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
VFS = REPO / "work" / "h5" / "vfs_entries"
OUT = REPO / "work" / "h5" / "analysis"
OUT.mkdir(parents=True, exist_ok=True)

CALC_FILES = {
    0: "calc_en",
    1: "calc_pl",
    2: "calc_sk",
}


def main() -> int:
    for idx, name in CALC_FILES.items():
        matches = list(VFS.glob(f"{idx:05d}_*.bin"))
        if not matches:
            print(f"missing vfs entry {idx}", file=sys.stderr)
            continue
        data = matches[0].read_bytes()
        if len(data) < 24 or (len(data) - 16) % 8 != 0:
            print(f"{name}: invalid length {len(data)}")
            continue
        md5_hdr = data[:16]
        body = data[16:]
        plain = mx_des_decrypt(body)
        ok = hashlib.md5(plain).digest() == md5_hdr
        out_file = OUT / f"{name}_plain.bin"
        out_file.write_bytes(plain)
        print(f"{name}: md5_match={ok}, plain_len={len(plain)} → {out_file.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
