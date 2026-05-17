"""Hero4 DES key brute-force v3 — known-plaintext signature 기반.

v1/v2 한계: SCN plaintext 형식이 Hero3 와 다르다는 사실을 모른 채
Hero3 sentinel/signature 로만 score 평가 → false negative.

v3 핵심 단서 (2026-05-18 발견):
    SCN 350 중 2개 (e0184_scn=30B, e0185_scn=6313B+1) 는 **8-byte misaligned
    + plaintext** 임을 확인. 첫 8 byte signature:
        e0184: 01 00 01 53 00 01 a1 ff
        e0185: 01 02 01 53 00 01 c8 ff
    공통 패턴 = **01 ?? 01 53 00 01 ?? ??** (5 byte fixed = 40 known bits)

    'S'(0x53) 는 'Scene'/'Scn'/'Stage' magic 일 가능성이 높고,
    바이트 1/6/7 만 SCN id/size 등에 따라 가변. byte 7 = 0xff = SCN 첫 header
    block 의 흔한 separator.

검증 전략 — first cipher block 다중 가설 매칭:
    348개 encrypted SCN 의 첫 cipher block 빈도 표:
        4655b8f39c0fe0b2 × 8
        38d18f6ac1c49c07 × 7
        0206740aa7b9edea × 6
        b5ef057a32611fa4 × 5
        ...
    각 후보 키로 모든 cipher block 후보를 decrypt 해보고,
    decrypt 결과가 `01 ?? 01 53 00 01 ?? ??` 패턴을 만족하면 강한 매치.

후보 소스 (v2 + v3 확장):
    a. 전체 binary 슬라이딩 (v2 와 동일)
    b. **`_DAT_DES` 824 byte 자체 슬라이딩** (key 가 DES table 의 padding 영역에 숨겨졌을 가능성)
    c. **`e0184_scn` / `e0185_scn` 자체 슬라이딩** (plaintext SCN 안 키 embed 가능성)
    d. JAR 의 META-INF/MANIFEST.MF / l/_LOGO / tdf/* 의 raw bytes
    e. AID 파생 (v2 동일)
"""
from __future__ import annotations
import argparse, collections, glob, os, pathlib, sys
from Crypto.Cipher import DES


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BIN = ROOT / 'work' / 'h4' / 'extracted' / 'client.bin387872'
SCN_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC'
DAT_DES = ROOT / 'work' / 'h4' / 'extracted' / 'DAT' / '_DAT_DES'
EXTRACTED_ROOT = ROOT / 'work' / 'h4' / 'extracted'
PLAINTEXT_SCN = [
    ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC' / 'e0184_scn',
    ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC' / 'e0185_scn',
]

# 새 known-plaintext signature (5 byte fixed)
def match_plaintext_signature(plain: bytes) -> tuple[bool, int]:
    """첫 8 byte plaintext 가 e0184/e0185 의 공통 패턴인지.

    반환 (matched, score)
    01 ?? 01 53 00 01 ?? ??
    """
    if len(plain) < 8:
        return False, 0
    score = 0
    # byte 0 == 0x01
    if plain[0] == 0x01:
        score += 100
    # byte 2 == 0x01
    if plain[2] == 0x01:
        score += 100
    # byte 3 == 0x53 ('S')
    if plain[3] == 0x53:
        score += 200
    # byte 4 == 0x00
    if plain[4] == 0x00:
        score += 100
    # byte 5 == 0x01
    if plain[5] == 0x01:
        score += 100
    # 5 byte all match = exact signature
    matched = (plain[0] == 0x01 and plain[2] == 0x01 and plain[3] == 0x53
               and plain[4] == 0x00 and plain[5] == 0x01)
    return matched, score


# 가장 흔한 first cipher block 들 (8회+ 반복)
TOP_FIRST_CIPHERS = [
    bytes.fromhex('4655b8f39c0fe0b2'),  # × 8
    bytes.fromhex('38d18f6ac1c49c07'),  # × 7
    bytes.fromhex('0206740aa7b9edea'),  # × 6
    bytes.fromhex('b5ef057a32611fa4'),  # × 5
    bytes.fromhex('365556a07ee5eea5'),  # × 4
    bytes.fromhex('d9f50e2e919ff21f'),  # × 4
    bytes.fromhex('ded3183dbeaf6fed'),  # × 4
]


# DES weak keys (PyCryptodome rejects)
DES_WEAK_KEYS = {
    bytes.fromhex('0101010101010101'), bytes.fromhex('fefefefefefefefe'),
    bytes.fromhex('e0e0e0e0f1f1f1f1'), bytes.fromhex('1f1f1f1f0e0e0e0e'),
    bytes.fromhex('011f011f010e010e'), bytes.fromhex('1f011f010e010e01'),
    bytes.fromhex('01e001e001f101f1'), bytes.fromhex('e001e001f101f101'),
    bytes.fromhex('01fe01fe01fe01fe'), bytes.fromhex('fe01fe01fe01fe01'),
    bytes.fromhex('1fe01fe00ef10ef1'), bytes.fromhex('e01fe01ff10ef10e'),
    bytes.fromhex('1ffe1ffe0efe0efe'), bytes.fromhex('fe1ffe1ffe0efe0e'),
    bytes.fromhex('e0fee0fef1fef1fe'), bytes.fromhex('fee0fee0fef1fef1'),
}


def candidates_from_bytes(data: bytes, label: str) -> set[bytes]:
    out = set()
    for i in range(len(data) - 7):
        out.add(bytes(data[i:i+8]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', choices=['binary', 'dat_des', 'plaintext_scn', 'all'],
                    default='all')
    ap.add_argument('--top', type=int, default=30)
    args = ap.parse_args()

    # 후보 빌드
    cands: set[bytes] = set()
    if args.source in ('binary', 'all'):
        if BIN.exists():
            c = candidates_from_bytes(BIN.read_bytes(), 'binary')
            print(f'  binary sliding ({BIN.name}): {len(c):,}', file=sys.stderr)
            cands |= c
    if args.source in ('dat_des', 'all'):
        if DAT_DES.exists():
            c = candidates_from_bytes(DAT_DES.read_bytes(), 'dat_des')
            print(f'  _DAT_DES sliding: {len(c):,}', file=sys.stderr)
            cands |= c
    if args.source in ('plaintext_scn', 'all'):
        for p in PLAINTEXT_SCN:
            if p.exists():
                c = candidates_from_bytes(p.read_bytes(), p.name)
                print(f'  {p.name} sliding: {len(c):,}', file=sys.stderr)
                cands |= c

    # weak filter
    cands = {k for k in cands if k not in DES_WEAK_KEYS}
    print(f'Total unique candidates after weak filter: {len(cands):,}', file=sys.stderr)
    print(f'Target ciphertexts (top first blocks): {len(TOP_FIRST_CIPHERS)}', file=sys.stderr)
    print(f'\nPhase 1: decrypt each candidate against top first-block ciphertexts...', file=sys.stderr)

    survivors = []
    for k in cands:
        try:
            cipher = DES.new(k, DES.MODE_ECB)
        except ValueError:
            continue
        best_score = 0
        best_match = None
        for ct in TOP_FIRST_CIPHERS:
            plain = cipher.decrypt(ct)
            matched, score = match_plaintext_signature(plain)
            if score > best_score:
                best_score = score
                best_match = (ct, plain, matched)
        if best_score >= 200:  # at least 2 bytes match
            survivors.append((best_score, k, best_match))

    survivors.sort(key=lambda x: -x[0])
    print(f'Phase 1 survivors (score >= 200): {len(survivors)}', file=sys.stderr)

    if not survivors:
        print('\n  → no key passed signature check. Hero4 DES key is likely NOT in:', file=sys.stderr)
        print('     - client.bin387872', file=sys.stderr)
        print('     - DAT/_DAT_DES', file=sys.stderr)
        print('     - plaintext SCN (e0184/e0185)', file=sys.stderr)
        print('\n  Suggests key is either (a) runtime-derived from non-string source,', file=sys.stderr)
        print('  (b) located in another JAR resource, or (c) literal bytes scrambled.', file=sys.stderr)
        return 0

    print('\nTop candidates:', file=sys.stderr)
    for i, (score, k, (ct, plain, matched)) in enumerate(survivors[:args.top]):
        ascii_repr = ''
        if all(0x20 <= b <= 0x7e for b in k):
            ascii_repr = f' ({k.decode("ascii")!r})'
        flag = ' [PERFECT MATCH]' if matched else ''
        print(f'  [{i+1:3}] score={score:4}{flag}  key={k.hex()}{ascii_repr}')
        print(f'        ct={ct.hex()}  →  plain={plain.hex()}')

    # Phase 2: top 5 survivor 들을 plaintext SCN 도 decrypt 안 한 채 다른 first cipher block 들도 확인
    print('\nPhase 2: top-5 cross-validation against all 7 top cipher blocks...', file=sys.stderr)
    for score, k, _ in survivors[:5]:
        try:
            cipher = DES.new(k, DES.MODE_ECB)
        except ValueError:
            continue
        ascii_repr = ''
        if all(0x20 <= b <= 0x7e for b in k):
            ascii_repr = f' ({k.decode("ascii")!r})'
        print(f'\n  Key {k.hex()}{ascii_repr}:')
        for ct in TOP_FIRST_CIPHERS:
            plain = cipher.decrypt(ct)
            matched, s = match_plaintext_signature(plain)
            mark = '*MATCH*' if matched else ('partial' if s >= 200 else '       ')
            print(f'    ct={ct.hex()} → plain={plain.hex()}  {mark}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
