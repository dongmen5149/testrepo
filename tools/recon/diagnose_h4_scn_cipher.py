"""Hero4 SCN 의 암호화 모드/특성을 진단.

자동 brute force 가 실패했을 때, Ghidra 작업 전 다음 단서를 자동 수집:
    1. SCN size 분포 — 8 의 배수? padding 패턴?
    2. ECB 가설 검증 — 같은 8-byte cipher block 반복 빈도
    3. byte 분포 — 랜덤 (DES/AES) vs 편향 (XOR / 약한 obfuscation)
    4. 두 SCN 의 첫 N byte 패턴 비교 — header 가 plain 인지 / 같은 IV 쓰는지

CBC 일 경우: IV 가 zero / 파일별 / 첫 cipher block 이 IV 자체
"""
from __future__ import annotations
import collections, math, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCN_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC'


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = collections.Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def main():
    files = sorted(SCN_DIR.glob('*_scn'))
    if not files:
        print(f'No SCN under {SCN_DIR}', file=sys.stderr)
        return 1

    print(f'== Hero4 SCN diagnostic ({len(files)} files) ==\n')

    # 1. size 분포
    sizes = [f.stat().st_size for f in files]
    aligned = sum(1 for s in sizes if s % 8 == 0)
    print(f'1. SIZE: total={len(sizes)} aligned-8={aligned} ({aligned*100//len(sizes)}%)')
    print(f'   min={min(sizes)} max={max(sizes)} mean={sum(sizes)//len(sizes)}')
    misaligned = [(f.name, s, s % 8) for f, s in zip(files, sizes) if s % 8 != 0]
    if misaligned:
        print(f'   misaligned (first 5): {misaligned[:5]}')

    # 2. ECB 가설 — 같은 8-byte block 반복 빈도
    print(f'\n2. ECB hypothesis (repeated 8-byte cipher blocks):')
    for f in files[:5]:
        data = f.read_bytes()
        blocks = [data[i:i+8] for i in range(0, len(data) - 7, 8)]
        cnt = collections.Counter(blocks)
        repeats = sum(c for c in cnt.values() if c > 1)
        unique = len(cnt)
        print(f'   {f.name:20} blocks={len(blocks):4} unique={unique:4} repeats={repeats:4} ({repeats*100//max(len(blocks),1)}%)')

    # 3. byte 분포 (전체 corpus)
    print(f'\n3. Byte distribution (whole SCN corpus):')
    total = collections.Counter()
    n_bytes = 0
    for f in files:
        d = f.read_bytes()
        total.update(d)
        n_bytes += len(d)
    bias = max(total.values()) / n_bytes
    ent = shannon_entropy(b''.join(f.read_bytes() for f in files[:20]))  # entropy of first 20 file concat
    print(f'   total bytes: {n_bytes:,}')
    print(f'   most common byte: 0x{total.most_common(1)[0][0]:02x} ({total.most_common(1)[0][1]:,} = {bias*100:.1f}%)')
    print(f'   shannon entropy (first 20 files): {ent:.4f} bits/byte (8.0 = uniform random)')
    if ent > 7.95:
        print('   → very high entropy: likely strong cipher (DES/AES) or compressed')
    elif ent > 7.5:
        print('   → high entropy: cipher or high-entropy data')
    else:
        print('   → moderate entropy: weak obfuscation (XOR, simple encoding)')

    # 4. 두 SCN 의 첫 16 byte 비교 — header plain 인지 검증
    print(f'\n4. First 16 bytes of first 5 SCN files (header plain or all encrypted?):')
    for f in files[:5]:
        d = f.read_bytes()[:16]
        print(f'   {f.name}: {d.hex()}')

    # 5. ECB IV check — 모든 파일의 첫 8-byte cipher block 이 unique 한가?
    first_blocks = [f.read_bytes()[:8] for f in files if f.stat().st_size >= 8]
    fb_unique = len(set(first_blocks))
    print(f'\n5. First-block uniqueness: {fb_unique}/{len(first_blocks)} unique')
    if fb_unique == len(first_blocks):
        print('   → all files start differently. CBC likely (per-file IV) or different plaintext + ECB.')
    else:
        print('   → some files share first cipher block. ECB hypothesis stronger.')

    # 6. CBC IV-zero hint: 같은 cipher 첫 블록 = 같은 plaintext 첫 블록 (만약 IV=0 ECB-equivalent first block)
    # 이건 ECB 와 동일 패턴이라 분리 불가, skip.

    return 0


if __name__ == '__main__':
    sys.exit(main())
