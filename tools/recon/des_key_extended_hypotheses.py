"""Hero4 DES key — 확장 가설 테스트.

find_h4_des_key_v2.py 의 sliding-window 외 추가 가설:
    * sequential byte runs (0x79..0x86)
    * Hash-based (MD5/SHA1 of '/DAT/_DAT_DES' 등)
    * __adf__ 의 SLvl/SLvl2/FSize/Timestamp 값을 big/little endian 8-byte 로
    * 다양한 ASCII 패턴
    * J@IWO8N7L0E7E 의 패턴 변형
"""
from __future__ import annotations
import collections, hashlib
from Crypto.Cipher import DES


KNOWN_LAST = bytes.fromhex('3b7af9a427907dac')
KNOWN_FIRST = bytes.fromhex('4655b8f39c0fe0b2')


def gen_keys():
    keys = []

    # 0x79..0x86 sliding (8 bytes wide)
    seq = bytes(range(0x79, 0x87))
    for i in range(len(seq) - 7):
        keys.append((seq[i:i+8], f'seq_0x{0x79+i:02x}'))

    # Hash-based
    sources = [
        b'/DAT/_DAT_DES', b'_DAT_DES', b'DAT_DES', b'DES', b'J@IWO8N7L0E7E',
        b'010100D4', b'PD008712', b'Hero4', b'HERO4', b'01.00.03',
        b'/DAT', b'DAT', b'Hanbit', b'HANBIT', b'hanbit',
        # Korean (UTF-8)
        '영웅서기4'.encode('utf-8'), '환영의검'.encode('utf-8'),
        '영웅서기4'.encode('euc-kr'), '환영의검'.encode('euc-kr'),
        '한빛'.encode('utf-8'), '한빛'.encode('euc-kr'),
    ]
    for src in sources:
        keys.append((hashlib.md5(src).digest()[:8], f'md5({src!r})[0:8]'))
        keys.append((hashlib.md5(src).digest()[-8:], f'md5({src!r})[-8:]'))
        keys.append((hashlib.sha1(src).digest()[:8], f'sha1({src!r})[0:8]'))
        keys.append((hashlib.sha1(src).digest()[-8:], f'sha1({src!r})[-8:]'))

    # __adf__ 숫자 값들
    for val in [0x00142F9C, 0x00000183, 2683680, 1262924594764 & 0xFFFFFFFFFFFFFFFF,
                4000, 240*320, 0x010100D4, 0x01041768, 0x008712, 0x32]:
        for endian in ('big', 'little'):
            try:
                keys.append((val.to_bytes(8, endian), f'int 0x{val:x} {endian}'))
            except OverflowError:
                pass

    # AID/Version concatenation
    keys.append((bytes.fromhex('010100D401000003'), 'AID+ver bytes BE'))
    keys.append((bytes.fromhex('D400010103000001'), 'AID+ver bytes LE'))

    # ASCII candidates
    ascii_tests = [
        b'JIWONLEE', b'EELNOWIJ', b'jiwonlee',
        b'HanbitSf', b'HanbitH4', b'h4nbitH4', b'01010101',
        b'PD041768', b'01041768',
        b'JeongWon', b'Jiwon@H4', b'HERO_H4_', b'_HERO_H4',
        # Pattern transformations of J@IWO8N7L0E7E
        b'JI@WO8N7', b'JIWO8N7L', b'EL0E7E07',
    ]
    for s in ascii_tests:
        if len(s) == 8:
            keys.append((s, f'ascii {s!r}'))

    return keys


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    keys = gen_keys()
    print(f'{len(keys)} candidates')
    hits = []
    seen = set()
    for k, label in keys:
        if len(k) != 8 or k in seen:
            continue
        seen.add(k)
        try:
            c = DES.new(k, DES.MODE_ECB)
            plast = c.decrypt(KNOWN_LAST)
            pfirst = c.decrypt(KNOWN_FIRST)
        except ValueError:
            continue
        distinct_last = len(set(plast))
        cnt_last = collections.Counter(plast)
        most = cnt_last.most_common(1)[0]
        score = 0
        reasons = []
        if distinct_last <= 2:
            score += 500; reasons.append(f'distinct={distinct_last}')
        elif distinct_last == 3:
            score += 100; reasons.append(f'distinct=3')
        if most[1] >= 5 and most[0] in (0, 0xff):
            score += 200; reasons.append(f'{hex(most[0])}*{most[1]}')
        elif most[1] >= 4:
            score += 30; reasons.append(f'{hex(most[0])}*{most[1]}')
        if pfirst[:3] == b'\x00\x00\x00':
            score += 100; reasons.append('first_000')
        if pfirst[:4] == b'\x00\x00\x00\xff':
            score += 100; reasons.append('first_000ff')
        hits.append((score, k, plast, pfirst, label, reasons))

    hits.sort(key=lambda x: -x[0])
    print(f'\nTop 30:')
    for s, k, pl, pf, lbl, rs in hits[:30]:
        ksafe = k.decode('latin-1', errors='replace').replace('\n', '\\n')
        print(f'  score={s:4} key={k.hex()} ({ksafe!r:30})  last={pl.hex()}  first={pf.hex()}  [{lbl} | {",".join(rs)}]')


if __name__ == '__main__':
    main()
