"""Hero4 DES key brute-force v5 — Hero5/Hero3 cross-game key + MX_desDecrypt variant.

Hypothesis 핵심 (Round 68, 2026-05-18):
    Hero3/Hero5 가 동일 키 `0EP@KO91` + libHeroesLore5.so 의 MX_desDecrypt
    (S1[58]=2 + startDes(mode=0) reversed subkey + half swap) 를 사용하는 것이
    R57+R58 (Hero3) 와 H5 docs/h5/DES_VARIANT.md 에서 확정됨.

    Hero4 의 _DAT_DES 도 S1[58]=2 동일 수정 → 한빛소프트 공용 DES variant.
    Hero4 binary 의 `J@IWO8N7L0E7E` (0x86edc) 는 Hero3 의 `0EP@KO91` (0xac594)
    와 동일 위치 패턴 → Hero4 키 후보 = J@IWO8N7L0E7E 의 8-byte slice.

목적:
    v4 까지 사용한 표준 DES + S1[58]=2 변형은 **swap/reverse 트릭 누락**.
    v5 는 tools/h5_des.py 의 mx_des_decrypt 사용 + Hero3/Hero5 키 cross-game test.

후보 키 set:
    1. Hero3/Hero5 공유 키: `0EP@KO91`
    2. Hero4 binary 의 J@IWO8N7L0E7E sliding 8-byte slices (6 slices)
    3. J@IWO8N7L0E7E 변형 (letter-only, digit-only, reversed)
    4. Hero3 client.bin64000 sliding window (cross-game 가설 보강)

검증:
    9 known-ciphertext block × 4 signature check:
        - SCN signature: plaintext[0]==0x01, [2]==0x01, [3]==0x53, [4]==0x00, [5]==0x01
        - Low-entropy: bytes 모두 같음 (sentinel 패턴)
        - EUC-KR Korean range: 0xa1-0xfe bytes 다수
        - ASCII range: 0x20-0x7e bytes 다수
"""
from __future__ import annotations
import pathlib, sys, time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from h5_des import mx_des_decrypt
from converter.custom_des_h4 import decrypt as h4_decrypt  # baseline 비교용

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# 9 known-ciphertext blocks (PROGRESS.md §🔑 known-ciphertext leverage)
KNOWN_CIPHERS = {
    'scn_last_x38':   bytes.fromhex('3b7af9a427907dac'),  # SCN last × 38 + HDAT-A × 92
    'scn_last_x13':   bytes.fromhex('1b7559e5bcf49488'),
    'scn_last_x12':   bytes.fromhex('ef9c94a1d8247276'),
    'scn_last_x11':   bytes.fromhex('c0f2daf72c2210e1'),
    'scn_first_x8':   bytes.fromhex('4655b8f39c0fe0b2'),  # signature crib
    'scn_first_x7':   bytes.fromhex('38d18f6ac1c49c07'),
    'scn_second_x17': bytes.fromhex('f7740f758b9a6ae4'),
    'bsdat_first':    bytes.fromhex('d6c1b1be38099f0e'),
    'esdat_first':    bytes.fromhex('8d6507ea29d02ca9'),
}


def score_plaintext(p: bytes, label: str) -> tuple[int, str]:
    """다양한 점수 체계 — signature, sentinel, korean."""
    if len(p) < 8:
        return 0, ''
    score = 0
    reasons = []

    # SCN signature: 01 ?? 01 53 00 01 ?? ?? (only first-block ciphers)
    if 'first' in label:
        sig = (p[0] == 0x01) + (p[2] == 0x01) + (p[3] == 0x53) + (p[4] == 0x00) + (p[5] == 0x01)
        if sig >= 3:
            score += sig * 100
            reasons.append(f'SCN_sig={sig}/5')

    # Low-entropy sentinel: bytes 다수 같음 (last block 후보)
    if 'last' in label:
        max_run = 0
        cur_run = 1
        for i in range(1, 8):
            if p[i] == p[i-1]:
                cur_run += 1
                max_run = max(max_run, cur_run)
            else:
                cur_run = 1
        if max_run >= 4:
            score += max_run * 50
            reasons.append(f'sentinel_run={max_run}')

    # EUC-KR Korean range (0xa1-0xfe pair)
    korean = sum(1 for b in p if 0xa1 <= b <= 0xfe)
    if korean >= 4:
        score += korean * 25
        reasons.append(f'korean={korean}')

    # ASCII printable
    ascii_n = sum(1 for b in p if 0x20 <= b <= 0x7e)
    if ascii_n >= 6:
        score += ascii_n * 10
        reasons.append(f'ascii={ascii_n}')

    return score, ', '.join(reasons)


def test_key(key: bytes, label: str = '', verbose: bool = False) -> tuple[int, list[str]]:
    """단일 키에 대해 9 ciphertext × 2 cipher (mx_des / std-S1-mod) 테스트.

    Returns (total_score, hits_log).
    """
    if len(key) > 8:
        key = key[:8]
    elif len(key) < 8:
        key = key + b'\x00' * (8 - len(key))

    hits = []
    total = 0
    for name, ct in KNOWN_CIPHERS.items():
        # MX_desDecrypt (Hero5 variant: swap + reversed subkey + S1[58]=2)
        p_mx = mx_des_decrypt(ct, key)
        s_mx, reason_mx = score_plaintext(p_mx, name)
        if s_mx > 0:
            total += s_mx
            hits.append(f'  MX[{name}] = {p_mx.hex()}  score={s_mx} ({reason_mx})')

        # Standard-tables DES with S1 mod only (v4 baseline, for comparison)
        p_std = h4_decrypt(key, ct)
        s_std, reason_std = score_plaintext(p_std, name)
        if s_std > 0:
            total += s_std // 2  # baseline 만 보조용
            hits.append(f'  ST[{name}] = {p_std.hex()}  score={s_std} ({reason_std})')

    if verbose or total > 100:
        try:
            kstr = key.decode('ascii', errors='replace')
        except Exception:
            kstr = key.hex()
        print(f'\n=== KEY: {kstr!r} (hex={key.hex()}) {label} ===  total={total}')
        for h in hits[:20]:
            print(h)
    return total, hits


def gen_candidates():
    cands: list[tuple[bytes, str]] = []

    # Hero3/Hero5 confirmed key
    cands.append((b'0EP@KO91', 'Hero3/Hero5 confirmed key'))

    # J@IWO8N7L0E7E sliding window (13 → 6 slices of 8)
    jiwo = b'J@IWO8N7L0E7E'
    for i in range(len(jiwo) - 7):
        cands.append((jiwo[i:i+8], f'J@IWO sliding @{i}'))

    # Letter-only / digit-only / mixed transforms of J@IWO8N7L0E7E
    cands.append((b'JIWONLEE', 'letters only (already in v2 list)'))
    cands.append((b'@8 707  ', 'digits-and-symbols only'))
    cands.append((bytes(reversed(jiwo[:8])), 'reversed J@IWO8N7'))

    # 0EP@KO91 variants
    cands.append((bytes(reversed(b'0EP@KO91')), 'reversed 0EP@KO91'))
    cands.append((b'19OK@PE0', 'reversed string'))

    # Hero4 specific identifiers
    cands.append((b'010100D4', 'Hero4 AID'))
    cands.append((b'PD008712', 'Hero4 PID'))
    cands.append((b'4D001010', 'Hero4 AID reversed'))

    return cands


def main():
    print('=== Hero4 DES key v5 — MX_desDecrypt (Hero5 variant) ===\n')

    # Phase 1: Curated candidates with verbose
    print('--- Phase 1: Curated keys (cross-game + variants) ---')
    survivors = []
    for key, label in gen_candidates():
        score, hits = test_key(key, label, verbose=False)
        if score > 0:
            try:
                kstr = key.decode('ascii', errors='replace')
            except Exception:
                kstr = key.hex()
            print(f'\n[{score:>5}]  {kstr!r} ({label})')
            for h in hits[:8]:
                print(h)
            if score > 50:
                survivors.append((score, key, label, hits))

    # Phase 2: Hero3 binary sliding window (cross-game hypothesis)
    print('\n--- Phase 2: Hero3 binary sliding window (cross-game) ---')
    h3_bin = ROOT / 'work' / 'h3' / 'extracted' / 'client.bin64000'
    if h3_bin.exists():
        data = h3_bin.read_bytes()
        print(f'  Source: {h3_bin.name} ({len(data):,}B → {len(data)-7:,} candidates)')
        start = time.time()
        last_print = start
        threshold = 200
        n_high = 0
        for i in range(len(data) - 7):
            if i % 5000 == 0:
                now = time.time()
                if now - last_print > 5:
                    rate = i / (now - start) if now > start else 0
                    print(f'  [{i:,}/{len(data)-7:,}] {rate:.0f} k/s  high_score={n_high}')
                    last_print = now
            k = bytes(data[i:i+8])
            # 빠른 첫 검증: 가장 흔한 last block 만
            p = mx_des_decrypt(KNOWN_CIPHERS['scn_last_x38'], k)
            max_run = max((sum(1 for c in range(min(8-r, 8-r)) if p[c+r] == p[r])
                           for r in range(0, 7)), default=0)
            if max_run >= 4 or all(0x20 <= b <= 0x7e for b in p):
                score, hits = test_key(k, f'H3-bin@0x{i:x}')
                if score >= threshold:
                    n_high += 1
                    survivors.append((score, k, f'H3-bin@0x{i:x}', hits))
                    if n_high <= 10:
                        try:
                            kstr = k.decode('ascii', errors='replace')
                        except Exception:
                            kstr = k.hex()
                        print(f'  [HIT] {kstr!r} @0x{i:x}  score={score}')
        elapsed = time.time() - start
        print(f'  Phase 2 done in {elapsed:.1f}s — {n_high} high-score candidates')

    # Final report
    print('\n=== FINAL SURVIVORS (score-sorted) ===')
    survivors.sort(reverse=True)
    for score, key, label, hits in survivors[:15]:
        try:
            kstr = key.decode('ascii', errors='replace')
        except Exception:
            kstr = key.hex()
        print(f'\n[score={score}]  {kstr!r} ({label})  hex={key.hex()}')
        for h in hits[:6]:
            print(h)

    if not survivors:
        print('  (no survivors)')

    return 0


if __name__ == '__main__':
    sys.exit(main())
