"""Hero4 SCN 파일을 DES 로 복호화.

Hero4 SCN 은 표준 DES (ECB 또는 CBC) 로 암호화되어 있음. `_DAT_DES` (824 bytes) 가
표준 DES 알고리즘 테이블 (PC-1, E-box, P-box, S1-S8) 그대로 담음을 검증.

사용 (단일 파일):
    python decrypt_h4_scn.py --key <8-byte-hex-or-ascii> <input_scn> <output_bin>

사용 (전체 SCN 일괄):
    python decrypt_h4_scn.py --key <key> --batch
        → work/h4/extracted/MAP/SC/*_scn → work/h4/decrypted/*_scn

키 입력 형식:
    --key "abcdefgh"            ASCII 8 bytes
    --key 0x6162636465666768    hex (16 nibble = 8 bytes)
    --key 61:62:63:64:65:66:67:68   colon-separated bytes
"""
from __future__ import annotations
import argparse, pathlib, sys
from Crypto.Cipher import DES


def parse_key(s: str) -> bytes:
    """다양한 형식의 키를 8 bytes 로 변환."""
    s = s.strip()
    if s.startswith('0x') or s.startswith('0X'):
        h = s[2:]
        if len(h) != 16:
            raise ValueError(f'hex key must be 16 nibbles, got {len(h)}')
        return bytes.fromhex(h)
    if ':' in s:
        parts = s.split(':')
        if len(parts) != 8:
            raise ValueError(f'colon-key must have 8 bytes, got {len(parts)}')
        return bytes(int(p, 16) for p in parts)
    if len(s) == 16 and all(c in '0123456789abcdefABCDEF' for c in s):
        return bytes.fromhex(s)
    if len(s) == 8:
        return s.encode('ascii')
    raise ValueError(f'unrecognized key format (len={len(s)}): {s!r}')


def decrypt_des(data: bytes, key: bytes, mode: str = 'ecb', iv: bytes | None = None) -> bytes:
    """DES decrypt. ECB default. data 가 8-byte 정렬 안 되어있으면 끝 잘림."""
    aligned = data[:len(data) - (len(data) % 8)]
    tail = data[len(aligned):]
    if mode == 'ecb':
        cipher = DES.new(key, DES.MODE_ECB)
    elif mode == 'cbc':
        cipher = DES.new(key, DES.MODE_CBC, iv or b'\x00' * 8)
    else:
        raise ValueError(f'unknown mode: {mode}')
    plain = cipher.decrypt(aligned)
    return plain + tail


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--key', required=True, help='DES key (ASCII / hex / colon)')
    ap.add_argument('--mode', choices=['ecb', 'cbc'], default='ecb', help='DES mode (default ecb)')
    ap.add_argument('--iv', help='CBC IV (hex). default zero')
    ap.add_argument('--batch', action='store_true', help='Decrypt all SCN files (HERO_GAME=h4)')
    ap.add_argument('input', nargs='?', help='Input file (single mode)')
    ap.add_argument('output', nargs='?', help='Output file (single mode)')
    args = ap.parse_args()

    key = parse_key(args.key)
    iv = bytes.fromhex(args.iv) if args.iv else None
    print(f'KEY: {key.hex()} ({"ASCII " + key.decode("ascii", errors="replace") if all(0x20 <= b <= 0x7e for b in key) else "binary"})', file=sys.stderr)

    if args.batch:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
        from _game import select  # noqa: E402
        g = select('h4')
        src_root = g.extracted_root / 'MAP' / 'SC'
        dst_root = g.work_root / 'decrypted' / 'SC'
        dst_root.mkdir(parents=True, exist_ok=True)
        files = sorted(src_root.glob('*_scn'))
        if not files:
            print(f'No *_scn under {src_root}', file=sys.stderr)
            return 1
        for f in files:
            data = f.read_bytes()
            out = decrypt_des(data, key, args.mode, iv)
            (dst_root / f.name).write_bytes(out)
        print(f'Decrypted {len(files)} files → {dst_root}', file=sys.stderr)
        return 0

    if not args.input or not args.output:
        ap.error('input and output required (or use --batch)')
    data = pathlib.Path(args.input).read_bytes()
    out = decrypt_des(data, key, args.mode, iv)
    pathlib.Path(args.output).write_bytes(out)
    print(f'Wrote {len(out)} bytes → {args.output}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
