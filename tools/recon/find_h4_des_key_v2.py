"""Hero4 DES key brute-force v2 — known-ciphertext leverage + 확장 후보 소스.

v1 ([find_h4_des_key.py](find_h4_des_key.py)) 한계:
    * binary `.data` 영역 (start=0x77000) 만 검색 — `.text` literal pool / GOT 패딩 미커버
    * 후보 score 가 Hero3 SCN header signature 의존 (헤더 plaintext 가 다르면 miss)
    * 한 SCN 파일만 검증

v2 결정적 단서 (2026-05-14 추가 정찰):
    1. **`3b 7a f9 a4 27 90 7d ac`** = SCN 마지막 8-byte ciphertext 가 **350 중 38회 반복**
       → ECB 모드 100% 확정 + 공통 평문 종단 마커 존재 (zero-padding / EOS opcode / sentinel)
    2. **`46 55 b8 f3 9c 0f e0 b2`** = 첫 8-byte ciphertext 가 8회 반복 → 다중 파일 동일 헤더
    3. **`e0 00 e2 02 da 1a 0e 31`** 등 다른 high-frequency cipher block 존재

전략:
    * 모든 후보 키로 가장 흔한 last-block (`3b7af9a427907dac`) 만 decrypt → fast filter
    * plaintext 가 매우 낮은 entropy (≤ 2 distinct bytes) / Hero3 sentinel 패턴 등이면 후보 통과
    * 통과 후보들만 first-block + 추가 검증

후보 소스 (확장):
    a. **전체 binary 슬라이딩 윈도우** (start=0, 모든 8-byte) — `.text` 포함
    b. **`__adf__` / `__class__` descriptor strings** (SKT 앱 메타데이터 — PID/AID/Ver/SLvl 등)
    c. **filename / AID 기반 파생 키** (010100D4 hex, 4-byte 변환, padding 패턴)
    d. **Hero5 KEY4ENCRYPT 변종** (혹시나)
    e. **일반 DES weak keys + 흔한 패턴** (`00`*8, `12345678`, `password`, …)
"""
from __future__ import annotations
import argparse, collections, itertools, pathlib, re, sys
from Crypto.Cipher import DES


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BIN = ROOT / 'work' / 'h4' / 'extracted' / 'client.bin387872'
SCN_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC'
SRC_DIR = ROOT / 'Hero4'

# 가장 흔한 last 8-byte ciphertext (38/350 = 11% 반복) — known plaintext crib
KNOWN_CIPHER_LAST = bytes.fromhex('3b7af9a427907dac')
# 가장 흔한 first 8-byte ciphertext (8/350)
KNOWN_CIPHER_FIRST = bytes.fromhex('4655b8f39c0fe0b2')

# 알려진 plain-text 종단 후보 (sentinel 가설)
SENTINEL_CANDIDATES = [
    b'\x00' * 8,
    b'\xff' * 8,
    b'\x08' * 8,        # PKCS#7 padding (block-full)
    b'\xff' * 4 + b'\x00' * 4,
    b'\x00' * 4 + b'\xff' * 4,
    b'\x01' * 8,
    b'\x80' + b'\x00' * 7,  # ISO/IEC 7816-4 padding
    b'\xff\xff\xff\xff\xff\xff\xff\x00',
]


def score_decrypted_last(plain: bytes) -> tuple[int, str]:
    """마지막 블록 plaintext score. (score, reason)"""
    distinct = len(set(plain))
    # sentinel exact match — strongest
    for sent in SENTINEL_CANDIDATES:
        if plain == sent:
            return 1000, f'sentinel exact {sent.hex()}'
    # 1~2 distinct bytes — high-confidence padding
    if distinct == 1:
        return 500, f'single byte 0x{plain[0]:02x}'
    if distinct == 2:
        return 200, f'2-byte alphabet {set(plain)}'
    # 3 distinct — possibly script EOS opcode sequence
    if distinct == 3:
        return 80, f'3-byte alphabet {sorted(set(plain))}'
    if distinct == 4:
        return 40, f'4-byte alphabet'
    # 0xff or 0x00 dominant
    cnt = collections.Counter(plain)
    most_common, most_count = cnt.most_common(1)[0]
    if most_common in (0x00, 0xff) and most_count >= 5:
        return 60 + most_count * 2, f'dominant {hex(most_common)} ×{most_count}'
    if most_common in (0x00, 0xff) and most_count >= 4:
        return 30, f'mod-{hex(most_common)} ×{most_count}'
    if most_count >= 4:
        return 10 + most_count, f'dominant {hex(most_common)} ×{most_count}'
    return 0, ''


def score_decrypted_first(plain: bytes) -> tuple[int, str]:
    """첫 블록 plaintext score — Hero3-like SCN header 가설."""
    score = 0
    reasons = []
    # Hero3 SCN signature
    if plain[:6] == b'\x00\x00\x00\xff\xff\xff':
        score += 200; reasons.append('hero3-sig')
    elif plain[:4] == b'\x00\x00\x00\xff':
        score += 80; reasons.append('00-ff-prefix')
    elif plain[:3] == b'\x00\x00\x00':
        score += 40; reasons.append('null-prefix')
    # `0xff` separator frequency
    ff = plain.count(0xff)
    score += ff * 4
    # opcode band (0x00..0x4f) — SCN bytecode typical
    opcode = sum(1 for b in plain if b < 0x50)
    score += opcode * 2
    # 너무 random 하면 reject
    if len(set(plain)) >= 7 and ff == 0:
        score = max(0, score - 30)
    return score, ' '.join(reasons)


# ---------- 후보 키 생성 ----------

def candidates_from_binary(binary: bytes, source: str, start: int = 0) -> set[bytes]:
    """binary 슬라이딩 윈도우."""
    out = set()
    end = len(binary) - 7
    for i in range(start, end):
        c = bytes(binary[i:i+8])
        if source == 'ascii':
            if all(0x20 <= b <= 0x7e for b in c):
                out.add(c)
        else:
            out.add(c)
    return out


def candidates_from_descriptors() -> set[bytes]:
    """__adf__, __class__ 의 ASCII 토큰 + 변환."""
    out: set[bytes] = set()
    for name in ('__adf__', '__class__'):
        p = SRC_DIR / name
        if not p.exists():
            continue
        data = p.read_bytes()
        # ASCII 토큰
        for m in re.finditer(rb'[\x20-\x7e]{4,}', data):
            tok = m.group(0)
            # 정확히 8-byte
            if len(tok) == 8:
                out.add(bytes(tok))
            # 8-byte 슬라이딩
            for i in range(len(tok) - 7):
                out.add(bytes(tok[i:i+8]))
            # 짧은 token 은 zero/space/null pad
            if 4 <= len(tok) <= 7:
                out.add(tok + b'\x00' * (8 - len(tok)))
                out.add(tok + b' ' * (8 - len(tok)))
                out.add(b'\x00' * (8 - len(tok)) + tok)
        # 8-byte 슬라이딩 (전체 raw bytes)
        for i in range(len(data) - 7):
            out.add(bytes(data[i:i+8]))
    return out


def candidates_aid_derived(aid_hex: str = '010100D4') -> set[bytes]:
    """AID 010100D4 의 다양한 표현."""
    out: set[bytes] = set()
    # 8-byte ASCII
    out.add(aid_hex.encode('ascii'))
    out.add(aid_hex.lower().encode('ascii'))
    # 4-byte hex + 4-byte pad
    raw = bytes.fromhex(aid_hex)
    out.add(raw + b'\x00' * 4)
    out.add(b'\x00' * 4 + raw)
    out.add(raw + raw)
    out.add(raw[::-1] + raw)
    out.add(raw + raw[::-1])
    # 'D4' 만 반복 등의 패턴은 별로 의미없음, skip
    # PID 8 자
    for pid in ('PD008712', 'PD008711', 'PD008713'):
        out.add(pid.encode('ascii'))
    # 흔한 한빛 / Hero4 추정
    for s in ('Hanbit01', 'HANBIT01', 'hanbit01', 'Hero4Key', 'HeroSaga', 'HEROSAGA',
              'hanbit_4', 'HanBitH4', 'h4nb1tk1', 'environment', 'Mu_Phi_Fa', 'Gorias_8',
              '01.00.03', '0101001Y', '01010101', '88888888'):
        if len(s) == 8:
            out.add(s.encode('ascii'))
    return out


def candidates_common_weak() -> set[bytes]:
    """잘 알려진 약한/기본 DES 키 + 흔한 패턴."""
    out: set[bytes] = set()
    out.add(b'\x00' * 8)
    out.add(b'\xff' * 8)
    out.add(b'\x01' * 8)
    out.add(bytes(range(8)))
    out.add(bytes(range(8, 0, -1)))
    out.add(bytes.fromhex('0123456789ABCDEF'))
    out.add(bytes.fromhex('FEDCBA9876543210'))
    out.add(b'12345678')
    out.add(b'password')
    out.add(b'88888888')
    out.add(b'00000000')
    out.add(b'aaaaaaaa')
    # Hero5 KEY4ENCRYPT 의 첫 8 / 마지막 8
    h5 = bytes.fromhex('ff0000000a33223c3111213902091321')  # 16 bytes
    out.add(h5[:8])
    out.add(h5[8:])
    return out


# ---------- DES weak-key 회피 (PyCryptodome 가 reject) ----------

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


def is_weak(k: bytes) -> bool:
    return k in DES_WEAK_KEYS


# ---------- 검증 ----------

def verify_key(key: bytes, scn_files: list[pathlib.Path], samples: int = 5) -> dict:
    """발견된 키 후보를 여러 SCN 파일로 검증.

    반환: {'first_block_pattern': str, 'last_block_pattern': str, 'samples': [...]}
    """
    cipher = DES.new(key, DES.MODE_ECB)
    sample = []
    for f in scn_files[:samples]:
        d = f.read_bytes()
        aligned = d[:len(d) - len(d) % 8]
        if not aligned:
            continue
        plain = cipher.decrypt(aligned)
        sample.append({
            'name': f.name,
            'size': len(d),
            'first16': plain[:16].hex(),
            'last16': plain[-16:].hex() if len(plain) >= 16 else plain.hex(),
        })
    return {'samples': sample}


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', choices=['ascii', 'all', 'descriptor', 'derived', 'weak', 'merged'],
                    default='merged', help='후보 소스 (merged = 모두)')
    ap.add_argument('--start', type=lambda s: int(s, 0), default=0,
                    help='binary 검색 시작 offset (default 0 = 전체)')
    ap.add_argument('--top', type=int, default=30)
    ap.add_argument('--mode', choices=['ecb'], default='ecb')
    ap.add_argument('--min-score', type=int, default=30)
    args = ap.parse_args()

    if not BIN.exists():
        print(f'MISSING: {BIN}', file=sys.stderr)
        return 1
    binary = BIN.read_bytes()
    print(f'Binary: {BIN.name} ({len(binary):,} bytes)', file=sys.stderr)

    # 후보 빌드
    cands: set[bytes] = set()
    if args.source in ('all', 'merged'):
        c = candidates_from_binary(binary, 'all', args.start)
        print(f'  binary sliding-all (start=0x{args.start:x}): {len(c):,}', file=sys.stderr)
        cands |= c
    if args.source in ('ascii', 'merged'):
        c = candidates_from_binary(binary, 'ascii', args.start)
        print(f'  binary sliding-ascii: {len(c):,}', file=sys.stderr)
        cands |= c
    if args.source in ('descriptor', 'merged'):
        c = candidates_from_descriptors()
        print(f'  descriptors (__adf__/__class__): {len(c):,}', file=sys.stderr)
        cands |= c
    if args.source in ('derived', 'merged'):
        c = candidates_aid_derived()
        print(f'  AID-derived: {len(c):,}', file=sys.stderr)
        cands |= c
    if args.source in ('weak', 'merged'):
        c = candidates_common_weak()
        print(f'  weak/common: {len(c):,}', file=sys.stderr)
        cands |= c

    print(f'Total unique candidates: {len(cands):,}', file=sys.stderr)
    # weak keys 제거
    cands = {k for k in cands if not is_weak(k)}
    print(f'After weak-key filter: {len(cands):,}', file=sys.stderr)

    # Phase 1: 가장 자주 반복되는 last-block (`3b7af9a427907dac`) 만 decrypt
    print(f'\nPhase 1: decrypt KNOWN_CIPHER_LAST ({KNOWN_CIPHER_LAST.hex()}) for all candidates...', file=sys.stderr)
    survivors: list[tuple[int, bytes, bytes, str]] = []
    for k in cands:
        try:
            cipher = DES.new(k, DES.MODE_ECB)
            plain = cipher.decrypt(KNOWN_CIPHER_LAST)
        except ValueError:
            continue
        s, reason = score_decrypted_last(plain)
        if s >= args.min_score:
            survivors.append((s, k, plain, reason))
    survivors.sort(key=lambda x: -x[0])
    print(f'Phase 1 survivors: {len(survivors)} (score >= {args.min_score})', file=sys.stderr)

    if not survivors:
        print('  → no key passed last-block sentinel check.', file=sys.stderr)
        return 0

    print('\nTop survivors (Phase 1 last-block):', file=sys.stderr)
    for i, (s, k, p, r) in enumerate(survivors[:args.top]):
        ascii_repr = repr(k.decode('ascii', errors='replace')) if all(0x20 <= b <= 0x7e for b in k) else '<binary>'
        print(f'  [{i+1:3}] score={s:4}  key={k.hex()} ({ascii_repr})  →  last8={p.hex()}  [{r}]')

    # Phase 2: top 20 survivor 들에 대해 first-block (`4655b8f39c0fe0b2`) 도 decrypt
    print(f'\nPhase 2: cross-validate with KNOWN_CIPHER_FIRST ({KNOWN_CIPHER_FIRST.hex()})...', file=sys.stderr)
    top_n = min(args.top, len(survivors))
    p2: list[tuple[int, bytes, bytes, bytes, str]] = []
    for s, k, plast, _ in survivors[:top_n]:
        cipher = DES.new(k, DES.MODE_ECB)
        pfirst = cipher.decrypt(KNOWN_CIPHER_FIRST)
        s2, r2 = score_decrypted_first(pfirst)
        p2.append((s + s2, k, plast, pfirst, r2))
    p2.sort(key=lambda x: -x[0])
    print('\nTop cross-validated:', file=sys.stderr)
    for i, (total, k, plast, pfirst, r) in enumerate(p2[:20]):
        ascii_repr = repr(k.decode('ascii', errors='replace')) if all(0x20 <= b <= 0x7e for b in k) else '<binary>'
        print(f'  [{i+1:2}] total={total:4}  key={k.hex()} ({ascii_repr})')
        print(f'        last8 = {plast.hex()}')
        print(f'        first8 = {pfirst.hex()}  [{r}]')

    # Phase 3: 1등 키로 전체 SCN 표본 검증
    if p2:
        winner_key = p2[0][1]
        print(f'\n=== WINNER candidate: {winner_key.hex()} ({winner_key.decode("ascii", errors="replace")!r}) ===', file=sys.stderr)
        scns = sorted(SCN_DIR.glob('*_scn'))
        v = verify_key(winner_key, scns, samples=5)
        for s in v['samples']:
            print(f'  {s["name"]:20} size={s["size"]:5} first16={s["first16"]} last16={s["last16"]}', file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
