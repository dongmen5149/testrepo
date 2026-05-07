"""Hero4 DES key brute-force candidate search.

Hero4 binary (`client.bin387872`) 의 .data 영역에서 8-byte 후보를 추출 (printable ASCII 등),
각 후보를 DES key 로 시도하여 SCN 파일을 ECB/CBC 로 decrypt. 결과가 Hero3 SCN bytecode
패턴 (낮은 byte 분포 + `0xff` separators + EUC-KR 한글 bigram) 을 띠면 score 가 높아짐.

전제:
    pip install pycryptodome

휴리스틱 (점수):
    * 0xff 출현 빈도 (Hero3 SCN 의 separator)        × 5
    * 0x00..0x4f opcode-band 비율                    × 1
    * EUC-KR 한글 bigram (0xa1..0xfe, 0xa1..0xfe)    × 3
    * high-entropy (랜덤한 byte 분포) reject

사용:
    python find_h4_des_key.py [--mode ecb|cbc] [--top N] [--candidates-source ascii|all]

자동으로 Hero4 binary 와 첫번째 SCN 파일을 사용. HERO_GAME 무시 (h4 hardcoded).
"""
from __future__ import annotations
import argparse, pathlib, sys
from Crypto.Cipher import DES


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
BIN = ROOT / 'work' / 'h4' / 'extracted' / 'client.bin387872'
SCN_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC'


def extract_candidates(binary: bytes, source: str = 'ascii', start: int = 0x77000) -> set[bytes]:
    """8-byte 후보 시퀀스를 binary 에서 추출.

    start: code/data 경계 (Hero4 ≈ 0x77000). 그 이후의 .data 영역만 검색.
    source:
        ascii    — 모든 byte 가 0x20..0x7e
        all      — sliding window 모든 위치 (느림, 후보 수 폭증)
    """
    candidates: set[bytes] = set()
    end = len(binary) - 7
    for i in range(start, end):
        chunk = binary[i:i+8]
        if source == 'ascii':
            if all(0x20 <= b <= 0x7e for b in chunk):
                candidates.add(bytes(chunk))
        else:
            candidates.add(bytes(chunk))
    return candidates


def score_decryption(plain: bytes) -> int:
    """복호화 결과가 Hero3-style SCN bytecode 같은지 점수.

    Hero3 SCN signature (관찰): `00 00 00 ff ff ff` 으로 시작 (header 4 + 0xff*2 padding).
    이게 매칭되면 매우 강한 signal → +200.
    """
    score = 0
    # 강력 시그니처 — Hero3 SCN header
    if plain[:6] == b'\x00\x00\x00\xff\xff\xff':
        score += 200
    elif plain[:4] == b'\x00\x00\x00\xff':
        score += 80
    # 인접 0xff 쌍 (separator)
    ff_pairs = sum(1 for i in range(len(plain) - 1) if plain[i] == 0xff and plain[i+1] == 0xff)
    score += ff_pairs * 10
    # 0xff 단독 빈도
    ff = plain.count(0xff)
    score += ff * 2
    # opcode band 비율
    opcode_band = sum(1 for b in plain if b < 0x50)
    score += opcode_band
    # EUC-KR 한글 bigram
    hangul = 0
    for i in range(len(plain) - 1):
        if 0xa1 <= plain[i] <= 0xfe and 0xa1 <= plain[i+1] <= 0xfe:
            hangul += 1
    score += hangul * 3
    # entropy 거부: distinct byte 가 너무 많으면 (random-looking) 0
    distinct = len(set(plain))
    if distinct >= len(plain) * 0.85 and ff < 2:
        return 0
    return score


def try_keys(binary_data: bytes, target: bytes, candidates: set[bytes], mode: str) -> list[tuple[int, bytes, bytes]]:
    """모든 후보로 target 첫 64 bytes 를 decrypt. 점수 순 정렬."""
    results = []
    for key in candidates:
        try:
            if mode == 'ecb':
                cipher = DES.new(key, DES.MODE_ECB)
            else:
                cipher = DES.new(key, DES.MODE_CBC, b'\x00' * 8)
            plain = cipher.decrypt(target)
        except ValueError:
            # weak key 등 — DES 모듈이 reject 하는 키들
            continue
        s = score_decryption(plain)
        if s >= 5:
            results.append((s, key, plain))
    results.sort(key=lambda x: -x[0])
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--mode', choices=['ecb', 'cbc'], default='ecb')
    ap.add_argument('--top', type=int, default=20, help='상위 N 결과 출력')
    ap.add_argument('--source', choices=['ascii', 'all'], default='ascii',
                    help='ascii: printable 8-bytes 만 (~수만개) / all: sliding window 전체 (~수십만개, 느림)')
    ap.add_argument('--start', type=lambda s: int(s, 0), default=0x77000,
                    help='binary 검색 시작 offset (.data 영역, default 0x77000)')
    ap.add_argument('--scn', help='검증용 SCN 파일 path (default: SC 디렉토리 첫 파일)')
    args = ap.parse_args()

    if not BIN.exists():
        print(f'MISSING: {BIN}', file=sys.stderr)
        return 1
    binary = BIN.read_bytes()
    print(f'Binary: {BIN.name} ({len(binary)} bytes, 0x{len(binary):x})', file=sys.stderr)

    if args.scn:
        scn_path = pathlib.Path(args.scn)
    else:
        scns = sorted(SCN_DIR.glob('*_scn'))
        if not scns:
            print(f'No SCN under {SCN_DIR}', file=sys.stderr)
            return 1
        scn_path = scns[0]
    scn_data = scn_path.read_bytes()
    target = scn_data[:64 if len(scn_data) >= 64 else len(scn_data) - len(scn_data) % 8]
    if len(target) % 8 != 0:
        target = target[:len(target) - len(target) % 8]
    print(f'SCN: {scn_path.name} ({len(scn_data)} bytes) — testing first {len(target)} bytes', file=sys.stderr)
    print(f'  cipher hex: {target.hex()}', file=sys.stderr)

    print(f'Extracting candidates ({args.source}, start=0x{args.start:x})...', file=sys.stderr)
    candidates = extract_candidates(binary, args.source, args.start)
    print(f'Got {len(candidates):,} candidates', file=sys.stderr)

    print(f'Trying DES-{args.mode.upper()}...', file=sys.stderr)
    results = try_keys(binary, target, candidates, args.mode)
    print(f'\nTop {min(args.top, len(results))} candidates (score, key, decrypted hex):', file=sys.stderr)

    for i, (s, k, p) in enumerate(results[:args.top]):
        ascii_repr = k.decode('ascii', errors='replace') if all(0x20 <= b <= 0x7e for b in k) else '<binary>'
        print(f'  [{i+1:2}] score={s:3}  key={k.hex()} ({ascii_repr!r})')
        print(f'        decrypted[0:32]: {p[:32].hex()}')

    if not results:
        print('  (no candidates passed score threshold)', file=sys.stderr)
        print('\nNext: try --source all (slower, full byte range), or --mode cbc, or expand --start.', file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
