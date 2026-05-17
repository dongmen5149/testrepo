"""Hero4 _DAT_DES 824 byte 표준 DES 테이블 정밀 검증.

2026-05-18 발견:
    표준 DES 테이블 모두 정확히 포함되어 있으나, **S1 에서 1 byte 차이**.
    S1[58] (row 3, col 10): standard=3, _DAT_DES=2  @ file offset 0x010a

함의:
    (a) 단순 typo / bit error: 게임 동작에는 영향 미미 (DES 출력만 일부 달라짐)
    (b) **의도적 변형**: 표준 DES 라이브러리 호환성을 의도적으로 깬 것이면,
        PyCryptodome/Java SunJCE 등의 stock DES 로는 복호화 절대 불가.
        반드시 custom S1 을 사용한 DES 구현 필요.

레이아웃 (824 bytes 전체):
    @0x0000 IP       (64B) — Initial Permutation
    @0x0040 IP-Inv   (64B) — Final Permutation
    @0x0080 E        (48B) — Expansion (32→48)
    @0x00b0 P        (32B) — Round permutation
    @0x00d0 S1       (64B) ⚠ 1-byte differ at relative offset 58
    @0x0110 S2       (64B)
    @0x0150 S3       (64B)
    @0x0190 S4       (64B)
    @0x01d0 S5       (64B)
    @0x0210 S6       (64B)
    @0x0250 S7       (64B)
    @0x0290 S8       (64B)
    @0x02d0 PC-1     (56B) — Permuted Choice 1
    @0x0308 PC-2     (48B) — Permuted Choice 2
    @0x0338 END
"""
from __future__ import annotations
import pathlib, sys


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DAT_DES = ROOT / 'work' / 'h4' / 'extracted' / 'DAT' / '_DAT_DES'


# Standard DES tables (FIPS 46)
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
P = [16, 7,20,21,29,12,28,17, 1,15,23,26, 5,18,31,10,
      2, 8,24,14,32,27, 3, 9,19,13,30, 6,22,11, 4,25]
S_STD = [
 [14,4,13,1,2,15,11,8,3,10,6,12,5,9,0,7,
  0,15,7,4,14,2,13,1,10,6,12,11,9,5,3,8,
  4,1,14,8,13,6,2,11,15,12,9,7,3,10,5,0,
  15,12,8,2,4,9,1,7,5,11,3,14,10,0,6,13],
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
PC1 = [57,49,41,33,25,17, 9, 1,58,50,42,34,26,18,10, 2,59,51,43,35,27,19,11, 3,60,52,44,36,
       63,55,47,39,31,23,15, 7,62,54,46,38,30,22,14, 6,61,53,45,37,29,21,13, 5,28,20,12, 4]
PC2 = [14,17,11,24, 1, 5, 3,28,15, 6,21,10,23,19,12, 4,26, 8,16, 7,27,20,13, 2,
       41,52,31,37,47,55,30,40,51,45,33,48,44,49,39,56,34,53,46,42,50,36,29,32]

LAYOUT = [
    ('IP',     0x0000, IP),
    ('IP_INV', 0x0040, IP_INV),
    ('E',      0x0080, E),
    ('P',      0x00b0, P),
    ('S1',     0x00d0, S_STD[0]),
    ('S2',     0x0110, S_STD[1]),
    ('S3',     0x0150, S_STD[2]),
    ('S4',     0x0190, S_STD[3]),
    ('S5',     0x01d0, S_STD[4]),
    ('S6',     0x0210, S_STD[5]),
    ('S7',     0x0250, S_STD[6]),
    ('S8',     0x0290, S_STD[7]),
    ('PC1',    0x02d0, PC1),
    ('PC2',    0x0308, PC2),
]


def main():
    if not DAT_DES.exists():
        print(f'MISSING: {DAT_DES}', file=sys.stderr)
        return 1
    data = DAT_DES.read_bytes()
    print(f'_DAT_DES size: {len(data)} bytes')
    expected_total = sum(len(t) for _, _, t in LAYOUT)
    print(f'Expected layout total: {expected_total} bytes')
    print()
    print(f'{"Table":<8} {"Offset":<8} {"Size":<6} {"Match":<10} Notes')
    print('-' * 60)

    deviations = []
    for name, off, table in LAYOUT:
        n = len(table)
        if off + n > len(data):
            print(f'{name:<8} 0x{off:04x}    {n:<6} OOB        skipped')
            continue
        region = data[off:off+n]
        match = sum(1 for j in range(n) if region[j] == table[j])
        mismatches = [(j, table[j], region[j]) for j in range(n) if region[j] != table[j]]
        status = 'EXACT' if match == n else f'{match}/{n}'
        notes = ''
        if mismatches:
            for j, e, a in mismatches:
                notes += f'@rel{j}(0x{off+j:04x}): std={e}, got={a}; '
                deviations.append((name, off+j, j, e, a))
        print(f'{name:<8} 0x{off:04x}   {n:<6} {status:<10} {notes}')

    print()
    if deviations:
        print('=== DEVIATIONS from standard DES ===')
        for name, abs_off, rel_off, std, actual in deviations:
            # Compute S-box row/col for S-boxes (rel = row*16 + col)
            extra = ''
            if name.startswith('S'):
                row = rel_off // 16
                col = rel_off % 16
                extra = f'(row {row}, col {col}; bit diff: 0x{std ^ actual:x})'
            print(f'  {name}[{rel_off}] @0x{abs_off:04x}: std={std}, actual={actual} {extra}')
        print()
        print('Implication:')
        print('  Hero4 DES is NOT byte-exact standard DES.')
        print('  PyCryptodome/SunJCE stock DES will produce different ciphertext.')
        print('  Need custom DES with modified S1 to decrypt SCN files.')
    else:
        print('All tables match standard DES exactly.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
