"""Hero4 SCN 파일을 DES 로 복호화.

Hero4 SCN 은 한빛소프트 자체 DES 변종 (Hero3/Hero5 공용) 으로 암호화됨:
    - 표준 FIPS DES 테이블 + S1[58]=2 한 byte 수정
    - startDes(mode=0) 인 swap halves + reversed subkey (Feistel 의 decrypt-path)

Round 68 (2026-05-18) 에 키 확정:
    KEY = b'J@IWO8N7'  (binary 0x86edc 의 `J@IWO8N7L0E7E` 처음 8 byte ASCII)
    구현 = tools/h5_des.py:mx_des_decrypt (Hero5 libHeroesLore5.so 의 MX_desDecrypt 포팅)

사용 (단일 파일):
    python decrypt_h4_scn.py --key <8-byte-hex-or-ascii> <input_scn> <output_bin>

사용 (전체 SCN + HDAT-A 일괄):
    python decrypt_h4_scn.py --key J@IWO8N7 --batch
        → work/h4/extracted/MAP/SC/*_scn → work/h4/decrypted/SC/*_scn
        → work/h4/extracted/HDAT/_H_{BH,BS,SA,SS,S000-S003} → work/h4/decrypted/HDAT/

사용 (디렉토리):
    python decrypt_h4_scn.py --key J@IWO8N7 --input_dir <DIR> --output_dir <DIR>

키 입력 형식:
    --key "abcdefgh"            ASCII 8 bytes
    --key 0x6162636465666768    hex (16 nibble = 8 bytes)
    --key 61:62:63:64:65:66:67:68   colon-separated bytes
    --mode std-ecb              표준 PyCryptodome DES (legacy v3 검증용)
    --mode mx-des               (default) Hero5 mx_des_decrypt 변종
"""
from __future__ import annotations
import argparse, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from h5_des import mx_des_decrypt  # noqa: E402


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


def decrypt_des(data: bytes, key: bytes, mode: str = 'mx-des', iv: bytes | None = None) -> bytes:
    """Hero4 DES decrypt. mx-des (default) 가 한빛 변종, std-ecb 는 PyCryptodome legacy."""
    aligned = data[:len(data) - (len(data) % 8)]
    tail = data[len(aligned):]
    if mode == 'mx-des':
        plain = mx_des_decrypt(aligned, key)
    elif mode == 'std-ecb':
        from Crypto.Cipher import DES  # legacy path
        plain = DES.new(key, DES.MODE_ECB).decrypt(aligned)
    elif mode == 'std-cbc':
        from Crypto.Cipher import DES
        plain = DES.new(key, DES.MODE_CBC, iv or b'\x00' * 8).decrypt(aligned)
    else:
        raise ValueError(f'unknown mode: {mode}')
    return plain + tail


def _is_plaintext_scn(data: bytes) -> bool:
    """e0184/e0185 처럼 SCN signature `01 ?? 01 53 00 01 ?? ??` 가 그대로 보이면 plaintext."""
    if len(data) < 8:
        return True
    return data[0] == 0x01 and data[2] == 0x01 and data[3] == 0x53 and data[4] == 0x00 and data[5] == 0x01


def _batch_dir(src: pathlib.Path, dst: pathlib.Path, key: bytes, mode: str, iv: bytes | None,
               pattern: str = '*_scn') -> int:
    """src 디렉토리의 pattern 매칭 파일 모두 복호화 → dst.

    Plaintext SCN (8B-aligned 아니거나 signature 매칭) 은 그대로 복사.
    """
    dst.mkdir(parents=True, exist_ok=True)
    files = sorted(src.glob(pattern))
    if not files:
        return 0
    for f in files:
        if not f.is_file():
            continue
        data = f.read_bytes()
        if len(data) % 8 != 0 or _is_plaintext_scn(data):
            (dst / f.name).write_bytes(data)
        else:
            out = decrypt_des(data, key, mode, iv)
            (dst / f.name).write_bytes(out)
    return len(files)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--key', required=True, help='DES key (ASCII / hex / colon)')
    ap.add_argument('--mode', choices=['mx-des', 'std-ecb', 'std-cbc'], default='mx-des',
                    help='DES variant (default mx-des = Hero5 MX_desDecrypt port)')
    ap.add_argument('--iv', help='std-cbc IV (hex). default zero')
    ap.add_argument('--batch', action='store_true',
                    help='Decrypt all SCN + HDAT-A files (HERO_GAME=h4)')
    ap.add_argument('--input_dir', help='Directory containing files to decrypt')
    ap.add_argument('--output_dir', help='Output directory')
    ap.add_argument('--pattern', default='*_scn', help='Glob pattern for batch/input_dir (default *_scn)')
    ap.add_argument('input', nargs='?', help='Input file (single mode)')
    ap.add_argument('output', nargs='?', help='Output file (single mode)')
    args = ap.parse_args()

    key = parse_key(args.key)
    iv = bytes.fromhex(args.iv) if args.iv else None
    ks = key.decode('ascii', errors='replace') if all(0x20 <= b <= 0x7e for b in key) else key.hex()
    print(f'KEY: {key.hex()} (ASCII {ks!r})  MODE: {args.mode}', file=sys.stderr)

    if args.batch:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
        from _game import select  # noqa: E402
        g = select('h4')
        # SCN files (348 encrypted + 2 plaintext)
        scn_src = g.extracted_root / 'MAP' / 'SC'
        scn_dst = g.work_root / 'decrypted' / 'SC'
        n_scn = _batch_dir(scn_src, scn_dst, key, args.mode, iv, '*_scn')
        print(f'  SCN: {n_scn} files → {scn_dst}', file=sys.stderr)

        # HDAT Group A 8 files share the same key (sentinel cross-ref 92회)
        hdat_src = g.extracted_root / 'HDAT'
        hdat_dst = g.work_root / 'decrypted' / 'HDAT'
        hdat_dst.mkdir(parents=True, exist_ok=True)
        hdat_a_names = ['_H_BH', '_H_BS', '_H_SA', '_H_SS', '_H_S000', '_H_S001', '_H_S002', '_H_S003']
        n_hdat = 0
        for name in hdat_a_names:
            src_f = hdat_src / name
            if not src_f.exists():
                continue
            data = src_f.read_bytes()
            out = decrypt_des(data, key, args.mode, iv)
            (hdat_dst / name).write_bytes(out)
            n_hdat += 1
        print(f'  HDAT-A: {n_hdat} files → {hdat_dst}', file=sys.stderr)
        print(f'Total: {n_scn + n_hdat} files decrypted.', file=sys.stderr)
        return 0

    if args.input_dir:
        src = pathlib.Path(args.input_dir)
        dst = pathlib.Path(args.output_dir) if args.output_dir else src.parent / (src.name + '.decrypted')
        n = _batch_dir(src, dst, key, args.mode, iv, args.pattern)
        print(f'Decrypted {n} files from {src} → {dst}', file=sys.stderr)
        return 0

    if not args.input or not args.output:
        ap.error('input and output required (or use --batch / --input_dir)')
    data = pathlib.Path(args.input).read_bytes()
    out = decrypt_des(data, key, args.mode, iv)
    pathlib.Path(args.output).write_bytes(out)
    print(f'Wrote {len(out)} bytes → {args.output}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
