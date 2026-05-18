"""Hero4 plaintext SCN bytecode disassembler.

대상: e0184_scn (30B), e0185_scn (6313B) — DES 미적용 outlier 2개.

Header (12 byte):
    [0] = 0x01            # SCN magic
    [1] = variant_a       # e0184:00, e0185:02  (record count?)
    [2] = 0x01            # type marker
    [3] = 0x53 = 'S'      # SCN signature
    [4] = 0x00
    [5] = 0x01
    [6] = variant_b       # e0184:a1, e0185:c8  (size hint? id?)
    [7..11] = 0xff × 5    # header terminator

Bytecode (from offset 12):
    0xff               = record/section separator
    0x01 [len] [data]  = length-prefixed payload (often NUL-terminated string)
    0x07 0x00 0x00 0x00 0xff = "BEGIN_BODY" marker (1회 등장, 헤더 직후 또는 prologue)
    0x0c [byte] [0xff] = small immediate / param
    0xf7 [a] [b] [c]   = resource-bind / opcode (e0185 에서 5회 연속 `f7 NN 01 NN`)
    0x2e               = high-frequency opcode (e0185 에서 498회) — 미정
    0x06 [len] [data\\0] = NUL-terminated ASCII/EUC-KR string with explicit len

Catalog (e0185 only, 시작 ~offset 5457):
    EUC-KR null-terminated strings 의 연속.
    글로벌 entity catalog (87 strings) — 캐릭터/장소/이벤트 이름.
    Tuatha Dé Danann 신화 인물 포함.

Output: JSON 으로 (header_meta, bytecode_tokens, korean_catalog) 분리.
"""
from __future__ import annotations
import argparse, json, pathlib, sys
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
SCN_DIR = ROOT / 'work' / 'h4' / 'extracted' / 'MAP' / 'SC'
DEFAULT_OUT_DIR = ROOT / 'work' / 'h4' / 'converted'


def parse_header(d: bytes) -> dict:
    """Decode the 12-byte SCN header."""
    if len(d) < 12:
        return {'error': 'too_short', 'size': len(d)}
    h = d[:12]
    return {
        'magic': h[0],
        'variant_a': h[1],
        'type_marker': h[2],
        'signature_S': h[3] == 0x53,
        'header_byte4': h[4],
        'header_byte5': h[5],
        'variant_b': h[6],
        'separator_count': sum(1 for b in h[7:12] if b == 0xff),
        'header_hex': h.hex(),
        'signature_ok': h[0] == 0x01 and h[2] == 0x01 and h[3] == 0x53 and h[4] == 0x00 and h[5] == 0x01,
    }


def find_catalog_start(d: bytes, min_strings: int = 5) -> int | None:
    """Detect the start of the EUC-KR catalog by finding a sequence of valid
    NUL-terminated EUC-KR strings."""
    n = len(d)
    for start in range(12, n - 32):
        valid = 0
        pos = start
        # Skip leading NULs
        while pos < n and d[pos] == 0:
            pos += 1
            if pos - start > 4: break
        if pos >= n: continue
        # Try to read consecutive null-terminated EUC-KR strings
        last_end = pos
        for _ in range(min_strings):
            if pos >= n: break
            j = pos
            while j < n and d[j] != 0:
                j += 1
            if j == pos or j - pos < 2:
                break
            chunk = d[pos:j]
            high_count = sum(1 for b in chunk if b >= 0xa1)
            if high_count >= 2:
                try:
                    chunk.decode('euc-kr')
                    valid += 1
                    pos = j + 1
                    last_end = pos
                except UnicodeDecodeError:
                    break
            else:
                break
        if valid >= min_strings:
            return start
    return None


def extract_catalog(d: bytes, start: int) -> list[dict]:
    """From `start`, extract all consecutive NUL-terminated EUC-KR strings.
    Allow short Latin strings between Korean entries (mixed catalog)."""
    catalog = []
    pos = start
    bad_streak = 0
    while pos < len(d):
        j = pos
        while j < len(d) and d[j] != 0:
            j += 1
        if j == pos:
            pos = j + 1
            continue
        chunk = d[pos:j]
        try:
            text = chunk.decode('euc-kr', errors='strict')
            catalog.append({
                'offset': pos,
                'length': len(chunk),
                'text': text,
                'has_korean': any('가' <= c <= '힣' for c in text),
            })
            bad_streak = 0
        except UnicodeDecodeError:
            bad_streak += 1
            if bad_streak >= 3:
                break
        pos = j + 1
    return catalog


def tokenize_bytecode(d: bytes, end: int) -> list[dict]:
    """Tokenize the bytecode region [12, end) into structured records.

    매우 단순한 1-pass 토큰화. 0xff 를 record 종료자로 사용해 record 단위로 자름.
    각 record 내부에서 알려진 opcode 패턴 detection.
    """
    tokens = []
    pos = 12
    rec_start = pos
    while pos < end:
        b = d[pos]
        if b == 0xff:
            # Finalize record
            if pos > rec_start:
                rec_bytes = d[rec_start:pos]
                token = analyze_record(rec_bytes, rec_start)
                tokens.append(token)
            tokens.append({'kind': 'sep', 'offset': pos, 'hex': 'ff'})
            pos += 1
            rec_start = pos
        else:
            pos += 1
    # Tail record (no trailing 0xff)
    if rec_start < end:
        tokens.append(analyze_record(d[rec_start:end], rec_start))
    return tokens


def analyze_record(rec: bytes, off: int) -> dict:
    """Best-effort interpretation of a bytecode record."""
    h = rec.hex()
    n = len(rec)
    # Try string detection: NUL-terminated ASCII or EUC-KR
    if n >= 3 and rec[-1] == 0x00:
        try:
            text = rec[1:-1].decode('ascii', errors='strict')
            if all(0x20 <= ord(c) < 0x7f for c in text) and len(text) >= 2:
                return {'kind': 'ascii_str', 'offset': off, 'len_byte': rec[0], 'text': text, 'hex': h}
        except UnicodeDecodeError:
            pass
        try:
            text = rec[1:-1].decode('euc-kr', errors='strict')
            if any('가' <= c <= '힣' for c in text):
                return {'kind': 'korean_str', 'offset': off, 'len_byte': rec[0], 'text': text, 'hex': h}
        except UnicodeDecodeError:
            pass
    # Magic markers
    if rec.startswith(bytes.fromhex('0700000000')):
        return {'kind': 'magic_07_zero', 'offset': off, 'hex': h, 'size': n}
    if rec.startswith(b'\x0c'):
        return {'kind': 'op_0c', 'offset': off, 'param': rec[1] if n > 1 else None, 'hex': h, 'size': n}
    if rec.startswith(b'\xf7') and n == 3:
        return {'kind': 'op_f7_bind', 'offset': off, 'a': rec[1], 'b': rec[2] if n > 2 else None, 'hex': h, 'size': n}
    # Generic
    op = rec[0] if n else None
    return {'kind': f'op_{op:#04x}' if op is not None else 'empty',
            'offset': off, 'hex': h, 'size': n}


def disassemble(d: bytes) -> dict:
    out = {
        'size': len(d),
        'header': parse_header(d),
    }
    catalog_start = find_catalog_start(d)
    body_end = catalog_start if catalog_start else len(d)
    out['body_end'] = body_end
    out['catalog_start'] = catalog_start
    out['bytecode_size'] = body_end - 12
    out['tokens'] = tokenize_bytecode(d, body_end)
    # Token stats
    token_kinds = Counter(t['kind'] for t in out['tokens'])
    out['token_kind_stats'] = dict(token_kinds)
    if catalog_start is not None:
        out['catalog'] = extract_catalog(d, catalog_start)
        out['catalog_size'] = len(out['catalog'])
    else:
        out['catalog'] = []
        out['catalog_size'] = 0
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='*', help='SCN files (default: e0184, e0185)')
    ap.add_argument('--out_dir', default=str(DEFAULT_OUT_DIR))
    args = ap.parse_args()

    targets = args.files
    if not targets:
        targets = [str(SCN_DIR / 'e0184_scn'), str(SCN_DIR / 'e0185_scn')]

    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for f in targets:
        path = pathlib.Path(f)
        d = path.read_bytes()
        result = disassemble(d)
        out_path = out_dir / f'{path.name}_disasm.json'
        with open(out_path, 'w', encoding='utf-8') as fp:
            json.dump(result, fp, ensure_ascii=False, indent=2)
        print(f'=== {path.name} ({result["size"]}B) ===')
        print(f'  signature_ok: {result["header"]["signature_ok"]}')
        print(f'  variant_a={result["header"]["variant_a"]}, variant_b={hex(result["header"]["variant_b"])}')
        print(f'  bytecode: {result["bytecode_size"]}B ({len(result["tokens"])} tokens)')
        print(f'  catalog: {result["catalog_size"]} strings (from offset {result["catalog_start"]})')
        print(f'  token kinds: {result["token_kind_stats"]}')
        # Sample first few non-sep tokens
        non_sep = [t for t in result['tokens'] if t['kind'] != 'sep'][:8]
        print(f'  First non-sep tokens:')
        for t in non_sep:
            print(f'    @{t["offset"]:4d} {t["kind"]:18} {t.get("hex","")[:32]} {repr(t.get("text",""))[:30]}')
        print(f'  -> {out_path}')
        print()

    # Save catalog separately for e0185 (translation_dict.py compatibility)
    e0185_path = next((t for t in targets if 'e0185' in t), None)
    if e0185_path:
        e0185_data = pathlib.Path(e0185_path).read_bytes()
        result = disassemble(e0185_data)
        nt_path = out_dir / 'e0185_name_table.json'
        with open(nt_path, 'w', encoding='utf-8') as fp:
            json.dump({
                'source': 'e0185_scn',
                'catalog_start': result['catalog_start'],
                'count': result['catalog_size'],
                'entries': result['catalog'],
            }, fp, ensure_ascii=False, indent=2)
        print(f'Wrote name_table -> {nt_path} ({result["catalog_size"]} entries)')

    return 0


if __name__ == '__main__':
    sys.exit(main())
