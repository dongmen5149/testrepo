"""Hero4 DES key brute-force v4 — custom DES (S1[58]=2) 사용.

v3 까지 모두 표준 DES (PyCryptodome) 로 brute-force. _DAT_DES 의 S1 1-byte
차이 발견 (2026-05-18) 후, 실제 Hero4 가 modified S-box 를 사용한다면
표준 DES 로는 절대 매치되지 않음. 이 가설을 검증.

후보 키: 전체 binary + DAT_DES + plaintext SCN sliding window.
대상 cipher: 348 encrypted SCN 중 가장 흔한 first cipher block 들.
검증 signature: 01 ?? 01 53 00 01 ?? ?? (e0184/e0185 plaintext 에서 추론).
"""
from __future__ import annotations
import pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from converter.custom_des_h4 import decrypt as h4_decrypt, _generate_subkeys, S_HERO4


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BIN = ROOT / 'work' / 'h4' / 'extracted' / 'client.bin387872'
DAT_DES = ROOT / 'work' / 'h4' / 'extracted' / 'DAT' / '_DAT_DES'
PLAINTEXT_SCN = [
    ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC' / 'e0184_scn',
    ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC' / 'e0185_scn',
]

# Top first cipher blocks from 348 encrypted SCN
TOP_CIPHERS = [
    bytes.fromhex('4655b8f39c0fe0b2'),  # × 8
    bytes.fromhex('38d18f6ac1c49c07'),  # × 7
    bytes.fromhex('0206740aa7b9edea'),  # × 6
    bytes.fromhex('b5ef057a32611fa4'),  # × 5
    bytes.fromhex('365556a07ee5eea5'),  # × 4
]

# DES weak keys (skip)
DES_WEAK = {bytes.fromhex(h) for h in (
    '0101010101010101', 'fefefefefefefefe', 'e0e0e0e0f1f1f1f1',
    '1f1f1f1f0e0e0e0e', '011f011f010e010e', '1f011f010e010e01',
    '01e001e001f101f1', 'e001e001f101f101', '01fe01fe01fe01fe',
    'fe01fe01fe01fe01', '1fe01fe00ef10ef1', 'e01fe01ff10ef10e',
    '1ffe1ffe0efe0efe', 'fe1ffe1ffe0efe0e', 'e0fee0fef1fef1fe',
    'fee0fee0fef1fef1',
)}


def match_sig(plain: bytes) -> int:
    """01 ?? 01 53 00 01 ?? ?? score (max 600)."""
    if len(plain) < 8:
        return 0
    score = 0
    if plain[0] == 0x01: score += 100
    if plain[2] == 0x01: score += 100
    if plain[3] == 0x53: score += 200
    if plain[4] == 0x00: score += 100
    if plain[5] == 0x01: score += 100
    return score


def collect_candidates() -> set[bytes]:
    cands = set()
    for src in [BIN, DAT_DES, *PLAINTEXT_SCN]:
        if not src.exists():
            continue
        data = src.read_bytes()
        for i in range(len(data) - 7):
            c = bytes(data[i:i+8])
            if c not in DES_WEAK:
                cands.add(c)
        print(f'  {src.name}: {len(data)}B', file=sys.stderr)
    return cands


def main():
    print('Collecting candidate keys (sliding window)...', file=sys.stderr)
    cands = collect_candidates()
    print(f'Total unique candidates: {len(cands):,}', file=sys.stderr)
    print(f'Target ciphertexts: {len(TOP_CIPHERS)} (custom DES decrypt)', file=sys.stderr)
    print(f'Estimated time: {len(cands) * len(TOP_CIPHERS) / 200:.0f}s @ 200 blocks/s', file=sys.stderr)
    print()

    survivors = []
    start = time.time()
    last_print = start
    done = 0
    for k in cands:
        done += 1
        if done % 1000 == 0:
            now = time.time()
            if now - last_print >= 5:
                rate = done / (now - start)
                eta = (len(cands) - done) / rate
                print(f'  [{done:,}/{len(cands):,}] {rate:.0f} keys/s, ETA {eta:.0f}s', file=sys.stderr)
                last_print = now
        best_score = 0
        best = None
        for ct in TOP_CIPHERS:
            plain = h4_decrypt(k, ct)
            s = match_sig(plain)
            if s > best_score:
                best_score = s
                best = (ct, plain)
        if best_score >= 500:  # 3+ bytes match in signature
            survivors.append((best_score, k, best))

    survivors.sort(key=lambda x: -x[0])
    elapsed = time.time() - start
    print(f'\nDone in {elapsed:.0f}s. Survivors (score>=500): {len(survivors)}', file=sys.stderr)

    if not survivors:
        print('\n  → No key passed signature check with custom DES either.', file=sys.stderr)
        print('  → Key is genuinely not present as 8-byte literal in scanned sources.', file=sys.stderr)
        return 0

    print('\nTop candidates:')
    for i, (s, k, (ct, plain)) in enumerate(survivors[:20]):
        ascii_repr = ''
        if all(0x20 <= b <= 0x7e for b in k):
            ascii_repr = f' ({k.decode("ascii")!r})'
        flag = ' [PERFECT]' if s >= 600 else ''
        print(f'  [{i+1}] score={s}{flag}  key={k.hex()}{ascii_repr}')
        print(f'      ct={ct.hex()} → plain={plain.hex()}')

    # Top 3 cross-validate against all 5 cipher blocks
    print('\nTop-3 cross-validation:')
    for s, k, _ in survivors[:3]:
        ascii_repr = ''
        if all(0x20 <= b <= 0x7e for b in k):
            ascii_repr = f' ({k.decode("ascii")!r})'
        print(f'\n  Key {k.hex()}{ascii_repr}:')
        for ct in TOP_CIPHERS:
            plain = h4_decrypt(k, ct)
            sc = match_sig(plain)
            mark = '*MATCH*' if sc >= 600 else ('partial' if sc >= 200 else '       ')
            print(f'    ct={ct.hex()} → plain={plain.hex()}  {mark}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
