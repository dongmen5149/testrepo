#!/usr/bin/env python3
"""Hero5 비표준 DES 변종 — libHeroesLore5.so 의 desRound/startDes/MX_desInit 정확 포팅.

표준 DES 와 동일 테이블 (IP, IP_inv, E, P, S1..S8, PC1, PC2, shift schedule) 을
사용하지만 호출 규약이 뒤바뀌어 있다:

- MX_desEncrypt: KEY4REAL 을 역순으로 뒤집은 다음 startDes(mode=1, ...) 호출.
                 결과적으로 입력 (L0,R0) 에 K_16,...,K_1 을 적용 — 표준 DES decrypt 와 동치.
- MX_desDecrypt: KEY4REAL 을 정방향으로 되돌린 다음 startDes(mode=0, ...) 호출.
                 startDes(mode=0) 은 입력의 두 절반을 swap 한 다음 K_1..K_16 적용.
                 이는 DES 의 "encrypt(swap(C)) = swap(decrypt(C))" 성질을 응용.

LoadResDecrypt 가 calc_*.dat 를 읽을 때 MX_desDecrypt 를 사용하므로,
그 동작을 정확히 복제하는 본 모듈의 `mx_des_decrypt(body, key)` 가 평문을 돌려준다.

사용:
    from h5_des import mx_des_decrypt
    plain = mx_des_decrypt(encrypted_body, b'0EP@KO91')
"""
from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────
# 표준 DES 테이블 (libHeroesLore5.so 에서 추출 검증 완료)
# ─────────────────────────────────────────────────────────────────────────

IP = [
    58, 50, 42, 34, 26, 18, 10, 2, 60, 52, 44, 36, 28, 20, 12, 4,
    62, 54, 46, 38, 30, 22, 14, 6, 64, 56, 48, 40, 32, 24, 16, 8,
    57, 49, 41, 33, 25, 17, 9, 1, 59, 51, 43, 35, 27, 19, 11, 3,
    61, 53, 45, 37, 29, 21, 13, 5, 63, 55, 47, 39, 31, 23, 15, 7,
]

IP_INV = [
    40, 8, 48, 16, 56, 24, 64, 32, 39, 7, 47, 15, 55, 23, 63, 31,
    38, 6, 46, 14, 54, 22, 62, 30, 37, 5, 45, 13, 53, 21, 61, 29,
    36, 4, 44, 12, 52, 20, 60, 28, 35, 3, 43, 11, 51, 19, 59, 27,
    34, 2, 42, 10, 50, 18, 58, 26, 33, 1, 41, 9, 49, 17, 57, 25,
]

E = [
    32, 1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 9, 8, 9, 10, 11, 12, 13,
    12, 13, 14, 15, 16, 17, 16, 17, 18, 19, 20, 21, 20, 21, 22, 23,
    24, 25, 24, 25, 26, 27, 28, 29, 28, 29, 30, 31, 32, 1,
]

P = [
    16, 7, 20, 21, 29, 12, 28, 17, 1, 15, 23, 26, 5, 18, 31, 10,
    2, 8, 24, 14, 32, 27, 3, 9, 19, 13, 30, 6, 22, 11, 4, 25,
]

PC1 = [
    57, 49, 41, 33, 25, 17, 9, 1, 58, 50, 42, 34, 26, 18, 10, 2,
    59, 51, 43, 35, 27, 19, 11, 3, 60, 52, 44, 36, 63, 55, 47, 39,
    31, 23, 15, 7, 62, 54, 46, 38, 30, 22, 14, 6, 61, 53, 45, 37,
    29, 21, 13, 5, 28, 20, 12, 4,
]

PC2 = [
    14, 17, 11, 24, 1, 5, 3, 28, 15, 6, 21, 10, 23, 19, 12, 4,
    26, 8, 16, 7, 27, 20, 13, 2, 41, 52, 31, 37, 47, 55, 30, 40,
    51, 45, 33, 48, 44, 49, 39, 56, 34, 53, 46, 42, 50, 36, 29, 32,
]

SHIFT = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]

SBOX = [
    # S1 (libHeroesLore5 modification: row 3 col 10 = 2 (std=3))
    14, 4, 13, 1, 2, 15, 11, 8, 3, 10, 6, 12, 5, 9, 0, 7,
    0, 15, 7, 4, 14, 2, 13, 1, 10, 6, 12, 11, 9, 5, 3, 8,
    4, 1, 14, 8, 13, 6, 2, 11, 15, 12, 9, 7, 3, 10, 5, 0,
    15, 12, 8, 2, 4, 9, 1, 7, 5, 11, 2, 14, 10, 0, 6, 13,
    # S2
    15, 1, 8, 14, 6, 11, 3, 4, 9, 7, 2, 13, 12, 0, 5, 10,
    3, 13, 4, 7, 15, 2, 8, 14, 12, 0, 1, 10, 6, 9, 11, 5,
    0, 14, 7, 11, 10, 4, 13, 1, 5, 8, 12, 6, 9, 3, 2, 15,
    13, 8, 10, 1, 3, 15, 4, 2, 11, 6, 7, 12, 0, 5, 14, 9,
    # S3
    10, 0, 9, 14, 6, 3, 15, 5, 1, 13, 12, 7, 11, 4, 2, 8,
    13, 7, 0, 9, 3, 4, 6, 10, 2, 8, 5, 14, 12, 11, 15, 1,
    13, 6, 4, 9, 8, 15, 3, 0, 11, 1, 2, 12, 5, 10, 14, 7,
    1, 10, 13, 0, 6, 9, 8, 7, 4, 15, 14, 3, 11, 5, 2, 12,
    # S4
    7, 13, 14, 3, 0, 6, 9, 10, 1, 2, 8, 5, 11, 12, 4, 15,
    13, 8, 11, 5, 6, 15, 0, 3, 4, 7, 2, 12, 1, 10, 14, 9,
    10, 6, 9, 0, 12, 11, 7, 13, 15, 1, 3, 14, 5, 2, 8, 4,
    3, 15, 0, 6, 10, 1, 13, 8, 9, 4, 5, 11, 12, 7, 2, 14,
    # S5
    2, 12, 4, 1, 7, 10, 11, 6, 8, 5, 3, 15, 13, 0, 14, 9,
    14, 11, 2, 12, 4, 7, 13, 1, 5, 0, 15, 10, 3, 9, 8, 6,
    4, 2, 1, 11, 10, 13, 7, 8, 15, 9, 12, 5, 6, 3, 0, 14,
    11, 8, 12, 7, 1, 14, 2, 13, 6, 15, 0, 9, 10, 4, 5, 3,
    # S6
    12, 1, 10, 15, 9, 2, 6, 8, 0, 13, 3, 4, 14, 7, 5, 11,
    10, 15, 4, 2, 7, 12, 9, 5, 6, 1, 13, 14, 0, 11, 3, 8,
    9, 14, 15, 5, 2, 8, 12, 3, 7, 0, 4, 10, 1, 13, 11, 6,
    4, 3, 2, 12, 9, 5, 15, 10, 11, 14, 1, 7, 6, 0, 8, 13,
    # S7
    4, 11, 2, 14, 15, 0, 8, 13, 3, 12, 9, 7, 5, 10, 6, 1,
    13, 0, 11, 7, 4, 9, 1, 10, 14, 3, 5, 12, 2, 15, 8, 6,
    1, 4, 11, 13, 12, 3, 7, 14, 10, 15, 6, 8, 0, 5, 9, 2,
    6, 11, 13, 8, 1, 4, 10, 7, 9, 5, 0, 15, 14, 2, 3, 12,
    # S8
    13, 2, 8, 4, 6, 15, 11, 1, 10, 9, 3, 14, 5, 0, 12, 7,
    1, 15, 13, 8, 10, 3, 7, 4, 12, 5, 6, 11, 0, 14, 9, 2,
    7, 11, 4, 1, 9, 12, 14, 2, 0, 6, 10, 13, 15, 3, 5, 8,
    2, 1, 14, 7, 4, 10, 8, 13, 15, 12, 9, 0, 3, 5, 6, 11,
]

# ─────────────────────────────────────────────────────────────────────────
# 비트 배열 헬퍼 (.so 의 char2binary / binary2char 와 동일: MSB-first)
# ─────────────────────────────────────────────────────────────────────────


def bytes_to_bits(data: bytes) -> list[int]:
    """각 바이트를 8비트로 (MSB-first) 펼침."""
    bits: list[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits: list[int]) -> bytes:
    """8비트씩 묶어 바이트 (MSB-first)."""
    out = bytearray()
    for i in range(0, len(bits), 8):
        b = 0
        for j in range(8):
            b = (b << 1) | bits[i + j]
        out.append(b)
    return bytes(out)


# ─────────────────────────────────────────────────────────────────────────
# 키 스케줄 (MX_desInit 등가)
# ─────────────────────────────────────────────────────────────────────────


def key_schedule(key: bytes) -> list[list[int]]:
    """8바이트 키 → 16개 라운드 서브키 (각 48비트 = 48 ints)."""
    if len(key) > 8:
        key = key[:8]
    elif len(key) < 8:
        key = key + b"\x00" * (8 - len(key))
    bits64 = bytes_to_bits(key)             # 64 bits
    after_pc1 = [bits64[PC1[i] - 1] for i in range(56)]
    C = after_pc1[:28]
    D = after_pc1[28:]
    subkeys: list[list[int]] = []
    for shift in SHIFT:
        C = C[shift:] + C[:shift]
        D = D[shift:] + D[:shift]
        CD = C + D
        subkey = [CD[PC2[i] - 1] for i in range(48)]
        subkeys.append(subkey)
    return subkeys


# ─────────────────────────────────────────────────────────────────────────
# F-함수 + 라운드 (.so 의 desRound 내부 한 라운드)
# ─────────────────────────────────────────────────────────────────────────


def feistel_F(R: list[int], K: list[int]) -> list[int]:
    """E → XOR K → S-box → P. 모두 비트 배열."""
    expanded = [R[E[i] - 1] for i in range(48)]
    xored = [expanded[i] ^ K[i] for i in range(48)]
    sbox_out: list[int] = []
    for s in range(8):
        b0, b1, b2, b3, b4, b5 = xored[s * 6 : s * 6 + 6]
        row = (b0 << 1) | b5
        col = (b1 << 3) | (b2 << 2) | (b3 << 1) | b4
        val = SBOX[s * 64 + row * 16 + col]
        for k in range(3, -1, -1):
            sbox_out.append((val >> k) & 1)
    return [sbox_out[P[i] - 1] for i in range(32)]


def des_block(L: list[int], R: list[int], subkeys: list[list[int]]) -> tuple[list[int], list[int]]:
    """16라운드 Feistel. 반환 (L_16, R_16)."""
    for i in range(16):
        L_new = R
        R_new = [L[j] ^ b for j, b in enumerate(feistel_F(R, subkeys[i]))]
        L, R = L_new, R_new
    return L, R


# ─────────────────────────────────────────────────────────────────────────
# startDes 의 두 모드 (mode=1 encrypt-path / mode=0 decrypt-path)
# ─────────────────────────────────────────────────────────────────────────


def start_des_block(block8: bytes, subkeys: list[list[int]], mode: int) -> bytes:
    """startDes 의 한 8-byte block 처리.

    mode == 1: L = ip[0..31],  R = ip[32..63]   (표준 split)
    mode == 0: L = ip[32..63], R = ip[0..31]    (decrypt-path 의 swap)
    16 라운드 후 combine = R || L, IP_inv 적용 → 출력 8 byte.
    """
    bits = bytes_to_bits(block8)
    after_ip = [bits[IP[i] - 1] for i in range(64)]
    if mode == 1:
        L, R = after_ip[:32], after_ip[32:]
    else:
        L, R = after_ip[32:], after_ip[:32]
    L16, R16 = des_block(L, R, subkeys)
    pre_inv = R16 + L16
    after_inv = [pre_inv[IP_INV[i] - 1] for i in range(64)]
    return bits_to_bytes(after_inv)


# ─────────────────────────────────────────────────────────────────────────
# MX_desEncrypt / MX_desDecrypt 고수준 진입점
# ─────────────────────────────────────────────────────────────────────────


def mx_des_encrypt(data: bytes, key: bytes = b"0EP@KO91") -> bytes:
    """MX_desEncrypt: MX_desInit 직후 init_flag=1 이면 reversal SKIP.

    즉 첫 호출 시 KEY4REAL = [K_1..K_16] 그대로 startDes(mode=1) → 표준 DES encrypt.
    """
    subkeys = key_schedule(key)  # [K_1..K_16]
    n = len(data) // 8
    out = bytearray()
    for i in range(n):
        out += start_des_block(data[i * 8 : (i + 1) * 8], subkeys, mode=1)
    return bytes(out)


def mx_des_decrypt(data: bytes, key: bytes = b"0EP@KO91") -> bytes:
    """MX_desDecrypt: MX_desInit 직후 init_flag=1 → reversal 수행.

    KEY4REAL = [K_16..K_1] 로 뒤집은 다음 startDes(mode=0).
    """
    subkeys = key_schedule(key)
    subkeys_rev = list(reversed(subkeys))
    n = len(data) // 8
    out = bytearray()
    for i in range(n):
        out += start_des_block(data[i * 8 : (i + 1) * 8], subkeys_rev, mode=0)
    return bytes(out)


# ─────────────────────────────────────────────────────────────────────────
# CLI: 전형 사용 — calc_*.dat 복호 + MD5 검증
# ─────────────────────────────────────────────────────────────────────────


if __name__ == "__main__":
    import argparse
    import hashlib
    from pathlib import Path

    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="암호 파일 경로 또는 디렉토리")
    ap.add_argument("--key", default="0EP@KO91")
    ap.add_argument("--encrypt", action="store_true", help="복호 대신 암호화")
    args = ap.parse_args()

    p = Path(args.path)
    files = [p] if p.is_file() else sorted(p.iterdir())
    for f in files:
        if not f.is_file():
            continue
        data = f.read_bytes()
        if len(data) < 24 or (len(data) - 16) % 8 != 0:
            continue
        md5_hdr = data[:16]
        body = data[16:]
        plain = mx_des_decrypt(body, args.key.encode())
        ok = hashlib.md5(plain).digest() == md5_hdr
        print(f"{f.name}: md5_match={ok} body={len(body)}")
        if ok:
            out = f.with_suffix(".plain")
            out.write_bytes(plain)
            print(f"  → {out}")
