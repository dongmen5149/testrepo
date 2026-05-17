"""Hero4 custom DES — S1[58] = 2 (표준 3).

Pure Python DES 구현. 다른 모든 테이블은 표준 FIPS 46 그대로,
S1 의 entry [58] (row 3 col 10) 만 표준값 3 → 2 로 수정.

배경: _DAT_DES 824 byte 의 S1 영역 1 byte 가 표준과 다른 것이 발견되어
(2026-05-18, [tools/recon/verify_h4_dat_des.py](../recon/verify_h4_dat_des.py)),
PyCryptodome/SunJCE stock DES 로는 Hero4 SCN 을 복호화할 수 없을 가능성 검증용.

API: encrypt(key, plaintext) / decrypt(key, ciphertext) — ECB single block (8 bytes).
"""
from __future__ import annotations

# Standard DES tables
IP = [58,50,42,34,26,18,10, 2,60,52,44,36,28,20,12, 4,
      62,54,46,38,30,22,14, 6,64,56,48,40,32,24,16, 8,
      57,49,41,33,25,17, 9, 1,59,51,43,35,27,19,11, 3,
      61,53,45,37,29,21,13, 5,63,55,47,39,31,23,15, 7]
IP_INV = [40, 8,48,16,56,24,64,32,39, 7,47,15,55,23,63,31,
          38, 6,46,14,54,22,62,30,37, 5,45,13,53,21,61,29,
          36, 4,44,12,52,20,60,28,35, 3,43,11,51,19,59,27,
          34, 2,42,10,50,18,58,26,33, 1,41, 9,49,17,57,25]
E = [32, 1, 2, 3, 4, 5, 4, 5, 6, 7, 8, 9,
     8, 9,10,11,12,13,12,13,14,15,16,17,
     16,17,18,19,20,21,20,21,22,23,24,25,
     24,25,26,27,28,29,28,29,30,31,32, 1]
P_TABLE = [16, 7,20,21,29,12,28,17, 1,15,23,26, 5,18,31,10,
            2, 8,24,14,32,27, 3, 9,19,13,30, 6,22,11, 4,25]
PC1 = [57,49,41,33,25,17, 9, 1,58,50,42,34,26,18,10, 2,59,51,43,35,27,19,11, 3,60,52,44,36,
       63,55,47,39,31,23,15, 7,62,54,46,38,30,22,14, 6,61,53,45,37,29,21,13, 5,28,20,12, 4]
PC2 = [14,17,11,24, 1, 5, 3,28,15, 6,21,10,23,19,12, 4,26, 8,16, 7,27,20,13, 2,
       41,52,31,37,47,55,30,40,51,45,33,48,44,49,39,56,34,53,46,42,50,36,29,32]
SHIFT = [1,1,2,2,2,2,2,2,1,2,2,2,2,2,2,1]

# Hero4 modified S-boxes — S1[58] = 2 instead of standard 3
S_HERO4 = [
 [14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7,
  0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8,
  4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0,
  15,12,8,2,4,9,1,7,5,11,2,14,10,0,6,13],  # <-- col 10 changed: 3 → 2
 [15,1,8,14,6,11,3,4,9,7,2,13,12,0,5,10,
  3,13,4,7,15,2,8,14,12,0,1,10,6,9,11,5,
  0,14,7,11,10,4,13,1,5,8,12,6,9,3,2,15,
  13,8,10,1,3,15,4,2,11,6,7,12,0,5,14,9],
 [10,0,9,14,6,3,15,5,1,13,12,7,11,4,2,8,
  13,7,0,9,3,4,6,10,2,8,5,14,12,11,15,1,
  13,6,4,9,8,15,3,0,11,1,2,12,5,10,14,7,
  1,10,13,0,6,9,8,7,4,15,14,3,11,5,2,12],
 [7,13,14,3,0,6,9,10,1,2,8,5,11,12,4,15,
  13,8,11,5,6,15,0,3,4,7,2,12,1,10,14,9,
  10,6,9,0,12,11,7,13,15,1,3,14,5,2,8,4,
  3,15,0,6,10,1,13,8,9,4,5,11,12,7,2,14],
 [2,12,4,1,7,10,11,6,8,5,3,15,13,0,14,9,
  14,11,2,12,4,7,13,1,5,0,15,10,3,9,8,6,
  4,2,1,11,10,13,7,8,15,9,12,5,6,3,0,14,
  11,8,12,7,1,14,2,13,6,15,0,9,10,4,5,3],
 [12,1,10,15,9,2,6,8,0,13,3,4,14,7,5,11,
  10,15,4,2,7,12,9,5,6,1,13,14,0,11,3,8,
  9,14,15,5,2,8,12,3,7,0,4,10,1,13,11,6,
  4,3,2,12,9,5,15,10,11,14,1,7,6,0,8,13],
 [4,11,2,14,15,0,8,13,3,12,9,7,5,10,6,1,
  13,0,11,7,4,9,1,10,14,3,5,12,2,15,8,6,
  1,4,11,13,12,3,7,14,10,15,6,8,0,5,9,2,
  6,11,13,8,1,4,10,7,9,5,0,15,14,2,3,12],
 [13,2,8,4,6,15,11,1,10,9,3,14,5,0,12,7,
  1,15,13,8,10,3,7,4,12,5,6,11,0,14,9,2,
  7,11,4,1,9,12,14,2,0,6,10,13,15,3,5,8,
  2,1,14,7,4,10,8,13,15,12,9,0,3,5,6,11]]


def _bytes_to_bits(data: bytes) -> list[int]:
    """64-bit big-endian. bit 1 = MSB."""
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits


def _bits_to_bytes(bits: list[int]) -> bytes:
    out = bytearray()
    for i in range(0, len(bits), 8):
        b = 0
        for j in range(8):
            b = (b << 1) | bits[i+j]
        out.append(b)
    return bytes(out)


def _permute(bits: list[int], table: list[int]) -> list[int]:
    return [bits[i-1] for i in table]


def _left_rotate(bits: list[int], n: int) -> list[int]:
    return bits[n:] + bits[:n]


def _generate_subkeys(key: bytes) -> list[list[int]]:
    """16 round sub-keys (each 48 bits)."""
    key_bits = _bytes_to_bits(key)
    permuted = _permute(key_bits, PC1)
    C = permuted[:28]
    D = permuted[28:]
    subkeys = []
    for shift in SHIFT:
        C = _left_rotate(C, shift)
        D = _left_rotate(D, shift)
        sk = _permute(C + D, PC2)
        subkeys.append(sk)
    return subkeys


def _f(R: list[int], subkey: list[int], s_boxes: list[list[int]]) -> list[int]:
    expanded = _permute(R, E)
    xored = [a ^ b for a, b in zip(expanded, subkey)]
    # S-box substitution: 8 × 6-bit → 8 × 4-bit
    out_bits = []
    for i in range(8):
        block = xored[i*6:(i+1)*6]
        row = (block[0] << 1) | block[5]
        col = (block[1] << 3) | (block[2] << 2) | (block[3] << 1) | block[4]
        val = s_boxes[i][row * 16 + col]
        for j in range(3, -1, -1):
            out_bits.append((val >> j) & 1)
    return _permute(out_bits, P_TABLE)


def _crypt_block(block: bytes, subkeys: list[list[int]], s_boxes: list[list[int]],
                 decrypt: bool = False) -> bytes:
    bits = _bytes_to_bits(block)
    bits = _permute(bits, IP)
    L = bits[:32]
    R = bits[32:]
    rounds = list(range(16))
    if decrypt:
        rounds = rounds[::-1]
    for r in rounds:
        sk = subkeys[r]
        new_L = R
        new_R = [a ^ b for a, b in zip(L, _f(R, sk, s_boxes))]
        L, R = new_L, new_R
    combined = R + L  # swap before final permutation
    final = _permute(combined, IP_INV)
    return _bits_to_bytes(final)


def encrypt(key: bytes, plaintext: bytes, s_boxes: list[list[int]] = S_HERO4) -> bytes:
    if len(key) != 8 or len(plaintext) % 8 != 0:
        raise ValueError(f'key must be 8 bytes, plaintext multiple of 8 (got key={len(key)}, pt={len(plaintext)})')
    subkeys = _generate_subkeys(key)
    out = bytearray()
    for i in range(0, len(plaintext), 8):
        out += _crypt_block(plaintext[i:i+8], subkeys, s_boxes, decrypt=False)
    return bytes(out)


def decrypt(key: bytes, ciphertext: bytes, s_boxes: list[list[int]] = S_HERO4) -> bytes:
    if len(key) != 8 or len(ciphertext) % 8 != 0:
        raise ValueError(f'key must be 8 bytes, ciphertext multiple of 8')
    subkeys = _generate_subkeys(key)
    out = bytearray()
    for i in range(0, len(ciphertext), 8):
        out += _crypt_block(ciphertext[i:i+8], subkeys, s_boxes, decrypt=True)
    return bytes(out)


if __name__ == '__main__':
    # Sanity test: encrypt+decrypt with standard S-boxes should give known answers
    from Crypto.Cipher import DES as RefDES
    S_STD = [list(row) for row in S_HERO4]
    S_STD[0][58] = 3  # restore standard S1[58]
    test_key = b'12345678'
    test_pt = b'ABCDEFGH'
    custom_ct = encrypt(test_key, test_pt, s_boxes=S_STD)
    ref_ct = RefDES.new(test_key, RefDES.MODE_ECB).encrypt(test_pt)
    print(f'Self-test (standard S-boxes):')
    print(f'  PyCrypto:   {ref_ct.hex()}')
    print(f'  Custom-Std: {custom_ct.hex()}')
    print(f'  Match: {ref_ct == custom_ct}')
    # Roundtrip with Hero4 S-boxes
    h4_ct = encrypt(test_key, test_pt)
    h4_pt = decrypt(test_key, h4_ct)
    print(f'\nHero4 S-box roundtrip:')
    print(f'  plaintext  = {test_pt.hex()}')
    print(f'  Hero4 ct   = {h4_ct.hex()}')
    print(f'  decrypted  = {h4_pt.hex()}')
    print(f'  Roundtrip OK: {h4_pt == test_pt}')
    print(f'  Differs from standard DES: {h4_ct != ref_ct}')
