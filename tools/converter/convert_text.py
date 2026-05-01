"""
Hero3 _txt 문자열 테이블 → JSON 변환기.

포맷:
    uint16 file_size
    uint16 string_count
    uint16 offsets[count]
    bytes  strings (EUC-KR)

사용:
    python convert_text.py <input.txt> <output.json>
"""
from __future__ import annotations
import struct, sys, json, pathlib


def parse_text_table(data: bytes) -> list[str]:
    declared_size, count = struct.unpack_from('<HH', data, 0)
    if declared_size != len(data):
        print(f'  warn: declared size {declared_size} != actual {len(data)}', file=sys.stderr)
    offsets = list(struct.unpack_from(f'<{count}H', data, 4))
    strings = []
    for i, off in enumerate(offsets):
        end = offsets[i + 1] if i + 1 < count else len(data)
        raw = data[off:end].rstrip(b'\x00')
        strings.append(raw.decode('euc-kr', errors='replace'))
    return strings


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = pathlib.Path(argv[1]), pathlib.Path(argv[2])
    data = src.read_bytes()
    strings = parse_text_table(data)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(strings, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  {src.name} -> {dst.name} ({len(strings)} strings)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
